"""Handbook §13.5 Phase 5 acceptance check: certainty-marker accuracy on 100 fixture articles.

Loads tests/fixtures/claims/certainty_fixtures.json — 100 hand-labelled sentences
spanning en/es/it/de/fr and all seven claim predicates — runs each through the real
StructuredClaimExtractor, and asserts extraction matches the hand-labelled key at
95% or better on both the predicate and the derived certainty marker
(has_happened / agreed / expected / reported / rumoured / denied), per the
handbook's requirement: "100 fixture articles produce claims whose certainty
markers match a hand-labelled key at 95% or better."
"""

import json
from pathlib import Path

from workers.pipeline.claim_extractor import StructuredClaimExtractor

FIXTURES_PATH = Path("tests/fixtures/claims/certainty_fixtures.json")

# Maps the deterministic predicate produced by StructuredClaimExtractor to the
# certainty vocabulary the handbook asks claim extraction to preserve (§13.2):
# has_happened, agreed, expected, reported, rumoured, denied.
PREDICATE_TO_CERTAINTY: dict[str, str] = {
    "official_signing": "has_happened",
    "contract_extension": "has_happened",
    "agrees_terms": "agreed",
    "medical_scheduled": "expected",
    "submits_bid": "reported",
    "inquiry_made": "rumoured",
    "transfer_denied": "denied",
    "transfer_linked": "rumoured",
}

ACCURACY_THRESHOLD = 0.95


def _load_fixtures() -> list[dict]:
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_fixture_set_has_100_hand_labelled_articles():
    fixtures = _load_fixtures()
    assert len(fixtures) == 100
    # Every certainty category from the handbook vocabulary must be represented.
    represented = {fx["expected_certainty"] for fx in fixtures}
    assert represented == {"has_happened", "agreed", "expected", "reported", "rumoured", "denied"}
    # At least three languages beyond English must be represented.
    languages = {fx["language"] for fx in fixtures}
    assert len(languages) >= 4


def test_claim_extraction_certainty_marker_accuracy_at_least_95_percent():
    fixtures = _load_fixtures()
    predicate_correct = 0
    certainty_correct = 0
    predicate_mismatches: list[tuple[str, str, str]] = []
    certainty_mismatches: list[tuple[str, str, str]] = []

    for fx in fixtures:
        triple = StructuredClaimExtractor.extract_structured_claim(headline=fx["headline"], body=fx["body"])

        if triple.predicate == fx["expected_predicate"]:
            predicate_correct += 1
        else:
            predicate_mismatches.append((fx["id"], fx["expected_predicate"], triple.predicate))

        derived_certainty = PREDICATE_TO_CERTAINTY.get(triple.predicate, "rumoured")
        if derived_certainty == fx["expected_certainty"]:
            certainty_correct += 1
        else:
            certainty_mismatches.append((fx["id"], fx["expected_certainty"], derived_certainty))

    total = len(fixtures)
    predicate_accuracy = predicate_correct / total
    certainty_accuracy = certainty_correct / total

    assert predicate_accuracy >= ACCURACY_THRESHOLD, (
        f"Predicate accuracy {predicate_accuracy:.2%} below {ACCURACY_THRESHOLD:.0%} threshold. Mismatches: {predicate_mismatches}"
    )
    assert certainty_accuracy >= ACCURACY_THRESHOLD, (
        f"Certainty-marker accuracy {certainty_accuracy:.2%} below {ACCURACY_THRESHOLD:.0%} threshold. Mismatches: {certainty_mismatches}"
    )


def test_certainty_accuracy_reported_per_language():
    """Reports per-language accuracy so a regression in one language is visible, not averaged away."""
    fixtures = _load_fixtures()
    by_lang: dict[str, list[bool]] = {}
    for fx in fixtures:
        triple = StructuredClaimExtractor.extract_structured_claim(headline=fx["headline"], body=fx["body"])
        derived_certainty = PREDICATE_TO_CERTAINTY.get(triple.predicate, "rumoured")
        by_lang.setdefault(fx["language"], []).append(derived_certainty == fx["expected_certainty"])

    for lang, results in by_lang.items():
        accuracy = sum(results) / len(results)
        # No single language may fall below 85%, even though the blended average clears 95%.
        assert accuracy >= 0.85, f"Language '{lang}' certainty accuracy {accuracy:.2%} is too low ({len(results)} samples)"
