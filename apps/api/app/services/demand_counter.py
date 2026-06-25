import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from app.services.skill_extractor import ALL_SKILLS, mentions_skill


REQUIRED_PHRASE_RE = re.compile(r"\b(required|essential|must have|must-have|requirements?)\b", re.I)
PREFERRED_PHRASE_RE = re.compile(r"\b(nice to have|preferred|bonus|desirable)\b", re.I)
NEUTRAL_PHRASE_RE = re.compile(r"\b(experience with|familiarity|familiar with|exposure to)\b", re.I)


@dataclass(frozen=True)
class SkillDemand:
    skill: str
    listing_count: int
    total_listings: int
    employer_count: int
    required_count: int


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


def _is_required_mention(text: str, skill: str) -> bool:
    for sentence in _sentences(text):
        if not mentions_skill(sentence, skill):
            continue
        if PREFERRED_PHRASE_RE.search(sentence):
            return False
        if REQUIRED_PHRASE_RE.search(sentence):
            return True
        window = sentence[:160]
        if REQUIRED_PHRASE_RE.search(window) and not NEUTRAL_PHRASE_RE.search(sentence):
            return True
    return False


def count_skill_demand(listings: list[dict[str, Any]]) -> list[SkillDemand]:
    listing_counts: Counter[str] = Counter()
    required_counts: Counter[str] = Counter()
    employers_by_skill: dict[str, set[str]] = defaultdict(set)

    for listing in listings:
        text = f"{listing.get('title', '')} {listing.get('description', '')}"
        employer = str(listing.get("company", "")).strip()
        for skill in ALL_SKILLS:
            if mentions_skill(text, skill):
                listing_counts[skill] += 1
                if employer:
                    employers_by_skill[skill].add(employer)
                if _is_required_mention(text, skill):
                    required_counts[skill] += 1

    demand = [
        SkillDemand(
            skill=skill,
            listing_count=listing_count,
            total_listings=len(listings),
            employer_count=len(employers_by_skill[skill]),
            required_count=required_counts[skill],
        )
        for skill, listing_count in listing_counts.items()
    ]
    return sorted(demand, key=lambda item: (item.employer_count, item.required_count), reverse=True)
