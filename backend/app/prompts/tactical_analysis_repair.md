Your previous response could not be accepted by the analysis system. The failure was a schema or formatting problem, not an analytical one — re-emit the same tactical interpretation, this time conforming exactly to the JSON Schema.

Original matchup:
- Home team: $home_team
- Away team: $away_team

Grounded knowledge from the FIFA World Cup 2026 dataset:

$football_context

Validation problem:
$validation_error

Previous response:
$invalid_response

# What to fix

- Read the validation problem carefully. Every field named in it must be present and shaped correctly.
- Keep the same grounded facts, team names, predicted winner, and overall analytical stance as the previous response. Only the form changes.
- Re-apply the four-step reasoning protocol from the system prompt before writing JSON. The reasoning itself is not in the output.
- Apply the score calibration ladder from the system prompt. Scores should land close to where they were in the previous response unless the validation problem named them.
- Keep the analyst voice: concrete observations, varied sentence length, no filler cliches.

Return only one valid JSON object that matches the JSON Schema exactly. No Markdown, no code fences, no explanation.

