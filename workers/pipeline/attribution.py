import re
from datetime import datetime, timezone
from typing import Any

REPETITION_CUE_PATTERNS = [
    # "according to [Outlet/Reporter]", "reported by [Outlet/Reporter]"
    r"\b(?:according to|reported by|per|as reported by|as revealed by|as broken by|sourced by)\s+([A-Z][\w\s&.]+?)(?:[,\n.]|$)",
    # "[Outlet/Reporter] reports that", "[Outlet] understands that"
    r"\b([A-Z][\w\s&.]+?)\s+(?:reports that|understands that|claims that|has claimed that|stated that|reports|claims)\b",
    # "cites [Outlet] as saying", "citing [Outlet]"
    r"\b(?:citing|cites|cited by)\s+([A-Z][\w\s&.]+?)(?:[,\n.]|$)",
    # "told [Outlet]", "speaking to [Outlet]"
    r"\b(?:speaking to|told|in an interview with)\s+([A-Z][\w\s&.]+?)(?:[,\n.]|$)",
]

SYNDICATION_PATTERNS = [
    # "Source: [Outlet]"
    r"\bSource:\s*([A-Z][\w\s&.]+)",
    # "Via [Outlet]"
    r"\bVia\s+([A-Z][\w\s&.]+)",
    # "(Reporting by ..., editing by ...)"
    r"\(Reporting by\s+[^,]+,\s*editing by\s+[^)]+\)",
    # "Originally published on [Outlet]"
    r"\bOriginally published (?:by|on)\s+([A-Z][\w\s&.]+)",
]

FIRST_PARTY_EXCLUSIVE_PATTERNS = [
    r"\bcan exclusively reveal\b",
    r"\bcan confirm\b",
    r"\bour sources understand\b",
    r"\bsources tell\b",
    r"\bexclusive\b",
]


def detect_attribution_type(
    headline: str,
    body: str,
    outlet: str,
    reporter: str | None = None,
    existing_claims_on_event: list[Any] | None = None,
    article_published_at: datetime | None = None,
) -> tuple[str, str | None]:
    """Deterministically classifies an article's attribution type as 'first_party' or 'secondary'.

    Returns (attribution_type, referenced_source_or_reason).
    """
    combined_text = f"{headline}\n{body}"
    outlet_norm = outlet.strip().lower()
    reporter_norm = reporter.strip().lower() if reporter else ""

    # Check syndication and wire credit lines
    for pat in SYNDICATION_PATTERNS:
        match = re.search(pat, combined_text, flags=re.IGNORECASE)
        if match:
            cited = match.group(1).strip() if match.groups() else "wire_syndication"
            if cited.lower() not in outlet_norm:
                return "secondary", cited

    # Check repetition cue phrases
    for pat in REPETITION_CUE_PATTERNS:
        matches = re.finditer(pat, combined_text, flags=re.IGNORECASE)
        for m in matches:
            cited = m.group(1).strip().rstrip(" ,.-")
            cited_low = cited.lower()
            # Ignore if the article is attributing to its own outlet or reporter
            if outlet_norm in cited_low or cited_low in outlet_norm:
                continue
            if reporter_norm and (reporter_norm in cited_low or cited_low in reporter_norm):
                continue
            # Filter out common false positives like "according to reports", "according to sources"
            if cited_low in {"reports", "sources", "close sources", "club sources", "insiders", "the player"}:
                continue
            return "secondary", cited

    # Check if there are existing root claims on this event
    if existing_claims_on_event and article_published_at:
        # If there are existing claims, check temporal lag
        for c in existing_claims_on_event:
            c_time = getattr(c, "timestamp", None)
            if c_time:
                if c_time.tzinfo is None:
                    c_time = c_time.replace(tzinfo=timezone.utc)
                if article_published_at.tzinfo is None:
                    article_published_at = article_published_at.replace(tzinfo=timezone.utc)
                lag_seconds = (article_published_at - c_time).total_seconds()
                # If published > 10 minutes after first report and doesn't contain exclusive marker
                if lag_seconds > 600:
                    has_exclusive = any(re.search(pat, combined_text, flags=re.IGNORECASE) for pat in FIRST_PARTY_EXCLUSIVE_PATTERNS)
                    if not has_exclusive:
                        return "secondary", "temporal_lag_pickup"

    return "first_party", None
