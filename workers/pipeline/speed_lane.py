import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from packages.common.entities import default_entity_graph
from packages.common.models import EventStatus
from packages.common.reporters import CanonicalReporter, default_reporter_graph
from packages.database.repository import LedgerRepository

from .adapters.rss_adapter import ArticleIngestionAdapter, RawArticle
from .attribution import detect_attribution_type
from .dedup import compute_content_hash, compute_simhash, strip_boilerplate


class SpeedLaneWorker:
    """Deterministic-only processing lane targeting under 90 seconds to alert.

    No model calls are permitted in this lane.
    Performs deterministic provenance validation, entity extraction, and claim recording.
    """

    def __init__(self, session: Session):
        self.session = session

    def process_raw_article(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        start_time = time.monotonic()

        # Step 1: Validate provenance strictly
        article: RawArticle = ArticleIngestionAdapter.ingest_payload(raw_payload)

        # Step 1b: Early Idempotency Check (same URL and timestamp)
        existing_claim = LedgerRepository.find_existing_claim_by_url_and_time(
            session=self.session,
            source_url=article.source_url,
            published_at=article.published_at,
        )
        if existing_claim:
            latency_ms = round((time.monotonic() - start_time) * 1000, 2)
            event_obj = existing_claim.event
            return {
                "lane": "speed_lane",
                "action": "idempotent_noop",
                "event_id": existing_claim.event_id,
                "claim_id": existing_claim.id,
                "headline": event_obj.headline if event_obj else article.headline,
                "status": event_obj.status if event_obj else EventStatus.RUMOUR.value,
                "entities": [e.name for e in event_obj.entities] if event_obj else [],
                "latency_ms": latency_ms,
                "source": article.outlet,
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Step 2: Boilerplate Stripping & Content Normalization
        cleaned_body = strip_boilerplate(article.body)
        content_hash = compute_content_hash(cleaned_body)
        simhash = compute_simhash(cleaned_body)

        # Step 2b: Deterministic entity extraction via entity graph
        combined_text = f"{article.headline} {cleaned_body}"
        entities = default_entity_graph.extract_entities(combined_text)
        entity_names = [e.name for e in entities]

        # Step 2c: Deterministic reporter resolution
        reporter_id: str | None = None
        reporter_name: str | None = None
        if article.author:
            canonical_rep, _ = default_reporter_graph.resolve_byline(article.author, outlet=article.outlet)
            if canonical_rep:
                reporter_id = canonical_rep.id
                reporter_name = canonical_rep.name
            else:
                # Tier 4: Check if outlet is approved and byline is a genuine personal name
                import re

                is_approved = LedgerRepository.is_approved_outlet(session=self.session, outlet_name=article.outlet)
                is_name_like = bool(re.match(r"^[A-Z][\w'\-]+(?:\s+[A-Z][\w'\-]+){1,3}$", article.author.strip()))
                if is_approved and is_name_like:
                    rep_model = LedgerRepository.get_or_create_reporter(
                        session=self.session,
                        name=article.author.strip(),
                        outlet_name=article.outlet,
                    )
                    reporter_id = rep_model.id
                    reporter_name = rep_model.name
                    default_reporter_graph.register_reporter(
                        CanonicalReporter(
                            id=rep_model.id,
                            name=rep_model.name,
                            slug=rep_model.slug,
                            aliases=[rep_model.name],
                            associated_outlets=[article.outlet],
                        )
                    )
                else:
                    reporter_id = None
                    reporter_name = None

        # Step 2d: Detect attribution cues
        prelim_attr_type, cited_source = detect_attribution_type(
            headline=article.headline,
            body=article.body,
            outlet=article.outlet,
            reporter=reporter_name,
            article_published_at=article.published_at,
        )

        # Step 3: Cross-Feed Deduplication & Evidence Roots (BEFORE event creation)
        near_claim, similarity = LedgerRepository.find_recent_near_duplicate(
            session=self.session,
            content_hash=content_hash,
            simhash=simhash,
            text=cleaned_body,
            window_hours=48,
            reference_time=article.published_at,
            cited_source=cited_source,
            entity_names=entity_names,
        )

        if near_claim:
            event = near_claim.event
            # Classify attribution with existing claims on this event
            existing_claims = LedgerRepository.list_claims(session=self.session, event_id=event.id)
            attribution_type, _ = detect_attribution_type(
                headline=article.headline,
                body=article.body,
                outlet=article.outlet,
                reporter=reporter_name,
                existing_claims_on_event=existing_claims,
                article_published_at=article.published_at,
            )

            evidence = LedgerRepository.append_evidence_to_claim(
                session=self.session,
                claim_id=near_claim.id,
                outlet_name=article.outlet,
                source_url=article.source_url,
                published_at=article.published_at,
                content_hash=content_hash,
                similarity_to_root=similarity,
                reporter=reporter_name,
                reporter_id=reporter_id,
                attribution_type=attribution_type,
            )
            self.session.commit()
            latency_ms = round((time.monotonic() - start_time) * 1000, 2)
            return {
                "lane": "speed_lane",
                "action": "evidence_attached",
                "event_id": event.id,
                "claim_id": near_claim.id,
                "evidence_id": evidence.id,
                "similarity_to_root": similarity,
                "headline": event.headline,
                "status": event.status,
                "entities": [e.name for e in event.entities] if event.entities else entity_names,
                "reporter": reporter_name,
                "reporter_id": reporter_id,
                "attribution_type": attribution_type,
                "latency_ms": latency_ms,
                "source": article.outlet,
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Step 4: Genuinely novel event: Deterministic event ID derivation and clustering
        if entities:
            entity_slug = "-".join(sorted(e.name.lower().replace(" ", "-") for e in entities[:2]))
            event_id = f"e-{entity_slug}"
        else:
            import hashlib

            h = hashlib.sha256(article.headline.encode("utf-8")).hexdigest()[:8]
            event_id = f"e-misc-{h}"

        entity_dicts = [{"name": e.name, "type": e.type.value} for e in entities]

        event = LedgerRepository.get_or_create_event(
            session=self.session,
            event_id=event_id,
            headline=article.headline,
            summary=cleaned_body[:280] + ("..." if len(cleaned_body) > 280 else ""),
            source_url=article.source_url,
            sport="Football",
            competition="Premier League",
            status=EventStatus.RUMOUR,
            first_reported_outlet=article.outlet,
            first_reported_lead_minutes=0,
            entities=entity_dicts,
        )

        # Step 5: Attribution classification for new claim
        existing_claims = LedgerRepository.list_claims(session=self.session, event_id=event.id)
        attribution_type, _ = detect_attribution_type(
            headline=article.headline,
            body=article.body,
            outlet=article.outlet,
            reporter=reporter_name,
            existing_claims_on_event=existing_claims,
            article_published_at=article.published_at,
        )
        attribution_category = "original" if attribution_type == "first_party" else "corroborating"

        # Intra-event near duplicate check fallback
        intra_claim, intra_sim = LedgerRepository.find_near_duplicate_claim(
            session=self.session,
            event_id=event.id,
            content_hash=content_hash,
            simhash=simhash,
            text=cleaned_body,
        )
        if intra_claim:
            evidence = LedgerRepository.append_evidence_to_claim(
                session=self.session,
                claim_id=intra_claim.id,
                outlet_name=article.outlet,
                source_url=article.source_url,
                published_at=article.published_at,
                content_hash=content_hash,
                similarity_to_root=intra_sim,
                reporter=reporter_name,
                reporter_id=reporter_id,
                attribution_type=attribution_type,
            )
            self.session.commit()
            latency_ms = round((time.monotonic() - start_time) * 1000, 2)
            return {
                "lane": "speed_lane",
                "action": "evidence_attached",
                "event_id": event.id,
                "claim_id": intra_claim.id,
                "evidence_id": evidence.id,
                "similarity_to_root": intra_sim,
                "headline": event.headline,
                "status": event.status,
                "entities": [e.name for e in entities],
                "reporter": reporter_name,
                "reporter_id": reporter_id,
                "attribution_type": attribution_type,
                "latency_ms": latency_ms,
                "source": article.outlet,
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Step 6: Append new claim to ledger
        import hashlib

        claim_hash = hashlib.sha256(f"{article.source_url}:{article.published_at.isoformat()}".encode()).hexdigest()[:8]
        claim_id = f"c-{claim_hash}"

        claim = LedgerRepository.append_claim(
            session=self.session,
            claim_id=claim_id,
            event_id=event.id,
            outlet_name=article.outlet,
            reporter=reporter_name,
            reporter_id=reporter_id,
            claim_text=cleaned_body,
            original_url=article.source_url,
            attribution=attribution_category,
            attribution_type=attribution_type,
            language=article.language,
            timestamp=article.published_at,
            content_hash=content_hash,
            simhash=simhash,
        )

        self.session.commit()
        latency_ms = round((time.monotonic() - start_time) * 1000, 2)

        return {
            "lane": "speed_lane",
            "action": "claim_created",
            "event_id": event.id,
            "claim_id": claim.id,
            "headline": event.headline,
            "status": event.status,
            "entities": [e.name for e in entities],
            "reporter": reporter_name,
            "reporter_id": reporter_id,
            "attribution_type": attribution_type,
            "latency_ms": latency_ms,
            "source": article.outlet,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
