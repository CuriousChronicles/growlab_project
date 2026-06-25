from dataclasses import dataclass
from typing import Literal

from app.services.demand_counter import SkillDemand
from app.services.skill_extractor import EvidenceHit


ProofStatus = Literal["strong_proof", "hidden_proof", "adjacent_proof", "no_proof"]

ADJACENT_SKILLS = {
    "Docker": ["Linux", "Git", "GitHub"],
    "CI/CD": ["Git", "GitHub", "Testing"],
    "RAG": ["LLMs", "Python", "Data Pipelines"],
    "Machine Learning": ["Python", "Pandas", "NumPy"],
    "PostgreSQL": ["SQL", "SQLite"],
    "React": ["TypeScript", "JavaScript", "HTML/CSS"],
    "Node.js": ["JavaScript", "TypeScript", "REST APIs"],
    "Data Pipelines": ["Python", "SQL", "Pandas"],
    "STM32": ["Embedded C", "Microcontrollers", "C"],
    "CAN": ["Embedded C", "Microcontrollers", "C"],
}


@dataclass(frozen=True)
class SkillEvidenceStatus:
    skill: str
    status: ProofStatus
    confidence: str
    demand: SkillDemand
    evidence: list[EvidenceHit]


def _best_confidence(hits: list[EvidenceHit]) -> str:
    order = {"high": 3, "medium": 2, "low": 1}
    if not hits:
        return "low"
    return max((hit.confidence for hit in hits), key=lambda confidence: order.get(confidence, 0))


def classify_skill_evidence(
    demand: SkillDemand,
    candidate_evidence: dict[str, list[EvidenceHit]],
) -> SkillEvidenceStatus:
    direct_hits = candidate_evidence.get(demand.skill, [])
    resume_hits = [hit for hit in direct_hits if hit.source == "resume_summary"]

    if resume_hits:
        return SkillEvidenceStatus(
            skill=demand.skill,
            status="strong_proof",
            confidence=_best_confidence(resume_hits),
            demand=demand,
            evidence=direct_hits,
        )

    if direct_hits:
        return SkillEvidenceStatus(
            skill=demand.skill,
            status="hidden_proof",
            confidence=_best_confidence(direct_hits),
            demand=demand,
            evidence=direct_hits,
        )

    adjacent_hits: list[EvidenceHit] = []
    for adjacent_skill in ADJACENT_SKILLS.get(demand.skill, []):
        adjacent_hits.extend(candidate_evidence.get(adjacent_skill, []))

    if adjacent_hits:
        return SkillEvidenceStatus(
            skill=demand.skill,
            status="adjacent_proof",
            confidence=_best_confidence(adjacent_hits),
            demand=demand,
            evidence=adjacent_hits[:3],
        )

    return SkillEvidenceStatus(
        skill=demand.skill,
        status="no_proof",
        confidence="low",
        demand=demand,
        evidence=[],
    )


def classify_in_demand_skills(
    demand: list[SkillDemand],
    candidate_evidence: dict[str, list[EvidenceHit]],
) -> list[SkillEvidenceStatus]:
    return [classify_skill_evidence(item, candidate_evidence) for item in demand]
