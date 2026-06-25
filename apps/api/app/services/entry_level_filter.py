import re
from dataclasses import dataclass
from typing import Any


POSITIVE_PATTERNS = [
    (re.compile(r"\bgraduate\b", re.I), 3),
    (re.compile(r"\brecent graduate\b", re.I), 3),
    (re.compile(r"\bjunior\b", re.I), 3),
    (re.compile(r"\bentry[\s-]?level\b", re.I), 3),
    (re.compile(r"\bintern(ship)?\b", re.I), 2),
    (re.compile(r"\bassociate\b", re.I), 2),
    (re.compile(r"\b0\s*[-–]\s*2\s+years?\b", re.I), 3),
    (re.compile(r"\b0\s+to\s+2\s+years?\b", re.I), 3),
    (re.compile(r"\bno experience\b", re.I), 2),
]

TITLE_EXCLUDE_PATTERNS = [
    re.compile(r"\bsenior\b", re.I),
    re.compile(r"\blead\b", re.I),
    re.compile(r"\bprincipal\b", re.I),
    re.compile(r"\bmanager\b", re.I),
    re.compile(r"\bhead\s+of\b", re.I),
    re.compile(r"\bstaff\b", re.I),
]

TEXT_EXCLUDE_PATTERNS = [
    re.compile(r"\b[57]\+?\s+years?\b", re.I),
    re.compile(r"\b[57]\s+or\s+more\s+years?\b", re.I),
    re.compile(r"\b[57]\s*[-–]\s*\d+\s+years?\b", re.I),
]


@dataclass(frozen=True)
class EntryLevelResult:
    listing: dict[str, Any]
    score: int
    relevant: bool
    positive_signals: list[str]
    negative_signals: list[str]


def _listing_text(listing: dict[str, Any]) -> str:
    return " ".join(str(listing.get(key, "")) for key in ("title", "description"))


def score_listing(listing: dict[str, Any]) -> EntryLevelResult:
    title = str(listing.get("title", ""))
    text = _listing_text(listing)
    score = 0
    positive_signals: list[str] = []
    negative_signals: list[str] = []

    for pattern, weight in POSITIVE_PATTERNS:
        if pattern.search(text):
            score += weight
            positive_signals.append(pattern.pattern)

    for pattern in TITLE_EXCLUDE_PATTERNS:
        if pattern.search(title):
            score -= 10
            negative_signals.append(pattern.pattern)

    for pattern in TEXT_EXCLUDE_PATTERNS:
        if pattern.search(text):
            score -= 10
            negative_signals.append(pattern.pattern)

    return EntryLevelResult(
        listing=listing,
        score=score,
        relevant=not negative_signals,
        positive_signals=positive_signals,
        negative_signals=negative_signals,
    )


def tag_entry_level_listings(listings: list[dict[str, Any]]) -> list[EntryLevelResult]:
    return [score_listing(listing) for listing in listings]


def relevant_listings(results: list[EntryLevelResult]) -> list[dict[str, Any]]:
    return [result.listing for result in results if result.relevant]
