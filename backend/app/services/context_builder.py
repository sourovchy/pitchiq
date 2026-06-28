"""Build grounded football contexts for the tactical analysis prompt.

Given the two teams a user requested, this module queries the
:class:`KnowledgeService` for the slice of World Cup 2026 data most useful
for a pre-match report.  The output is a plain string that can be injected
into the user prompt without changing the public API contract.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)

# How many representative players per role we surface for each squad.  Keeps
# the prompt compact while still giving Gemini concrete personnel.
_PLAYERS_PER_ROLE = 3

# Roles we expose in a deterministic order so the prompt reads consistently.
_POSITION_ORDER: tuple[str, ...] = ("GK", "DF", "MF", "FW")


class FootballContextBuilder:
    """Assemble a per-match football knowledge snippet."""

    def __init__(self, knowledge: "KnowledgeService") -> None:
        self._knowledge = knowledge

    def build(self, home_team: str, away_team: str) -> str:
        home = self._knowledge.resolve_team(home_team)
        away = self._knowledge.resolve_team(away_team)

        sections: list[str] = ["FIFA WORLD CUP 2026 — GROUNDED KNOWLEDGE"]

        sections.extend(self._team_section("Home team", home, query=home_team))
        sections.extend(self._team_section("Away team", away, query=away_team))

        if home is not None and away is not None:
            sections.extend(self._head_to_head_sections(home.name, away.name))
        else:
            missing = [
                label
                for label, record in (("Home team", home), ("Away team", away))
                if record is None
            ]
            if missing:
                sections.append(
                    "Team resolution: "
                    + ", ".join(missing)
                    + " not found in the World Cup 2026 dataset."
                )

        return "\n\n".join(section for section in sections if section).strip()

    # ---------------------------------------------------------------- builders

    def _team_section(
        self,
        label: str,
        record,
        query: str = "",
    ) -> list[str]:
        if record is None:
            # Echo the original query so downstream prompts (and humans
            # reading the rendered context) can see exactly which input
            # failed to resolve.
            echoed = query.strip() or "(unnamed team)"
            return [f"{label} ({echoed}): no matching World Cup 2026 team found."]

        lines = [f"{label}: {record.name}"]
        meta_bits: list[str] = []
        if record.fifa_code:
            meta_bits.append(f"FIFA code {record.fifa_code}")
        if record.confed:
            meta_bits.append(f"Confederation: {record.confed}")
        if record.continent:
            meta_bits.append(f"Continent: {record.continent}")
        if record.group:
            meta_bits.append(f"World Cup group: {record.group}")
        if record.normalised and record.normalised != record.name:
            meta_bits.append(f"Also known as: {record.normalised}")
        if meta_bits:
            lines.append("Profile — " + "; ".join(meta_bits))

        squad = self._knowledge.get_squad(record.name)
        if squad is not None:
            lines.append(self._squad_summary(squad))

        group_summary = self._group_summary(record.name, record.group)
        if group_summary:
            lines.append(group_summary)

        return ["\n".join(lines)]

    def _squad_summary(self, squad: dict) -> str:
        players = squad.get("players") or []
        if not players:
            return "Squad: no registered players in the dataset."

        header_bits: list[str] = [f"Squad size: {squad.get('player_count', len(players))}"]
        fifa_code = squad.get("fifa_code")
        if fifa_code:
            header_bits.append(f"FIFA code {fifa_code}")
        header = "Squad — " + "; ".join(header_bits) + "."

        buckets: dict[str, list[str]] = {pos: [] for pos in _POSITION_ORDER}
        other: list[str] = []
        for player in players:
            position = (player.get("position") or "").upper()
            label = self._format_player(player)
            if position in buckets:
                buckets[position].append(label)
            else:
                other.append(label)

        lines = [header]
        for position in _POSITION_ORDER:
            names = buckets[position][:_PLAYERS_PER_ROLE]
            if not names:
                continue
            lines.append(
                f"  - {self._position_heading(position)}: " + ", ".join(names)
            )
        if other:
            lines.append("  - Others: " + ", ".join(other[:_PLAYERS_PER_ROLE]))
        return "\n".join(lines)

    def _group_summary(self, team_name: str, group_letter: str | None) -> str:
        identifier = f"Group {group_letter}" if group_letter else team_name
        group = self._knowledge.get_group(identifier)
        if group is None:
            return ""
        opponents = [name for name in group.get("teams", []) if name != team_name]
        if not opponents:
            return f"World Cup group: {group['name']}."
        return f"World Cup group {group['name']}: opponents include " + ", ".join(opponents) + "."

    def _head_to_head_sections(self, home_name: str, away_name: str) -> list[str]:
        sections: list[str] = []

        fixtures = self._knowledge.get_fixture(home_name, away_name)
        if fixtures:
            sections.append(self._fixtures_section("Scheduled fixtures", fixtures))

        stadium = self._first_fixture_stadium(fixtures)
        if stadium is not None:
            sections.append(self._stadium_section(stadium))

        return sections

    def _fixtures_section(self, heading: str, fixtures: list[dict]) -> str:
        ordered = sorted(
            fixtures,
            key=lambda fixture: (
                fixture.get("date") or "",
                fixture.get("time") or "",
            ),
        )
        lines = [f"{heading} ({len(ordered)}):"]
        for fixture in ordered:
            bits = [
                fixture["team1"],
                "vs",
                fixture["team2"],
            ]
            if fixture.get("round"):
                bits.append(f"[{fixture['round']}]")
            if fixture.get("date"):
                bits.append(f"on {fixture['date']}")
            if fixture.get("time"):
                bits.append(f"at {fixture['time']}")
            if fixture.get("ground"):
                bits.append(f"at {fixture['ground']}")
            lines.append("- " + " ".join(bits))
        return "\n".join(lines)

    def _stadium_section(self, ground: str) -> str:
        stadium = self._knowledge.get_stadium(ground)
        if stadium is None:
            return ""
        bits = [f"Venue: {stadium['name']} in {stadium['city']}"]
        if stadium.get("country"):
            bits.append(f"({stadium['country'].upper()})")
        if stadium.get("capacity"):
            bits.append(f"— capacity {stadium['capacity']:,}")
        if stadium.get("timezone"):
            bits.append(f"· kickoff in {stadium['timezone']}")
        return " ".join(bits)

    @staticmethod
    def _format_player(player: dict) -> str:
        name = player.get("name") or "Unknown"
        club = player.get("club")
        country = player.get("club_country")
        if club and country:
            return f"{name} ({club}, {country})"
        if club:
            return f"{name} ({club})"
        return name

    @staticmethod
    def _position_heading(position: str) -> str:
        return {
            "GK": "Goalkeepers",
            "DF": "Defenders",
            "MF": "Midfielders",
            "FW": "Forwards",
        }.get(position, position)

    @staticmethod
    def _first_fixture_stadium(fixtures: list[dict]) -> str | None:
        for fixture in fixtures:
            ground = fixture.get("ground")
            if ground:
                return ground
        return None


def build_football_context(
    knowledge: "KnowledgeService",
    home_team: str,
    away_team: str,
) -> str:
    """Functional helper used by the analysis service and tests."""

    builder = FootballContextBuilder(knowledge)
    context = builder.build(home_team, away_team)
    if not context:
        logger.info(
            "No World Cup 2026 knowledge available for %s vs %s",
            home_team,
            away_team,
        )
    return context
