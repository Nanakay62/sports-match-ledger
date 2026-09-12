import uuid
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


class MLflowTracer:
    """Telemetry and MLflow tracing interface for all AI Gateway model executions."""

    def __init__(self, experiment_name: str = "sports_news_ai_gateway"):
        self.experiment_name = experiment_name

    @staticmethod
    def generate_trace_id() -> str:
        return f"trc-{uuid.uuid4().hex[:12]}"

    @contextmanager
    def start_trace(
        self,
        stage_name: str,
        trace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[str, None, None]:
        tid = trace_id or self.generate_trace_id()
        # In production/integration, this attaches to mlflow.start_run()
        try:
            yield tid
        finally:
            pass
