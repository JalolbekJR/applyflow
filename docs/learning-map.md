# Learning Map

This map records the engineering topics exercised by ApplyFlow and the remaining backend and
operational work. Phase numbers follow the current implementation roadmap.

## Frontend

| Topic | Why It Matters In ApplyFlow | Be Able To Explain | Reproduce Manually | Phase |
| --- | --- | --- | --- | --- |
| Vue reactivity | Form fields and upload state update the UI. | How reactive values trigger renders. | Reproduce a small reactive form. | 1 |
| `ref` versus `reactive` | Field primitives and grouped state need different shapes. | When each is easier to test and serialize. | Trace both patterns in the current forms. | 1 |
| Computed values | Progress, completion, and validation summaries derive from state. | Why derived state should not be duplicated. | Trace the current completion state. | 1 |
| Watchers | Vacancy and upload state react to verified changes. | Why watchers should be limited and cleanup-aware. | Trace the current vacancy and upload watchers. | 1 |
| Props and emits | Form components communicate without owning everything. | One-way data flow and event naming. | Trace the file-upload metadata event. | 1 |
| Composables | Draft and route behavior are shared across steps. | Difference between useful composable and needless abstraction. | Trace draft ownership across routes. | 1 |
| Nuxt pages | Routes map to public and application pages. | File-based routing and page metadata. | Trace the implemented route files. | 1 |
| Layouts | Public pages and application steps share structure. | Layout selection and page responsibility. | Trace the site and application shells. | 1 |
| Route ownership | Application steps must match the active draft vacancy. | Why a focused domain guard is preferable to generic middleware here. | Reproduce direct cross-vacancy recovery. | 1 |
| SSR | Vacancy pages need readable initial HTML. | What server rendering helps and what still hydrates. | Inspect a rendered vacancy detail page. | 1 |
| Hydration | File inputs and draft state are browser-dependent. | How mismatches happen. | Trace the fixture control and file input boundaries. | 1 |
| TypeScript | Service models and form data need stable contracts. | DTOs versus UI state. | Trace the current domain contracts. | 1 |
| Form state | The application flow is the product core. | Local state, cloning, and validation timing. | Reproduce a validated step transition. | 1 |
| API integration | Fixture services will be replaced by DRF endpoints. | Mapping server errors to UI errors. | Compare fixture contracts with the planned API. | 3 |
| Accessibility | The flow must be keyboard-completable. | Labels, focus, error summary, reduced motion. | Complete a step using keyboard only. | 1 |
| Testing | Prevents regressions in the main flow. | Unit vs component vs end-to-end tests. | Trace a validation test and Playwright flow. | 1 |

## Backend

| Topic | Why It Matters In ApplyFlow | Be Able To Explain | Reproduce Manually | Phase |
| --- | --- | --- | --- | --- |
| Django project structure | Keeps apps and settings understandable. | Project package vs app responsibilities. | Create vacancies/applications/documents apps. | 3 |
| Models | Vacancies, drafts, applications, documents need persistence. | Fields, constraints, indexes. | Model a vacancy and application draft. | 3 |
| Migrations | Schema changes must be reviewable. | Migration discipline and rollback thinking. | Create and inspect a migration. | 3 |
| Serializers | DRF validates and shapes API data. | Serializer validation vs model constraints. | Build a draft update serializer. | 3 |
| ViewSets/views | HTTP layer maps requests to services. | Why views stay thin. | Create a vacancy detail endpoint. | 3 |
| Permissions | Protect drafts, documents, and admin behavior. | Object-level authorization. | Test cross-draft access denial. | 4 |
| Authentication | Admin users and anonymous candidates differ. | Session auth, anonymous flow, and cookies. | Configure admin login separately. | 3 |
| CSRF | Same-origin unsafe methods need protection. | How CSRF differs from CORS. | Explain settings for local vs production. | 3 |
| Throttling | Status lookup and uploads need abuse limits. | Why throttling is not authorization. | Add a scoped throttle test. | 5 |
| PostgreSQL constraints | Duplicate submissions need database enforcement. | Unique constraints and indexes. | Add unique rule for vacancy/email. | 5 |
| Transactions | Submission must be atomic. | What rolls back on failure. | Submit draft and document in one transaction. | 5 |
| File storage | CV upload is private and hostile input. | Storage key, metadata, safe download. | Save a document with generated name. | 4 |
| Testing | Backend rules must not rely on manual checks. | pytest fixtures, database tests, negative tests. | Write upload rejection tests. | 4 |
| Docker | Local and production environments need repeatability later. | Image, container, service, volume. | Build and inspect backend packaging. | 7 |
| CI/CD | Checks should run before merge. | Workflow jobs and required checks. | Add and inspect the required workflows. | 7 |

## UX

| Topic | Why It Matters In ApplyFlow | Be Able To Explain | Reproduce Manually | Phase |
| --- | --- | --- | --- | --- |
| Heuristic review | Finds friction before user testing. | Difference between observation and assumption. | Review the flow against NN/g heuristics. | 1 |
| User flow | The route structure follows candidate steps. | Happy path and error paths. | Draw the application flow. | 1 |
| Information architecture | Pages need clear purpose. | Why separate routes were chosen. | Map routes to user needs. | 1 |
| Browser review | Tests structure in the implemented interaction context. | What each screen must answer. | Review mobile and desktop routes. | 1 |
| Design tokens | Prevent random styling. | Color, type, spacing, radius, focus tokens. | Trace the coded CSS token set. | 1 |
| Component variants | Forms need complete states. | Default, hover, focus, disabled, loading, error, success. | Review implemented input and upload states. | 1 |
| Mobile-first design | Many candidates apply on phones. | Keyboard, safe areas, touch targets. | Design details step for a small phone. | 1 |
| Accessibility | Candidate flow must be usable beyond pointer/mouse. | Labels, focus order, error summary, reduced motion. | Audit the implemented flow. | 1 |
| Usability testing | Assumptions need evidence. | Tasks, observation, limitations. | Run a small moderated test. | 2 |
| Design documentation | Coded choices must remain understandable. | What maintainers need beyond implementation. | Reconcile component notes with browser behavior. | 2 |
