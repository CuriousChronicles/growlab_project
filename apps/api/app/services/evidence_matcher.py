import json

from app.services.paths import DATA_DIR
from app.services.skill_extractor import find_resume_evidence, mentions_skill


ADJACENT_SKILLS = {
    "Docker": ["Linux", "Git", "REST APIs"],
    "CI/CD": ["Git", "GitHub", "Testing"],
    "RAG": ["LLMs", "Python", "Data Pipelines"],
    "Machine Learning": ["Python", "Pandas", "NumPy"],
    "PostgreSQL": ["SQL", "SQLite"],
    "React": ["TypeScript", "JavaScript", "HTML/CSS"],
    "STM32": ["Embedded C", "Microcontrollers", "C"],
    "CAN": ["Embedded C", "Microcontrollers"],
}


def load_demo_candidate() -> dict:
    return json.loads((DATA_DIR / "demo_candidate.json").read_text(encoding="utf-8"))


def demo_resume_text() -> str:
    candidate = load_demo_candidate()
    return "\n".join(candidate["resume_bullets"])


def repository_evidence(skill: str, repo_url: str | None, use_demo_data: bool) -> list[dict]:
    if not use_demo_data:
        return []
    candidate = load_demo_candidate()
    evidence = []
    for item in candidate["repository_evidence"]:
        text = f"{item['path']} {item['evidence']}"
        if mentions_skill(text, skill):
            evidence.append({"source": f"repository:{item['path']}", "excerpt": item["evidence"]})
    return evidence[:2]


def classify_skill(skill: str, resume_text: str, repo_url: str | None, use_demo_data: bool) -> dict:
    resume_hits = find_resume_evidence(resume_text, skill)
    repo_hits = repository_evidence(skill, repo_url, use_demo_data)
    evidence = [{"source": hit.source, "excerpt": hit.excerpt} for hit in resume_hits]
    evidence.extend(repo_hits)

    if any(hit.confidence == "high" for hit in resume_hits):
        return {
            "status": "strong_proof",
            "confidence": "high",
            "candidate_evidence": evidence,
            "recommended_action": "Surface this skill in a role-targeted project bullet with the concrete contribution intact.",
        }
    if repo_hits:
        return {
            "status": "hidden_proof",
            "confidence": "medium",
            "candidate_evidence": evidence,
            "recommended_action": "Make this proof visible in the resume or project README, and confirm you personally created or maintained it.",
        }
    if resume_hits:
        return {
            "status": "adjacent_proof",
            "confidence": "low",
            "candidate_evidence": evidence,
            "recommended_action": "Strengthen this with a concrete project outcome before making a stronger resume claim.",
        }

    adjacent = []
    for related in ADJACENT_SKILLS.get(skill, []):
        adjacent.extend(find_resume_evidence(resume_text, related))
    if adjacent:
        return {
            "status": "adjacent_proof",
            "confidence": "medium",
            "candidate_evidence": [{"source": hit.source, "excerpt": hit.excerpt} for hit in adjacent[:2]],
            "recommended_action": f"Extend an existing project so the adjacent {', '.join(ADJACENT_SKILLS[skill][:2])} evidence proves {skill} directly.",
        }

    return {
        "status": "no_proof_yet",
        "confidence": "low",
        "candidate_evidence": [],
        "recommended_action": "Build a small, reviewable proof artifact before adding this skill to a resume.",
    }
