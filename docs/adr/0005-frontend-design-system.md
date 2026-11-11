# ADR 0005: Shared design system package (`@driftless/ui`)

- **Status:** Accepted
- **Date:** 2026-11-11

## Context

The product has many dense enterprise screens. The approved v5 mockups define a clean
SaaS look: neutral surfaces, one accent, colour only for status, full-fill active states.

## Decision

- Tokens live in `packages/ui/src/styles/theme.css` (Tailwind v4 `@theme`).
- Reusable, router-agnostic components in `@driftless/ui` (links are injected via
  `renderLink`); variants via `class-variance-authority`.
- Apps import only from package entry points (lint-enforced).
- No gradients and no one-sided borders for active states.

## Consequences

- New screens are composed from existing components; visual drift is caught in review.
- The UI package has no data fetching or routing, so it is easy to test in isolation.
