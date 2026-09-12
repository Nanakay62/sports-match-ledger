"""Seeds localized translations for active events in the ledger."""

import logging

from packages.ai.translation import TranslationService
from packages.common.entities import GLOSSARY_VERSION
from packages.database.repository import LedgerRepository
from packages.database.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_translations")


def seed_translations(limit: int = 25):
    db = SessionLocal()
    svc = TranslationService()
    events = LedgerRepository.list_events(db, limit=limit)
    logger.info(f"Seeding translations for {len(events)} events...")

    for em in events:
        source_lang = "en"
        if em.claims and em.claims[0].language:
            source_lang = em.claims[0].language.lower()
        elif any(c in em.headline.lower() for c in ["all'estero", "espande", "dopo", "calcio", "società", "brasile"]):
            source_lang = "it"

        for target in ["en", "es", "de", "fr"]:
            if target == source_lang:
                continue

            existing = LedgerRepository.get_event_translation(
                session=db,
                event_id=em.id,
                language=target,
                glossary_version=GLOSSARY_VERSION,
            )
            if existing and existing.headline.strip().lower() != em.headline.strip().lower():
                continue

            entity_ids = [e.name for e in em.entities]
            try:
                res = svc.translate_event_summary(
                    event_id=em.id,
                    headline=em.headline,
                    summary=em.summary,
                    source_lang=source_lang,
                    target_lang=target,
                    entity_ids=entity_ids,
                )
                if res.validation_passed and res.translated_headline:
                    logger.info(f"[{target}] {em.id}: {res.translated_headline[:50]}")
                    LedgerRepository.get_or_create_translation(
                        session=db,
                        event_id=em.id,
                        language=target,
                        headline=res.translated_headline,
                        summary=res.translated_text,
                        source_language=source_lang,
                        glossary_version=GLOSSARY_VERSION,
                        cost_eur=res.cost_eur,
                        trace_id=res.trace_id,
                    )
                    db.commit()
            except Exception as e:
                logger.warning(f"Failed to translate {em.id} to {target}: {e}")

    db.close()
    logger.info("Done seeding event translations.")


if __name__ == "__main__":
    seed_translations()
