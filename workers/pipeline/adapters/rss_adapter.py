import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class ProvenanceError(ValueError):
    """Raised when an incoming article fails provenance or attribution rules."""


class RawArticle(BaseModel):
    """Untrusted raw article input with strictly validated source attribution."""

    outlet: str = Field(..., min_length=1, description="Publishing outlet name")
    author: str | None = Field(None, description="Byline author or reporter")
    source_url: str = Field(..., min_length=10, description="Canonical source URL")
    published_at: datetime = Field(..., description="Timestamp of publication")
    headline: str = Field(..., min_length=3, description="Raw article headline")
    body: str = Field(..., min_length=10, description="Untrusted article body text")
    language: str = Field(default="en", description="Original publication language")

    @field_validator("source_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid source URL format: {v}")
        return v

    @field_validator("published_at")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v


KNOWN_OUTLET_NAMES = {
    "the athletic",
    "sky sports",
    "bbc sport",
    "the telegraph",
    "the daily telegraph",
    "the guardian",
    "the times",
    "the woodwork",
    "sky germany",
    "sky sport deutschland",
    "cbs sports",
    "espn",
    "reuters",
    "associated press",
}

GENERIC_BYLINE_SUBSTRINGS = [
    "staff",
    "editorial",
    "desk",
    "team",
    "reporters",
    "admin",
    "press",
    "newsroom",
    "agency",
]


def clean_extracted_byline(raw: str) -> str | None:
    """Cleans a raw author string, stripping prefixes, suffixes, and generic terms."""
    if not raw:
        return None
    cleaned = raw.strip()
    cleaned = re.sub(r"^(?:by|byline:|reported by|written by|words by)\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r",\s*(?:senior writer|chief football writer|northern football correspondent|football correspondent|correspondent|senior reporter|reporter|transfer expert|columnist|sports writer|expert|editor)\b.*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+in\s+[A-Za-z\s]+$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*\(.+?\)\s*$", "", cleaned)
    cleaned = cleaned.strip(" ,.-|:")
    if not cleaned:
        return None

    low = cleaned.lower()
    if low in KNOWN_OUTLET_NAMES:
        return None

    for sub in GENERIC_BYLINE_SUBSTRINGS:
        if sub in low:
            return None

    words = cleaned.split()
    if len(words) < 2 and not (cleaned.startswith("@") or cleaned in {"Plettigoal"}):
        return None
    return cleaned


def extract_byline(author: str | None, body: str, headline: str) -> str | None:
    """Extracts and normalises author byline from structured field or article text."""
    if author is not None:
        return clean_extracted_byline(author)

    # Fallback to body inspection when author field is omitted entirely
    # Leading byline at the very start of the text
    leading_match = re.match(
        r"^(?:By|BY|Author:|Words by)\s+([A-Z][\w'\-]+(?:\s+[A-Z][\w'\-]+){1,3})(?:,|\s*[-|]\s*|\s*\n|$)",
        body.strip(),
    )
    if leading_match:
        cand = clean_extracted_byline(leading_match.group(1))
        if cand:
            return cand

    # Trailing author credit line
    trailing_match = re.search(
        r"(?:^|\n)\s*(?:Written by|Byline:?|Words by)\s+([A-Z][\w'\-]+(?:\s+[A-Z][\w'\-]+){1,3})\s*(?:\n|$)",
        body,
        flags=re.IGNORECASE,
    )
    if trailing_match:
        cand = clean_extracted_byline(trailing_match.group(1))
        if cand:
            return cand

    return None


class ArticleIngestionAdapter:
    """Ingests raw source reports while preserving source provenance."""

    @staticmethod
    def ingest_payload(payload: dict[str, Any]) -> RawArticle:
        """Validates and parses a raw feed payload into a structured RawArticle."""
        mutable_payload = dict(payload)

        # Byline extraction and normalisation
        extracted_author = extract_byline(
            author=mutable_payload.get("author"),
            body=str(mutable_payload.get("body", "")),
            headline=str(mutable_payload.get("headline", "")),
        )
        mutable_payload["author"] = extracted_author

        try:
            article = RawArticle(**mutable_payload)
        except Exception as exc:
            raise ProvenanceError(f"Provenance validation failed: {exc}") from exc

        return article


def calculate_extraction_confidence(
    headline: str,
    body: str,
    author: str | None = None,
) -> float:
    """Calculates deterministic extraction confidence score in range [0.0, 1.0].

    Penalizes truncated bodies (<15 words), missing/short headlines, and boilerplate error text.
    Articles scoring below 0.50 are quarantined before ledger entry.
    """
    score = 1.0

    # Body validation
    words = body.strip().split()
    word_count = len(words)
    if word_count < 15:
        score -= 0.55
    elif word_count < 25:
        score -= 0.10

    # Headline validation
    clean_headline = headline.strip()
    hl_words = len(clean_headline.split())
    if hl_words < 3 or len(clean_headline) < 10:
        score -= 0.35

    # Boilerplate / paywall / error fragments
    low_body = body.lower()
    low_headline = clean_headline.lower()
    error_phrases = [
        "subscribe to read",
        "sign in to continue",
        "javascript is required",
        "page not found",
        "access denied",
        "403 forbidden",
        "404 not found",
        "error 404",
        "enable cookies",
        "captcha",
    ]
    for phrase in error_phrases:
        if phrase in low_body or phrase in low_headline:
            score -= 0.60
            break

    # Lack of byline has small penalty
    if not author:
        score -= 0.05

    return round(max(0.0, min(1.0, score)), 2)
