# ADR 0002: Python 3.14, FastAPI and Temporal

- **Status:** Accepted
- **Date:** 2026-11-11

## Context

The engine is mostly database I/O and SQL transformation. Migrations run for hours
and must survive crashes and restarts.

## Decision

- **Python 3.14** (latest stable; 3.15 is in beta — move once drivers ship wheels).
- **FastAPI + Pydantic v2** for the API; Pydantic models double as the canonical schema.
- **Temporal** for orchestration: durable, resumable workflows with retries.
- **sqlglot** for dialect-aware SQL generation and transpilation.

## Consequences

- Rich driver ecosystem (psycopg 3, python-oracledb, mssql-python).
- Raw copy throughput is the main risk; mitigated by COPY/bulk APIs, Arrow batches,
  process-level parallelism, and a performance spike in S4.
- Workflow code must stay deterministic (enforced by keeping I/O in activities).
