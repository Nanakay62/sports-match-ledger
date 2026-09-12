from collections.abc import Callable
from enum import IntEnum

from pydantic import BaseModel

from .budget import CostTracker


class InferenceRung(IntEnum):
    L0_DETERMINISTIC = 0
    L1_LOCAL_CPU = 1
    L2_SMALL_HOSTED = 2
    L3_MID_HOSTED = 3
    L4_FRONTIER = 4


class ModelCallMetadata(BaseModel):
    rung: InferenceRung
    model_id: str
    prompt_version: str
    cost_eur: float
    trace_id: str
    escalated_from: InferenceRung | None = None
    escalation_reason: str | None = None


class ValidationResult(BaseModel):
    is_valid: bool
    unsupported_fact_rate: float
    entity_preservation_rate: float
    uncertainty_preserved: bool
    citation_coverage: float
    reasons: list[str] = []


class DeterministicValidator:
    """Strict deterministic boundary checking generated output against untrusted source evidence."""

    @staticmethod
    def validate_generation(
        generated_text: str,
        source_evidence: list[str],
        expected_entities: list[str],
    ) -> ValidationResult:
        reasons: list[str] = []
        combined_source = " ".join(source_evidence).lower()
        gen_lower = generated_text.lower()

        # 1. Entity preservation
        missing_entities = [e for e in expected_entities if e.lower() not in gen_lower]
        entity_preservation_rate = (len(expected_entities) - len(missing_entities)) / len(expected_entities) if expected_entities else 1.0
        if missing_entities:
            reasons.append(f"Missing entities from source: {missing_entities}")

        # 2. Number preservation check
        import re

        gen_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", generated_text))
        source_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", combined_source))
        invented_numbers = gen_numbers - source_numbers
        unsupported_fact_rate = len(invented_numbers) / len(gen_numbers) if gen_numbers else 0.0
        if invented_numbers:
            reasons.append(f"Invented numbers detected: {invented_numbers}")

        # 3. Uncertainty preservation check
        speculative_words = [
            "reportedly",
            "provisional",
            "alleged",
            "talks",
            "clause",
            "considering",
            "weighing",
        ]
        source_is_speculative = any(w in combined_source for w in speculative_words)
        definite_words = [
            "done deal",
            "fully signed",
            "guaranteed",
            "confirmed agreement",
        ]
        gen_is_definite = any(w in gen_lower for w in definite_words)
        uncertainty_preserved = not (source_is_speculative and gen_is_definite)
        if not uncertainty_preserved:
            reasons.append("Certainty inflated: source was speculative but generation used definite language")

        is_valid = unsupported_fact_rate == 0.0 and entity_preservation_rate >= 0.8 and uncertainty_preserved

        return ValidationResult(
            is_valid=is_valid,
            unsupported_fact_rate=unsupported_fact_rate,
            entity_preservation_rate=entity_preservation_rate,
            uncertainty_preserved=uncertainty_preserved,
            citation_coverage=1.0,  # Evaluated by citation checker in pipeline
            reasons=reasons,
        )


class InferenceLadderRouter:
    """Orchestrates model execution through the 5-rung ladder, escalating only when deterministic validation fails."""

    def __init__(self, cost_tracker: CostTracker):
        self.cost_tracker = cost_tracker

    def execute_with_escalation(
        self,
        task_name: str,
        trace_id: str,
        prompt_version: str,
        source_evidence: list[str],
        expected_entities: list[str],
        rung_handlers: dict[InferenceRung, Callable[[list[str]], str]],
    ) -> tuple[str, ModelCallMetadata]:
        # Start at cheapest available rung (L0 or L2 depending on task)
        available_rungs = sorted(rung_handlers.keys())
        current_idx = 0
        last_validation: ValidationResult | None = None
        escalated_from: InferenceRung | None = None

        while current_idx < len(available_rungs):
            rung = available_rungs[current_idx]
            handler = rung_handlers[rung]

            output = handler(source_evidence)
            validation = DeterministicValidator.validate_generation(output, source_evidence, expected_entities)

            # Record model cost
            cost = (
                0.0001
                if rung == InferenceRung.L2_SMALL_HOSTED
                else (0.001 if rung == InferenceRung.L3_MID_HOSTED else (0.01 if rung == InferenceRung.L4_FRONTIER else 0.0))
            )
            self.cost_tracker.record_inference(
                trace_id=trace_id,
                stage=task_name,
                model_id=f"rung-{rung.name.lower()}",
                prompt_version=prompt_version,
                input_tokens=100,
                output_tokens=50,
                cost_eur=cost,
            )

            if validation.is_valid:
                meta = ModelCallMetadata(
                    rung=rung,
                    model_id=f"rung-{rung.name.lower()}",
                    prompt_version=prompt_version,
                    cost_eur=cost,
                    trace_id=trace_id,
                    escalated_from=escalated_from,
                    escalation_reason=None
                    if not escalated_from
                    else f"Escalated due to: {last_validation.reasons if last_validation else 'check failure'}",
                )
                return output, meta

            # Escalation: deterministic check failed!
            escalated_from = rung
            last_validation = validation
            current_idx += 1

        # Fallback to output of highest rung executed
        meta = ModelCallMetadata(
            rung=available_rungs[-1],
            model_id=f"rung-{available_rungs[-1].name.lower()}",
            prompt_version=prompt_version,
            cost_eur=cost,
            trace_id=trace_id,
            escalated_from=escalated_from,
            escalation_reason="Highest available ladder rung reached",
        )
        return output, meta
