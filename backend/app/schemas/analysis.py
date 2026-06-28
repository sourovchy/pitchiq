from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator
from pydantic.alias_generators import to_camel

TeamName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=160)]
AnalysisText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=12, max_length=700)]
Score = Annotated[int, Field(ge=0, le=100)]


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


class AnalysisRequest(CamelModel):
    home_team: TeamName
    away_team: TeamName

    @model_validator(mode="after")
    def teams_must_differ(self) -> "AnalysisRequest":
        if self.home_team.casefold() == self.away_team.casefold():
            raise ValueError("Home and away teams must be different")
        return self


class TeamProfile(CamelModel):
    name: TeamName
    formation: ShortText
    playing_style: AnalysisText
    tactical_identity: AnalysisText


class FormationMatchup(CamelModel):
    home: ShortText
    away: ShortText
    matchup: AnalysisText


class TeamFactors(CamelModel):
    home: list[AnalysisText] = Field(min_length=2, max_length=4)
    away: list[AnalysisText] = Field(min_length=2, max_length=4)


class KeyBattle(CamelModel):
    zone: ShortText
    home_player_or_unit: ShortText
    away_player_or_unit: ShortText
    edge: Literal["home", "away", "even"]
    analysis: AnalysisText


class TacticalInsight(CamelModel):
    title: ShortText
    detail: AnalysisText
    importance: Literal["critical", "high", "medium"]


class GameFlow(CamelModel):
    opening_phase: AnalysisText
    middle_phase: AnalysisText
    closing_phase: AnalysisText


class CoachRecommendation(CamelModel):
    home: AnalysisText
    away: AnalysisText
    decisive_adjustment: AnalysisText


class TeamScore(CamelModel):
    home: Score
    away: Score


class AnalysisResponse(CamelModel):
    match_overview: AnalysisText
    home_team: TeamProfile
    away_team: TeamProfile
    predicted_winner: TeamName | Literal["Draw"]
    confidence: Score
    formations: FormationMatchup
    strengths: TeamFactors
    weaknesses: TeamFactors
    key_battles: list[KeyBattle] = Field(min_length=3, max_length=5)
    tactical_insights: list[TacticalInsight] = Field(min_length=3, max_length=6)
    expected_game_flow: GameFlow
    coach_recommendation: CoachRecommendation
    pressing_score: TeamScore
    possession_score: TeamScore
    attacking_threat: TeamScore
    defensive_stability: TeamScore

    @field_validator("predicted_winner")
    @classmethod
    def predicted_winner_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Predicted winner cannot be blank")
        return value


class AnalysisApiResponse(CamelModel):
    data: AnalysisResponse
    model: str

