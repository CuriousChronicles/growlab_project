from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.analysis import PathwayId


class JobListing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    company: str
    source: Literal["Adzuna NZ", "fixture"] = "Adzuna NZ"
    location: str
    description: str
    created: str
    redirect_url: HttpUrl
    pathway: PathwayId


class JobSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    captured_at: str = Field(min_length=1)
    source: Literal["Adzuna NZ"]
    location: str = Field(min_length=1)
    listings: list[JobListing]
