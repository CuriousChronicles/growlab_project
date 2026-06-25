from dataclasses import dataclass
from typing import Any

from app.schemas.candidate import DemoCandidate
from app.services.skill_taxonomy import load_skill_taxonomy, skill_pattern, variants_for

SKILL_TAXONOMY = load_skill_taxonomy().taxonomy
ALIASES = load_skill_taxonomy().aliases
ALL_SKILLS = load_skill_taxonomy().all_skills

""" Uses the taxonomy to scan text and produce structured evidence."""

def mentions_skill(text: str, skill: str) -> bool:
    haystack = text or ""
    for variant in variants_for(skill):
        if skill_pattern(variant).search(haystack):
            return True
    return False

def extract_skills(text: str) -> set[str]:
    return {skill for skill in ALL_SKILLS if mentions_skill(text, skill)}

@dataclass(frozen=True)
class EvidenceHit:
    source: str
    excerpt: str
    confidence: str
    evidence_index: int | None = None

EVIDENCE_CONFIDENCE = {
    "resume_summary": "high",
    "experience": "high",
    "project": "medium",
    "skills_section": "low",
}

def find_resume_evidence(resume_text: str, skill: str) -> list[EvidenceHit]:
    if not resume_text:
        return []
    sentences = [part.strip() for part in resume_text.replace("\n", ". ").split(".")]
    hits: list[EvidenceHit] = []
    for sentence in sentences:
        clean = " ".join(sentence.split())
        if clean and mentions_skill(clean, skill):
            hits.append(EvidenceHit(source="resume_summary", excerpt=clean[:220], confidence="high"))
    return hits[:3]

def extract_listing_skills(listing: dict[str, Any]) -> set[str]:
    text = f"{listing.get('title', '')} {listing.get('description', '')}"
    return extract_skills(text)


def extract_candidate_skill_evidence(candidate: DemoCandidate) -> dict[str, list[EvidenceHit]]:
    hits_by_skill: dict[str, list[EvidenceHit]] = {skill: [] for skill in ALL_SKILLS}

    for index, evidence in enumerate(candidate.evidence):
        for skill in extract_skills(evidence.excerpt):
            hits_by_skill[skill].append(
                EvidenceHit(
                    source=evidence.source,
                    excerpt=evidence.excerpt,
                    confidence=EVIDENCE_CONFIDENCE.get(evidence.source, "low"),
                    evidence_index=index,
                )
            )

    return {skill: hits for skill, hits in hits_by_skill.items() if hits}
