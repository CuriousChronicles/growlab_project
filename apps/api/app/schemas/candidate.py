from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


EvidenceSource = Literal["resume_summary", "project", "experience", "skills_section"]


class CandidateEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: EvidenceSource
    excerpt: str = Field(min_length=1)


class DemoCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    degree: str = Field(min_length=1)
    location: str = Field(min_length=1)
    resume_summary: str = Field(min_length=1)
    evidence: list[CandidateEvidence]
    portfolio_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
