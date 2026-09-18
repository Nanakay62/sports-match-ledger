"""Handbook §15.6 Phase 7 acceptance checks run as a simulated full day of fixture traffic.

Builds 100 synthetic events — a realistic mix of officially-confirmed events (template
eligible, Rung L0) and developing/rumoured events (routed through the model-preferred
path, Rung L2) — through the real StructuredEvidenceSummarizer and CostTracker, then
asserts the two acceptance numbers the handbook calls out by name:

- "Deterministic templates handle at least 30% of published events."
- "Blended AI cost per published event sits under EUR 0.02 on a full day of
  fixture traffic."

Also exercises the cache-hit-is-zero-cost path across the batch (a repeated event
must not add to spend) and confirms cost is recorded per generated asset.
"""

from packages.ai.budget import CostTracker
from packages.ai.cache import SemanticCache
from packages.ai.evidence_package import ApprovedSource, EvidencePackage, UncertainClaim, VerifiedFact
from packages.ai.summarizer import StructuredEvidenceSummarizer

PAIRS = [
    ("Emeka Osei", "Arsenal"),
    ("Kylian Mbappé", "Real Madrid"),
    ("Jonas Lindqvist", "Bayern Munich"),
    ("Rafael Duarte", "Chelsea"),
    ("Kaito Mori", "Napoli"),
    ("Viktor Barski", "Barcelona"),
    ("Thiago Ferraz", "Manchester City"),
    ("Luca Brandt", "Brighton"),
]

TOTAL_EVENTS = 100
# The handbook's own worked example collapses ~2,000 articles to ~400 events, of
# which ~150 (well over 30%) are deterministic results/fixtures at zero cost. Mix
# a smaller, more conservative confirmed-official share here to prove the floor
# is met even under a generation-heavy day.
OFFICIAL_TEMPLATE_SHARE = 0.35


def _valid_model_handler(package: EvidencePackage) -> tuple[str, str]:
    """Simulates a well-behaved Rung L2 model call that only cites facts present in the package."""
    if package.uncertain_claims:
        c = package.uncertain_claims[0]
        return (
            f"Developing: {c.subject} linked with {c.object}",
            f"{c.outlet} reports {c.subject} is {c.marker} to join {c.object} [{c.fact_id}].",
        )
    return "Update", "Story developing [no-fact]."


def _build_official_package(idx: int, subj: str, obj: str) -> EvidencePackage:
    fact = VerifiedFact(
        fact_id="fact-1",
        claim_id=None,
        subject=subj,
        predicate="official_signing",
        object=obj,
        qualifiers={"fee_eur_millions": 10.0 + idx},
        evidence_span=f"{obj} confirm the signing of {subj}.",
        authority_rank=1,
    )
    return EvidencePackage(
        package_id=f"pkg-official-{idx}",
        event_id=f"evt-official-{idx}",
        verified_facts=[fact],
        entity_glossary={subj: subj, obj: obj},
        approved_sources=[ApprovedSource(outlet="Club Official", reliability_score=0.99)],
    )


def _build_developing_package(idx: int, subj: str, obj: str) -> EvidencePackage:
    claim = UncertainClaim(
        claim_id=idx,
        fact_id="claim-fact-1",
        marker="reported",
        statement=f"{obj} are reportedly interested in {subj}.",
        subject=subj,
        object=obj,
        outlet="Transfer Wire",
        reporter=None,
    )
    return EvidencePackage(
        package_id=f"pkg-developing-{idx}",
        event_id=f"evt-developing-{idx}",
        uncertain_claims=[claim],
        entity_glossary={subj: subj, obj: obj},
        approved_sources=[ApprovedSource(outlet="Transfer Wire", reliability_score=0.6)],
    )


def test_template_share_and_blended_cost_within_budget_over_100_events():
    tracker = CostTracker(max_event_budget_eur=1.0)
    cache = SemanticCache()
    summarizer = StructuredEvidenceSummarizer(cost_tracker=tracker, cache=cache)

    official_count = int(TOTAL_EVENTS * OFFICIAL_TEMPLATE_SHARE)
    developing_count = TOTAL_EVENTS - official_count

    template_hits = 0
    results = []

    for i in range(official_count):
        subj, obj = PAIRS[i % len(PAIRS)]
        package = _build_official_package(i, subj, obj)
        res = summarizer.summarize(package=package, trace_id=f"trc-official-{i}", prefer_model=False)
        results.append(res)
        if res.model_id.startswith("rung-l0"):
            template_hits += 1

    for i in range(developing_count):
        subj, obj = PAIRS[i % len(PAIRS)]
        package = _build_developing_package(i, subj, obj)
        res = summarizer.summarize(
            package=package,
            trace_id=f"trc-developing-{i}",
            prefer_model=True,
            custom_model_handler=_valid_model_handler,
        )
        results.append(res)
        if res.model_id.startswith("rung-l0"):
            template_hits += 1

    assert len(results) == TOTAL_EVENTS

    template_share = template_hits / TOTAL_EVENTS
    assert template_share >= 0.30, f"Template (Rung L0) share {template_share:.2%} is below the 30% floor"

    total_cost = sum(r.cost_eur for r in results)
    blended_cost_per_event = total_cost / TOTAL_EVENTS
    assert blended_cost_per_event < 0.02, (
        f"Blended cost per event €{blended_cost_per_event:.5f} exceeds the €0.02 budget "
        f"(total spend €{total_cost:.4f} across {TOTAL_EVENTS} events)"
    )

    # Cost per generated asset must be individually recorded and visible, not only blended.
    assert all(hasattr(r, "cost_eur") for r in results)
    assert all(r.trace_id for r in results)


def test_identical_package_rerun_within_the_batch_is_a_free_cache_hit():
    """A repeated event within the same day's run must not add to the day's spend."""
    tracker = CostTracker()
    cache = SemanticCache()
    summarizer = StructuredEvidenceSummarizer(cost_tracker=tracker, cache=cache)

    package = _build_official_package(0, "Emeka Osei", "Arsenal")

    first = summarizer.summarize(package=package, trace_id="trc-dup-1", prefer_model=False)
    second = summarizer.summarize(package=package, trace_id="trc-dup-2", prefer_model=False)

    assert first.cache_hit is False
    assert second.cache_hit is True
    assert second.cost_eur == 0.0
    assert second.summary_text == first.summary_text
