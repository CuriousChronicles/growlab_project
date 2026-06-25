from fastapi import APIRouter

from app.schemas.analysis import AnalyseRequest, AnalysisResponse
from app.services.analysis_service import analyse


router = APIRouter()


@router.post("/analyse", response_model=AnalysisResponse)
def analyse_resume(request: AnalyseRequest) -> AnalysisResponse:
    return analyse(request)


@router.post("/demo-analysis", response_model=AnalysisResponse)
def demo_analysis(request: AnalyseRequest | None = None) -> AnalysisResponse:
    payload = request or AnalyseRequest(use_demo_data=True)
    return analyse(payload.model_copy(update={"use_demo_data": True}))
