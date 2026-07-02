# Testing Strategy

Testing covers the implemented Phase 1 frontend, Phase 2 backend foundation, completed Phase 3
backend slices through Slice 8 cleanup, and current frontend integration.

## Current Frontend Checks

Run from `frontend/`:

```powershell
npm run format:check
npm run lint
npm run typecheck
npm run test
npm run build
npm run test:e2e
```

### Unit And Component Coverage

- Candidate and experience validation.
- Relative API transport, same-origin credentials, empty `204` responses, safe error
  normalization, CSRF bootstrap deduplication, and memory-only CSRF token storage.
- Runtime response guards and draft `ETag` parsing.
- Vacancy API mapping and active-vacancy lookup.
- Draft aggregate mapping, employment-entry mapping, and private document metadata exclusion.
- Backend field-error mapping to existing UI controls.
- Draft mutation serialization.
- Step progress semantics.
- Error-summary focus, scrolling, links, and grouped destinations.
- PDF selection, unsupported file rejection, oversize file rejection, upload event emission, and
  protected metadata display.
- Default brand validation, alternate fictional brand validation, unsafe config rejection, and proxy
  target validation.

### Playwright Coverage

The default Playwright suite is a deterministic browser smoke with Playwright-routed API responses.
It exercises the current Slice 7 UI shape, deferred submission behavior, employment-entry controls,
CV metadata display, and mobile overflow.

The real-stack Slice 7 harness is run separately with:

```powershell
npm run test:e2e:fullstack
```

It verifies:

- Browser to Nuxt same-origin `/api/**` proxy to Django.
- Temporary SQLite database and temporary private document root.
- Fictional seeded vacancy only.
- Real draft create/resume after reload.
- Candidate details save, experience summary save, employment-entry create/edit/delete.
- Real CV upload, replacement, and deletion.
- Review route shows the persisted aggregate.
- Active-draft conflict, conflict/error focus, abandonment, keyboard flow, 320px, 390px, and 1440px
  checks.
- No generated database, storage object, screenshot, report, or trace is committed.

## Current Backend Checks

Run from `backend/` with the virtual environment installed:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
```

The PostgreSQL verification boundary is separate from the ordinary SQLite suite. Use
[PostgreSQL verification](postgresql-verification.md) for the test-only service, environment
variables, focused command, relevant existing-test subset, proof command, and teardown.

Current pytest coverage includes:

- Vacancy UUID, status choices, slug uniqueness, published reads, and unpublished rejection.
- Separate draft and submitted application records.
- Submitted-application public-reference and vacancy/normalized-email uniqueness.
- Draft credential hashing and verification for the current draft API.
- Submitted-application status-secret hashing helper coverage at model level only; no private
  status-lookup endpoint or end-to-end status flow exists.
- Document owner XOR, active-document uniqueness, checksum, and physical-deletion constraints.
- Safe Django Admin registration with credential hashes, storage keys, and checksums excluded.
- Health, read-only vacancy API, unsupported mutation, and JSON error behavior.
- PostgreSQL URL parsing and secure DRF permission defaults.
- Canonical private document storage keys, invalid-key rejection, duplicate-save protection,
  chunked local writes, temporary-file cleanup, deterministic fake/local adapter enumeration,
  strict document-storage configuration, no public storage route or URL capability, secure PDF
  validation, and authorized singleton CV metadata/upload/replacement/delete behavior.
- Cleanup command dry-run/apply behavior, expired-draft transition, terminal scrubbing, pending
  document deletion retry, missing-object completion, stale-orphan grace handling, batch limits,
  hard-delete eligibility, item-failure exit behavior, and privacy-safe aggregate output.

## Phase 3 Verification Matrix

### Models, Constraints, And Services

| Area                        | Status                                                        | Required tests                                                                                                                                                                                                                  | Primary engine                                       |
| --------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Credential hashing          | Implemented and currently tested                              | Raw secret never stored; correct secret verifies; wrong secret fails; compound cookie UUID alone cannot authorize.                                                                                                              | SQLite                                               |
| Draft expiry                | Implemented and currently tested                              | Seven-day inactivity expiry, thirty-day absolute lifetime, vacancy-deadline bound, successful mutation refresh, and reads that do not renew retention.                                                                          | SQLite                                               |
| Ownership                   | Implemented and currently tested                              | Cookie UUID and route UUID must match; secret hash, active status, null revocation, expiry, and stored vacancy are all required.                                                                                                | SQLite                                               |
| State transitions           | Implemented and currently tested                              | Only active drafts mutate; abandon/request-time expire revoke and scrub; submitted transition remains unavailable in Phase 3.                                                                                                   | SQLite                                               |
| Optimistic version          | Implemented and covered by PostgreSQL-specific tests          | Authorized reads return `ETag`; accepted mutations increment once and return a fresh `ETag`; missing `If-Match` returns `428`; stale version is rejected; failed validation does not increment or refresh expiry.               | SQLite; concurrent lock behavior on PostgreSQL       |
| Experience entries          | Implemented; constraints covered by PostgreSQL-specific tests | Parent ownership, month validation, current/end consistency, unique position, five-entry cap, persisted order, cascade/scrub, and parent-version increment.                                                                     | SQLite; concurrent constraint behavior on PostgreSQL |
| Active document uniqueness  | Implemented and covered by PostgreSQL-specific tests          | One active document per draft; deleted history may coexist; replacement swaps active metadata atomically.                                                                                                                       | SQLite; concurrent replacement on PostgreSQL         |
| Cleanup-supporting metadata | Implemented and currently tested                              | Logical deletion, deletion timestamps, pending physical-deletion metadata, request-path delete attempts, replacement compensation, and adapter enumeration.                                                                     | SQLite plus temporary fake/local storage             |
| Cleanup command coverage    | Implemented and currently tested                              | Cleanup eligibility beyond request paths, stale-orphan grace-period behavior, batch selection, dry-run, repeated execution, retry across command runs, aggregate output, item-failure exit behavior, and conservative rechecks. | SQLite plus temporary fake/local storage             |
| Scrubbing                   | Implemented and currently tested                              | Candidate fields, skills, message, consent, experience text, and original display filename are removed by cleanup for expired/abandoned shells; current request paths revoke or logically retire data where reached.            | SQLite                                               |

### API Authorization And CSRF

| Scenario               | Status                                                                   | Expected evidence                                                                                                                                                                             |
| ---------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Create and resume      | Implemented and currently tested                                         | No cookie creates `201`; same valid cookie/vacancy restores `200`; no duplicate draft.                                                                                                        |
| Active resolution      | Implemented and currently tested                                         | No cookie returns `204`; valid cookie returns the aggregate and `ETag`; response excludes hashes, normalized email, storage key, checksum, physical-deletion fields, and public document IDs. |
| Missing credential     | Implemented and currently tested                                         | Generic `404 draft_unavailable`; no object details.                                                                                                                                           |
| Incorrect credential   | Implemented and currently tested                                         | Same status, code, message shape, and safe fields as missing credential.                                                                                                                      |
| Cross-draft access     | Implemented and currently tested                                         | A valid cookie for draft A cannot read or mutate draft B, its experience, or its document.                                                                                                    |
| Cross-vacancy access   | Implemented and currently tested                                         | A draft cannot be rebound or reused for another vacancy; creation returns the defined conflict.                                                                                               |
| Expired or abandoned   | Implemented and currently tested                                         | Access is revoked, cookie cleared where appropriate, data scrubbed on current paths, and generic response returned.                                                                           |
| Enumeration resistance | Implemented and currently tested                                         | Random, real-other, deleted, expired, and malformed UUID targets use indistinguishable candidate-facing errors.                                                                               |
| CSRF                   | Implemented and currently tested                                         | Unsafe requests without a token, with a wrong token, or from an untrusted origin fail; valid same-origin header succeeds. Use clients with `enforce_csrf_checks=True`.                        |
| Fixation               | Implemented and currently tested                                         | An attacker-supplied invalid cookie is cleared and is not adopted or replaced in the same create request.                                                                                     |
| Replay                 | Implemented and currently tested                                         | Revoked or expired credentials cannot resume or mutate; ordinary valid concurrent requests still face version checks.                                                                         |
| Conflict               | Implemented and currently tested                                         | Stale candidate, experience, entry, upload, replace, and delete mutations return `409` without changing data.                                                                                 |
| Version precondition   | Implemented and currently tested                                         | Missing `If-Match` on candidate, experience, entry, CV, and abandonment mutations returns `428 draft_version_required`.                                                                       |
| Error envelope         | Implemented for error JSON and response header; log correlation deferred | Current API errors include a JSON request ID and `X-Request-ID`; no test or implementation proves shared structured log correlation.                                                          |
| Cache policy           | Implemented and currently tested                                         | CSRF, draft, candidate, experience, and document responses use `Cache-Control: no-store`.                                                                                                     |
| Methods                | Implemented and currently tested                                         | Unsupported methods return the existing JSON envelope and do not mutate state.                                                                                                                |

### Upload, Storage, Replacement, And Deletion

| Scenario                    | Expected evidence                                                                                                                                                                                                                             |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Valid PDF                   | `.pdf`, declared `application/pdf`, valid header/structure, 1-10 pages, no forbidden active content; private generated key and safe metadata persist.                                                                                         |
| Wrong extension             | Rejected even if MIME and magic bytes claim PDF.                                                                                                                                                                                              |
| Wrong MIME                  | Rejected even with `.pdf` and PDF bytes.                                                                                                                                                                                                      |
| Wrong magic bytes           | Rejected even with extension and MIME.                                                                                                                                                                                                        |
| Empty file                  | Rejected without storage or metadata.                                                                                                                                                                                                         |
| Oversized file              | Exactly 5 MiB accepted if otherwise valid; one byte over rejected with `413`; chunk reader stops without unbounded memory.                                                                                                                    |
| Malformed/encrypted PDF     | Structural parse failure, zero pages, over-ten pages, encryption, embedded files, JavaScript, `/OpenAction`, `/AA`, file-attachment annotations, RichMedia/Movie/Sound/Screen/3D annotations, or automatic actions rejected.                  |
| Malicious filename          | Traversal separators, absolute paths, control characters, Unicode edge cases, excessive length, and blank names normalize to safe display metadata and never affect the key.                                                                  |
| Checksum                    | SHA-256 matches stored bytes but never appears in API output or logs.                                                                                                                                                                         |
| Storage key boundary        | Implemented in Slice 4: canonical `drafts/{draft_uuid}/{document_uuid}.pdf` keys reject traversal, alternate separators, control characters, non-canonical UUIDs, unexpected extensions, and temporary-name collisions before storage access. |
| Private adapter contract    | Implemented in Slice 4: local and fake adapters share save/open/delete/exists/enumeration behavior, duplicate saves never overwrite, failed writes clean temporary files, and enumeration returns stable relative keys only.                  |
| Validation service boundary | Implemented in Slice 5: validates bytes or binary streams and returns safe metadata only; no endpoint, storage write, database write, URL, or download route is introduced.                                                                   |
| Initial storage failure     | No active metadata; form answers preserved; safe retry response.                                                                                                                                                                              |
| Metadata failure after save | Compensating delete runs; failed compensation becomes orphan-cleanup evidence.                                                                                                                                                                |
| Replacement success         | Old document stays active until new validation/storage succeeds; transaction activates only the new metadata; old blob becomes cleanup-eligible.                                                                                              |
| Replacement failure         | Old active metadata and blob remain authorized; no second active document.                                                                                                                                                                    |
| Deletion                    | Authorization stops at logical deletion; physical failure is retryable; repeat does not restore access.                                                                                                                                       |
| Unauthorized mutation       | Another draft cannot read metadata, create/replace, or delete the singleton CV.                                                                                                                                                               |
| Orphan cleanup              | Implemented Slice 8 coverage: unreferenced keys younger than the approved grace period are retained; older confirmed orphans are removed in bounded idempotent runs; referenced and uncertain objects are retained.                           |
| Public exposure             | No API response, admin field, static route, or Nuxt route exposes a storage key or public URL.                                                                                                                                                |

Malware scanning is not tested or claimed because Phase 3 does not implement it.

### Frontend Unit And Component Coverage

- CSRF bootstrap and header injection without exposing the draft cookie to JavaScript.
- Draft create, active resolve, restore after refresh, and vacancy-conflict normalization.
- Explicit save/continue mutation handling, one in-flight mutation queue, retry, and cancellation.
- Server field errors mapped to existing summary and input associations.
- Generic expired/unavailable recovery that clears in-memory candidate data.
- Stale-version conflict preserves local text and requires a deliberate refresh/review action.
- Experience-entry add, edit, persisted position ordering, cap, validation, delete confirmation,
  and server rollback.
- Upload progress, cancel, retry, successful singleton-CV metadata, replacement preserving old
  metadata until success, and confirmed deletion.
- Loading, saving, saved, failed, retrying, uploaded, removed, conflict, and expired announcements.
- Disabled states, stable layout regions, focus movement, keyboard operation, and reduced-motion
  behavior.
- Final submission and status lookup remain disabled/deferred. No fake submission or fake status
  service remains active in the real candidate path.

### Browser Coverage

- Start, save candidate fields, refresh, and restore on every application route.
- Continue an existing same-vacancy draft and deliberately abandon a conflicting-vacancy draft.
- Direct cross-vacancy route navigation never mutates the authorized draft.
- Save failure and retry preserve typed values; stale conflict does not overwrite either tab.
- Expired draft offers a fresh start without revealing target existence.
- Valid upload reports progress and persists metadata across refresh.
- Invalid, oversized, and malformed uploads preserve candidate and experience data.
- Replacement failure preserves the old CV; replacement success and deletion update review state.
- Experience-entry CRUD works by keyboard and at 320 px without horizontal overflow.
- Error summary, grouped controls, upload region, conflict notice, and destructive confirmations
  receive correct focus and accessible descriptions.
- Touch operation does not depend on hover; reduced-motion mode avoids smooth/ornamental motion.
- Final submission and status remain disabled/deferred and no Phase 4 API is called.

## SQLite And PostgreSQL Boundary

SQLite remains appropriate for serializer, service, API, cleanup-supporting metadata,
storage-adapter, and most model tests. It can exercise the existing check and partial-unique
behavior used by the local project.

The following evidence must pass on PostgreSQL before production-readiness claims:

- `select_for_update` behavior for simultaneous save, abandon, upload, replace, and delete;
- stale-version losers and no lost updates across transactions;
- concurrent five-entry cap and unique entry position;
- conditional one-active-document uniqueness under concurrent replacement;
- generated check constraints and migration SQL;
- transaction/on-commit compensation behavior with the production database driver;
- cleanup rechecks and accidental overlapping operator runs. The current command has no parallel
  feature.

Phase 3 can be implemented with SQLite locally, but a skipped or blocked PostgreSQL check remains an
explicit release risk. The repository includes a loopback-only test Compose service and explicit
PostgreSQL settings module for this verification track. Suitable verification environments include
a local Docker PostgreSQL service, an already-running local PostgreSQL instance that satisfies the
settings guard, or a later CI service container. PostgreSQL evidence must be rerun after database,
storage, cleanup, or mutation changes.

## Test Data Rules

Use obviously fictional values such as:

- `Avery Example`
- `avery.candidate@example.test`
- `AF-9Q2K-M7P4`
- `slk_9Wn6zQp4v2T8mR7cX5bL3kY1`
- `avery-example-cv.pdf`

Do not use real CVs, names, emails, phone numbers, addresses, employers, credentials, or application
records.

## Evidence Rules

- A command is passing only after it has run successfully.
- Retries and warnings remain part of the execution report.
- Screenshots prove rendered state only; they do not prove usability or accessibility conformance.
- Client-side checks do not prove backend security.
