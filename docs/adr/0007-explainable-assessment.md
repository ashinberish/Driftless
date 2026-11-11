# ADR 0007: Explainable, rule-based assessment

- **Status:** Accepted
- **Date:** 2026-12-14 (Sprint 2)

## Context

The Check screen is where users decide whether a migration is worth starting. They
(and their change boards) must be able to see *why* a database scored the way it did.

## Decision

- Assessment = a list of small, independent rules over the canonical catalog. Each
  rule returns findings with a plain-language title, detail, recommendation, affected
  objects and how many columns need a human (`affected_columns`).
- Rules receive an `AssessContext` with the source and target connector classes, so
  cross-engine rules use the real type mappers and capability flags rather than
  hard-coded engine pairs. Example: `lossy_type_conversions` round-trips every column
  through the target mapper and reports what changes.
- Scoring is additive and documented in `scoring.py`: size and table count add a
  bounded amount, findings dominate, and any blocking finding raises the level to at
  least "moderate". Readiness = share of columns that need no review.
- Each run is stored (JSON) with the migration, so results are auditable and comparable
  over time; a Markdown report is generated from the stored result.

## Consequences

- Adding a check is one function plus tests — no UI change needed.
- Weights are a first guess; calibrate them against real migrations from design
  partners and record changes here.
- Assessment runs synchronously in the API for now (seconds). It moves into the
  Temporal workflow with the copy pipeline (S4) without changing the API contract.
