from fastapi import APIRouter, Depends

from app.config.settings import Settings, get_settings
from app.core.prompt_loader import PromptLoader
from app.schemas.analysis import AnalysisApiResponse, AnalysisRequest
from app.services.analysis_service import AnalysisService
from app.services.gemini_service import GeminiService
from app.services.knowledge_service import get_knowledge_service

router = APIRouter(tags=["intelligence"])


def get_analysis_service(settings: Settings = Depends(get_settings)) -> AnalysisService:
    # Reuse the process-wide cached knowledge singleton so we never re-read
    # the bundled JSON files on every request.
    return AnalysisService(
        generator=GeminiService(settings),
        prompt_loader=PromptLoader(),
        settings=settings,
        knowledge=get_knowledge_service(),
    )


@router.post("/analyze", response_model=AnalysisApiResponse)
async def analyze_match(
    payload: AnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
    settings: Settings = Depends(get_settings),
) -> AnalysisApiResponse:
    result = await service.analyze(payload)
    return AnalysisApiResponse(data=result, model=settings.gemini_model)
