# Driftless

Database migrations with zero drift.

Driftless moves databases between engines and hosts — assess, convert, copy, keep in
sync, verify and cut over — with minimal downtime and a full audit trail.

## Repository layout

```
driftless/
├── backend/                     uv workspace (Python 3.14)
│   ├── apps/
│   │   ├── api/                 FastAPI control plane — modules/<feature>/{router,service,repository,schemas}
│   │   ├── worker/              Temporal worker — workflows/ (deterministic) + activities/
│   │   └── cli/                 `dbm` CLI — offline assess / DDL on catalog snapshots
│   └── libs/
│       ├── core/                canonical schema + types, value normalization, ids, config, errors
│       ├── connectors/          connector SDK, plugin registry, postgres/, mysql/
│       └── engine/              assess/, convert/, copy/, validate/
├── frontend/                    pnpm workspace (React 19, Vite, Tailwind v4)
│   ├── apps/web/                app/ (shell, router, nav) + features/<feature>/
│   └── packages/
│       ├── ui/                  design tokens + reusable components
│       └── api-client/          typed API client
├── deploy/                      docker-compose (local), Dockerfiles, Helm chart
├── docs/                        architecture, ADRs, execution plan
└── .github/                     CI, PR template, CODEOWNERS, Dependabot
```

See [docs/architecture.md](docs/architecture.md) for the layering rules.

## Quick start

```bash
make setup       # install dependencies
make infra-up    # Postgres, MySQL, Temporal (docker compose)
make api         # API at http://localhost:8000/api/v1/docs
make web         # web app at http://localhost:5173
make ci          # lint, type-check, test, build
```

Try the engine without any database:

```bash
cd backend
uv run dbm connectors
uv run dbm assess --catalog examples/catalog.sample.json --target postgres
uv run dbm ddl --catalog examples/catalog.sample.json --target postgres --schema billing
```

## Status

Sprint 0 foundation. See [docs/execution-plan.md](docs/execution-plan.md) for what
lands when, and [CONTRIBUTING.md](CONTRIBUTING.md) for where new code goes.
