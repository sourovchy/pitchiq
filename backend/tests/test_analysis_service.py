"""Integration tests for AnalysisService ↔ KnowledgeService wiring.

These tests verify that the tactical analysis service:
- Resolves the two requested teams against the knowledge layer.
- Injects a relevant World Cup context into every Gemini prompt.
- Only includes information for the requested teams.
- Reuses the same context across retries.
- Degrades gracefully when knowledge is unavailable.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.config.settings import get_settings
from app.core.errors import AnalysisGenerationError
from app.core.prompt_loader import PromptLoader
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import AnalysisService
from app.services.context_builder import FootballContextBuilder
from app.services.knowledge_service import KnowledgeService


HOME_TEAM = "Argentina"
AWAY_TEAM = "France"
OTHER_TEAM = "Brazil"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _minimal_response(home: str = HOME_TEAM, away: str = AWAY_TEAM) -> str:
    """Return a valid schema-conforming JSON payload for the stub generator."""

    payload: dict[str, Any] = {
        "matchOverview": "Grounded tactical read with concise prose for dashboard cards.",
        "homeTeam": {
            "name": home,
            "formation": "4-3-3",
            "playingStyle": "Positional possession with high fullbacks.",
            "tacticalIdentity": "Half-space occupation through eights and inverted fullbacks.",
        },
        "awayTeam": {
            "name": away,
            "formation": "4-2-3-1",
            "playingStyle": "Vertical transitions from a compact mid-block.",
            "tacticalIdentity": "Counter-press built from a defensive double pivot.",
        },
        "predictedWinner": home,
        "confidence": 60,
        "formations": {
            "home": "4-3-3",
            "away": "4-2-3-1",
            "matchup": "Numerical equality centrally with attacking fullback edge.",
        },
        "strengths": {
            "home": ["Half-space rotations", "Progressive combinations"],
            "away": ["Counter-press recovery", "Rest defense compactness"],
        },
        "weaknesses": {
            "home": [
                "High line exposure to vertical balls",
                "Limited central cover when fullbacks invert",
            ],
            "away": [
                "Limited width without wide forwards",
                "Set-piece defending in the near post zone",
            ],
        },
        "keyBattles": [
            {
                "zone": "Left half-space",
                "homePlayerOrUnit": "Left eight",
                "awayPlayerOrUnit": "Right winger",
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
                "analysis": "Timing of striker runs decides transitions.",
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
    return AnalysisResponse.model_validate(payload).model_dump_json(by_alias=True)


class RecordingGenerator:
    """Stub Gemini generator that records every prompt it receives."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
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
        if not self._responses:
            raise AssertionError("RecordingGenerator ran out of responses")
        return self._responses.pop(0)


class TrackingKnowledgeService:
    """Stub :class:`KnowledgeService` whose every call is recorded.

    Each team resolves to a distinctive marker so tests can assert the prompt
    only references the two requested teams.
    """

    def __init__(self, *, resolved: dict[str, str | None] | None = None) -> None:
        self._resolved = resolved or {}
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def _marker(self, name: str) -> str | None:
        return self._resolved.get(name)

    def resolve_team(self, name: str) -> Any:
        self.calls.append(("resolve_team", (name,)))
        marker = self._marker(name)
        if marker is None:
            return None

        # Return a small object that mimics the TeamRecord interface used by
        # the real FootballContextBuilder.
        from app.services.knowledge_service import TeamRecord

        return TeamRecord(
            name=marker,
            normalised=None,
            display_name=name,
            continent=None,
            fifa_code=marker[:3].upper(),
            group=None,
            confed=None,
        )

    def get_squad(self, team_name: str) -> dict[str, Any] | None:
        self.calls.append(("get_squad", (team_name,)))
        return None

    def get_group(self, identifier: str) -> dict[str, Any] | None:
        self.calls.append(("get_group", (identifier,)))
        del identifier
        return None

    def get_fixture(
        self, home_team: str, away_team: str
    ) -> list[dict[str, Any]]:
        self.calls.append(("get_fixture", (home_team, away_team)))
        return []

    def get_stadium(self, ground: str | None) -> dict[str, Any] | None:
        self.calls.append(("get_stadium", (ground,)))
        del ground
        return None


def _build_service(
    generator: RecordingGenerator,
    knowledge: KnowledgeService | TrackingKnowledgeService,
) -> AnalysisService:
    return AnalysisService(
        generator=generator,  # type: ignore[arg-type]
        prompt_loader=PromptLoader(),
        settings=get_settings(),
        knowledge=knowledge,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


def test_knowledge_service_resolves_both_teams() -> None:
    knowledge = TrackingKnowledgeService(
        resolved={HOME_TEAM: "argentina-canonical", AWAY_TEAM: "france-canonical"}
    )
    generator = RecordingGenerator(responses=[_minimal_response()])
    service = _build_service(generator, knowledge)

    request = AnalysisRequest(home_team=HOME_TEAM, away_team=AWAY_TEAM)

    import asyncio

    response = asyncio.run(service.analyze(request))

    assert isinstance(response, AnalysisResponse)
    resolved_names = [call[1][0] for call in knowledge.calls if call[0] == "resolve_team"]
    assert HOME_TEAM in resolved_names
    assert AWAY_TEAM in resolved_names


def test_user_prompt_includes_grounded_context() -> None:
    knowledge = TrackingKnowledgeService(
        resolved={HOME_TEAM: "argentina-canonical", AWAY_TEAM: "france-canonical"}
    )
    generator = RecordingGenerator(responses=[_minimal_response()])
    service = _build_service(generator, knowledge)

    request = AnalysisRequest(home_team=HOME_TEAM, away_team=AWAY_TEAM)

    import asyncio

    asyncio.run(service.analyze(request))

    user_prompt = generator.calls[0]["user_prompt"]
    assert "argentina-canonical" in user_prompt
    assert "france-canonical" in user_prompt
    assert HOME_TEAM in user_prompt
    assert AWAY_TEAM in user_prompt
    # The placeholder must have been substituted away.
    assert "$football_context" not in user_prompt


def test_user_prompt_excludes_unrequested_teams() -> None:
    knowledge = TrackingKnowledgeService(
        resolved={
            HOME_TEAM: "argentina-canonical",
            AWAY_TEAM: "france-canonical",
            OTHER_TEAM: "brazil-canonical",
        }
    )
    generator = RecordingGenerator(responses=[_minimal_response()])
    service = _build_service(generator, knowledge)

    request = AnalysisRequest(home_team=HOME_TEAM, away_team=AWAY_TEAM)

    import asyncio

    asyncio.run(service.analyze(request))

    user_prompt = generator.calls[0]["user_prompt"]
    assert "brazil-canonical" not in user_prompt
    assert OTHER_TEAM not in user_prompt


def test_retry_path_reuses_same_context() -> None:
    knowledge = TrackingKnowledgeService(
        resolved={HOME_TEAM: "argentina-canonical", AWAY_TEAM: "france-canonical"}
    )
    generator = RecordingGenerator(
        responses=["not-json", _minimal_response()],
    )
    service = _build_service(generator, knowledge)

    request = AnalysisRequest(home_team=HOME_TEAM, away_team=AWAY_TEAM)

    import asyncio

    asyncio.run(service.analyze(request))

    assert len(generator.calls) == 2
    repair_prompt = generator.calls[1]["user_prompt"]
    assert "argentina-canonical" in repair_prompt
    assert "france-canonical" in repair_prompt
    assert "Validation problem" in repair_prompt
    assert "not-json" in repair_prompt


def test_graceful_degradation_when_no_knowledge_resolves() -> None:
    knowledge = TrackingKnowledgeService(resolved={})  # every team returns None
    generator = RecordingGenerator(responses=[_minimal_response()])
    service = _build_service(generator, knowledge)

    request = AnalysisRequest(home_team=HOME_TEAM, away_team=AWAY_TEAM)

    import asyncio

    response = asyncio.run(service.analyze(request))

    # Request still succeeds — knowledge gaps must never fail the analysis.
    assert response.home_team.name == HOME_TEAM
    assert response.away_team.name == AWAY_TEAM
    user_prompt = generator.calls[0]["user_prompt"]
    # Graceful degradation: the builder surfaces an explanatory "not found"
    # message rather than leaving the model without any grounding at all.
    assert "no matching World Cup 2026 team found" in user_prompt
    assert HOME_TEAM in user_prompt
    assert AWAY_TEAM in user_prompt
    # Both teams were still resolved against the knowledge layer so the model
    # can be told what was searched.
    assert ("resolve_team", (HOME_TEAM,)) in knowledge.calls
    assert ("resolve_team", (AWAY_TEAM,)) in knowledge.calls


def test_exhausted_retries_raise_analysis_error() -> None:
    knowledge = TrackingKnowledgeService(
        resolved={HOME_TEAM: "argentina-canonical", AWAY_TEAM: "france-canonical"}
    )
    generator = RecordingGenerator(responses=["not-json", "still-not-json"])
    service = _build_service(generator, knowledge)

    request = AnalysisRequest(home_team=HOME_TEAM, away_team=AWAY_TEAM)

    import asyncio

    with pytest.raises(AnalysisGenerationError):
        asyncio.run(service.analyze(request))

    # Context should still have been injected into every retry.
    assert len(generator.calls) == 2
    for call in generator.calls:
        assert "argentina-canonical" in call["user_prompt"]
        assert "france-canonical" in call["user_prompt"]


def test_system_prompt_is_loaded_from_template() -> None:
    knowledge = TrackingKnowledgeService(resolved={})
    generator = RecordingGenerator(responses=[_minimal_response()])
    service = _build_service(generator, knowledge)

    request = AnalysisRequest(home_team=HOME_TEAM, away_team=AWAY_TEAM)

    import asyncio

    asyncio.run(service.analyze(request))

    system_prompt = generator.calls[0]["system_prompt"]
    # Source-of-truth signals from the .md file content.
    assert "Tactical Analyst" in system_prompt or "tactical" in system_prompt.lower()
    assert "JSON" in system_prompt


@pytest.mark.parametrize(
    "home,away",
    [
        ("Argentina", "France"),
        ("Brazil", "Germany"),
        ("England", "Portugal"),
    ],
)
def test_real_knowledge_layer_satisfies_required_matchups(
    home: str, away: str
) -> None:
    """Smoke-test the real cached KnowledgeService through AnalysisService.

    Confirms the integration works end-to-end against the bundled JSON files
    without needing a live Gemini call.
    """

    generator = RecordingGenerator(responses=[_minimal_response(home=home, away=away)])
    service = AnalysisService(
        generator=generator,  # type: ignore[arg-type]
        prompt_loader=PromptLoader(),
        settings=get_settings(),
        knowledge=KnowledgeService(),
    )

    request = AnalysisRequest(home_team=home, away_team=away)

    import asyncio

    response = asyncio.run(service.analyze(request))

    assert response.home_team.name == home
    assert response.away_team.name == away
    user_prompt = generator.calls[0]["user_prompt"]
    # The grounded context must contain at least one of the resolved names.
    assert home in user_prompt or any(
        token in user_prompt
        for token in (home.split()[0], away.split()[0])
    )


def test_football_context_builder_does_not_call_unrelated_teams() -> None:
    """Defensive check: the builder should only touch the two requested teams.

    Uses a tracking service whose every call is recorded.
    """

    knowledge = TrackingKnowledgeService(
        resolved={HOME_TEAM: "ARGENTINA", AWAY_TEAM: "FRANCE"}
    )
    builder = FootballContextBuilder(knowledge)  # type: ignore[arg-type]

    builder.build(HOME_TEAM, AWAY_TEAM)

    # The only resolution request must be for the two requested teams.
    resolved_names = {call[1][0] for call in knowledge.calls if call[0] == "resolve_team"}
    assert resolved_names == {HOME_TEAM, AWAY_TEAM}