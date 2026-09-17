"""Authority Outcome Resolver.

Automated scheduled worker matching authoritative real-world outcomes
(Rank 1: Official Club Announcements, Rank 2: Official League Registrations)
against append-only claims in the Accountability Ledger.

Enforces Handbook §5.3 rules:
- Auto-resolves only at Authority Rank 1–2.
- Aggregated claims (attribution_type == 'aggregation') are excluded from reliability scoring.
- Recomputes Wilson lower bound reliability scores upon resolution.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.common.scoring import evaluate_reliability
from packages.database.models import ClaimModel, PipelineJobModel, ResolutionModel, SourceModel
from packages.database.queue import JobQueueService
from packages.database.repository import LedgerRepository
from workers.pipeline.claim_extractor import StructuredClaimExtractor


class OutcomeResolverWorker:
    """Matches confirmed outcomes to ledger claims and updates reliability scores."""

    @staticmethod
    def resolve_claim(
        session: Session,
        claim: ClaimModel,
        outcome: str,
        authority_rank: int,
        authority_source_url: str,
        notes: str | None = None,
        entity_correct: bool | None = None,
        direction_correct: bool | None = None,
        timing_correct: bool | None = None,
        fee_correct: bool | None = None,
    ) -> ResolutionModel:
        """Appends an outcome resolution to a claim and updates subject reliability metrics."""
        # Verify claim is not already resolved
        existing_res = session.execute(select(ResolutionModel).where(ResolutionModel.claim_id == claim.id)).scalar_one_or_none()
        if existing_res:
            raise ValueError(f"Claim {claim.id} is already resolved by resolution {existing_res.id}")

        if authority_rank not in {1, 2, 3, 4, 5}:
            raise ValueError(f"Invalid authority rank: {authority_rank}. Must be 1-5.")

        now = datetime.now(timezone.utc)
        res_id = f"res-{uuid.uuid4().hex[:12]}"
        resolution = ResolutionModel(
            id=res_id,
            claim_id=claim.id,
            outcome=outcome,
            authority_rank=authority_rank,
            authority_source_url=authority_source_url,
            notes=notes or f"Resolved by Authority Rank {authority_rank} verification.",
            entity_correct=entity_correct,
            direction_correct=direction_correct,
            timing_correct=timing_correct,
            fee_correct=fee_correct,
            resolved_at=now,
        )
        session.add(resolution)

        is_aggregation = claim.attribution_type == "aggregation"

        # 1. Update publishing Outlet reliability
        if claim.source:
            source = claim.source
            if is_aggregation:
                source.sample_size_aggregation += 1
                if outcome == "correct":
                    source.correct_count_aggregation += 1
                agg_metrics = evaluate_reliability(
                    subject_name=source.name,
                    subject_type=source.source_type,
                    correct_count=source.correct_count_aggregation,
                    sample_size=source.sample_size_aggregation,
                )
                source.wilson_lower_bound_aggregation = agg_metrics.wilson_lower_bound
            else:
                source.sample_size += 1
                source.sample_size_original += 1
                if outcome == "correct":
                    source.correct_count += 1
                    source.correct_count_original += 1
                metrics = evaluate_reliability(
                    subject_name=source.name,
                    subject_type=source.source_type,
                    correct_count=source.correct_count,
                    sample_size=source.sample_size,
                )
                source.wilson_lower_bound = metrics.wilson_lower_bound
                orig_metrics = evaluate_reliability(
                    subject_name=source.name,
                    subject_type=source.source_type,
                    correct_count=source.correct_count_original,
                    sample_size=source.sample_size_original,
                )
                source.wilson_lower_bound_original = orig_metrics.wilson_lower_bound

        # 2. Update individual Reporter reliability if linked
        if claim.reporter_rel and claim.reporter_rel.primary_source_id:
            rep_source = session.execute(
                select(SourceModel).where(SourceModel.id == claim.reporter_rel.primary_source_id)
            ).scalar_one_or_none()
            if rep_source:
                if is_aggregation:
                    rep_source.sample_size_aggregation += 1
                    if outcome == "correct":
                        rep_source.correct_count_aggregation += 1
                    rep_agg_metrics = evaluate_reliability(
                        subject_name=rep_source.name,
                        subject_type="reporter",
                        correct_count=rep_source.correct_count_aggregation,
                        sample_size=rep_source.sample_size_aggregation,
                    )
                    rep_source.wilson_lower_bound_aggregation = rep_agg_metrics.wilson_lower_bound
                else:
                    rep_source.sample_size += 1
                    rep_source.sample_size_original += 1
                    if outcome == "correct":
                        rep_source.correct_count += 1
                        rep_source.correct_count_original += 1
                    rep_metrics = evaluate_reliability(
                        subject_name=rep_source.name,
                        subject_type="reporter",
                        correct_count=rep_source.correct_count,
                        sample_size=rep_source.sample_size,
                    )
                    rep_source.wilson_lower_bound = rep_metrics.wilson_lower_bound
                    rep_orig_metrics = evaluate_reliability(
                        subject_name=rep_source.name,
                        subject_type="reporter",
                        correct_count=rep_source.correct_count_original,
                        sample_size=rep_source.sample_size_original,
                    )
                    rep_source.wilson_lower_bound_original = rep_orig_metrics.wilson_lower_bound

        session.flush()
        return resolution

    @classmethod
    def resolve_from_authoritative_announcement(
        cls,
        session: Session,
        headline: str,
        body: str,
        authority_source_url: str,
        authority_rank: int = 1,
    ) -> dict[str, Any]:
        """Scans authoritative announcement (Rank 1-2) to auto-resolve matching pending claims."""
        if authority_rank not in {1, 2}:
            return {
                "status": "skipped",
                "reason": f"Auto-resolution requires Authority Rank 1 or 2 (received Rank {authority_rank}).",
            }

        # Deterministically extract the verified outcome fact
        triple = StructuredClaimExtractor.extract_structured_claim(headline=headline, body=body)

        if not triple.subject_id and not triple.object_id:
            return {
                "status": "skipped",
                "reason": "Could not extract canonical subject/object entities from authoritative announcement.",
            }

        # Find unresolved claims involving this subject and/or object
        unresolved = LedgerRepository.find_unresolved_claims(
            session=session,
            subject_id=triple.subject_id,
            object_id=triple.object_id,
        )

        resolved_count = 0
        resolutions_created: list[dict[str, str]] = []

        for pending_claim in unresolved:
            outcome: str | None = None
            explanation: str | None = None

            if triple.predicate == "official_signing":
                if pending_claim.predicate in {
                    "official_signing",
                    "agrees_terms",
                    "submits_bid",
                    "medical_scheduled",
                    "transfer_linked",
                }:
                    outcome = "correct"
                    explanation = f"Confirmed by official club announcement at {authority_source_url}."
                elif pending_claim.predicate == "transfer_denied":
                    outcome = "incorrect"
                    explanation = f"Contradicted by official signing announcement at {authority_source_url}."

            elif triple.predicate == "transfer_denied":
                if pending_claim.predicate == "transfer_denied":
                    outcome = "correct"
                    explanation = f"Official club denial verified at {authority_source_url}."
                elif pending_claim.predicate in {
                    "official_signing",
                    "agrees_terms",
                    "medical_scheduled",
                }:
                    outcome = "incorrect"
                    explanation = f"Formally denied by club official statement at {authority_source_url}."

            elif triple.predicate == "contract_extension":
                if pending_claim.predicate == "contract_extension":
                    outcome = "correct"
                    explanation = f"Contract renewal officially confirmed at {authority_source_url}."

            if outcome:
                # Calculate component correctness
                ent_corr = bool(pending_claim.subject_id and pending_claim.subject_id == triple.subject_id)
                if pending_claim.object_id and triple.object_id:
                    ent_corr = ent_corr and (pending_claim.object_id == triple.object_id)

                dir_corr = outcome == "correct"
                timing_corr = True

                fee_corr: bool | None = None
                if pending_claim.qualifiers and triple.qualifiers:
                    import json

                    q_data = json.loads(pending_claim.qualifiers) if isinstance(pending_claim.qualifiers, str) else pending_claim.qualifiers
                    claim_fee = q_data.get("fee_eur_millions") if isinstance(q_data, dict) else None
                    triple_fee = triple.qualifiers.get("fee_eur_millions")
                    if claim_fee is not None and triple_fee is not None and triple_fee > 0:
                        fee_corr = abs(float(claim_fee) - float(triple_fee)) / float(triple_fee) <= 0.15

                res = cls.resolve_claim(
                    session=session,
                    claim=pending_claim,
                    outcome=outcome,
                    authority_rank=authority_rank,
                    authority_source_url=authority_source_url,
                    notes=explanation,
                    entity_correct=ent_corr,
                    direction_correct=dir_corr,
                    timing_correct=timing_corr,
                    fee_correct=fee_corr,
                )
                resolved_count += 1
                resolutions_created.append(
                    {
                        "resolution_id": res.id,
                        "claim_id": pending_claim.id,
                        "outcome": outcome,
                        "outlet": pending_claim.source.name if pending_claim.source else "Unknown",
                    }
                )

        return {
            "status": "success",
            "authority_rank": authority_rank,
            "claims_matched": len(unresolved),
            "claims_resolved": resolved_count,
            "resolutions": resolutions_created,
        }

    @classmethod
    def check_rank3_consensus(
        cls,
        session: Session,
        claim: ClaimModel,
        min_independent_outlets: int = 3,
        min_delay_hours: float = 6.0,
    ) -> dict[str, Any]:
        """Rank 3: Checks whether 3+ independent tier-one outlets corroborate a claim after a delay window."""
        claim_time = claim.timestamp
        if claim_time.tzinfo is None:
            claim_time = claim_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age_hours = (now - claim_time).total_seconds() / 3600.0

        if age_hours < min_delay_hours:
            return {
                "status": "too_recent",
                "age_hours": round(age_hours, 2),
                "required_delay_hours": min_delay_hours,
                "hours_remaining": round(min_delay_hours - age_hours, 2),
            }

        # Collect distinct non-aggregation outlets
        distinct_outlets: set[str] = set()
        if claim.source and claim.attribution_type != "aggregation":
            distinct_outlets.add(claim.source.name)

        for ev in claim.evidence_sources:
            if ev.attribution_type != "aggregation" and ev.source:
                distinct_outlets.add(ev.source.name)

        if len(distinct_outlets) >= min_independent_outlets:
            return {
                "status": "eligible",
                "independent_count": len(distinct_outlets),
                "outlets": sorted(distinct_outlets),
                "authority_rank": 3,
            }

        return {
            "status": "insufficient_corroboration",
            "independent_count": len(distinct_outlets),
            "required_count": min_independent_outlets,
            "outlets": sorted(distinct_outlets),
        }

    @classmethod
    def resolve_rank3_consensus(
        cls,
        session: Session,
        claim: ClaimModel,
        outcome: str = "correct",
        authority_source_url: str = "consensus://tier1-corroboration",
        notes: str | None = None,
    ) -> ResolutionModel:
        """Resolves an eligible claim at Authority Rank 3 (delayed multi-outlet corroboration)."""
        consensus = cls.check_rank3_consensus(session=session, claim=claim)
        if consensus.get("status") != "eligible":
            raise ValueError(f"Claim {claim.id} is not eligible for Rank 3 resolution: {consensus}")

        return cls.resolve_claim(
            session=session,
            claim=claim,
            outcome=outcome,
            authority_rank=3,
            authority_source_url=authority_source_url,
            notes=notes or f"Resolved by Authority Rank 3 corroboration ({consensus['independent_count']} outlets).",
        )

    @classmethod
    def escalate_to_human_queue(
        cls,
        session: Session,
        claim: ClaimModel,
        reason: str = "Single uncorroborated outlet requiring human editorial review.",
    ) -> PipelineJobModel:
        """Rank 4: Escalates a single-outlet unconfirmed claim to the human review queue."""
        return JobQueueService.enqueue_job(
            session=session,
            lane="human_review",
            payload={
                "claim_id": claim.id,
                "event_id": claim.event_id,
                "outlet": claim.source.name if claim.source else "Unknown",
                "reporter": claim.reporter,
                "claim_text": claim.claim_text,
                "reason": reason,
                "authority_rank": 4,
            },
        )

    @classmethod
    def resolve_expired_deadline(
        cls,
        session: Session,
        claim: ClaimModel,
        deadline_days: int = 30,
    ) -> dict[str, Any]:
        """Rank 5: Auto-resolves unconfirmed rumours to did_not_occur after deadline expires."""
        existing = session.execute(select(ResolutionModel).where(ResolutionModel.claim_id == claim.id)).scalar_one_or_none()
        if existing:
            return {"status": "already_resolved", "resolution_id": existing.id, "outcome": existing.outcome}

        claim_time = claim.timestamp
        if claim_time.tzinfo is None:
            claim_time = claim_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age_days = (now - claim_time).total_seconds() / 86400.0

        if age_days < deadline_days:
            return {"status": "pending", "days_remaining": round(deadline_days - age_days, 1)}

        res = cls.resolve_claim(
            session=session,
            claim=claim,
            outcome="did_not_occur",
            authority_rank=5,
            authority_source_url="system://deadline-expiry",
            notes=f"Unresolved rumour deadline elapsed ({deadline_days} days). Auto-resolved as did_not_occur.",
        )
        return {
            "status": "resolved",
            "outcome": "did_not_occur",
            "authority_rank": 5,
            "resolution_id": res.id,
        }
