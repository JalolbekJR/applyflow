# ADR 0008 - Avoid Pinia In The First Application-Flow Implementation

Status: Accepted

## Context

The planned frontend has a vacancy flow, multi-step form, upload state, and review step. A state library may be useful later, but adding one too early can make the code harder to study.

## Decision

Use route state for step navigation, local component state for local interaction, composables for shared flow behavior, and typed API services for server communication. Server draft state remains authoritative. Do not install Pinia during Phase 0 or by default in the first application-flow implementation.

Pinia may be reconsidered if state becomes shared across unrelated route trees or if testing becomes clearer with a central store.

## Consequences

- The first version keeps the state model small.
- Draft serialization is handled by explicit form services and composables.
- SSR and hydration boundaries stay easier to reason about.
- Some prop or composable wiring may be more verbose than a store.

## Alternatives Considered

- Pinia from the start: rejected because the first version does not yet prove the need.
- Only component state: too narrow for route transitions and draft restoration.
- localStorage-backed state: rejected for sensitive candidate data.

## Follow-Up Work

- Review state complexity after Phase 4.
- Add a superseding ADR if Pinia becomes justified.
