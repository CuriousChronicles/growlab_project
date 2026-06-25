from app.services.llm_service import get_resume_draft_provider, parse_bullet_json, validate_refined_bullet


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
