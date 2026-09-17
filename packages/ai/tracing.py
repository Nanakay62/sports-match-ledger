import json
import logging
import os
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TRACES_DIR = Path("data/traces")
TRACES_FILE = TRACES_DIR / "traces.jsonl"


class MLflowTracer:
    """Telemetry and MLflow tracing interface for all AI Gateway model executions.

    Enforces AGENTS.md requirements:
    - Every generated asset records model ID, prompt version, cost and trace ID.
    - Offline fallback to local structured JSONL trace file.
    """

    def __init__(
        self,
        experiment_name: str = "sports_news_ai_gateway",
        log_to_file: bool = True,
    ) -> None:
        self.experiment_name = experiment_name
        self.log_to_file = log_to_file
        self._recent_traces: list[dict[str, Any]] = []

    @staticmethod
    def generate_trace_id() -> str:
        return f"trc-{uuid.uuid4().hex[:12]}"

    def record_trace(
        self,
        trace_id: str,
        stage_name: str,
        model_id: str,
        prompt_version: str,
        rung: str | int,
        cost_eur: float,
        latency_ms: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        success: bool = True,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Records a completed model inference trace."""
        trace_entry: dict[str, Any] = {
            "trace_id": trace_id,
            "stage_name": stage_name,
            "model_id": model_id,
            "prompt_version": prompt_version,
            "rung": str(rung),
            "cost_eur": round(cost_eur, 6),
            "latency_ms": round(latency_ms, 2),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "success": success,
            "error": error,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 1. Maintain in-memory ring buffer (up to 200 recent traces)
        self._recent_traces.append(trace_entry)
        if len(self._recent_traces) > 200:
            self._recent_traces.pop(0)

        # 2. Append to local JSONL trace log
        if self.log_to_file:
            try:
                TRACES_DIR.mkdir(parents=True, exist_ok=True)
                with open(TRACES_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(trace_entry) + "\n")
            except Exception as exc:
                logger.warning(f"Failed to append to local trace file: {exc}")

        # 3. Optional MLflow integration if available and configured
        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI")
        if mlflow_uri:
            try:
                import mlflow  # type: ignore

                mlflow.set_tracking_uri(mlflow_uri)
                mlflow.set_experiment(self.experiment_name)
                with mlflow.start_run(run_name=f"{stage_name}-{trace_id}", nested=True):
                    mlflow.log_params(
                        {
                            "model_id": model_id,
                            "prompt_version": prompt_version,
                            "rung": str(rung),
                            "stage": stage_name,
                            "trace_id": trace_id,
                        }
                    )
                    mlflow.log_metrics(
                        {
                            "cost_eur": cost_eur,
                            "latency_ms": latency_ms,
                            "input_tokens": float(input_tokens),
                            "output_tokens": float(output_tokens),
                        }
                    )
            except Exception as ml_exc:
                logger.debug(f"MLflow telemetry logging skipped: {ml_exc}")

        return trace_entry

    @contextmanager
    def start_trace(
        self,
        stage_name: str,
        trace_id: str | None = None,
        model_id: str = "deterministic-l0",
        prompt_version: str = "v1.0.0",
        rung: str | int = "L0",
        metadata: dict[str, Any] | None = None,
    ) -> Generator[str, None, None]:
        """Context manager tracing an inference execution."""
        tid = trace_id or self.generate_trace_id()
        start_time = time.monotonic()
        error_msg: str | None = None
        success = True

        try:
            yield tid
        except Exception as exc:
            success = False
            error_msg = str(exc)
            raise
        finally:
            elapsed_ms = (time.monotonic() - start_time) * 1000.0
            self.record_trace(
                trace_id=tid,
                stage_name=stage_name,
                model_id=model_id,
                prompt_version=prompt_version,
                rung=rung,
                cost_eur=0.0,
                latency_ms=elapsed_ms,
                success=success,
                error=error_msg,
                metadata=metadata,
            )

    def get_recent_traces(self, limit: int = 50) -> list[dict[str, Any]]:
        """Returns the most recent traces."""
        return list(reversed(self._recent_traces[-limit:]))


default_tracer = MLflowTracer()
