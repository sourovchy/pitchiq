from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.routes import analysis as analysis_route
from app.config.settings import get_settings
from app.core.errors import AnalysisGenerationError, GeminiProviderError
from app.core.prompt_loader import PromptLoader
from app.schemas.analysis import AnalysisResponse
from app.services.analysis_service import AnalysisService
from app.services.context_builder import build_football_context
from app.services.knowledge_service import KnowledgeService

HOME_TEAM = "Argentina"
AWAY_TEAM = "France"


def _stub_response(
    home: str = HOME_TEAM, away: str = AWAY_TEAM
) -> AnalysisResponse:
    """Build a minimal but fully populated AnalysisResponse for stub services."""
    payload: dict[str, Any] = {
        "matchOverview": "Two possession-oriented systems meet in a control contest.",
        "homeTeam": {
            "name": home,
            "formation": "4-3-3",
            "playingStyle": "Possession-based with high fullbacks.",
            "tacticalIdentity": "Positional play focused on half-space occupation.",
        },
        "awayTeam": {
            "name": away,
            "formation": "4-2-3-1",
            "playingStyle": "Compact mid-block with vertical transitions.",
            "tacticalIdentity": "Counter-pressing structure built from a double pivot.",
        },
        "predictedWinner": home,
        "confidence": 62,
        "formations": {
            "home": "4-3-3",
            "away": "4-2-3-1",
            "matchup": "Numerical equality centrally with attacking fullback advantage.",
        },
        "strengths": {
            "home": ["Half-space rotations", "Progressive left half-space combinations"],
            "away": ["Counter-press recovery", "Rest defense compactness"],
        },
        "weaknesses": {
            "home": [
                "High line exposure to vertical balls",
                "Limited central cover when fullbacks invert.",
            ],
            "away": [
                "Limited width without wide forwards",
                "Set-piece defending in the near post zone.",
            ],
        },
        "keyBattles": [
            {
                "zone": "Left half-space",
                "homePlayerOrUnit": "Left half-space eight",
                "awayPlayerOrUnit": "Away right winger",
                "edge": "home",
                "analysis": "Numerical overload should create repeated entries.",
            },
            {
                "zone": "Central midfield",
                "homePlayerOrUnit": "Single pivot",
                "awayPlayerOrUnit": "Double pivot",
                "edge": "away",
                "analysis": "Numerical inferiority invites second-ball losses.",
            },
            {
                "zone": "Rest defense",
                "homePlayerOrUnit": "Right centre-back",
                "awayPlayerOrUnit": "Striker",
                "edge": "even",
                "analysis": "Timing of striker runs decides transition outcomes.",
            },
        ],
        "tacticalInsights": [
            {
                "title": "Rest defense timing",
                "detail": "Centre-backs must step in sync to cut vertical channels.",
                "importance": "critical",
            },
            {
                "title": "Half-space overloads",
                "detail": "Use opposite eight to pin the double pivot laterally.",
                "importance": "high",
            },
            {
                "title": "Counter-press triggers",
                "detail": "Press only after backward passes to avoid central exposure.",
                "importance": "medium",
            },
        ],
        "expectedGameFlow": {
            "openingPhase": "Cautious possession probes with wide circulation.",
            "middlePhase": "Increasing half-space rotations as legs tire.",
            "closingPhase": "Vertical transitions decide late scoring chances.",
        },
        "coachRecommendation": {
            "home": "Invite pressure, then attack the vacated half-space.",
            "away": "Stay compact centrally and attack wide after recovery.",
            "decisiveAdjustment": "Tempo control in the first ten minutes after half-time.",
        },
        "pressingScore": {"home": 64, "away": 58},
        "possessionScore": {"home": 60, "away": 52},
        "attackingThreat": {"home": 66, "away": 55},
        "defensiveStability": {"home": 58, "away": 61},
    }
    return AnalysisResponse.model_validate(payload)


class StubGenerator:
    """Stub Gemini JSON generator returning deterministic responses."""

    def __init__(
        self,
        responses: list[str] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._responses = list(responses or [])
        self._error = error
        self.calls: list[dict[str, Any]] = []

    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any],
    ) -> str:
        del response_schema
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        if self._error is not None:
            raise self._error
        if not self._responses:
            raise AssertionError("Stub generator ran out of responses")
        return self._responses.pop(0)


class StubKnowledgeService:
    """Stub :class:`KnowledgeService` returning deterministic empty context.

    The route tests are not exercising the knowledge layer, so we hand back an
    empty context to keep them fast and decoupled from the bundled JSON files.
    """

    def resolve_team(self, name: str) -> None:
        del name
        return None

    def get_team(self, name: str) -> None:
        del name
        return None

    def search_team(self, query: str) -> list[dict[str, Any]]:
        del query
        return []

    def get_group(self, identifier: str) -> None:
        del identifier
        return None

    def get_squad(self, team_name: str) -> None:
        del team_name
        return None

    def get_fixture(self, home_team: str, away_team: str) -> list[dict[str, Any]]:
        del home_team, away_team
        return []

    def get_stadium(self, ground: str | None) -> None:
        del ground
        return None


def _stub_knowledge_service() -> StubKnowledgeService:
    return StubKnowledgeService()


@pytest.fixture()
def override_service(monkeypatch: pytest.MonkeyPatch) -> Iterator:
    """Yield a helper that swaps the analysis service factory for a stub."""

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    get_settings.cache_clear()
    installed: list[StubGenerator] = []

    def install(generator: StubGenerator) -> AnalysisService:
        installed.append(generator)
        return AnalysisService(
            generator=generator,  # type: ignore[arg-type]
            prompt_loader=PromptLoader(),
            settings=get_settings(),
            knowledge=_stub_knowledge_service(),
        )

    yield install

    assert installed, "override_service was set up but never used"


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "tactiq-api"}


def test_analyze_success(override_service: Any, client: TestClient) -> None:
    generator = StubGenerator(
        responses=[_stub_response().model_dump_json(by_alias=True)]
    )
    client.app.dependency_overrides[analysis_route.get_analysis_service] = (
        lambda: override_service(generator)
    )

    response = client.post(
        "/api/analyze", json={"homeTeam": HOME_TEAM, "awayTeam": AWAY_TEAM}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["homeTeam"]["name"] == HOME_TEAM
    assert body["data"]["awayTeam"]["name"] == AWAY_TEAM
    assert body["data"]["predictedWinner"] == HOME_TEAM
    assert body["model"]


def test_analyze_validation_error_same_teams(client: TestClient) -> None:
    response = client.post(
        "/api/analyze", json={"homeTeam": HOME_TEAM, "awayTeam": HOME_TEAM}
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "invalid_request"


def test_analyze_validation_error_missing_fields(client: TestClient) -> None:
    response = client.post("/api/analyze", json={"homeTeam": HOME_TEAM})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_analyze_retries_when_first_response_invalid(
    override_service: Any, client: TestClient
) -> None:
    good = _stub_response().model_dump_json(by_alias=True)
    generator = StubGenerator(responses=["not-json", good])
    client.app.dependency_overrides[analysis_route.get_analysis_service] = (
        lambda: override_service(generator)
    )

    response = client.post(
        "/api/analyze", json={"homeTeam": HOME_TEAM, "awayTeam": AWAY_TEAM}
    )

    assert response.status_code == 200
    assert len(generator.calls) == 2


def test_analyze_fails_after_max_validation_attempts(
    override_service: Any, client: TestClient
) -> None:
    generator = StubGenerator(responses=["not-json", "still-not-json"])
    client.app.dependency_overrides[analysis_route.get_analysis_service] = (
        lambda: override_service(generator)
    )

    response = client.post(
        "/api/analyze", json={"homeTeam": HOME_TEAM, "awayTeam": AWAY_TEAM}
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "invalid_analysis_response"


def test_analyze_returns_503_when_gemini_key_missing(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()

    response = client.post(
        "/api/analyze", json={"homeTeam": HOME_TEAM, "awayTeam": AWAY_TEAM}
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "gemini_not_configured"


def test_analyze_returns_502_when_provider_fails(
    override_service: Any, client: TestClient
) -> None:
    generator = StubGenerator(error=GeminiProviderError())
    client.app.dependency_overrides[analysis_route.get_analysis_service] = (
        lambda: override_service(generator)
    )

    response = client.post(
        "/api/analyze", json={"homeTeam": HOME_TEAM, "awayTeam": AWAY_TEAM}
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "gemini_unavailable"


def test_cors_preflight_for_configured_origin(client: TestClient) -> None:
    response = client.options(
        "/api/analyze",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"

