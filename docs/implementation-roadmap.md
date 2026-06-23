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

Status: complete.

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

## Design Documentation And Review Track

Status: ongoing when useful.

The implemented frontend is the current design-review surface. Figma reconstruction is optional and
should resume only when useful editing access is available or a collaboration need justifies it.

Future work:

- Record approved tokens and component variants in a shared design file when useful.
- Run manual keyboard, screen-reader, zoom, contrast, and reduced-motion reviews.
- Conduct usability research before reporting candidate findings.
- Refine content and layouts only from observed evidence or a documented product decision.

## Phase 2 - Django, DRF, PostgreSQL, And Django Admin

Status: complete.

Objective: make the backend the source of truth for vacancies and staff-managed application records.

Implemented foundation:

- Django project and focused vacancy, application, and document modules.
- PostgreSQL-ready models, constraints, initial migrations, and SQLite test configuration.
- DRF configuration, consistent errors, health endpoint, and read-only vacancy endpoints.
- Django Admin registration for vacancy, application, draft, and document metadata.
- Pytest and Ruff tooling.

Still deferred:

- Frontend API integration and authoritative server-backed candidate workflows.
- Candidate draft authorization, throttling, OpenAPI generation, and privacy-safe operational logs.
- PostgreSQL runtime validation.

Production database or migration actions require separate approval.

## Phase 3 - Secure Drafts And Private CV Upload

Status: in progress. Slice 1 ownership/lifecycle, Slice 2 draft API, Slice 3 backend
experience-entry persistence, and Slice 4 private storage abstraction are implemented in the
backend foundation. Phase 3 overall remains in progress.

Objective: replace in-memory fixture draft persistence with authorized, expiring server-side drafts,
bounded employment entries, and private PDF upload/metadata/replacement/deletion while preserving
the accepted four-step frontend.

Accepted planning decisions:

- One active anonymous draft total per browser, matching ADR 0004 and the existing conflict UI.
- A server-generated 256-bit random secret in a same-origin host-only HttpOnly cookie; only its
  password-style hash is stored.
- `Secure=True` outside local development, `SameSite=Lax`, and a path restricted to Phase 3 draft
  APIs. The cookie is renewed only after successful mutations and cleared after abandonment, expiry,
  revocation, or invalid ownership.
- Django CSRF middleware on every unsafe request, with a no-store token-bootstrap endpoint and
  `X-CSRFToken` from the Nuxt service.
- Same-origin browser APIs in production and through a local Nuxt development proxy; no CORS
  dependency.
- Seven-day inactivity expiry bounded by a thirty-day absolute lifetime from creation and the
  vacancy deadline. Reads never renew expiry. Successful mutations renew only within those bounds.
- Optimistic draft versions through `ETag` and `If-Match` plus short database row locks; missing
  `If-Match` returns `428 draft_version_required`, and stale clients receive a conflict instead of
  silent last-write-wins behavior.
- Optional, bounded employment entries with concise month-level fields, explicit `position`
  ordering, a five-entry cap, and the existing free-text summary retained alongside them.
- Private local storage through an application-owned interface, allowing a future object-store
  adapter without a domain-model redesign.
- PDF only, 5 MiB maximum, one file per request, 1-10 pages, layered extension/MIME/signature and
  strict `pypdf` structural checks, generated storage keys, and no malware-scanning claim.
- Upload, metadata, replacement, and deletion only through the singleton CV endpoint. Candidate,
  public, and staff document download are excluded from Phase 3.
- The first checksum migration leaves `sha256` nullable for existing metadata while service-layer
  creation requires SHA-256 for every new Phase 3 upload.
- Submission and status lookup remain visibly simulated in the frontend until Phase 4.

Still deferred:

- CV upload, PDF validation, document mutation APIs, and cleanup.
- Frontend integration with the draft API.
- Submission, deployment, monitoring, and PostgreSQL runtime verification.

### Implementation Slices

Each slice requires its own review before the next security boundary depends on it. Model guidance
names the preferred model for implementation support, not permission to begin work.

| Slice | Scope | Dependencies | Model recommendation | Reasoning level | Expected validation |
| --- | --- | --- | --- | --- | --- |
| 1. Ownership and lifecycle | Cookie helpers, CSRF bootstrap, credential verification, draft version/activity/revocation, seven-day inactivity plus thirty-day absolute expiry, deadline bound, and generic unavailable behavior. | Phase 2 models and ADRs 0004/0009. | GPT-5.5 | High; authorization and lifecycle edge cases are security-critical. | Model/service tests, CSRF enforcement, cookie-attribute assertions, cross-draft/cross-vacancy tests, Django checks. |
| 2. Draft API | Create/resolve/read, candidate and experience-summary PATCH, API error/request-ID integration, no-store responses. | Slice 1. | GPT-5.5 | High; every endpoint must preserve enumeration-safe authorization. | API matrix, stale-version conflicts, validation mapping, unsupported methods, lint/format/tests. |
| 3. Experience persistence | `DraftExperienceEntry`, migration, bounded CRUD/reorder, and parent-version increments. Frontend integration remains part of Slice 7. | Slices 1-2. | GPT-5.4 | Medium; conventional child CRUD with explicit constraints. | Migration dry-run, model constraints, ownership and count-cap API tests, frontend unit tests when integration begins. |
| 4. Private storage abstraction | Complete: provider-neutral interface, private local adapter, ignored root, fake/test adapter, canonical key generation, and configuration validation. No upload endpoint or document download was added. | Slice 1. | GPT-5.5 | High; storage-path and privacy boundaries must be exact. | Traversal/key tests, no public route, adapter contract tests, configuration checks. |
| 5. Upload validation | Complete: size/empty/extension/MIME/magic/structure/active-content checks, filename normalization, SHA-256, bounded temporary-file handling, strict `pypdf==6.14.1` validation, and no endpoint/storage/DB write. | Slice 4 and the reviewed base parser package. | GPT-5.5 | High; hostile parser input and resource limits require defensive review. | Complete upload rejection matrix, malformed/encrypted/active PDF tests, memory/size boundaries, no secret logging. |
| 6. Document mutation API | Singleton CV create/read/replace/delete, compensation, row locks, active uniqueness, and retryable deletion metadata. | Slices 1, 2, 4, and 5. | GPT-5.5 | High; database and external storage cannot share one transaction. | Failure-injection tests, race/conflict tests, old-document preservation, orphan prevention, unauthorized mutation tests. |
| 7. Frontend integration | Real draft service/composable, browser-only bootstrap, 800 ms autosave, route refresh, conflict/expiry UI, experience CRUD, XHR upload progress/retry/cancel/replace/delete. | Stable API from slices 2, 3, and 6. | GPT-5.4 for primary work; GPT-5.5 for conflict/security review. | High; state recovery and accessibility cross multiple routes. | Format, lint, typecheck, Vitest, build, Playwright candidate flow, responsive/reduced-motion/manual screen-reader spot checks. |
| 8. Cleanup | Idempotent dry-run/batched management command, revoke/scrub, pending blob deletion, stale-orphan grace period, aggregate logs. | Slices 1, 4, and 6. | GPT-5.5 | High; deletion failures must not leak data or lose cleanup keys. | Dry-run/apply tests, repeated-run tests, storage-failure retries, cleanup eligibility, privacy-log assertions. |
| 9. Security and regression tests | Complete authorization, CSRF, upload, race, logging, admin, and existing Phase 1/2 regression matrix. | Slices 1-8. | GPT-5.5 | High; independent adversarial review is needed before handoff. | Full backend/frontend suites; PostgreSQL-specific plan executed when an approved service exists; browser interaction review. |
| 10. Documentation reconciliation | Align README/current-state copy, contracts, runbook outline, settings inventory, and deferred claims with implemented evidence. | Slices 1-9 passing. | GPT-5.4 | Medium; accuracy and handoff consistency are primary. | Link review, `git diff --check`, documentation search for stale simulation/implementation claims. |

### Review Gates

1. **Ownership gate:** cookie, CSRF, generic errors, fixation/replay limits, and one-draft behavior are
   approved before exposing mutation views.
2. **Schema gate:** migrations, field privacy, constraints, and rollback SQL are reviewed before any
   migration is applied.
3. **Dependency gate:** the exact `pypdf==6.14.1` base release, license, Python compatibility, and
   dependency graph were reviewed before parser code. Future parser upgrades repeat this gate.
4. **Storage gate:** Slice 4 now covers private-root isolation, generated keys, duplicate-save
   protection, failure cleanup, strict configuration, and no public URL capability. Replacement
   compensation and retryable physical deletion remain part of later document mutation and cleanup
   slices before accepting uploads.
5. **Frontend gate:** existing fixtures remain available until the real API path passes unit,
   browser, responsive, keyboard, focus, and reduced-motion checks.
6. **Database gate:** SQLite checks may support implementation, but PostgreSQL row locking,
   concurrency, and conditional uniqueness must pass before production-readiness claims.
7. **Phase gate:** review and submit controls remain simulated and no status API is introduced.
8. **Completion gate:** no skipped required checks, stale capability claims, public document URL, or
   logged candidate/credential/file data remains.

### Phase 3 Exit Criteria

- Same-browser drafts survive refresh and reject missing, incorrect, expired, revoked, malformed,
  cross-draft, and cross-vacancy access without enumeration.
- Candidate fields, experience summary, and bounded experience entries persist server-side with
  recoverable conflicts.
- Valid PDFs upload privately and invalid, empty, oversized, spoofed, malformed, encrypted, or
  active-content PDFs fail safely without losing other draft data.
- Replacement preserves the previous active document until the new one succeeds; deletion and
  cleanup remain retryable.
- Frontend loading, autosave, conflict, expiry, upload, replacement, deletion, and failure states are
  accessible and do not shift layout.
- Backend/frontend verification passes, with PostgreSQL-only evidence clearly separated if no
  approved PostgreSQL runtime is available.
- Documentation states exactly what is implemented and what remains simulated or deferred.

### Explicit Phase 3 Exclusions

- Final application submission or submitted-record immutability implementation.
- Status-reference generation, status-secret delivery, or public status lookup.
- Email notifications, applicant accounts, magic links, or cross-device recovery.
- Employer-facing workflow changes or staff mutation APIs.
- Candidate, public, or staff document download.
- Production object storage, deployment, CI, scheduling, backup, or monitoring integration.
- Malware-scanning service, quarantine workflow, OCR, CV parsing, or AI features.

### Pre-Implementation Requirements

The plan is approved at the architecture level. Implementation still must:

1. Repeat the dependency gate before changing the pinned `pypdf` release or adding parser extras.
2. Keep `sha256` nullable in the first migration while enforcing checksums for every new accepted
   Phase 3 upload in the service layer.
3. Treat PostgreSQL row-lock, concurrency, conditional-constraint, and replacement tests as a
   separate verification track that blocks production claims, not initial coding.

### Principal Risks

- A bearer cookie stolen through device compromise can authorize the draft until revocation or
  expiry; Phase 3 has no account or device binding.
- Cookie loss can leave an inaccessible active draft until cleanup and permit a new one because the
  system deliberately avoids browser fingerprinting.
- Structural PDF validation reduces format risk but is not malware scanning. Phase 3 avoids staff
  exposure by excluding document download.
- Database and storage operations cannot be one transaction; compensation and orphan cleanup must
  pass failure-injection tests.
- SQLite cannot prove PostgreSQL locking and concurrent uniqueness behaviour.
- Local in-memory throttling cannot support production abuse-resistance claims across workers.
- Production HTTPS, private object-store ACLs, backups, scheduler, monitoring, and incident response
  remain unimplemented, so real candidate data remains prohibited.

## Phase 4 - Integrated Submission And Status Lookup

Status: not started.

Objective: replace simulated completion with atomic persistence and minimal private status access.

Planned work:

- Final server-side revalidation.
- Transactional submission and PostgreSQL duplicate constraints.
- Submission-in-progress handling in the client and idempotent server behavior.
- Separate application reference and high-entropy status lookup secret.
- Generic lookup failures, rate limiting, secret hashing, and minimal response content.
- Integration and concurrency tests.

## Phase 5 - Security, Accessibility, And Operational Hardening

Status: not started.

Planned work:

- Defensive authorization, upload, CSRF, XSS, logging, and admin review.
- Automated accessibility checks plus keyboard, screen-reader, zoom, contrast, and reduced-motion
  review.
- Performance budgets and failure monitoring.
- Retention policy, cleanup verification, diagnostics, and incident guidance.
- Production-readiness review only after implemented controls have evidence.

## Phase 6 - CI, Packaging, And Deployment

Status: not started.

Planned work:

- CI for frontend and backend checks.
- Reproducible packaging and environment separation.
- Same-origin deployment, HTTPS, secure cookies, restricted admin access, and secret injection.
- Backup, restore, rollback, smoke-test, and runbook validation.

Deployment, cloud resources, production secrets, and live data remain approval-gated actions.
