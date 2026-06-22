# ADR 0002 - Use Django REST Framework And PostgreSQL For The Backend

Status: Accepted

## Context

ApplyFlow needs vacancy management, draft applications, secure document upload, status lookup, server-side validation, and a maintainable staff workflow.

## Decision

Use Django, Django REST Framework, and PostgreSQL.

Django Admin will support internal vacancy and application management. Django REST Framework will expose versioned REST endpoints for the Nuxt frontend. PostgreSQL will enforce constraints, indexes, uniqueness, and transactional submission behavior.

## Consequences

- The backend can enforce authorization, validation, and duplicate-submission rules server-side.
- PostgreSQL constraints reduce reliance on application-only validation.
- DRF serializers can centralize API validation and error mapping.
- The implementation must avoid turning a small app into ceremonial architecture.

## Alternatives Considered

- FastAPI: good API framework, but Django Admin and the requested Django skill set make Django a better fit.
- SQLite: acceptable for early local experiments, but the planned backend should use PostgreSQL to match constraints and deployment expectations.
- Microservices: rejected because one developer and one domain do not justify the overhead.

## Follow-Up Work

- Phase 2 selected Python 3.11, Django 5.2 LTS, DRF 3.17, and psycopg 3.3.
- Add OpenAPI generation during backend implementation.
- Add pytest and pytest-django coverage with PostgreSQL.

## Current Status

The Django foundation, models, migrations, admin registration, health endpoint, and read-only
vacancy API are implemented. SQLite was used locally. PostgreSQL settings parsing is tested, but an
actual PostgreSQL connection was not validated.
