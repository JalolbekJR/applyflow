# API Contract

Phase 2 implements health and read-only vacancy endpoints. Phase 3 adds authorized application
drafts, bounded experience entries, and private CV upload and mutation. Final submission and public
status lookup remain Phase 4 work and are not part of this contract.

This file is the backend implementation contract. Frontend replacement work should start with the
frontend-facing contract in [docs/frontend-integration/api-contract.md](frontend-integration/api-contract.md)
and the security rules in [docs/frontend-integration/security-contract.md](frontend-integration/security-contract.md).
If the two documents appear to conflict, verify the current Django URL configuration, views,
serializers, services, and tests before changing either contract.

## Principles

- Version candidate APIs under `/api/v1/`.
- Keep every candidate API same-origin. Do not add CORS middleware for Phase 3.
- Treat server-side validation and object authorization as authoritative.
- Use a same-origin HttpOnly cookie for anonymous draft ownership; never use a numeric or UUID
  identifier as proof of ownership.
- Require Django CSRF protection on every unsafe request, including anonymous draft creation.
- Use a separate short-lived HttpOnly creation-key cookie and a unique keyed database digest so
  concurrent initial requests and lost-response retries resolve one logical draft.
- Return the existing API error envelope and use the same generic `draft_unavailable` response for
  missing, incorrect, expired, abandoned, or cross-draft credentials.
- Return `Cache-Control: no-store` on CSRF, draft, candidate, experience, and document responses.
- Never return a draft credential, credential hash, storage key, checksum, or public document URL in
  JSON.
- Return `ETag: "draft-<version>"` on every authorized draft read or mutation response.
- Require `If-Match: "draft-<expected-version>"` on every unsafe draft mutation. Missing `If-Match`
  returns `428 draft_version_required`; a stale version returns `409 draft_conflict`; the client
  must re-fetch before retrying.

## Implemented Phase 2 Endpoints

| Method | Path                        | Purpose                                                    |
| ------ | --------------------------- | ---------------------------------------------------------- |
| `GET`  | `/api/v1/health/`           | Return `{ "status": "ok" }` without configuration details. |
| `GET`  | `/api/v1/vacancies/`        | List published, non-expired vacancies.                     |
| `GET`  | `/api/v1/vacancies/{slug}/` | Return published vacancy detail.                           |

Vacancy mutation methods are not exposed.

## Phase 3 Endpoint Summary

All draft and document paths require the `applyflow_draft` ownership cookie unless marked
otherwise. `GET` and `HEAD` are safe and do not require a CSRF header. Every `POST`, `PATCH`, `PUT`,
and `DELETE` requires `X-CSRFToken`.

| Method   | Path                                                                 | Purpose                                                                                                                                | Success                             | Expected errors                                                                                                                                                                                                 | Idempotency                                                                                                                                                                                                                                                                |
| -------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET`    | `/api/v1/csrf/`                                                      | Set the CSRF cookie, establish a short-lived draft-creation key when needed, and return a masked token for the request header.         | `200`                               | `500`                                                                                                                                                                                                           | Safe and repeatable.                                                                                                                                                                                                                                                       |
| `GET`    | `/api/v1/application-drafts/active/`                                 | Resolve the draft authorized by the ownership cookie.                                                                                  | `204` no cookie, `200` active draft | `404 draft_unavailable`                                                                                                                                                                                         | Safe and repeatable; does not extend expiry. Invalid, expired, revoked, or malformed ownership clears the cookie.                                                                                                                                                          |
| `POST`   | `/api/v1/application-drafts/`                                        | Create a draft for a vacancy or resolve the authorized draft for that vacancy.                                                         | `201` created, `200` resumed        | `404 vacancy_unavailable`, `404 draft_unavailable`, `409 active_draft_conflict`, `422 validation_error`                                                                                                         | Idempotent for the same valid ownership cookie or unexpired creation key and vacancy. A lost create response can be retried with the same creation key without creating another row. An invalid ownership cookie is cleared and never creates a draft in the same request. |
| `GET`    | `/api/v1/application-drafts/{draft_id}/`                             | Read the authorized draft aggregate.                                                                                                   | `200`                               | `404 draft_unavailable`                                                                                                                                                                                         | Safe and repeatable; does not extend expiry.                                                                                                                                                                                                                               |
| `PATCH`  | `/api/v1/application-drafts/{draft_id}/candidate/`                   | Partially update candidate fields.                                                                                                     | `200`                               | `404 draft_unavailable`, `409 draft_conflict`, `422 validation_error`, `428 draft_version_required`                                                                                                             | Data-idempotent for the current `If-Match`. An accepted mutation increments `version` once. Re-fetch after an ambiguous network result.                                                                                                                                    |
| `PATCH`  | `/api/v1/application-drafts/{draft_id}/experience/`                  | Partially update experience level, skills, message, and acknowledgement.                                                               | `200`                               | `404 draft_unavailable`, `409 draft_conflict`, `422 validation_error`, `428 draft_version_required`                                                                                                             | Same as candidate update.                                                                                                                                                                                                                                                  |
| `POST`   | `/api/v1/application-drafts/{draft_id}/experiences/`                 | Create one bounded employment entry.                                                                                                   | `201`                               | `404 draft_unavailable`, `409 draft_conflict`, `422 validation_error`, `428 draft_version_required`                                                                                                             | Not automatically repeatable. Disable duplicate activation and re-fetch before retrying after an unknown result.                                                                                                                                                           |
| `PATCH`  | `/api/v1/application-drafts/{draft_id}/experiences/{experience_id}/` | Partially update an owned employment entry.                                                                                            | `200`                               | `404 draft_unavailable`, `409 draft_conflict`, `422 validation_error`, `428 draft_version_required`                                                                                                             | Data-idempotent for the current `If-Match`.                                                                                                                                                                                                                                |
| `DELETE` | `/api/v1/application-drafts/{draft_id}/experiences/{experience_id}/` | Delete an owned employment entry.                                                                                                      | `204`                               | `404 draft_unavailable`, `409 draft_conflict`, `428 draft_version_required`                                                                                                                                     | First request deletes; a repeat returns the generic `404`.                                                                                                                                                                                                                 |
| `DELETE` | `/api/v1/application-drafts/{draft_id}/`                             | Abandon and revoke the draft, remove experience entries, logically retire active draft documents, and queue physical document cleanup. | `204`                               | `404 draft_unavailable`, `409 draft_conflict`, `428 draft_version_required`                                                                                                                                     | First request revokes the secret and clears the cookie. Cleanup completes candidate-field scrubbing and safe shell removal. A repeat is safe and returns the generic `404`.                                                                                                |
| `GET`    | `/api/v1/application-drafts/{draft_id}/documents/cv/`                | Retrieve authorized singleton CV metadata only.                                                                                        | `200`                               | `404 draft_unavailable`                                                                                                                                                                                         | Safe and repeatable.                                                                                                                                                                                                                                                       |
| `PUT`    | `/api/v1/application-drafts/{draft_id}/documents/cv/`                | Create or replace the authorized singleton CV after the new file passes validation.                                                    | `201` created, `200` replaced       | `404 draft_unavailable`, `409 draft_conflict`, `413 upload_too_large`, `415 unsupported_file_type`, `422 validation_error`, `422 invalid_pdf`, `428 draft_version_required`, `503 document_storage_unavailable` | Replacement is one logical operation. Re-fetch after an unknown result; never blindly resend file bytes.                                                                                                                                                                   |
| `DELETE` | `/api/v1/application-drafts/{draft_id}/documents/cv/`                | Logically delete the authorized singleton CV and schedule physical deletion.                                                           | `204`                               | `404 draft_unavailable`, `409 draft_conflict`, `428 draft_version_required`                                                                                                                                     | First request deletes; a repeat returns the generic `404`.                                                                                                                                                                                                                 |

Phase 3 does not expose document contents. There is no candidate or public download endpoint, no
storage URL, and no staff mutation API. A later staff download, if approved, must be an
authenticated, object-authorized streaming response with safe attachment headers.

## CSRF Bootstrap

Request:

```http
GET /api/v1/csrf/
Accept: application/json
```

Response:

```json
{
  "csrf_token": "masked-django-csrf-token"
}
```

The response generates and returns Django's masked CSRF token, sets or refreshes the normal Django
CSRF cookie, establishes a short-lived HttpOnly creation-key cookie when one is absent or unusable,
preserves `Vary: Cookie`, and uses `Cache-Control: no-store`. The frontend keeps the masked token in
memory, sends it as `X-CSRFToken` on unsafe same-origin requests, and reacquires a fresh token after
a CSRF rejection when that retry is appropriate. The endpoint is not a draft-authentication
endpoint. The CSRF cookie, creation-key cookie, and draft ownership cookie have separate purposes,
and none of their raw values is returned as an ownership credential in JSON.

## Draft Aggregate

A successful create, resolve, or read returns the same aggregate shape:

```json
{
  "draft": {
    "id": "4de2b191-1a54-4a48-b4ff-799e6b900102",
    "status": "active",
    "version": 3,
    "vacancy": {
      "slug": "frontend-developer",
      "title": "Frontend Developer"
    },
    "candidate": {
      "full_name": "Avery Example",
      "email": "avery.candidate@example.test",
      "phone": "",
      "portfolio_url": "https://example.test/avery",
      "preferred_contact_method": "email"
    },
    "experience": {
      "experience_level": "mid_level",
      "skills": ["Vue 3", "TypeScript", "Accessibility"],
      "optional_message": "",
      "consent_acknowledged": true,
      "consent_version": "privacy-v1"
    },
    "experience_entries": [
      {
        "id": "38e7a7ce-1c4f-4861-b61d-a69a0a513312",
        "organization": "Example Studio",
        "role_title": "Frontend Developer",
        "start_month": "2024-01",
        "end_month": null,
        "is_current": true,
        "summary": "Built accessible fictional product interfaces.",
        "position": 0
      }
    ],
    "document": {
      "original_name_display": "avery-example-cv.pdf",
      "detected_content_type": "application/pdf",
      "size": 42137,
      "uploaded_at": "2026-06-22T09:00:00Z"
    },
    "last_activity_at": "2026-06-22T09:00:00Z",
    "expires_at": "2026-06-29T09:00:00Z"
  }
}
```

The aggregate deliberately excludes `secret_hash`, `credential_revoked_at`, `email_normalized`,
`storage_key`, `sha256`, and physical-deletion state.

Every authorized draft response also returns:

```http
ETag: "draft-3"
```

`expires_at` is the effective expiry boundary for candidate access. It never exceeds seven days
after the last successful mutation, thirty days after draft creation, or the vacancy application
deadline.

## Draft Creation And Conflict

Request:

```json
{
  "vacancy_slug": "frontend-developer"
}
```

Canonical outcomes:

- No ownership cookie: create an active draft, set the cookie, and return `201`.
- Valid active draft for the requested vacancy: return the existing aggregate with `200` and do not
  create or rotate credentials.
- Valid active draft for another vacancy: return `409 active_draft_conflict`. The frontend can call
  the active-draft endpoint to render the authorized existing vacancy and offer continue or abandon.
- Invalid, expired, abandoned, or revoked cookie: clear it and return generic
  `404 draft_unavailable`; do not create a replacement in the same request.
- Missing or unavailable vacancy: return `404 vacancy_unavailable` without creating a draft.

The frontend may retry creation only after the unusable cookie has been cleared and the candidate
chooses to start again. This prevents an attacker-supplied cookie from being adopted as a new
credential.

The active-draft bootstrap endpoint behaves as follows:

- No ownership cookie: return `204` and do not create a draft.
- Valid active draft: return `200` with the aggregate and `ETag`.
- Malformed, invalid, expired, or revoked cookie: clear it and return generic
  `404 draft_unavailable`.

## Mutation Requests

Every unsafe mutation sends the current draft version in the `If-Match` header:

```http
If-Match: "draft-3"
```

If `If-Match` is missing, return `428 draft_version_required`. If the draft has already advanced,
return `409 draft_conflict` and do not apply a partial change.

Every successful mutation returns a fresh:

```http
ETag: "draft-<new-version>"
```

Candidate example:

```json
{
  "full_name": "Avery Example",
  "preferred_contact_method": "email"
}
```

Experience summary example:

```json
{
  "experience_level": "mid_level",
  "skills": ["Vue 3", "TypeScript", "Accessibility"],
  "optional_message": "Fictional context for the application.",
  "consent_acknowledged": true,
  "consent_version": "privacy-v1"
}
```

Employment-entry example:

```json
{
  "organization": "Example Studio",
  "role_title": "Frontend Developer",
  "start_month": "2024-01",
  "end_month": null,
  "is_current": true,
  "summary": "Built accessible fictional product interfaces.",
  "position": 0
}
```

Employment entries are optional, capped at five per draft, and bounded to short structured fields.
They do not replace the CV or turn the form into a full employment-history or resume-builder
workflow. The existing free-text experience summary remains optional alongside zero to five ordered
entries.

Incomplete drafts may save valid partial fields. Cross-field validation still applies when both
fields are present, and Phase 4 performs final completeness and consent validation before
submission.

## Document Requests

Singleton CV create and replacement use `multipart/form-data` with:

- `file`: one PDF.

No additional form fields or additional files are accepted. The draft cookie, route UUID, and
`If-Match` precondition are checked before multipart parsing and PDF validation begin.

`PUT /api/v1/application-drafts/{draft_id}/documents/cv/` creates the active CV when none exists
and replaces it when one already exists. No public document identifier is required for normal
candidate operations. The response contains only the safe document metadata shown in the draft
aggregate plus refreshed expiry timestamps. It never contains a storage path, checksum, internal
document UUID, or download URL.

Replacement preserves the current active document until the new file has passed validation and has
been stored. A failed replacement leaves the previous document active. Delete makes the document
unavailable before physical storage cleanup runs; failed physical deletion remains retryable via
`storage_deleted_at` metadata that is never returned to candidates. Phase 3 exposes metadata only:
there is no candidate, public, or staff download endpoint and no public storage URL.

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
- `request_id` is generated once per request, returned in the `X-Request-ID` response header, and
  reused in the error body.
- Internal exceptions, candidate text, cookie contents, hashes, filenames, checksums, and storage
  keys are not returned.
- A request for another draft, experience entry, or document receives the same
  `404 draft_unavailable` envelope as a missing resource.
- CSRF failure returns `403 csrf_failed` through the same envelope without disabling middleware.

## Status Codes

| Code  | Meaning in Phase 3                                                          |
| ----- | --------------------------------------------------------------------------- |
| `200` | Read, restore, update, or replacement succeeded.                            |
| `201` | Draft, experience entry, or initial document was created.                   |
| `204` | Abandonment or deletion succeeded.                                          |
| `400` | Malformed JSON, multipart data, or request shape.                           |
| `403` | CSRF validation failed. Object authorization failures do not use this code. |
| `404` | Vacancy unavailable or draft/resource intentionally hidden.                 |
| `409` | Active-vacancy mismatch, stale draft version, or invalid resource state.    |
| `413` | Request or file exceeds configured limits.                                  |
| `415` | Declared or detected file type is unsupported.                              |
| `422` | Candidate, experience, or PDF content validation failed.                    |
| `428` | An unsafe mutation omitted the required `If-Match` header.                  |

## Explicitly Deferred

- `POST /api/v1/application-drafts/{draft_id}/submit/`.
- Application-reference or status-secret generation.
- `POST /api/v1/application-status/lookup/`.
- Candidate accounts or cross-device draft recovery.
- Candidate, public, or staff document download.
- Staff mutation APIs.
- OpenAPI tooling selection.
