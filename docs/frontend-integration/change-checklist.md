# Frontend Change Checklist

## Before Changes

- Read `docs/frontend-integration/README.md`.
- Inspect Git status and preserve uncommitted work.
- Classify the task as visual, integration, API, backend, or database scope.
- Confirm no backend change is needed for frontend-only work.
- Identify affected API routes.
- Identify security requirements: cookies, CSRF, ETags, privacy, and upload behavior.
- Identify required tests from [testing contract](testing-contract.md).

## During Changes

- Keep API calls in typed API modules.
- Keep page components free from duplicated low-level fetch logic when the architecture provides
  services/composables.
- Preserve relative `/api/v1/` paths.
- Preserve cookies and CSRF.
- Preserve `ETag`/`If-Match` behavior.
- Preserve local input after validation, network, storage, and conflict failures.
- Preserve accessible labels, focus, keyboard operation, and reduced-motion behavior.
- Do not introduce localStorage or sessionStorage candidate persistence.
- Do not touch models or migrations for frontend-only work.

## Before Completion

- Run required commands.
- Run real full-stack tests when integration changed.
- Compare Django URL configuration against endpoint documentation.
- Compare serializers against documented request and response shapes.
- Compare settings and validators against documented limits.
- Compare backend error codes and envelopes against frontend error mapping.
- Compare `ETag` and `If-Match` behavior against mutation clients.
- Compare CSRF and cookie settings against the security contract.
- Compare full-stack tests against the documented workflow.
- Review browser network requests for `/api/v1/...`.
- Confirm no raw credential appears in code, logs, snapshots, or docs.
- Confirm no CV public URL appears.
- Confirm no candidate data appears in logs.
- Confirm deferred submission/status behavior remains deferred.
- Review the complete Git diff.
- Stop test servers.
- Remove generated test artifacts only after confirming they are reproducible and untracked.
- Report limitations truthfully.

## Stop And Escalate When

- A new persisted field is needed.
- An endpoint response must change.
- A security header or cookie policy must change.
- A migration appears necessary.
- A new document type is requested.
- A public file URL is requested.
- Cross-origin deployment is proposed.
- Candidate accounts are proposed.
- Submission or status APIs are requested.
- A test requires weakening existing security.

## Contract Drift Check

When backend URLs, serializers, response fields, status codes, required headers, cookie settings,
CSRF behavior, validation limits, upload rules, ETag behavior, or machine-readable error codes
change, update the frontend integration contract, relevant frontend clients, contract tests, and
documentation in the same change.

A backend contract change is incomplete until:

- the implementation,
- frontend integration,
- automated tests, and
- frontend integration documentation

agree with one another.
