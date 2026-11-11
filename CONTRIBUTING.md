# Contributing

## Setup

Requirements: [uv](https://docs.astral.sh/uv/), Node 22 + pnpm, Docker.

```bash
make setup      # backend + frontend dependencies, git hooks
make dev        # infra in Docker + api/worker/web with hot reload → http://localhost:5173
# or run pieces yourself:
make infra-up   # Postgres, MySQL, Temporal
make db-upgrade # apply metadata-DB migrations
make api        # http://localhost:8000/api/v1/docs
make web        # http://localhost:5173
```

## Workflow

- Branch from `main` (`feature/<short-name>`), open a draft PR early.
- `make ci` must pass locally before requesting review.
- Architecture changes need an ADR in `docs/adr/` (copy the latest one).
- Changed an ORM model? `make db-revision m="describe change"`, review the generated
  migration, commit it. CI runs `alembic check` to catch forgotten migrations.
- Changed an API schema? `make api-types` and commit `frontend/packages/api-client`.
- `make test-integration` runs tests against a real PostgreSQL (`TEST_PG_URL=...`).

## Where code goes

| You are adding… | Put it in |
|---|---|
| A new database engine | `backend/libs/connectors/src/driftless_connectors/<engine>/` |
| An assessment rule | `backend/libs/engine/src/driftless_engine/assess/rules.py` |
| An API endpoint | `backend/apps/api/src/driftless_api/modules/<feature>/` |
| A long-running step | activity in `backend/apps/worker/.../activities/`, called from a workflow |
| A reusable UI element | `frontend/packages/ui/src/components/` (export it from `index.ts`) |
| A screen | `frontend/apps/web/src/features/<feature>/` + a route in `app/router.tsx` |

## Standards

- Python: ruff (lint + format), pyright strict for production code, pytest.
- TypeScript: strict mode, ESLint, Vitest + Testing Library.
- Every data-integrity change (normalization, checksums, copy) needs tests that cover
  more than one engine.
- Never log credentials or row data. Connections store secret **references** only.
