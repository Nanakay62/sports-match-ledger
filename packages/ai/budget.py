from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CostRecord:
    trace_id: str
    stage: str
    model_id: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    cost_eur: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BudgetExceededError(Exception):
    """Raised when an inference call would exceed the configured budget pool."""


class CostTracker:
    """Enforces strict separation between Build, Run, and Inference cost pools.

    Target: Blended AI cost per published event under EUR 0.02.
    """

    TARGET_COST_PER_EVENT_EUR: float = 0.02

    def __init__(self, max_event_budget_eur: float = 0.05):
        self.max_event_budget_eur = max_event_budget_eur
        self.records: list[CostRecord] = []
        self._stage_totals: dict[str, float] = {}

    def record_inference(
        self,
        trace_id: str,
        stage: str,
        model_id: str,
        prompt_version: str,
        input_tokens: int,
        output_tokens: int,
        cost_eur: float,
    ) -> CostRecord:
        record = CostRecord(
            trace_id=trace_id,
            stage=stage,
            model_id=model_id,
            prompt_version=prompt_version,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_eur=cost_eur,
        )
        self.records.append(record)
        self._stage_totals[stage] = self._stage_totals.get(stage, 0.0) + cost_eur

        event_cost = sum(r.cost_eur for r in self.records if r.trace_id == trace_id)
        if event_cost > self.max_event_budget_eur:
            raise BudgetExceededError(f"Trace {trace_id} exceeded budget cap: €{event_cost:.4f} > €{self.max_event_budget_eur:.4f}")

        return record

    def total_inference_cost(self) -> float:
        return sum(r.cost_eur for r in self.records)
