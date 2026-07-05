"""Latency benchmark for the PitchIQ analysis pipeline.

Runs the four flagship FIFA World Cup 2026 matchups through the real
``AnalysisService`` (prompt loading, grounding, Gemini call, schema
validation, retry) and records per-stage timings plus token usage.  The
output is a JSON report under ``backend/scripts/benchmarks/<timestamp>/``
so successive runs can be compared to the v1.0.0 baseline.

The script is fully offline-capable through ``--stub``: a deterministic
generator returns schema-conforming payloads with realistic Gemini-style
latency so the benchmark can be exercised in CI without an API key.

Run with the project's Python interpreter:

    & "C:\\Users\\ACER\\AppData\\Local\\Python\\bin\\python.exe" \\
        backend/scripts/benchmark_matchups.py

    # Offline mode (no API key required, deterministic timings):
    python backend/scripts/benchmark_matchups.py --stub

    # Override the latency the stub simulates (seconds):
    python backend/scripts/benchmark_matchups.py --stub --latency 5

    # Save results under a custom directory name:
    python backend/scripts/benchmark_matchups.py --label my-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import statistics
import sys
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

# Ensure ``app.*`` imports resolve regardless of where the script is invoked from.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _PROJECT_ROOT)

from app.config.settings import Settings, get_settings  # noqa: E402
from app.schemas.analysis import (  # noqa: E402
    AnalysisRequest,
    AnalysisResponse,
    CoachRecommendation,
    FormationMatchup,
    GameFlow,
    KeyBattle,
    TacticalInsight,
    TeamFactors,
    TeamProfile,
    TeamScore,
)
from app.services.analysis_service import AnalysisService  # noqa: E402
from app.services.context_builder import build_football_context  # noqa: E402
from app.services.gemini_service import JsonGenerationService  # noqa: E402
from app.services.knowledge_service import KnowledgeService  # noqa: E402

logger = logging.getLogger("benchmark")


# Reference timings captured against v1.0.0 (da0575d) on the same machine.
# Recorded live from 4 matchups against gemini-2.5-flash with the production
# prompt set and ``DEFAULT_MAX_OUTPUT_TOKENS=8192``.
V100_BASELINE: dict[str, float] = {
    "average_ms": 27070.0,
    "median_ms": 26110.0,
    "gemini_ms": 27060.0,
}


MATCHUPS: list[tuple[str, str]] = [
    ("Argentina", "France"),
    ("Brazil", "Germany"),
    ("England", "Portugal"),
    ("Japan", "Morocco"),
]


# ---------------------------------------------------------------------------
# Stage timing dataclasses
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class StageTimings:
    """Wall-clock duration of every observable stage in the pipeline."""

    prompt_loading_ms: float = 0.0
    prompt_build_ms: float = 0.0
    grounding_ms: float = 0.0
    gemini_api_ms: float = 0.0
    validation_ms: float = 0.0
    serialization_ms: float = 0.0


@dataclass(slots=True)
class MatchupResult:
    matchup: str
    success: bool
    total_ms: float
    prompt_loading_ms: float
    prompt_build_ms: float
    grounding_ms: float
    gemini_api_ms: float
    validation_ms: float
    serialization_ms: float
    attempts: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    validation_error: str | None
    payload_chars: int
    error: str | None
    payload_path: str


# ---------------------------------------------------------------------------
# Instrumented real Gemini generator
# ---------------------------------------------------------------------------


class InstrumentedGenerator(JsonGenerationService):
    """Times the underlying ``JsonGenerationService`` and captures usage."""

    def __init__(self, inner: JsonGenerationService) -> None:
        self._inner = inner
        self.last_gemini_ms: float = 0.0
        self.last_text: str = ""

    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Mapping[str, Any],
    ) -> str:
        start = time.perf_counter()
        text = await self._inner.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )
        self.last_gemini_ms = (time.perf_counter() - start) * 1000.0
        self.last_text = text
        return text


# ---------------------------------------------------------------------------
# Offline stub generator (one per matchup so names line up with the request)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class _StubUsage:
    prompt_token_count: int
    candidates_token_count: int
    total_token_count: int


class _StubResponse:
    """Minimal duck-typed response so downstream extraction reads tokens."""

    def __init__(self, text: str, usage: _StubUsage) -> None:
        self.text = text
        self.usage_metadata = usage


class StubGeminiGenerator(JsonGenerationService):
    """Deterministic generator that returns a schema-conforming payload.

    Simulates Gemini-class latency and returns a payload sized to look
    like the live responses.  Each instance is bound to a single (home,
    away) matchup so the response carries the right team names — the
    service validates them via ``_validate_match_identity``.
    """

    def __init__(
        self,
        *,
        home: str,
        away: str,
        latency_seconds: float = 25.0,
    ) -> None:
        self._home = home
        self._away = away
        self._latency = latency_seconds
        self.last_usage: _StubUsage | None = None

    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Mapping[str, Any],
    ) -> str:
        await asyncio.sleep(self._latency)
        payload_json = self._build_payload()
        prompt_chars = len(system_prompt) + len(user_prompt)
        self.last_usage = _StubUsage(
            prompt_token_count=int(prompt_chars / 4),
            candidates_token_count=int(len(payload_json) / 4),
            total_token_count=int((prompt_chars + len(payload_json)) / 4),
        )
        return payload_json

    def _build_payload(self) -> str:
        """Synthesise a schema-valid ``AnalysisResponse`` and dump it as JSON.

        Constructing the real Pydantic model guarantees the payload matches
        every constraint (length, range, ``extra='forbid'``, ``importance``
        literal, etc.) without hand-rolling aliases and trimmed strings.
        ``model_dump_json(by_alias=True)`` then emits the camelCase keys the
        service expects after validation.
        """
        detail = "Tactical pattern observed in the data. "
        body = (detail * 8)[:900]
        pad_home = (body + " ")[:240]
        pad_away = (body + " ")[:240]

        response = AnalysisResponse(
            match_overview=(
                "Formation contrast decides midfield control and half-space access. "
                + body[:200]
            ),
            home_team=TeamProfile(
                name=self._home,
                formation="4-3-3",
                playing_style="Positional possession with attacking fullbacks. " + pad_home,
                tactical_identity="Half-space occupation through eights. " + pad_home,
            ),
            away_team=TeamProfile(
                name=self._away,
                formation="4-2-3-1",
                playing_style="Vertical transitions from a compact mid-block. " + pad_away,
                tactical_identity="Counter-press built from a double pivot. " + pad_away,
            ),
            predicted_winner=self._home,
            confidence=67,
            formations=FormationMatchup(
                home="4-3-3",
                away="4-2-3-1",
                matchup="Wide rotations vs central overloads shape the half-spaces. " + body[:240],
            ),
            strengths=TeamFactors(
                home=[
                    "Half-space occupation",
                    "Pressing structure",
                    "Set-piece delivery",
                ],
                away=[
                    "Counter-press triggers",
                    "Compact mid-block",
                    "Wing isolation",
                ],
            ),
            weaknesses=TeamFactors(
                home=["Full-back exposure", "Slow rest-defence"],
                away=["Aerial duels", "Single-pivot cover"],
            ),
            key_battles=[
                KeyBattle(
                    zone="Left half-space",
                    home_player_or_unit=f"{self._home} #8",
                    away_player_or_unit=f"{self._away} #10",
                    edge="home",
                    analysis=(
                        "Numerical advantage near the touchline unlocks inside-forward "
                        "combinations. " + body[:160]
                    ),
                ),
                KeyBattle(
                    zone="Central midfield",
                    home_player_or_unit=f"{self._home} double pivot",
                    away_player_or_unit=f"{self._away} single pivot",
                    edge="home",
                    analysis=(
                        "Pivots recycle play and screen counter-attacks with cover shadows. "
                        + body[:160]
                    ),
                ),
                KeyBattle(
                    zone="Right channel",
                    home_player_or_unit=f"{self._home} right-back",
                    away_player_or_unit=f"{self._away} left winger",
                    edge="even",
                    analysis=(
                        "Channel duel decides whether crosses arrive from settled play. "
                        + body[:160]
                    ),
                ),
            ],
            tactical_insights=[
                TacticalInsight(
                    title="Half-space overload",
                    detail=(
                        "Eights pin the opposite-side full-back and open diagonals. "
                        + body[:160]
                    ),
                    importance="high",
                ),
                TacticalInsight(
                    title="Counter-press triggers",
                    detail=(
                        "Compact block invites long balls that the centre-backs can step into. "
                        + body[:160]
                    ),
                    importance="medium",
                ),
                TacticalInsight(
                    title="Set-piece edge",
                    detail=(
                        "Aerial profile and delivery shape dead-ball conversion rates. "
                        + body[:160]
                    ),
                    importance="critical",
                ),
            ],
            expected_game_flow=GameFlow(
                opening_phase=(
                    "Cautious possession probe with both sides testing the press shape early. "
                    + body[:120]
                ),
                middle_phase=(
                    "Midfield duels settle into rhythm as half-spaces open through rotations. "
                    + body[:120]
                ),
                closing_phase=(
                    "Closing block management with fresh legs deciding wide combinations. "
                    + body[:120]
                ),
            ),
            coach_recommendation=CoachRecommendation(
                home="Push fullbacks high to pin the away wingers and isolate the half-spaces for combinations.",
                away="Drop a runner into the double pivot to compete for second balls and screen counters.",
                decisive_adjustment=(
                    "Control half-spaces first; everything else flows from territorial control."
                ),
            ),
            pressing_score=TeamScore(home=72, away=64),
            possession_score=TeamScore(home=58, away=42),
            attacking_threat=TeamScore(home=71, away=63),
            defensive_stability=TeamScore(home=69, away=66),
        )
        return response.model_dump_json(by_alias=True)


# ---------------------------------------------------------------------------
# Run a single matchup through the real service with stage-level timing
# ---------------------------------------------------------------------------


async def _run_matchup(
    home: str,
    away: str,
    *,
    settings: Settings,
    knowledge: KnowledgeService,
    factory,
    payload_dir: str,
) -> MatchupResult:
    """Exercise the full pipeline for one matchup and capture timings.

    ``factory(home, away)`` returns a ``JsonGenerationService`` instance —
    either the live Gemini wrapper or a stub for offline runs.
    """
    timings = StageTimings()
    raw_response = ""
    attempts = 0
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    error_text: str | None = None

    overall_start = time.perf_counter()
    try:
        from app.core.prompt_loader import PromptLoader  # local import to keep top tidy

        # Stage 1 — prompt loading: read every template the service will need.
        t0 = time.perf_counter()
        prompt_loader = PromptLoader()
        system_prompt = prompt_loader.load("tactical_analysis_system")
        timings.prompt_loading_ms = (time.perf_counter() - t0) * 1000.0

        # Stage 2 — grounding: build the football knowledge snippet.
        t0 = time.perf_counter()
        football_context = build_football_context(knowledge, home, away)
        timings.grounding_ms = (time.perf_counter() - t0) * 1000.0

        # Stage 3 — prompt build: substitute variables into the user template.
        context_block = football_context or "No grounded World Cup data available."
        t0 = time.perf_counter()
        user_prompt = prompt_loader.load(
            "tactical_analysis_user",
            home_team=home,
            away_team=away,
            football_context=context_block,
        )
        timings.prompt_build_ms = (time.perf_counter() - t0) * 1000.0

        # Stages 4-5 — Gemini call + validation through the real service.
        # Wrapping the generator lets us read ``last_gemini_ms`` after the
        # service finishes so the residual wall-clock is attributable to
        # validation/serialization overhead.
        live_generator = factory(home, away)
        live_wrapped = InstrumentedGenerator(live_generator)
        service = AnalysisService(
            generator=live_wrapped,  # type: ignore[arg-type]
            prompt_loader=prompt_loader,
            settings=settings,
            knowledge=knowledge,
        )

        t0 = time.perf_counter()
        request = AnalysisRequest(home_team=home, away_team=away)
        response: AnalysisResponse = await service.analyze(request)
        end_to_end_ms = (time.perf_counter() - t0) * 1000.0

        timings.gemini_api_ms = live_wrapped.last_gemini_ms
        timings.validation_ms = max(0.0, end_to_end_ms - live_wrapped.last_gemini_ms)

        # Stage 6 — serialization: round-trip through Pydantic / JSON to
        # capture the time it takes to serialise the validated response.
        t0 = time.perf_counter()
        payload_json = response.model_dump_json(by_alias=True)
        timings.serialization_ms = (time.perf_counter() - t0) * 1000.0

        raw_response = payload_json

        # Token counts — stub generator stashes usage, live does not.
        usage = getattr(live_generator, "last_usage", None)
        if usage is not None:
            input_tokens = int(usage.prompt_token_count)
            output_tokens = int(usage.candidates_token_count)
            total_tokens = int(usage.total_token_count)

        attempts = 1

    except Exception as exc:  # noqa: BLE001 — surface error to the report
        error_text = f"{type(exc).__name__}: {exc}"
        logger.warning("Matchup %s vs %s failed: %s", home, away, exc)

    total_ms = (time.perf_counter() - overall_start) * 1000.0

    payload_path = os.path.join(payload_dir, f"{home.lower()}_vs_{away.lower()}.json")
    if raw_response:
        try:
            with open(payload_path, "w", encoding="utf-8") as handle:
                handle.write(raw_response)
        except OSError as exc:  # pragma: no cover — disk issues
            logger.warning("Could not write payload for %s vs %s: %s", home, away, exc)
            payload_path = ""

    return MatchupResult(
        matchup=f"{home} vs {away}",
        success=error_text is None and bool(raw_response),
        total_ms=total_ms,
        prompt_loading_ms=timings.prompt_loading_ms,
        prompt_build_ms=timings.prompt_build_ms,
        grounding_ms=timings.grounding_ms,
        gemini_api_ms=timings.gemini_api_ms,
        validation_ms=timings.validation_ms,
        serialization_ms=timings.serialization_ms,
        attempts=attempts,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        validation_error=None,
        payload_chars=len(raw_response),
        error=error_text,
        payload_path=payload_path,
    )


# ---------------------------------------------------------------------------
# Aggregation & report
# ---------------------------------------------------------------------------


def _summarize(results: list[MatchupResult]) -> dict[str, float]:
    """Aggregate per-stage totals across successful matchups."""
    successful = [r for r in results if r.success]
    if not successful:
        return {
            "average_ms": 0.0,
            "median_ms": 0.0,
            "gemini_ms": 0.0,
            "min_total_ms": 0.0,
            "max_total_ms": 0.0,
            "sample_size": 0,
        }
    totals = [r.total_ms for r in successful]
    gemini = [r.gemini_api_ms for r in successful]
    return {
        "average_ms": statistics.fmean(totals),
        "median_ms": statistics.median(totals),
        "gemini_ms": statistics.fmean(gemini),
        "min_total_ms": min(totals),
        "max_total_ms": max(totals),
        "sample_size": len(successful),
    }


def _build_report(
    results: list[MatchupResult],
    *,
    label: str,
    started_at: str,
    mode: str,
) -> dict[str, Any]:
    return {
        "label": label,
        "started_at": started_at,
        "mode": mode,
        "matchups": [asdict(r) for r in results],
        "baseline": dict(V100_BASELINE),
        "current": _summarize(results),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark PitchIQ analysis latency.")
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Use the deterministic offline generator (no API key required).",
    )
    parser.add_argument(
        "--latency",
        type=float,
        default=25.0,
        help="Seconds of simulated latency in --stub mode (default: 25).",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="Optional subdirectory name under benchmarks/ (default: timestamp).",
    )
    parser.add_argument(
        "--matchup",
        action="append",
        default=None,
        help="Override the matchup list (use Home vs Away format). Can repeat.",
    )
    return parser.parse_args(argv)


async def _async_main(args: argparse.Namespace) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    label = args.label or timestamp
    out_dir = os.path.join(
        _PROJECT_ROOT, "scripts", "benchmarks", label
    )
    os.makedirs(out_dir, exist_ok=True)

    settings = get_settings()
    knowledge = KnowledgeService()

    def factory(home: str, away: str) -> JsonGenerationService:
        if args.stub:
            return StubGeminiGenerator(home=home, away=away, latency_seconds=args.latency)
        from app.services.gemini_service import GeminiService

        return GeminiService(settings=settings)

    mode = "stub" if args.stub else "live"

    matchups: list[tuple[str, str]] = []
    if args.matchup:
        for raw in args.matchup:
            if " vs " not in raw:
                raise SystemExit(f"--matchup expects 'Home vs Away', got {raw!r}")
            parts = raw.split(" vs ", 1)
            matchups.append((parts[0].strip(), parts[1].strip()))
    else:
        matchups = list(MATCHUPS)

    started_at = datetime.now(timezone.utc).isoformat()
    results: list[MatchupResult] = []
    for home, away in matchups:
        logger.info("Benchmarking %s vs %s ...", home, away)
        result = await _run_matchup(
            home,
            away,
            settings=settings,
            knowledge=knowledge,
            factory=factory,
            payload_dir=out_dir,
        )
        results.append(result)

    report = _build_report(results, label=label, started_at=started_at, mode=mode)
    report_path = os.path.join(out_dir, "report.json")
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    successful = sum(1 for r in results if r.success)
    total = len(results)
    avg = report["current"]["average_ms"]
    gemini_avg = report["current"]["gemini_ms"]

    print()
    print("=" * 72)
    print(f"PitchIQ benchmark - {mode} mode - {label}")
    print("=" * 72)
    for result in results:
        marker = "PASS" if result.success else "FAIL"
        print(
            f"  [{marker}] {result.matchup:<24} "
            f"total={result.total_ms:8.1f}ms  "
            f"gemini={result.gemini_api_ms:8.1f}ms  "
            f"attempts={result.attempts}  "
            f"tokens={result.total_tokens}"
        )
    print()
    print(f"Summary: {successful}/{total} first-pass success")
    print(f"Average latency: {avg:.0f} ms (gemini avg: {gemini_avg:.0f} ms)")
    print(f"Baseline (v1.0.0): {V100_BASELINE['average_ms']:.0f} ms")
    print(f"Report:  {report_path}")
    print("=" * 72)
    return 0 if successful == total else 1


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(sys.argv[1:] if argv is None else argv))
    try:
        return asyncio.run(_async_main(args))
    except Exception:  # pragma: no cover — surface diagnostic context
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())