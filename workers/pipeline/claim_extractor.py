"""Deterministic and Model-Assisted Structured Claim Extractor.

Decomposes raw article reports into Handbook §5.2 structured triples:
(Subject Entity, Predicate, Object Entity, Qualifiers, Verbatim Evidence Span).

Operates at Inference Rung L0 (Deterministic) to guarantee zero inference cost.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from packages.common.entities import default_entity_graph
from packages.common.models import EntityType


@dataclass
class ExtractedClaimTriple:
    """Handbook §5.2 structured claim record."""

    subject_id: str | None
    subject_name: str | None
    predicate: str  # e.g., "official_signing", "agrees_terms", "submits_bid", "transfer_denied"
    object_id: str | None
    object_name: str | None
    qualifiers: dict[str, Any] = field(default_factory=dict)
    evidence_span: str | None = None
    resolvable: bool = True
    resolution_class: str = "binary"  # "binary", "continuous_fee", "date_bound"
    confidence: float = 1.0


# Predicate regex patterns with canonical mappings across supported languages
PREDICATE_PATTERNS: list[tuple[str, str, str]] = [
    # (predicate_name, regex_pattern, resolution_class)
    (
        "official_signing",
        r"(?:signs for|officially joins|has signed|completed transfer to|confirmed as new player|unveiled by|ha fichado por|firma por|nuevo jugador de|ha firmato con|ufficiale:|wechselt zu|unterschreibt bei|s'engage avec|rejoint)",
        "binary",
    ),
    (
        "agrees_terms",
        r"(?:agree personal terms|agreed personal terms|agrees terms|reaches agreement|verbal agreement|contract agreed|acuerda t[ée]rminos|acuerdo alcanzado|acuerdo verbal|raggiunge l'accordo|accordo verbale|termini personali|einigt sich|m[üu]ndliche einigung|trouve un accord|accord verbal)",
        "binary",
    ),
    (
        "submits_bid",
        r"(?:submits bid|makes offer|makes formal bid|bids|bid of|offer of|submits proposal|presenta oferta|hace oferta|propuesta formal|presenta offerta|offerta formale|ha offerto|gibt angebot ab|bietet|fait une offre)",
        "continuous_fee",
    ),
    (
        "medical_scheduled",
        r"(?:medical scheduled|undergoing medical|passed medical|completes medical|reconocimiento m[ée]dico|visite mediche|medizincheck|visite m[ée]dicale)",
        "binary",
    ),
    (
        "contract_extension",
        r"(?:extends contract|signs new deal|signs extension|new long-term contract|renews contract|renueva contrato|renueva con|estende contratto|rinnova con|verl[äa]ngert vertrag|prolonge son contrat)",
        "binary",
    ),
    (
        "transfer_denied",
        r"(?:denies|rejects move|rules out move|will not leave|dismisses rumours|desmiente|descarta salida|no saldr[áa]|smentisce|non lascer[àa]|dementiert|schlie[ßs]t\b.*?\baus\b|schlie[ßs]t wechsel aus|d[ée]ment|exclut un d[ée]part)",
        "binary",
    ),
    (
        "inquiry_made",
        r"(?:inquires about|inquired about|shows interest|interested in|monitors|approaches|se interesa por|interesado en|mostra interesse|interessato a|bekundet interesse|s'int[ée]resse [àa])",
        "binary",
    ),
]


class StructuredClaimExtractor:
    """Deterministic extractor for structured claims."""

    @staticmethod
    def extract_fee(text: str) -> float | None:
        """Extracts monetary fee normalized to EUR float value in millions."""
        # Match EUR / €
        eur_match = re.search(
            r"(?:EUR|€)\s*(\d+(?:\.\d+)?)\s*(?:m|million|millones|milioni|mio)?",
            text,
            flags=re.IGNORECASE,
        )
        if eur_match:
            try:
                return float(eur_match.group(1))
            except ValueError:
                pass

        # Match GBP / £ (approx 1.18 EUR)
        gbp_match = re.search(
            r"(?:£|GBP)\s*(\d+(?:\.\d+)?)\s*(?:m|million)?",
            text,
            flags=re.IGNORECASE,
        )
        if gbp_match:
            try:
                return round(float(gbp_match.group(1)) * 1.18, 2)
            except ValueError:
                pass

        # Match USD / $ (approx 0.92 EUR)
        usd_match = re.search(
            r"(?:\$|USD)\s*(\d+(?:\.\d+)?)\s*(?:m|million)?",
            text,
            flags=re.IGNORECASE,
        )
        if usd_match:
            try:
                return round(float(usd_match.group(1)) * 0.92, 2)
            except ValueError:
                pass

        return None

    @staticmethod
    def extract_contract_duration(text: str) -> int | None:
        """Extracts contract duration in years if present."""
        match = re.search(r"(\d+)[- ]year (?:contract|deal)", text, flags=re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None

    @classmethod
    def find_evidence_span(
        cls,
        body: str,
        subject_name: str | None,
        predicate_pattern: str | None,
        object_name: str | None,
    ) -> str | None:
        """Locates the exact verbatim sentence in the body serving as evidence for the claim.

        Guarantees that the returned span is a 100% exact substring of the body text.
        """
        if not body:
            return None

        # Split body into natural sentence boundaries
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if len(s.strip()) > 10]

        best_span: str | None = None
        best_score = 0

        for sentence in sentences:
            score = 0
            if subject_name and re.search(r"\b" + re.escape(subject_name) + r"\b", sentence, re.IGNORECASE):
                score += 3
            if object_name and re.search(r"\b" + re.escape(object_name) + r"\b", sentence, re.IGNORECASE):
                score += 2
            if predicate_pattern and re.search(predicate_pattern, sentence, re.IGNORECASE):
                score += 3

            if score > best_score:
                best_score = score
                best_span = sentence

        # Verify that best_span is an exact substring of body
        if best_span and best_span in body:
            return best_span

        # Fallback to the first sentence if it is contained
        if sentences and sentences[0] in body:
            return sentences[0]

        return None

    @classmethod
    def extract_structured_claim(
        cls,
        headline: str,
        body: str,
    ) -> ExtractedClaimTriple:
        """Deterministically extracts a structured claim triple from article text."""
        combined_text = f"{headline} {body}"

        # 1. Match canonical entities
        matched_entities = default_entity_graph.extract_entities(combined_text)

        subject_entity = None
        object_entity = None

        # Categorize into subject (player or manager) and object (club)
        for ent in matched_entities:
            if ent.type in {EntityType.PLAYER, EntityType.MANAGER} and not subject_entity:
                subject_entity = ent
            elif ent.type == EntityType.CLUB and not object_entity:
                object_entity = ent

        # If no player entity matched in graph, check for player name heuristic in headline
        if not subject_entity:
            # Look for 2-word capitalized phrase not matching known clubs
            words = headline.split()
            for i in range(len(words) - 1):
                cand = f"{words[i]} {words[i + 1]}".strip(" ,:.-")
                resolved = default_entity_graph.resolve_alias(cand)
                if resolved and resolved.type in {EntityType.PLAYER, EntityType.MANAGER}:
                    subject_entity = resolved
                    break

        # 2. Determine predicate
        detected_predicate = "transfer_linked"
        detected_res_class = "binary"
        detected_pattern = None

        for pred_name, pattern, res_class in PREDICATE_PATTERNS:
            if re.search(pattern, combined_text, flags=re.IGNORECASE):
                detected_predicate = pred_name
                detected_res_class = res_class
                detected_pattern = pattern
                break

        # 3. Extract qualifiers (fees, contract length)
        qualifiers: dict[str, Any] = {}
        fee_eur = cls.extract_fee(combined_text)
        if fee_eur is not None:
            qualifiers["fee_eur_millions"] = fee_eur
            detected_res_class = "continuous_fee"

        contract_years = cls.extract_contract_duration(combined_text)
        if contract_years is not None:
            qualifiers["contract_years"] = contract_years

        # 4. Extract exact verbatim evidence span
        sub_name = subject_entity.name if subject_entity else None
        obj_name = object_entity.name if object_entity else None
        evidence_span = cls.find_evidence_span(
            body=body,
            subject_name=sub_name,
            predicate_pattern=detected_pattern,
            object_name=obj_name,
        )

        confidence = 1.0 if (subject_entity and object_entity and detected_predicate != "transfer_linked") else 0.85

        return ExtractedClaimTriple(
            subject_id=subject_entity.id if subject_entity else None,
            subject_name=subject_entity.name if subject_entity else None,
            predicate=detected_predicate,
            object_id=object_entity.id if object_entity else None,
            object_name=object_entity.name if object_entity else None,
            qualifiers=qualifiers,
            evidence_span=evidence_span,
            resolvable=True,
            resolution_class=detected_res_class,
            confidence=confidence,
        )
