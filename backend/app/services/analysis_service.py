import logging
from collections import OrderedDict

from pydantic import ValidationError

from ..config.settings import Settings
from ..core.errors import AnalysisGenerationError
from ..core.prompt_loader import PromptLoader
from ..schemas.analysis import AnalysisRequest, AnalysisResponse
from .context_builder import build_football_context
from .gemini_service import JsonGenerationService
from .knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(
        self,
        *,
        generator: JsonGenerationService,
        prompt_loader: PromptLoader,
        settings: Settings,
        knowledge: KnowledgeService,
    ) -> None:
        self._generator = generator
        self._prompt_loader = prompt_loader
        self._settings = settings
        self._knowledge = knowledge
        self._cache_enabled = settings.analysis_cache_enabled
        self._cache_size = settings.analysis_cache_size
        self._cache: "OrderedDict[tuple[str, str], AnalysisResponse]" = OrderedDict()
        self._cache_hits = 0
        self._cache_misses = 0

    def _cache_key(self, request: AnalysisRequest) -> tuple[str, str]:
        return (
            request.home_team.strip().casefold(),
            request.away_team.strip().casefold(),
        )

    def cache_info(self) -> dict[str, int]:
        return {
            "enabled": int(self._cache_enabled),
            "size": self._cache_size,
            "entries": len(self._cache),
            "hits": self._cache_hits,
            "misses": self._cache_misses,
        }

    async def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        cache_key = self._cache_key(request)
        if self._cache_enabled:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._cache.move_to_end(cache_key)
                self._cache_hits += 1
                logger.debug(
                    "Tactical analysis cache hit for %s vs %s",
                    request.home_team,
                    request.away_team,
                )
                return cached
            self._cache_misses += 1

        logger.debug(
            "Tactical analysis requested for %s vs %s",
            request.home_team,
            request.away_team,
        )

        system_prompt = self._prompt_loader.load("tactical_analysis_system")
        football_context = build_football_context(
            self._knowledge,
            request.home_team,
            request.away_team,
        )
        logger.debug(
            "Knowledge retrieved for %s vs %s: %s characters",
            request.home_team,
            request.away_team,
            len(football_context),
        )

        context_block = football_context or "No grounded World Cup data available."
        user_prompt = self._prompt_loader.load(
            "tactical_analysis_user",
            home_team=request.home_team,
            away_team=request.away_team,
            football_context=context_block,
        )
        logger.debug(
            "Prompt assembled: system=%s chars, user=%s chars",
            len(system_prompt),
            len(user_prompt),
        )

        schema = AnalysisResponse.model_json_schema(by_alias=True)
        validation_error = ""
        invalid_response = ""
        raw_response = ""
        max_attempts = self._settings.gemini_max_validation_attempts

        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                logger.info(
                    "Retrying tactical analysis (attempt %s/%s)",
                    attempt,
                    max_attempts,
                )
                user_prompt = self._prompt_loader.load(
                    "tactical_analysis_repair",
                    home_team=request.home_team,
                    away_team=request.away_team,
                    football_context=context_block,
                    validation_error=validation_error,
                    invalid_response=invalid_response,
                )

            logger.debug(
                "Gemini request started (attempt %s/%s)",
                attempt,
                max_attempts,
            )
            try:
                raw_response = await self._generator.generate_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_schema=schema,
                )
            except Exception:
                # Propagate provider / configuration failures unchanged so the
                # global FastAPI handlers map them to the correct status codes.
                raise

            try:
                analysis = AnalysisResponse.model_validate_json(raw_response)
                self._validate_match_identity(analysis, request)
                logger.debug(
                    "Validation completed successfully on attempt %s",
                    attempt,
                )
                if attempt > 1:
                    logger.info(
                        "Tactical analysis recovered on attempt %s", attempt
                    )
                if self._cache_enabled:
                    self._cache[cache_key] = analysis
                    self._cache.move_to_end(cache_key)
                    while len(self._cache) > self._cache_size:
                        self._cache.popitem(last=False)
                return analysis
            except (ValidationError, ValueError) as error:
                validation_error = str(error)
                invalid_response = raw_response
                logger.warning(
                    "Tactical analysis attempt %s failed validation: %s",
                    attempt,
                    error,
                )

        logger.error(
            "Tactical analysis exhausted %s attempts for %s vs %s",
            max_attempts,
            request.home_team,
            request.away_team,
        )
        raise AnalysisGenerationError()

    @staticmethod
    def _validate_match_identity(
        analysis: AnalysisResponse,
        request: AnalysisRequest,
    ) -> None:
        if analysis.home_team.name.casefold() != request.home_team.casefold():
            raise ValueError("homeTeam.name must match the requested home team")
        if analysis.away_team.name.casefold() != request.away_team.casefold():
            raise ValueError("awayTeam.name must match the requested away team")

        valid_winners = {
            request.home_team.casefold(),
            request.away_team.casefold(),
            "draw",
        }
        if analysis.predicted_winner.casefold() not in valid_winners:
            raise ValueError(
                "predictedWinner must be one of the requested teams or Draw"
            )

