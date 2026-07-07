---
name: pitchiq
description: Build and maintain the PitchIQ football intelligence monorepo (Football Intelligence, Reimagined.). Use when implementing or reviewing its React frontend, FastAPI REST API, structured Gemini prompts and schemas, Firebase Hosting deployment, Cloud Run deployment, or repository conventions.
---

# Work on PitchIQ

PitchIQ is a single-purpose, production-ready monorepo: a React frontend and a FastAPI backend that turns two FIFA World Cup 2026 team names into a structured tactical brief. Before touching anything, internalize the architecture in `AGENTS.md` and treat the rules in this file as the order of operations for any change.

## Deployment boundary (always)

- `frontend/` deploys to Firebase Hosting (`firebase deploy --only hosting`, source `frontend/dist/`).
- `backend/` deploys to Google Cloud Run (`gcloud run deploy`, image from `backend/Dockerfile`, `--port 8080`).
- The frontend reads the REST origin from `VITE_API_BASE_URL` (build-time, baked into the bundle).
- Backend CORS origins live in `CORS_ORIGINS` (comma-separated); always list the exact Firebase domain.
- Never serve React from FastAPI; never bundle a server secret into a `VITE_` variable.
- Immutable cache headers (`public, max-age=31536000, immutable`) live in `frontend/nginx.conf` for the Docker image. Firebase Hosting ignores nginx headers; configure caching in `firebase.json` if you switch hosts.

## The 10-step workflow

Run these steps for every change. Skip none.

1. **Read the constitution.** Skim `AGENTS.md` (mission, folder conventions, env vars, testing) before opening a file. If `AGENTS.md` and source disagree, the source wins; update `AGENTS.md` in the same PR.
2. **Define the change in one sentence.** Example: "Add a 5th strength/weakness slot." If the sentence needs "and", split the change into multiple PRs.
3. **Identify the layer order.** Schemas -> prompts -> services -> routes -> frontend types -> frontend components -> docs. Never edit a layer out of order; the tests will fail downstream.
4. **Update Pydantic schemas first.** Edit `backend/app/schemas/analysis.py` (CamelModel, `extra="forbid"`, `str_strip_whitespace`). Mirror the change in `frontend/src/types/analysis.ts`. Run `npm run typecheck` before continuing.
5. **Update prompts only when reasoning changes.** `backend/app/prompts/tactical_analysis_*.md` use `$variable` placeholders that `PromptLoader` substitutes. If the new field needs different instructions, change `tactical_analysis_system.md` or `tactical_analysis_user.md`; never edit `tactical_analysis_repair.md` unless the JSON shape changes.
6. **Update services and tests together.** `analysis_service.py` orchestrates validation and retry; `gemini_service.py` owns the provider; `context_builder.py` slices the knowledge bundle. Add or update tests in `backend/tests/` next to the change. Stub `JsonGenerationService`; never call the live API from a test.
7. **Update routes only for HTTP concerns.** `app/api/routes/analysis.py` maps requests, returns `AnalysisApiResponse`, and maps `AppError` subclasses to status codes. Do not push Gemini calls into the route.
8. **Update frontend types and components together.** Change `frontend/src/types/analysis.ts` first, then feature-local components under `frontend/src/features/match-analysis/components/`. Co-locate new hooks under the feature. Avoid `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/utils/`, `frontend/src/assets/` for an MVP.
9. **Verify locally before handoff.** `docker compose up` boots both services (backend healthcheck gates the frontend). Run `pytest` in `backend/` and `npm run typecheck && npm run build` in `frontend/`. The test count for the README comes from `pytest --collect-only -q`; never write a number you did not just measure.
10. **Verify deployment readiness.** Backend image: non-root user, `$PORT` honored, healthcheck `GET /health` returns `200`. Frontend image: `/healthz` returns `200 healthy`, SPA rewrites to `/index.html`, hashed assets cached immutable. Secrets: `GEMINI_API_KEY` in Secret Manager (Cloud Run) or `.env` (local), never in `firebase.json` or `VITE_` variables.

## Deployment verification (always required)

After deploying backend or frontend changes to production, run the verification checklist in [README.md → Post-Deployment Verification](README.md#post-deployment-verification) **within 5 minutes** of deployment. Critical checks:

- ✓ `CORS_ORIGINS` includes the correct Firebase domain (`https://pitchiq-ai.web.app` for production)
- ✓ `VITE_API_BASE_URL` in the frontend bundle points to the correct Cloud Run URL
- ✓ `GEMINI_API_KEY` is set in Secret Manager and accessible by the Cloud Run service account
- ✓ `/health` endpoint returns `200 healthy`
- ✓ OPTIONS preflight request to `/api/analyze` returns `200` with correct CORS headers
- ✓ One complete analysis request from `https://pitchiq-ai.web.app` completes within 30 seconds
- ✓ No CORS errors in the browser console
- ✓ All tactical cards populate with valid data

Never consider a deployment complete until all verification checks pass.

## Gemini-specific rules

- One specialized football role per use case lives in `tactical_analysis_system.md`. Do not collapse two roles into one prompt.
- Always request `response_mime_type="application/json"` AND `response_json_schema=...` from the Gemini client; never accept prose when a schema is available.
- Treat model output as untrusted input. Parse with `AnalysisResponse.model_validate_json`; on failure send the repair prompt with `$validation_error` and `$invalid_response` interpolated. Bound retries with `GEMINI_MAX_VALIDATION_ATTEMPTS` (default 2).
- Fail closed: `GeminiConfigurationError` -> 503, `GeminiProviderError` -> 502, `AnalysisGenerationError` -> 502, `RequestValidationError` -> 422. Never echo the prompt or the raw model output to the caller.
- Never claim live football knowledge. The bundled `backend/app/knowledge/*.json` is the only authoritative source for team rosters, squads, groups, stadiums, and fixtures.

## Frontend rules

- Server state lives in TanStack Query (`useMatchAnalysis`). Local UI state uses `useState`/`useReducer`.
- The visual brief renders one feature; do not add a chat box, history list, or settings screen without approval.
- Every server interaction must show loading, empty, success, and error states. Components live under `frontend/src/features/match-analysis/components/`.
- Match the dark, premium football-analysis aesthetic; respect `prefers-reduced-motion`; ensure keyboard focus is visible at every breakpoint.

## Commit and PR rules

- Conventional Commits only (`feat(frontend): ...`, `feat(api): ...`, `fix(api): ...`, `docs: ...`, `chore: ...`).
- One change per commit. Refactors that are not required by the change belong in their own commit.
- Update `README.md`, `PROJECT_OVERVIEW.md`, and `DEMO_SCRIPT.md` whenever behavior, count, route, or timeout changes.
- Update `AGENTS.md` whenever folder layout, env vars, or deployment assumptions change.

