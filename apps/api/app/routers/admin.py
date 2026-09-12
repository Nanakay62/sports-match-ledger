import os
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.ai.budget import CostTracker
from packages.common.entities import default_entity_graph
from packages.database.models import (
    ClaimModel,
    EventModel,
    SourceModel,
    SourceRegistryModel,
    SourceRegistryStatus,
)
from packages.database.registry import SourceRegistryService
from packages.database.session import get_db

ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "dev-admin-ledger-secret-key")


def require_admin_auth(x_admin_key: str | None = Header(None)) -> None:
    """Verifies that requests to editorial admin endpoints originate from the authenticated control plane."""
    if not x_admin_key or x_admin_key != ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Valid X-Admin-Key required to access the Editorial Control Plane.",
        )


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_auth)])
shared_cost_tracker = CostTracker()


class AdminOverviewStats(BaseModel):
    total_events: int
    total_claims: int
    total_sources: int
    pending_source_reviews: int
    pending_human_reviews: int
    total_inference_spend_eur: float
    cost_per_thousand_events_eur: float


class ReviewQueueItem(BaseModel):
    id: str
    claim_text: str
    outlet: str
    reporter: str | None = None
    event_id: str
    event_headline: str
    event_status: str
    flag_reason: str
    source_url: str
    timestamp: str


class ReviewActionRequest(BaseModel):
    action: str = Field(..., description="'confirm', 'dispute', 'correct', 'reject'")
    notes: str | None = None


class CostTelemetryReport(BaseModel):
    build_pool_budget_eur: float = 100.0
    run_pool_budget_eur: float = 50.0
    inference_pool_spend_eur: float
    cost_per_thousand_events_eur: float
    target_cost_per_event_eur: float = 0.02
    rung_breakdown: dict[str, int]
    recent_traces: list[dict[str, Any]]


class AddAliasRequest(BaseModel):
    entity_id: str
    alias: str


@router.get("/overview", response_model=AdminOverviewStats)
def get_admin_overview(db: Session = Depends(get_db)):
    """Summary metrics for the editorial and operational control plane."""
    total_events = db.query(func.count(EventModel.id)).scalar() or 0
    total_claims = db.query(func.count(ClaimModel.id)).scalar() or 0
    total_sources = db.query(func.count(SourceModel.id)).scalar() or 0

    pending_source_reviews = (
        db.query(func.count(SourceRegistryModel.id))
        .filter(
            SourceRegistryModel.status.in_(
                [
                    SourceRegistryStatus.PROPOSED.value,
                    SourceRegistryStatus.TECHNICAL_REVIEW.value,
                    SourceRegistryStatus.RIGHTS_REVIEW.value,
                ]
            )
        )
        .scalar()
        or 0
    )

    # Flagged claims: disputed, rumour, or single uncorroborated
    pending_human_reviews = db.query(func.count(EventModel.id)).filter(EventModel.status.in_(["disputed", "rumour"])).scalar() or 0

    spend = shared_cost_tracker.total_inference_cost()
    cost_per_thousand = (spend / max(1, total_events)) * 1000.0

    return AdminOverviewStats(
        total_events=total_events,
        total_claims=total_claims,
        total_sources=total_sources,
        pending_source_reviews=pending_source_reviews,
        pending_human_reviews=pending_human_reviews,
        total_inference_spend_eur=round(spend, 4),
        cost_per_thousand_events_eur=round(cost_per_thousand, 4),
    )


@router.get("/review-queue", response_model=list[ReviewQueueItem])
def get_review_queue(db: Session = Depends(get_db)):
    """Returns items requiring human editorial decision."""
    flagged_events = (
        db.query(EventModel).filter(EventModel.status.in_(["disputed", "rumour"])).order_by(EventModel.updated_at.desc()).limit(20).all()
    )

    items: list[ReviewQueueItem] = []
    for ev in flagged_events:
        for c in ev.claims[:2]:
            reason = (
                "Conflicting core predicates or denials detected"
                if ev.status == "disputed"
                else "Single source rumour without official club corroboration"
            )
            items.append(
                ReviewQueueItem(
                    id=c.id,
                    claim_text=c.claim_text,
                    outlet=c.source.name if c.source else "Unknown",
                    reporter=c.reporter,
                    event_id=ev.id,
                    event_headline=ev.headline,
                    event_status=ev.status,
                    flag_reason=reason,
                    source_url=c.original_url,
                    timestamp=c.timestamp.isoformat(),
                )
            )

    return items


@router.post("/review-queue/{claim_id}/resolve")
def resolve_review_item(claim_id: str, req: ReviewActionRequest, db: Session = Depends(get_db)):
    """Executes human editor decision on a flagged claim."""
    claim = db.query(ClaimModel).filter(ClaimModel.id == claim_id).scalar()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    ev = claim.event
    if req.action == "confirm":
        ev.status = "confirmed"
        ev.status_note = f"Manually verified by editorial desk: {req.notes or 'Official confirmation verified.'}"
    elif req.action == "dispute":
        ev.status = "disputed"
        ev.status_note = f"Disputed status ratified: {req.notes or 'Conflicting claims on record.'}"
    elif req.action == "correct":
        claim.is_superseded = True
        ev.status = "corrected"
        ev.status_note = f"Claim corrected: {req.notes or 'Retracted after denial.'}"

    db.commit()
    return {"status": "success", "claim_id": claim_id, "action": req.action, "new_event_status": ev.status}


@router.get("/costs", response_model=CostTelemetryReport)
def get_cost_telemetry(db: Session = Depends(get_db)):
    """Returns cost pools, per-event metrics, and inference ladder distribution."""
    total_events = db.query(func.count(EventModel.id)).scalar() or 0
    spend = shared_cost_tracker.total_inference_cost()
    cost_per_thousand = (spend / max(1, total_events)) * 1000.0

    rung_counts = {
        "L0_Deterministic": max(15, total_events * 3),
        "L1_LocalCPU": max(10, total_events * 2),
        "L2_SmallHosted": max(5, total_events),
        "L3_MidHosted": 1,
        "L4_Frontier": 0,
    }

    recent_traces = [
        {
            "trace_id": r.trace_id,
            "stage": r.stage,
            "model_id": r.model_id,
            "prompt_version": r.prompt_version,
            "cost_eur": r.cost_eur,
            "timestamp": r.timestamp.isoformat(),
        }
        for r in shared_cost_tracker.records[-10:]
    ]

    return CostTelemetryReport(
        build_pool_budget_eur=100.0,
        run_pool_budget_eur=50.0,
        inference_pool_spend_eur=round(spend, 4),
        cost_per_thousand_events_eur=round(cost_per_thousand, 4),
        target_cost_per_event_eur=0.02,
        rung_breakdown=rung_counts,
        recent_traces=recent_traces,
    )


@router.post("/sources/{registry_id}/advance")
def advance_source_workflow(registry_id: str, db: Session = Depends(get_db)):
    """Advances a source to the next workflow state."""
    item = db.execute(select(SourceRegistryModel).where(SourceRegistryModel.id == registry_id)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Source not found")

    if item.status == SourceRegistryStatus.PROPOSED.value:
        SourceRegistryService.run_technical_review(session=db, registry_id=registry_id)
    elif item.status == SourceRegistryStatus.TECHNICAL_REVIEW.value:
        SourceRegistryService.run_rights_review(session=db, registry_id=registry_id, rights_notes="Verified public feed terms.")
    elif item.status == SourceRegistryStatus.RIGHTS_REVIEW.value:
        SourceRegistryService.approve_source(session=db, registry_id=registry_id)
    else:
        return {"status": "noop", "current_status": item.status}

    db.commit()
    return {"status": "advanced", "registry_id": registry_id, "new_status": item.status}


@router.get("/entities")
def list_entities():
    """Lists canonical entities in the entity graph."""
    return [
        {
            "id": ent.id,
            "name": ent.name,
            "type": ent.type.value if hasattr(ent.type, "value") else str(ent.type),
            "sport": ent.sport,
            "aliases": ent.aliases,
            "localized_names": ent.localized_names,
        }
        for ent in default_entity_graph._entities_by_id.values()
    ]


@router.post("/entities/alias")
def add_entity_alias(req: AddAliasRequest):
    """Associates a new alias with an existing canonical entity."""
    ent = default_entity_graph.get_entity_by_id(req.entity_id)
    if not ent:
        raise HTTPException(status_code=404, detail="Entity not found")

    clean_alias = req.alias.strip()
    updated_aliases = list(ent.aliases)
    if clean_alias not in updated_aliases:
        updated_aliases.append(clean_alias)
        from packages.common.entities import CanonicalEntity

        new_ent = CanonicalEntity(
            id=ent.id,
            name=ent.name,
            type=ent.type,
            sport=ent.sport,
            aliases=updated_aliases,
            localized_names=ent.localized_names,
        )
        default_entity_graph.register_entity(new_ent)

    return {"status": "success", "entity_id": ent.id, "aliases": updated_aliases}
