"""Deterministic Schema Validation Gate for Structured Claims.

Enforces Handbook §5.2 invariants:
- Claims must adhere strictly to structured triples: (Subject, Predicate, Object, Evidence Span).
- Predicate must belong to the approved canonical dictionary.
- Evidence span must be a verbatim exact substring of source text when body is provided.
- Extraction confidence must satisfy the quality threshold (>= 0.50).
- Pure deterministic validation at Rung L0 (€0.00 spend).
"""

from dataclasses import dataclass, field
from typing import Any

APPROVED_PREDICATES: set[str] = {
    "official_signing",
    "agrees_terms",
    "submits_bid",
    "medical_scheduled",
    "contract_extension",
    "transfer_denied",
    "inquiry_made",
    "transfer_linked",
}


@dataclass
class ClaimValidationResult:
    """Outcome of validating an extracted claim triple."""

    is_valid: bool
    reasons: list[str] = field(default_factory=list)
    requires_human_review: bool = False


class ClaimSchemaValidator:
    """Deterministic validator verifying claim schema completeness and provenance."""

    @classmethod
    def validate_claim_triple(
        cls,
        triple_data: dict[str, Any],
        source_text: str | None = None,
        min_confidence: float = 0.50,
    ) -> ClaimValidationResult:
        reasons: list[str] = []
        requires_review = False

        # 1. Check predicate validity
        predicate = triple_data.get("predicate")
        if not predicate:
            reasons.append("Missing predicate in claim record.")
            requires_review = True
        elif predicate not in APPROVED_PREDICATES:
            reasons.append(f"Invalid predicate '{predicate}'. Must be one of {sorted(APPROVED_PREDICATES)}.")
            requires_review = True

        # 2. Check subject entity resolution
        subject_id = triple_data.get("subject_id")
        subject_name = triple_data.get("subject_name")
        if not subject_id and not subject_name:
            reasons.append("Claim lacks a resolved subject entity (player or manager).")
            requires_review = True

        # 3. Check evidence span presence
        evidence_span = triple_data.get("evidence_span")
        if not evidence_span or not str(evidence_span).strip():
            reasons.append("Claim is missing a mandatory verbatim evidence span.")
            requires_review = True
        elif source_text and str(evidence_span) not in source_text:
            reasons.append("Evidence span is not a verbatim substring of source document.")
            requires_review = True

        # 4. Check extraction confidence threshold
        confidence = float(triple_data.get("confidence", 1.0))
        if confidence < min_confidence:
            reasons.append(f"Extraction confidence ({confidence:.2f}) below threshold ({min_confidence:.2f}).")
            requires_review = True

        is_valid = len(reasons) == 0
        return ClaimValidationResult(
            is_valid=is_valid,
            reasons=reasons,
            requires_human_review=requires_review,
        )
