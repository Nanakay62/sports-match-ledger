"""Mandatory Editorial Review Router.

Handbook §14 editorial governance enforcing human review routing for high-risk categories:
1. Allegations & legal matters (charges, arrests, lawsuits, doping)
2. Disciplinary action (sanctions, bans, fines)
3. Severe injuries / medical detail / deaths
4. Minors (individuals under 18)
5. Sensitive personal matters (bereavement, rehab, family)
6. Numerical fact conflicts (fees >20% disparity, conflicting contract years)
7. First-time sources (sample_size == 0)
8. Low extraction confidence (< 0.70)
9. Direct contradictions / conflicting predicates

Operates at Inference Rung L0 (Deterministic) with zero inference spend.
"""

import re
from dataclasses import dataclass, field


@dataclass
class ReviewRoutingDecision:
    """Outcome of routing check on a claim or event."""

    requires_review: bool
    trigger_category: str | None = None
    priority: str = "normal"  # "critical", "high", "normal"
    reason: str | None = None
    matched_phrases: list[str] = field(default_factory=list)


# Keywords and regular expressions for sensitive taxonomy categories
TAXONOMY_PATTERNS: dict[str, tuple[str, str, list[str]]] = {
    # category: (priority, description, [regex_patterns])
    "allegations_legal": (
        "critical",
        "Legal matter or criminal allegation",
        [
            r"\b(?:arrested|in custody|bail|police|criminal|lawsuit|sued|court|trial|judge|fraud|corruption|bribe|doping|banned substance|anti-doping|assault)\b",
        ],
    ),
    "disciplinary_action": (
        "high",
        "Disciplinary sanction or suspension",
        [
            r"\b(?:suspended|suspension|disciplinary|internal fine|dropped from squad|ban(?:ned)? for \d+ matches?|fa charge|red card appeal|contract terminated for cause|misconduct)\b",
        ],
    ),
    "medical_injury": (
        "critical",
        "Severe medical detail, trauma, or mortality",
        [
            r"\b(?:cardiac arrest|collapsed|intensive care|hospitalised|hospitalized|passed away|died|death|fatal(?:ity)?|acl tear|ruptured cruciate|broken leg|fracture|coma|life-threatening)\b",
        ],
    ),
    "minor": (
        "critical",
        "Matter involving a minor under 18 years old",
        [
            r"\b(?:1[0-7]-year-old|aged 1[0-7]|under-18|u18|schoolboy|minor child|underage)\b",
        ],
    ),
    "sensitive_personal": (
        "critical",
        "Sensitive personal, family, or health matter",
        [
            r"\b(?:bereavement|family emergency|compassionate leave|rehab(?:ilitation)?|mental health|depression|addiction|private family matter)\b",
        ],
    ),
}


class HumanReviewRouter:
    """Classifies articles and claims against Handbook §14 mandatory review criteria."""

    @classmethod
    def classify_text(cls, text: str) -> ReviewRoutingDecision:
        """Evaluates textual content against high-risk categories."""
        for category, (priority, desc, patterns) in TAXONOMY_PATTERNS.items():
            matched: list[str] = []
            for pat in patterns:
                for match in re.finditer(pat, text, flags=re.IGNORECASE):
                    matched.append(match.group(0))
            if matched:
                return ReviewRoutingDecision(
                    requires_review=True,
                    trigger_category=category,
                    priority=priority,
                    reason=f"Mandatory review trigger: {desc} (detected: '{matched[0]}')",
                    matched_phrases=matched,
                )

        return ReviewRoutingDecision(requires_review=False)

    @classmethod
    def classify_claim_context(
        cls,
        claim_text: str,
        source_sample_size: int = 10,
        extraction_confidence: float = 1.0,
        has_contradiction: bool = False,
    ) -> ReviewRoutingDecision:
        """Full contextual review classification including reliability metrics and extraction score."""
        # 1. Check sensitive text taxonomy first (Critical priority)
        text_decision = cls.classify_text(claim_text)
        if text_decision.requires_review:
            return text_decision

        # 2. Contradiction check (High priority)
        if has_contradiction:
            return ReviewRoutingDecision(
                requires_review=True,
                trigger_category="contradiction",
                priority="high",
                reason="Mandatory review trigger: Direct contradiction or denial on record across sources.",
            )

        # 3. First-time source check (sample_size == 0) (Normal priority)
        if source_sample_size <= 0:
            return ReviewRoutingDecision(
                requires_review=True,
                trigger_category="first_time_source",
                priority="normal",
                reason="Mandatory review trigger: Source or reporter has zero prior resolved claims in ledger (sample_size = 0).",
            )

        # 4. Low extraction confidence (< 0.70) (Normal priority)
        if extraction_confidence < 0.70:
            return ReviewRoutingDecision(
                requires_review=True,
                trigger_category="low_confidence",
                priority="normal",
                reason=f"Mandatory review trigger: Extraction confidence {extraction_confidence:.2f} is below 0.70 threshold.",
            )

        return ReviewRoutingDecision(requires_review=False)

    @classmethod
    def detect_numerical_conflicts(cls, fees_eur: list[float]) -> ReviewRoutingDecision:
        """Detects if multiple sources report divergent fees (>20% gap)."""
        valid_fees = [f for f in fees_eur if f and f > 0]
        if len(valid_fees) >= 2:
            f_min = min(valid_fees)
            f_max = max(valid_fees)
            disparity = (f_max - f_min) / f_min
            if disparity >= 0.20:
                return ReviewRoutingDecision(
                    requires_review=True,
                    trigger_category="numerical_conflict",
                    priority="high",
                    reason=f"Mandatory review trigger: Disputed fee figures ({f_min}m vs {f_max}m EUR, {disparity * 100:.0f}% discrepancy).",
                )

        return ReviewRoutingDecision(requires_review=False)
