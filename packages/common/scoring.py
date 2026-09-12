import math
from dataclasses import dataclass
from datetime import datetime, timezone


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
