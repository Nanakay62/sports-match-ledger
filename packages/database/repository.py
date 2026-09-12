import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from packages.common.models import EventStatus
from packages.common.scoring import evaluate_reliability

from .models import (
    Base,
    ClaimEvidenceModel,
    ClaimModel,
    EventEntityModel,
    EventModel,
    EventTranslationModel,
    ReporterAliasModel,
    ReporterModel,
    ReporterOutletModel,
    SourceModel,
    SourceRegistryModel,
    SourceRegistryStatus,
)


class LedgerRepository:
    """Encapsulates append-only database operations for the Accountability Ledger."""

    @staticmethod
    def init_db(engine) -> None:
        """Initializes database schema tables."""
        Base.metadata.create_all(bind=engine)

    @staticmethod
    def get_or_create_source(
        session: Session,
        name: str,
        source_type: str = "outlet",
        affiliation: str | None = None,
        beat: str | None = None,
    ) -> SourceModel:
        source = session.execute(select(SourceModel).where(SourceModel.name == name)).scalar_one_or_none()

        if not source:
            source_id = f"src-{name.lower().replace(' ', '-')}"
            source = SourceModel(
                id=source_id,
                name=name,
                source_type=source_type,
                affiliation=affiliation,
                beat=beat,
                sample_size=0,
                correct_count=0,
                wilson_lower_bound=None,
            )
            session.add(source)
            session.flush()

        return source

    APPROVED_OUTLETS = {
        "the athletic",
        "sky sports",
        "bbc sport",
        "the telegraph",
        "the daily telegraph",
        "the guardian",
        "the times",
        "the woodwork",
        "sky germany",
        "sky sport deutschland",
        "cbs sports",
        "espn",
        "reuters",
    }

    @staticmethod
    def is_approved_outlet(session: Session, outlet_name: str) -> bool:
        """Checks if an outlet is already approved in the source registry, ledger sources, or approved whitelist."""
        # 1. Check Source Registry for APPROVED status
        reg_item = session.execute(
            select(SourceRegistryModel).where(
                SourceRegistryModel.source_name == outlet_name,
                SourceRegistryModel.status == SourceRegistryStatus.APPROVED.value,
            )
        ).scalar_one_or_none()
        if reg_item:
            return True

        # 2. Check approved whitelist
        if outlet_name.strip().lower() in LedgerRepository.APPROVED_OUTLETS:
            return True

        # 3. Check existing sources table
        source = session.execute(
            select(SourceModel).where(
                SourceModel.name == outlet_name,
                SourceModel.source_type == "outlet",
            )
        ).scalar_one_or_none()
        return source is not None

    @staticmethod
    def get_or_create_reporter(
        session: Session,
        name: str,
        outlet_name: str | None = None,
        aliases: list[str] | None = None,
        social_handles: dict[str, str] | None = None,
    ) -> ReporterModel:
        """Resolves or auto-creates a canonical reporter entity, linking to sources and outlets."""
        rep = session.execute(select(ReporterModel).where(ReporterModel.name == name)).scalar_one_or_none()

        if not rep:
            alias_entry = session.execute(select(ReporterAliasModel).where(ReporterAliasModel.alias == name)).scalar_one_or_none()
            if alias_entry:
                rep = alias_entry.reporter

        if not rep:
            import re

            slug = name.lower().strip().replace(" ", "-")
            slug = re.sub(r"[^\w\-]", "", slug)
            rep_id = f"rep-{slug}"

            source = LedgerRepository.get_or_create_source(
                session=session,
                name=name,
                source_type="reporter",
                affiliation=outlet_name,
            )

            rep = ReporterModel(
                id=rep_id,
                name=name,
                slug=slug,
                primary_source_id=source.id,
                social_handles_json=json.dumps(social_handles) if social_handles else None,
                created_at=datetime.now(timezone.utc),
            )
            session.add(rep)
            session.flush()

            session.add(
                ReporterAliasModel(
                    id=f"alias-{slug}-canonical",
                    reporter_id=rep.id,
                    alias=name,
                    created_at=datetime.now(timezone.utc),
                )
            )

            if aliases:
                for idx, a in enumerate(aliases):
                    if a.strip().lower() != name.strip().lower():
                        session.add(
                            ReporterAliasModel(
                                id=f"alias-{slug}-{idx}",
                                reporter_id=rep.id,
                                alias=a,
                                created_at=datetime.now(timezone.utc),
                            )
                        )

            if outlet_name:
                outlet_source = LedgerRepository.get_or_create_source(
                    session=session,
                    name=outlet_name,
                    source_type="outlet",
                )
                existing_link = session.execute(
                    select(ReporterOutletModel).where(
                        ReporterOutletModel.reporter_id == rep.id,
                        ReporterOutletModel.source_id == outlet_source.id,
                    )
                ).scalar_one_or_none()
                if not existing_link:
                    session.add(
                        ReporterOutletModel(
                            id=f"ro-{slug}-{outlet_source.id}",
                            reporter_id=rep.id,
                            source_id=outlet_source.id,
                            created_at=datetime.now(timezone.utc),
                        )
                    )

            session.flush()

        return rep

    @staticmethod
    def find_existing_claim_by_url_and_time(
        session: Session,
        source_url: str,
        published_at: datetime,
    ) -> ClaimModel | None:
        """Looks up an already-ingested claim by canonical source URL and published timestamp."""
        claim = session.execute(
            select(ClaimModel).where(
                ClaimModel.original_url == source_url,
                ClaimModel.timestamp == published_at,
            )
        ).scalar_one_or_none()
        if claim:
            return claim

        evidence = session.execute(
            select(ClaimEvidenceModel).where(
                ClaimEvidenceModel.source_url == source_url,
                ClaimEvidenceModel.published_at == published_at,
            )
        ).scalar_one_or_none()
        if evidence:
            return evidence.claim

        return None

    @staticmethod
    def find_near_duplicate_claim(
        session: Session,
        event_id: str,
        content_hash: str,
        simhash: str,
        text: str,
    ) -> tuple[ClaimModel | None, float]:
        """Searches existing claims for this event to detect verbatim syndications or lightly-edited near-duplicates."""
        from workers.pipeline.dedup import is_near_duplicate

        claims = session.execute(select(ClaimModel).where(ClaimModel.event_id == event_id)).scalars().all()

        for c in claims:
            if c.content_hash and c.content_hash == content_hash:
                return c, 1.0

            is_match, similarity = is_near_duplicate(text, c.claim_text)
            if is_match:
                return c, similarity

        return None, 0.0

    @staticmethod
    def find_recent_near_duplicate(
        session: Session,
        content_hash: str,
        simhash: str,
        text: str,
        window_hours: int = 48,
        reference_time: datetime | None = None,
        cited_source: str | None = None,
        entity_names: list[str] | None = None,
    ) -> tuple[ClaimModel | None, float]:
        """Searches existing claims across all events within a rolling time window
        to detect cross-feed syndications, near-duplicates, or wire republishing.

        Returns (matched_claim, similarity_score) or (None, 0.0).
        """
        from workers.pipeline.dedup import is_near_duplicate

        # 1. Exact content hash lookup on ClaimModel (indexed)
        exact_claim = session.execute(select(ClaimModel).where(ClaimModel.content_hash == content_hash)).scalars().first()
        if exact_claim:
            return exact_claim, 1.0

        # 2. Exact content hash lookup on ClaimEvidenceModel (indexed)
        exact_evidence = (
            session.execute(select(ClaimEvidenceModel).where(ClaimEvidenceModel.content_hash == content_hash)).scalars().first()
        )
        if exact_evidence and exact_evidence.claim:
            return exact_evidence.claim, 1.0

        # 3. Retrieve candidates within rolling window (or recent pool)
        ref = reference_time or datetime.now(timezone.utc)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)

        cutoff_lower = ref - timedelta(hours=window_hours)
        cutoff_upper = ref + timedelta(hours=window_hours)

        try:
            candidates = (
                session.execute(
                    select(ClaimModel)
                    .where(
                        ClaimModel.timestamp >= cutoff_lower,
                        ClaimModel.timestamp <= cutoff_upper,
                    )
                    .order_by(desc(ClaimModel.timestamp))
                )
                .scalars()
                .all()
            )
        except Exception:
            candidates = []

        # If window query returned empty, retrieve recent pool
        if not candidates:
            candidates = session.execute(select(ClaimModel).order_by(desc(ClaimModel.timestamp)).limit(50)).scalars().all()

        # 4. Compare candidate claims
        for candidate in candidates:
            if candidate.content_hash and candidate.content_hash == content_hash:
                return candidate, 1.0

            is_match, similarity = is_near_duplicate(text, candidate.claim_text)
            if is_match:
                return candidate, similarity

            # 5. Check secondary attribution cue match:
            # If the incoming article cites an outlet or reporter, and candidate belongs to that outlet/reporter,
            # and they share key entities.
            if cited_source and entity_names:
                outlet_match = bool(candidate.source and candidate.source.name.lower() == cited_source.lower())
                reporter_match = bool(candidate.reporter and candidate.reporter.lower() == cited_source.lower())
                if outlet_match or reporter_match:
                    cand_event = candidate.event
                    cand_entities = {e.name.lower() for e in cand_event.entities} if cand_event else set()
                    incoming_entities = {n.lower() for n in entity_names}
                    if cand_entities & incoming_entities:
                        return candidate, 0.85

        return None, 0.0

    @staticmethod
    def append_evidence_to_claim(
        session: Session,
        claim_id: str,
        outlet_name: str,
        source_url: str,
        published_at: datetime,
        content_hash: str,
        similarity_to_root: float = 1.0,
        reporter: str | None = None,
        reporter_id: str | None = None,
        attribution_type: str = "first_party",
    ) -> ClaimEvidenceModel:
        """Appends a supporting evidence source (wire copy, syndicated report) to an existing claim."""
        import hashlib

        claim = session.execute(select(ClaimModel).where(ClaimModel.id == claim_id)).scalar_one_or_none()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found in ledger")

        source = LedgerRepository.get_or_create_source(
            session=session,
            name=outlet_name,
            source_type="outlet",
        )

        ev_hash = hashlib.sha256(f"{source_url}:{published_at.isoformat()}".encode()).hexdigest()[:8]
        evidence_id = f"ev-{ev_hash}"

        existing_ev = session.execute(select(ClaimEvidenceModel).where(ClaimEvidenceModel.id == evidence_id)).scalar_one_or_none()
        if existing_ev:
            return existing_ev

        evidence = ClaimEvidenceModel(
            id=evidence_id,
            claim_id=claim.id,
            source_id=source.id,
            source_url=source_url,
            reporter_id=reporter_id,
            reporter=reporter,
            attribution_type=attribution_type,
            published_at=published_at,
            content_hash=content_hash,
            similarity_to_root=similarity_to_root,
            recorded_at=datetime.now(timezone.utc),
        )
        session.add(evidence)

        # Update source stats
        source.sample_size += 1
        metrics = evaluate_reliability(
            subject_name=source.name,
            subject_type=source.source_type,
            correct_count=source.correct_count,
            sample_size=source.sample_size,
        )
        source.wilson_lower_bound = metrics.wilson_lower_bound

        # Update reporter stats if reporter attached
        if reporter:
            rep_source = session.execute(
                select(SourceModel).where(
                    SourceModel.name == reporter,
                    SourceModel.source_type == "reporter",
                )
            ).scalar_one_or_none()
            if rep_source:
                rep_source.sample_size += 1
                rep_metrics = evaluate_reliability(
                    subject_name=rep_source.name,
                    subject_type=rep_source.source_type,
                    correct_count=rep_source.correct_count,
                    sample_size=rep_source.sample_size,
                )
                rep_source.wilson_lower_bound = rep_metrics.wilson_lower_bound

        # Update parent event independent sources if this outlet is new to the event
        event = claim.event
        if event:
            all_evidence_sources = (
                session.execute(
                    select(SourceModel.name)
                    .join(ClaimEvidenceModel, ClaimEvidenceModel.source_id == SourceModel.id)
                    .join(ClaimModel, ClaimEvidenceModel.claim_id == ClaimModel.id)
                    .where(ClaimModel.event_id == event.id)
                )
                .scalars()
                .all()
            )
            all_claim_sources = (
                session.execute(
                    select(SourceModel.name).join(ClaimModel, ClaimModel.source_id == SourceModel.id).where(ClaimModel.event_id == event.id)
                )
                .scalars()
                .all()
            )
            distinct_outlets = set(all_evidence_sources) | set(all_claim_sources) | {outlet_name}
            event.independent_sources = len(distinct_outlets)
            event.updated_at = datetime.now(timezone.utc)

        session.flush()
        return evidence

    @staticmethod
    def append_claim(
        session: Session,
        claim_id: str,
        event_id: str,
        outlet_name: str,
        claim_text: str,
        original_url: str,
        attribution: str = "original",
        attribution_type: str = "first_party",
        reporter: str | None = None,
        reporter_id: str | None = None,
        language: str = "en",
        timestamp: datetime | None = None,
        content_hash: str | None = None,
        simhash: str | None = None,
    ) -> ClaimModel:
        """Appends an immutable claim to the ledger. Claims can never be updated or deleted."""
        existing = session.execute(select(ClaimModel).where(ClaimModel.id == claim_id)).scalar_one_or_none()

        if existing:
            raise ValueError(f"Ledger violation: claim {claim_id} is already recorded and immutable.")

        source = LedgerRepository.get_or_create_source(
            session=session,
            name=outlet_name,
            source_type="outlet",
        )

        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        claim = ClaimModel(
            id=claim_id,
            event_id=event_id,
            source_id=source.id,
            reporter_id=reporter_id,
            reporter=reporter,
            claim_text=claim_text,
            attribution=attribution,
            attribution_type=attribution_type,
            language=language,
            original_url=original_url,
            content_hash=content_hash,
            simhash=simhash,
            timestamp=timestamp,
            is_superseded=False,
        )
        session.add(claim)

        evidence_id = f"ev-{claim_id[2:] if claim_id.startswith('c-') else claim_id}-root"
        primary_evidence = ClaimEvidenceModel(
            id=evidence_id,
            claim_id=claim.id,
            source_id=source.id,
            source_url=original_url,
            reporter_id=reporter_id,
            reporter=reporter,
            attribution_type=attribution_type,
            published_at=timestamp,
            content_hash=content_hash or "",
            similarity_to_root=1.0,
            recorded_at=datetime.now(timezone.utc),
        )
        session.add(primary_evidence)

        # Update source stats
        source.sample_size += 1
        metrics = evaluate_reliability(
            subject_name=source.name,
            subject_type=source.source_type,
            correct_count=source.correct_count,
            sample_size=source.sample_size,
        )
        source.wilson_lower_bound = metrics.wilson_lower_bound

        # Update reporter stats if reporter attached
        if reporter:
            rep_source = session.execute(
                select(SourceModel).where(
                    SourceModel.name == reporter,
                    SourceModel.source_type == "reporter",
                )
            ).scalar_one_or_none()
            if rep_source:
                rep_source.sample_size += 1
                rep_metrics = evaluate_reliability(
                    subject_name=rep_source.name,
                    subject_type=rep_source.source_type,
                    correct_count=rep_source.correct_count,
                    sample_size=rep_source.sample_size,
                )
                rep_source.wilson_lower_bound = rep_metrics.wilson_lower_bound

        session.flush()
        return claim

    @staticmethod
    def get_or_create_event(
        session: Session,
        event_id: str,
        headline: str,
        summary: str,
        source_url: str,
        sport: str = "Football",
        competition: str = "Premier League",
        status: EventStatus = EventStatus.RUMOUR,
        first_reported_outlet: str | None = None,
        first_reported_lead_minutes: int = 0,
        status_note: str | None = None,
        evidence_rationale: list[dict] | None = None,
        entities: list[dict] | None = None,
    ) -> EventModel:
        event = session.execute(select(EventModel).where(EventModel.id == event_id)).scalar_one_or_none()

        if not event:
            rationale_json = json.dumps(evidence_rationale) if evidence_rationale else None
            event = EventModel(
                id=event_id,
                headline=headline,
                status=status.value,
                independent_sources=1,
                sport=sport,
                competition=competition,
                summary=summary,
                source_url=source_url,
                status_note=status_note,
                evidence_rationale_json=rationale_json,
                first_reported_outlet=first_reported_outlet,
                first_reported_lead_minutes=first_reported_lead_minutes,
                updated_at=datetime.now(timezone.utc),
            )
            session.add(event)
            session.flush()

            if entities:
                for ent in entities:
                    ent_id = f"{event.id}-{ent.get('name', '').lower().replace(' ', '-')}"
                    entity_record = EventEntityModel(
                        id=ent_id,
                        event_id=event.id,
                        name=ent.get("name", ""),
                        entity_type=ent.get("type", "club"),
                    )
                    session.add(entity_record)
                session.flush()

        return event

    @staticmethod
    def list_events(
        session: Session,
        status: str | None = None,
        limit: int = 20,
    ) -> list[EventModel]:
        stmt = select(EventModel).order_by(desc(EventModel.updated_at)).limit(limit)
        if status:
            stmt = stmt.where(EventModel.status == status)
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_event(session: Session, event_id: str) -> EventModel | None:
        return session.execute(select(EventModel).where(EventModel.id == event_id)).scalar_one_or_none()

    @staticmethod
    def list_claims(session: Session, event_id: str) -> list[ClaimModel]:
        return list(
            session.execute(select(ClaimModel).where(ClaimModel.event_id == event_id).order_by(desc(ClaimModel.timestamp))).scalars().all()
        )

    @staticmethod
    def get_or_create_translation(
        session: Session,
        event_id: str,
        language: str,
        headline: str,
        summary: str,
        source_language: str,
        glossary_version: str = "v1",
        cost_eur: float = 0.0,
        trace_id: str | None = None,
    ) -> EventTranslationModel:
        """Stores or retrieves a generated translation for an event."""
        tr = session.execute(
            select(EventTranslationModel).where(
                EventTranslationModel.event_id == event_id,
                EventTranslationModel.language == language,
                EventTranslationModel.glossary_version == glossary_version,
            )
        ).scalar_one_or_none()
        if not tr:
            import hashlib

            h = hashlib.sha256(f"{event_id}:{language}:{glossary_version}".encode()).hexdigest()[:8]
            tr_id = f"tr-{event_id}-{language}-{h}"
            tr = EventTranslationModel(
                id=tr_id,
                event_id=event_id,
                language=language,
                headline=headline,
                summary=summary,
                glossary_version=glossary_version,
                source_language=source_language,
                cost_eur=cost_eur,
                trace_id=trace_id,
                created_at=datetime.now(timezone.utc),
            )
            session.add(tr)
            session.flush()
        return tr

    @staticmethod
    def get_event_translation(
        session: Session,
        event_id: str,
        language: str,
        glossary_version: str | None = None,
    ) -> EventTranslationModel | None:
        """Retrieves an existing translation for an event in the requested language."""
        stmt = select(EventTranslationModel).where(
            EventTranslationModel.event_id == event_id,
            EventTranslationModel.language == language,
        )
        if glossary_version:
            stmt = stmt.where(EventTranslationModel.glossary_version == glossary_version)
        return session.execute(stmt.order_by(desc(EventTranslationModel.created_at))).scalars().first()

    @staticmethod
    def get_event_translations(
        session: Session,
        event_id: str,
    ) -> list[EventTranslationModel]:
        """Lists all existing translations for an event."""
        return list(
            session.execute(
                select(EventTranslationModel).where(EventTranslationModel.event_id == event_id).order_by(EventTranslationModel.language)
            )
            .scalars()
            .all()
        )
