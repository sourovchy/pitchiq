import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config.settings import get_settings
from app.core.errors import AppError
from app.services.knowledge_service import get_knowledge_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

settings = get_settings()

# Eagerly construct the knowledge layer so its file-by-file load logs surface
# during application startup rather than the first /api/analyze request.
knowledge_service = get_knowledge_service()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

app.include_router(api_router)


@app.exception_handler(AppError)
async def handle_app_error(request: Request, error: AppError) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.code, "message": error.message}},
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    del request, error
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "invalid_request",
                "message": "Check the submitted team names and try again.",
            }
        },
    )


@app.on_event("startup")
async def log_startup_summary() -> None:
    logger = logging.getLogger("app.startup")
    logger.info(
        "%s ready (env=%s, origins=%s, model=%s)",
        settings.app_name,
        settings.app_env,
        settings.allowed_origins,
        settings.gemini_model,
    )
    logger.info(
        "Knowledge layer ready — %s teams, %s groups, %s stadiums, %s squads, %s fixtures",
        knowledge_service.team_count,
        knowledge_service.group_count,
        knowledge_service.stadium_count,
        knowledge_service.squad_count,
        knowledge_service.fixture_count,
    )
