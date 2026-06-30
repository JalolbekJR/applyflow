# Privacy Model

This is a product privacy plan, not legal advice. Real recruitment use requires legal review of notices, consent, retention, and deletion obligations.

## Data Minimization

ApplyFlow collects only fields needed for a small application flow:

- Full name for staff review.
- Email for contact and duplicate-submission checks.
- Optional phone only if the candidate accepts phone contact.
- One profile link instead of multiple repeated fields.
- Preferred contact method to avoid unwanted contact.
- CV as the primary experience source.
- Experience level and skills as light structured review data.
- Optional message for context not present in the CV.
- Consent version for auditability.

## Field Purpose

See [field inventory](field-inventory.md) for purpose, validation, privacy classification, persistence, and logging restrictions.

## Draft Retention

Phase 3 rule:

- Drafts expire after seven days without a successful meaningful mutation, thirty days after
  creation, or at the vacancy application deadline, whichever comes first.
- Candidate, experience, experience-entry, and CV mutations refresh `last_activity_at`,
  `expires_at`, and the ownership-cookie lifetime together, but never beyond the thirty-day
  absolute limit or vacancy deadline. Reads do not extend retention.
- Expiry or confirmed abandonment immediately revokes access, scrubs structured candidate fields,
  deletes experience entries, blanks original filename display metadata, and makes the CV logically
  unavailable.
- Physical document deletion is retryable. A scrubbed draft shell may remain only while its private
  storage key is needed for cleanup, then the shell and metadata are hard-deleted.
- Abandonment, expiry, revocation, and invalid ownership clear the ownership cookie.
- Stale unreferenced storage objects receive a 24-hour grace period before orphan cleanup so an
  in-flight or compensating transaction is not deleted prematurely.

The seven-day period is the Phase 3 engineering default, not a legally validated retention policy.
Real recruitment use still requires legal and organizational review.

## Submitted Application Retention

Submitted applications require a retention period. This remains undecided because real retention depends on legal and hiring policy requirements.

Current recommendation:

- Define a short retention period for fictional test data.
- Do not use real candidate data.
- Add deletion and export procedures before real use.

## Document Retention

CV documents follow the submitted application retention policy after Phase 4. Draft documents are
logically removed with expired or abandoned drafts and physically removed by retryable cleanup.
Phase 3 has no candidate, public, or staff download endpoint and no public storage URL.

## Deletion Workflow

Later implementation should support:

- Admin-initiated deletion for demo data.
- System deletion for expired drafts.
- Document deletion tied to application deletion.
- Audit events that record deletion category without personal data.

Candidate self-service deletion is not part of version one.

## Consent Versioning

Store the consent version accepted at submission. If privacy wording changes, a new version should be recorded for future submissions.

## Status Lookup

Status lookup remains Phase 4. The Phase 3 frontend does not fabricate an application reference,
status lookup secret, or successful status result.

The planned Phase 4 design uses a readable `application_reference` and a separate high-entropy
`status_lookup_secret`. The reference helps support; the secret authorizes status access. Email is
not treated as a secret. Responses should reveal only:

- Public status label.
- Vacancy title.
- Submitted date.
- Minimal next-step text.

Do not show:

- Internal notes.
- Staff names.
- Ranking.
- Rejection reasoning.
- Automated decision output.
- Other candidate data.

## Access Control

- Public vacancy content is public.
- Drafts require draft authorization.
- Submitted applications require authenticated, least-privilege staff authorization.
- Documents require explicit object-level staff authorization before storage access.
- Status lookup requires correct lookup credentials.

Phase 3 backend slices implement candidate draft authorization and authorized CV metadata, upload,
replacement, and deletion. Slice 7 connects the candidate frontend to the real vacancy, draft,
experience-entry, CV, and abandonment APIs. Status-secret lookup, final submission, staff document
download, cleanup processing, production deployment, and runtime multi-company configuration remain
unimplemented. ApplyFlow still must not collect real candidate data until the remaining privacy,
legal, accessibility, operational, and production-readiness gates are complete.

Phase 3 ownership is one active draft per browser. The browser receives a host-only HttpOnly cookie
containing a versioned draft UUID plus a 256-bit random secret; only the secret hash is stored. The
cookie is `Secure` outside local development, uses `SameSite=Lax`, and is restricted to draft API
paths. No localStorage, sessionStorage, browser fingerprint, or cross-device identity is collected.

## Logging Restrictions

Do not log:

- Full name.
- Email.
- Phone.
- CV contents.
- Original filename.
- Storage key.
- Draft secret.
- Status lookup secret.
- Candidate or experience request/response bodies.
- Cookie or CSRF token values.
- Credential hashes.
- Document checksum.

Application references may appear in support workflows, but they must not be treated as proof of ownership.

Allowed logs:

- Request ID.
- Event type.
- Result category.
- Vacancy ID.
- Actor type.
- Timestamp.
- Result or rejection category.
- HTTP status and duration.
- Opaque draft or document UUID only in restricted security events where incident correlation
  requires it.

Ordinary Phase 3 application logs do not collect browser fingerprints or persist source IP
addresses. If a future edge rate-limit or incident process retains network identifiers, it requires
its own purpose, access, and retention review.

Initial engineering retention targets are 14 days for ordinary application logs, 30 days for
restricted security-denial events, and 90 days for aggregate cleanup evidence. These targets are
not legal advice and must be reviewed before real recruitment use. Local development should avoid
persistent request logs and use only fictional candidate data.

## Test And Demo Data

Never use real candidate data in:

- Fixtures.
- Tests.
- Screenshots.
- Seed data.
- Documentation examples.
- Case-study visuals.

Use obviously fictional values.
