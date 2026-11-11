# Architecture

## System view

```
                 ┌────────────── Web (React) ──────────────┐
                 │  @driftless/web → @driftless/ui, api-client
                 └───────────────────┬──────────────────────┘
                                     │ REST /api/v1
┌────────────────────────── Control plane ───────────────────────────┐
│  driftless-api (FastAPI)       driftless-worker (Temporal)          │
│   modules/<feature>             workflows/  (deterministic)         │
│     router → service → repo     activities/ (side effects)          │
│                  │                     │                            │
│                  └──── driftless-engine (assess · convert · copy · validate)
│                               │                                     │
│                  driftless-connectors (SDK + engines)               │
│                               │                                     │
│                  driftless-core (canonical schema, values, errors)  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ drivers (inside the customer network)
                     source DB ◄─┴─► target DB
```

## Dependency rules

Dependencies point **down only**; CI and code review enforce it.

| Layer | May import | Must not import |
|---|---|---|
| `apps/*` (api, worker, cli) | engine, connectors, core | other apps |
| `libs/engine` | connectors, core | apps, web frameworks, Temporal |
| `libs/connectors` | core, drivers | engine, apps |
| `libs/core` | pydantic, stdlib | everything else in the repo |
| `@driftless/web` | `@driftless/ui`, `@driftless/api-client` (entry points only) | package internals (`*/src/*`) |
| `@driftless/ui` | React, Tailwind, lucide | router, data fetching, app code |

## The canonical model (hub, not pairs)

Every connector maps native types **to and from** `driftless_core.schema.DataType`.
Converting MySQL → PostgreSQL is `MySQLTypeMapper.to_canonical` followed by
`PostgresTypeMapper.to_native`. Adding an engine costs one mapper instead of one per
engine pair.

Validation uses the same idea: values are rendered in a versioned canonical text form
(`driftless_core.values`) before hashing, so rows read from different engines produce
identical digests.

## Backend module anatomy (API)

```
modules/connections/
  schemas.py      # request/response contracts (what the frontend sees)
  repository.py   # persistence port (Protocol) + in-memory adapter
  service.py      # business rules — no FastAPI imports, unit-testable
  router.py       # HTTP mapping only
```

Cross-cutting HTTP concerns (error mapping, request IDs) live in `platform/`.

## Frontend anatomy

```
apps/web/src/
  app/            # providers, router, layout, navigation config
  features/<x>/   # pages, feature components, data hooks, model
  shared/         # app-wide helpers (api client instance, generic pages)
packages/ui/      # design tokens + reusable components (no business logic)
packages/api-client/  # typed HTTP client (generated from OpenAPI in S1)
```

Status → label/colour mapping lives in one place per domain (e.g.
`features/migrations/model.ts`) so every screen renders statuses identically.
