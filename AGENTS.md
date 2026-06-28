# PitchIQ Repository Guide

## Mission

Build a memorable, production-minded football intelligence MVP for Hack Days CUET 2026. Optimize decisions for a solo developer and a 24-hour build window. Prefer clear, reversible solutions over speculative abstractions.

## Repository rules

- Keep `frontend/` and `backend/` independently deployable.
- Never serve frontend assets from FastAPI.
- Keep API origins and secrets in environment variables.
- Never commit `.env`, credentials, generated builds, or dependency folders.
- Do not add authentication, databases, queues, or new endpoints without explicit approval.
- Finish and verify the current milestone before beginning the next.

## Architecture

```text
React feature/page -> typed service -> REST endpoint
FastAPI route -> service -> Gemini client -> prompt -> validated schema
```

Routes handle HTTP concerns only. Services own use-case orchestration. The future Gemini client owns provider calls; prompt modules own prompt text; Pydantic schemas validate every model response.

## Folder conventions

- `frontend/src/pages`: route-level screens
- `frontend/src/layouts`: shared page shells
- `frontend/src/components`: reusable cross-feature UI
- `frontend/src/features`: feature-owned components, hooks, and types
- `frontend/src/hooks`: shared React hooks
- `frontend/src/services`: external and REST clients
- `frontend/src/types`: shared TypeScript contracts
- `frontend/src/utils`: pure utilities
- `backend/app/api/routes`: thin HTTP controllers
- `backend/app/services`: use-case orchestration
- `backend/app/prompts`: versioned prompt builders
- `backend/app/schemas`: request and response contracts
- `backend/app/models`: internal domain models, not database models
- `backend/app/config`: environment settings
- `backend/app/core`: cross-cutting infrastructure
- `backend/app/utils`: pure helpers

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

- Do not call Gemini from route modules.
- Give each use case a specialized football role and a dedicated prompt template.
- Require JSON matching an explicit schema; validate it before returning it.
- Treat model output as untrusted input and fail with safe, useful errors.
- Keep temperature and model configuration explicit and testable.
- Do not claim live football knowledge unless a verified data source is introduced.
- Never log API keys, full secrets, or sensitive request headers.

## Testing expectations

- Run `npm run typecheck` and `npm run build` for frontend changes.
- Run `pytest` for backend changes.
- Add unit tests for parsing, validation, and prompt construction.
- Add route tests for success and expected failure contracts.
- Manually verify responsive behavior and keyboard navigation for UI changes.

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

