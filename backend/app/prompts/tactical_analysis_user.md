Produce a complete pre-match tactical analysis for:

Home team: $home_team
Away team: $away_team

Grounded knowledge from the FIFA World Cup 2026 dataset:

$football_context

Treat the grounded knowledge above as the only reliable source for team identities, confederations, groups, registered squad personnel, scheduled fixtures, and venues. You may reference the personnel who appear in it; do not reference any who do not. When grounded knowledge is missing or thin, reason from established tactical identities and confederational playing styles only.

# Working procedure

Run through these four steps in order before writing JSON. The output is JSON only — do not include the reasoning itself.

1. **Base structures.** Lock in the most likely base formation and shape for each team. Note the numerical balance in each phase (e.g. 3v2 centrally in build-up, 2v3 in the press).
2. **Zone interactions.** Identify the zones most likely to decide the matchup. For each, explain why the balance favors one team or sits even, and which role or unit carries the load.
3. **Deciding questions.** Distill the two or three questions that, if answered differently than expected, would flip the prediction. Examples: who wins the second ball, who controls zone 14, who handles the press trigger first, who copes with the wide-back overload.
4. **Coaching implications.** Convert the answers into a concrete action per team and one decisive tactical adjustment that decides the result.

# Quality bar per field

- `matchOverview`: one paragraph that names the central tactical question of the matchup and gives the analyst's first answer. No throat-clearing.
- `playingStyle`: how the team habitually builds, presses, and transitions from its base shape. Patterns, not adjectives.
- `tacticalIdentity`: the philosophy that sits underneath the patterns. Why this team plays the way it plays. Distinct from `playingStyle` — do not repeat it.
- `formations.matchup`: the interaction between the two base shapes, including numerical balances and which side of the pitch the asymmetry shows.
- `strengths` / `weaknesses`: matchup-specific. A strength is only a strength if the opposing weakness invites it. Two to four items each.
- `keyBattles`: name a zone and the role or unit on each side. In `analysis`, state **what happens**, **who wins if X**, and **why** in two or three tight sentences.
- `tacticalInsights`: identify the most important tactical themes naturally and let the insights emerge from those themes. Do not force a fixed mapping to a fixed number of questions. Three to six items, ordered from most to least consequential, with `importance` set honestly.
- `expectedGameFlow`: open, middle, close phases. Each phase names a specific trigger (e.g. "the first sustained spell of away possession" or "the first substitution window") rather than vague tempo changes.
- `coachRecommendation`: per team, give an action, a trigger condition, and a one-line rationale. End with the single decisive adjustment that decides the result.
- Scores: apply the calibration ladder from the system prompt. If a score sits at 50, the matchup is genuinely even on that attribute; do not drift.

# Voice

Professional, analytical, varied in sentence length. Avoid the cliche phrases listed in the system prompt. One specific observation per sentence. No padding, no restating the question.

Return only the schema-conforming JSON object.

