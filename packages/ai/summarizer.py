from collections.abc import Callable

from pydantic import BaseModel, Field

from .budget import CostTracker
from .cache import SemanticCache
from .evidence_package import EvidencePackage
from .ladder import DeterministicValidator


class SummaryResult(BaseModel):
    """Structured, verified summary output with provenance, citation tracking, and cost telemetry."""

    summary_text: str
    headline: str
    package_id: str
    target_lang: str = "en"
    cache_hit: bool = False
    cost_eur: float = 0.0
    model_id: str = "rung-l0-deterministic"
    prompt_version: str = "evidence-summary-v1"
    trace_id: str
    validation_passed: bool = True
    validation_reasons: list[str] = Field(default_factory=list)
    cited_fact_ids: list[str] = Field(default_factory=list)


class StructuredEvidenceSummarizer:
    """Generates evidence-grounded sports news summaries from an isolated EvidencePackage under Handbook §7.

    Guarantees:
    - Never receives raw article bodies; operates solely on structured EvidencePackage.
    - Deterministically validates all cited fact IDs ([fact-1], [claim-fact-1]).
    - Reruns with identical facts are instant semantic cache hits at €0.00 cost.
    - On validation failure, falls back to deterministic Rung L0 templates.
    """

    PROMPT_VERSION = "evidence-summary-v1"

    def __init__(self, cost_tracker: CostTracker | None = None, cache: SemanticCache | None = None):
        self.cost_tracker = cost_tracker or CostTracker()
        self.cache = cache or SemanticCache()

    def generate_l0_template_summary(self, package: EvidencePackage, target_lang: str = "en") -> tuple[str, str]:
        """Generates a verifiable summary and headline using pure deterministic templates (Rung L0, €0.00 cost)."""
        # Case 1: Contradictions / Disputes
        if package.contradictions:
            c = package.contradictions[0]
            # Find the claims
            claim_a = next((cl for cl in package.uncertain_claims if cl.claim_id == c.claim_a_id), None)
            claim_b = next((cl for cl in package.uncertain_claims if cl.claim_id == c.claim_b_id), None)
            subj = (claim_a.subject if claim_a else None) or (claim_b.subject if claim_b else "Subject")
            obj = (claim_a.object if claim_a else None) or (claim_b.object if claim_b else "Club")

            outlet_a = claim_a.outlet if claim_a else "Sources"
            tag_a = f"[{claim_a.fact_id}]" if claim_a else ""
            outlet_b = claim_b.outlet if claim_b else "Opposing reports"
            tag_b = f"[{claim_b.fact_id}]" if claim_b else ""

            headline = f"Disputed: {subj} and {obj}"
            summary = (
                f"{outlet_a} reports agreement between {subj} and {obj} {tag_a}. "
                f"However, {outlet_b} denies any deal has been agreed {tag_b}."
            )
            return headline, summary

        # Case 2: Verified Official Fact (signing, extension, confirmed match)
        if package.verified_facts:
            f = package.verified_facts[0]
            subj = package.entity_glossary.get(f.subject, f.subject)
            obj = package.entity_glossary.get(f.object, f.object)
            tag = f"[{f.fact_id}]"

            fee_eur = f.qualifiers.get("fee_eur_millions") or f.qualifiers.get("fee_eur")
            fee_text = f" for an estimated fee of €{fee_eur}m" if fee_eur else ""

            headline = f"Confirmed: {subj} completes move to {obj}"
            summary = f"{subj} has officially signed for {obj}{fee_text} {tag}."
            return headline, summary

        # Case 3: Uncertain / Developing Rumours
        if package.uncertain_claims:
            cl = package.uncertain_claims[0]
            subj = package.entity_glossary.get(cl.subject or "Subject", cl.subject or "Subject")
            obj = package.entity_glossary.get(cl.object or "Club", cl.object or "Club")
            tag = f"[{cl.fact_id}]"

            headline = f"Developing: {subj} linked with {obj}"
            summary = f"{cl.outlet} reports that {subj} is {cl.marker} to join {obj} {tag}."
            return headline, summary

        # Fallback empty case
        return "Update: Story details", "Developing story details are currently being corroborated."

    def summarize(
        self,
        package: EvidencePackage,
        trace_id: str,
        target_lang: str = "en",
        prefer_model: bool = False,
        custom_model_handler: Callable[[EvidencePackage], tuple[str, str]] | None = None,
    ) -> SummaryResult:
        """Generates a validated summary, checking semantic cache and enforcing citation verification."""
        cache_key = f"{package.package_id}:{self.PROMPT_VERSION}:{target_lang}"
        cached = self.cache.get(cache_key)
        if cached:
            return SummaryResult(
                summary_text=cached["summary_text"],
                headline=cached["headline"],
                package_id=package.package_id,
                target_lang=target_lang,
                cache_hit=True,
                cost_eur=0.0,
                model_id=cached.get("model_id", "cached"),
                prompt_version=self.PROMPT_VERSION,
                trace_id=trace_id,
                validation_passed=True,
                cited_fact_ids=cached.get("cited_fact_ids", []),
            )

        headline: str
        summary_text: str
        model_id: str = "rung-l0-deterministic"
        cost_eur: float = 0.0

        if prefer_model and custom_model_handler:
            # Rung L2 generation via custom handler / small hosted model
            model_headline, model_summary = custom_model_handler(package)
            model_id = "rung-l2-small-hosted"
            cost_eur = 0.00015

            # Deterministically validate model output
            val = DeterministicValidator.validate_package_generation(model_summary, package)
            if val.is_valid:
                headline, summary_text = model_headline, model_summary
                self.cost_tracker.record_inference(
                    trace_id=trace_id,
                    stage="structured_evidence_summarization",
                    model_id=model_id,
                    prompt_version=self.PROMPT_VERSION,
                    input_tokens=150,
                    output_tokens=60,
                    cost_eur=cost_eur,
                )
            else:
                # Validation check failed: safely fall back to Rung L0 template!
                template_h, template_s = self.generate_l0_template_summary(package, target_lang=target_lang)
                headline, summary_text = template_h, template_s
                model_id = "rung-l0-deterministic-fallback"
                cost_eur = 0.0
                val = DeterministicValidator.validate_package_generation(summary_text, package)
        else:
            # Rung L0 deterministic template
            headline, summary_text = self.generate_l0_template_summary(package, target_lang=target_lang)
            val = DeterministicValidator.validate_package_generation(summary_text, package)
            self.cost_tracker.record_inference(
                trace_id=trace_id,
                stage="structured_evidence_summarization",
                model_id=model_id,
                prompt_version=self.PROMPT_VERSION,
                input_tokens=80,
                output_tokens=40,
                cost_eur=0.0,
            )

        result_data = {
            "summary_text": summary_text,
            "headline": headline,
            "package_id": package.package_id,
            "target_lang": target_lang,
            "model_id": model_id,
            "cited_fact_ids": val.cited_fact_ids,
        }
        self.cache.set(cache_key, result_data)

        return SummaryResult(
            summary_text=summary_text,
            headline=headline,
            package_id=package.package_id,
            target_lang=target_lang,
            cache_hit=False,
            cost_eur=cost_eur,
            model_id=model_id,
            prompt_version=self.PROMPT_VERSION,
            trace_id=trace_id,
            validation_passed=val.is_valid,
            validation_reasons=val.reasons,
            cited_fact_ids=val.cited_fact_ids,
        )
