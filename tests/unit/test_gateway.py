import pytest

from packages.ai.budget import BudgetExceededError, CostTracker
from packages.ai.ladder import DeterministicValidator


def test_validator_detects_invented_numbers():
    source = ["Arsenal have submitted a £45m bid for Emeka Osei."]
    # Generation introduces an unverified €60m
    gen_with_invented_number = "Arsenal agreed a €60m deal for Emeka Osei."

    res = DeterministicValidator.validate_generation(
        generated_text=gen_with_invented_number,
        source_evidence=source,
        expected_entities=["Arsenal", "Emeka Osei"],
    )
    assert res.is_valid is False
    assert res.unsupported_fact_rate > 0.0
    assert any("Invented numbers" in r for r in res.reasons)


def test_validator_preserves_entities():
    source = ["Real Madrid opened talks for Jonas Lindqvist."]
    gen_missing_entity = "Real Madrid opened talks for the striker."

    res = DeterministicValidator.validate_generation(
        generated_text=gen_missing_entity,
        source_evidence=source,
        expected_entities=["Real Madrid", "Jonas Lindqvist"],
    )
    assert res.is_valid is False
    assert res.entity_preservation_rate < 1.0


def test_validator_detects_certainty_inflation():
    source = ["Chelsea are weighing a provisional move for Rafael Duarte."]
    gen_inflated = "Chelsea have signed a done deal with Rafael Duarte."

    res = DeterministicValidator.validate_generation(
        generated_text=gen_inflated,
        source_evidence=source,
        expected_entities=["Chelsea", "Rafael Duarte"],
    )
    assert res.is_valid is False
    assert res.uncertainty_preserved is False


def test_budget_tracker_enforces_cap():
    tracker = CostTracker(max_event_budget_eur=0.03)

    # 1st call within budget
    tracker.record_inference(
        trace_id="trc-001",
        stage="extraction",
        model_id="rung-l2",
        prompt_version="v1.0",
        input_tokens=100,
        output_tokens=50,
        cost_eur=0.015,
    )

    # 2nd call exceeds 0.03 cap
    with pytest.raises(BudgetExceededError):
        tracker.record_inference(
            trace_id="trc-001",
            stage="synthesis",
            model_id="rung-l4",
            prompt_version="v1.0",
            input_tokens=500,
            output_tokens=200,
            cost_eur=0.020,
        )
