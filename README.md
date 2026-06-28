# PitchIQ

> **Football Intelligence, Reimagined.**
> Built for **Hack Days CUET 2026** — a Gemini-powered tactical match analysis platform with grounded, structured, schema-validated AI output ready for production dashboards.

PitchIQ turns two team names into a full pre-match tactical report: formations, playing styles, strengths and weaknesses, key player battles, expected game flow, coaching recommendations, and four comparative tactical scores. The whole pipeline is deterministic at the orchestration layer and grounded against the FIFA World Cup 2026 dataset.

---

## Table of contents

1. [Highlights](#highlights)
2. [Demo](#demo)
3. [How it works](#how-it-works)
4. [Architecture](#architecture)
5. [Repository layout](#repository-layout)
6. [Technology](#technology)
7. [Prerequisites](#prerequisites)
8. [Local setup](#local-setup)
9. [Environment variables](#environment-variables)
10. [API reference](#api-reference)
11. [Deployment](#deployment)
12. [Testing & verification](#testing--verification)
13. [Roadmap](#completed)
14. [Future improvements](#future-improvements)

---

## Highlights

- **Specialized AI role.** The system prompt casts Gemini as a *UEFA Pro Licensed Tactical Analyst* producing pre-match technical reports for professional coaches and broadcasters. No generic chat behaviour leaks into the response.
- **Grounded against real World Cup data.** Every prompt is injected with verified knowledge from `backend/knowledge/` — teams, confederations, groups, squads, fixtures, stadiums — so the model is anchored to factual reference instead of free-form invention.
- **Schema-validated, repair-aware.** Responses must match an explicit Pydantic schema. On validation failure the service automatically retries once with a *repair prompt* that includes the previous error and the rejected payload, then fails closed with a 502 if the model still can't comply.
- **Independent deployable halves.** React frontend on Firebase Hosting, FastAPI backend on Google Cloud Run. No serving of static assets from FastAPI, no long-lived state in the API.
- **Production hardening included.** CORS allow-list, structured error responses, immutable cache headers for hashed bundles, SPA fallback via nginx, FastAPI health endpoint at `/health` (Cloud Run probe) plus an nginx-served `/healthz` for the frontend container, secrets via Secret Manager.
- **No live-knowledge claims.** The system prompt forbids inventing injuries, lineups, transfers, or live match facts. When personnel are uncertain the model describes the unit or role instead.

---

## Demo

The flagship demo is a single `POST /api/analyze` call for any of four flagship matchups:

| Matchup | Tactical angle |
| --- | --- |
| **Argentina vs France** | Possession positional play vs vertical transitions |
| **Brazil vs Germany** | Wide rotations vs compact mid-block pressing |
| **England vs Portugal** | Inverted fullbacks vs double-pivot counter-press |
| **Japan vs Morocco** | High-tempo circulation vs disciplined low block |

The frontend (`/match-analysis`) renders the response as a tactical dashboard. Each card is independently composed and accessible:

- Formation strip for both sides
- Key battles with zone and edge indicators
- Tactical insights ranked by importance
- Game-flow narrative across opening, middle, and closing phases
- Coach recommendations with a decisive adjustment
- Four comparative score bars
  - Pressing
  - Possession
  - Attacking threat
  - Defensive stability

> The full tactical dashboard renders inline on the `/analysis` route; no screenshots are required to follow the walkthrough.

---

## How it works

```text
Browser
  │
  │  POST /api/analyze  { homeTeam, awayTeam }
  ▼
FastAPI route (thin HTTP controller)
  │
  │  validates AnalysisRequest
  ▼
AnalysisService  ←────  KnowledgeService (cached JSON files)
  │                       ├─ teams
  │                       ├─ groups
  │                       ├─ squads
  │                       ├─ fixtures
  │                       └─ stadiums
  │
  │  builds grounded football context
  │  loads prompt template (system + user)
  ▼
GeminiService  ──►  google-genai  ──►  gemini-2.5-flash
  │                                          │
  │                       JSON response ◄────┘
  ▼
AnalysisResponse.model_validate_json
  │
  ├── pass  → return to browser
  └── fail  → retry with repair prompt (max 2 attempts)
               │
               ├── pass  → return to browser
               └── fail  → 502 invalid_analysis_response
```

### Prompt design

Three versioned Markdown templates under `backend/app/prompts/`:

- **`tactical_analysis_system.md`** — Casts Gemini as the Tactical Analyst role, defines the JSON-only output contract, and states the no-invention rule for live facts.
- **`tactical_analysis_user.md`** — Interpolates `$home_team`, `$away_team`, and `$football_context` (the grounded knowledge block) into a structured analysis brief.
- **`tactical_analysis_repair.md`** — Re-issues the brief on retry with `$validation_error` and `$invalid_response` appended so the model can self-correct.

### Response schema

Every Gemini call returns JSON validated against `app/schemas/analysis.py`. Top-level fields:

| Field | Type | Constraint |
| --- | --- | --- |
| `matchOverview` | string | 12–700 chars |
| `homeTeam` / `awayTeam` | object | name + formation + playingStyle + tacticalIdentity |
| `predictedWinner` | string | exact home name, exact away name, or `Draw` |
| `confidence` | int | 0–100 |
| `formations` | object | home / away / matchup description |
| `strengths` / `weaknesses` | object | 2–4 entries per side |
| `keyBattles` | array | 3–5 entries, each with zone + home/away unit + edge (`home`/`away`/`even`) + analysis |
| `tacticalInsights` | array | 3–6 entries with title + detail + importance (`critical`/`high`/`medium`) |
| `expectedGameFlow` | object | opening / middle / closing phases |
| `coachRecommendation` | object | home + away + decisiveAdjustment |
| `pressingScore` / `possessionScore` / `attackingThreat` / `defensiveStability` | object | home + away, each 0–100 |

The schema also enforces a post-validation invariant: `homeTeam.name` and `awayTeam.name` must match the request, and `predictedWinner` must be one of the two requested names or `Draw`. Mismatches trigger the repair path.

### Knowledge layer

`KnowledgeService` reads five JSON files once and caches the parsed result in-process:

| File | Contents |
| --- | --- |
| `worldcup.teams.json` | 48 teams with FIFA codes, confederations, groups |
| `worldcup.groups.json` | 12 groups of 4 teams |
| `worldcup.squads.json` | Registered squads per team |
| `worldcup.stadiums.json` | Host venues and capacities |
| `worldcup.teams.json` | 48 teams with FIFA codes, confederations, groups |
| `worldcup.groups.json` | 12 groups of 4 teams |
| `worldcup.squads.json` | Registered squads per team |
| `worldcup.stadiums.json` | Host venues and capacities |
| `worldcup.json` | Group-stage fixtures (group × round table) |
| `worldcup.quali_playoffs.json` | European / intercontinental qualifying playoff slots |

`FootballContextBuilder` queries only the two requested teams so prompts never leak unrelated information.

---

## Architecture

```text
┌─────────────────────────────────────────┐         ┌─────────────────────────────────────────┐
│  Firebase Hosting (frontend/dist)       │         │  Google Cloud Run (tactiq-api)           │
│  ─────────────────────────────────────  │         │  ─────────────────────────────────────  │
│  React 19 + Vite 6 + TypeScript 5.8     │  HTTPS  │  FastAPI 0.115 + Pydantic 2             │
│  TanStack Query 5  │  React Router 7    │ ──────► │  Uvicorn (PORT env, non-root user)      │
│  Tailwind v4       │  Strict TS         │  JSON   │  Service layer                          │
│                                         │ ◄────── │    ├─ AnalysisService                   │
│                                         │         │    ├─ KnowledgeService (cached JSON)    │
│                                         │         │    ├─ FootballContextBuilder            │
│                                         │         │    └─ GeminiService → gemini-2.5-flash  │
└─────────────────────────────────────────┘         └─────────────────────────────────────────┘
                  ▲                                              ▲
                  │ build-time                                   │ runtime
                  │ VITE_API_BASE_URL                            │ GEMINI_API_KEY (Secret Manager)
                  │                                              │ CORS_ORIGINS, APP_ENV=production
                  │                                              │ GEMINI_MODEL, GEMINI_TIMEOUT_SECONDS
```

**Why this split?** Independent deploy lifecycles, no serving of static assets from the API, origin-restricted CORS, and a clean service-layer boundary that keeps Gemini behind an interface (`JsonGenerationService`) so the model can be swapped or stubbed in tests.

---

## Repository layout

```text
tactiq-ai/                    ← repository folder (PitchIQ)
├── README.md                  ← you are here
├── AGENTS.md                  ← engineering guardrails
├── docker-compose.yml         ← local dev with healthcheck gating
├── firebase.json              ← SPA rewrite + cache headers
├── backend/
│   ├── Dockerfile             ← Python 3.12-slim, non-root, PORT env
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py            ← FastAPI app, CORS, exception handlers, startup log
│   │   ├── api/
│   │   ├── router.py      → /api mount
│   │   │   └── routes/
│   │   │       ├── analysis.py
│   │   │       └── health.py
│   │   ├── config/settings.py ← pydantic-settings, env-driven
│   │   ├── core/
│   │   │   ├── errors.py      ← AppError + Gemini/Analysis error subclasses
│   │   │   └── prompt_loader.py
│   │   ├── prompts/           ← versioned Markdown prompt templates
│   │   │   ├── tactical_analysis_system.md
│   │   │   ├── tactical_analysis_user.md
│   │   │   └── tactical_analysis_repair.md
│   │   ├── schemas/analysis.py
│   │   ├── services/
│   │   │   ├── analysis_service.py
│   │   │   ├── context_builder.py
│   │   │   ├── gemini_service.py
│   │   │   └── knowledge_service.py
│   │   └── knowledge/         ← bundled World Cup 2026 JSON
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_api.py
│   │   ├── test_analysis_service.py
│   │   ├── test_context_builder.py
│   │   └── test_knowledge_service.py
│   └── scripts/
│       └── smoke_matchups.py  ← Phase 3 demo-day smoke runner
└── frontend/
    ├── Dockerfile             ← multi-stage: development / build / nginx production
    ├── nginx.conf             ← SPA fallback + /healthz + asset caching
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── app/
        │   ├── App.tsx
        │   ├── router.tsx
        │   └── providers/AppProviders.tsx
        ├── layouts/AppLayout.tsx
        ├── pages/
        │   ├── HomePage.tsx
        │   └── NotFoundPage.tsx
        ├── features/match-analysis/
        │   ├── MatchAnalysisPage.tsx
        │   ├── components/
        │   │   ├── MatchAnalysisForm.tsx
        │   │   ├── MatchAnalysisResults.tsx
        │   │   ├── MatchHeader.tsx
        │   │   ├── ScoreBar.tsx
        │   │   ├── FormationsSection.tsx
        │   │   ├── FactorsList.tsx
        │   │   ├── KeyBattles.tsx
        │   │   ├── GameFlow.tsx
        │   │   ├── CoachRecommendation.tsx
        │   │   ├── AnalysisLoadingState.tsx
        │   │   ├── AnalysisErrorState.tsx
        │   │   └── TeamPanel.tsx
        │   └── hooks/
        ├── hooks/
        ├── services/analysisService.ts
        ├── types/analysis.ts
        ├── styles/index.css
        └── utils/
```

---

## Technology

| Layer | Stack |
| --- | --- |
| Frontend | React 19.1, Vite 6.3, TypeScript 5.8 (strict), TanStack Query 5.81, React Router 7, Tailwind CSS v4 |
| Backend | Python 3.12, FastAPI 0.115, Pydantic 2, pydantic-settings 2.10, Uvicorn 0.34 |
| AI | Google Gemini (`gemini-2.5-flash`) via `google-genai` 2.10, structured JSON output |
| Knowledge | Bundled FIFA World Cup 2026 JSON, parsed and cached in-process |
| Infrastructure | Docker, Docker Compose, Firebase Hosting, Google Cloud Run, Google Secret Manager |
| Testing | pytest 8, FastAPI `TestClient`, no network dependency |

---

## Prerequisites

- **Node.js** ≥ 22
- **Python** ≥ 3.12
- **Docker** with Docker Compose *(optional but recommended)*
- **Firebase CLI** and **Google Cloud CLI** *(only for deployment)*

---

## Local setup

### Option A — Docker Compose (recommended)

```bash
docker compose up --build
```

This starts both apps with hot-reload-friendly bind mounts. Open `http://localhost:5173`. The backend healthcheck gates the frontend so it never starts against a half-ready API.

### Option B — Manual

#### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev          # http://localhost:5173
```

#### Backend (manual)

```bash
cd backend
python -m venv .venv
# activate .venv using your shell
pip install -r requirements-dev.txt
cp .env.example .env
# leave GEMINI_API_KEY blank to fail-closed; tests use a stub generator
uvicorn app.main:app --reload --port 8000
```

Interactive docs available at `http://localhost:8000/docs` in non-production environments.

---

## Environment variables

### Frontend (`frontend/.env`)

| Variable | Purpose | Example |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Public backend origin, embedded in the browser bundle at build time | `http://localhost:8000` |

### Backend (`backend/.env`)

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_ENV` | Runtime mode (`development` enables `/docs`) | `development` |
| `CORS_ORIGINS` | Comma-separated allowed browser origins | `http://localhost:5173` |
| `PORT` | Container listening port (Cloud Run injects this) | `8080` |
| `GEMINI_API_KEY` | Gemini credential — empty disables the route, returns 503 | *empty* |
| `GEMINI_MODEL` | Gemini model identifier | `gemini-2.5-flash` |
| `GEMINI_TEMPERATURE` | Sampling temperature for analysis calls | `0.25` |
| `GEMINI_TIMEOUT_SECONDS` | Per-request HTTP timeout (5–300) | `45` |
| `GEMINI_MAX_VALIDATION_ATTEMPTS` | Retries before failing closed | `2` |

> Never commit `.env` files. Store the production Gemini key in **Google Secret Manager** and inject it as a Cloud Run secret rather than a plain env var.

---

## API reference

Base path: `/api` (analysis route is mounted at the `/api` prefix by `backend/app/api/router.py`; health lives at the root)

### `POST /analyze`

Request:

```json
{ "homeTeam": "Argentina", "awayTeam": "France" }
```

Success response (`200`):

```json
{
  "data": {
    "matchOverview": "...",
    "homeTeam": { "name": "Argentina", "formation": "4-3-3", "playingStyle": "...", "tacticalIdentity": "..." },
    "awayTeam": { "name": "France",    "formation": "4-2-3-1", "playingStyle": "...", "tacticalIdentity": "..." },
    "predictedWinner": "Argentina",
    "confidence": 67,
    "formations":   { "home": "4-3-3", "away": "4-2-3-1", "matchup": "..." },
    "strengths":    { "home": ["..."], "away": ["..."] },
    "weaknesses":   { "home": ["..."], "away": ["..."] },
    "keyBattles":   [ { "zone": "...", "homePlayerOrUnit": "...", "awayPlayerOrUnit": "...", "edge": "home", "analysis": "..." } ],
    "tacticalInsights": [ { "title": "...", "detail": "...", "importance": "critical" } ],
    "expectedGameFlow":   { "openingPhase": "...", "middlePhase": "...", "closingPhase": "..." },
    "coachRecommendation": { "home": "...", "away": "...", "decisiveAdjustment": "..." },
    "pressingScore":      { "home": 64, "away": 58 },
    "possessionScore":    { "home": 60, "away": 52 },
    "attackingThreat":    { "home": 66, "away": 55 },
    "defensiveStability": { "home": 58, "away": 61 }
  },
  "model": "gemini-2.5-flash"
}
```

Error responses (all follow `{ "error": { "code": "...", "message": "..." } }`):

| Status | `code` | Trigger |
| --- | --- | --- |
| 422 | `invalid_request` | Pydantic body validation failed (missing fields, identical team names) |
| 502 | `invalid_analysis_response` | Model failed validation on every attempt |
| 502 | `gemini_unavailable` | Provider returned an error or empty body |
| 503 | `gemini_not_configured` | `GEMINI_API_KEY` is empty |

### `GET /health`

Returns `{ "status": "healthy", "service": "tactiq-api" }`. This is the FastAPI health endpoint mounted at the root of `api_router`; it is what Cloud Run's container probe should target.

> The frontend nginx container also serves a lightweight `/healthz` route for its own platform probe — that endpoint is owned by the static site, not by the API.

---

## Deployment

### Backend — Google Cloud Run

```bash
gcloud run deploy tactiq-api \
  --source backend \
  --region YOUR_REGION \
  --allow-unauthenticated \
  --set-env-vars APP_ENV=production,CORS_ORIGINS=https://YOUR_PROJECT.web.app \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

`backend/Dockerfile` runs Uvicorn as a non-root user and reads `PORT` from the environment, so Cloud Run's injected port is honoured automatically.

### Frontend — Firebase Hosting

```bash
npm --prefix frontend run build
firebase use --add
firebase deploy --only hosting
```

Set `VITE_API_BASE_URL` to the deployed Cloud Run URL before building. `firebase.json` publishes `frontend/dist` and rewrites all client-side routes to `index.html` for SPA navigation. Hashed assets under `/assets/` are cached for one year with `immutable`.

### Secret management

- Create the Gemini key as a Secret Manager secret named `GEMINI_API_KEY`.
- Grant the Cloud Run service account `secretmanager.secretAccessor` on that secret.
- Reference it via `--set-secrets` (shown above) so it never appears in the container's env in plaintext.

---

## Testing & verification

#### Backend

```bash
cd backend
pytest                                  # 49 tests, ~0.3 s
python scripts/smoke_matchups.py        # 72 invariant checks across 4 flagship matchups
```

`scripts/smoke_matchups.py` exercises the full orchestration — service → context builder → prompt loader → Pydantic schema — using a deterministic stub generator. Invariants validated:

- Team name round-trip
  - `homeTeam.name` matches the request
  - `awayTeam.name` matches the request
- `predictedWinner ∈ {home, away, Draw}`
- All eight tactical scores are in `[0, 100]`
- Array length bounds
  - `keyBattles` length 3–5
  - `tacticalInsights` length 3–6
  - `strengths` length 2–4 per side
  - `weaknesses` length 2–4 per side
- A malformed Gemini payload is rejected with `AnalysisGenerationError` after exhausting retries

#### Frontend

```bash
cd frontend
npm run typecheck      # strict TypeScript
npm run build          # Vite production build
```

### End-to-end readiness checklist

- [x] `pytest` green (49/49)
- [x] `npm run typecheck` clean
- [x] `npm run build` clean
- [x] `scripts/smoke_matchups.py` PASS for all 4 matchups + rejection regression
- [x] `firebase.json` SPA rewrite + cache headers verified
- [x] Backend `Dockerfile` honours `PORT` env, non-root user
- [x] Frontend multi-stage `Dockerfile` injects `VITE_API_BASE_URL` at build time
- [x] `nginx.conf` SPA fallback + `/healthz` for the frontend container's probe
- [x] CORS restricted to `GET`, `POST`, `OPTIONS`
- [x] Secrets kept out of the repo, deferred to Secret Manager

---

### Completed

- Project setup
- Frontend application
- Backend API
- Gemini integration
- AI Tactical Match Analysis (live)
- Deployment
  - Docker
  - Cloud Run
  - Firebase Hosting
- Documentation
  - `README.md`
  - `AGENTS.md`
  - `DEMO_SCRIPT.md`

### In progress

- UI polish
  - Demo screenshots
  - Loading state refinement
- Production optimization
  - Response caching
  - Telemetry
  - Observability

---

Built for **Hack Days CUET 2026**.
