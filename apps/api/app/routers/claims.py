import json
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from packages.common.models import (
    Claim,
    ClaimAttribution,
    EntityType,
    Event,
    EventEntity,
    EventFirstReport,
    EventStatus,
)
from packages.database.models import ClaimModel, SourceModel
from packages.database.repository import LedgerRepository
from packages.database.session import get_db

router = APIRouter(prefix="/claims", tags=["claims"])


def slugify_name(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    return re.sub(r"[-\s]+", "-", s)


def parse_claim_attribution(raw: str) -> ClaimAttribution:
    r = (raw or "").lower().strip()
    if r in {"original", "first_party"}:
        return ClaimAttribution.ORIGINAL
    elif r in {"conflicting", "disputed"}:
        return ClaimAttribution.CONFLICTING
    return ClaimAttribution.CORROBORATING


class ClaimWithEvent(BaseModel):
    claim: Claim
    event: Event


@router.get("/by-event/{event_id}", response_model=list[Claim])
def list_claims_for_event(
    event_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve all claims associated with an event, newest first."""
    claim_models = LedgerRepository.list_claims(session=db, event_id=event_id)
    result: list[Claim] = []
    for cm in claim_models:
        result.append(
            Claim(
                id=cm.id,
                event_id=cm.event_id,
                outlet=cm.source.name if cm.source else "Unknown",
                reporter=cm.reporter,
                text=cm.claim_text,
                timestamp=cm.timestamp,
                attribution=parse_claim_attribution(cm.attribution),
                language=cm.language,
                url=cm.original_url,
                is_superseded=cm.is_superseded,
                superseded_by=cm.superseded_by,
            )
        )
    return result


@router.get("/by-source/{subject_slug}", response_model=list[ClaimWithEvent])
def list_claims_by_source(
    subject_slug: str,
    db: Session = Depends(get_db),
):
    """Retrieve all claims and parent events associated with an outlet or reporter."""
    normalized = subject_slug.replace("-", " ").strip().lower()

    # Find matching source
    sources = db.query(SourceModel).all()
    target_source = None
    for s in sources:
        if s.name.lower() == normalized or s.id == subject_slug or slugify_name(s.name) == subject_slug or s.id == f"src-{subject_slug}":
            target_source = s
            break

    target_name = target_source.name if target_source else normalized
    target_id = target_source.id if target_source else subject_slug

    claims = (
        db.query(ClaimModel)
        .filter(
            (ClaimModel.source_id == target_id)
            | (ClaimModel.reporter == target_name)
            | (ClaimModel.reporter_id == target_id)
            | (ClaimModel.source.has(SourceModel.name.ilike(target_name)))
        )
        .order_by(ClaimModel.timestamp.desc())
        .limit(100)
        .all()
    )

    results: list[ClaimWithEvent] = []
    for cm in claims:
        em = cm.event
        if not em:
            continue

        rationale_raw = json.loads(em.evidence_rationale_json) if em.evidence_rationale_json else []
        entities = [EventEntity(name=e.name, type=EntityType(e.entity_type)) for e in em.entities]
        first_rep = (
            EventFirstReport(
                outlet=em.first_reported_outlet,
                lead_time_minutes=em.first_reported_lead_minutes,
            )
            if em.first_reported_outlet
            else None
        )
        event_obj = Event(
            id=em.id,
            headline=em.headline,
            status=EventStatus(em.status),
            independent_sources=em.independent_sources,
            sport=em.sport,
            competition=em.competition,
            updated_at=em.updated_at,
            summary=em.summary,
            first_reported_by=first_rep,
            entities=entities,
            source_url=em.source_url,
            status_note=em.status_note,
            evidence_rationale=[b["text"] if isinstance(b, dict) else str(b) for b in rationale_raw],
        )

        claim_obj = Claim(
            id=cm.id,
            event_id=cm.event_id,
            outlet=cm.source.name if cm.source else "Unknown",
            reporter=cm.reporter,
            text=cm.claim_text,
            timestamp=cm.timestamp,
            attribution=parse_claim_attribution(cm.attribution),
            language=cm.language,
            url=cm.original_url,
            is_superseded=cm.is_superseded,
            superseded_by=cm.superseded_by,
        )

        results.append(ClaimWithEvent(claim=claim_obj, event=event_obj))

    return results


@router.get("/corrections", response_model=list[ClaimWithEvent])
def list_corrections(
    db: Session = Depends(get_db),
):
    """Retrieve all claims and events that have been superseded, corrected, or marked disputed."""
    from packages.database.models import EventModel

    claims = (
        db.query(ClaimModel)
        .join(EventModel, ClaimModel.event_id == EventModel.id)
        .filter((ClaimModel.is_superseded.is_(True)) | (EventModel.status.in_(["corrected", "disputed"])))
        .order_by(ClaimModel.timestamp.desc())
        .limit(50)
        .all()
    )

    results: list[ClaimWithEvent] = []
    for cm in claims:
        em = cm.event
        if not em:
            continue

        rationale_raw = json.loads(em.evidence_rationale_json) if em.evidence_rationale_json else []
        entities = [EventEntity(name=e.name, type=EntityType(e.entity_type)) for e in em.entities]
        first_rep = (
            EventFirstReport(
                outlet=em.first_reported_outlet,
                lead_time_minutes=em.first_reported_lead_minutes,
            )
            if em.first_reported_outlet
            else None
        )
        event_obj = Event(
            id=em.id,
            headline=em.headline,
            status=EventStatus(em.status),
            independent_sources=em.independent_sources,
            sport=em.sport,
            competition=em.competition,
            updated_at=em.updated_at,
            summary=em.summary,
            first_reported_by=first_rep,
            entities=entities,
            source_url=em.source_url,
            status_note=em.status_note,
            evidence_rationale=[b["text"] if isinstance(b, dict) else str(b) for b in rationale_raw],
        )

        claim_obj = Claim(
            id=cm.id,
            event_id=cm.event_id,
            outlet=cm.source.name if cm.source else "Unknown",
            reporter=cm.reporter,
            text=cm.claim_text,
            timestamp=cm.timestamp,
            attribution=parse_claim_attribution(cm.attribution),
            language=cm.language,
            url=cm.original_url,
            is_superseded=cm.is_superseded,
            superseded_by=cm.superseded_by,
        )
        results.append(ClaimWithEvent(claim=claim_obj, event=event_obj))

    return results
