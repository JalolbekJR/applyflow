# ApplyFlow

ApplyFlow is a candidate-facing vacancy and job application experience built around a short,
transparent application process.

Phase 3 implementation is in progress. A Nuxt 4 frontend implements vacancy discovery and a
four-step application flow. Django 5.2 and DRF provide health, vacancy, anonymous draft,
experience-entry, and private singleton CV metadata/upload/delete APIs. The current frontend uses
the real vacancy, draft, experience, employment-entry, CV, conflict, and abandonment APIs through a
same-origin `/api/v1/` boundary. Final submission, private status lookup, deployment, cleanup
scheduling, monitoring, backups, and production operations remain incomplete. Phase 3 now includes
an isolated PostgreSQL verification boundary for runtime concurrency and constraint evidence.

## Current Frontend

The frontend currently includes:

- API-backed home, vacancy index, and vacancy detail pages.
- Position, candidate details, experience, and review application routes backed by authorized
  server drafts.
- Client-side validation with error summaries and grouped-control associations.
- In-memory draft aggregate restored from the authorized active-draft endpoint.
- Candidate, experience, optional employment-entry, CV upload/replacement/deletion, and abandonment
  integration.
- XHR upload progress and cancellation for CV files.
- Submission and private status lookup routes that remain intentionally unavailable.
- Loading, empty, unavailable, validation, save-failure, upload-failure, and success states.
- Responsive layouts from 320px upward, keyboard navigation, route focus, and reduced-motion support.
- Vitest component/unit tests, mocked Playwright browser tests, and a real Django full-stack
  Playwright smoke harness.

Seeded test vacancies and example candidate values are fictional. Do not use ApplyFlow with real
candidate information until the remaining privacy, legal, accessibility, operational, and
production-readiness gates are complete.

## Architecture

Frontend application code lives under `frontend/app/` and follows Nuxt 4 conventions:

- `pages/` owns route-level behavior and metadata.
- `components/` owns focused, accessible interface elements.
- `composables/` coordinates vacancy and application state across routes.
- `api/` provides typed same-origin API clients, CSRF bootstrap, response guards, and upload
  transport.
- `branding/` provides source-controlled brand and presentation configuration.
- `utils/` contains validation, cloning, and focus behavior.
- `types/` defines the shared frontend domain model.

The current draft is held in Nuxt state and rehydrated from the backend active-draft endpoint.
Candidate data, draft credentials, CSRF tokens, document storage keys, and status secrets are not
written to localStorage or sessionStorage. The draft ownership credential is HttpOnly and
browser-managed.

The backend lives under `backend/` and uses Django, Django REST Framework, and PostgreSQL-ready
settings. SQLite is the local bootstrap and fast test database. A test-only PostgreSQL verification
boundary covers row-lock, concurrency, constraint, cleanup, and rollback evidence and must be rerun
against an actual PostgreSQL service before release or production-readiness claims. The API keeps a
same-origin modular monolith with one active
browser-owned draft at a time, a host-only HttpOnly ownership cookie, seven-day inactivity expiry
bounded by a thirty-day absolute lifetime and the vacancy deadline, `ETag`/`If-Match` optimistic
concurrency, and singleton private CV metadata/upload/delete endpoints with no candidate download
route.

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
    |   |-- api/
    |   |-- branding/
    |   |-- types/
    |   `-- utils/
    |-- tests/
    |   |-- e2e/
    |   |-- fixtures/
    |   `-- unit/
    |-- nuxt.config.ts
    |-- playwright.fullstack.config.ts
    |-- package.json
    |-- playwright.config.ts
    |-- proxy-target.ts
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

Playwright starts the Nuxt development server automatically on `127.0.0.1:3000`. The full-stack
smoke harness starts Django and Nuxt against a temporary SQLite database and private document root:

```powershell
npm run test:e2e:fullstack
```

Browser-review screenshots and Playwright traces are generated artifacts and are ignored by Git
unless a failure output directory is intentionally inspected during debugging.

## Backend Setup

Requirements:

- Python 3.11, 3.12, or 3.13.
- PostgreSQL for opt-in verification and later production integration; SQLite is sufficient for the
  default local bootstrap and fast tests.

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

PostgreSQL verification is separate from the ordinary SQLite suite. See
[PostgreSQL verification](docs/postgresql-verification.md) for the test-only Compose service,
required environment variables, focused PostgreSQL commands, and teardown. PostgreSQL-only tests are
marked and skip explicitly when SQLite is selected.

Draft cleanup is an explicit management command. It defaults to a privacy-safe dry-run:

```powershell
.\.venv\Scripts\python.exe manage.py cleanup_application_drafts
.\.venv\Scripts\python.exe manage.py cleanup_application_drafts --apply --batch-size 100 --orphan-grace-hours 24
```

Only run `--apply` against disposable synthetic data or an approved environment with a reviewed
retention procedure. Scheduling, production object storage, production PostgreSQL topology,
monitoring, backups, and deployment remain separate work.

## Replacing Or Redesigning The Frontend

The frontend is replaceable. Visual redesigns, component changes, and source-controlled
white-label variants can stay frontend-only when they preserve the API and security contract.

Read [the frontend integration contract](docs/frontend-integration/README.md) before frontend
architecture or integration changes. Major redesigns should use a parallel `frontend-v2` until the
documented cutover checks pass. Normal frontend redesigns do not require backend or database
changes. Persisted-field changes, endpoint changes, draft-security changes, upload-policy changes,
or API-semantic changes require coordinated backend work.

## Implemented Boundaries And Limitations

- Draft answers persist in authorized server drafts while the draft cookie and server lifecycle
  remain valid.
- Selecting a valid PDF uploads to private backend-managed storage and returns metadata only.
- Save operations for implemented draft fields are real API calls.
- Submission credentials and status lookup are not implemented.
- Client validation improves feedback but is not a security boundary.
- Server-side authorization, retention, CSRF, ETags, PDF validation, and private storage are
  implemented for Phase 3 draft and CV APIs.
- The cleanup command supports dry-run/apply modes for expired drafts, pending private-document
  deletion, stale draft-storage orphans, and verified draft-shell hard deletion. Scheduling,
  production rate limiting, duplicate final submission workflows, deployment, and production
  operations remain future work.
- No usability study or accessibility conformance audit has been completed.
- No CI, deployment, production database, or validated operational staff workflow exists; Django
  Admin registration is a foundation only.

Do not use the current frontend to collect real candidate information.

## Documentation

- [Product brief](docs/product-brief.md)
- [Frontend architecture](docs/frontend-architecture.md)
- [Frontend integration contract](docs/frontend-integration/README.md)
- [Accessibility plan](docs/accessibility.md)
- [Testing strategy](docs/testing-strategy.md)
- [PostgreSQL verification](docs/postgresql-verification.md)
- [Upload security](docs/upload-security.md)
- [Threat model](docs/threat-model.md)
- [Implementation roadmap](docs/implementation-roadmap.md)
- [Architecture decisions](docs/decisions/index.md)

## License

ApplyFlow is available under the [MIT License](LICENSE).
