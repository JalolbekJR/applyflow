# Error Handling

API errors use a JSON envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Check the highlighted fields.",
    "fields": {
      "email": ["Enter a valid email address."]
    },
    "request_id": "req_fictional"
  }
}
```

The `message` is safe to show. `fields` maps server validation to controls. Unknown backend errors
must not become false success or empty data.

## Mapping Rules

| Error                     | Status       | Code                                    | Retry                                                  | Preserve local values                           | Clear draft state              | Candidate-facing behavior                        |
| ------------------------- | ------------ | --------------------------------------- | ------------------------------------------------------ | ----------------------------------------------- | ------------------------------ | ------------------------------------------------ |
| Field validation          | `422`        | `validation_error`                      | After correction                                       | Yes                                             | No                             | Focus error summary and mapped fields.           |
| Draft unavailable         | `404`        | `draft_unavailable`                     | Start over only                                        | Clear sensitive stale state when unrecoverable  | Yes for expired/unusable draft | Generic message; do not reveal object existence. |
| Active draft conflict     | `409`        | `active_draft_conflict`                 | Yes after user chooses                                 | Yes                                             | No                             | Show continue-or-abandon decision.               |
| Version conflict          | `409`        | `draft_conflict`                        | Re-fetch/review first                                  | Yes                                             | No                             | Stop mutation queue; do not overwrite silently.  |
| Missing version           | `428`        | `draft_version_required`                | Re-fetch first                                         | Yes                                             | No                             | Ask candidate to refresh/review the draft.       |
| CSRF failure              | `403`        | `csrf_failed`                           | Safe retry after token refresh for repeatable requests | Yes                                             | No                             | Reacquire token; do not disable CSRF.            |
| Invalid credential        | `404`        | `draft_unavailable`                     | Start over only                                        | Clear stale draft if active route depends on it | Yes                            | Same generic unavailable message.                |
| Vacancy unavailable       | `404`        | `vacancy_unavailable` or `not_found`    | No for same slug                                       | Yes                                             | No                             | Show application unavailable.                    |
| Upload too large          | `413`        | `upload_too_large`                      | Yes with smaller file                                  | Yes                                             | No                             | Show file error.                                 |
| Unsupported file type     | `415`        | `unsupported_file_type`                 | Yes with PDF                                           | Yes                                             | No                             | Show file error.                                 |
| Invalid PDF               | `422`        | `invalid_pdf`                           | Yes with different PDF                                 | Yes                                             | No                             | Show safe PDF recovery text.                     |
| Storage unavailable       | `503`        | `document_storage_unavailable`          | Later                                                  | Yes                                             | No                             | Show temporary upload failure.                   |
| Network failure           | `0`          | `network_failure`                       | Yes                                                    | Yes                                             | No                             | Preserve typed values and allow retry.           |
| Unexpected server error   | `500`        | `unexpected_error`                      | Later                                                  | Yes                                             | No                             | Show calm temporary failure.                     |
| Proxy/backend unavailable | `0` or `5xx` | `network_failure` or `unexpected_error` | Later                                                  | Yes                                             | No                             | Do not convert to empty vacancy/draft success.   |

## Focus And Recovery

- Validation errors focus the summary, then the relevant field.
- Upload errors stay near the CV upload group and preserve the previous accepted metadata.
- Conflict and unavailable states must be visible without relying on color.
- A server response that clears an unusable cookie is the only way the frontend indirectly clears
  the HttpOnly draft credential.
- The frontend must not clear a valid-looking local draft on a simple network failure.

## Generic Unavailable Rule

Wrong draft IDs, missing ownership, expired credentials, abandoned drafts, cross-draft access,
cross-entry access, and unauthorized CV metadata access all use generic unavailable behavior. Do not
surface more specific wording in a replacement frontend.
