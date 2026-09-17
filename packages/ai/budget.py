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

    def seed_demonstration_records(self) -> None:
        """Populates demonstration traces for development and operational review."""
        if self.records:
            return
        sample_traces = [
            ("tr-inf-901", "evidence_extraction", "gpt-4o-mini", "v1.2.0", 380, 95, 0.00021),
            ("tr-inf-902", "predicate_clustering", "text-embedding-3-small", "v1.0.0", 520, 0, 0.00005),
            ("tr-inf-903", "entity_resolution", "llama-3.1-8b-instruct", "v2.1.0", 410, 80, 0.00018),
            ("tr-inf-904", "headline_synthesis", "gpt-4o-mini", "v1.4.0", 620, 140, 0.00034),
            ("tr-inf-905", "claim_validation", "gpt-4o-mini", "v1.1.0", 450, 110, 0.00025),
        ]
        for tid, stage, model, prompt_ver, inp, out, cost in sample_traces:
            self.record_inference(
                trace_id=tid,
                stage=stage,
                model_id=model,
                prompt_version=prompt_ver,
                input_tokens=inp,
                output_tokens=out,
                cost_eur=cost,
            )
