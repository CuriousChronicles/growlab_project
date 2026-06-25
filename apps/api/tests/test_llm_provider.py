from app.schemas.analysis import CandidateEvidence, SkillAnalysis
from app.services.llm_service import (
    GeminiFlashProvider,
    cache_key,
    get_resume_draft_provider,
    parse_bullet_json,
    read_cached_refinement,
    refined_by_llm,
    validate_refined_bullet,
    write_cached_refinement,
)


def test_missing_api_key_disables_resume_draft_provider(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")

    assert get_resume_draft_provider() is None


def test_env_toggle_disables_resume_draft_provider(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")
    monkeypatch.setenv("LLM_API_KEY", "fake-key")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")

    assert get_resume_draft_provider() is None


def test_refined_by_llm_returns_provider_model_name():
    provider = GeminiFlashProvider(api_key="fake-key", model="gemini-2.5-flash")

    assert refined_by_llm(provider) == "gemini-2.5-flash"


def test_refined_bullet_json_must_match_schema():
    assert parse_bullet_json('{"bullet": "Containerised project demos with Docker."}').bullet == "Containerised project demos with Docker."
    assert parse_bullet_json('{"bullet": "Valid", "extra": "discard me"}') is None
    assert parse_bullet_json('{"text": "Missing bullet"}') is None


def test_refined_bullet_validation_rejects_empty_or_same_text():
    template = "Containerised a project with Docker to support reproducible setup and demos."
    evidence = "Project setup used Docker for reproducible demos."

    assert validate_refined_bullet("", template) is None
    assert validate_refined_bullet(template, template, evidence) is None
    assert validate_refined_bullet(" Containerised the project setup with Docker. ", template, evidence) == "Containerised the project setup with Docker."


def test_refined_bullet_validation_rejects_new_tools_or_metrics():
    template = "Containerised a telemetry app with Docker for reproducible demos."
    evidence = "EVolocity telemetry app used Docker."

    assert validate_refined_bullet("Containerised the EVolocity telemetry app with Docker.", template, evidence)
    assert validate_refined_bullet("Containerised the EVolocity telemetry app with Kubernetes.", template, evidence) is None
    assert validate_refined_bullet("Improved the EVolocity telemetry app by 40%.", template, evidence) is None


def test_refined_bullet_validation_allows_pr_abbreviation_when_grounded():
    template = "Used Git version control to manage project changes and keep team development work traceable."
    evidence = "Used Git and GitHub pull requests to review firmware and capstone changes."

    assert validate_refined_bullet("Reviewed firmware changes with GitHub PRs.", template, evidence)
    assert validate_refined_bullet("Reviewed firmware changes with Jira PRs.", template, evidence) is None


def test_llm_cache_round_trips_by_skill_and_evidence(monkeypatch, tmp_path):
    import app.services.llm_service as llm_service

    monkeypatch.setattr(llm_service, "LLM_CACHE_PATH", tmp_path / "llm_cache.json")
    template = "Containerised a telemetry app with Docker for reproducible demos."
    evidence = "EVolocity telemetry app used Docker."
    bullet = "Containerised the EVolocity telemetry app with Docker."

    write_cached_refinement("Docker", evidence, bullet)

    assert read_cached_refinement("Docker", evidence, template) == bullet
    assert read_cached_refinement("Docker", "Different evidence", template) is None


def test_cache_key_is_stable_for_identical_skill_and_evidence():
    assert cache_key("Docker", "EVolocity telemetry app used Docker.") == cache_key(
        "Docker",
        "EVolocity   telemetry app used Docker.",
    )


def test_cached_refinement_skips_http_call(monkeypatch, tmp_path):
    import app.services.llm_service as llm_service

    monkeypatch.setattr(llm_service, "LLM_CACHE_PATH", tmp_path / "llm_cache.json")
    evidence = "EVolocity telemetry app used Docker."
    template = "Containerised a telemetry app with Docker for reproducible demos."
    bullet = "Containerised the EVolocity telemetry app with Docker."
    write_cached_refinement("Docker", evidence, bullet)

    def fail_post(*args, **kwargs):
        raise AssertionError("Gemini should not be called on a cache hit")

    monkeypatch.setattr(llm_service.httpx, "post", fail_post)
    provider = GeminiFlashProvider(api_key="fake-key")
    skill = SkillAnalysis(
        name="Docker",
        market_label="Growing signal",
        demand_score=50,
        listing_count=4,
        total_listings=8,
        employer_count=4,
        required_count=2,
        status="hidden_proof",
        confidence="medium",
        market_evidence="Present in selected listings.",
        candidate_evidence=[CandidateEvidence(source="project", excerpt=evidence)],
        recommended_action="Add an evidence-backed resume bullet.",
    )

    assert provider.refine_resume_draft(skill, template, "") == bullet


def test_provider_retries_after_transient_failure(monkeypatch, tmp_path):
    import app.services.llm_service as llm_service

    monkeypatch.setattr(llm_service, "LLM_CACHE_PATH", tmp_path / "llm_cache.json")
    calls = []

    def fake_post_gemini_json(url: str, api_key: str, payload: dict):
        calls.append(payload)
        if len(calls) == 1:
            return None
        return {"candidates": [{"content": {"parts": [{"text": '{"bullet": "Containerised the EVolocity telemetry app with Docker."}'}]}}]}

    monkeypatch.setattr(llm_service, "post_gemini_json", fake_post_gemini_json)
    provider = GeminiFlashProvider(api_key="fake-key")
    skill = SkillAnalysis(
        name="Docker",
        market_label="Growing signal",
        demand_score=50,
        listing_count=4,
        total_listings=8,
        employer_count=4,
        required_count=2,
        status="hidden_proof",
        confidence="medium",
        market_evidence="Present in selected listings.",
        candidate_evidence=[CandidateEvidence(source="project", excerpt="EVolocity telemetry app used Docker.")],
        recommended_action="Add an evidence-backed resume bullet.",
    )

    assert provider.refine_resume_draft(skill, "Containerised a telemetry app with Docker for demos.", "") == (
        "Containerised the EVolocity telemetry app with Docker."
    )
    assert len(calls) == 2
    assert calls[0]["generationConfig"]["responseSchema"]["required"] == ["bullet"]
