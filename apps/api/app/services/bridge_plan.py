from app.schemas.analysis import BridgePlanItem, SkillAnalysis


STATUS_PRIORITY = {
    "hidden_proof": 0,
    "adjacent_proof": 1,
    "no_proof_yet": 2,
    "strong_proof": 3,
}


def action_type_for(status: str) -> str:
    if status == "hidden_proof":
        return "surface"
    if status == "adjacent_proof":
        return "strengthen"
    return "build"


def make_resume_draft(skill: SkillAnalysis) -> str | None:
    if skill.status == "no_proof_yet" or not skill.candidate_evidence:
        return None
    first = skill.candidate_evidence[0].excerpt.rstrip(".")
    return f"Evidence-backed draft to review: {first}, highlighting {skill.name} only if this reflects your own contribution."


def build_bridge_plan(skills: list[SkillAnalysis]) -> list[BridgePlanItem]:
    candidates = [skill for skill in skills if skill.status != "strong_proof"]
    candidates.sort(key=lambda skill: (STATUS_PRIORITY[skill.status], -skill.employer_count, -skill.required_count))
    selected = candidates[:3]

    fallback = [skill for skill in skills if skill.status == "strong_proof"][: 3 - len(selected)]
    selected.extend(fallback)

    items: list[BridgePlanItem] = []
    for index, skill in enumerate(selected, start=1):
        action_type = action_type_for(skill.status)
        title_prefix = {"surface": "Surface", "strengthen": "Strengthen", "build": "Build proof for"}[action_type]
        evidence = "; ".join(item.excerpt for item in skill.candidate_evidence) or "No direct evidence found yet."
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
                skill_name=skill.name,
                title=f"{title_prefix} {skill.name}",
                time_estimate=time_estimate,
                market_signal=skill.market_evidence,
                candidate_evidence_found=evidence,
                confidence=skill.confidence,
                recommended_action=skill.recommended_action,
                why=f"{skill.name} is a {skill.market_label.lower()} in this selected snapshot, based on raw listing and employer counts.",
                steps=steps,
                resume_draft=make_resume_draft(skill),
            )
        )
    return items
