# ADR 0009 - Prefer Same-Origin Deployment For The First Public Version

Status: Accepted

## Context

ApplyFlow has anonymous drafts, cookies, uploads, CSRF concerns, Django Admin, and a Nuxt frontend. Deployment shape affects auth, CORS, cookies, and operational complexity.

## Decision

Prefer same-origin deployment for the first public version.

A reverse proxy routes public pages to Nuxt and API/admin/media-access routes to Django. Administrative sessions use secure cookies. Candidate draft secrets should use secure HttpOnly cookies when implemented.

## Consequences

- CORS complexity is reduced.
- Cookies can be scoped more simply.
- CSRF behavior is easier to reason about.
- The reverse proxy must be configured carefully.
- Local development may still run frontend and backend on separate ports with explicit dev settings.

## Alternatives Considered

- Fully separate frontend and API domains: more CORS and cookie complexity than version one needs.
- Static-only frontend: insufficient for SSR vacancy pages and route behavior.
- Backend-rendered only: would discard the accepted Nuxt frontend architecture.

## Follow-Up Work

- Document local and production proxy behavior during Phase 7 deployment work.
- Add deployment checks for cookies, HTTPS, and security headers.

Deployment is not implemented. This decision remains the target topology for the future integrated
frontend and backend.
