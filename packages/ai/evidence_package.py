import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from packages.common.entities import default_entity_graph


class VerifiedFact(BaseModel):
    """A verified, immutable fact triple grounded in authoritative reporting or rank 1-2 confirmation."""

    fact_id: str = Field(..., description="Unique fact identifier within the package, e.g. 'fact-1'")
    claim_id: str | int | None = Field(None, description="Originating database claim ID")
    subject: str = Field(..., description="Canonical subject entity name (e.g. player, manager)")
    predicate: str = Field(..., description="Canonical action or state (e.g. 'official_signing', 'agrees_terms')")
    object: str = Field(..., description="Canonical object entity name (e.g. club, league)")
    qualifiers: dict[str, Any] = Field(default_factory=dict, description="Normalized qualifiers (e.g. fee_eur_millions, years)")
    evidence_span: str = Field(..., description="Verbatim short textual span from source, max 200 chars")
    authority_rank: int = Field(default=1, description="Authority rank (1=official announcement, 2=registration, 3=tier 1)")


class UncertainClaim(BaseModel):
    """An unconfirmed or developing claim with an explicit, preserved uncertainty marker."""

    claim_id: str | int = Field(..., description="Originating database claim ID")
    fact_id: str = Field(..., description="Unique identifier within the package, e.g. 'claim-fact-1'")
    marker: str = Field(
        ...,
        description="Preserved uncertainty marker: 'reported', 'expected', 'alleged', 'understood', 'denied'",
    )
    statement: str = Field(..., description="Structured statement or verified excerpt")
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    outlet: str = Field(..., description="Reporting source outlet")
    reporter: str | None = Field(None, description="Byline reporter if known")


class Contradiction(BaseModel):
    """Explicit record of conflicting claims or disputed assertions."""

    conflict_id: str = Field(..., description="Unique contradiction identifier, e.g. 'conflict-1'")
    claim_a_id: str | int = Field(..., description="First conflicting claim ID")
    claim_b_id: str | int = Field(..., description="Second conflicting claim ID")
    details: str = Field(..., description="Description of the dispute (e.g. 'signing vs denial')")


class ApprovedSource(BaseModel):
    """Provenance and reliability record for an approved source outlet."""

    outlet: str = Field(..., description="Outlet name")
    reliability_score: float = Field(..., description="Wilson lower bound reliability score")
    attribution_type: str = Field(default="first_party", description="'first_party' (original) or 'aggregation'")


class EvidencePackage(BaseModel):
    """Physical isolation container for generation under Handbook §7.

    The summariser receives ONLY this package — never raw article text.
    """

    package_id: str = Field(..., description="Deterministic SHA-256 hash of verified facts and claims")
    event_id: str | int = Field(..., description="Parent event ID")
    verified_facts: list[VerifiedFact] = Field(default_factory=list)
    uncertain_claims: list[UncertainClaim] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    entity_glossary: dict[str, str] = Field(
        default_factory=dict,
        description="Map of canonical entity names to approved target forms",
    )
    approved_sources: list[ApprovedSource] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def all_fact_ids(self) -> set[str]:
        """Returns the set of all valid fact_id tags in this evidence package."""
        ids = {f.fact_id for f in self.verified_facts}
        ids.update(c.fact_id for c in self.uncertain_claims)
        return ids

    @classmethod
    def compute_package_id(
        cls,
        event_id: str | int,
        verified_facts: list[VerifiedFact],
        uncertain_claims: list[UncertainClaim],
        contradictions: list[Contradiction],
        entity_glossary: dict[str, str],
    ) -> str:
        """Computes a deterministic SHA-256 hash for cache keys and audit trails."""
        payload = {
            "event_id": str(event_id),
            "facts": [f.model_dump(exclude={"evidence_span"}) for f in sorted(verified_facts, key=lambda x: x.fact_id)],
            "claims": [c.model_dump() for c in sorted(uncertain_claims, key=lambda x: x.fact_id)],
            "contradictions": [k.model_dump() for k in sorted(contradictions, key=lambda x: x.conflict_id)],
            "glossary": sorted(entity_glossary.items()),
        }
        raw_bytes = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw_bytes).hexdigest()


class EvidencePackageBuilder:
    """Constructs isolated EvidencePackage instances from database models, stripping all untrusted raw text."""

    @classmethod
    def extract_uncertainty_marker(cls, text: str) -> str:
        """Detects the exact uncertainty marker present in the claim."""
        t_lower = text.lower()
        if any(w in t_lower for w in ["denied", "denies", "rejects", "rules out", "dementi", "schließt aus"]):
            return "denied"
        if any(w in t_lower for w in ["alleged", "allegation", "accused"]):
            return "alleged"
        if any(w in t_lower for w in ["expected", "expects", "anticipated"]):
            return "expected"
        if any(w in t_lower for w in ["understood", "it is understood"]):
            return "understood"
        return "reported"

    @classmethod
    def build_from_event(
        cls,
        event: Any,
        claims: list[Any],
        target_lang: str = "en",
        has_contradiction: bool = False,
    ) -> EvidencePackage:
        """Builds a structured evidence package from an EventModel and its ClaimModels."""
        verified_facts: list[VerifiedFact] = []
        uncertain_claims: list[UncertainClaim] = []
        contradictions: list[Contradiction] = []
        approved_sources: list[ApprovedSource] = []
        seen_outlets: set[str] = set()

        # Build entity glossary
        raw_entity_names = [e.name for e in getattr(event, "entities", [])]
        entity_glossary = default_entity_graph.get_localized_glossary(raw_entity_names, target_lang=target_lang)

        # Index and classify claims
        fact_idx = 1
        for c in claims:
            # Source attribution
            outlet = c.source.name if getattr(c, "source", None) else "Unknown Source"
            wilson = 0.5
            if getattr(c, "source", None):
                src_val = getattr(c.source, "wilson_lower_bound", None)
                if src_val is None:
                    src_val = getattr(c.source, "reliability_score", None)
                wilson = float(src_val) if src_val is not None else 0.5
            attr_type = getattr(c, "attribution_type", "first_party") or "first_party"

            if outlet not in seen_outlets:
                approved_sources.append(
                    ApprovedSource(
                        outlet=outlet,
                        reliability_score=round(wilson, 4),
                        attribution_type=attr_type,
                    )
                )
                seen_outlets.add(outlet)

            # Determine whether this is a verified fact (Rank 1 official / confirmed) or uncertain claim
            predicate = getattr(c, "predicate", None) or "reports"
            is_official = predicate in ["official_signing", "contract_extension"] or (
                hasattr(c, "source") and getattr(c.source, "rank", 3) <= 2
            )

            # Parse qualifiers safely
            qualifiers: dict[str, Any] = {}
            if getattr(c, "qualifiers", None):
                try:
                    q_raw = c.qualifiers
                    qualifiers = json.loads(q_raw) if isinstance(q_raw, str) else q_raw
                except Exception:
                    pass

            if is_official:
                fid = f"fact-{fact_idx}"
                fact_idx += 1
                subj = getattr(c, "subject_id", None)
                if not subj and raw_entity_names:
                    subj = raw_entity_names[0]
                obj = getattr(c, "object_id", None)
                if not obj and len(raw_entity_names) > 1:
                    obj = raw_entity_names[1]

                verified_facts.append(
                    VerifiedFact(
                        fact_id=fid,
                        claim_id=str(getattr(c, "id", "")) if getattr(c, "id", None) is not None else None,
                        subject=subj or "Subject",
                        predicate=predicate,
                        object=obj or "Object",
                        qualifiers=qualifiers,
                        evidence_span=(getattr(c, "evidence_span", None) or c.claim_text)[:200],
                        authority_rank=1 if predicate == "official_signing" else 2,
                    )
                )
            else:
                cid = f"claim-fact-{fact_idx}"
                fact_idx += 1
                marker = cls.extract_uncertainty_marker(c.claim_text)
                uncertain_claims.append(
                    UncertainClaim(
                        claim_id=str(getattr(c, "id", "0")),
                        fact_id=cid,
                        marker=marker,
                        statement=getattr(c, "evidence_span", None) or c.claim_text,
                        subject=getattr(c, "subject_id", None),
                        predicate=predicate,
                        object=getattr(c, "object_id", None),
                        outlet=outlet,
                        reporter=getattr(c, "reporter", None),
                    )
                )

        # Detect contradictions if multiple predicates conflict (e.g. signing vs denial)
        if has_contradiction or any(u.marker == "denied" for u in uncertain_claims):
            for i, u in enumerate(uncertain_claims):
                if u.marker == "denied":
                    for j, other in enumerate(uncertain_claims):
                        if i != j and other.marker != "denied":
                            contradictions.append(
                                Contradiction(
                                    conflict_id=f"conflict-{len(contradictions) + 1}",
                                    claim_a_id=str(other.claim_id),
                                    claim_b_id=str(u.claim_id),
                                    details=f"{u.outlet} denied report from {other.outlet}",
                                )
                            )

        package_id = EvidencePackage.compute_package_id(
            event_id=str(getattr(event, "id", "0")),
            verified_facts=verified_facts,
            uncertain_claims=uncertain_claims,
            contradictions=contradictions,
            entity_glossary=entity_glossary,
        )

        return EvidencePackage(
            package_id=package_id,
            event_id=str(getattr(event, "id", "0")),
            verified_facts=verified_facts,
            uncertain_claims=uncertain_claims,
            contradictions=contradictions,
            entity_glossary=entity_glossary,
            approved_sources=approved_sources,
        )
