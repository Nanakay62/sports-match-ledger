"""Sports News AI — Weekly Trace Sampling for Human Labelling (Handbook §16.5)

"Sample production traces weekly and convert human decisions into labelled
examples." Reads the local structured trace log (packages/ai/tracing.py writes
every inference trace to data/traces/traces.jsonl), takes the last 7 days,
and writes a labelling queue: one row per trace needing a human verdict
(correct / incorrect / needs-fix) that can be reviewed and then folded into
tests/fixtures/eval/ as new golden fixtures.

This does not label anything itself — it only selects what a human should look
at this week, with a bias toward what is actually worth reviewing: L2+ model
calls (deterministic L0/L1 work needs no review) and any trace that failed.

Usage: PYTHONPATH=. python scripts/sample_traces_for_review.py [--days 7] [--limit 50]
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TRACES_FILE = Path("data/traces/traces.jsonl")
OUTPUT_DIR = Path("data/review_queues")

# Deterministic L0/L1 work has no model in the loop and needs no human review;
# only model-touched stages are candidates for the weekly labelling queue.
REVIEWABLE_RUNGS = {"L2", "L3", "L4"}


def load_traces() -> list[dict]:
    if not TRACES_FILE.exists():
        return []
    traces = []
    with open(TRACES_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                traces.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return traces


def select_for_review(traces: list[dict], since: datetime, limit: int) -> list[dict]:
    candidates = []
    for t in traces:
        try:
            ts = datetime.fromisoformat(t["timestamp"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        if ts < since:
            continue
        is_failure = not t.get("success", True)
        touched_model = str(t.get("rung", "")).upper() in REVIEWABLE_RUNGS
        if is_failure or touched_model:
            candidates.append(t)

    # Failures first (highest-signal review material), then most recent.
    candidates.sort(key=lambda t: (t.get("success", True), t.get("timestamp", "")), reverse=False)
    return candidates[:limit]


def build_queue(selected: list[dict]) -> list[dict]:
    queue = []
    for t in selected:
        queue.append(
            {
                "trace_id": t.get("trace_id"),
                "stage_name": t.get("stage_name"),
                "model_id": t.get("model_id"),
                "prompt_version": t.get("prompt_version"),
                "rung": t.get("rung"),
                "cost_eur": t.get("cost_eur"),
                "success": t.get("success", True),
                "error": t.get("error"),
                "timestamp": t.get("timestamp"),
                "human_verdict": None,  # to be filled: "correct" | "incorrect" | "needs_fix"
                "notes": "",
                "promote_to_golden_fixture": False,
            }
        )
    return queue


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7, help="Look-back window in days (default 7)")
    parser.add_argument("--limit", type=int, default=50, help="Maximum traces to queue (default 50)")
    args = parser.parse_args()

    traces = load_traces()
    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    selected = select_for_review(traces, since=since, limit=args.limit)
    queue = build_queue(selected)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    week_label = datetime.now(timezone.utc).strftime("%Y-W%W")
    out_path = OUTPUT_DIR / f"review_queue_{week_label}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2)

    print(f"Scanned {len(traces)} total traces from {TRACES_FILE}")
    print(f"Selected {len(queue)} for review (last {args.days} days, model-touched or failed)")
    print(f"Wrote review queue: {out_path}")
    if not traces:
        print("No trace log found yet — this is expected before any inference traffic has run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
