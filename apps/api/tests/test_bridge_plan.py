from app.schemas.analysis import CandidateEvidence, SkillAnalysis
from app.services.bridge_plan import build_bridge_plan


def skill(name: str, status: str, evidence: str) -> SkillAnalysis:
    return SkillAnalysis(
        name=name,
        market_label="Growing signal",
        demand_score=50,
        listing_count=4,
        total_listings=8,
        employer_count=4,
        required_count=2,
        status=status,
        confidence="medium",
        market_evidence=f"Present in 4 of 8 relevant listings for {name}.",
        candidate_evidence=[CandidateEvidence(source="project", excerpt=evidence)] if evidence else [],
        recommended_action="Add an evidence-backed resume or README bullet so this proof is visible.",
    )


def test_surface_resume_draft_is_clean_docker_bullet():
    plan = build_bridge_plan(
        [
            skill(
                "Docker",
                "hidden_proof",
                "EVolocity telemetry app used a Docker container to run the Node.js backend and PostgreSQL database during demos.",
            )
        ]
    )

    assert plan[0].resume_draft == "Containerised a full-stack telemetry app (Node.js backend + PostgreSQL) with Docker for reproducible team demos."
    assert "highlighting" not in plan[0].resume_draft


def test_non_surface_actions_do_not_emit_resume_drafts():
    plan = build_bridge_plan(
        [
            skill("RAG", "adjacent_proof", "Integrated Gemini LLM workflows."),
        ]
    )

    assert plan[0].action_type == "strengthen"
    assert plan[0].resume_draft is None


def test_placeholder_evidence_does_not_emit_resume_draft():
    plan = build_bridge_plan(
        [
            skill("Docker", "hidden_proof", "Docker: Evidence detected in your resume - confirm and refine"),
        ]
    )

    assert plan[0].action_type == "surface"
    assert plan[0].resume_draft is None
