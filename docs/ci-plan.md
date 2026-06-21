# CI Plan

The Phase 1 frontend has local formatting, lint, type, unit, build, and Playwright commands. CI and
GitHub Actions workflows are not implemented and remain Phase 7 work.

Reference: [GitHub Actions documentation](https://docs.github.com/actions).

## Goals

- Block merges when checks fail.
- Run frontend and backend checks independently.
- Avoid deployment until tests and builds pass.
- Avoid workflows that require unavailable secrets.
- Add security-oriented repository checks when CI implementation begins.

## Frontend Checks To Run In CI

- Install dependencies.
- Lint.
- TypeScript checking.
- Unit tests.
- Nuxt production build.
- Playwright critical paths.

## Planned Backend Checks

- Install dependencies.
- Ruff.
- Optional mypy if configured.
- Migration consistency.
- pytest with PostgreSQL.
- Django system checks.
- Django deployment checks for production settings.
- Docker image build in later deployment phase.

## Repository Checks

- Secret scanning guidance.
- Dependency review guidance.
- Required pull-request checks.
- Branch protection recommendations.
- No deployment when checks fail.

## Suggested Workflow Split

Later workflows may be:

- `frontend-ci.yml`
- `backend-ci.yml`
- `e2e.yml`
- `docker-build.yml`

Create only the workflows supported by the relevant frontend or backend code.

## Branch Protection

Recommended later:

- Pull request required before merging to `main`.
- Required status checks.
- No direct pushes to `main`.
- Review required for security-sensitive changes.

## Deployment

Deployment automation is deferred to Phase 7. When deployment starts, use staging before
production and document rollback.
