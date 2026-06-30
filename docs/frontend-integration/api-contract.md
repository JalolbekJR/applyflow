# Frontend-Facing API Contract

The browser contract is relative, same-origin, versioned, and trailing-slash based:

```text
/api/v1/...
```

Frontend code must not rewrite browser calls to `/v1/...`. The Nuxt development proxy preserves the
full `/api/v1/...` path when forwarding to Django.

## Shared Rules

- JSON requests use `Content-Type: application/json`.
- CV upload uses `multipart/form-data` with one `file` field.
- Browser requests include cookies with `credentials: "include"` or equivalent.
- Unsafe requests send `X-CSRFToken` from `GET /api/v1/csrf/`.
- Draft mutations send `If-Match: "draft-<version>"`.
- Successful authorized draft responses return `ETag: "draft-<version>"`.
- Draft and document responses use `Cache-Control: no-store`.
- Candidate-facing errors use the envelope documented in [error handling](error-handling.md).

## Implemented Endpoints

| Method   | Path                                                                 | Purpose                                                         | Access                          | CSRF | Headers                   | Body                       | Success                                 | Important errors                                                                                                                                                                                                | Implementation                       | Tests                                                                               |
| -------- | -------------------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------- | ---- | ------------------------- | -------------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------- |
| `GET`    | `/api/v1/health/`                                                    | Health check                                                    | Public                          | No   | `Accept`                  | None                       | `200 {"status":"ok"}`                   | `500`                                                                                                                                                                                                           | `backend/config/api_views.py`        | `backend/tests/test_api.py`                                                         |
| `GET`    | `/api/v1/csrf/`                                                      | Set CSRF cookie, return masked token, establish creation cookie | Public                          | No   | `Accept`                  | None                       | `200 {"csrf_token": string}`            | `500`                                                                                                                                                                                                           | `backend/config/api_views.py`        | `backend/tests/test_draft_api.py`                                                   |
| `GET`    | `/api/v1/vacancies/`                                                 | List published, non-expired vacancies                           | Public                          | No   | `Accept`                  | None                       | `200 ApiVacancy[]`                      | `405` for mutation                                                                                                                                                                                              | `backend/apps/vacancies/views.py`    | `backend/tests/test_api.py`, `frontend/tests/e2e/slice7-fullstack.spec.ts`          |
| `GET`    | `/api/v1/vacancies/{slug}/`                                          | Read one published vacancy                                      | Public                          | No   | `Accept`                  | None                       | `200 ApiVacancy`                        | `404 not_found`                                                                                                                                                                                                 | `backend/apps/vacancies/views.py`    | `backend/tests/test_api.py`, `frontend/tests/e2e/slice7-fullstack.spec.ts`          |
| `GET`    | `/api/v1/application-drafts/active/`                                 | Resolve active draft from cookie                                | Draft cookie if present         | No   | `Accept`                  | None                       | `204` no draft, `200 ApiDraftAggregate` | `404 draft_unavailable` and cookie clear                                                                                                                                                                        | `backend/apps/applications/views.py` | `backend/tests/test_draft_api.py`, `frontend/tests/e2e/slice7-fullstack.spec.ts`    |
| `POST`   | `/api/v1/application-drafts/`                                        | Create or restore draft for a vacancy                           | Creation cookie or draft cookie | Yes  | `X-CSRFToken`             | `{"vacancy_slug": string}` | `201` created, `200` restored           | `404 vacancy_unavailable`, `404 draft_unavailable`, `409 active_draft_conflict`, `422 validation_error`                                                                                                         | `backend/apps/applications/views.py` | `backend/tests/test_draft_api.py`, `frontend/tests/e2e/slice7-fullstack.spec.ts`    |
| `GET`    | `/api/v1/application-drafts/{draft_id}/`                             | Read authorized draft aggregate                                 | Draft cookie                    | No   | `Accept`                  | None                       | `200 ApiDraftAggregate`                 | `404 draft_unavailable`                                                                                                                                                                                         | `backend/apps/applications/views.py` | `backend/tests/test_draft_api.py`                                                   |
| `DELETE` | `/api/v1/application-drafts/{draft_id}/`                             | Abandon draft and clear ownership                               | Draft cookie                    | Yes  | `X-CSRFToken`, `If-Match` | None                       | `204` with `ETag`                       | `404 draft_unavailable`, `409 draft_conflict`, `428 draft_version_required`                                                                                                                                     | `backend/apps/applications/views.py` | `backend/tests/test_draft_api.py`, `frontend/tests/e2e/slice7-fullstack.spec.ts`    |
| `PATCH`  | `/api/v1/application-drafts/{draft_id}/candidate/`                   | Update candidate fields                                         | Draft cookie                    | Yes  | `X-CSRFToken`, `If-Match` | Candidate patch JSON       | `200 ApiDraftAggregate`                 | `404 draft_unavailable`, `409 draft_conflict`, `422 validation_error`, `428 draft_version_required`                                                                                                             | `backend/apps/applications/views.py` | `backend/tests/test_draft_api.py`, `frontend/tests/e2e/slice7-fullstack.spec.ts`    |
| `PATCH`  | `/api/v1/application-drafts/{draft_id}/experience/`                  | Update summary experience fields                                | Draft cookie                    | Yes  | `X-CSRFToken`, `If-Match` | Experience patch JSON      | `200 ApiDraftAggregate`                 | Same as candidate patch                                                                                                                                                                                         | `backend/apps/applications/views.py` | `backend/tests/test_draft_api.py`, `frontend/tests/e2e/slice7-fullstack.spec.ts`    |
| `POST`   | `/api/v1/application-drafts/{draft_id}/experiences/`                 | Create employment entry                                         | Draft cookie                    | Yes  | `X-CSRFToken`, `If-Match` | Entry JSON                 | `201 ApiDraftAggregate`                 | `404 draft_unavailable`, `409 draft_conflict`, `422 validation_error`, `428 draft_version_required`                                                                                                             | `backend/apps/applications/views.py` | `backend/tests/test_draft_api.py`, `frontend/tests/e2e/slice7-fullstack.spec.ts`    |
| `PATCH`  | `/api/v1/application-drafts/{draft_id}/experiences/{experience_id}/` | Update employment entry                                         | Draft cookie                    | Yes  | `X-CSRFToken`, `If-Match` | Entry patch JSON           | `200 ApiDraftAggregate`                 | Same as entry create                                                                                                                                                                                            | `backend/apps/applications/views.py` | `backend/tests/test_draft_api.py`                                                   |
| `DELETE` | `/api/v1/application-drafts/{draft_id}/experiences/{experience_id}/` | Delete employment entry                                         | Draft cookie                    | Yes  | `X-CSRFToken`, `If-Match` | None                       | `204` with `ETag`                       | `404 draft_unavailable`, `409 draft_conflict`, `428 draft_version_required`                                                                                                                                     | `backend/apps/applications/views.py` | `backend/tests/test_draft_api.py`                                                   |
| `GET`    | `/api/v1/application-drafts/{draft_id}/documents/cv/`                | Read CV metadata through draft aggregate                        | Draft cookie                    | No   | `Accept`                  | None                       | `200 ApiDraftAggregate`                 | `404 draft_unavailable`                                                                                                                                                                                         | `backend/apps/documents/views.py`    | `backend/tests/test_document_api.py`                                                |
| `PUT`    | `/api/v1/application-drafts/{draft_id}/documents/cv/`                | Upload or replace singleton CV                                  | Draft cookie                    | Yes  | `X-CSRFToken`, `If-Match` | multipart `file`           | `201` created, `200` replaced           | `404 draft_unavailable`, `409 draft_conflict`, `413 upload_too_large`, `415 unsupported_file_type`, `422 validation_error`, `422 invalid_pdf`, `428 draft_version_required`, `503 document_storage_unavailable` | `backend/apps/documents/views.py`    | `backend/tests/test_document_api.py`, `frontend/tests/e2e/slice7-fullstack.spec.ts` |
| `DELETE` | `/api/v1/application-drafts/{draft_id}/documents/cv/`                | Delete singleton CV metadata/access                             | Draft cookie                    | Yes  | `X-CSRFToken`, `If-Match` | None                       | `204` with `ETag`                       | `404 draft_unavailable`, `409 draft_conflict`, `428 draft_version_required`                                                                                                                                     | `backend/apps/documents/views.py`    | `backend/tests/test_document_api.py`, `frontend/tests/e2e/slice7-fullstack.spec.ts` |

## Vacancy Shape

```json
{
  "slug": "frontend-developer",
  "title": "Frontend Developer",
  "summary": "Build accessible candidate-facing interfaces.",
  "description": "Fictional role description.",
  "responsibilities": ["Build clear product workflows"],
  "requirements": ["TypeScript"],
  "benefits": ["Focused product work"],
  "location": "Tashkent, Uzbekistan",
  "work_format": "hybrid",
  "employment_type": "full_time",
  "status": "published",
  "published_at": "2026-06-20T09:00:00Z",
  "closing_at": null
}
```

## Draft Aggregate Shape

```json
{
  "draft": {
    "id": "11111111-2222-4333-8444-555555555555",
    "status": "active",
    "version": 3,
    "vacancy": { "slug": "frontend-developer", "title": "Frontend Developer" },
    "candidate": {
      "full_name": "Avery Example",
      "email": "avery.candidate@example.test",
      "phone": "",
      "portfolio_url": "https://example.test/avery",
      "preferred_contact_method": "email"
    },
    "experience": {
      "experience_level": "mid_level",
      "skills": ["Vue 3", "TypeScript"],
      "optional_message": "Fictional context.",
      "consent_acknowledged": true,
      "consent_version": "privacy-v1"
    },
    "experience_entries": [
      {
        "id": "22222222-3333-4444-8555-666666666666",
        "organization": "Fictional Systems",
        "role_title": "Interface Engineer",
        "start_month": "2024-01",
        "end_month": null,
        "is_current": true,
        "summary": "Built accessible application flows.",
        "position": 0
      }
    ],
    "document": {
      "original_name_display": "avery-example-cv.pdf",
      "detected_content_type": "application/pdf",
      "size": 42137,
      "uploaded_at": "2026-06-24T00:00:00Z"
    },
    "last_activity_at": "2026-06-24T00:00:00Z",
    "expires_at": "2026-07-01T00:00:00Z"
  }
}
```

`document` is nullable. The aggregate never includes raw credentials, credential hashes,
normalized email, storage keys, checksums, internal paths, document UUIDs, or public URLs.

## Patch Field Rules

Candidate fields are optional patch fields: `full_name`, `email`, `phone`, `portfolio_url`,
`preferred_contact_method`. The phone field is required only when choosing phone contact.

Experience fields are optional patch fields: `experience_level`, `skills`, `optional_message`,
`consent_acknowledged`, `consent_version`. Skills are capped at 12, each 80 characters or fewer.

Employment entry fields are `organization`, `role_title`, `start_month`, `end_month`, `is_current`,
`summary`, and `position`. Entries are capped at five per draft and `position` is 0 through 4.
`position` is part of the backend employment-entry representation and ordering contract. The
current frontend preserves and sends entry position as required by the API, sorts entries
deterministically by `position`, and assigns new entries to the next available position, but it does
not currently expose a dedicated drag-and-drop or manual reordering control. A future replacement
frontend may implement reordering only by using existing supported API behavior or through a
separately coordinated API change. Do not assume array order alone changes persisted position unless
the backend contract supports it.

## Deferred API

No endpoint currently implements final application submission or private status lookup. A frontend
must not call guessed endpoints, generate fictional credentials as real, or present status lookup as
implemented. Future submission/status APIs require separate design, implementation, versioning, and
tests.
