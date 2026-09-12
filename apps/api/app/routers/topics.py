import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from packages.common.entities import default_entity_graph
from packages.common.models import (
    EntityType,
    Event,
    EventEntity,
    EventFirstReport,
    EventStatus,
)
from packages.database.models import EventModel
from packages.database.session import get_db

router = APIRouter(prefix="/topics", tags=["topics"])


class TopicDetail(BaseModel):
    slug: str
    name: str
    type: EntityType
    events: list[Event] = []


@router.get("/{slug}", response_model=TopicDetail)
def get_topic(
    slug: str,
    db: Session = Depends(get_db),
):
    """Retrieve entity dossier and related ledger events."""
    normalized = slug.replace("-", " ").strip().lower()
    entity = default_entity_graph.resolve_alias(normalized)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Topic {slug} not found in entity graph")

    # Find events with matching entity
    all_events = db.query(EventModel).all()
    matched_events: list[Event] = []
    for em in all_events:
        entity_names = [e.name.lower() for e in em.entities]
        if entity.name.lower() in entity_names:
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
            matched_events.append(
                Event(
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
            )

    return TopicDetail(
        slug=slug,
        name=entity.name,
        type=entity.type,
        events=matched_events,
    )
