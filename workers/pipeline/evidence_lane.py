import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from packages.ai.budget import CostTracker
from packages.ai.claim_validator import ClaimSchemaValidator
from packages.ai.evidence_package import EvidencePackageBuilder
from packages.ai.ladder import DeterministicValidator
from packages.ai.summarizer import StructuredEvidenceSummarizer
from packages.common.validation import DeterministicValidationEngine, ValidationClaimInput
from packages.database.repository import LedgerRepository
from packages.notifications.dispatcher import NotificationDispatcher
from workers.pipeline.claim_extractor import StructuredClaimExtractor
from workers.pipeline.review_router import HumanReviewRouter

logger = logging.getLogger(__name__)


class EvidenceLaneWorker:
    """Model-assisted processing lane targeting under 6 minutes to publication.

    Runs L0/L1 deterministic evidence synthesis and status reasoning.
    Validates outputs via DeterministicValidator before publication.
    """

    def __init__(self, session: Session, cost_tracker: CostTracker, notification_dispatcher: NotificationDispatcher | None = None):
        self.session = session
        self.cost_tracker = cost_tracker
        self.notification_dispatcher = notification_dispatcher or NotificationDispatcher()

    def evaluate_and_publish_event(
        self,
        event_id: str,
        trace_id: str,
    ) -> dict[str, Any]:
        start_time = time.monotonic()
        event = LedgerRepository.get_event(self.session, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found in ledger")

        claims = LedgerRepository.list_claims(self.session, event_id)

        # Convert claims to 8-factor validation input
        validation_claims: list[ValidationClaimInput] = []
        for c in claims:
            outlet_name = c.source.name if c.source else "Unknown"
            rep_wilson: float | None = None
            if c.source and c.source.wilson_lower_bound is not None:
                rep_wilson = c.source.wilson_lower_bound

            fee_val: float | None = None
            if c.qualifiers:
                try:
                    q_data = json.loads(c.qualifiers) if isinstance(c.qualifiers, str) else c.qualifiers
                    if isinstance(q_data, dict) and "fee_eur_millions" in q_data:
                        fee_val = float(q_data["fee_eur_millions"])
                except Exception:
                    pass
            if fee_val is None:
                fee_val = StructuredClaimExtractor.extract_fee(c.claim_text)

            validation_claims.append(
                ValidationClaimInput(
                    claim_id=c.id,
                    outlet_name=outlet_name,
                    authority_rank=3,
                    reporter_name=c.reporter,
                    reporter_wilson_score=rep_wilson,
                    predicate=c.predicate,
                    attribution_type=c.attribution_type or "first_party",
                    fee_eur=fee_val,
                    timestamp=c.timestamp or datetime.now(timezone.utc),
                    is_superseded=c.is_superseded,
                )
            )

        # Evaluate using the 8 deterministic validation factors
        val_result = DeterministicValidationEngine.evaluate(validation_claims)
        bullets = list(val_result.rationale_bullets)

        # Check for mandatory human review triggers across all claims
        for c in claims:
            routing = HumanReviewRouter.classify_claim_context(
                claim_text=c.claim_text,
                source_sample_size=c.source.sample_size if c.source else 0,
                has_contradiction=val_result.has_contradiction,
            )
            if routing.requires_review:
                bullets.append(
                    {
                        "kind": "warn",
                        "text": f"**Editorial review triggered ({routing.priority}):** {routing.reason}",
                    }
                )
                break

            # Deterministic claim schema validation gate (§5.2)
            triple_dict = {
                "subject_id": c.subject_id,
                "predicate": c.predicate,
                "object_id": c.object_id,
                "evidence_span": c.evidence_span,
                "confidence": 1.0 if (c.subject_id and c.evidence_span) else 0.40,
            }
            claim_validation = ClaimSchemaValidator.validate_claim_triple(triple_dict)
            if not claim_validation.is_valid and claim_validation.requires_human_review:
                bullets.append(
                    {
                        "kind": "warn",
                        "text": f"**Claim schema validation review ({c.id[:8]}):** {'; '.join(claim_validation.reasons)}",
                    }
                )
                break

        # Build isolated EvidencePackage (Handbook §7: physical isolation from raw article text)
        evidence_package = EvidencePackageBuilder.build_from_event(
            event=event,
            claims=claims,
            target_lang="en",
            has_contradiction=val_result.has_contradiction,
        )

        # Generate evidence-grounded summary with citations and zero-cost cache
        summarizer = StructuredEvidenceSummarizer(cost_tracker=self.cost_tracker)
        summary_res = summarizer.summarize(package=evidence_package, trace_id=trace_id)

        # Deterministically validate generated output against the isolated EvidencePackage
        package_validation = DeterministicValidator.validate_package_generation(
            generated_text=summary_res.summary_text,
            package=evidence_package,
        )

        # Update event record in DB
        previous_status = event.status
        event.status = val_result.status.value
        event.independent_sources = val_result.independent_roots
        event.evidence_rationale_json = json.dumps(bullets)
        if summary_res.summary_text:
            event.summary = summary_res.summary_text
        event.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        # Handbook §18.1: notify watchlist subscribers — real-time for Pro, queued
        # into the daily digest for Free. Never blocks or fails publication itself.
        if previous_status != event.status:
            try:
                self.notification_dispatcher.dispatch_status_change(
                    session=self.session,
                    event_id=event.id,
                    headline=event.headline,
                    old_status=previous_status,
                    new_status=event.status,
                )
            except Exception as exc:
                logger.warning(f"Notification dispatch failed for event {event.id}: {exc}")

        duration_sec = round(time.monotonic() - start_time, 3)
        return {
            "lane": "evidence_lane",
            "event_id": event.id,
            "status": event.status,
            "package_id": evidence_package.package_id,
            "headline": summary_res.headline,
            "summary": summary_res.summary_text,
            "cited_facts": summary_res.cited_fact_ids,
            "sources_count": val_result.independent_roots,
            "reasoning": bullets,
            "validation_passed": package_validation.is_valid and summary_res.validation_passed,
            "validation_reasons": package_validation.reasons,
            "cache_hit": summary_res.cache_hit,
            "cost_eur": summary_res.cost_eur,
            "duration_sec": duration_sec,
        }
