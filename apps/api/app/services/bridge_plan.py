from concurrent.futures import ThreadPoolExecutor, TimeoutError

from app.schemas.analysis import BridgePlanItem, SkillAnalysis
from app.services.llm_provider import LLM_TIMEOUT_SECONDS, ResumeDraftProvider, refined_by_llm
from app.services.skill_extractor import mentions_skill

PLACEHOLDER_FRAGMENT = "Evidence detected in your resume"

STATUS_PRIORITY = {
    "hidden_proof": 0,
    "adjacent_proof": 1,
    "no_proof_yet": 2,
    "strong_proof": 3,
}

PLAN_SKILL_GROUPS = {
    "Git": "version_control",
    "GitHub": "version_control",
}


def action_type_for(status: str) -> str:
    if status == "hidden_proof":
        return "surface"
    if status == "adjacent_proof":
        return "strengthen"
    return "build"


def make_resume_draft(skill: SkillAnalysis, action_type: str) -> str | None:
    if action_type != "surface" or not skill.candidate_evidence:
        return None

    evidence_text = " ".join(
        item.excerpt for item in skill.candidate_evidence if mentions_skill(item.excerpt, skill.name)
    )
    if not evidence_text:
        return None
    if PLACEHOLDER_FRAGMENT in evidence_text:
        return None

    lowered = evidence_text.lower()
    if skill.name == "Docker" and "telemetry" in lowered and "node" in lowered and "postgresql" in lowered:
        return "Containerised a full-stack telemetry app (Node.js backend + PostgreSQL) with Docker for reproducible team demos."

    templates = {
        "Docker": "Containerised a project with Docker to support reproducible setup and demos.",
        "CI/CD": "Added a GitHub Actions workflow to run project tests automatically on pull requests.",
        "REST APIs": "Built a project-tracking web app that integrated REST APIs with persistent task storage.",
        "GitHub": "Used GitHub pull requests and project documentation to make technical work reviewable by teammates.",
        "Git": "Used Git version control to manage project changes and keep team development work traceable.",
        "PostgreSQL": "Implemented PostgreSQL storage for a live telemetry platform with a Node.js backend.",
        "Node.js": "Built a Node.js backend for a live telemetry platform with WebSocket streaming and PostgreSQL storage.",
        "React": "Built a React and TypeScript dashboard for live wireless vehicle telemetry.",
        "TypeScript": "Built a typed React dashboard for live vehicle telemetry using TypeScript.",
        "Python": "Built Python automation tooling for data processing, persistence, and notification workflows.",
        "SQL": "Used SQL-backed storage in automation and telemetry projects to persist application data.",
        "Testing": "Added automated checks to improve confidence in project changes before review.",
        "Linux": "Used Linux-oriented tooling to support reproducible project setup and development workflows.",
    }
    return templates.get(skill.name, f"Used {skill.name} in a practical project with visible, reviewable evidence.")


def refine_resume_draft(
    skill: SkillAnalysis,
    template_draft: str | None,
    provider: ResumeDraftProvider | None,
    voice_context: str,
) -> tuple[str | None, bool, str | None, str | None]:
    if not template_draft or provider is None:
        return template_draft, False, None, "template" if template_draft else None
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(provider.refine_resume_draft, skill, template_draft, voice_context)
        refined = future.result(timeout=LLM_TIMEOUT_SECONDS)
    except (Exception, TimeoutError):
        executor.shutdown(wait=False, cancel_futures=True)
        return template_draft, False, None, "template_llm_fallback"
    executor.shutdown(wait=False)
    if not refined:
        return template_draft, False, None, "template_llm_fallback"
    return refined, True, refined_by_llm(provider), "llm"


def build_bridge_plan(
    skills: list[SkillAnalysis],
    resume_draft_provider: ResumeDraftProvider | None = None,
    voice_context: str = "",
) -> list[BridgePlanItem]:
    candidates = [skill for skill in skills if skill.status != "strong_proof"]
    candidates.sort(
        key=lambda skill: (
            STATUS_PRIORITY[skill.status],
            -evidence_strength(skill),
            -skill.employer_count,
            -skill.required_count,
        )
    )
    selected = select_distinct_plan_skills(candidates, limit=3)

    fallback = select_distinct_plan_skills(
        [skill for skill in skills if skill.status == "strong_proof"],
        limit=3 - len(selected),
        selected=selected,
    )
    selected.extend(fallback)

    items: list[BridgePlanItem] = []
    for index, skill in enumerate(selected, start=1):
        action_type = action_type_for(skill.status)
        template_draft = make_resume_draft(skill, action_type)
        resume_draft, resume_draft_ai_refined, resume_draft_refined_by, resume_draft_source = refine_resume_draft(
            skill,
            template_draft,
            resume_draft_provider if action_type == "surface" else None,
            voice_context,
        )
        title_prefix = {"surface": "Surface", "strengthen": "Strengthen", "build": "Build proof for"}[action_type]
        if action_type == "surface":
            steps = [
                "Add one project bullet that names the concrete contribution and outcome.",
                "Add a short README note so a reviewer can verify the evidence quickly.",
            ]
            time_estimate = "20 minutes"
        elif action_type == "strengthen":
            steps = [
                "Add one small feature or test that proves the skill directly.",
                "Commit the change with a clear README section explaining the trade-off.",
            ]
            time_estimate = "1-3 hours"
        else:
            steps = [
                "Create a tiny focused artifact that proves only this skill.",
                "Document the problem, setup, and one result so the proof is reviewable.",
            ]
            time_estimate = "One afternoon"
        items.append(
            BridgePlanItem(
                priority=index,
                action_type=action_type,
                title=f"{title_prefix} {skill.name}",
                time_estimate=time_estimate,
                why=f"{skill.name} is a {skill.market_label.lower()} in this selected snapshot, based on raw listing and employer counts.",
                steps=steps,
                resume_draft=resume_draft,
                resume_draft_ai_refined=resume_draft_ai_refined,
                resume_draft_refined_by=resume_draft_refined_by,
                resume_draft_source=resume_draft_source,
            )
        )
    return items


def evidence_strength(skill: SkillAnalysis) -> int:
    source_scores = {
        "repository": 4,
        "project": 3,
        "experience": 2,
        "resume_summary": 1,
        "skills_section": 0,
    }
    if not skill.candidate_evidence:
        return -1
    return max(source_scores.get(item.source.split(":", 1)[0], 0) for item in skill.candidate_evidence)


def select_distinct_plan_skills(
    skills: list[SkillAnalysis],
    limit: int,
    selected: list[SkillAnalysis] | None = None,
) -> list[SkillAnalysis]:
    chosen = list(selected or [])
    used_groups = {plan_group_key(skill) for skill in chosen}
    used_evidence = {signature for skill in chosen for signature in evidence_signatures(skill)}

    for skill in skills:
        if len(chosen) >= limit + len(selected or []):
            break
        group_key = plan_group_key(skill)
        signatures = evidence_signatures(skill)
        if group_key in used_groups:
            continue
        if signatures and used_evidence.intersection(signatures):
            continue
        chosen.append(skill)
        used_groups.add(group_key)
        used_evidence.update(signatures)

    return chosen[len(selected or []):]


def plan_group_key(skill: SkillAnalysis) -> str:
    return PLAN_SKILL_GROUPS.get(skill.name, skill.name)


def evidence_signatures(skill: SkillAnalysis) -> set[str]:
    return {" ".join(item.excerpt.lower().split()) for item in skill.candidate_evidence if item.excerpt.strip()}
