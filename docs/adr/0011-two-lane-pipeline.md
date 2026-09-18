# ADR-0011: Two-Lane Pipeline — Speed Versus Evidence

## Status
Accepted

## Context
Handbook §4.4 identifies a structural tension: being first is a competitive, saleable advantage (§1.4's "two-speed delivery" differentiator, §2.1's Data API line where "latency is the product"), but speed pressure is exactly the condition under which a system is tempted to publish something ungrounded. Handling both in a single linear pipeline forces a choice between being slow and safe, or fast and risky. The handbook resolves this by splitting the pipeline into two lanes with different latency budgets and different amounts of AI involvement, rather than picking one trade-off for every event.

## Decision
`workers/pipeline/speed_lane.py` (`SpeedLaneWorker`) runs deterministic-only work — dedup hash, entity match, novelty check — and emits an alert containing only the publisher's headline, source and entity tags, with no generated prose and no status claim beyond "newly reported, unverified." Target: under 90 seconds, achievable because nothing in this path touches a hosted model. `workers/pipeline/evidence_lane.py` (`EvidenceLaneWorker`) does everything expensive: claim extraction, validation, corroboration counting, and — only after all of that — grounded summary generation through the AI Gateway (ADR-0005's deterministic validation boundary; ADR-0012 covers the evaluation gate that gates a candidate generation before it can be promoted). Target: under 6 minutes. The two lanes write to the same event record but on independent timelines; a reader sees the speed-lane alert immediately and watches the page fill in as the evidence lane completes.

## Consequences
- **Positive**: the fastest path to a reader is also the path with the least AI involvement, which — as the handbook notes — means "the pressure to publish quickly can never become pressure to publish something invented" (§4.4). This is a safety property that falls out of the architecture rather than needing to be enforced by policy on every request.
- **Negative**: an event's public status can visibly change shape within its first few minutes (from a bare alert to a fully evidenced summary), which is a UX behaviour a reader needs to understand is normal, not a sign of instability — the interface communicates this via the explicit status vocabulary (ADR-0010) rather than leaving it unexplained.
