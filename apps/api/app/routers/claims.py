import csv
import io
import json
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
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
from packages.database.billing_repository import BillingRepository
from packages.database.models import ClaimModel, SourceModel
from packages.database.repository import LedgerRepository
from packages.database.session import get_db

from ..security.api_keys import APIClient, get_api_client

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


class StructuredClaimDetail(BaseModel):
    id: str
    event_id: str
    outlet: str
    reporter: str | None
    text: str
    subject_id: str | None
    predicate: str | None
    object_id: str | None
    evidence_span: str | None
    resolvable: bool
    resolution_class: str
    attribution: str
    attribution_type: str
    language: str
    original_url: str
    is_superseded: bool
    superseded_by: str | None
    timestamp: datetime


@router.get("", response_model=list[StructuredClaimDetail])
def query_claims(
    subject_id: str | None = Query(default=None, description="Filter by subject entity ID"),
    predicate: str | None = Query(default=None, description="Filter by predicate"),
    object_id: str | None = Query(default=None, description="Filter by object entity ID"),
    attribution_type: str | None = Query(default=None, description="Filter by attribution type"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    client: APIClient = Depends(get_api_client),
    db: Session = Depends(get_db),
) -> list[StructuredClaimDetail]:
    """Public claims data API: query structured ledger claims with optional entity and predicate filters."""
    claims = LedgerRepository.query_claims(
        session=db,
        subject_id=subject_id,
        predicate=predicate,
        object_id=object_id,
        attribution_type=attribution_type,
        limit=limit,
        offset=offset,
    )
    return [
        StructuredClaimDetail(
            id=c.id,
            event_id=c.event_id,
            outlet=c.source.name if c.source else "Unknown",
            reporter=c.reporter,
            text=c.claim_text,
            subject_id=c.subject_id,
            predicate=c.predicate,
            object_id=c.object_id,
            evidence_span=c.evidence_span,
            resolvable=c.resolvable,
            resolution_class=c.resolution_class,
            attribution=c.attribution,
            attribution_type=c.attribution_type,
            language=c.language,
            original_url=c.original_url,
            is_superseded=c.is_superseded,
            superseded_by=c.superseded_by,
            timestamp=c.timestamp,
        )
        for c in claims
    ]


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


EXPORT_FIELDS = [
    "id",
    "event_id",
    "outlet",
    "reporter",
    "text",
    "attribution",
    "language",
    "url",
    "timestamp",
    "is_superseded",
]


def _claim_export_row(cm: ClaimModel) -> dict:
    return {
        "id": cm.id,
        "event_id": cm.event_id,
        "outlet": cm.source.name if cm.source else "Unknown",
        "reporter": cm.reporter,
        "text": cm.claim_text,
        "attribution": cm.attribution,
        "language": cm.language,
        "url": cm.original_url,
        "timestamp": cm.timestamp.isoformat(),
        "is_superseded": cm.is_superseded,
    }


@router.get("/export")
def export_claims(
    email: str = Query(..., description="Email to check Pro entitlement against"),
    event_id: str | None = Query(default=None, description="Export claims for a single event"),
    subject_slug: str | None = Query(default=None, description="Export claims for an outlet or reporter"),
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    db: Session = Depends(get_db),
):
    """CSV/JSON claim-ledger export — a Pro-only feature (Handbook §18.3/§18.4).

    Never trusts a client-supplied entitlement flag: looks up the real persisted
    entitlement for the given email on every call.
    """
    if not event_id and not subject_slug:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide event_id or subject_slug")

    record = BillingRepository.get_entitlement_by_email(db, email)
    if record is None or not record.is_pro:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Export is a Pro feature. Upgrade at /pro to export the claim ledger.",
        )

    if event_id:
        claim_models = LedgerRepository.list_claims(session=db, event_id=event_id)
    else:
        normalized = (subject_slug or "").replace("-", " ").strip().lower()
        sources = db.query(SourceModel).all()
        target_source = next(
            (s for s in sources if s.name.lower() == normalized or s.id == subject_slug or slugify_name(s.name) == subject_slug),
            None,
        )
        target_name = target_source.name if target_source else normalized
        target_id = target_source.id if target_source else subject_slug
        claim_models = (
            db.query(ClaimModel)
            .filter((ClaimModel.source_id == target_id) | (ClaimModel.reporter == target_name) | (ClaimModel.reporter_id == target_id))
            .order_by(ClaimModel.timestamp.desc())
            .all()
        )

    rows = [_claim_export_row(cm) for cm in claim_models]
    filename_scope = event_id or subject_slug

    if format == "json":
        return Response(
            content=json.dumps(rows, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="claims_{filename_scope}.json"'},
        )

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="claims_{filename_scope}.csv"'},
    )
