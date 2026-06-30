# Frontend Architecture

## Documentation Baseline

The Nuxt 4.4.8 directory, application, pages, rendering, and data-fetching documentation was
reviewed on 2026-06-19. Application code belongs under `frontend/app/`; tests and root configuration
remain under `frontend/`. Recheck official Nuxt guidance before framework upgrades.

Frontend replacement and integration rules are maintained in
[the frontend integration contract](frontend-integration/README.md).

## Current Stack

- Vue 3 and Nuxt 4.
- Client-rendered Nuxt app for the candidate surface. Draft APIs depend on browser-managed
  same-origin cookies and CSRF; server-side rendering must not perform candidate draft mutations.
- TypeScript and Composition API.
- Semantic HTML and project-specific CSS tokens.
- Vitest and Vue Test Utils.
- Playwright.

No component library, animation dependency, or client state library is used.

## Current Structure

```text
frontend/
|-- app/
|   |-- api/
|   |-- assets/css/
|   |-- branding/
|   |-- components/
|   |-- composables/
|   |-- data/
|   |-- layouts/
|   |-- pages/
|   |-- types/
|   |-- utils/
|   `-- app.vue
|-- tests/
|   |-- e2e/
|   |-- fixtures/
|   `-- unit/
|-- nuxt.config.ts
|-- package.json
|-- playwright.config.ts
`-- vitest.config.ts
```

## Layer Boundaries

| Boundary                                                                                                                                 | Responsibility                                                                                                                                                                            |
| ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Presentation layer: `app/pages/`, `app/components/`, `app/layouts/`, `app/assets/css/`, `app/branding/`                                  | Route composition, visual design, accessible controls, responsive behavior, and source-controlled brand configuration. These are replaceable when the API/security contract is preserved. |
| Application state: `app/composables/useApplicationDraft.ts`, `app/composables/useDraftMutations.ts`, `app/composables/useVacancyPage.ts` | In-memory draft aggregate, active-draft restoration, mutation serialization, vacancy loading, save/conflict/offline states, and route orchestration.                                      |
| API client layer: `app/api/`                                                                                                             | Relative same-origin API transport, CSRF bootstrap, `ETag` handling, response guards, backend field mapping, upload XHR, and normalized errors.                                           |
| Security/session integration: `app/api/client.ts`, `app/api/runtime-guards.ts`, `proxy-target.ts`, `nuxt.config.ts`                      | Relative `/api/v1/` requests, cookies included by the browser, memory-only masked CSRF token, safe loopback dev-proxy target, and no JavaScript access to draft credentials.              |
| Upload transport: `app/api/documents.ts`, `app/components/forms/FileUpload.vue`                                                          | Multipart `file` upload, XHR progress/cancel, CV metadata display, replacement, deletion, and file-error presentation.                                                                    |
| Backend boundary                                                                                                                         | Django owns authorization, CSRF enforcement, validation, ETags, draft lifecycle, private storage, PDF validation, and database schema.                                                    |

Supporting paths:

- `app/utils/`: validation, data cloning, formatting, and focus behavior.
- `app/types/`: vacancy, draft, API aggregate, form, document, branding, and save-state contracts.

## Routes

Public and supporting routes:

- `/`
- `/vacancies`
- `/vacancies/[slug]`
- `/case-study`
- `/privacy`
- `/accessibility`

Candidate flow routes:

- `/apply/[slug]`
- `/apply/[slug]/details`
- `/apply/[slug]/experience`
- `/apply/[slug]/review`
- `/application/submitted`
- `/application/status`

Every application route verifies that the vacancy exists and is active before rendering application
content or changing draft state.

## State And Services

The current frontend uses Nuxt state for one in-memory application draft. Route state owns step and
review-return navigation. Components own local interaction state. The draft state is rehydrated from
the authorized backend active-draft endpoint rather than browser storage.

Candidate data, CSRF tokens, ownership credentials, document storage keys, checksums, status lookup
secrets, and application references are not stored in localStorage, sessionStorage, IndexedDB, URL
query strings, or URL hashes. The ownership cookie remains HttpOnly and browser-managed. Pinia
remains unnecessary under [ADR 0008](decisions/0008-state-management.md).

The DRF API is authoritative for vacancies, anonymous draft ownership, candidate fields, experience
summary, employment entries, CV metadata, CV upload/replacement/deletion, ETags, and abandonment.
Final submission and private status lookup remain Phase 4 and are not active in the real candidate
path.

Local development keeps browser requests same-origin through the Nuxt dev proxy. Browser code calls
`/api/v1/...`; Nuxt forwards to the configured loopback Django origin while preserving the `/api/`
prefix.

## Focus And Validation

- Meaningful path changes focus the new page heading.
- Query and hash-only changes do not trigger global heading focus.
- Failed validation focuses a visible error summary.
- Summary links focus text fields, grouped controls, the upload group, or consent checkbox.
- Recoverable save failures focus page-level feedback while preserving values.
- Save status changes are announced through a polite live region without announcing every keystroke.
- Active-draft conflicts and disabled final submission use visible explanatory text rather than
  color-only state.
- Reduced-motion preferences disable smooth page behavior.

## Testing

- Unit tests cover validation, API transport, CSRF memory-only behavior, runtime guards, draft/API
  mapping, field-error mapping, mutation serialization, file selection, branding validation, and
  error summaries.
- Playwright provides deterministic browser smoke coverage with routed API responses and a real
  Django full-stack Slice 7 harness through `npm run test:e2e:fullstack`.
- Browser-review screenshots remain ignored artifacts for human inspection.
