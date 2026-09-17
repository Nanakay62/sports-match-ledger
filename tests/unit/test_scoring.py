from datetime import datetime, timedelta, timezone

import pytest

from packages.common.scoring import (
    evaluate_component_accuracy,
    evaluate_dual_reliability,
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


def test_evaluate_component_accuracy():
    resolutions = [
        {"entity_correct": True, "direction_correct": True, "timing_correct": True, "fee_correct": True},
        {"entity_correct": True, "direction_correct": True, "timing_correct": False, "fee_correct": False},
        {"entity_correct": True, "direction_correct": False, "timing_correct": True, "fee_correct": None},
        {"entity_correct": False, "direction_correct": False, "timing_correct": None, "fee_correct": None},
    ]
    comp = evaluate_component_accuracy(resolutions)

    # Entity: 3 of 4 = 0.75
    assert comp.entity_accuracy == 0.75
    assert comp.entity_evaluable == 4

    # Direction: 2 of 4 = 0.50
    assert comp.direction_accuracy == 0.50
    assert comp.direction_evaluable == 4

    # Timing: 2 of 3 = 0.6667
    assert comp.timing_accuracy == pytest.approx(0.6667, abs=1e-3)
    assert comp.timing_evaluable == 3

    # Fee: 1 of 2 = 0.50
    assert comp.fee_accuracy == 0.50
    assert comp.fee_evaluable == 2


def test_evaluate_component_accuracy_empty():
    comp = evaluate_component_accuracy([])
    assert comp.entity_accuracy is None
    assert comp.direction_accuracy is None
    assert comp.timing_accuracy is None
    assert comp.fee_accuracy is None
    assert comp.entity_evaluable == 0


def test_evaluate_dual_reliability():
    dual = evaluate_dual_reliability(
        subject_name="Sky Sports",
        subject_type="outlet",
        correct_count_overall=18,
        sample_size_overall=20,
        correct_count_original=14,
        sample_size_original=15,
        correct_count_aggregation=4,
        sample_size_aggregation=5,
    )
    assert dual.overall.wilson_lower_bound is not None
    assert dual.original.wilson_lower_bound is not None
    # Original (14/15) is sufficient record (>=10)
    assert dual.original.is_insufficient_record is False
    # Aggregation (4/5) is insufficient record (<10)
    assert dual.aggregation.is_insufficient_record is True
    assert dual.aggregation.wilson_lower_bound is None
