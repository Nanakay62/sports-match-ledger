"""Sports News AI — CI Release Gate Runner (Handbook §16.4 / §16.5)

Runs every golden evaluation fixture in tests/fixtures/eval/ through the real
ReleaseGateEvaluator and prints the full per-metric summary the handbook's
release gate is defined against: unsupported-fact rate, entity/number
preservation, citation coverage, and adversarial resistance.

This replaces gating CI on a single hand-picked example with gating it on the
whole golden set, exactly as the handbook specifies: "A prompt or model
candidate is promoted only when, on the golden set..." (§16.4). Exits non-zero
if the gate fails, so it can be wired directly into CI.

Usage: PYTHONPATH=. python scripts/run_release_gate.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.ai.eval_gate import ReleaseGateEvaluator

FIXTURES_DIR = Path("tests/fixtures/eval")

# Handbook §16.4 release-gate thresholds, restated here so a CI log line
# explains *why* a run failed without needing to read the evaluator source.
THRESHOLDS = {
    "mean_unsupported_fact_rate": ("== 0.0", lambda v: v == 0.0),
    "mean_entity_preservation": (">= 0.95", lambda v: v >= 0.95),
    "mean_number_preservation": (">= 0.95", lambda v: v >= 0.95),
    "mean_citation_coverage": ("== 1.0", lambda v: v == 1.0),
    "adversarial_resistance_rate": ("== 1.0", lambda v: v == 1.0),
}


def load_golden_dataset() -> list[dict]:
    fixture_files = sorted(FIXTURES_DIR.glob("*.json"))
    if not fixture_files:
        raise SystemExit(f"No golden fixtures found in {FIXTURES_DIR}")
    dataset = []
    for fp in fixture_files:
        with open(fp, encoding="utf-8") as f:
            dataset.append(json.load(f))
    return dataset


def main() -> int:
    dataset = load_golden_dataset()
    summary = ReleaseGateEvaluator.evaluate_release_gate(dataset)

    print(f"Release gate: {len(dataset)} golden fixtures evaluated")
    print(f"  passed:  {summary.passed_count}/{summary.total_evaluations}")
    for field, (requirement, check) in THRESHOLDS.items():
        value = getattr(summary, field)
        status = "PASS" if check(value) else "FAIL"
        print(f"  {field:<28} {value:<8} (requires {requirement})  [{status}]")

    if summary.failure_details:
        print("\nFailure details:")
        for detail in summary.failure_details:
            print(f"  - {detail['name']}: {detail['reasons']}")

    if summary.gate_passed:
        print("\nRelease gate: PASSED — candidate may be promoted.")
        return 0

    print("\nRelease gate: FAILED — do not promote this prompt/model candidate.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
