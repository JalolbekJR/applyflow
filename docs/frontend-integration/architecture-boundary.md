# Architecture Boundary

ApplyFlow's frontend can be redesigned or replaced when it preserves the API, security, and data
lifecycle contracts described in this directory.

## Replaceable Frontend Areas

These paths are presentation-owned and may be redesigned without backend changes:

| Path                       | Responsibility                                                                                         |
| -------------------------- | ------------------------------------------------------------------------------------------------------ |
| `frontend/app/pages/`      | Route composition for vacancy, application, review, deferred submission, and status-unavailable pages. |
| `frontend/app/components/` | Accessible UI controls, layout pieces, save status, upload field, summaries, and shell components.     |
| `frontend/app/layouts/`    | Nuxt layout wrappers.                                                                                  |
| `frontend/app/assets/`     | CSS tokens, global styles, focus, spacing, and responsive presentation.                                |
| `frontend/app/branding/`   | Source-controlled brand identity, copy snippets, semantic tokens, and capability flags.                |

Visual style, component names, layout order, responsive behavior, and accessibility presentation can
change while preserving route purpose and user workflows.

## Integration-Layer Frontend Areas

These paths can be rewritten, but their external behavior must satisfy the backend contract:

| Path                                                     | Contract-bearing responsibility                                                                                   |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `frontend/app/api/client.ts`                             | Relative `/api/v1/` fetches, `credentials: "include"`, memory-only CSRF token, JSON parsing, error normalization. |
| `frontend/app/api/drafts.ts`                             | Draft aggregate mapping, creation, active restore, candidate and experience mutations, entry CRUD, abandonment.   |
| `frontend/app/api/documents.ts`                          | XHR upload with progress/cancel, multipart `file`, CSRF, cookies, `If-Match`, CV deletion.                        |
| `frontend/app/api/vacancies.ts`                          | Public vacancy list/detail mapping.                                                                               |
| `frontend/app/api/runtime-guards.ts`                     | Response shape guards and relative API path enforcement.                                                          |
| `frontend/app/api/errors.ts`                             | Error envelope mapping to candidate-facing states.                                                                |
| `frontend/app/composables/useApplicationDraft.ts`        | In-memory draft aggregate, active-draft restore, mutation orchestration, conflict/offline/error state.            |
| `frontend/app/composables/useDraftMutations.ts`          | Serialization of unsafe draft mutations.                                                                          |
| `frontend/app/composables/useVacancyPage.ts`             | API-backed vacancy route loading.                                                                                 |
| `frontend/proxy-target.ts` and `frontend/nuxt.config.ts` | Local Nuxt development proxy that preserves `/api/v1/...`.                                                        |

## Protected Backend Areas

These paths are outside frontend-only scope:

| Path                                                      | Why protected                                                        |
| --------------------------------------------------------- | -------------------------------------------------------------------- |
| `backend/apps/*/models.py` and migrations                 | Database schema, constraints, retention, and data lifecycle.         |
| `backend/apps/applications/drafts.py`                     | Draft credential parsing, hashing, cookies, ETags, and ownership.    |
| `backend/apps/applications/views.py`                      | Draft create/read/mutate/abandon API behavior.                       |
| `backend/apps/applications/serializers.py`                | Candidate, experience, and entry validation and response projection. |
| `backend/apps/documents/views.py`                         | CV metadata, upload, replacement, deletion, and error mapping.       |
| `backend/apps/documents/services.py`                      | Storage/metadata consistency and replacement safety.                 |
| `backend/apps/documents/pdf_validation.py`                | Server-authoritative PDF validation.                                 |
| `backend/apps/documents/storage.py`                       | Private storage boundary.                                            |
| `backend/config/api_urls.py` and `backend/config/urls.py` | Versioned API routes.                                                |
| `backend/config/settings.py`                              | CSRF, cookies, storage limits, database, and security settings.      |

Editing these areas changes the product contract and is outside a frontend-only task. They may
evolve only through a separate approved backend/API change with impact review, compatibility and
versioning analysis for API-breaking behavior, migration review where applicable, updated tests,
and corresponding frontend contract updates. Security behavior must not be weakened as a
convenience for a replacement frontend.

## Database Isolation

Browser code cannot and must not access the database directly. A frontend build or redesign must not
create migrations or modify model fields, constraints, indexes, retention rules, or cleanup
eligibility. Database schema changes require explicit approval and a dedicated migration plan.

## Private Document Isolation

CVs remain in backend-managed private storage. The frontend receives metadata only:

- `original_name_display`
- `detected_content_type`
- `size`
- `uploaded_at`

No public document URL exists. A replacement frontend must not derive, expose, log, or store private
storage keys, checksums, internal file paths, or document UUIDs. Direct-to-public-storage behavior
requires a separate approved architecture change.
