# CI Plan

Phase 0 plans CI only. No GitHub Actions workflow files are created yet.

Reference: [GitHub Actions documentation](https://docs.github.com/actions).

## Goals

- Block merges when checks fail.
- Run frontend and backend checks independently.
- Avoid deployment until tests and builds pass.
- Avoid workflows that require unavailable secrets.
- Add security-oriented repository checks when implementation begins.

## Planned Frontend Checks

- Install dependencies.
- Lint.
- TypeScript checking.
- Unit tests.
- Nuxt production build.
- Playwright critical paths when an app exists.

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

Do not create these until the relevant app code exists.

## Branch Protection

Recommended later:

- Pull request required before merging to `main`.
- Required status checks.
- No direct pushes to `main`.
- Review required for security-sensitive changes.

## Deployment

No deployment automation is planned for Phase 0. When deployment starts, use staging before production and document rollback.
