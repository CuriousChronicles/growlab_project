import json

from app.schemas.analysis import (
    AnalyseRequest,
    AnalysisResponse,
    CandidateEvidence,
    LocationId,
    MarketSnapshot,
    PathwayId,
    RolePathway,
    SkillAnalysis,
)
from app.schemas.candidate import CandidateEvidence as CandidateEvidenceInput
from app.schemas.candidate import DemoCandidate
from app.schemas.job_snapshot import JobListing
from app.services.bridge_plan import build_bridge_plan
from app.services.demand_counter import SkillDemand, count_skill_demand
from app.services.evidence_classifier import SkillEvidenceStatus, classify_in_demand_skills
from app.services.paths import DATA_DIR
from app.services.llm_provider import get_resume_draft_provider
from app.services.skill_extractor import (
    EvidenceHit,
    extract_candidate_skill_evidence,
    extract_skills,
    find_resume_evidence,
    truncate_excerpt,
)


PATHWAY_LABELS: dict[PathwayId, str] = {
    "ai_automation": "AI & Automation",
    "software_fullstack": "Graduate Software / Full-Stack",
    "embedded_firmware": "Embedded / Firmware",
}

LOCATION_LABELS: dict[LocationId, str] = {
    "auckland": "Auckland",
    "new_zealand": "New Zealand",
    "remote": "Remote-friendly",
}

STATUS_WEIGHTS = {
    "strong_proof": 1.0,
    "hidden_proof": 0.75,
    "adjacent_proof": 0.45,
    "no_proof": 0.0,
    "no_proof_yet": 0.0,
}


def load_snapshot_payload() -> dict:
    return json.loads((DATA_DIR / "jobs_snapshot.json").read_text(encoding="utf-8"))


def load_jobs() -> list[dict]:
    payload = load_snapshot_payload()
    raw_listings = payload["listings"] if isinstance(payload, dict) else payload
    return [JobListing.model_validate(listing).model_dump(mode="json") for listing in raw_listings]


def load_demo_candidate() -> DemoCandidate:
    payload = json.loads((DATA_DIR / "demo_candidate.json").read_text(encoding="utf-8"))
    return DemoCandidate.model_validate(payload)


def candidate_from_resume_text(resume_text: str) -> DemoCandidate:
    text = resume_text.strip() or "No resume text supplied."
    detected_skills = sorted(extract_skills(text))
    evidence: list[CandidateEvidenceInput] = []
    for skill in detected_skills:
        hits = find_resume_evidence(text, skill)
        excerpt = hits[0].excerpt if hits else f"{skill}: Evidence detected in your resume - confirm and refine"
        evidence.append(CandidateEvidenceInput(source="resume_summary", excerpt=excerpt))

    return DemoCandidate(
        name="Uploaded candidate",
        headline="Candidate supplied resume text",
        degree="Unknown",
        location="Unknown",
        resume_summary=truncate_excerpt(text),
        evidence=evidence,
    )


def location_matches(listing: dict, location: LocationId) -> bool:
    listing_location = str(listing.get("location", "")).lower()
    if location == "new_zealand":
        return True
    if location == "remote":
        return "remote" in listing_location or listing_location == "new zealand"
    return "auckland" in listing_location or "north shore" in listing_location or "takapuna" in listing_location


def filtered_relevant_listings(pathway: PathwayId, location: LocationId) -> list[dict]:
    pathway_listings = [
        listing
        for listing in load_jobs()
        if listing.get("pathway") == pathway and location_matches(listing, location)
    ]
    return pathway_listings


def demand_label(employer_count: int, distinct_employers: int) -> str:
    if distinct_employers == 0:
        return "Low signal"
    ratio = employer_count / distinct_employers
    if ratio >= 0.55:
        return "Core demand"
    if ratio >= 0.30:
        return "Growing signal"
    if ratio >= 0.12:
        return "Differentiator"
    return "Low signal"


def confidence_for(status: SkillEvidenceStatus) -> str:
    if status.status == "no_proof":
        return "low"
    return status.confidence


def recommended_action_for(status: SkillEvidenceStatus) -> str:
    if status.status == "strong_proof":
        return "Surface this skill prominently in a role-targeted project or experience bullet."
    if status.status == "hidden_proof":
        return "Add an evidence-backed resume or README bullet so this proof is visible."
    if status.status == "adjacent_proof":
        return "Extend an existing project so the adjacent evidence proves this skill directly."
    return "Build one small, reviewable proof artifact before adding this skill to the resume."


def evidence_to_response(hits: list[EvidenceHit]) -> list[CandidateEvidence]:
    return [CandidateEvidence(source=hit.source, excerpt=truncate_excerpt(hit.excerpt)) for hit in hits[:3]]


def skill_response(
    demand: SkillDemand,
    status: SkillEvidenceStatus,
    distinct_employers: int,
) -> SkillAnalysis:
    market_label = demand_label(demand.employer_count, distinct_employers)
    status_name = "no_proof_yet" if status.status == "no_proof" else status.status
    demand_score = round(demand.listing_count / demand.total_listings * 100) if demand.total_listings else 0
    return SkillAnalysis(
        name=demand.skill,
        market_label=market_label,
        demand_score=demand_score,
        listing_count=demand.listing_count,
        total_listings=demand.total_listings,
        employer_count=demand.employer_count,
        required_count=demand.required_count,
        status=status_name,
        confidence=confidence_for(status),
        market_evidence=(
            f"Present in {demand.listing_count} of {demand.total_listings} relevant listings "
            f"from {demand.employer_count} distinct employers; required in {demand.required_count}."
        ),
        candidate_evidence=evidence_to_response(status.evidence),
        recommended_action=recommended_action_for(status),
    )


def coverage_for(skills: list[SkillAnalysis]) -> int:
    if not skills:
        return 0
    top = skills[:8]
    return round(sum(STATUS_WEIGHTS[skill.status] for skill in top) / len(top) * 100)


def market_demand_for(listing_count: int) -> str:
    if listing_count >= 25:
        return "high"
    if listing_count >= 10:
        return "medium"
    return "focused"


def build_skills_for(pathway: PathwayId, location: LocationId, candidate: DemoCandidate) -> tuple[list[SkillAnalysis], list[dict]]:
    listings = filtered_relevant_listings(pathway, location)
    demand = count_skill_demand(listings)
    candidate_evidence = extract_candidate_skill_evidence(candidate)
    statuses = classify_in_demand_skills(demand, candidate_evidence)
    employers = {listing["company"] for listing in listings}
    status_by_skill = {status.skill: status for status in statuses}
    skills = [
        skill_response(item, status_by_skill[item.skill], len(employers))
        for item in demand[:30]
    ]
    return skills, listings


def build_role_pathways(candidate: DemoCandidate, location: LocationId) -> list[RolePathway]:
    role_pathways: list[RolePathway] = []
    for pathway_id, label in PATHWAY_LABELS.items():
        skills, listings = build_skills_for(pathway_id, location, candidate)
        coverage = coverage_for(skills)
        role_pathways.append(
            RolePathway(
                id=pathway_id,
                label=label,
                evidence_coverage=coverage,
                market_demand=market_demand_for(len(listings)),
                summary=f"{coverage}% evidence coverage across the top recurring skills in {len(listings)} relevant listings.",
            )
        )
    role_pathways.sort(key=lambda item: item.evidence_coverage, reverse=True)
    return role_pathways


def resume_voice_context(candidate: DemoCandidate) -> str:
    evidence_lines = [f"- {item.source}: {item.excerpt}" for item in candidate.evidence[:5]]
    return "\n".join([candidate.resume_summary, *evidence_lines]).strip()


def analyse(request: AnalyseRequest) -> AnalysisResponse:
    payload = load_snapshot_payload()
    candidate = load_demo_candidate() if request.use_demo_data else candidate_from_resume_text(request.resume_text)
    skills, listings = build_skills_for(request.target_pathway, request.location, candidate)
    employers = {listing["company"] for listing in listings}
    sources = sorted({str(listing.get("source", "Adzuna NZ")) for listing in listings})

    response = AnalysisResponse(
        market_snapshot=MarketSnapshot(
            listing_count=len(listings),
            distinct_employers=len(employers),
            location=LOCATION_LABELS[request.location],
            captured_at=str(payload.get("captured_at", "")),
            sources=sources,
        ),
        resume_text=candidate.resume_text if request.use_demo_data else None,
        role_pathways=build_role_pathways(candidate, request.location),
        skills=skills,
        bridge_plan=build_bridge_plan(
            skills,
            resume_draft_provider=get_resume_draft_provider(),
            voice_context=resume_voice_context(candidate),
        ),
    )
    return AnalysisResponse.model_validate(response.model_dump())
