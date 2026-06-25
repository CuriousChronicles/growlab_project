from app.services.demand_counter import SkillDemand
from app.services.evidence_classifier import classify_skill_evidence
from app.services.skill_extractor import EvidenceHit


def demand(skill: str) -> SkillDemand:
    return SkillDemand(skill=skill, listing_count=3, total_listings=5, employer_count=2, required_count=1)


def test_resume_summary_direct_hit_is_strong_proof():
    result = classify_skill_evidence(
        demand("Python"),
        {
            "Python": [
                EvidenceHit(
                    source="resume_summary",
                    excerpt="Built automation tooling with Python.",
                    confidence="high",
                )
            ]
        },
    )

    assert result.status == "strong_proof"
    assert result.confidence == "high"


def test_project_only_direct_hit_is_hidden_proof():
    result = classify_skill_evidence(
        demand("Docker"),
        {
            "Docker": [
                EvidenceHit(
                    source="project",
                    excerpt="Project used a Docker container for repeatable demos.",
                    confidence="medium",
                )
            ]
        },
    )

    assert result.status == "hidden_proof"
    assert result.confidence == "medium"


def test_related_skill_hit_is_adjacent_proof():
    result = classify_skill_evidence(
        demand("RAG"),
        {
            "LLMs": [
                EvidenceHit(
                    source="resume_summary",
                    excerpt="Integrated Gemini LLM workflows.",
                    confidence="high",
                )
            ]
        },
    )

    assert result.status == "adjacent_proof"


def test_missing_evidence_is_no_proof():
    result = classify_skill_evidence(demand("AWS"), {})

    assert result.status == "no_proof"
