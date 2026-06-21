# ApplyFlow

ApplyFlow is a candidate-facing vacancy and job application experience built around a short,
transparent application process.

The repository is currently in Phase 1. A Nuxt 4 frontend implements vacancy discovery, a
four-step application flow, confirmation, and private status lookup using fictional fixtures and
simulated services. There is no backend, database, persistent draft, document storage, or real
submission yet.

## Current Frontend

The frontend currently includes:

- Home, vacancy index, and vacancy detail pages.
- Position, candidate details, experience, and review application routes.
- Client-side validation with error summaries and grouped-control associations.
- In-memory draft state for the current browser tab.
- PDF file-selection validation and metadata display without uploading file contents.
- Simulated save, submission, confirmation, and private status lookup behavior.
- Loading, empty, unavailable, validation, save-failure, upload-failure, and success states.
- Responsive layouts from 320px upward, keyboard navigation, route focus, and reduced-motion support.
- Vitest component tests and Playwright browser tests.

All vacancies, credentials, candidate details, and status responses are fictional.

## Architecture

Frontend application code lives under `frontend/app/` and follows Nuxt 4 conventions:

- `pages/` owns route-level behavior and metadata.
- `components/` owns focused, accessible interface elements.
- `composables/` coordinates vacancy and application state across routes.
- `services/` provides typed fixture-backed boundaries that can later be replaced by API calls.
- `utils/` contains validation, cloning, and focus behavior.
- `types/` defines the shared frontend domain model.

The current draft is held in Nuxt state for the browser session. Candidate data and credentials are
not written to localStorage.

The planned backend is a modular Python application using Django, Django REST Framework, and
PostgreSQL. It will make server-side drafts authoritative, validate and store CV documents
privately, enforce duplicate submission rules transactionally, expose minimal status responses,
and use Django Admin for staff workflows. Backend work has not started.

Relevant decisions are recorded in [the ADR index](docs/decisions/index.md).

## Repository Structure

```text
.
|-- AGENTS.md
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- LICENSE
|-- README.md
|-- docs/
|   |-- decisions/
|   |-- accessibility.md
|   |-- frontend-architecture.md
|   |-- product-brief.md
|   |-- testing-strategy.md
|   `-- implementation-roadmap.md
`-- frontend/
    |-- app/
    |   |-- assets/
    |   |-- components/
    |   |-- composables/
    |   |-- pages/
    |   |-- plugins/
    |   |-- services/
    |   |-- types/
    |   `-- utils/
    |-- tests/
    |   |-- e2e/
    |   |-- fixtures/
    |   `-- unit/
    |-- nuxt.config.ts
    |-- package.json
    |-- playwright.config.ts
    `-- vitest.config.ts
```

## Local Setup

Requirements:

- Node.js `^22.12.0`, `^24.11.0`, or `>=26.0.0`.
- npm, included with Node.js.

From the repository root:

```powershell
Set-Location .\frontend
npm ci
npm run dev
```

The development server is available at `http://127.0.0.1:3000` when started with the Playwright
configuration, or at the URL printed by Nuxt when started directly.

## Development Commands

Run commands from `frontend/`:

```powershell
npm run format:check  # Check formatting
npm run format        # Apply formatting
npm run lint          # Run ESLint
npm run typecheck     # Run Nuxt/Vue TypeScript checks
npm run test          # Run Vitest unit and component tests
npm run test:e2e      # Run Playwright browser tests
npm run build         # Create the Nuxt production build
```

Playwright starts the Nuxt development server automatically on `127.0.0.1:3000`. Browser-review
screenshots are written under `frontend/tests/screenshots/` and are ignored by Git.

## Simulated Behavior And Limitations

- Draft answers last only while the current application state remains in memory.
- Selecting a PDF reads browser-provided file metadata only; no file is uploaded or stored.
- Save and submission delays are fixture behavior, not API calls.
- Confirmation credentials and status responses are fixed fictional values.
- Client validation improves feedback but is not a security boundary.
- Server-side authorization, upload inspection, rate limiting, persistence, retention, and duplicate
  protection still require the planned backend.
- No usability study or accessibility conformance audit has been completed.
- No CI, deployment, production database, or staff administration system exists.

Do not use the current frontend to collect real candidate information.

## Documentation

- [Product brief](docs/product-brief.md)
- [Frontend architecture](docs/frontend-architecture.md)
- [Accessibility plan](docs/accessibility.md)
- [Testing strategy](docs/testing-strategy.md)
- [Upload security](docs/upload-security.md)
- [Threat model](docs/threat-model.md)
- [Implementation roadmap](docs/implementation-roadmap.md)
- [Architecture decisions](docs/decisions/index.md)

## License

ApplyFlow is available under the [MIT License](LICENSE).
