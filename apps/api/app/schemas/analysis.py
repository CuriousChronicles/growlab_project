from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


PathwayId = Literal["ai_automation", "software_fullstack", "embedded_firmware"]
LocationId = Literal["auckland", "new_zealand", "remote"]
SkillStatus = Literal["strong_proof", "hidden_proof", "adjacent_proof", "no_proof_yet"]
Confidence = Literal["high", "medium", "low"]


class AnalyseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resume_text: str = ""
    target_pathway: PathwayId = "ai_automation"
    location: LocationId = "auckland"
    github_repo_url: HttpUrl | None = None
    use_demo_data: bool = False


class DemoAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resume_text: str = ""
    target_pathway: PathwayId = "ai_automation"
    location: LocationId = "new_zealand"
    github_repo_url: HttpUrl | None = None
    use_demo_data: bool = True


class MarketSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    listing_count: int
    distinct_employers: int
    location: str
    captured_at: str
    sources: list[str]


class RolePathway(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: PathwayId
    label: str
    evidence_coverage: int = Field(ge=0, le=100)
    market_demand: Literal["high", "medium", "focused"]
    summary: str


class CandidateEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    excerpt: str


class SkillAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    market_label: str
    demand_score: int = Field(default=0, ge=0, le=100)
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
    model_config = ConfigDict(extra="forbid")

    priority: int
    action_type: Literal["surface", "strengthen", "build"]
    title: str
    time_estimate: str
    why: str
    steps: list[str]
    resume_draft: str | None = None
    resume_draft_ai_refined: bool = False
    resume_draft_refined_by: Literal["llm"] | None = None


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    market_snapshot: MarketSnapshot
    resume_text: str | None = None
    role_pathways: list[RolePathway]
    skills: list[SkillAnalysis]
    bridge_plan: list[BridgePlanItem]
