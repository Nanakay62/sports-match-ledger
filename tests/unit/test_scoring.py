from datetime import datetime, timedelta, timezone

import pytest

from packages.common.scoring import (
    evaluate_reliability,
    recency_decay_weight,
    wilson_lower_bound,
)


def test_wilson_lower_bound_zero_total():
    assert wilson_lower_bound(0, 0) == 0.0


def test_wilson_lower_bound_invalid_inputs():
    with pytest.raises(ValueError):
        wilson_lower_bound(5, 4)
    with pytest.raises(ValueError):
        wilson_lower_bound(-1, 5)


def test_wilson_penalizes_small_sample():
    # 1/1 is 100% accuracy, but small sample size yields lower bound around ~0.20
    score_1_of_1 = wilson_lower_bound(1, 1)
    # 34/41 is ~82.9% accuracy, but larger sample yields lower bound around ~0.69
    score_34_of_41 = wilson_lower_bound(34, 41)
    assert score_34_of_41 > score_1_of_1


def test_evaluate_reliability_insufficient_record():
    # Sample size 9 < threshold 10
    metrics = evaluate_reliability(
        subject_name="The Woodwork",
        subject_type="outlet",
        correct_count=8,
        sample_size=9,
        min_sample_threshold=10,
    )
    assert metrics.is_insufficient_record is True
    assert metrics.wilson_lower_bound is None
    assert metrics.sample_size == 9
    assert metrics.correct_count == 8


def test_evaluate_reliability_sufficient_record():
    # Sample size 10 >= threshold 10
    metrics = evaluate_reliability(
        subject_name="The Woodwork",
        subject_type="outlet",
        correct_count=9,
        sample_size=10,
        min_sample_threshold=10,
    )
    assert metrics.is_insufficient_record is False
    assert metrics.wilson_lower_bound is not None
    assert metrics.wilson_lower_bound > 0.5


def test_recency_decay():
    now = datetime.now(timezone.utc)
    half_life = 90.0

    w_now = recency_decay_weight(now, now, half_life_days=half_life)
    assert pytest.approx(w_now, rel=1e-3) == 1.0

    t_90d_ago = now - timedelta(days=90)
    w_90d = recency_decay_weight(t_90d_ago, now, half_life_days=half_life)
    assert pytest.approx(w_90d, rel=1e-2) == 0.5

    t_180d_ago = now - timedelta(days=180)
    w_180d = recency_decay_weight(t_180d_ago, now, half_life_days=half_life)
    assert pytest.approx(w_180d, rel=1e-2) == 0.25
