# Frontend Architecture

## References Checked

- [Nuxt 4 directory structure](https://nuxt.com/docs/4.x/directory-structure)
- [Nuxt 4 app directory](https://nuxt.com/docs/4.x/directory-structure/app)
- [Nuxt 4 pages directory](https://nuxt.com/docs/4.x/directory-structure/app/pages)
- [Nuxt 4 public directory](https://nuxt.com/docs/4.x/directory-structure/public)
- [Nuxt rendering modes](https://nuxt.com/docs/4.x/guide/concepts/rendering)
- [Nuxt data fetching](https://nuxt.com/docs/4.x/getting-started/data-fetching)

Context7 was requested for this reconciliation but was not available in the session or install catalog. The official Nuxt `4.x` documentation source was retrieved from `nuxt/nuxt` through the GitHub connector on 2026-06-19. It verified that application code belongs under `app/`; built-in application directories include `assets/`, `components/`, `composables/`, `layouts/`, `pages/`, and `utils/`; `app.vue` belongs under `app/`; and `public/` plus `nuxt.config.ts` remain at the project root. The retrieved docs package reported version `4.4.8`. Recheck exact version guidance before Phase 3 scaffolding.

## Planned Stack

- Vue 3
- Nuxt 4
- TypeScript
- Composition API
- Semantic HTML
- Native CSS, CSS Modules, or SCSS
- Vitest
- Vue Test Utils
- Playwright

Do not choose a large component library by default. The visual identity should come from ApplyFlow tokens and primitives.

## Planned Structure

```text
frontend/
|-- app/
|   |-- assets/
|   |-- components/
|   |   |-- ui/
|   |   |-- vacancies/
|   |   |-- application/
|   |   `-- upload/
|   |-- composables/
|   |-- layouts/
|   |-- pages/
|   |-- services/
|   |-- types/
|   |-- utils/
|   `-- app.vue
|-- public/
|-- tests/
|-- nuxt.config.ts
|-- package.json
`-- tsconfig.json
```

This is a plan, not an implemented directory structure. It follows Nuxt 4's `app/` convention for application code. Public assets, tests, configuration, and package metadata remain outside `app/`. Create a listed directory only when its responsibility exists. Nuxt can provide a default `app.vue`; ApplyFlow should add one only when global layout or application-shell behavior requires it. `services/` and `types/` are ApplyFlow conventions, not Nuxt auto-import directories, so their modules use explicit imports.

## Boundaries

| Boundary | Responsibility |
| --- | --- |
| `app/components/` | Render accessible UI from props. No API calls in small UI primitives. |
| `app/pages/` | Route-level behavior and page metadata. |
| `app/composables/` | Reusable stateful behavior such as draft status, upload state, and step navigation. |
| `app/services/` | Typed REST API calls and response normalization; no independent source of truth. |
| `app/utils/` | Client-side format and step validation helpers. |
| `app/types/` | API DTOs, form models, status enums. |

## Pages

Server-rendered public pages:

- `/`
- `/vacancies`
- `/vacancies/[slug]`
- `/case-study`
- `/privacy`
- `/accessibility`

Client-sensitive flow pages:

- `/apply/[slug]`
- `/apply/[slug]/details`
- `/apply/[slug]/experience`
- `/apply/[slug]/review`
- `/application/submitted`
- `/application/status`

Vacancy content can be rendered on the server. Application form state depends on browser interaction and server draft restoration.

## SSR And Hydration

Nuxt can render public vacancy pages before hydration. The application flow must handle:

- Draft restoration after hydration.
- One-active-draft-per-browser behavior.
- Browser-only file input APIs.
- Upload progress.
- Focus management after route changes.
- Expired draft recovery.
- JavaScript failure messaging.

The project should not claim full progressive enhancement until a no-JavaScript path is actually designed and tested. For version one, public vacancy reading should remain useful without JavaScript, while application submission may require JavaScript.

## State Management

See [ADR 0008](decisions/0008-state-management.md).

Use:

- Route state for application-step navigation and page metadata.
- Local component state for interaction that belongs to one component.
- Dedicated composables for shared application-flow, draft, and upload behavior.
- Typed API services for server communication and response normalization.
- Explicit serialization at the API boundary.
- Server draft state as the authority for persisted candidate data and allowed submission state.

Avoid:

- Pinia by default.
- localStorage for candidate data or secrets.
- One giant form component.

Pinia may be introduced only if implementation demonstrates a real cross-route ownership problem and a new or superseding ADR records the decision.

## API Integration

REST services should:

- Use typed request and response models.
- Map DRF validation errors to field and summary errors.
- Preserve form data after recoverable failures.
- Handle `401`, `403`, `404`, `409`, `413`, `415`, `422`, and `429` with calm messages.
- Avoid logging candidate values to the browser console.

## Motion

CSS transitions are enough for most states:

- Button feedback.
- Input focus.
- Step indicator line.
- Upload status changes.

No animation dependency is planned for version one.

## Testing Plan

Frontend tests are planned for Phase 3 and Phase 4:

- Unit tests for validation and serialization.
- Component tests for field states.
- Playwright flows for vacancy discovery, application completion, upload failure recovery, keyboard completion, mobile completion, and status lookup.
