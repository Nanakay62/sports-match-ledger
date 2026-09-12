from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SourceRegistryStatus(StrEnum):
    PROPOSED = "proposed"
    TECHNICAL_REVIEW = "technical_review"
    RIGHTS_REVIEW = "rights_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class SourceRegistryModel(Base):
    """Source Registry table managing the PROPOSED -> TECHNICAL_REVIEW -> RIGHTS_REVIEW -> APPROVED workflow."""

    __tablename__ = "source_registry"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    feed_url: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    feed_format: Mapped[str] = mapped_column(String(32), default="rss2", nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    coverage_category: Mapped[str] = mapped_column(String(32), default="general", nullable=False)
    authority_rank: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=SourceRegistryStatus.PROPOSED.value, nullable=False, index=True)
    technical_check_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    technical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rights_review_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rights_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    polling_interval_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class SourceModel(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    affiliation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    beat: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wilson_lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    claims: Mapped[list["ClaimModel"]] = relationship("ClaimModel", back_populates="source")


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    headline: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    independent_sources: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sport: Mapped[str] = mapped_column(String(64), nullable=False)
    competition: Mapped[str] = mapped_column(String(128), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    status_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_rationale_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_reported_outlet: Mapped[str | None] = mapped_column(String(128), nullable=True)
    first_reported_lead_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    claims: Mapped[list["ClaimModel"]] = relationship("ClaimModel", back_populates="event")
    entities: Mapped[list["EventEntityModel"]] = relationship("EventEntityModel", back_populates="event", cascade="all, delete-orphan")
    translations: Mapped[list["EventTranslationModel"]] = relationship(
        "EventTranslationModel", back_populates="event", cascade="all, delete-orphan"
    )


class EventEntityModel(Base):
    __tablename__ = "event_entities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(64), ForeignKey("events.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)

    event: Mapped["EventModel"] = relationship("EventModel", back_populates="entities")


class EventTranslationModel(Base):
    """Stores generated translations for event headlines and summaries, linked to parent event."""

    __tablename__ = "event_translations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(64), ForeignKey("events.id"), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    headline: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    glossary_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    source_language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    cost_eur: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    event: Mapped["EventModel"] = relationship("EventModel", back_populates="translations")


class ReporterModel(Base):
    __tablename__ = "reporters"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    primary_source_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("sources.id"), nullable=True)
    social_handles_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    aliases: Mapped[list["ReporterAliasModel"]] = relationship(
        "ReporterAliasModel", back_populates="reporter", cascade="all, delete-orphan"
    )
    outlets: Mapped[list["ReporterOutletModel"]] = relationship(
        "ReporterOutletModel", back_populates="reporter", cascade="all, delete-orphan"
    )
    claims: Mapped[list["ClaimModel"]] = relationship("ClaimModel", back_populates="reporter_rel")


class ReporterAliasModel(Base):
    __tablename__ = "reporter_aliases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    reporter_id: Mapped[str] = mapped_column(String(64), ForeignKey("reporters.id"), nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    reporter: Mapped["ReporterModel"] = relationship("ReporterModel", back_populates="aliases")


class ReporterOutletModel(Base):
    __tablename__ = "reporter_outlets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    reporter_id: Mapped[str] = mapped_column(String(64), ForeignKey("reporters.id"), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(64), ForeignKey("sources.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    reporter: Mapped["ReporterModel"] = relationship("ReporterModel", back_populates="outlets")
    source: Mapped["SourceModel"] = relationship("SourceModel")


class ClaimModel(Base):
    """Append-only table. Claims are never edited or deleted, only superseded."""

    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(64), ForeignKey("events.id"), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(64), ForeignKey("sources.id"), nullable=False, index=True)
    reporter_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("reporters.id"), nullable=True, index=True)
    reporter: Mapped[str | None] = mapped_column(String(128), nullable=True)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    attribution: Mapped[str] = mapped_column(String(32), nullable=False)
    attribution_type: Mapped[str] = mapped_column(String(32), default="first_party", nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    original_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    simhash: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_superseded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    superseded_by: Mapped[str | None] = mapped_column(String(64), ForeignKey("claims.id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    event: Mapped["EventModel"] = relationship("EventModel", back_populates="claims")
    source: Mapped["SourceModel"] = relationship("SourceModel", back_populates="claims")
    reporter_rel: Mapped["ReporterModel | None"] = relationship("ReporterModel", back_populates="claims")
    resolutions: Mapped[list["ResolutionModel"]] = relationship("ResolutionModel", back_populates="claim")
    evidence_sources: Mapped[list["ClaimEvidenceModel"]] = relationship(
        "ClaimEvidenceModel", back_populates="claim", cascade="all, delete-orphan"
    )


class ClaimEvidenceModel(Base):
    """Append-only evidence sources (articles, syndications, wire pickups) corroborating a claim."""

    __tablename__ = "claim_evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(64), ForeignKey("sources.id"), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    reporter_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("reporters.id"), nullable=True, index=True)
    reporter: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attribution_type: Mapped[str] = mapped_column(String(32), default="first_party", nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    similarity_to_root: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    claim: Mapped["ClaimModel"] = relationship("ClaimModel", back_populates="evidence_sources")
    source: Mapped["SourceModel"] = relationship("SourceModel")


class ResolutionModel(Base):
    """Append-only resolutions for claims."""

    __tablename__ = "resolutions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    authority_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    authority_source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    claim: Mapped["ClaimModel"] = relationship("ClaimModel", back_populates="resolutions")


class PipelineJobModel(Base):
    """Postgres-backed job queue table supporting FOR UPDATE SKIP LOCKED."""

    __tablename__ = "pipeline_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lane: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
