# ADR 0003 - Use Separate Routes For Application Steps

Status: Accepted

## Context

The application flow has four steps: position, candidate details, experience, and review. The route strategy affects accessibility, browser history, reload behavior, analytics, draft persistence, and implementation complexity.

## Decision

Use separate Nuxt routes for the application steps:

- `/apply/[slug]`
- `/apply/[slug]/details`
- `/apply/[slug]/experience`
- `/apply/[slug]/review`

The routes share one application-flow layout and draft context. The server remains authoritative for draft ownership and submission.

## Consequences

- Browser back and forward behavior maps to meaningful steps.
- Each step can have a page title, heading, and focus target.
- Reloads can restore the draft through server-backed state.
- Analytics can measure step-level friction later without custom event gymnastics.
- The frontend must guard step access and handle missing or expired drafts.

## Alternatives Considered

- One route with internal step state: simpler initially, but poorer browser history and accessibility semantics.
- Nested child routes: useful if Nuxt layout structure benefits from it, but the public URL shape should remain simple.
- Query parameter steps: less readable and easier to mishandle in links.

## Follow-Up Work

- Define route middleware only when implementation needs it.
- Add Playwright coverage for route reload and keyboard navigation.
