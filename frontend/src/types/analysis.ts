export type Score = number;

export type Importance = "critical" | "high" | "medium";
export type Edge = "home" | "away" | "even";

export interface AnalysisRequestPayload {
  homeTeam: string;
  awayTeam: string;
}

export interface TeamProfile {
  name: string;
  formation: string;
  playingStyle: string;
  tacticalIdentity: string;
}

export interface FormationMatchup {
  home: string;
  away: string;
  matchup: string;
}

export interface TeamFactors {
  home: string[];
  away: string[];
}

export interface KeyBattle {
  zone: string;
  homePlayerOrUnit: string;
  awayPlayerOrUnit: string;
  edge: Edge;
  analysis: string;
}

export interface TacticalInsight {
  title: string;
  detail: string;
  importance: Importance;
}

export interface GameFlow {
  openingPhase: string;
  middlePhase: string;
  closingPhase: string;
}

export interface CoachRecommendation {
  home: string;
  away: string;
  decisiveAdjustment: string;
}

export interface TeamScore {
  home: Score;
  away: Score;
}

export interface AnalysisResponse {
  matchOverview: string;
  homeTeam: TeamProfile;
  awayTeam: TeamProfile;
  predictedWinner: string;
  confidence: Score;
  formations: FormationMatchup;
  strengths: TeamFactors;
  weaknesses: TeamFactors;
  keyBattles: KeyBattle[];
  tacticalInsights: TacticalInsight[];
  expectedGameFlow: GameFlow;
  coachRecommendation: CoachRecommendation;
  pressingScore: TeamScore;
  possessionScore: TeamScore;
  attackingThreat: TeamScore;
  defensiveStability: TeamScore;
}

export interface AnalysisApiResponse {
  data: AnalysisResponse;
  model: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}