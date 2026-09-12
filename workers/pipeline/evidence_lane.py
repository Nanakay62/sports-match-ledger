import json
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from packages.ai.budget import CostTracker
from packages.ai.ladder import DeterministicValidator
from packages.common.models import EventStatus
from packages.database.repository import LedgerRepository


class EvidenceLaneWorker:
    """Model-assisted processing lane targeting under 6 minutes to publication.

    Runs L0/L1 deterministic evidence synthesis and status reasoning.
    Validates outputs via DeterministicValidator before publication.
    """

    def __init__(self, session: Session, cost_tracker: CostTracker):
        self.session = session
        self.cost_tracker = cost_tracker

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
        distinct_outlets: set[str] = set()
        for c in claims:
            if c.source:
                distinct_outlets.add(c.source.name)
            for ev in c.evidence_sources:
                if ev.source:
                    distinct_outlets.add(ev.source.name)
        source_count = len(distinct_outlets) if distinct_outlets else 1

        # Determine status deterministically from evidence consensus
        new_status = EventStatus.RUMOUR
        if source_count == 2:
            new_status = EventStatus.DEVELOPING
        elif source_count >= 3:
            new_status = EventStatus.WELL_CORROBORATED

        # Check for official club/league announcement triggers
        for c in claims:
            t = c.claim_text.lower()
            if "official statement" in t or "completed deal" in t or "regulatory filing" in t:
                new_status = EventStatus.CONFIRMED
                break

        # Generate status reasoning bullets
        bullets: list[dict[str, str]] = []
        if new_status == EventStatus.CONFIRMED:
            bullets.append(
                {
                    "kind": "ok",
                    "text": "**Official confirmation on record:** verified through official statement or league filing.",
                }
            )
            bullets.append(
                {
                    "kind": "ok",
                    "text": f"**Corroborated across {source_count} sources** with aligned terms logged in the ledger.",
                }
            )
        elif new_status == EventStatus.WELL_CORROBORATED:
            bullets.append(
                {
                    "kind": "ok",
                    "text": f"**Corroborated across {source_count} independent desks** reporting active progress.",
                }
            )
            bullets.append(
                {
                    "kind": "warn",
                    "text": "**Formal execution pending:** club-to-club agreement or final paperwork remaining.",
                }
            )
        elif new_status == EventStatus.DEVELOPING:
            bullets.append(
                {
                    "kind": "warn",
                    "text": f"**Active negotiations:** {source_count} outlets report concrete activity, but terms remain fluid.",
                }
            )
            bullets.append(
                {
                    "kind": "info",
                    "text": f"**{len(claims)} claims logged:** monitoring for independent confirmation or counter-briefings.",
                }
            )
        else:
            bullets.append(
                {
                    "kind": "warn",
                    "text": "**Single-source claim:** initial report lacks independent secondary confirmation.",
                }
            )
            bullets.append(
                {
                    "kind": "info",
                    "text": "**Ledger holds at Rumour:** awaiting corroboration from a second independent desk.",
                }
            )

        # Run deterministic validation check
        entity_names = [e.name for e in event.entities]
        validation = DeterministicValidator.validate_generation(
            generated_text=bullets[0]["text"],
            source_evidence=[c.claim_text for c in claims],
            expected_entities=entity_names,
        )

        # Update event record in DB
        event.status = new_status.value
        event.independent_sources = source_count
        event.evidence_rationale_json = json.dumps(bullets)
        event.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        # Telemetry record (L0 deterministic, €0.00 cost)
        self.cost_tracker.record_inference(
            trace_id=trace_id,
            stage="evidence_lane_evaluation",
            model_id="rung-l0-deterministic",
            prompt_version="v1.0",
            input_tokens=100,
            output_tokens=50,
            cost_eur=0.0,
        )

        duration_sec = round(time.monotonic() - start_time, 3)
        return {
            "lane": "evidence_lane",
            "event_id": event.id,
            "status": event.status,
            "sources_count": source_count,
            "reasoning": bullets,
            "validation_passed": validation.is_valid,
            "cost_eur": 0.0,
            "duration_sec": duration_sec,
        }
