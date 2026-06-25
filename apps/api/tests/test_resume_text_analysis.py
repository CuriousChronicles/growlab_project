from app.schemas.analysis import AnalyseRequest
from app.services.analysis_service import analyse, candidate_from_resume_text


def test_pasted_resume_candidate_uses_placeholder_for_long_skill_sentence():
    resume_text = " ".join(
        [
            "Docker",
            "was used on a project",
            "with many surrounding resume details" * 30,
        ]
    )

    candidate = candidate_from_resume_text(resume_text)

    assert candidate.evidence
    assert all(len(item.excerpt) <= 200 for item in candidate.evidence)
    assert any(item.excerpt == "Docker: Evidence detected in your resume - confirm and refine" for item in candidate.evidence)
    assert resume_text not in [item.excerpt for item in candidate.evidence]


def test_pasted_resume_analysis_never_returns_full_resume_evidence():
    resume_text = (
        "Docker was used on a project with extensive pasted resume content "
        + "describing responsibilities, context, tools, outcomes, and unrelated details " * 20
    )

    response = analyse(AnalyseRequest(resume_text=resume_text, target_pathway="ai_automation", location="new_zealand"))

    excerpts = [evidence.excerpt for skill in response.skills for evidence in skill.candidate_evidence]
    drafts = [item.resume_draft for item in response.bridge_plan if item.resume_draft]

    assert excerpts
    assert all(len(excerpt) <= 200 for excerpt in excerpts)
    assert all(resume_text not in excerpt for excerpt in excerpts)
    assert all(resume_text not in draft for draft in drafts)
