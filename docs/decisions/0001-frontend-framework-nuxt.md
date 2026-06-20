# ADR 0001 - Use Nuxt With Vue 3 For The Frontend

Status: Accepted

## Context

ApplyFlow needs public vacancy pages, a case-study page, and an application flow that can demonstrate Vue, Nuxt, TypeScript, REST API integration, responsive design, and testing.

Current Nuxt documentation describes server-side rendering, file-based routing, code splitting, and data fetching primitives that fit public vacancy pages and route-based application steps.

## Decision

Use Nuxt 4 with Vue 3, TypeScript, Composition API, semantic HTML, and project-specific CSS primitives. Application code follows the Nuxt 4 `frontend/app/` convention; root configuration, `public/`, and tests remain under `frontend/`.

Nuxt will be used for page routing, server-rendered public pages, metadata, and frontend application structure. The Django API remains the backend source of truth.

## Consequences

- Vacancy pages can be server-rendered for initial readability and metadata.
- The application flow can use Nuxt routes while keeping sensitive draft state client-side only when required.
- Hydration and browser-only controls must be handled deliberately.
- The exact Nuxt version should be verified again before Phase 3 scaffolding.

## Alternatives Considered

- Plain Vue SPA: simpler but weaker for vacancy SEO and route-level portfolio demonstration.
- React/Next.js: strong ecosystem, but the vacancy requirements emphasize Vue and Nuxt.
- Large UI library: rejected for version one because the visual identity should come from project-specific primitives.

## Follow-Up Work

- Recheck Nuxt docs before scaffolding.
- Define page routes in Phase 3.
- Add Vitest, Vue Test Utils, and Playwright only during implementation.
