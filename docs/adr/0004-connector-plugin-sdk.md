# ADR 0004: Connector SDK with capability flags and entry-point plugins

- **Status:** Accepted
- **Date:** 2026-11-11

## Context

Engines differ in what they support (CDC, writes, native checksums), and partners may
build their own connectors.

## Decision

- One `Connector` base class per engine with declared `Capabilities`; unsupported
  operations raise `UnsupportedFeatureError` with a clear message.
- Built-ins register via `@registry.register`; external packages expose a
  `driftless.connectors` entry point.
- The UI reads capabilities from `/api/v1/connectors` to decide what to offer.

## Consequences

- The engine never imports drivers directly; drivers are optional extras.
- A shared conformance test suite (S1+) must pass for every connector.
