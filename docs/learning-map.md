# Learning Map

This map helps Jalolbek JR study the technologies while building ApplyFlow. It is tied to the roadmap, not a generic curriculum.

## Frontend

| Topic | Why It Matters In ApplyFlow | Be Able To Explain | Reproduce Manually | Phase |
| --- | --- | --- | --- | --- |
| Vue reactivity | Form fields and upload state update the UI. | How reactive values trigger renders. | Build a small reactive form. | 3 |
| `ref` versus `reactive` | Field primitives and grouped state need different shapes. | When each is easier to test and serialize. | Convert a small form between both approaches. | 3 |
| Computed values | Progress, completion, and validation summaries derive from state. | Why derived state should not be duplicated. | Create computed completion state. | 4 |
| Watchers | Draft save feedback may react to changes. | Why watchers should be limited and cleanup-aware. | Watch a field and debounce a save mock. | 4 |
| Props and emits | Form components communicate without owning everything. | One-way data flow and event naming. | Build a text input component. | 3 |
| Composables | Draft, upload, and step behavior can be reused. | Difference between useful composable and needless abstraction. | Extract upload state to a composable. | 4 |
| Nuxt pages | Routes map to public and application pages. | File-based routing and page metadata. | Create planned page files. | 3 |
| Layouts | Public pages and application steps share structure. | Layout selection and page responsibility. | Build public and application layouts. | 3 |
| Middleware | Step access may need guards. | When route middleware is justified. | Redirect incomplete draft to first incomplete step. | 4 |
| SSR | Vacancy pages need readable initial HTML. | What server rendering helps and what still hydrates. | Render a vacancy detail page. | 3 |
| Hydration | File inputs and draft state are browser-dependent. | How mismatches happen. | Add client-only upload state safely. | 4 |
| TypeScript | API models and form data need stable contracts. | DTOs versus UI state. | Type draft request/response objects. | 3 |
| Form state | The application flow is the product core. | Local state, serialization, validation timing. | Build step validation. | 4 |
| API integration | Frontend consumes DRF endpoints. | Mapping server errors to UI errors. | Mock a validation error response. | 4 |
| Accessibility | The flow must be keyboard-completable. | Labels, focus, error summary, reduced motion. | Complete a step using keyboard only. | 4 |
| Testing | Prevents regressions in the main flow. | Unit vs component vs end-to-end tests. | Write a validation test and a Playwright happy path. | 4 |

## Backend

| Topic | Why It Matters In ApplyFlow | Be Able To Explain | Reproduce Manually | Phase |
| --- | --- | --- | --- | --- |
| Django project structure | Keeps apps and settings understandable. | Project package vs app responsibilities. | Create vacancies/applications/documents apps. | 5 |
| Models | Vacancies, drafts, applications, documents need persistence. | Fields, constraints, indexes. | Model a vacancy and application draft. | 5 |
| Migrations | Schema changes must be reviewable. | Migration discipline and rollback thinking. | Create and inspect a migration. | 5 |
| Serializers | DRF validates and shapes API data. | Serializer validation vs model constraints. | Build a draft update serializer. | 5 |
| ViewSets/views | HTTP layer maps requests to services. | Why views stay thin. | Create a vacancy detail endpoint. | 5 |
| Permissions | Protect drafts, documents, and admin behavior. | Object-level authorization. | Test cross-draft access denial. | 6 |
| Authentication | Admin users and anonymous candidates differ. | Session auth, anonymous flow, and cookies. | Configure admin login separately. | 5 |
| CSRF | Same-origin unsafe methods need protection. | How CSRF differs from CORS. | Explain settings for local vs production. | 5 |
| Throttling | Status lookup and uploads need abuse limits. | Why throttling is not authorization. | Add a scoped throttle test. | 7 |
| PostgreSQL constraints | Duplicate submissions need database enforcement. | Unique constraints and indexes. | Add unique rule for vacancy/email. | 7 |
| Transactions | Submission must be atomic. | What rolls back on failure. | Submit draft and document in one transaction. | 7 |
| File storage | CV upload is private and hostile input. | Storage key, metadata, safe download. | Save a document with generated name. | 6 |
| Testing | Backend rules must not rely on manual checks. | pytest fixtures, database tests, negative tests. | Write upload rejection tests. | 6 |
| Docker | Local/prod environments need repeatability later. | Image, container, service, volume. | Build a backend image in Phase 9. | 9 |
| CI/CD | Checks should run before merge. | Workflow jobs and required checks. | Add backend CI workflow later. | 9 |

## UX

| Topic | Why It Matters In ApplyFlow | Be Able To Explain | Reproduce Manually | Phase |
| --- | --- | --- | --- | --- |
| Heuristic review | Finds friction before user testing. | Difference between observation and assumption. | Review the flow against NN/g heuristics. | 1 |
| User flow | The route structure follows candidate steps. | Happy path and error paths. | Draw the application flow. | 1 |
| Information architecture | Pages need clear purpose. | Why separate routes were chosen. | Map routes to user needs. | 1 |
| Wireframes | Low-cost way to test structure. | What each screen must answer. | Sketch mobile first. | 1 |
| Design tokens | Prevent random styling later. | Color, type, spacing, radius, focus tokens. | Define Figma token page. | 1 |
| Component variants | Forms need complete states. | Default, hover, focus, disabled, loading, error, success. | Build input and upload variants. | 2 |
| Mobile-first design | Many candidates apply on phones. | Keyboard, safe areas, touch targets. | Design details step for a small phone. | 1 |
| Accessibility | Candidate flow must be usable beyond pointer/mouse. | Labels, focus order, error summary, reduced motion. | Annotate a wireframe. | 1 |
| Usability testing | Assumptions need evidence. | Tasks, observation, limitations. | Run a small moderated test. | 2 |
| Developer handoff | Design choices must become buildable specs. | What engineers need from Figma. | Write component notes and field behavior. | 2 |
