# ADR 0012 - Use A Code-First Design Validation Workflow

Status: Accepted

## Context

Phase 1 needs a review surface for responsive layout, semantics, focus, form behavior, and recovery
states. Useful Figma canvas operations are unavailable under the connected plan, while the accepted
Nuxt architecture can exercise those behaviors directly.

## Decision

Use the running Nuxt frontend and browser screenshots as the primary Phase 1 design-validation
surface. Preserve accepted product, security, privacy, accessibility, and architecture decisions.
Treat screenshots as implementation-review evidence, not user-research evidence.

Figma remains optional and deferred until useful editing access or a concrete collaboration need
justifies reconstructing the approved coded system.

## Consequences

- Responsive, semantic, focus, keyboard, validation, and recovery behavior can be reviewed together.
- Typed fixture services allow frontend progress without claiming backend persistence or security.
- Browser tests and screenshots become part of the Phase 1 quality gate.
- Design-file components, variables, and prototypes remain incomplete.
- The coded frontend does not become suitable for real recruitment without the planned backend and
  hardening work.

## Alternatives Considered

- Wait for expanded Figma access: rejected because it would block behavior that can be validated in
  the browser now.
- Use static image mockups as the primary surface: rejected because they cannot validate semantics,
  focus, responsive behavior, or recovery flows.
- Reduce the design-review standard: rejected because the tooling constraint does not change
  candidate needs.

## Reconsideration Criteria

Reconsider this decision if a shared design file becomes necessary for collaboration, useful Figma
editing access becomes available, or browser-first validation no longer covers the active design
questions.
