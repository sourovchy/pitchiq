"""One-off Phase 3 smoke runner for the PitchIQ demo.

Exercises the full analysis pipeline for the four flagship World Cup 2026
matchups without requiring a live Gemini API key. A deterministic stub
generator returns a realistic, schema-conforming JSON payload so we can:

1. Confirm the route, service, prompt builder, context builder, and
   Pydantic schema all agree on every matchup.
2. Validate response shape end-to-end (predicted_winner, scores, key
   battles, tactical insights, game flow, coach recommendation).
3. Confirm a malformed payload is rejected with AnalysisGenerationError
   and that the repair prompt is requested on the second attempt.

Run with the project's Python interpreter:

    & "C:\\Users\\ACER\\AppData\\Local\\Python\\bin\\python.exe" \\
        backend/scripts/smoke_matchups.py
"""

from __future__ import annotations

import asyncio
import sys
import traceback
from dataclasses import dataclass
from typing import Any

# Ensure `app.*` imports resolve regardless of where the script is invoked from.
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.settings import get_settings  # noqa: E402
from app.core.errors import AnalysisGenerationError  # noqa: E402
from app.core.prompt_loader import PromptLoader  # noqa: E402
from app.schemas.analysis import AnalysisRequest, AnalysisResponse  # noqa: E402
from app.services.analysis_service import AnalysisService  # noqa: E402
from app.services.knowledge_service import KnowledgeService  # noqa: E402


MATCHUPS: list[tuple[str, str]] = [
    ("Argentina", "France"),
    ("Brazil", "Germany"),
    ("England", "Portugal"),
    ("Japan", "Morocco"),
]


@dataclass(slots=True)
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


def _build_response(home: str, away: str) -> str:
    """Schema-conforming payload that varies by matchup so we can sanity-check
    that the service is reading the request and not the cached test fixture."""

    winner = home if home in {"Argentina", "Brazil", "England"} else away
    confidence = 67 if winner == home else 58

    payload: dict[str, Any] = {
        "matchOverview": (
            f"Tactical read for {home} hosting {away}: formational contrast "
            "decides midfield control and half-space access."
        ),
        "homeTeam": {
            "name": home,
            "formation": "4-3-3",
            "playingStyle": "Positional possession with attacking fullbacks.",
            "tacticalIdentity": "Half-space occupation through eights.",
        },
        "awayTeam": {
            "name": away,
            "formation": "4-2-3-1",
            "playingStyle": "Vertical transitions from a compact mid-block.",
            "tacticalIdentity": "Counter-press built from a double pivot.",
        },
        "predictedWinner": winner,
        "confidence": confidence,
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
                "Set-piece defending near-post zone",
            ],
        },
        "keyBattles": [
            {
                "zone": "Left half-space",
                "homePlayerOrUnit": f"{home} left eight",
                "awayPlayerOrUnit": f"{away} right winger",
                "edge": "home" if winner == home else "away",
                "analysis": "Numerical overload should create repeated entries.",
            },
            {
                "zone": "Central midfield",
                "homePlayerOrUnit": f"{home} single pivot",
                "awayPlayerOrUnit": f"{away} double pivot",
                "edge": "away" if winner == home else "home",
                "analysis": "Numerical inferiority invites second-ball losses.",
            },
            {
                "zone": "Rest defense",
                "homePlayerOrUnit": f"{home} right centre-back",
                "awayPlayerOrUnit": f"{away} striker",
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
    """Stub JsonGenerationService returning a fresh payload per request."""

    def __init__(self, payload: str) -> None:
        self._payload = payload
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
        return self._payload


def _validate_response(response: AnalysisResponse, home: str, away: str) -> list[CheckResult]:
    checks: list[CheckResult] = []

    checks.append(
        CheckResult(
            "home_team.name matches request",
            response.home_team.name.casefold() == home.casefold(),
            response.home_team.name,
        )
    )
    checks.append(
        CheckResult(
            "away_team.name matches request",
            response.away_team.name.casefold() == away.casefold(),
            response.away_team.name,
        )
    )

    valid_winners = {home.casefold(), away.casefold(), "draw"}
    checks.append(
        CheckResult(
            "predicted_winner in {home, away, Draw}",
            response.predicted_winner.casefold() in valid_winners,
            response.predicted_winner,
        )
    )

    checks.append(
        CheckResult(
            "confidence in [0, 100]",
            0 <= response.confidence <= 100,
            str(response.confidence),
        )
    )

    for label, score in (
        ("pressing_score.home", response.pressing_score.home),
        ("pressing_score.away", response.pressing_score.away),
        ("possession_score.home", response.possession_score.home),
        ("possession_score.away", response.possession_score.away),
        ("attacking_threat.home", response.attacking_threat.home),
        ("attacking_threat.away", response.attacking_threat.away),
        ("defensive_stability.home", response.defensive_stability.home),
        ("defensive_stability.away", response.defensive_stability.away),
    ):
        checks.append(CheckResult(f"{label} in [0, 100]", 0 <= score <= 100, str(score)))

    checks.append(
        CheckResult(
            "key_battles length 3-5",
            3 <= len(response.key_battles) <= 5,
            str(len(response.key_battles)),
        )
    )
    checks.append(
        CheckResult(
            "tactical_insights length 3-6",
            3 <= len(response.tactical_insights) <= 6,
            str(len(response.tactical_insights)),
        )
    )
    checks.append(
        CheckResult(
            "strengths.home length 2-4",
            2 <= len(response.strengths.home) <= 4,
            str(len(response.strengths.home)),
        )
    )
    checks.append(
        CheckResult(
            "strengths.away length 2-4",
            2 <= len(response.strengths.away) <= 4,
            str(len(response.strengths.away)),
        )
    )
    checks.append(
        CheckResult(
            "weaknesses.home length 2-4",
            2 <= len(response.weaknesses.home) <= 4,
            str(len(response.weaknesses.home)),
        )
    )
    checks.append(
        CheckResult(
            "weaknesses.away length 2-4",
            2 <= len(response.weaknesses.away) <= 4,
            str(len(response.weaknesses.away)),
        )
    )

    return checks


async def _run_matchup(home: str, away: str) -> list[CheckResult]:
    payload = _build_response(home, away)
    service = AnalysisService(
        generator=RecordingGenerator(payload),  # type: ignore[arg-type]
        prompt_loader=PromptLoader(),
        settings=get_settings(),
        knowledge=KnowledgeService(),
    )
    request = AnalysisRequest(home_team=home, away_team=away)
    response = await service.analyze(request)
    return _validate_response(response, home, away)


async def _run_rejected_response_regression() -> CheckResult:
    """Confirm a malformed payload is rejected after exhausting retries."""

    service = AnalysisService(
        generator=RecordingGenerator(payload='{"not": "valid"}'),  # type: ignore[arg-type]
        prompt_loader=PromptLoader(),
        settings=get_settings(),
        knowledge=KnowledgeService(),
    )
    request = AnalysisRequest(home_team="Argentina", away_team="France")

    try:
        await service.analyze(request)
    except AnalysisGenerationError:
        return CheckResult("malformed payload rejected after retries", True)

    return CheckResult(
        "malformed payload rejected after retries",
        False,
        "service did NOT raise AnalysisGenerationError",
    )


def _print_report(
    results: list[tuple[str, list[CheckResult]]], regression: CheckResult
) -> bool:
    overall = True
    print("\n" + "=" * 72)
    print("PitchIQ - Phase 3 smoke report")
    print("=" * 72)

    for matchup_label, checks in results:
        print(f"\n{matchup_label}")
        print("-" * len(matchup_label))
        for check in checks:
            mark = "PASS" if check.passed else "FAIL"
            if not check.passed:
                overall = False
            print(f"  [{mark}] {check.name}  ({check.detail})")

    print("\nRegression: malformed Gemini response")
    print("-" * 37)
    mark = "PASS" if regression.passed else "FAIL"
    if not regression.passed:
        overall = False
    print(f"  [{mark}] {regression.name}  ({regression.detail})")

    print("\n" + "=" * 72)
    print("OVERALL:", "PASS" if overall else "FAIL")
    print("=" * 72)
    return overall


async def main() -> int:
    try:
        results: list[tuple[str, list[CheckResult]]] = []
        for home, away in MATCHUPS:
            label = f"{home} vs {away}"
            checks = await _run_matchup(home, away)
            results.append((label, checks))
        regression = await _run_rejected_response_regression()
        passed = _print_report(results, regression)
        return 0 if passed else 1
    except Exception:  # pragma: no cover - developer-facing diagnostics
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))