# Testing Strategy

Phase 0 defines the test plan only. No tests exist yet.

## Backend Unit And Integration Tests

Planned coverage:

- Active vacancy rules.
- Closed vacancy rules.
- Draft creation.
- Draft token authorization.
- One-active-draft-per-browser conflict handling.
- Same-vacancy draft creation restores the current draft instead of creating another.
- Continue-existing-draft never creates a new draft.
- Abandon deletes the draft document and clears authorization before a new draft is created.
- Draft cookie loss and expiration behavior.
- Draft expiration.
- Application validation.
- Atomic submission.
- Duplicate submission under concurrent requests and the database constraint.
- Upload size limits.
- Non-PDF file rejected.
- Browser MIME, extension, PDF signature, and inspected-content mismatch handling.
- Second active CV for the same draft is rejected until the first is removed.
- Invalid PDF signature and malformed PDF rejection.
- Document access authorization.
- Throttling.
- Status lookup enumeration resistance.
- Status lookup secret hashing and non-logging.
- Application reference not accepted as authorization.
- Retention cleanup.
- Privacy-safe logging.
- Admin permissions.
- Least-privilege admin document access.
- Allowed and rejected transitions for `submitted`, `under_review`, and `closed`.

## Frontend Unit And Component Tests

Planned coverage:

- Field validation.
- Step navigation.
- Progress state.
- Draft serialization.
- Draft restoration.
- Upload state.
- Upload cancellation.
- API validation mapping.
- Review summary.
- Duplicate-submission lock.
- Recoverable errors.
- Reduced-motion behavior.
- Keyboard interaction.

## Playwright Flows

Planned flows:

- Vacancy discovery.
- Vacancy detail.
- Starting an application.
- Completing all steps.
- Uploading a valid CV.
- Recovering from invalid upload.
- Reviewing data.
- Submitting.
- Viewing confirmation.
- Keyboard-only completion.
- Mobile completion.
- Preserving entered data after recoverable API failure.
- Private status lookup.
- Status lookup response excludes internal notes, rankings, staff identities, and rejection reasoning.
- Accessibility scanning.

## Accessibility Checks

Automated checks are helpful but not enough. Manual checks should include:

- Keyboard-only completion.
- Visible focus review.
- Screen-reader label review.
- Error summary and field association.
- Reduced-motion review.
- Mobile touch and keyboard behavior.

## Security Review

Security review should focus on:

- Draft authorization.
- Document access.
- Upload validation.
- Status lookup enumeration.
- CSRF.
- XSS through vacancy content.
- Admin permissions.
- Logging restrictions.
- Environment handling.

## Test Data Rules

Use obviously fictional values:

- `Avery Example`
- `avery.candidate@example.test`
- `AF-9Q2K-M7P4`
- `slk_9Wn6zQp4v2T8mR7cX5bL3kY1`
- `avery-example-cv.pdf`

Do not use real CVs, real names, real emails, or real phone numbers.

## Quality Gates By Phase

| Phase | Required Checks |
| --- | --- |
| Phase 3 | Frontend lint/typecheck/build once scaffold exists, basic component tests. |
| Phase 4 | Form validation tests and Playwright happy path. |
| Phase 5 | Backend pytest, Ruff, migration consistency, Django system checks. |
| Phase 6 | Upload and draft security tests. |
| Phase 7 | End-to-end submission and status lookup tests. |
| Phase 8 | Accessibility, security, and performance hardening checks. |
| Phase 9 | Docker image build and CI workflow checks. |

No command should be reported as passing until it has actually run.
