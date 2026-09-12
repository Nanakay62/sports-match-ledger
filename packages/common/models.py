from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EventStatus(StrEnum):
    CONFIRMED = "confirmed"
    WELL_CORROBORATED = "well_corroborated"
    DEVELOPING = "developing"
    RUMOUR = "rumour"
    DISPUTED = "disputed"
    CORRECTED = "corrected"


class ClaimAttribution(StrEnum):
    ORIGINAL = "original"
    CORROBORATING = "corroborating"
    CONFLICTING = "conflicting"


class EntityType(StrEnum):
    PLAYER = "player"
    CLUB = "club"
    MANAGER = "manager"
    COMPETITION = "competition"


class SubjectType(StrEnum):
    OUTLET = "outlet"
    REPORTER = "reporter"


class EventEntity(BaseModel):
    name: str
    type: EntityType
    alias_of: str | None = None


class EventFirstReport(BaseModel):
    outlet: str
    lead_time_minutes: int = Field(ge=0, description="Minutes ahead of next outlet. 0 = sole report")


class Claim(BaseModel):
    id: str
    event_id: str
    outlet: str
    reporter: str | None = None
    text: str
    timestamp: datetime
    attribution: ClaimAttribution
    language: str = "en"
    url: str
    is_superseded: bool = False
    superseded_by: str | None = None


class Event(BaseModel):
    id: str
    headline: str
    status: EventStatus
    independent_sources: int = Field(ge=1)
    sport: str
    competition: str
    updated_at: datetime
    summary: str
    first_reported_by: EventFirstReport | None = None
    entities: list[EventEntity] = Field(default_factory=list)
    source_url: str
    status_note: str | None = None
    evidence_rationale: list[str] = Field(default_factory=list)
    language: str = "en"
    original_language: str | None = None
    original_headline: str | None = None
    original_summary: str | None = None
    is_translated: bool = False
    available_translations: list[str] = Field(default_factory=list)


class ResolutionOutcome(StrEnum):
    CORRECT = "correct"
    INCORRECT = "incorrect"


class ClaimResolution(BaseModel):
    id: str
    claim_id: str
    outcome: ResolutionOutcome
    authority_rank: int = Field(
        ge=1,
        le=5,
        description="1=Official club/league, 2=Direct quotes, 3=Reputable desk, 4=Aggregator, 5=Rumour",
    )
    authority_source_url: str
    resolved_at: datetime
    notes: str | None = None
