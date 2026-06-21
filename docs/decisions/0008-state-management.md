# ADR 0008 - Avoid Pinia In The First Application-Flow Implementation

Status: Accepted

## Context

The application requires shared vacancy ownership, a multi-step form, upload metadata, and review
state. A state library may be useful later, but adding one before the current ownership model proves
insufficient would add unnecessary indirection.

## Decision

Use route state for step navigation, local component state for local interaction, composables for
shared flow behavior, and typed services for external boundaries. The Phase 1 implementation keeps
its simulated draft in memory and uses fixture services. The future server draft will become
authoritative. Do not install Pinia by default.

Pinia may be reconsidered if state becomes shared across unrelated route trees or if testing becomes clearer with a central store.

## Consequences

- The first version keeps the state model small.
- Draft serialization is handled by explicit form services and composables.
- SSR and hydration boundaries stay easier to reason about.
- Some prop or composable wiring may be more verbose than a store.

## Current Status

Phase 1 uses route state, component state, focused composables, typed fixture services, and one
in-memory application draft. The current implementation does not demonstrate a need for Pinia.

## Alternatives Considered

- Pinia from the start: rejected because the first version does not yet prove the need.
- Only component state: too narrow for route transitions and draft restoration.
- localStorage-backed state: rejected for sensitive candidate data.

## Follow-Up Work

- Review state complexity when server-backed drafts are integrated.
- Add a superseding ADR if Pinia becomes justified.
