# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project does not have a released version yet.

## Unreleased

### Added

- Django 5.2 backend foundation with DRF, environment-based settings, and PostgreSQL configuration.
- UUID-backed vacancy, application draft, submitted application, and document-metadata models with
  initial migrations and database constraints.
- Django Admin registrations, a minimal health endpoint, and read-only vacancy API endpoints.
- Pytest and Ruff configuration with backend model, API, admin, settings, and constraint coverage.
- Nuxt 4 candidate-facing frontend with fictional vacancy fixtures and simulated services.
- Unit, component, and Playwright coverage for the Phase 1 candidate flow.
- ADR 0012 documenting the code-first design-validation workflow.
- Phase 0 documentation and architecture planning.
- Product, UX, frontend, backend, security, privacy, testing, infrastructure, and roadmap documents.
- Architecture decision records for initial technical and product choices.
- Repository operating contract for future agent work.
- Contribution guide for documentation and later implementation phases.
- MIT license.

### Changed

- Reconciled the roadmap so the backend foundation is Phase 2 and deferred design documentation is
  maintained as an ongoing track.
- Advanced the repository to a Phase 1 Nuxt frontend foundation using the running application as the primary design-review surface.
- Reconciled the README, roadmap, architecture notes, and governance rules with the implemented frontend and remaining backend work.
- Reconciled Phase 0 draft, status authorization, PDF upload, lifecycle, Nuxt 4, privacy, and admin-security decisions across the documentation.
- Corrected invalid application routes, form error relationships, focus behavior, mobile vacancy reading order, simulated failure recovery, clipboard recovery, and submission activation handling.

## Repository History

### Added

- Initial ApplyFlow repository.

### Changed

- Normalized repository line endings.
