import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from packages.ai.budget import CostTracker
from packages.database.session import get_db
from workers.pipeline.evidence_lane import EvidenceLaneWorker
from workers.pipeline.speed_lane import SpeedLaneWorker

router = APIRouter(prefix="/ingest", tags=["ingest"])
shared_cost_tracker = CostTracker()


@router.post("/claim")
def ingest_claim(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """Ingests a raw transfer report into the two-lane pipeline."""
    try:
        # Step 1: Speed lane (<90s SLA)
        speed_worker = SpeedLaneWorker(session=db)
        speed_result = speed_worker.process_raw_article(payload)

        # Idempotent return for already-recorded duplicate articles
        if speed_result.get("action") == "idempotent_noop":
            return {
                "status": "already_recorded",
                "event_id": speed_result["event_id"],
                "claim_id": speed_result["claim_id"],
                "headline": speed_result["headline"],
                "event_status": speed_result["status"],
                "speed_lane_latency_ms": speed_result["latency_ms"],
            }

        # Step 2: Evidence lane (<6min SLA)
        trace_id = f"trc-{uuid.uuid4().hex[:10]}"
        evidence_worker = EvidenceLaneWorker(session=db, cost_tracker=shared_cost_tracker)
        evidence_result = evidence_worker.evaluate_and_publish_event(
            event_id=speed_result["event_id"],
            trace_id=trace_id,
        )

        is_evidence_attached = speed_result.get("action") == "evidence_attached"
        return {
            "status": "evidence_attached" if is_evidence_attached else "success",
            "event_id": speed_result["event_id"],
            "claim_id": speed_result["claim_id"],
            "evidence_id": speed_result.get("evidence_id"),
            "similarity_to_root": speed_result.get("similarity_to_root"),
            "reporter": speed_result.get("reporter"),
            "reporter_id": speed_result.get("reporter_id"),
            "attribution_type": speed_result.get("attribution_type"),
            "headline": speed_result["headline"],
            "event_status": evidence_result["status"],
            "evidence_bullets": evidence_result["reasoning"],
            "speed_lane_latency_ms": speed_result["latency_ms"],
            "evidence_lane_duration_sec": evidence_result["duration_sec"],
            "trace_id": trace_id,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
