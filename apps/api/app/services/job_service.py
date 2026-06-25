import json
import re
from collections import Counter, defaultdict

from app.schemas.analysis import LocationId, PathwayId
from app.services.paths import DATA_DIR
from app.services.skill_extractor import ALL_SKILLS, mentions_skill


PATHWAY_LABELS = {
    "ai_automation": "AI & Automation",
    "software_fullstack": "Graduate Software / Full-Stack",
    "embedded_firmware": "Embedded / Firmware",
}

LOCATION_LABELS = {
    "auckland": "Auckland",
    "new_zealand": "New Zealand",
    "remote": "Remote-friendly",
}

REQUIRED_RE = re.compile(r"\b(required|essential|must have)\b", re.I)


def load_jobs() -> list[dict]:
    return json.loads((DATA_DIR / "jobs_snapshot.json").read_text(encoding="utf-8"))


def filter_jobs(pathway: PathwayId, location: LocationId) -> list[dict]:
    jobs = [job for job in load_jobs() if job["pathway"] == pathway]
    if location == "new_zealand":
        return jobs
    return [job for job in jobs if job["location"] == LOCATION_LABELS[location]]


def demand_label(employer_count: int, total_employers: int) -> str:
    if total_employers == 0:
        return "Low signal"
    ratio = employer_count / total_employers
    if ratio >= 0.55:
        return "Core demand"
    if ratio >= 0.3:
        return "Growing signal"
    if ratio >= 0.12:
        return "Differentiator"
    return "Low signal"


def market_summary(pathway: PathwayId, location: LocationId) -> dict:
    jobs = filter_jobs(pathway, location)
    employers = {job["company"] for job in jobs}
    skill_listings: dict[str, int] = Counter()
    skill_employers: dict[str, set[str]] = defaultdict(set)
    required_counts: dict[str, int] = Counter()

    for job in jobs:
        text = f"{job['title']} {job['description']}"
        for skill in ALL_SKILLS:
            if mentions_skill(text, skill):
                skill_listings[skill] += 1
                skill_employers[skill].add(job["company"])
                nearby = text.lower()
                if REQUIRED_RE.search(nearby) and skill.lower() in nearby:
                    required_counts[skill] += 1

    skills = []
    for skill, listing_count in skill_listings.items():
        employer_count = len(skill_employers[skill])
        skills.append(
            {
                "name": skill,
                "listing_count": listing_count,
                "total_listings": len(jobs),
                "employer_count": employer_count,
                "required_count": required_counts[skill],
                "market_label": demand_label(employer_count, len(employers)),
                "market_evidence": f"{skill} appeared in {listing_count} of {len(jobs)} relevant roles ({required_counts[skill]} listed it as required).",
            }
        )

    skills.sort(key=lambda item: (item["employer_count"], item["required_count"], item["listing_count"]), reverse=True)
    return {
        "listing_count": len(jobs),
        "distinct_employers": len(employers),
        "location": LOCATION_LABELS[location],
        "role_pathway": PATHWAY_LABELS[pathway],
        "captured_at": "2026-06-25T10:00:00Z",
        "sources": ["Cached curated snapshot"],
        "skills": skills,
    }
