import time

from app.schemas.analysis import CandidateEvidence, SkillAnalysis
from app.services.bridge_plan import build_bridge_plan


def skill(name: str, status: str, evidence: str, source: str = "project", employer_count: int = 4) -> SkillAnalysis:
    return SkillAnalysis(
        name=name,
        market_label="Growing signal",
        demand_score=50,
        listing_count=4,
        total_listings=8,
        employer_count=employer_count,
        required_count=2,
        status=status,
        confidence="medium",
        market_evidence=f"Present in 4 of 8 relevant listings for {name}.",
        candidate_evidence=[CandidateEvidence(source=source, excerpt=evidence)] if evidence else [],
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
    assert plan[0].resume_draft_ai_refined is False
    assert "highlighting" not in plan[0].resume_draft


def test_non_surface_actions_do_not_emit_resume_drafts():
    plan = build_bridge_plan(
        [
            skill("RAG", "adjacent_proof", "Integrated Gemini LLM workflows."),
        ]
    )

    assert plan[0].action_type == "strengthen"
    assert plan[0].resume_draft is None


def test_non_surface_actions_do_not_call_llm_provider():
    class Provider:
        def refine_resume_draft(self, skill: SkillAnalysis, template_draft: str, voice_context: str) -> str:
            raise AssertionError("strengthen actions must not request resume bullet refinement")

    plan = build_bridge_plan(
        [
            skill("RAG", "adjacent_proof", "Integrated Gemini LLM workflows for summarisation."),
        ],
        resume_draft_provider=Provider(),
    )

    assert plan[0].action_type == "strengthen"
    assert plan[0].resume_draft is None
    assert plan[0].resume_draft_source is None


def test_surface_actions_prefer_concrete_project_evidence_over_skills_section():
    plan = build_bridge_plan(
        [
            skill(
                "SQL",
                "hidden_proof",
                "Skills: Python, SQL, PostgreSQL, Git, GitHub.",
                source="skills_section",
                employer_count=8,
            ),
            skill(
                "Docker",
                "hidden_proof",
                "EVolocity telemetry app used a Docker container to run the Node.js backend and PostgreSQL database during demos.",
                source="project",
                employer_count=4,
            ),
        ]
    )

    assert plan[0].action_type == "surface"
    assert plan[0].title == "Surface Docker"
    assert "telemetry app" in (plan[0].resume_draft or "")


def test_bridge_plan_does_not_repeat_git_and_github_surface_actions():
    shared_evidence = (
        "Used Git and GitHub pull requests to review firmware and capstone changes, "
        "keep issue history visible, and coordinate integration work."
    )

    plan = build_bridge_plan(
        [
            skill(
                "Docker",
                "hidden_proof",
                "EVolocity telemetry app used a Docker container for repeatable demos.",
                employer_count=10,
            ),
            skill("Git", "hidden_proof", shared_evidence, source="experience", employer_count=8),
            skill("GitHub", "hidden_proof", shared_evidence, source="experience", employer_count=8),
            skill("SQL", "hidden_proof", "Used SQL-backed storage in the Jarvis automation project.", employer_count=7),
        ]
    )

    titles = [item.title for item in plan]

    assert "Surface Git" in titles
    assert "Surface GitHub" not in titles
    assert "Surface SQL" in titles


def test_placeholder_evidence_does_not_emit_resume_draft():
    plan = build_bridge_plan(
        [
            skill("Docker", "hidden_proof", "Docker: Evidence detected in your resume - confirm and refine"),
        ]
    )

    assert plan[0].action_type == "surface"
    assert plan[0].resume_draft is None


def test_llm_provider_can_refine_resume_draft_wording_only():
    class Provider:
        def refine_resume_draft(self, skill: SkillAnalysis, template_draft: str, voice_context: str) -> str:
            assert skill.name == "Docker"
            assert "telemetry app" in template_draft
            assert "capstone" in voice_context
            return "Containerised the EVolocity telemetry app backend and PostgreSQL setup for repeatable team demos."

    plan = build_bridge_plan(
        [
            skill(
                "Docker",
                "hidden_proof",
                "EVolocity telemetry app used a Docker container to run the Node.js backend and PostgreSQL database during demos.",
            )
        ],
        resume_draft_provider=Provider(),
        voice_context="EVolocity capstone telemetry platform.",
    )

    assert plan[0].resume_draft == "Containerised the EVolocity telemetry app backend and PostgreSQL setup for repeatable team demos."
    assert plan[0].resume_draft_ai_refined is True


def test_llm_provider_failure_falls_back_to_template_silently():
    class Provider:
        def refine_resume_draft(self, skill: SkillAnalysis, template_draft: str, voice_context: str) -> str:
            raise TimeoutError("provider took too long")

    plan = build_bridge_plan(
        [
            skill(
                "Docker",
                "hidden_proof",
                "EVolocity telemetry app used a Docker container to run the Node.js backend and PostgreSQL database during demos.",
            )
        ],
        resume_draft_provider=Provider(),
        voice_context="EVolocity capstone telemetry platform.",
    )

    assert plan[0].resume_draft == "Containerised a full-stack telemetry app (Node.js backend + PostgreSQL) with Docker for reproducible team demos."
    assert plan[0].resume_draft_ai_refined is False


def test_llm_provider_timeout_falls_back_to_template_silently(monkeypatch):
    import app.services.bridge_plan as bridge_plan

    class Provider:
        def refine_resume_draft(self, skill: SkillAnalysis, template_draft: str, voice_context: str) -> str:
            time.sleep(0.05)
            return "This should arrive too late."

    monkeypatch.setattr(bridge_plan, "LLM_TIMEOUT_SECONDS", 0.01)

    plan = build_bridge_plan(
        [
            skill(
                "Docker",
                "hidden_proof",
                "EVolocity telemetry app used a Docker container to run the Node.js backend and PostgreSQL database during demos.",
            )
        ],
        resume_draft_provider=Provider(),
        voice_context="EVolocity capstone telemetry platform.",
    )

    assert plan[0].resume_draft == "Containerised a full-stack telemetry app (Node.js backend + PostgreSQL) with Docker for reproducible team demos."
    assert plan[0].resume_draft_ai_refined is False
