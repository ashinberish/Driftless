# ADR 0001: Monorepo with separate Python and TypeScript workspaces

- **Status:** Accepted
- **Date:** 2026-11-11

## Context

Driftless has a Python backend (API, worker, CLI sharing engine code) and a React
frontend with a shared component library. Changes often span both (e.g. a new API
field and the screen that shows it).

## Decision

One repository with two workspaces:

- `backend/` — a **uv workspace**: `apps/` (deployables) and `libs/` (shared packages).
- `frontend/` — a **pnpm workspace**: `apps/` (web) and `packages/` (ui, api-client).
- `deploy/` — Docker, Compose and Helm; `docs/` — architecture and ADRs.

## Consequences

- Atomic cross-stack changes and one CI pipeline.
- Each language keeps its native tooling; no polyglot build system to learn.
- Libraries are versioned together; extracting one later means publishing it.
