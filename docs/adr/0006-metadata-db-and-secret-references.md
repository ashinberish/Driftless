# ADR 0006: Metadata database and secret references

- **Status:** Accepted
- **Date:** 2026-11-30 (Sprint 1)

## Context

The control plane must remember connections (and soon migrations, runs and audit
events). Enterprise customers will not accept a tool that stores database passwords.

## Decision

**Metadata DB**

- PostgreSQL via async SQLAlchemy 2; schema owned by Alembic migrations that ship
  inside the `driftless-api` package (`driftless-api-migrate`).
- The API never migrates on start-up (replicas would race). Migrations run as a Helm
  `pre-install/pre-upgrade` Job, a compose `migrate` service, or `make db-upgrade`.
- Persistence sits behind repository protocols; every adapter passes the same contract
  tests on SQLite and PostgreSQL, and CI fails if models and migrations drift
  (`alembic check`).
- Without `DRIFTLESS_DATABASE_URL` the API uses an in-memory store for local dev; in
  `production` it refuses to start.

**Secret references**

- A connection stores `scheme:path` (e.g. `vault:db/billing-ro#password`,
  `env:BILLING_PW`), never a password. Plain values are rejected by validation.
- `SecretResolverRegistry` maps schemes to resolvers. Built in: `env:` (dev/CI, can be
  disabled) and `vault:` (KV v2). New backends implement one `resolve()` method.
- Secrets are resolved only at connect time and held as `SecretStr` (never logged).
- Missing or unreadable secrets surface as a failed **Credentials** check, not a 500.

## Consequences

- Sprint 1 runs pre-flight checks and discovery from the API process. In S12 this moves
  to customer-network agents, so the control plane never needs network access to
  customer databases or their secrets; the service interface stays the same.
- Frontend types are generated from the OpenAPI document (`make api-types`), and a CI
  job fails when they are stale.
