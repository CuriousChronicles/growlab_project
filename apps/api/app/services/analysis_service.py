from app.schemas.analysis import AnalyseRequest, AnalysisResponse, RolePathway, SkillAnalysis
from app.services.bridge_plan import build_bridge_plan
from app.services.evidence_matcher import classify_skill, demo_resume_text
from app.services.job_service import PATHWAY_LABELS, market_summary


def coverage_for(skills: list[SkillAnalysis]) -> int:
    if not skills:
        return 0
    weights = {"strong_proof": 1.0, "hidden_proof": 0.75, "adjacent_proof": 0.45, "no_proof_yet": 0.0}
    top = skills[:8]
    return round(sum(weights[skill.status] for skill in top) / len(top) * 100)


def analyse(request: AnalyseRequest) -> AnalysisResponse:
    resume_text = demo_resume_text() if request.use_demo_data and not request.resume_text else request.resume_text
    summary = market_summary(request.target_pathway, request.location)
    top_market_skills = summary["skills"][:12]

    skills = []
    for market_skill in top_market_skills:
        evidence = classify_skill(
            market_skill["name"],
            resume_text,
            str(request.github_repo_url) if request.github_repo_url else None,
            request.use_demo_data,
        )
        skills.append(SkillAnalysis(**market_skill, **evidence))

    selected_coverage = coverage_for(skills)
    role_pathways = []
    for pathway_id, label in PATHWAY_LABELS.items():
        pathway_summary = market_summary(pathway_id, request.location)
        pathway_skills = []
        for market_skill in pathway_summary["skills"][:8]:
            evidence = classify_skill(market_skill["name"], resume_text, None, request.use_demo_data)
            pathway_skills.append(SkillAnalysis(**market_skill, **evidence))
        coverage = coverage_for(pathway_skills)
        role_pathways.append(
            RolePathway(
                id=pathway_id,
                label=label,
                evidence_coverage=coverage,
                market_demand="high" if pathway_summary["listing_count"] >= 8 else "medium",
                summary=f"{coverage}% evidence coverage across the top skills in {pathway_summary['listing_count']} cached roles.",
            )
        )
    role_pathways.sort(key=lambda pathway: pathway.evidence_coverage, reverse=True)

    best = role_pathways[0]
    headline = (
        f"You are closest to {best.label} roles."
        if best.id == request.target_pathway
        else f"Your evidence is strongest for {best.label}, with useful overlap for {PATHWAY_LABELS[request.target_pathway]}."
    )

    return AnalysisResponse(
        market_snapshot=summary,
        headline=headline,
        role_pathways=role_pathways,
        skills=skills,
        bridge_plan=build_bridge_plan(skills),
        methodology=[
            "Market demand is shown as raw counts from the selected cached snapshot.",
            "Evidence coverage is not an employability score; it only reflects visible proof against recurring skills.",
            "Skills are classified with deterministic rules before any language-model style wording would be used.",
        ],
    )
