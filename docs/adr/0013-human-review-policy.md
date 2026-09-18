# ADR-0013: Human-Review Policy and High-Risk Categories

## Status
Accepted

## Context
Handbook §14.3 requires mandatory human review for a specific set of high-risk categories, on the grounds that these are exactly the situations where an automation error causes real harm to real people — a wrongly automated allegation, disciplinary claim, or report involving a minor is a different order of mistake than a wrong transfer fee. Leaving this to editorial judgement alone, with no deterministic backstop, risks the policy being applied inconsistently under deadline pressure.

ADR-0006 already established that the review queue isolates "high-risk items (allegations, numerical discrepancies, single-source leaks)" as part of the editorial control plane — that ADR is the record of *that* the queue exists and *what happens* once an item lands in it (an editor confirms, disputes or corrects, never a raw `UPDATE`). This ADR is the record of the routing policy that decides what lands there in the first place: the specific, versioned taxonomy `HumanReviewRouter` actually implements, which ADR-0006 only referenced by example rather than specifying in full.

## Decision
`HumanReviewRouter` (`workers/pipeline/review_router.py`) runs at Rung L0 (zero inference cost, so there is no cost incentive to skip it) and routes to mandatory human review on nine triggers matching Handbook §14.3 exactly: allegations/legal matters, disciplinary action, severe injury/medical detail/death, anything involving a minor, sensitive personal matters, numerical fact conflicts (fees differing by more than 20%, conflicting contract years), first-time sources (zero sample size), low extraction confidence (below 0.70), and direct contradictions between claims. Each category is matched via an explicit, auditable regex taxonomy (`TAXONOMY_PATTERNS`) rather than a model judgement call, with a priority (`critical`/`high`/`normal`) and the matched phrase recorded on the routing decision — so an editor can see *why* an item was flagged, not just that it was. These routing decisions feed the same review queue and editorial workflow ADR-0006 defines; `apps/api/app/routers/admin.py` and `apps/web/app/admin/review/page.tsx` surface them for one-click editorial confirmation, and every decision is logged as a labelled evaluation example (`EditorialEvaluationLogModel`) per §14's "your review queue is also your training data."

## Consequences
- **Positive**: the set of things that force a human into the loop is a fixed, versioned list in source control, not a matter of individual editorial memory — and because it runs at L0, expanding the taxonomy never touches the inference budget.
- **Negative**: regex/keyword matching over free text will both over-trigger (a false positive on an injury-adjacent word used non-medically) and under-trigger (a phrasing the taxonomy doesn't anticipate) at the margins. This is an accepted trade-off — a deterministic, explainable filter that sometimes over-flags is preferable to a model-based classifier that would be faster to fool and harder to audit for exactly the categories where getting it wrong matters most.
