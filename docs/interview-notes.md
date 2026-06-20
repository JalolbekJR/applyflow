# Interview Notes

These notes describe the planned architecture. They must not be presented as implemented behavior until the relevant phases are complete.

## Why Nuxt Rather Than Plain Vue?

The planned architecture uses Nuxt because ApplyFlow has public vacancy pages and a case-study page that benefit from server-rendered HTML, metadata, route structure, and a clear portfolio demonstration of Nuxt. Plain Vue would be enough for a small SPA, but it would not show the same route and SSR decisions.

## Why Django REST Framework?

The planned backend uses DRF because the project needs a REST API, serializer validation, permission checks, throttling, and a Django Admin-backed internal workflow. DRF fits the requested backend skill set and keeps the API close to Django models and services.

## Why PostgreSQL?

PostgreSQL is planned because duplicate submission protection, indexes, constraints, and transactional submission behavior matter. SQLite may be fine for small local experiments, but it would not demonstrate the same production-shaped data decisions.

## Why No Candidate Account?

The first version avoids candidate accounts because accounts add friction and scope. The flow only needs anonymous draft protection, submission, and private status lookup. If later validation proves candidates need cross-device draft recovery, the project can revisit magic links or accounts with a new ADR.

## How Are Drafts Protected?

The planned draft model uses a server-generated high-entropy secret, stored hashed on the server. A non-sensitive draft ID is not proof of ownership. The preferred same-origin implementation uses an HttpOnly secure cookie instead of localStorage. Version one intentionally allows one active anonymous draft per browser; starting another application requires continuing or abandoning the current draft.

## How Will CV Uploads Be Secured?

The planned upload design treats CV files as hostile input. Version one accepts PDF only with a 5 MB maximum. The server checks the extension, inspects the PDF signature and content, generates storage names, stores documents privately, and authorizes every download. Malware scanning is not claimed for the first prototype.

## How Will Duplicate Submission Be Prevented?

The planned backend will enforce duplicate protection during atomic submission. The product rule and PostgreSQL constraint are one submitted application per normalized email and vacancy record. A materially changed or reopened role is represented by a new vacancy record; version one does not need a publication-cycle entity.

## How Does Status Lookup Stay Private?

The planned status flow separates a readable `application_reference` from a high-entropy `status_lookup_secret`. The reference is useful for support, but it is not an authorization credential. The secret is hashed at rest, never logged, and required for status access. Email is not treated as a secret.

## Why Use Django Admin?

Django Admin is enough for version one because the portfolio focus is the candidate application experience. A custom recruiter dashboard would expand scope without proving the core product idea.

Production admin ingress must be restricted and hardened, staff permissions remain least privilege, and document access requires an explicit authorization check.

## Why Only Three Application States?

Version one uses `submitted`, `under_review`, and `closed`. Additional workflow states would imply recruiter operations, candidate communication, and privacy rules that the product does not yet need.

## How Will Errors Preserve User Input?

The planned frontend keeps entered values visible after recoverable errors and maps server validation to field errors and an error summary. Server-side drafts preserve progress across reloads and failed upload/submission attempts.

## How Will The Application Remain Accessible?

The plan requires semantic landmarks, persistent labels, visible focus, keyboard navigation, focus movement after step changes, error summaries, associated hints and errors, reduced-motion support, and keyboard-only Playwright coverage.

## Why Is Pinia Not Planned First?

The first version can use route-local state and composables. Pinia is useful when state is shared across unrelated parts of the app or when it improves testing. The project should not add it before that need appears.

## How Will SSR Interact With Client-Side Form State?

Vacancy pages can render on the server. Application forms need hydration because file inputs, upload progress, draft restoration, and focus behavior depend on browser APIs. The implementation should avoid claiming full progressive enhancement until that path is designed and tested.

## What Belongs In Client Validation Versus Server Validation?

Client validation helps candidates fix common errors quickly. Server validation is authoritative. The server must verify vacancy status, draft authorization, required fields, PDF upload rules, duplicate submissions, and consent version.

## How Will CI Verify The System?

The planned CI will run frontend lint/typecheck/tests/build, backend Ruff/pytest/migration/system checks, Playwright critical paths, and later Docker builds. No workflow exists yet because Phase 0 is documentation only.
