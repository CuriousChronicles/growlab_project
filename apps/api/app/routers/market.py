from fastapi import APIRouter

from app.schemas.analysis import LocationId, PathwayId
from app.services.job_service import market_summary


router = APIRouter()


@router.get("/market-summary")
def get_market_summary(target_pathway: PathwayId = "ai_automation", location: LocationId = "auckland") -> dict:
    return market_summary(target_pathway, location)
