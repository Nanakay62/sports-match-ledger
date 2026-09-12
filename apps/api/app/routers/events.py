import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from packages.ai.translation import TranslationService
from packages.common.entities import GLOSSARY_VERSION
from packages.common.models import (
    EntityType,
    Event,
    EventEntity,
    EventFirstReport,
    EventStatus,
)
from packages.database.repository import LedgerRepository
from packages.database.session import get_db

router = APIRouter(prefix="/events", tags=["events"])
shared_translation_service = TranslationService()


def build_localized_event(em: Any, target_lang: str, db: Session) -> Event:
    """Constructs localized Event model, applying translation if target_lang differs from source."""
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

    # Determine source language from primary claim or default to English
    source_lang = "en"
    if em.claims and em.claims[0].language:
        source_lang = em.claims[0].language.lower()

    headline = em.headline
    summary = em.summary
    is_translated = False
    original_headline = None
    original_summary = None

    target_norm = (target_lang or "en").strip().lower()

    # Translate if target language differs from source
    if target_norm != source_lang:
        # 1. Check existing translation in repository
        tr = LedgerRepository.get_event_translation(
            session=db,
            event_id=em.id,
            language=target_norm,
            glossary_version=GLOSSARY_VERSION,
        )
        is_stale_stub = tr and (
            tr.headline.strip().lower() == em.headline.strip().lower() and tr.summary.strip().lower() == em.summary.strip().lower()
        )
        if tr and not is_stale_stub:
            headline = tr.headline
            summary = tr.summary
            is_translated = True
            original_headline = em.headline
            original_summary = em.summary
        else:
            # 2. Translate on demand via TranslationService
            try:
                entity_ids = [e.name for e in em.entities]
                res = shared_translation_service.translate_event_summary(
                    event_id=em.id,
                    headline=em.headline,
                    summary=em.summary,
                    source_lang=source_lang,
                    target_lang=target_norm,
                    entity_ids=entity_ids,
                )
                if res.validation_passed:
                    headline = res.translated_headline or em.headline
                    summary = res.translated_text
                    is_translated = True
                    original_headline = em.headline
                    original_summary = em.summary
                    # Persist translation
                    if tr:
                        tr.headline = headline
                        tr.summary = summary
                    else:
                        LedgerRepository.get_or_create_translation(
                            session=db,
                            event_id=em.id,
                            language=target_norm,
                            headline=headline,
                            summary=summary,
                            source_language=source_lang,
                            glossary_version=GLOSSARY_VERSION,
                            cost_eur=res.cost_eur,
                            trace_id=res.trace_id,
                        )
                    db.commit()
            except Exception:
                # Graceful degradation on translation issue
                pass

    # Retrieve all available translations for this event
    existing_trs = LedgerRepository.get_event_translations(session=db, event_id=em.id)
    available_translations = sorted({source_lang} | {t.language for t in existing_trs})

    return Event(
        id=em.id,
        headline=headline,
        status=EventStatus(em.status),
        independent_sources=em.independent_sources,
        sport=em.sport,
        competition=em.competition,
        updated_at=em.updated_at,
        summary=summary,
        first_reported_by=first_rep,
        entities=entities,
        source_url=em.source_url,
        status_note=em.status_note,
        evidence_rationale=[b["text"] if isinstance(b, dict) else str(b) for b in rationale_raw],
        language=target_norm if is_translated else source_lang,
        original_language=source_lang,
        original_headline=original_headline,
        original_summary=original_summary,
        is_translated=is_translated,
        available_translations=available_translations,
    )


@router.get("", response_model=list[Event])
def list_events(
    status: EventStatus | None = None,
    competition: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    lang: str = Query("en", description="Target language for headlines and summaries"),
    db: Session = Depends(get_db),
):
    """List ledger events with optional status and competition filters, localized to target language."""
    event_models = LedgerRepository.list_events(
        session=db,
        status=status.value if status else None,
        limit=limit,
    )
    return [build_localized_event(em=em, target_lang=lang, db=db) for em in event_models]


@router.get("/{event_id}", response_model=Event)
def get_event(
    event_id: str,
    lang: str = Query("en", description="Target language for headline and summary"),
    db: Session = Depends(get_db),
):
    """Retrieve a single event and its evidence rationale by ID, localized to target language."""
    em = LedgerRepository.get_event(session=db, event_id=event_id)
    if not em:
        raise HTTPException(status_code=404, detail="Event not found in ledger")
    return build_localized_event(em=em, target_lang=lang, db=db)
