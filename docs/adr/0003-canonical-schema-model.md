# ADR 0003: Canonical schema and value model for cross-engine migrations

- **Status:** Accepted
- **Date:** 2026-11-11

## Context

Pairwise conversion rules grow as N×(N−1). Validating data across engines also fails
if each engine hashes its own text rendering of values.

## Decision

- All connectors map native types to/from `driftless_core.schema.DataType` (hub model).
- Validation hashes values rendered in a **versioned canonical text form**
  (`driftless_core.values`, `NORMALIZATION_VERSION`), combined order-independently.
- Engine quirks are explicit options (e.g. `empty_string_as_null` for Oracle).

## Consequences

- Each new engine needs one type mapper and one set of normalization tests.
- Changing the canonical value form requires a version bump; stored evidence records
  the version it was produced with.
