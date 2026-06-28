# PitchIQ Repository Guide

## Mission

Build a memorable, production-minded football intelligence MVP for Hack Days CUET 2026. Optimize decisions for a solo developer and a 24-hour build window. Prefer clear, reversible solutions over speculative abstractions.

PitchIQ turns two FIFA World Cup 2026 team names into a structured, schema-validated tactical brief. The MVP is single-purpose; do not add new modules, screens, or AI capabilities without explicit approval.

## Repository rules

- Keep `frontend/` and `backend/` independently deployable.
- Never serve frontend assets from FastAPI.
- Keep API origins, CORS origins, and secrets in environment variables. Never commit `.env`, credentials, generated builds, or dependency folders.
- Do not add authentication, databases, queues, or new endpoints without explicit approval.
- Finish and verify the current milestone before beginning the next.
- All product copy is English. Keep tone analytical and concise; avoid marketing superlatives in source code.

## Architecture

```text
React feature/page -> typed service -> REST endpoint
FastAPI route -> service -> Gemini client -> prompt -> validated schema
```

Routes handle HTTP concerns only. Services own use-case orchestration. The Gemini client owns provider calls. Prompt modules own prompt text. Pydantic schemas validate every model response.

Frontend and backend each have one focused job: the page renders one feature, the API exposes one feature.

## Folder conventions (matches the tree today)

```text
backend/app/
  api/                FastAPI routers and thin route handlers only
    router.py         Aggregates the analysis and health routers
    routes/
      analysis.py     POST /api/analyze
      health.py       GET /health
  config/settings.py  Pydantic settings, env-driven
  core/
    errors.py         AppError hierarchy + status codes
    prompt_loader.py  Reads markdown prompts from app/prompts/
  prompts/
    tactical_analysis_system.md   role + reasoning protocol
    tactical_analysis_user.md     per-match procedure
    tactical_analysis_repair.md   re-emit with correct schema
  schemas/
    analysis.py       CamelModel request/response contracts
    common.py         HealthResponse + ErrorResponse envelope
  services/
    analysis_service.py     orchestrator + validation + retry
    context_builder.py      builds grounded WC 2026 context
    gemini_service.py       google-genai async client wrapper
    knowledge_service.py    frozen dataclass records + JSON load
  knowledge/          bundled FIFA World Cup 2026 JSON fixtures

frontend/src/
  app/
    App.tsx           router shell
    router.tsx        createBrowserRouter routes
    providers/        TanStack Query and other React providers
  features/match-analysis/      one feature, one folder
    MatchAnalysisPage.tsx
    hooks/useMatchAnalysis.ts
    components/       Feature-local UI (12 files today)
  layouts/AppLayout.tsx         shared shell with sticky header
  pages/              route-level screens (HomePage, NotFoundPage)
  services/
    analysisService.ts  fetch wrapper + AnalysisApiError
  types/analysis.ts    mirrors backend schema in TypeScript
  styles/index.css     Tailwind v4 + theme tokens
```

Do not create `app/models/`, `app/utils/`, `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/utils/`, or `frontend/src/assets/` for this MVP. Domain records are frozen dataclasses inside `services/knowledge_service.py`. Shared utilities go inside the feature folder until something is actually shared.

Prefer feature-local code until it is genuinely shared. Avoid index/barrel files that conceal ownership or create import cycles.

## Coding standards

- Use strict TypeScript; do not use `any` to bypass design work.
- Type all Python functions and public module boundaries.
- Keep components focused and accessible; include loading, empty, and error states.
- Use TanStack Query for server state and ordinary React state for local UI state.
- Use semantic HTML, keyboard-safe interactions, visible focus, and sufficient contrast.
- Keep functions small, names explicit, and constants centralized.
- Return structured JSON from AI-backed endpoints.

## API and prompt engineering

- Routes never call Gemini directly. The analysis route calls `AnalysisService.analyze`, which delegates to `GeminiJsonGenerator.generate_json`.
- Each use case has a specialized football role (the system prompt) and a dedicated user prompt template.
- Every Gemini response is parsed with `AnalysisResponse.model_validate_json`; on failure, the repair prompt is sent with `$validation_error` and `$invalid_response` interpolated.
- Treat model output as untrusted input. Fail with safe, useful errors: `AnalysisGenerationError` -> 502, `GeminiProviderError` -> 502, `GeminiConfigurationError` -> 503, `RequestValidationError` -> 422.
- Temperature and model configuration are explicit: `Settings.gemini_temperature=0.25`, `gemini_model="gemini-2.5-flash"`, `gemini_max_validation_attempts=2`, `gemini_timeout_seconds=45`.
- Do not claim live football knowledge unless a verified data source is introduced. The bundled `app/knowledge/` JSON is the only authoritative source.
- Never log API keys, full secrets, or sensitive request headers.
- Prompt files are markdown with `$variable` placeholders; `PromptLoader.load` substitutes them with `string.Template`.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_API_KEY` | empty | Required in production. Empty triggers 503 `gemini_not_configured`. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model name echoed in the API response. |
| `GEMINI_TEMPERATURE` | `0.25` | Must satisfy `0 <= value <= 1`. |
| `GEMINI_MAX_VALIDATION_ATTEMPTS` | `2` | Must satisfy `1 <= value <= 3`. |
| `GEMINI_TIMEOUT_SECONDS` | `45` | Must satisfy `5 <= value <= 300`. |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated origins. |
| `PORT` | `8080` | Container port. Cloud Run sets this. |
| `APP_ENV` | `development` | Disables docs/redoc when `production`. |
| `APP_NAME` | `PitchIQ API` | Logged on startup. |
| `VITE_API_BASE_URL` | (frontend) | Build-time API origin. Empty string falls back to `/api/analyze`. |

## Deployment

- Backend: single-stage Python 3.12-slim, non-root user, `uvicorn app.main:app --host 0.0.0.0 --port ${PORT}`. Deploy to Cloud Run with `--port 8080`; eager knowledge init is handled by the FastAPI startup hook.
- Frontend Docker: three-stage (development -> build -> production nginx 1.27-alpine). Immutable `Cache-Control: public, max-age=31536000, immutable` for `/assets/`, SPA fallback to `/index.html`, `/healthz` returns `200 healthy`. The immutable cache headers live in `frontend/nginx.conf`, not `firebase.json`; Firebase Hosting is the static-file CDN and does not honor those nginx headers.
- Local: `docker compose up` boots both services; backend healthcheck gates the frontend dependency.

## Testing expectations

- Run `npm run typecheck` and `npm run build` before merging frontend changes.
- Run `pytest` for backend changes. Test files live in `backend/tests/`; `backend/scripts/smoke_matchups.py` is a manual smoke script, not a pytest module.
- Add unit tests for parsing, validation, and prompt construction.
- Add route tests for success and the expected failure contracts (422, 502, 503).
- Manually verify responsive behavior and keyboard navigation for UI changes.
- Tests must not call the live Gemini API; stub the `JsonGenerationService` interface.
- The single source of truth for the test count is the count of test functions in `backend/tests/`; do not document a number elsewhere.

## Commit conventions

Use focused commits following Conventional Commits:

- `feat(frontend): add tactical analysis form`
- `feat(api): add structured analysis service`
- `fix(api): reject malformed Gemini output`
- `docs: document Cloud Run deployment`
- `chore: update development tooling`

Do not mix unrelated refactors with feature work.

## Definition of done

A change is done when its contracts are typed, errors are handled, relevant tests pass, documentation and environment examples are current, secrets remain external, and deployment assumptions still hold.

```

```

