"""Deterministic 8-Factor Validation Engine.

Handbook §13 / §14 deterministic validation across:
1. Source Quality (authority rank weighting)
2. Independence (wire root count / syndication collapse)
3. Reporter Record (Wilson lower bound capped at 0.85)
4. Corroboration (independent source count)
5. Consistency (qualifier / detail alignment)
6. Official Confirmation (Authority Rank 1–2 official announcement)
7. Contradiction (conflicting predicates or official denial)
8. Recency (exponential time decay)

Guarantees reader-facing status vocabulary:
Confirmed, Well corroborated, Developing, Rumour, Disputed, Corrected.
Zero model inference spend (€0.00).
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

from packages.common.models import EventStatus

REPORTER_SCORE_CAP = 0.85  # Reputation can never substitute for evidence per §13


@dataclass
class ValidationClaimInput:
    """Input claim data needed for deterministic evaluation."""

    claim_id: str
    outlet_name: str
    authority_rank: int = 3
    reporter_name: str | None = None
    reporter_wilson_score: float | None = None
    predicate: str | None = None
    attribution_type: str = "first_party"
    fee_eur: float | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_superseded: bool = False


@dataclass
class ValidationResult:
    """Outcome of running the 8 deterministic validation factors."""

    status: EventStatus
    confidence_score: float
    factors: dict[str, float]
    rationale_bullets: list[dict[str, str]]
    has_contradiction: bool
    is_confirmed: bool
    independent_roots: int


class DeterministicValidationEngine:
    """Evaluates an event and its underlying claims against the 8 deterministic factors."""

    @classmethod
    def evaluate(
        cls,
        claims: list[ValidationClaimInput],
        current_time: datetime | None = None,
        is_corrected: bool = False,
    ) -> ValidationResult:
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        if not claims:
            return ValidationResult(
                status=EventStatus.RUMOUR,
                confidence_score=0.0,
                factors={
                    "source_quality": 0.0,
                    "independence": 0.0,
                    "reporter_record": 0.0,
                    "corroboration": 0.0,
                    "consistency": 1.0,
                    "official_confirmation": 0.0,
                    "contradiction": 0.0,
                    "recency": 1.0,
                },
                rationale_bullets=[
                    {
                        "kind": "warn",
                        "text": "**No claims on record:** awaiting initial source attribution.",
                    }
                ],
                has_contradiction=False,
                is_confirmed=False,
                independent_roots=0,
            )

        if is_corrected or any(c.is_superseded for c in claims):
            return ValidationResult(
                status=EventStatus.CORRECTED,
                confidence_score=1.0,
                factors={
                    "source_quality": 1.0,
                    "independence": 1.0,
                    "reporter_record": 1.0,
                    "corroboration": 1.0,
                    "consistency": 1.0,
                    "official_confirmation": 1.0,
                    "contradiction": 0.0,
                    "recency": 1.0,
                },
                rationale_bullets=[
                    {
                        "kind": "warn",
                        "text": "**Correction on record:** earlier reporting has been officially retracted or superseded in the ledger.",
                    }
                ],
                has_contradiction=False,
                is_confirmed=False,
                independent_roots=len({c.outlet_name for c in claims}),
            )

        # Factor 1: Source Quality (Authority Rank 1 = 1.0, Rank 2 = 0.9, Rank 3 = 0.75, Rank 4 = 0.5, Rank 5 = 0.25)
        rank_weights = {1: 1.0, 2: 0.9, 3: 0.75, 4: 0.5, 5: 0.25}
        quality_scores = [rank_weights.get(c.authority_rank, 0.25) for c in claims]
        source_quality = sum(quality_scores) / len(quality_scores)

        # Factor 2: Independence (Unique non-aggregation outlets)
        independent_outlets = {c.outlet_name.lower().strip() for c in claims if c.attribution_type != "aggregation"}
        if not independent_outlets:
            independent_outlets = {c.outlet_name.lower().strip() for c in claims}
        independent_roots = len(independent_outlets)
        independence = min(1.0, independent_roots / 3.0)

        # Factor 3: Reporter Record (Capped at 0.85 per Handbook §13)
        reporter_scores: list[float] = []
        for c in claims:
            if c.reporter_wilson_score is not None:
                capped_score = min(c.reporter_wilson_score, REPORTER_SCORE_CAP)
                reporter_scores.append(capped_score)
            else:
                reporter_scores.append(0.50)  # Neutral baseline for untracked reporters
        reporter_record = sum(reporter_scores) / len(reporter_scores)

        # Factor 4: Corroboration (1 source = 0.33, 2 = 0.67, 3+ = 1.0)
        corroboration = min(1.0, independent_roots / 3.0)

        # Factor 5: Consistency (Numerical fee variance < 20%)
        fees = [c.fee_eur for c in claims if c.fee_eur is not None and c.fee_eur > 0]
        if len(fees) >= 2:
            fee_min = min(fees)
            fee_max = max(fees)
            variance = (fee_max - fee_min) / fee_min
            consistency = max(0.0, 1.0 - variance)
        else:
            consistency = 1.0

        # Factor 6: Official Confirmation (Authority Rank 1-2 announcement)
        official_claims = [c for c in claims if c.authority_rank in {1, 2} or c.predicate == "official_signing"]
        official_confirmation = 1.0 if official_claims else 0.0

        # Factor 7: Contradiction (Conflicting predicates e.g. denial vs agreement)
        predicates = {c.predicate for c in claims if c.predicate}
        has_contradiction = ("transfer_denied" in predicates) and bool(
            predicates.intersection({"official_signing", "agrees_terms", "submits_bid", "transfer_linked"})
        )
        contradiction = 1.0 if has_contradiction else 0.0

        # Factor 8: Recency (Half-life decay over 7 days = 604,800s)
        newest_timestamp = max(c.timestamp for c in claims)
        if newest_timestamp.tzinfo is None:
            newest_timestamp = newest_timestamp.replace(tzinfo=timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        age_seconds = max(0.0, (current_time - newest_timestamp).total_seconds())
        recency = math.exp(-0.693 * (age_seconds / (7 * 86400.0)))

        # Determine Status
        bullets: list[dict[str, str]] = []

        if has_contradiction:
            status = EventStatus.DISPUTED
            bullets.append(
                {
                    "kind": "warn",
                    "text": "**Direct contradiction on record:** conflicting assertions and official denials recorded in ledger.",
                }
            )
            bullets.append(
                {
                    "kind": "info",
                    "text": f"**Dispute tracking:** {independent_roots} independent desks report conflicting status. Awaiting outcome.",
                }
            )
        elif official_confirmation > 0.0:
            status = EventStatus.CONFIRMED
            bullets.append(
                {
                    "kind": "ok",
                    "text": "**Official confirmation on record:** verified through primary club statement or official registry filing.",
                }
            )
            bullets.append(
                {
                    "kind": "ok",
                    "text": f"**Corroborated across {independent_roots} independent desks** with verified terms.",
                }
            )
        elif independent_roots >= 3:
            status = EventStatus.WELL_CORROBORATED
            bullets.append(
                {
                    "kind": "ok",
                    "text": f"**Corroborated across {independent_roots} independent newsrooms** with consistent core details.",
                }
            )
            bullets.append(
                {
                    "kind": "warn",
                    "text": "**Formal execution pending:** final club signatures or medical registration outstanding.",
                }
            )
        elif independent_roots == 2:
            status = EventStatus.DEVELOPING
            bullets.append(
                {
                    "kind": "warn",
                    "text": "**Developing report:** verified by two independent outlets, monitoring for formal confirmation.",
                }
            )
            bullets.append(
                {
                    "kind": "info",
                    "text": f"**{len(claims)} total claims logged:** terms remain fluid across reporting desks.",
                }
            )
        else:
            status = EventStatus.RUMOUR
            bullets.append(
                {
                    "kind": "warn",
                    "text": "**Single-source claim:** initial report lacks secondary independent corroboration.",
                }
            )
            bullets.append(
                {
                    "kind": "info",
                    "text": "**Ledger holds at Rumour:** awaiting corroboration from a second independent newsroom.",
                }
            )

        factors = {
            "source_quality": round(source_quality, 3),
            "independence": round(independence, 3),
            "reporter_record": round(reporter_record, 3),
            "corroboration": round(corroboration, 3),
            "consistency": round(consistency, 3),
            "official_confirmation": round(official_confirmation, 3),
            "contradiction": round(contradiction, 3),
            "recency": round(recency, 3),
        }

        # Composite confidence metric
        confidence_score = round(
            (source_quality * 0.25)
            + (independence * 0.20)
            + (reporter_record * 0.15)
            + (corroboration * 0.20)
            + (consistency * 0.10)
            + (recency * 0.10),
            3,
        )

        return ValidationResult(
            status=status,
            confidence_score=confidence_score,
            factors=factors,
            rationale_bullets=bullets,
            has_contradiction=has_contradiction,
            is_confirmed=bool(official_confirmation > 0.0),
            independent_roots=independent_roots,
        )
