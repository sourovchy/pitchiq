---
name: pitchiq
description: Build and maintain the PitchIQ football intelligence monorepo (Football Intelligence, Reimagined.). Use when implementing or reviewing its React frontend, FastAPI REST API, structured Gemini prompts and schemas, Firebase Hosting deployment, Cloud Run deployment, or repository conventions.
---

# Work on PitchIQ

## Preserve the deployment boundary

- Deploy `frontend/` to Firebase Hosting.
- Deploy `backend/` to Google Cloud Run.
- Read the REST origin from `VITE_API_BASE_URL`.
- Configure exact browser origins through backend `CORS_ORIGINS`.
- Never serve React from FastAPI.

## Follow the implementation path

1. Read `AGENTS.md` and the active milestone before editing.
2. Keep API routes thin: route -> service -> Gemini client -> prompt -> validated schema.
3. Keep frontend server state in TanStack Query and calls in typed service modules.
4. Add only dependencies required by the active milestone.
5. Update `.env.example` and `README.md` when configuration changes.
6. Verify frontend type-check/build and backend tests before handoff.

## Engineer Gemini features

- Define one specialized football role per use case.
- Require schema-constrained JSON instead of prose.
- Validate all model output with Pydantic before returning it.
- Separate prompt construction from provider calls and HTTP handling.
- Bound retries, timeouts, and repair attempts.
- Return safe errors without leaking prompts, keys, or internal output.

## Design API schemas

- Use explicit request and response models.
- Prefer stable enums and named nested objects over free-form dictionaries.
- Represent confidence consistently and document its range.
- Version contracts deliberately when breaking changes become necessary.
- Keep TypeScript response types aligned with Pydantic schemas.

## Build the interface

- Produce a dark, premium football-analysis aesthetic rather than a chat UI.
- Use semantic HTML, visible focus states, and accessible contrast.
- Include loading, empty, success, and error states for every server interaction.
- Keep animation subtle and honor reduced-motion preferences.
- Verify mobile, tablet, and desktop layouts.

## Use FastAPI patterns

- Place HTTP concerns in `app/api/routes`.
- Place orchestration in `app/services`.
- Place settings in `app/config` and read them from environment variables.
- Place prompt builders in `app/prompts` and contracts in `app/schemas`.
- Keep provider-specific code behind a client in `app/core`.

## Use React patterns

- Place route screens in `src/pages` and shells in `src/layouts`.
- Keep feature-specific components, hooks, and types under `src/features/<feature>`.
- Move code to shared folders only after multiple features use it.
- Avoid duplicated request state and effect-driven data fetching.

## Check deployment readiness

- Build the frontend with the production Cloud Run URL.
- Restrict backend CORS to Firebase production and preview domains in use.
- Listen on Cloud Run's `PORT` and keep containers stateless.
- Store Gemini credentials in Google Secret Manager.
- Confirm `/health`, SPA rewrites, cache headers, and cold-start behavior.
- Never embed server secrets in `VITE_` variables.

