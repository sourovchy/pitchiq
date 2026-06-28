"""In-memory knowledge layer for PitchIQ.

Loads the bundled FIFA World Cup 2026 JSON files once at startup and exposes
typed lookup helpers so the analysis service can ground every Gemini prompt in
the provided match, team, squad, group, and stadium data.

The service is deliberately read-only and side-effect free after construction.
All helper methods are case-insensitive and tolerate the small set of name
aliases the dataset exposes via ``name_normalised`` (USA, South Korea, Czech
Republic, Turkey, Iran, DR Congo, Ivory Coast, Cape Verde).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)

DEFAULT_KNOWLEDGE_DIRNAME = "knowledge"

# Aliases resolved against team ``name_normalised`` values when the input does
# not match a canonical ``name``.  Keys are casefolded input names; values are
# the canonical team name the alias should resolve to.  The canonical value
# must match either the raw ``name`` field or the ``name_normalised`` field
# of the corresponding entry in ``worldcup.teams.json``.
_TEAM_NAME_ALIASES: dict[str, str] = {
    "usa": "usa",
    "united states": "usa",
    "united states of america": "usa",
    "us": "usa",
    "south korea": "korea republic",
    "korea": "korea republic",
    "korea republic": "korea republic",
    "czech republic": "czechia",
    "czechia": "czechia",
    "turkey": "türkiye",
    "turkiye": "türkiye",
    "iran": "ir iran",
    "ir iran": "ir iran",
    "dr congo": "congo dr",
    "congo dr": "congo dr",
    "ivory coast": "cote d'ivoire",
    "cote d'ivoire": "cote d'ivoire",
    "cape verde": "cabo verde",
    "cabo verde": "cabo verde",
}


@dataclass(frozen=True, slots=True)
class TeamRecord:
    """Strongly-typed view over an entry from ``worldcup.teams.json``.

    ``name`` always holds the canonical (FIFA-preferred) form.  When the
    dataset provides ``name_normalised`` we treat it as canonical; otherwise
    we fall back to the raw ``name`` field.  The original raw label is kept
    on ``display_name`` so downstream code (squad lookups, prompt text) can
    still recover it when the canonical form differs from the dataset label.
    """

    name: str
    normalised: str | None
    display_name: str
    continent: str | None
    fifa_code: str | None
    group: str | None
    confed: str | None

    @property
    def lookup_keys(self) -> tuple[str, ...]:
        """Casefolded keys the record can be resolved under."""

        keys: list[str] = [self.display_name.casefold()]
        if self.normalised:
            keys.append(self.normalised.casefold())
        if self.name and self.name != self.display_name:
            keys.append(self.name.casefold())
        return tuple(keys)


@dataclass(frozen=True, slots=True)
class GroupRecord:
    name: str
    teams: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StadiumRecord:
    city: str
    name: str
    capacity: int | None
    timezone: str | None
    country: str | None


@dataclass(frozen=True, slots=True)
class PlayerRecord:
    number: int | None
    position: str | None
    name: str
    club: str | None
    club_country: str | None


@dataclass(frozen=True, slots=True)
class SquadRecord:
    team_name: str
    fifa_code: str | None
    group: str | None
    players: tuple[PlayerRecord, ...]


@dataclass(frozen=True, slots=True)
class FixtureRecord:
    round: str
    date: str | None
    time: str | None
    team1: str
    team2: str
    group: str | None
    ground: str | None


class KnowledgeService:
    """Loads World Cup JSON files once and provides typed lookup helpers."""

    def __init__(
        self,
        *,
        knowledge_dir: Path | None = None,
    ) -> None:
        self._knowledge_dir = (
            knowledge_dir
            if knowledge_dir is not None
            else Path(__file__).resolve().parents[2] / DEFAULT_KNOWLEDGE_DIRNAME
        )

        self._raw: dict[str, Any] = {}
        self._teams_by_name: dict[str, TeamRecord] = {}
        self._teams_by_code: dict[str, TeamRecord] = {}
        self._teams_by_group: dict[str, list[TeamRecord]] = {}
        self._groups_by_name: dict[str, GroupRecord] = {}
        self._stadiums_by_city: dict[str, StadiumRecord] = {}
        self._squads_by_name: dict[str, SquadRecord] = {}
        self._fixtures: tuple[FixtureRecord, ...] = ()
        self._qualifying_fixtures: tuple[FixtureRecord, ...] = ()

        self._load_all()

    # ------------------------------------------------------------------ loading

    def _load_all(self) -> None:
        if not self._knowledge_dir.is_dir():
            logger.warning(
                "Knowledge directory not found at %s; running with empty context",
                self._knowledge_dir,
            )
            return

        for json_path in sorted(self._knowledge_dir.glob("*.json")):
            try:
                payload = json.loads(json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                logger.warning("Skipping malformed knowledge file %s: %s", json_path.name, error)
                continue
            except OSError as error:
                logger.warning("Skipping unreadable knowledge file %s: %s", json_path.name, error)
                continue

            self._raw[json_path.name] = payload
            self._index_payload(json_path.name, payload)
            logger.info("Loaded %s", json_path.name)

        logger.info(
            "Knowledge layer initialized: %s teams, %s groups, %s stadiums, %s squads, %s fixtures",
            len(self._teams_by_name),
            len(self._groups_by_name),
            len(self._stadiums_by_city),
            len(self._squads_by_name),
            len(self._fixtures),
        )

    def _index_payload(self, filename: str, payload: Any) -> None:
        if filename == "worldcup.teams.json":
            self._index_teams(payload)
        elif filename == "worldcup.groups.json":
            self._index_groups(payload)
        elif filename == "worldcup.stadiums.json":
            self._index_stadiums(payload)
        elif filename == "worldcup.squads.json":
            self._index_squads(payload)
        elif filename == "worldcup.json":
            self._index_tournament_fixtures(payload)
        elif filename == "worldcup.quali_playoffs.json":
            self._index_qualifying_fixtures(payload)
        # Unknown files are intentionally ignored; the loader still logs them.

    def _index_teams(self, payload: Any) -> None:
        items = self._extract_list(payload, "teams", fallback_keys=("value",))
        for entry in items:
            display_name = self._string_field(entry, "name") or ""
            if not display_name:
                continue
            normalised = self._string_field(entry, "name_normalised")
            # Canonical resolution order:
            # 1. Alias dict value matching one of the dataset fields.
            # 2. The ``name_normalised`` field, when present.
            # 3. The raw ``name`` field as a last-resort fallback.
            canonical = self._canonical_for(display_name, normalised)
            record = TeamRecord(
                name=canonical,
                normalised=normalised,
                display_name=display_name,
                continent=self._string_field(entry, "continent"),
                fifa_code=self._string_field(entry, "fifa_code"),
                group=self._string_field(entry, "group"),
                confed=self._string_field(entry, "confed"),
            )
            for key in record.lookup_keys:
                self._teams_by_name[key] = record
            if record.fifa_code:
                self._teams_by_code[record.fifa_code.upper()] = record
            if record.group:
                self._teams_by_group.setdefault(record.group, []).append(record)

    @staticmethod
    def _canonical_for(display_name: str, normalised: str | None) -> str:
        """Return the canonical identity for a team entry.

        The alias dict values are matched case-insensitively against the
        dataset's ``name`` and ``name_normalised`` fields; the original
        casing of the matching dataset field is preserved in the result.
        """

        candidates = [display_name]
        if normalised:
            candidates.append(normalised)
        candidate_index = {candidate.casefold(): candidate for candidate in candidates}
        for alias_value in _TEAM_NAME_ALIASES.values():
            hit = candidate_index.get(alias_value.casefold())
            if hit is not None:
                return hit
        if normalised:
            return normalised
        return display_name

    def _index_groups(self, payload: Any) -> None:
        groups = self._extract_list(payload, "groups")
        for entry in groups:
            name = self._string_field(entry, "name")
            if not name:
                continue
            teams = self._parse_group_teams(entry.get("teams"))
            if not teams:
                continue
            self._groups_by_name[name.casefold()] = GroupRecord(name=name, teams=teams)
            # Mirror by group letter for quick lookups ("A" -> "Group A").
            short = name.replace("Group ", "").strip()
            if short:
                self._groups_by_name[short.casefold()] = GroupRecord(name=name, teams=teams)

    @staticmethod
    def _parse_group_teams(value: Any) -> tuple[str, ...]:
        """Normalise the ``teams`` field of a group entry into a tuple of names.

        The bundled JSON sometimes serialises the field as a space-separated
        string and sometimes as a list of strings; accept both.
        """

        if isinstance(value, list):
            return tuple(
                str(item).strip() for item in value if isinstance(item, (str, int)) and str(item).strip()
            )
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return ()
            return tuple(part for part in stripped.split() if part)
        return ()

    def _index_stadiums(self, payload: Any) -> None:
        stadiums = self._extract_list(payload, "stadiums")
        for entry in stadiums:
            city = self._string_field(entry, "city")
            name = self._string_field(entry, "name")
            if not city or not name:
                continue
            capacity = self._int_field(entry, "capacity")
            country = self._string_field(entry, "cc")
            # Normalise the country code to uppercase ISO-3166 form so callers
            # can rely on a stable shape regardless of source casing.
            if country:
                country = country.upper()
            self._stadiums_by_city[city.casefold()] = StadiumRecord(
                city=city,
                name=name,
                capacity=capacity,
                timezone=self._string_field(entry, "timezone"),
                country=country,
            )

    def _index_squads(self, payload: Any) -> None:
        teams = payload if isinstance(payload, list) else self._extract_list(payload, "teams")
        for entry in teams:
            team_name = self._string_field(entry, "name")
            if not team_name:
                continue
            players_raw = entry.get("players") if isinstance(entry, dict) else None
            players: list[PlayerRecord] = []
            if isinstance(players_raw, list):
                for player in players_raw:
                    if not isinstance(player, dict):
                        continue
                    club = player.get("club")
                    club_name: str | None = None
                    club_country: str | None = None
                    if isinstance(club, dict):
                        club_name = self._string_field(club, "name")
                        club_country = self._string_field(club, "country")
                    players.append(
                        PlayerRecord(
                            number=self._int_field(player, "number"),
                            position=self._string_field(player, "pos"),
                            name=self._string_field(player, "name") or "",
                            club=club_name,
                            club_country=club_country,
                        )
                    )
            self._squads_by_name[team_name.casefold()] = SquadRecord(
                team_name=team_name,
                fifa_code=self._string_field(entry, "fifa_code"),
                group=self._string_field(entry, "group"),
                players=tuple(players),
            )

    def _index_tournament_fixtures(self, payload: Any) -> None:
        matches = self._extract_list(payload, "matches")
        self._fixtures = self._build_fixture_records(matches)

    def _index_qualifying_fixtures(self, payload: Any) -> None:
        matches = self._extract_list(payload, "matches")
        self._qualifying_fixtures = self._build_fixture_records(matches)

    def _build_fixture_records(
        self,
        matches: Iterable[Any],
    ) -> tuple[FixtureRecord, ...]:
        records: list[FixtureRecord] = []
        for entry in matches:
            if not isinstance(entry, dict):
                continue
            team1 = self._string_field(entry, "team1")
            team2 = self._string_field(entry, "team2")
            round_name = self._string_field(entry, "round")
            if not team1 or not team2 or not round_name:
                continue
            records.append(
                FixtureRecord(
                    round=round_name,
                    date=self._string_field(entry, "date"),
                    time=self._string_field(entry, "time"),
                    team1=team1,
                    team2=team2,
                    group=self._string_field(entry, "group"),
                    ground=self._string_field(entry, "ground"),
                )
            )
        return tuple(records)

    @staticmethod
    def _extract_list(
        payload: Any,
        primary_key: str,
        *,
        fallback_keys: tuple[str, ...] = (),
    ) -> list[Any]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, (dict, list))]
        if not isinstance(payload, dict):
            return []
        if primary_key in payload and isinstance(payload[primary_key], list):
            return [item for item in payload[primary_key] if isinstance(item, (dict, list))]
        for key in fallback_keys:
            if key in payload and isinstance(payload[key], list):
                return [item for item in payload[key] if isinstance(item, (dict, list))]
        return []

    @staticmethod
    def _string_field(entry: dict[str, Any], key: str) -> str | None:
        value = entry.get(key)
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return None

    @staticmethod
    def _int_field(entry: dict[str, Any], key: str) -> int | None:
        value = entry.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, str):
            try:
                return int(value.replace(",", ""))
            except ValueError:
                return None
        return None

    # --------------------------------------------------------------- public api

    def resolve_team(self, name: str) -> TeamRecord | None:
        """Resolve a possibly-aliased team name to its canonical record.

        Resolution order:

        1. Explicit alias dictionary (``_TEAM_NAME_ALIASES``).
        2. Direct index hit on the canonical or display name.
        3. Case-insensitive substring fallback across canonical names.
        """

        if not name:
            return None
        key = name.strip().casefold()
        if not key:
            return None

        aliased = _TEAM_NAME_ALIASES.get(key)
        if aliased:
            record = self._teams_by_name.get(aliased.casefold())
            if record is not None:
                return record

        record = self._teams_by_name.get(key)
        if record is not None:
            return record

        # Fuzzy fallback: case-insensitive substring on the canonical names.
        for candidate_key, candidate in self._teams_by_name.items():
            if key in candidate_key or candidate_key in key:
                return candidate
        return None

    def get_team(self, name: str) -> dict[str, Any] | None:
        record = self.resolve_team(name)
        if record is None:
            return None
        return self._team_to_dict(record)

    def search_team(self, query: str) -> list[dict[str, Any]]:
        """Return teams whose name or normalised name contains ``query``."""

        if not query:
            return []
        needle = query.strip().casefold()
        if not needle:
            return []
        seen: set[str] = set()
        results: list[dict[str, Any]] = []
        for record in self._teams_by_name.values():
            haystacks = {record.name.casefold()}
            if record.normalised:
                haystacks.add(record.normalised.casefold())
            if any(needle in hay for hay in haystacks):
                key = record.name.casefold()
                if key in seen:
                    continue
                seen.add(key)
                results.append(self._team_to_dict(record))
        return results

    def get_group(self, identifier: str) -> dict[str, Any] | None:
        if not identifier:
            return None
        key = identifier.strip().casefold()
        record = self._groups_by_name.get(key)
        if record is None:
            # Accept plain letters such as "A" or "group a".
            short = key.replace("group ", "").strip()
            if short and short != key:
                record = self._groups_by_name.get(short)
        if record is None:
            return None
        members = [self._team_to_dict(team) for team in self._teams_in_group(record.name)]
        return {
            "name": record.name,
            "teams": record.teams,
            "members": members,
        }

    def get_squad(self, team_name: str) -> dict[str, Any] | None:
        record = self._resolve_squad(team_name)
        if record is None:
            return None
        return {
            "team": record.team_name,
            "fifa_code": record.fifa_code,
            "group": record.group,
            "player_count": len(record.players),
            "players": [self._player_to_dict(player) for player in record.players],
        }

    def get_fixture(
        self,
        home_team: str,
        away_team: str,
    ) -> list[dict[str, Any]]:
        home = self.resolve_team(home_team)
        away = self.resolve_team(away_team)
        if home is None or away is None:
            return []
        home_names = {home.name.casefold()}
        if home.normalised:
            home_names.add(home.normalised.casefold())
        away_names = {away.name.casefold()}
        if away.normalised:
            away_names.add(away.normalised.casefold())

        results: list[dict[str, Any]] = []
        for fixture in self._fixtures:
            teams = {fixture.team1.casefold(), fixture.team2.casefold()}
            if teams == home_names | away_names or teams == away_names | home_names:
                results.append(self._fixture_to_dict(fixture))
        return results

    def get_stadium(self, ground: str | None) -> dict[str, Any] | None:
        if not ground:
            return None
        record = self._stadiums_by_city.get(ground.strip().casefold())
        if record is None:
            # Fuzzy fallback: match any city that contains the query as a
            # whole token (e.g. "New York" -> "New York/New Jersey (...)").
            needle = ground.strip().casefold()
            if needle:
                token_hits: list[StadiumRecord] = []
                substring_hits: list[StadiumRecord] = []
                for city_key, candidate in self._stadiums_by_city.items():
                    if needle in city_key.split("/")[0].split(" "):
                        token_hits.append(candidate)
                    elif needle in city_key:
                        substring_hits.append(candidate)
                if token_hits:
                    record = token_hits[0]
                elif substring_hits:
                    record = substring_hits[0]
        if record is None:
            return None
        return {
            "city": record.city,
            "name": record.name,
            "capacity": record.capacity,
            "timezone": record.timezone,
            "country": record.country,
        }

    def all_fixtures(self) -> list[dict[str, Any]]:
        return [self._fixture_to_dict(fixture) for fixture in self._fixtures]

    # ----------------------------------------------------------------- metrics

    @property
    def team_count(self) -> int:
        """Number of distinct team records indexed by name."""

        return len(self._teams_by_name)

    @property
    def group_count(self) -> int:
        return len(self._groups_by_name)

    @property
    def stadium_count(self) -> int:
        return len(self._stadiums_by_city)

    @property
    def squad_count(self) -> int:
        return len(self._squads_by_name)

    @property
    def fixture_count(self) -> int:
        return len(self._fixtures)

    # -------------------------------------------------------------- serialization

    @staticmethod
    def _team_to_dict(record: TeamRecord) -> dict[str, Any]:
        return {
            "name": record.name,
            "display_name": record.display_name,
            "normalised": record.normalised,
            "continent": record.continent,
            "fifa_code": record.fifa_code,
            "group": record.group,
            "confederation": record.confed,
        }

    @staticmethod
    def _player_to_dict(record: PlayerRecord) -> dict[str, Any]:
        return {
            "number": record.number,
            "position": record.position,
            "name": record.name,
            "club": record.club,
            "club_country": record.club_country,
        }

    @staticmethod
    def _fixture_to_dict(record: FixtureRecord) -> dict[str, Any]:
        return {
            "round": record.round,
            "date": record.date,
            "time": record.time,
            "team1": record.team1,
            "team2": record.team2,
            "group": record.group,
            "ground": record.ground,
        }

    # --------------------------------------------------------------- internals

    def _teams_in_group(self, group_name: str) -> Iterable[TeamRecord]:
        for letter, members in self._teams_by_group.items():
            if letter.casefold() == group_name.replace("Group ", "").strip().casefold():
                return members
        return []

    def _resolve_squad(self, team_name: str) -> SquadRecord | None:
        if not team_name:
            return None
        key = team_name.strip().casefold()
        record = self._squads_by_name.get(key)
        if record is not None:
            return record
        team = self.resolve_team(team_name)
        if team is None:
            return None
        # Squads JSON is keyed by the dataset's raw ``name`` field, which we
        # preserve on ``display_name``; fall back to canonical ``name`` last.
        for candidate in (team.display_name, team.name):
            if not candidate:
                continue
            record = self._squads_by_name.get(candidate.casefold())
            if record is not None:
                return record
        return None


@lru_cache(maxsize=1)
def get_knowledge_service() -> KnowledgeService:
    """Return a process-wide cached :class:`KnowledgeService`."""

    return KnowledgeService()
