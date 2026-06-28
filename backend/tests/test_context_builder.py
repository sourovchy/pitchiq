"""Unit tests for the FootballContextBuilder."""

from __future__ import annotations

import pytest

from app.services.context_builder import FootballContextBuilder, build_football_context
from app.services.knowledge_service import KnowledgeService


@pytest.fixture(scope="module")
def knowledge_service() -> KnowledgeService:
    return KnowledgeService()


@pytest.fixture(scope="module")
def context_builder(knowledge_service: KnowledgeService) -> FootballContextBuilder:
    return FootballContextBuilder(knowledge_service)


# ---------------------------------------------------------------------------
# helper invariants
# ---------------------------------------------------------------------------


def test_context_includes_section_header(
    context_builder: FootballContextBuilder,
) -> None:
    context = context_builder.build("Argentina", "France")
    assert "FIFA WORLD CUP 2026 — GROUNDED KNOWLEDGE" in context


def test_context_contains_both_team_names(
    context_builder: FootballContextBuilder,
) -> None:
    context = context_builder.build("Argentina", "France")
    assert "Home team: Argentina" in context
    assert "Away team: France" in context


def test_context_contains_profile_metadata(
    context_builder: FootballContextBuilder,
) -> None:
    context = context_builder.build("Argentina", "France")
    assert "FIFA code ARG" in context
    assert "FIFA code FRA" in context
    assert "CONMEBOL" in context
    assert "UEFA" in context


def test_context_contains_squad_players(
    context_builder: FootballContextBuilder,
) -> None:
    context = context_builder.build("Argentina", "France")
    # The bundled dataset lists Messi for Argentina and Mbappé for France.
    assert "Lionel Messi" in context
    assert "Kylian Mbappé" in context


def test_context_contains_group_opponents(
    context_builder: FootballContextBuilder,
) -> None:
    context = context_builder.build("Argentina", "France")
    # Argentina is in group J (with Algeria, Austria, Jordan).
    assert "Group J" in context
    # France is in group I (with Senegal, Norway, ...).
    assert "Group I" in context


def test_context_includes_scheduled_fixture_when_present(
    knowledge_service: KnowledgeService,
    context_builder: FootballContextBuilder,
) -> None:
    # Pick a matchup we know appears in the bundled fixtures by querying the
    # knowledge service directly; if it's there, the context must surface it.
    candidates = [
        ("Mexico", "South Africa"),
        ("Spain", "Croatia"),
        ("Argentina", "Brazil"),  # unlikely in the group stage but cheap to try
    ]
    for home, away in candidates:
        if knowledge_service.get_fixture(home, away):
            context = context_builder.build(home, away)
            assert "Scheduled fixtures" in context
            assert any(token in context for token in (home, away))
            return
    pytest.skip("No sample fixture available in the bundled dataset")


# ---------------------------------------------------------------------------
# required matchups from the spec
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "home,away",
    [
        ("Argentina", "France"),
        ("Brazil", "Germany"),
        ("England", "Portugal"),
    ],
)
def test_spec_matchups_produce_grounded_context(
    context_builder: FootballContextBuilder,
    home: str,
    away: str,
) -> None:
    context = context_builder.build(home, away)
    assert context, f"No context generated for {home} vs {away}"
    assert f"Home team: {home}" in context
    assert f"Away team: {away}" in context
    assert "Profile" in context
    assert "Squad" in context
    assert "World Cup group" in context


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------


def test_context_flags_missing_team(
    context_builder: FootballContextBuilder,
) -> None:
    context = context_builder.build("Atlantis", "Argentina")
    assert "no matching World Cup 2026 team found" in context
    assert "Atlantis" in context
    # The known side should still produce a full section.
    assert "Away team: Argentina" in context


def test_context_with_both_unknown_teams(
    context_builder: FootballContextBuilder,
) -> None:
    context = context_builder.build("Atlantis", "El Dorado")
    assert "no matching World Cup 2026 team found" in context
    # The header still wraps the document.
    assert "FIFA WORLD CUP 2026" in context


def test_functional_helper_matches_builder(
    knowledge_service: KnowledgeService,
) -> None:
    context = build_football_context(knowledge_service, "Brazil", "Germany")
    assert "FIFA WORLD CUP 2026 — GROUNDED KNOWLEDGE" in context
    assert "Brazil" in context
    assert "Germany" in context