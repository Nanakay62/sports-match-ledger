import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ReliabilityMetrics:
    subject_name: str
    subject_type: str  # "outlet" | "reporter"
    sample_size: int
    correct_count: int
    wilson_lower_bound: float | None
    is_insufficient_record: bool
    unweighted_accuracy: float


def wilson_lower_bound(correct: int, total: int, confidence: float = 0.95) -> float:
    """Computes the Wilson score interval lower bound for a Bernoulli parameter.

    Default confidence is 95% (z = 1.95996).
    Returns 0.0 if total is 0.
    """
    if total <= 0:
        return 0.0
    if correct < 0 or correct > total:
        raise ValueError(f"Invalid correct count {correct} for total {total}")

    # z-value lookup for common confidence levels
    z_values = {
        0.90: 1.64485,
        0.95: 1.95996,
        0.99: 2.57583,
    }
    z = z_values.get(confidence, 1.95996)

    p = correct / total
    z2 = z * z
    n = total

    denominator = 1.0 + (z2 / n)
    center = p + (z2 / (2.0 * n))
    spread = z * math.sqrt((p * (1.0 - p) / n) + (z2 / (4.0 * (n * n))))

    lower = (center - spread) / denominator
    return max(0.0, min(1.0, lower))


def recency_decay_weight(
    timestamp: datetime,
    reference_time: datetime | None = None,
    half_life_days: float = 90.0,
) -> float:
    """Computes exponential recency decay weight based on claim age.

    weight = 2 ^ (-delta_days / half_life_days)
    """
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    delta_seconds = (reference_time - timestamp).total_seconds()
    if delta_seconds < 0:
        return 1.0

    delta_days = delta_seconds / 86400.0
    return math.pow(2.0, -delta_days / half_life_days)


def evaluate_reliability(
    subject_name: str,
    subject_type: str,
    correct_count: int,
    sample_size: int,
    min_sample_threshold: int = 10,
    confidence: float = 0.95,
) -> ReliabilityMetrics:
    """Evaluates public reliability metrics, strictly enforcing the 10+ resolved claim threshold."""
    if sample_size < min_sample_threshold:
        return ReliabilityMetrics(
            subject_name=subject_name,
            subject_type=subject_type,
            sample_size=sample_size,
            correct_count=correct_count,
            wilson_lower_bound=None,
            is_insufficient_record=True,
            unweighted_accuracy=round(correct_count / sample_size, 4) if sample_size > 0 else 0.0,
        )

    w_score = wilson_lower_bound(correct_count, sample_size, confidence=confidence)
    return ReliabilityMetrics(
        subject_name=subject_name,
        subject_type=subject_type,
        sample_size=sample_size,
        correct_count=correct_count,
        wilson_lower_bound=round(w_score, 4),
        is_insufficient_record=False,
        unweighted_accuracy=round(correct_count / sample_size, 4),
    )


@dataclass(frozen=True)
class ComponentAccuracy:
    """Component scoring breakdown preserving partial correctness."""

    entity_accuracy: float | None
    direction_accuracy: float | None
    timing_accuracy: float | None
    fee_accuracy: float | None
    entity_evaluable: int
    direction_evaluable: int
    timing_evaluable: int
    fee_evaluable: int


def evaluate_component_accuracy(resolutions: list[Any]) -> ComponentAccuracy:
    """Evaluates component accuracy across a set of resolution records.

    Accepts list of ResolutionModel instances or dictionaries containing
    entity_correct, direction_correct, timing_correct, fee_correct.
    """
    counts: dict[str, list[int]] = {
        "entity": [0, 0],  # [correct, evaluable]
        "direction": [0, 0],
        "timing": [0, 0],
        "fee": [0, 0],
    }
    for r in resolutions:
        for comp in ("entity", "direction", "timing", "fee"):
            attr_name = f"{comp}_correct"
            val = getattr(r, attr_name, None) if hasattr(r, attr_name) else (r.get(attr_name) if isinstance(r, dict) else None)
            if val is not None:
                counts[comp][1] += 1
                if val is True:
                    counts[comp][0] += 1

    def calc_acc(comp: str) -> float | None:
        correct, total = counts[comp]
        return round(correct / total, 4) if total > 0 else None

    return ComponentAccuracy(
        entity_accuracy=calc_acc("entity"),
        direction_accuracy=calc_acc("direction"),
        timing_accuracy=calc_acc("timing"),
        fee_accuracy=calc_acc("fee"),
        entity_evaluable=counts["entity"][1],
        direction_evaluable=counts["direction"][1],
        timing_evaluable=counts["timing"][1],
        fee_evaluable=counts["fee"][1],
    )


@dataclass(frozen=True)
class DualReliabilityMetrics:
    """Dual reliability record isolating original reporting from repetition/aggregation."""

    subject_name: str
    subject_type: str
    overall: ReliabilityMetrics
    original: ReliabilityMetrics
    aggregation: ReliabilityMetrics
    component_accuracy: ComponentAccuracy | None = None


def evaluate_dual_reliability(
    subject_name: str,
    subject_type: str,
    correct_count_overall: int,
    sample_size_overall: int,
    correct_count_original: int,
    sample_size_original: int,
    correct_count_aggregation: int,
    sample_size_aggregation: int,
    resolutions: list[Any] | None = None,
    min_sample_threshold: int = 10,
    confidence: float = 0.95,
) -> DualReliabilityMetrics:
    """Evaluates separate reliability scores for original scoops and syndication/aggregation."""
    overall = evaluate_reliability(
        subject_name=subject_name,
        subject_type=subject_type,
        correct_count=correct_count_overall,
        sample_size=sample_size_overall,
        min_sample_threshold=min_sample_threshold,
        confidence=confidence,
    )
    original = evaluate_reliability(
        subject_name=subject_name,
        subject_type=subject_type,
        correct_count=correct_count_original,
        sample_size=sample_size_original,
        min_sample_threshold=min_sample_threshold,
        confidence=confidence,
    )
    aggregation = evaluate_reliability(
        subject_name=subject_name,
        subject_type=subject_type,
        correct_count=correct_count_aggregation,
        sample_size=sample_size_aggregation,
        min_sample_threshold=min_sample_threshold,
        confidence=confidence,
    )
    comp_acc = evaluate_component_accuracy(resolutions) if resolutions else None

    return DualReliabilityMetrics(
        subject_name=subject_name,
        subject_type=subject_type,
        overall=overall,
        original=original,
        aggregation=aggregation,
        component_accuracy=comp_acc,
    )
