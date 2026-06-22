# API Contract

Phase 2 implements `/api/v1/health/` and the two read-only vacancy endpoints. All draft, document,
submission, and status endpoints below remain proposed. Represent the implemented contract with
OpenAPI in a later phase.

## Principles

- Version all public API routes under `/api/v1/`.
- Use server-side validation as the authority.
- Avoid numeric IDs as proof of ownership.
- Keep candidate endpoints anonymous but rate limited.
- Return generic errors where detailed errors would help enumeration.
- Keep document access private.
- Use same-origin cookies for draft authorization when implemented.
- Keep `application_reference` separate from `status_lookup_secret`; the readable reference is not confidential and is not an authorization credential.

## Endpoints

### Health

| Method | Path | Purpose | Status |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health/` | Return `{ "status": "ok" }` without configuration details. | Implemented |

### Vacancies

| Method | Path | Purpose | Status |
| --- | --- | --- | --- |
| `GET` | `/api/v1/vacancies/` | List published, non-expired vacancies. | Implemented |
| `GET` | `/api/v1/vacancies/{slug}/` | Return published vacancy detail. | Implemented |

Mutation methods are not exposed for vacancies.

### Application Drafts

Status: planned; no route is implemented.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/application-drafts/` | Create draft for a vacancy and set the active-draft cookie. |
| `GET` | `/api/v1/application-drafts/{draft_id}/` | Restore draft after authorization. |
| `PATCH` | `/api/v1/application-drafts/{draft_id}/` | Update draft fields. |
| `DELETE` | `/api/v1/application-drafts/{draft_id}/` | Abandon draft and delete draft documents. |

The `{draft_id}` is not proof of ownership. Draft access also requires the server-generated secret. Version one allows one active anonymous draft per browser.

`POST /api/v1/application-drafts/` has these canonical outcomes:

- No active-draft credential presented: create one and return `201`.
- Valid active draft for the requested vacancy: restore it and return `200`; do not create another.
- Valid active draft for another vacancy: return `409 active_draft_conflict` so the interface can offer continue or abandon; do not create another.
- Invalid or expired active-draft credential presented to the create endpoint: return a generic safe response, clear the unusable cookie when appropriate, and do not create a draft in the same request.
- Continue: restore the existing draft and navigate to its vacancy flow.
- Abandon: authorize and delete the existing draft and its document, clear the credential, then permit a new create request.
- For restore, update, delete, or submit requests that target a draft, a missing, invalid, or expired credential returns a generic safe response and does not reveal whether another draft exists.

### Documents

Status: planned; no route or storage behavior is implemented.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/application-drafts/{draft_id}/documents/` | Upload CV for a draft. |
| `DELETE` | `/api/v1/application-drafts/{draft_id}/documents/{document_id}/` | Remove draft document. |

Version one permits one active CV per draft. The upload endpoint accepts PDF only, enforces the 5 MB maximum, performs server-side signature/content inspection, and stores the file privately under a generated name. A second active document is rejected until the candidate removes the current one.

### Submission

Status: planned; no route is implemented.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/application-drafts/{draft_id}/submit/` | Validate and atomically submit. |

### Status Lookup

Status: planned; no route is implemented.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/application-status/lookup/` | Return minimal status for application reference plus status lookup secret. |

## Error Shape

```json
{
  "error": {
    "code": "validation_error",
    "message": "Check the highlighted fields.",
    "fields": {
      "email": ["Enter an email address in the format name@example.com."]
    },
    "request_id": "req_01JXAMPLE000000000000000"
  }
}
```

Rules:

- `message` is safe to show to candidates.
- `fields` maps server validation to inputs.
- `request_id` helps support without exposing internals.
- Internal exception details are not returned.

## Example Draft Creation

Request:

```http
POST /api/v1/application-drafts/
Content-Type: application/json

{
  "vacancy_slug": "frontend-developer"
}
```

Response:

```json
{
  "draft_id": "4de2b191-1a54-4a48-b4ff-799e6b900102",
  "vacancy": {
    "slug": "frontend-developer",
    "title": "Frontend Developer"
  },
  "expires_at": "2026-06-21T09:00:00Z"
}
```

The backend sets an appropriately protected same-origin HttpOnly cookie containing the active-draft credential. Only its secure hash is stored server-side. The frontend must not store the credential in localStorage. Cookie attributes and lifetime are finalized during backend implementation.

## Example Submission Response

```json
{
  "application_reference": "AF-9Q2K-M7P4",
  "status_lookup_secret": "slk_9Wn6zQp4v2T8mR7cX5bL3kY1",
  "status_lookup_path": "/application/status",
  "submitted_at": "2026-06-14T09:00:00Z"
}
```

The `status_lookup_secret` is delivered in the successful submission response for immediate confirmation display because email delivery is out of scope. The response must use `Cache-Control: no-store`; the secret must not appear in a URL, log, analytics event, or localStorage. The frontend holds it only in memory for the confirmation flow. It is not recoverable through self-service in version one.

## Example Status Lookup Request

```json
{
  "application_reference": "AF-9Q2K-M7P4",
  "status_lookup_secret": "slk_9Wn6zQp4v2T8mR7cX5bL3kY1"
}
```

Email is not used as a status secret. The API should return the same generic failure for wrong reference, wrong secret, revoked secret, expired credential, or rate-limited abuse.

A successful lookup returns only the candidate-facing status label, vacancy title, submitted date, and minimal next-step text. It never returns internal notes, ranking, staff identities, or rejection reasoning.

## Status Codes

| Code | Meaning |
| --- | --- |
| `200` | Request succeeded. |
| `201` | Draft or resource created. |
| `204` | Delete succeeded. |
| `400` | Malformed request. |
| `401` | Draft secret missing or invalid. |
| `403` | Authenticated but not allowed. |
| `404` | Resource missing or intentionally hidden. |
| `409` | Duplicate submission or invalid state transition. |
| `413` | Upload too large. |
| `415` | Unsupported file type. |
| `422` | Field validation failed. |
| `429` | Rate limit exceeded. |

## Unresolved

- Exact cookie name and lifetime.
- Whether draft response returns all form data or only step-specific data.
- Exact OpenAPI tooling.
