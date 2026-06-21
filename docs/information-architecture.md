# Information Architecture

## Planned Public Routes

| Route | Purpose | Notes |
| --- | --- | --- |
| `/` | Entry point and concise product context | Should lead quickly to vacancies and case study. |
| `/vacancies` | Vacancy index | Shows active roles and closed-state handling when relevant. |
| `/vacancies/[slug]` | Vacancy detail | Server-rendered public page with metadata. |
| `/apply/[slug]` | Step 1: position | Starts or restores a draft. |
| `/apply/[slug]/details` | Step 2: candidate details | Contact fields and validation. |
| `/apply/[slug]/experience` | Step 3: experience | CV upload, skills, message, consent. |
| `/apply/[slug]/review` | Step 4: review | Summary, edit links, submit. |
| `/application/submitted` | Confirmation | Shows the application reference and delivers the separate status lookup secret through the planned secure confirmation flow. |
| `/application/status` | Private status lookup | Requires the application reference and high-entropy status lookup secret. |
| `/case-study` | Product notes | Explains current behavior, assumptions, and planned architecture. |
| `/privacy` | Candidate privacy explanation | Product wording, not legal advice. |
| `/accessibility` | Accessibility statement | Planned support and known limitations. |

## Route Strategy Decision

ApplyFlow will use separate routes for application steps. See [ADR 0003](decisions/0003-application-step-routing.md).

## Options Considered

| Option | Benefits | Problems |
| --- | --- | --- |
| Separate routes | Clear browser history, page titles, focus targets, reload recovery, step analytics. | Requires route guards and shared draft context. |
| Nested routes | Similar benefits with a shared layout. | More implementation detail than the URL decision needs in Phase 0. |
| One route with internal step state | Simple initial implementation. | Poorer history, harder reload behavior, weaker page-level accessibility. |

## Accessibility Implications

Each step route needs:

- Unique page title.
- One visible `h1`.
- Programmatic focus to the step heading after navigation.
- Error summary focus after failed validation.
- Step indicator that exposes current step without relying on color.

## Draft Persistence Implications

Separate routes require draft restoration after reload. The frontend should fetch the draft from the server and handle expired or missing drafts with a clear recovery path.

## Browser History Behavior

Back and forward should move through meaningful steps. If a required earlier step is incomplete, the app may redirect to the first incomplete step with an explanation.

## Complexity

Separate routes add modest complexity, but the accessibility and history benefits are worth it for the first public version.
