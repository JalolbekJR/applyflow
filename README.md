# ApplyFlow

ApplyFlow is a focused portfolio project for improving vacancy discovery and job application flows.

Product statement:

> A job application experience that respects the candidate's time.

Current status: Phase 0 documentation and architecture. No production application has been implemented yet.

## Problem

Many application forms ask candidates to repeat information already present in a CV, hide progress, and fail late with unclear errors. ApplyFlow plans a smaller flow that helps candidates understand the role, provide only necessary details, upload a CV safely, review before submitting, and check a private application status later.

No user research has been conducted yet. The current problem definition is based on interface-pattern review, supplied context screenshots, and product assumptions that require validation.

## Planned Experience

The first public version is planned around:

- One fictional employer and a small fictional vacancy dataset
- Vacancy index
- Vacancy detail page
- Four-step application flow
- Draft persistence
- Secure CV upload
- Review-before-submit step
- Submission confirmation
- Private application-status lookup
- Responsive mobile experience
- Public UX case-study page
- Django Admin for internal vacancy and application management

The four application steps are position, candidate details, experience, and review.

## Scope

ApplyFlow is intentionally smaller than a full applicant-tracking platform. It should be deep enough to discuss in technical interviews, but small enough for one developer to implement, test, and explain.

Planned stack:

- Frontend: Vue 3, Nuxt 4, TypeScript, semantic HTML, CSS, Vitest, Vue Test Utils, Playwright
- Backend: Python, Django, Django REST Framework, PostgreSQL, pytest, pytest-django, Ruff, OpenAPI
- Operations: Docker planning, GitHub Actions planning, same-origin deployment target
- Design: mobile-first flow, original restrained art direction, Figma handoff plan, accessibility annotations

## Non-Goals

Version one will not include candidate accounts, cross-device draft recovery, multiple employers, recruiter messaging, interview scheduling, video interviews, AI candidate scoring, automated ranking, automated rejection, resume generation, chatbot assistance, payments, subscriptions, native mobile apps, a job marketplace, analytics dashboards, microservices, Kubernetes, broad audit infrastructure, DOC or DOCX uploads, or unnecessary background queues.

The internal workflow uses Django Admin instead of a custom recruiter dashboard.

## Planned Architecture

The planned backend is a modular Django application with focused apps for vacancies, applications, and documents. Views stay thin. Domain operations such as draft creation, document attachment, final submission, duplicate protection, and retention cleanup belong in service functions.

The planned frontend uses Nuxt 4 application code under `frontend/app/`, with file-based pages for public vacancy discovery and separate routes for application steps. Route state owns step navigation, components own local interaction, composables coordinate shared flow behavior, and typed services handle API communication. Server draft state is authoritative. Pinia is not planned initially and requires a later ADR if implementation proves it necessary.

Drafts use an anonymous server-side model protected by a server-generated high-entropy secret, with one active anonymous draft per browser in version one. CV uploads are PDF-only and treated as hostile input. Status lookup separates a readable application reference from a high-entropy lookup secret, with rate limiting and generic failure responses.

## Repository Structure

```text
.
|-- .env.example
|-- .gitattributes
|-- .gitignore
|-- AGENTS.md
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- LICENSE
|-- README.md
`-- docs/
    |-- decisions/
    |-- product-brief.md
    |-- design-direction.md
    |-- frontend-architecture.md
    |-- backend-architecture.md
    |-- api-contract.md
    |-- threat-model.md
    |-- testing-strategy.md
    `-- implementation-roadmap.md
```

## Documentation Map

- [Product brief](docs/product-brief.md)
- [Problem audit](docs/problem-audit.md)
- [Assumptions and validation](docs/assumptions-and-validation.md)
- [Candidate journey](docs/candidate-journey.md)
- [User flow](docs/user-flow.md)
- [Information architecture](docs/information-architecture.md)
- [Field inventory](docs/field-inventory.md)
- [Content design](docs/content-design.md)
- [Design direction](docs/design-direction.md)
- [Design system plan](docs/design-system-plan.md)
- [Figma structure](docs/figma-structure.md)
- [Accessibility plan](docs/accessibility.md)
- [Frontend architecture](docs/frontend-architecture.md)
- [Backend architecture](docs/backend-architecture.md)
- [Domain model](docs/domain-model.md)
- [Application lifecycle](docs/application-lifecycle.md)
- [API contract](docs/api-contract.md)
- [Draft persistence](docs/draft-persistence.md)
- [Upload security](docs/upload-security.md)
- [Privacy model](docs/privacy.md)
- [Threat model](docs/threat-model.md)
- [Testing strategy](docs/testing-strategy.md)
- [Infrastructure plan](docs/infrastructure-plan.md)
- [CI plan](docs/ci-plan.md)
- [Implementation roadmap](docs/implementation-roadmap.md)
- [Learning map](docs/learning-map.md)
- [Interview notes](docs/interview-notes.md)
- [Runbook outline](docs/runbook-outline.md)
- [Architecture decisions](docs/decisions/index.md)

## Security And Privacy Position

ApplyFlow must collect only data needed for the vacancy application. Candidate personal data, draft data, and uploaded documents must not be used in screenshots, fixtures, tests, or demo seeds. Uploaded files must be stored privately, served only after authorization, and logged without personal file contents or user-controlled paths.

Legal retention periods and production privacy wording require review before real recruitment use.

## Accessibility Position

The application is planned around persistent labels, semantic landmarks, keyboard access, visible focus states, error summaries, step-heading focus movement, reduced-motion support, and mobile touch targets. The project must not claim WCAG conformance until it has been tested.

## Testing Strategy

Phase 0 defines the test plan only. Later phases should add backend unit and integration tests, frontend unit tests, Playwright end-to-end flows, accessibility checks, manual UX review, and security review.

No tests exist yet.

## Development Workflow

Current Phase 0 workflow:

1. Keep work on `phase-0-product-architecture`.
2. Update documentation only.
3. Do not scaffold Nuxt, Django, Docker, or CI workflows.
4. Do not install dependencies.
5. Do not commit or push unless explicitly instructed.

Later implementation phases will add code and tests according to [the roadmap](docs/implementation-roadmap.md).

## Roadmap

Phase 0 defines product and architecture. Phase 1 prepares UX foundations and Figma work. Later phases cover high-fidelity design, Nuxt foundation, application flow, Django/DRF foundation, secure drafts and uploads, integrated submission, security and accessibility hardening, Docker/CI/deployment, and portfolio release.

## Known Limitations

- No application code exists yet.
- No Figma file has been created by Codex.
- No usability testing has been performed.
- No security controls have been implemented.
- No CI workflow exists.
- No deployment exists.

## Author

Built by Jalolbek JR.

Applying for a job should not feel like filing taxes twice.
