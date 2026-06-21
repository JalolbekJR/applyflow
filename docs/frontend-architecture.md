# Frontend Architecture

## Documentation Baseline

The Nuxt 4.4.8 directory, application, pages, rendering, and data-fetching documentation was
reviewed on 2026-06-19. Application code belongs under `frontend/app/`; tests and root configuration
remain under `frontend/`. Recheck official Nuxt guidance before framework upgrades.

## Current Stack

- Vue 3 and Nuxt 4.
- TypeScript and Composition API.
- Semantic HTML and project-specific CSS tokens.
- Vitest and Vue Test Utils.
- Playwright.

No component library, animation dependency, or client state library is used.

## Current Structure

```text
frontend/
|-- app/
|   |-- assets/css/
|   |-- components/
|   |-- composables/
|   |-- data/
|   |-- layouts/
|   |-- pages/
|   |-- plugins/
|   |-- services/
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

## Boundaries

| Boundary | Responsibility |
| --- | --- |
| `app/components/` | Focused, accessible interface elements. Small components do not call services. |
| `app/pages/` | Route-level orchestration, form submission, and page metadata. |
| `app/composables/` | Shared vacancy and in-memory application state. |
| `app/services/` | Typed fixture behavior now; API communication and response normalization later. |
| `app/utils/` | Validation, data cloning, formatting, and focus behavior. |
| `app/types/` | Vacancy, form, service, and status contracts. |

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
review-return navigation. Components own local interaction state. Typed fixture services simulate
save, submission, and status behavior.

Candidate data and credentials are not stored in localStorage. Pinia remains unnecessary under
[ADR 0008](decisions/0008-state-management.md).

The planned DRF API will replace fixture services and become authoritative for draft ownership,
field validation, file storage, submission, and status access.

## Focus And Validation

- Meaningful path changes focus the new page heading.
- Query and hash-only changes do not trigger global heading focus.
- Failed validation focuses a visible error summary.
- Summary links focus text fields, grouped controls, the upload group, or consent checkbox.
- Recoverable save failures focus page-level feedback while preserving values.
- Reduced-motion preferences disable smooth page behavior.

## Testing

- Unit tests cover validation, services, file selection, credentials, progress, and error summaries.
- Playwright covers the candidate path, invalid routes, error focus, failure retry, status lookup,
  duplicate activation, keyboard behavior, and mobile reflow.
- Browser-review screenshots remain ignored artifacts for human inspection.
