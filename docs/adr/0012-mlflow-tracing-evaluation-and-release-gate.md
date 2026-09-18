# ADR-0012: MLflow Tracing, Evaluation Datasets and the Release Gate

## Status
Accepted

## Context
Handbook Phase 8 (§16) requires that quality be measurable and every release reversible: every inference trace records cost and provenance, a golden evaluation dataset gates prompt/model changes on deterministic scorers, and production traffic is periodically converted into new labelled examples. Prior to this ADR, `packages/ai/tracing.py::MLflowTracer` and `packages/ai/eval_gate.py::ReleaseGateEvaluator` existed with test coverage, but three gaps remained:

1. `infra/docker-compose.yml`'s MLflow service wrote its SQLite backend store (`sqlite:///mlflow.db`) to the container's working directory root, outside the `mlflow_data` volume mount at `/mlflow`. Only artifacts persisted; all experiment/run metadata was lost on every container recreation.
2. CI Gate 6 ("MLflow Deterministic Scorer Gate") ran one hand-picked example inline in the workflow YAML against an older validator API, rather than the full 7-fixture golden set through `ReleaseGateEvaluator`.
3. There was no tooling to act on the handbook's instruction to "sample production traces weekly and convert human decisions into labelled examples" — only the policy statement.

## Decision
1. **Persistent MLflow backend store**: `infra/docker-compose.yml` now points `--backend-store-uri` at `sqlite:////mlflow/mlflow.db`, an absolute path inside the `mlflow_data`-backed `/mlflow` mount, alongside the existing `--default-artifact-root /mlflow/artifacts`. Verified by creating an experiment via the MLflow REST API, recreating the container against the same named volume, and confirming the experiment is still present.
2. **CI evaluation job wired to the real golden set**: `scripts/run_release_gate.py` loads every fixture in `tests/fixtures/eval/`, runs it through `ReleaseGateEvaluator.evaluate_release_gate`, and prints each threshold from §16.4 (unsupported-fact rate == 0, entity/number preservation >= 0.95, citation coverage == 1.0, adversarial resistance == 1.0) with a PASS/FAIL line per metric, exiting non-zero on failure. CI Gate 6 now runs this script instead of an inline single-example assertion.
3. **Weekly trace sampling**: `scripts/sample_traces_for_review.py` reads the local structured trace log (`data/traces/traces.jsonl`), selects traces from the last N days that either failed or touched a hosted model (L2+; deterministic L0/L1 work needs no human review), and writes a dated review queue to `data/review_queues/`. A human fills in `human_verdict` and `promote_to_golden_fixture`; approved rows become new files under `tests/fixtures/eval/`.

## Consequences
- **Positive**: MLflow survives container restarts and redeploys, matching the handbook's "Run MLflow locally as a Compose service with persistent storage." Prompt/model changes are now gated on the full golden set, not one example, with per-metric pass/fail visible in CI logs. There is now a runnable path from raw production traces to new golden fixtures, rather than an unenforced policy.
- **Negative**: The release-gate script and trace-sampling script are additive CLI tools with no scheduling of their own — the weekly cadence in §16.5 still depends on someone actually running `sample_traces_for_review.py` (or wiring it to a cron/CI schedule) each week; this ADR does not add that scheduling.
- **Follow-up**: A per-PR "projected cost delta" line (handbook §3.6: "Any pull request that changes a prompt, a schema or a batch size must state its cost-per-1000-events delta") is not implemented here — the golden fixtures evaluate already-generated text against ground truth and do not themselves invoke the AI Gateway, so there is no real cost signal to diff yet without also running generation. Tracked as a future addition once the release gate runs generation directly rather than evaluating pre-generated text.
