from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


PathwayId = Literal["ai_automation", "software_fullstack", "embedded_firmware"]
LocationId = Literal["auckland", "new_zealand", "remote"]
SkillStatus = Literal["strong_proof", "hidden_proof", "adjacent_proof", "no_proof_yet"]
Confidence = Literal["high", "medium", "low"]


class AnalyseRequest(BaseModel):
    resume_text: str = ""
    target_pathway: PathwayId = "ai_automation"
    location: LocationId = "auckland"
    github_repo_url: HttpUrl | None = None
    use_demo_data: bool = False


class MarketSnapshot(BaseModel):
    listing_count: int
    distinct_employers: int
    location: str
    role_pathway: str
    captured_at: str
    sources: list[str]


class RolePathway(BaseModel):
    id: PathwayId
    label: str
    evidence_coverage: int = Field(ge=0, le=100)
    market_demand: Literal["high", "medium", "focused"]
    summary: str


class CandidateEvidence(BaseModel):
    source: str
    excerpt: str


class SkillAnalysis(BaseModel):
    name: str
    market_label: str
    listing_count: int
    total_listings: int
    employer_count: int
    required_count: int
    status: SkillStatus
    confidence: Confidence
    market_evidence: str
    candidate_evidence: list[CandidateEvidence]
    recommended_action: str


class BridgePlanItem(BaseModel):
    priority: int
    action_type: Literal["surface", "strengthen", "build"]
    skill_name: str
    title: str
    time_estimate: str
    market_signal: str
    candidate_evidence_found: str
    confidence: Confidence
    recommended_action: str
    why: str
    steps: list[str]
    resume_draft: str | None = None


class AnalysisResponse(BaseModel):
    market_snapshot: MarketSnapshot
    headline: str
    role_pathways: list[RolePathway]
    skills: list[SkillAnalysis]
    bridge_plan: list[BridgePlanItem]
    methodology: list[str]
