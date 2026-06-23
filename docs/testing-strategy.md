# Testing Strategy

Testing covers the implemented Phase 1 frontend, Phase 2 backend foundation, and completed Phase 3
backend slices.

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
- Vacancy service cloning and active-vacancy lookup.
- Step progress semantics.
- Error-summary focus, scrolling, links, and grouped destinations.
- PDF metadata acceptance, unsupported file rejection, and oversize metadata rejection.
- Credential copy success and manual-copy recovery.
- Deterministic simulated save failure and retry.

### Playwright Coverage

- Vacancy discovery through confirmation and valid status lookup.
- Invalid application routes and draft-mutation regression.
- Route heading focus and review-edit navigation.
- Text, radio group, upload group, and consent error destinations.
- Generic status failure and form relationship.
- Save failure, preserved values, announcement, focus, and retry.
- Rejected upload without loss of unrelated values.
- Submission-in-progress duplicate activation guard.
- Keyboard application start.
- Mobile semantic and visual vacancy order, footer targets, and 320px reflow.
- Responsive and affected-state screenshots for human review.

## Current Backend Checks

Run from `backend/` with the virtual environment installed:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
```

Current pytest coverage includes:

- Vacancy UUID, status choices, slug uniqueness, published reads, and unpublished rejection.
- Separate draft and submitted application records.
- Submitted-application public-reference and vacancy/normalized-email uniqueness.
- Draft and status credential hashing and verification.
- Document owner XOR, active-document uniqueness, checksum, and physical-deletion constraints.
- Safe Django Admin registration with credential hashes, storage keys, and checksums excluded.
- Health, read-only vacancy API, unsupported mutation, and JSON error behavior.
- PostgreSQL URL parsing and secure DRF permission defaults.
- Canonical private document storage keys, invalid-key rejection, duplicate-save protection,
  chunked local writes, temporary-file cleanup, deterministic fake/local adapter enumeration,
  strict document-storage configuration, no public storage route or URL capability, secure PDF
  validation, and authorized singleton CV metadata/upload/replacement/delete behavior.

## Phase 3 Planned Test Matrix

### Models, Constraints, And Services

| Area | Required tests | Primary engine |
| --- | --- | --- |
| Credential hashing | Raw secret never stored; correct secret verifies; wrong secret fails; compound cookie UUID alone cannot authorize. | SQLite |
| Draft expiry | Seven-day inactivity expiry, thirty-day absolute lifetime, vacancy-deadline bound, successful mutation refresh, and reads that do not renew retention. | SQLite |
| Ownership | Cookie UUID and route UUID must match; secret hash, active status, null revocation, expiry, and stored vacancy are all required. | SQLite |
| State transitions | Only active drafts mutate; abandon/expire revoke and scrub; submitted transition remains unavailable in Phase 3. | SQLite |
| Optimistic version | Authorized reads return `ETag`; accepted mutations increment once and return a fresh `ETag`; missing `If-Match` returns `428`; stale version is rejected; failed validation does not increment or refresh expiry. | SQLite; concurrent lock behavior on PostgreSQL |
| Experience entries | Parent ownership, month validation, current/end consistency, unique position, five-entry cap, ordering, cascade/scrub, and parent-version increment. | SQLite; concurrent cap/order on PostgreSQL |
| Active document uniqueness | One active document per draft; deleted history may coexist; replacement swaps active metadata atomically. | SQLite; concurrent replacement on PostgreSQL |
| Cleanup eligibility | Expired, abandoned, pending physical deletion, and stale orphan grace-period rules; active/recent objects excluded. | SQLite plus temporary fake/local storage |
| Scrubbing | Candidate fields, skills, message, consent, experience text, and original display filename are removed before retryable storage cleanup. | SQLite |

### API Authorization And CSRF

| Scenario | Expected evidence |
| --- | --- |
| Create and resume | No cookie creates `201`; same valid cookie/vacancy restores `200`; no duplicate draft. |
| Active resolution | No cookie returns `204`; valid cookie returns the aggregate and `ETag`; response excludes hashes, normalized email, storage key, checksum, physical-deletion fields, and public document IDs. |
| Missing credential | Generic `404 draft_unavailable`; no object details. |
| Incorrect credential | Same status, code, message shape, and safe fields as missing credential. |
| Cross-draft access | A valid cookie for draft A cannot read or mutate draft B, its experience, or its document. |
| Cross-vacancy access | A draft cannot be rebound or reused for another vacancy; creation returns the defined conflict. |
| Expired or abandoned | Access is revoked, cookie cleared where appropriate, data scrubbed, and generic response returned. |
| Enumeration resistance | Random, real-other, deleted, expired, and malformed UUID targets use indistinguishable candidate-facing errors. |
| CSRF | Unsafe requests without a token, with a wrong token, or from an untrusted origin fail; valid same-origin header succeeds. Use clients with `enforce_csrf_checks=True`. |
| Fixation | An attacker-supplied invalid cookie is cleared and is not adopted or replaced in the same create request. |
| Replay | Revoked or expired credentials cannot resume or mutate; ordinary valid concurrent requests still face version checks. |
| Conflict | Stale candidate, experience, entry, upload, replace, and delete mutations return `409` without changing data. |
| Version precondition | Missing `If-Match` on candidate, experience, entry, CV, and abandonment mutations returns `428 draft_version_required`. |
| Error envelope | Every Phase 3 error has one request ID shared with `X-Request-ID` and no internal details. |
| Cache policy | CSRF, draft, candidate, experience, and document responses use `Cache-Control: no-store`. |
| Methods | Unsupported methods return the existing JSON envelope and do not mutate state. |

### Upload, Storage, Replacement, And Deletion

| Scenario | Expected evidence |
| --- | --- |
| Valid PDF | `.pdf`, declared `application/pdf`, valid header/structure, 1-10 pages, no forbidden active content; private generated key and safe metadata persist. |
| Wrong extension | Rejected even if MIME and magic bytes claim PDF. |
| Wrong MIME | Rejected even with `.pdf` and PDF bytes. |
| Wrong magic bytes | Rejected even with extension and MIME. |
| Empty file | Rejected without storage or metadata. |
| Oversized file | Exactly 5 MiB accepted if otherwise valid; one byte over rejected with `413`; chunk reader stops without unbounded memory. |
| Malformed/encrypted PDF | Structural parse failure, zero pages, over-ten pages, encryption, embedded files, JavaScript, `/OpenAction`, `/AA`, file-attachment annotations, RichMedia/Movie/Sound/Screen/3D annotations, or automatic actions rejected. |
| Malicious filename | Traversal separators, absolute paths, control characters, Unicode edge cases, excessive length, and blank names normalize to safe display metadata and never affect the key. |
| Checksum | SHA-256 matches stored bytes but never appears in API output or logs. |
| Storage key boundary | Implemented in Slice 4: canonical `drafts/{draft_uuid}/{document_uuid}.pdf` keys reject traversal, alternate separators, control characters, non-canonical UUIDs, unexpected extensions, and temporary-name collisions before storage access. |
| Private adapter contract | Implemented in Slice 4: local and fake adapters share save/open/delete/exists/enumeration behavior, duplicate saves never overwrite, failed writes clean temporary files, and enumeration returns stable relative keys only. |
| Validation service boundary | Implemented in Slice 5: validates bytes or binary streams and returns safe metadata only; no endpoint, storage write, database write, URL, or download route is introduced. |
| Initial storage failure | No active metadata; form answers preserved; safe retry response. |
| Metadata failure after save | Compensating delete runs; failed compensation becomes orphan-cleanup evidence. |
| Replacement success | Old document stays active until new validation/storage succeeds; transaction activates only the new metadata; old blob becomes cleanup-eligible. |
| Replacement failure | Old active metadata and blob remain authorized; no second active document. |
| Deletion | Authorization stops at logical deletion; physical failure is retryable; repeat does not restore access. |
| Unauthorized mutation | Another draft cannot read metadata, create/replace, or delete the singleton CV. |
| Orphan cleanup | Unreferenced keys younger than 24 hours are retained; older confirmed orphans are removed in bounded idempotent runs. |
| Public exposure | No API response, admin field, static route, or Nuxt route exposes a storage key or public URL. |

Malware scanning is not tested or claimed because Phase 3 does not implement it.

### Frontend Unit And Component Coverage

- CSRF bootstrap and header injection without exposing the draft cookie to JavaScript.
- Draft create, active resolve, restore after refresh, and vacancy-conflict normalization.
- 800 ms debounce, explicit flush before navigation, one in-flight save, retry, and cancellation.
- Server field errors mapped to existing summary and input associations.
- Generic expired/unavailable recovery that clears in-memory candidate data.
- Stale-version conflict preserves local text and requires a deliberate refresh/review action.
- Experience-entry add, edit, order, cap, validation, delete confirmation, and server rollback.
- Upload progress, cancel, retry, successful singleton-CV metadata, replacement preserving old
  metadata until success, and confirmed deletion.
- Loading, saving, saved, failed, retrying, uploaded, removed, conflict, and expired announcements.
- Disabled states, stable layout regions, focus movement, keyboard operation, and reduced-motion
  behavior.
- Fixture submission and status behavior remains explicitly simulated and isolated from real draft
  services.

### Browser Coverage

- Start, save candidate fields, refresh, and restore on every application route.
- Continue an existing same-vacancy draft and deliberately abandon a conflicting-vacancy draft.
- Direct cross-vacancy route navigation never mutates the authorized draft.
- Autosave failure and retry preserve typed values; stale conflict does not overwrite either tab.
- Expired draft offers a fresh start without revealing target existence.
- Valid upload reports progress and persists metadata across refresh.
- Invalid, oversized, and malformed uploads preserve candidate and experience data.
- Replacement failure preserves the old CV; replacement success and deletion update review state.
- Experience-entry CRUD works by keyboard and at 320 px without horizontal overflow.
- Error summary, grouped controls, upload region, conflict notice, and destructive confirmations
  receive correct focus and accessible descriptions.
- Touch operation does not depend on hover; reduced-motion mode avoids smooth/ornamental motion.
- Final submission and status remain visibly simulated and no Phase 4 API is called.

## SQLite And PostgreSQL Boundary

SQLite remains appropriate for serializer, service, API, cleanup, storage-adapter, and most model
tests. It can exercise the existing check and partial-unique behavior used by the local project.

The following evidence must be repeated on PostgreSQL before production-readiness claims:

- `select_for_update` behavior for simultaneous save, abandon, upload, replace, and delete;
- stale-version losers and no lost updates across transactions;
- concurrent five-entry cap and unique entry position;
- conditional one-active-document uniqueness under concurrent replacement;
- generated check constraints and migration SQL;
- transaction/on-commit compensation behavior with the production database driver;
- cleanup batch locking if parallel cleanup is ever allowed.

Phase 3 can be implemented with SQLite locally, but a skipped PostgreSQL check must remain an
explicit release risk. Creating or connecting a PostgreSQL service requires separate approval.
Suitable later verification environments include a free local PostgreSQL or Docker runtime, or a
GitHub Actions service container.

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
