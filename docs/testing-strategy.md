# Testing Strategy

Testing is split between the implemented Phase 1 frontend and the planned backend.

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

## Planned Backend Tests

- Active and closed vacancy rules.
- Draft creation, authorization, restoration, expiration, abandonment, and cleanup.
- Server-side field validation and privacy-safe error mapping.
- Atomic submission and duplicate protection under concurrency.
- PDF extension, size, signature, content, malformed input, storage name, and authorization checks.
- Status secret hashing, non-logging, throttling, and enumeration resistance.
- Retention cleanup, staff permissions, and allowed application transitions.

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
