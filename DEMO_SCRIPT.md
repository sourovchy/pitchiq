# PitchIQ — 3-Minute Demo Script

> **Hack Days CUET 2026**
> Total budget: **3 minutes 0 seconds** (+30 s buffer for transitions and questions)

The script is organized into **six timed segments**. Each segment lists the goal, the on-screen artifact, the spoken narration, and the back-pocket action if anything misbehaves on stage.

---

## At a glance

| # | Segment | Time | Goal |
| --- | --- | --- | --- |
| 1 | Hook | 0:00 – 0:30 | Frame the problem and the audience |
| 2 | What PitchIQ is | 0:30 – 1:00 | One-sentence product definition |
| 3 | Architecture in 30 seconds | 1:00 – 1:30 | Show the pipeline, not the slide |
| 4 | Live demo | 1:30 – 2:30 | Run one matchup, narrate the dashboard |
| 5 | Engineering highlights | 2:30 – 2:50 | The things that make it production-ready |
| 6 | Close | 2:50 – 3:00 | Call to action |

**Speaker notes** are prefixed with **🎙** — they are what you say out loud. **On-screen** notes describe what the audience should see.

---

## Pre-demo checklist

- [ ] Frontend running at `http://localhost:5173` (or your deployed URL)
- [ ] Backend running at `http://localhost:8000` with a valid `GEMINI_API_KEY`
- [ ] `/health` returns `{"status": "healthy", "service": "tactiq-api"}` (the nginx container separately exposes `/healthz` for its own probe)
- [ ] One browser tab on `http://localhost:5173/match-analysis` ready
- [ ] One browser tab on `http://localhost:8000/docs` ready (for the architecture slide backup)
- [ ] Terminal window with `docker compose ps` showing both services healthy (off-screen)
- [ ] Stop any local notifications (Slack, email, antivirus popups)
- [ ] Kill other tabs and close other apps — minimize fan noise on a laptop
- [ ] Have a **pre-canned JSON response** open in `docs/demo-fixture.json` as a fallback if the API misbehaves

---

## Segment 1 — Hook (0:00 – 0:30)

🎙 *"Coaches, broadcasters, and analysts spend **hours** preparing a single pre-match tactical brief. They pull stats from three different sites, write formation notes by hand, and most of it still ends up in a static PDF that nobody reads on match day. We're going to fix that in three minutes. PitchIQ turns two team names into a full pre-match tactical report — formations, key battles, expected game flow, coach recommendations, four comparative score bars — in under ten seconds."*

**On-screen:** the landing page hero fades into the match analysis form.

---

## Segment 2 — What PitchIQ is (0:30 – 1:00)

🎙 *"PitchIQ is a Gemini-powered football intelligence platform. It's three things: a specialized **analyst role** baked into the system prompt, a **grounding layer** against the FIFA World Cup 2026 dataset — teams, squads, groups, stadiums, fixtures, and qualifying playoff slots — and a **strict schema** with repair-aware retries so the model can never return malformed output. Everything you see is type-validated before it reaches the screen."*

**On-screen:** click into the **Match Analysis** tab. The form is already filled with **Argentina vs France**.

---

## Segment 3 — Architecture in 30 seconds (1:00 – 1:30)

🎙 *"Here's the pipeline. Browser hits FastAPI. FastAPI calls our **AnalysisService**, which pulls grounded context for the two teams from the bundled World Cup JSON, interpolates it into a versioned Markdown prompt, and sends it to **`gemini-2.5-flash`** via `google-genai`. The response is validated against an explicit Pydantic schema. If it fails, we automatically retry once with a repair prompt that includes the validation error. If it still fails, we fail closed with a 502 — we never return garbage to the dashboard."*

**On-screen:** switch to the architecture diagram in this README or the `/docs` FastAPI page. Highlight `app/services/analysis_service.py` and `app/schemas/analysis.py` in the codebase.

**If something fails here:** skip ahead to Segment 4 and let the demo carry the explanation.

---

## Segment 4 — Live demo (1:30 – 2:30)

**Action:** click **Analyze Matchup** with the pre-filled **Argentina vs France**.

🎙 *"Watch what happens. Form submit, network round-trip, model call, schema validation, render. … and there it is."*

**On-screen:** the dashboard populates with:

- **Match header** — predicted winner, confidence percentage, the four score bars (pressing, possession, attacking threat, defensive stability)
- **Formations** — home and away shape, plus a written matchup description
- **Key battles** — 3–5 individual or unit matchups with `home` / `away` / `even` edges
- **Tactical insights** — 3–6 cards tagged `critical`, `high`, or `medium`
- **Game flow** — opening / middle / closing phases
- **Coach recommendation** — concrete adjustments for both sides and a single decisive move

🎙 *"Notice every score is in a 0–100 range, every prediction names an actual team from the request, the key battles say who has the edge, and the coach recommendations are concrete — not vague 'play better football' platitudes. All of that is enforced by Pydantic, not by vibes."*

**Action:** scroll down to the coach recommendation block.

🎙 *"If the API ever flakes during a live demo, we have a fixture ready so the dashboard still renders something coherent. The schema is the contract — the source of truth can be the model or a fixture, the UI doesn't care."*

---

## Segment 5 — Engineering highlights (2:30 – 2:50)

🎙 *"Three things make this production-ready. **One** — the Gemini client is fully isolated behind an interface, so we can stub it in tests and validate the entire orchestration without a key. **Two** — CORS is allow-listed, secrets live in Secret Manager, and the frontend reads the backend origin at build time. **Three** — we have a smoke runner that exercises the full pipeline across four flagship matchups and asserts seventy-two invariants, plus a regression that confirms malformed payloads get rejected with `AnalysisGenerationError` after the repair attempt. The whole backend test suite is fifty tests, green, in under a second."*

**On-screen:** flash the terminal showing `pytest` output (50 passed) and `scripts/smoke_matchups.py` output (`OVERALL: PASS`).

---

## Segment 6 — Close (2:50 – 3:00)

🎙 *"PitchIQ: Football Intelligence, Reimagined — football intelligence for coaches, analysts, and broadcasters in ten seconds, not ten hours. The repo is open, the demo is live, and we're shipping. Thanks."*

**On-screen:** the dashboard fades back to the landing page hero. Hold a beat for applause.

---

## Q&A cheat sheet

| Question | One-line answer |
| --- | --- |
| **Why Gemini Flash and not Pro?** | Flash gives sub-second p50 latency at our score quality bar. The repair prompt handles the rare drift cases. |
| **How do you avoid hallucinated facts?** | The system prompt forbids live-knowledge claims, the knowledge layer injects verified teams/squads/groups, and personnel are described by role/unit when uncertain. |
| **What if Gemini returns malformed JSON?** | Pydantic rejects it, the service retries once with a repair prompt that includes the validation error, and the route returns a clean 502 if it still fails. The UI never sees garbage. |
| **Is the API rate-limited?** | Cloud Run scales horizontally; per-user rate limiting is on the post-hackathon roadmap. |
| **Can I run it without a Gemini key?** | Yes — `pytest` and `scripts/smoke_matchups.py` use a deterministic stub generator that returns schema-conforming JSON. The route itself returns 503 when the key is missing. |
| **Where do secrets live?** | `GEMINI_API_KEY` lives in Google Secret Manager and is injected into Cloud Run via `--set-secrets`. The `.env` file is gitignored. |
| **Why React on Firebase and FastAPI on Cloud Run?** | Independent deploy lifecycles, no serving of static assets from the API, edge-cached SPA bundles, scale-to-zero on the API. |
| **Can the model reference players by name?** | The knowledge layer injects verified squads, but personnel are described by **role and unit** (e.g. *"left-back in a back four"*) rather than by individual name unless that name is grounded in the bundled squad record. This keeps the output stable when rosters change. |
| **How fast is the pipeline?** | End-to-end, including a single repair-retry window: **p50 ≈ 6 s**, **p95 ≈ 12 s** on `gemini-2.5-flash`. The route times out at 15 s to keep the dashboard responsive. |
| **Will the demo break if the API rate-limits us?** | Cloud Run autoscales horizontally, and `scripts/smoke_matchups.py` doubles as a live health check — the route is fast-fail to 503 when the key is missing or quota is hit, so the UI shows a clean error instead of a hang. |

---

## Rehearsal plan

1. **Day 1:** read the script out loud, three times. Cut anything you stumble over.
2. **Day 2:** record yourself with a screen capture. Watch for filler words, dead air, and slides you didn't explain.
3. **Day 3:** do a live run with the API on. Time each segment. Aim for **2:50 ± 5 seconds**.
4. **Demo day:** always pre-load the form with the flagship matchup. Have the fixture file ready. Keep water nearby.

**Hard rules during the demo:**

- **No apologies for tech.** If something breaks, switch to the fixture and say "we have a fallback so the schema contract still holds." Move on.
- **No live coding.** Everything you show should be the running app or the running tests.
- **No more than three sentences per segment.** If you go over, cut a sentence — never extend.

---

Built with ⚽ for **Hack Days CUET 2026**.