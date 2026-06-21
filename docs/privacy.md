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

Planned rule:

- Drafts expire after a short period, such as 7 days.
- Expired drafts are deleted by a cleanup process.
- Abandoned draft documents are deleted with the draft.

Any exact period is a proposed operational policy and requires legal and organizational review before real recruitment use. This project does not claim legal validation.

## Submitted Application Retention

Submitted applications require a retention period. This remains undecided because real retention depends on legal and hiring policy requirements.

Current recommendation:

- Define a short retention period for fictional test data.
- Do not use real candidate data.
- Add deletion and export procedures before real use.

## Document Retention

CV documents follow the submitted application retention policy. Draft documents are deleted with expired or abandoned drafts.

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

Status lookup uses a readable `application_reference` and a separate high-entropy `status_lookup_secret`. The reference helps support; the secret authorizes status access. Email is not treated as a secret. Responses reveal only:

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

Application references may appear in support workflows, but they must not be treated as proof of ownership.

Allowed logs:

- Request ID.
- Event type.
- Result category.
- Vacancy ID.
- Actor type.
- Timestamp.

## Test And Demo Data

Never use real candidate data in:

- Fixtures.
- Tests.
- Screenshots.
- Seed data.
- Documentation examples.
- Case-study visuals.

Use obviously fictional values.
