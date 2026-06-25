from fastapi import APIRouter, Body

from app.schemas.analysis import AnalyseRequest, AnalysisResponse, DemoAnalysisRequest
from app.services.analysis_service import analyse


router = APIRouter()


@router.post("/analyse", response_model=AnalysisResponse)
def analyse_resume(request: AnalyseRequest) -> AnalysisResponse:
    response = analyse(request)
    return AnalysisResponse.model_validate(response.model_dump())


@router.post("/demo-analysis", response_model=AnalysisResponse)
def demo_analysis(request: DemoAnalysisRequest | None = Body(default=None)) -> AnalysisResponse:
    demo_request = request or DemoAnalysisRequest()
    payload = AnalyseRequest(
        resume_text=demo_request.resume_text,
        target_pathway=demo_request.target_pathway,
        location="new_zealand",
        github_repo_url=demo_request.github_repo_url,
        use_demo_data=True,
    )
    response = analyse(payload.model_copy(update={"use_demo_data": True}))
    return AnalysisResponse.model_validate(response.model_dump())
