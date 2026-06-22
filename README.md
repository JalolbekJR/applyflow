# ApplyFlow

ApplyFlow is a candidate-facing vacancy and job application experience built around a short,
transparent application process.

The repository is currently in Phase 2. A Nuxt 4 frontend implements vacancy discovery and a
four-step application flow using fictional fixtures and simulated services. A Django 5.2 backend
foundation now provides domain models, initial migrations, Django Admin registration, a health
endpoint, and read-only vacancy APIs. The frontend is not connected to the backend, and candidate
authentication, authorized drafts, uploads, real submission, deployment, and production operations
remain unimplemented.

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

The backend lives under `backend/` and uses Django, Django REST Framework, and PostgreSQL-ready
settings. SQLite is the local bootstrap and test database. PostgreSQL runtime behavior has not been
validated in this phase. The current API exposes only health and read-only published-vacancy routes;
fixture-backed frontend behavior remains unchanged.

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
|-- backend/
|   |-- apps/
|   |   |-- applications/
|   |   |-- documents/
|   |   `-- vacancies/
|   |-- config/
|   |-- tests/
|   |-- manage.py
|   `-- pyproject.toml
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

## Backend Setup

Requirements:

- Python 3.11, 3.12, or 3.13.
- PostgreSQL for later integration; SQLite is sufficient for the current local bootstrap and tests.

From the repository root on Windows PowerShell:

```powershell
Set-Location .\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

`backend/.env.example` documents the supported variables. Settings read process environment
variables directly; the file is not loaded automatically. Without `DATABASE_URL`, development and
tests use the ignored `backend/db.sqlite3` database. A PostgreSQL URL uses the form shown in the
example file.

Backend quality commands:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
```

## Simulated Behavior And Limitations

- Draft answers last only while the current application state remains in memory.
- Selecting a PDF reads browser-provided file metadata only; no file is uploaded or stored.
- Save and submission delays are fixture behavior, not API calls.
- Confirmation credentials and status responses are fixed fictional values.
- Client validation improves feedback but is not a security boundary.
- Server-side authorization, upload inspection, rate limiting, persistence, retention, and duplicate
  submission workflows are not connected to the frontend.
- Backend models exist, but anonymous draft authorization, status lookup, CV upload/storage, and
  submission services remain future work.
- No usability study or accessibility conformance audit has been completed.
- No CI, deployment, production database, or validated operational staff workflow exists; Django
  Admin registration is a foundation only.

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
