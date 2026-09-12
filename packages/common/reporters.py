import difflib
import re
import unicodedata
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CanonicalReporter:
    id: str
    name: str
    slug: str
    aliases: list[str] = field(default_factory=list)
    associated_outlets: list[str] = field(default_factory=list)
    social_handles: dict[str, str] = field(default_factory=dict)


def normalize_byline_text(text: str) -> str:
    """Normalises byline text by removing diacritics, honorifics, titles, and punctuation."""
    if not text:
        return ""

    # Remove diacritics
    nfkd = unicodedata.normalize("NFKD", text)
    cleaned = "".join(c for c in nfkd if not unicodedata.combining(c))

    # Strip prefixes like "By ", "Reported by "
    cleaned = re.sub(r"^(?:by|byline:|reported by|written by|words by)\s+", "", cleaned, flags=re.IGNORECASE)

    # Strip trailing titles, affiliations, and locations
    title_patterns = [
        r",\s*(?:senior writer|chief football writer|northern football correspondent|football correspondent|correspondent|senior reporter|reporter|transfer expert|columnist|sports writer|expert|editor)\b.*$",
        r"\s+in\s+[a-z\s]+$",
        r"\s+for\s+[a-z\s]+$",
    ]
    for pattern in title_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Remove punctuation except spaces and letters/numbers
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


SEED_REPORTERS: list[CanonicalReporter] = [
    CanonicalReporter(
        id="rep-fabrizio-romano",
        name="Fabrizio Romano",
        slug="fabrizio-romano",
        aliases=[
            "Fabrizio Romano",
            "Fabrizio Romano, Correspondent",
            "Fabrizio Romano, Transfer Expert",
            "F. Romano",
            "@FabrizioRomano",
        ],
        associated_outlets=["Sky Sports", "The Guardian", "CaughtOffside"],
        social_handles={"twitter": "@FabrizioRomano"},
    ),
    CanonicalReporter(
        id="rep-david-ornstein",
        name="David Ornstein",
        slug="david-ornstein",
        aliases=[
            "David Ornstein",
            "David Ornstein, Senior Writer",
            "David Ornstein, Football Correspondent",
            "D. Ornstein",
            "@David_Ornstein",
        ],
        associated_outlets=["The Athletic", "BBC Sport", "The New York Times"],
        social_handles={"twitter": "@David_Ornstein"},
    ),
    CanonicalReporter(
        id="rep-james-ducker",
        name="James Ducker",
        slug="james-ducker",
        aliases=[
            "James Ducker",
            "James Ducker, Northern Football Correspondent",
            "J. Ducker",
        ],
        associated_outlets=["The Daily Telegraph", "The Telegraph"],
        social_handles={"twitter": "@TelegraphDucker"},
    ),
    CanonicalReporter(
        id="rep-florian-plettenberg",
        name="Florian Plettenberg",
        slug="florian-plettenberg",
        aliases=[
            "Florian Plettenberg",
            "Florian Plettenberg, Sky Germany",
            "Florian Plettenberg, Reporter",
            "Plettigoal",
        ],
        associated_outlets=["Sky Germany", "Sky Sport Deutschland"],
        social_handles={"twitter": "@Plettigoal"},
    ),
    CanonicalReporter(
        id="rep-guillem-balague",
        name="Guillem Balague",
        slug="guillem-balague",
        aliases=[
            "Guillem Balague",
            "Guillem Balagué",
            "Guillem Balague, Football Expert",
            "G. Balague",
        ],
        associated_outlets=["BBC Sport", "CBS Sports"],
        social_handles={"twitter": "@GuillemBalague"},
    ),
]


class ReporterGraph:
    """Reporter lookup and alias resolution graph supporting a four-tier cascade."""

    def __init__(self, reporters: list[CanonicalReporter] | None = None):
        self._reporters_by_id: dict[str, CanonicalReporter] = {}
        self._alias_map: dict[str, CanonicalReporter] = {}
        self._normalised_alias_map: dict[str, CanonicalReporter] = {}
        for rep in reporters or SEED_REPORTERS:
            self.register_reporter(rep)

    def register_reporter(self, reporter: CanonicalReporter) -> None:
        self._reporters_by_id[reporter.id] = reporter

        # Exact alias mappings (lowercased)
        self._alias_map[reporter.name.strip().lower()] = reporter
        norm_canonical = normalize_byline_text(reporter.name)
        if norm_canonical:
            self._normalised_alias_map[norm_canonical] = reporter

        for alias in reporter.aliases:
            self._alias_map[alias.strip().lower()] = reporter
            norm_alias = normalize_byline_text(alias)
            if norm_alias:
                self._normalised_alias_map[norm_alias] = reporter

    def get_reporter_by_id(self, reporter_id: str) -> CanonicalReporter | None:
        return self._reporters_by_id.get(reporter_id)

    def resolve_byline(
        self,
        byline: str,
        outlet: str | None = None,
    ) -> tuple[CanonicalReporter | None, str]:
        """Resolves a byline string using the deterministic four-tier cascade.

        Tier 1: Exact alias match
        Tier 2: Normalised match (stripped punctuation, diacritics, and titles)
        Tier 3: Fuzzy match constrained by outlet (similarity >= 0.85)
        Tier 4: Unresolved queue (returns None)
        """
        raw_clean = byline.strip()
        if not raw_clean:
            return None, "unresolved"

        # Tier 1: Exact alias match
        exact_hit = self._alias_map.get(raw_clean.lower())
        if exact_hit:
            return exact_hit, "exact_alias"

        # Tier 2: Normalised match
        norm_key = normalize_byline_text(raw_clean)
        if norm_key:
            norm_hit = self._normalised_alias_map.get(norm_key)
            if norm_hit:
                return norm_hit, "normalised"

        # Tier 3: Fuzzy match constrained by outlet
        if outlet and norm_key:
            outlet_clean = outlet.strip().lower()
            best_match: CanonicalReporter | None = None
            best_score = 0.0

            for rep in self._reporters_by_id.values():
                # Constrain search strictly to reporters associated with this outlet
                is_associated = any(outlet_clean in assoc.lower() or assoc.lower() in outlet_clean for assoc in rep.associated_outlets)
                if not is_associated:
                    continue

                # Compare normalised candidate byline against reporter name and all aliases
                candidates_to_compare = [normalize_byline_text(rep.name)] + [normalize_byline_text(a) for a in rep.aliases]
                for cand in candidates_to_compare:
                    if not cand:
                        continue
                    ratio = difflib.SequenceMatcher(None, norm_key, cand).ratio()
                    if ratio > best_score:
                        best_score = ratio
                        best_match = rep

            if best_match and best_score >= 0.85:
                return best_match, "fuzzy_constrained"

        # Tier 4: Unresolved
        return None, "unresolved"


default_reporter_graph = ReporterGraph()
