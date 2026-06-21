# Implementation Roadmap

This roadmap separates the implemented frontend foundation from simulated behavior and future
backend work. Phase changes require an explicit scope decision.

## Phase 0 - Product And Architecture Foundation

Status: complete.

Completed work:

- Product scope, candidate journey, field inventory, and information architecture.
- Frontend, backend, privacy, upload, threat-model, testing, and infrastructure plans.
- Architecture decision records for the initial product and technical boundaries.

No user research was conducted in this phase. Product decisions remain hypotheses until they are
validated with appropriate evidence.

## Phase 1 - Candidate Frontend Foundation

Status: current.

Objective: maintain a usable Nuxt 4 candidate experience as the browser-based design and interaction
review surface described in [ADR 0012](decisions/0012-code-first-design-workflow.md).

Implemented:

- Nuxt 4 application structure under `frontend/app/`.
- Typed fictional vacancy data behind a vacancy service.
- Home, vacancy index, vacancy detail, privacy, accessibility, and product-notes routes.
- Position, candidate details, experience, and review application routes.
- Confirmation and private status lookup routes.
- Responsive design tokens and layouts from 320px upward.
- Semantic landmarks, keyboard focus, error summaries, grouped-control relationships, and reduced
  motion.
- Unit, component, Playwright, and ignored browser-screenshot coverage.

Simulated in this phase:

- Draft state exists only in frontend memory.
- Save operations use deterministic fixture delays and failure seams.
- PDF selection keeps file metadata only; no upload occurs.
- Submission returns fixed fictional credentials.
- Status lookup uses fixed fictional responses and client-only attempt limiting.

Acceptance criteria:

- Invalid or unavailable application routes never create or alter a draft.
- Validation and recoverable failures preserve entered values.
- Visual and semantic reading order agree at mobile widths.
- Fixture behavior is clearly distinguished from future backend guarantees.
- Formatting, lint, type checking, unit tests, production build, and Playwright checks pass.
- No real candidate data, backend code, production infrastructure, or deployment is added.

## Phase 2 - Design Documentation And Review

Status: deferred.

The implemented frontend is the current design-review surface. Figma reconstruction is optional and
should resume only when useful editing access is available or a collaboration need justifies it.

Future work:

- Record approved tokens and component variants in a shared design file when useful.
- Run manual keyboard, screen-reader, zoom, contrast, and reduced-motion reviews.
- Conduct usability research before reporting candidate findings.
- Refine content and layouts only from observed evidence or a documented product decision.

## Phase 3 - Django, DRF, PostgreSQL, And Django Admin

Status: not started.

Objective: make the backend the source of truth for vacancies and staff-managed application records.

Planned work:

- Django project and focused vacancy, application, and document modules.
- PostgreSQL models, constraints, migrations, and test configuration.
- DRF serializers, views, permissions, throttling, and OpenAPI contract.
- Django Admin for vacancy and application operations; no custom staff dashboard.
- Server-side validation and privacy-safe logging.

Production database or migration actions require separate approval.

## Phase 4 - Secure Drafts And Private CV Upload

Status: not started.

Objective: replace in-memory fixture behavior with authorized, expiring server-side drafts and
private document storage.

Planned work:

- High-entropy draft credentials delivered through a same-origin secure HttpOnly cookie.
- One active anonymous draft per browser, with continue and abandon behavior.
- Draft expiration and cleanup.
- PDF-only upload with extension, signature, content, and size validation on the server.
- Server-generated storage names, private storage, authorized download, and safe deletion.
- Recoverable upload errors that preserve other candidate data.

## Phase 5 - Integrated Submission And Status Lookup

Status: not started.

Objective: replace simulated completion with atomic persistence and minimal private status access.

Planned work:

- Final server-side revalidation.
- Transactional submission and PostgreSQL duplicate constraints.
- Submission-in-progress handling in the client and idempotent server behavior.
- Separate application reference and high-entropy status lookup secret.
- Generic lookup failures, rate limiting, secret hashing, and minimal response content.
- Integration and concurrency tests.

## Phase 6 - Security, Accessibility, And Operational Hardening

Status: not started.

Planned work:

- Defensive authorization, upload, CSRF, XSS, logging, and admin review.
- Automated accessibility checks plus keyboard, screen-reader, zoom, contrast, and reduced-motion
  review.
- Performance budgets and failure monitoring.
- Retention policy, cleanup verification, diagnostics, and incident guidance.
- Production-readiness review only after implemented controls have evidence.

## Phase 7 - CI, Packaging, And Deployment

Status: not started.

Planned work:

- CI for frontend and backend checks.
- Reproducible packaging and environment separation.
- Same-origin deployment, HTTPS, secure cookies, restricted admin access, and secret injection.
- Backup, restore, rollback, smoke-test, and runbook validation.

Deployment, cloud resources, production secrets, and live data remain approval-gated actions.
