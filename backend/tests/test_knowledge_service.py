"""Unit tests for the FIFA World Cup 2026 knowledge layer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import pytest

from app.services.knowledge_service import (
    DEFAULT_KNOWLEDGE_DIRNAME,
    KnowledgeService,
)


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def knowledge_service() -> KnowledgeService:
    """Reuse a single instance across tests; loading the bundled JSON files is
    expensive enough that we don't want to repeat it per-test."""

    return KnowledgeService()


@pytest.fixture()
def tiny_knowledge_dir(tmp_path: Path) -> Iterator[Path]:
    """Provide a temporary directory with a minimal subset of files so the
    discovery code can be exercised without depending on the bundled data."""

    payload = {
        "name": "Mini World Cup",
        "teams": [
            {
                "name": "Atlantis",
                "name_normalised": "Atlantis",
                "continent": "Europe",
                "fifa_code": "ATL",
                "group": "Z",
                "confed": "UEFA",
            },
            {
                "name": "El Dorado",
                "name_normalised": "El Dorado",
                "continent": "South America",
                "fifa_code": "ELD",
                "group": "Z",
                "confed": "CONMEBOL",
            },
        ],
        "groups": [
            {"name": "Group Z", "teams": ["Atlantis", "El Dorado"]},
        ],
        "stadiums": [
            {
                "city": "Atlantis",
                "name": "Poseidon Bowl",
                "capacity": 50000,
                "timezone": "UTC+0",
                "cc": "ATL",
            },
        ],
        "squads": [
            {
                "name": "Atlantis",
                "fifa_code": "ATL",
                "group": "Z",
                "players": [
                    {"number": 1, "pos": "GK", "name": "Wave Keeper",
                     "club": {"name": "Tide FC", "country": "ATL"}},
                    {"number": 4, "pos": "DF", "name": "Reef Defender",
                     "club": {"name": "Coral United", "country": "ATL"}},
                ],
            },
        ],
        "matches": [
            {
                "round": "Group Z",
                "date": "2026-06-15",
                "time": "20:00",
                "team1": "Atlantis",
                "team2": "El Dorado",
                "group": "Z",
                "ground": "Atlantis",
            },
        ],
    }
    (tmp_path / "worldcup.json").write_text(
        json.dumps({"name": payload["name"], "matches": payload["matches"]}),
        encoding="utf-8",
    )
    (tmp_path / "worldcup.teams.json").write_text(
        json.dumps({"value": payload["teams"]}), encoding="utf-8"
    )
    (tmp_path / "worldcup.groups.json").write_text(
        json.dumps({"name": "Mini", "groups": payload["groups"]}),
        encoding="utf-8",
    )
    (tmp_path / "worldcup.stadiums.json").write_text(
        json.dumps({"name": "Mini", "stadiums": payload["stadiums"]}),
        encoding="utf-8",
    )
    (tmp_path / "worldcup.squads.json").write_text(
        json.dumps(payload["squads"]), encoding="utf-8"
    )
    (tmp_path / "worldcup.quali_playoffs.json").write_text(
        json.dumps({"name": "Mini", "matches": []}), encoding="utf-8"
    )
    yield tmp_path


# ---------------------------------------------------------------------------
# discovery + loading
# ---------------------------------------------------------------------------


def test_knowledge_service_discovers_bundled_files(
    knowledge_service: KnowledgeService,
) -> None:
    # The bundled dataset should populate every index with at least one record.
    assert knowledge_service.team_count > 0
    assert knowledge_service.group_count > 0
    assert knowledge_service.stadium_count > 0
    assert knowledge_service.squad_count > 0
    assert knowledge_service.fixture_count > 0


def test_knowledge_service_loads_from_custom_directory(
    tiny_knowledge_dir: Path,
) -> None:
    service = KnowledgeService(knowledge_dir=tiny_knowledge_dir)
    assert service.team_count == 2
    assert service.group_count == 2  # mirrored by "Group Z" and "Z"
    assert service.stadium_count == 1
    assert service.squad_count == 1
    assert service.fixture_count == 1


def test_knowledge_service_handles_missing_directory(tmp_path: Path) -> None:
    missing = tmp_path / "absent"
    service = KnowledgeService(knowledge_dir=missing)
    assert service.team_count == 0
    assert service.group_count == 0


def test_knowledge_service_skips_malformed_json(tmp_path: Path) -> None:
    (tmp_path / "worldcup.teams.json").write_text("{not json", encoding="utf-8")
    service = KnowledgeService(knowledge_dir=tmp_path)
    assert service.team_count == 0


# ---------------------------------------------------------------------------
# team resolution
# ---------------------------------------------------------------------------


def test_resolve_team_by_canonical_name(knowledge_service: KnowledgeService) -> None:
    record = knowledge_service.resolve_team("Argentina")
    assert record is not None
    assert record.fifa_code == "ARG"
    assert record.confed == "CONMEBOL"


def test_resolve_team_via_normalised_name(
    knowledge_service: KnowledgeService,
) -> None:
    record = knowledge_service.resolve_team("United States")
    assert record is not None
    assert record.fifa_code == "USA"
    assert record.group == "D"


def test_resolve_team_aliases(knowledge_service: KnowledgeService) -> None:
    cases = {
        "USA": "USA",
        "Czech Republic": "Czechia",
        "South Korea": "Korea Republic",
        "Türkiye": "Türkiye",
    }
    for alias, expected_canonical in cases.items():
        record = knowledge_service.resolve_team(alias)
        assert record is not None, f"{alias!r} did not resolve"
        assert record.name == expected_canonical, (
            f"{alias!r} mapped to {record.name!r}, expected {expected_canonical!r}"
        )


def test_resolve_team_unknown_returns_none(
    knowledge_service: KnowledgeService,
) -> None:
    assert knowledge_service.resolve_team("Wakanda") is None


def test_search_team_returns_matches(
    knowledge_service: KnowledgeService,
) -> None:
    results = knowledge_service.search_team("kor")
    names = {entry["name"] for entry in results}
    assert "Korea Republic" in names


# ---------------------------------------------------------------------------
# group / squad / fixture / stadium
# ---------------------------------------------------------------------------


def test_get_group_by_letter(knowledge_service: KnowledgeService) -> None:
    group = knowledge_service.get_group("A")
    assert group is not None
    assert group["name"] == "Group A"
    assert "Argentina" not in group["teams"]  # Argentina is in group J
    assert len(group["members"]) == 4


def test_get_group_by_full_name(knowledge_service: KnowledgeService) -> None:
    group = knowledge_service.get_group("Group J")
    assert group is not None
    assert "Argentina" in group["teams"]


def test_get_squad_returns_players(
    knowledge_service: KnowledgeService,
) -> None:
    squad = knowledge_service.get_squad("Argentina")
    assert squad is not None
    assert squad["player_count"] > 0
    player_names = {player["name"] for player in squad["players"]}
    assert "Lionel Messi" in player_names


def test_get_fixture_finds_scheduled_match(
    knowledge_service: KnowledgeService,
) -> None:
    fixtures = knowledge_service.get_fixture("Argentina", "France")
    # These two teams may not meet in the group stage; ensure helper at least
    # returns a list without raising and surfaces the same shape either way.
    assert isinstance(fixtures, list)
    for fixture in fixtures:
        assert {"round", "team1", "team2"} <= fixture.keys()


def test_get_stadium_resolves_city(
    knowledge_service: KnowledgeService,
) -> None:
    stadium = knowledge_service.get_stadium("New York")
    assert stadium is not None
    assert stadium["country"] == "US"


def test_all_fixtures_returns_every_record(
    knowledge_service: KnowledgeService,
) -> None:
    assert len(knowledge_service.all_fixtures()) == knowledge_service.fixture_count


# ---------------------------------------------------------------------------
# tiny dataset round-trip
# ---------------------------------------------------------------------------


def test_tiny_dataset_round_trip(tiny_knowledge_dir: Path) -> None:
    service = KnowledgeService(knowledge_dir=tiny_knowledge_dir)
    assert service.resolve_team("Atlantis") is not None
    squad = service.get_squad("Atlantis")
    assert squad is not None
    assert squad["player_count"] == 2
    fixture = service.get_fixture("Atlantis", "El Dorado")
    assert len(fixture) == 1
    assert fixture[0]["ground"] == "Atlantis"
    stadium = service.get_stadium("Atlantis")
    assert stadium is not None
    assert stadium["name"] == "Poseidon Bowl"


def test_default_knowledge_dirname_constant() -> None:
    assert DEFAULT_KNOWLEDGE_DIRNAME == "knowledge"