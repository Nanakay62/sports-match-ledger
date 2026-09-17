from collections.abc import Callable
from enum import IntEnum

from pydantic import BaseModel

from .budget import CostTracker
from .evidence_package import EvidencePackage


class InferenceRung(IntEnum):
    L0_DETERMINISTIC = 0
    L1_LOCAL_CPU = 1
    L2_SMALL_HOSTED = 2
    L3_MID_HOSTED = 3
    L4_FRONTIER = 4


class ModelCallMetadata(BaseModel):
    rung: InferenceRung
    model_id: str
    prompt_version: str
    cost_eur: float
    trace_id: str
    escalated_from: InferenceRung | None = None
    escalation_reason: str | None = None


class ValidationResult(BaseModel):
    is_valid: bool
    unsupported_fact_rate: float
    entity_preservation_rate: float
    uncertainty_preserved: bool
    citation_coverage: float
    invalid_citations: list[str] = []
    cited_fact_ids: list[str] = []
    reasons: list[str] = []


class DeterministicValidator:
    """Strict deterministic boundary checking generated output against untrusted source evidence."""

    @staticmethod
    def validate_generation(
        generated_text: str,
        source_evidence: list[str],
        expected_entities: list[str],
    ) -> ValidationResult:
        reasons: list[str] = []
        combined_source = " ".join(source_evidence).lower()
        gen_lower = generated_text.lower()

        # 1. Entity preservation
        missing_entities = [e for e in expected_entities if e.lower() not in gen_lower]
        entity_preservation_rate = (len(expected_entities) - len(missing_entities)) / len(expected_entities) if expected_entities else 1.0
        if missing_entities:
            reasons.append(f"Missing entities from source: {missing_entities}")

        # 2. Number preservation check
        import re

        gen_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", generated_text))
        source_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", combined_source))
        invented_numbers = gen_numbers - source_numbers
        unsupported_fact_rate = len(invented_numbers) / len(gen_numbers) if gen_numbers else 0.0
        if invented_numbers:
            reasons.append(f"Invented numbers detected: {invented_numbers}")

        # 3. Uncertainty preservation check
        speculative_words = [
            "reportedly",
            "provisional",
            "alleged",
            "talks",
            "clause",
            "considering",
            "weighing",
        ]
        source_is_speculative = any(w in combined_source for w in speculative_words)
        definite_words = [
            "done deal",
            "fully signed",
            "guaranteed",
            "confirmed agreement",
        ]
        gen_is_definite = any(w in gen_lower for w in definite_words)
        uncertainty_preserved = not (source_is_speculative and gen_is_definite)
        if not uncertainty_preserved:
            reasons.append("Certainty inflated: source was speculative but generation used definite language")

        is_valid = unsupported_fact_rate == 0.0 and entity_preservation_rate >= 0.8 and uncertainty_preserved

        return ValidationResult(
            is_valid=is_valid,
            unsupported_fact_rate=unsupported_fact_rate,
            entity_preservation_rate=entity_preservation_rate,
            uncertainty_preserved=uncertainty_preserved,
            citation_coverage=1.0,  # Evaluated by citation checker in pipeline
            reasons=reasons,
        )

    @staticmethod
    def validate_package_generation(
        generated_text: str,
        package: EvidencePackage,
    ) -> ValidationResult:
        """Deterministically validates a generated summary against an isolated EvidencePackage under Handbook §7 & §15."""
        import re

        reasons: list[str] = []
        gen_lower = generated_text.lower()

        # 1. Citation extraction & verification
        cited_tags = re.findall(r"\[((?:fact|claim-fact)-[a-zA-Z0-9_-]+)\]", generated_text)
        valid_fact_ids = package.all_fact_ids
        invalid_citations = [cid for cid in cited_tags if cid not in valid_fact_ids]
        if invalid_citations:
            for bad_cid in invalid_citations:
                reasons.append(f"Hallucinated fact ID cited: '{bad_cid}' is absent from EvidencePackage")

        # Citation coverage: check if generation contains valid citations when facts exist
        citation_coverage = 1.0
        if valid_fact_ids and not cited_tags:
            citation_coverage = 0.0
            reasons.append("Missing citation: generation contains no [fact-id] citations")

        # 2. Number & Fee preservation check
        # Strip citation brackets before extracting figures to avoid matching citation IDs as numbers
        text_without_citations = re.sub(r"\[(?:fact|claim-fact)-[a-zA-Z0-9_-]+\]", "", generated_text)
        gen_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", text_without_citations))

        allowed_number_sources: list[str] = []
        for f in package.verified_facts:
            allowed_number_sources.append(f.evidence_span)
            for v in f.qualifiers.values():
                allowed_number_sources.append(str(v))
        for c in package.uncertain_claims:
            allowed_number_sources.append(c.statement)

        combined_allowed = " ".join(allowed_number_sources)
        allowed_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", combined_allowed))
        invented_numbers = gen_numbers - allowed_numbers
        unsupported_fact_rate = len(invented_numbers) / len(gen_numbers) if gen_numbers else 0.0
        if invented_numbers:
            reasons.append(f"Invented numbers detected in generation: {sorted(invented_numbers)}")

        # 3. Uncertainty preservation check
        has_verified_deal = any(f.predicate in ["official_signing", "contract_extension"] for f in package.verified_facts)
        has_only_speculation = not has_verified_deal and len(package.uncertain_claims) > 0
        definite_words = [
            "done deal",
            "fully signed",
            "guaranteed",
            "confirmed agreement",
            "has signed",
            "officially signed",
            "is official",
        ]
        gen_is_definite = any(w in gen_lower for w in definite_words)
        uncertainty_preserved = True
        if has_only_speculation and gen_is_definite:
            uncertainty_preserved = False
            reasons.append(
                "Certainty inflated: evidence package contains only unconfirmed/speculative claims but generation asserted definite outcome"
            )

        # 4. Entity preservation
        expected_entities = list(package.entity_glossary.keys())
        missing_entities = [
            e for e in expected_entities if e.lower() not in gen_lower and package.entity_glossary[e].lower() not in gen_lower
        ]
        entity_preservation_rate = (len(expected_entities) - len(missing_entities)) / len(expected_entities) if expected_entities else 1.0
        if missing_entities:
            reasons.append(f"Missing expected glossary entities from generation: {missing_entities}")

        # 5. Banned hallucinated terms check (Handbook §15.4)
        banned_terms = ["munich bavaria", "bavaria munich", "sporting lisbon fc"]
        for b in banned_terms:
            if b in gen_lower:
                reasons.append(f"Forbidden hallucinated entity name detected: '{b}'")

        is_valid = (
            len(invalid_citations) == 0
            and unsupported_fact_rate == 0.0
            and uncertainty_preserved
            and entity_preservation_rate >= 0.8
            and not any("Forbidden hallucinated entity" in r for r in reasons)
        )

        return ValidationResult(
            is_valid=is_valid,
            unsupported_fact_rate=unsupported_fact_rate,
            entity_preservation_rate=entity_preservation_rate,
            uncertainty_preserved=uncertainty_preserved,
            citation_coverage=citation_coverage,
            invalid_citations=invalid_citations,
            cited_fact_ids=cited_tags,
            reasons=reasons,
        )


class InferenceLadderRouter:
    """Orchestrates model execution through the 5-rung ladder, escalating only when deterministic validation fails."""

    def __init__(self, cost_tracker: CostTracker):
        self.cost_tracker = cost_tracker

    def execute_with_escalation(
        self,
        task_name: str,
        trace_id: str,
        prompt_version: str,
        source_evidence: list[str],
        expected_entities: list[str],
        rung_handlers: dict[InferenceRung, Callable[[list[str]], str]],
    ) -> tuple[str, ModelCallMetadata]:
        # Start at cheapest available rung (L0 or L2 depending on task)
        available_rungs = sorted(rung_handlers.keys())
        current_idx = 0
        last_validation: ValidationResult | None = None
        escalated_from: InferenceRung | None = None

        while current_idx < len(available_rungs):
            rung = available_rungs[current_idx]
            handler = rung_handlers[rung]

            output = handler(source_evidence)
            validation = DeterministicValidator.validate_generation(output, source_evidence, expected_entities)

            # Record model cost
            cost = (
                0.0001
                if rung == InferenceRung.L2_SMALL_HOSTED
                else (0.001 if rung == InferenceRung.L3_MID_HOSTED else (0.01 if rung == InferenceRung.L4_FRONTIER else 0.0))
            )
            self.cost_tracker.record_inference(
                trace_id=trace_id,
                stage=task_name,
                model_id=f"rung-{rung.name.lower()}",
                prompt_version=prompt_version,
                input_tokens=100,
                output_tokens=50,
                cost_eur=cost,
            )

            if validation.is_valid:
                meta = ModelCallMetadata(
                    rung=rung,
                    model_id=f"rung-{rung.name.lower()}",
                    prompt_version=prompt_version,
                    cost_eur=cost,
                    trace_id=trace_id,
                    escalated_from=escalated_from,
                    escalation_reason=None
                    if not escalated_from
                    else f"Escalated due to: {last_validation.reasons if last_validation else 'check failure'}",
                )
                return output, meta

            # Escalation: deterministic check failed!
            escalated_from = rung
            last_validation = validation
            current_idx += 1

        # Fallback to output of highest rung executed
        meta = ModelCallMetadata(
            rung=available_rungs[-1],
            model_id=f"rung-{available_rungs[-1].name.lower()}",
            prompt_version=prompt_version,
            cost_eur=cost,
            trace_id=trace_id,
            escalated_from=escalated_from,
            escalation_reason="Highest available ladder rung reached",
        )
        return output, meta
