# Backend Architecture

## References Checked

- [Django deployment checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
- [Django REST Framework authentication](https://www.django-rest-framework.org/api-guide/authentication/)
- [Django REST Framework permissions](https://www.django-rest-framework.org/api-guide/permissions/)
- [Django REST Framework throttling](https://www.django-rest-framework.org/api-guide/throttling/)
- [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)

These references were checked before the Phase 2 implementation. Recheck official guidance before
dependency upgrades or production configuration.

## Implemented Foundation Stack

- Python 3.11.
- Django 5.2 LTS and Django REST Framework.
- PostgreSQL-ready settings through psycopg; SQLite for local bootstrap and tests.
- pytest, pytest-django, and Ruff.

OpenAPI generation, Docker, CI, and production deployment remain future work.

## Django Apps

Implemented apps:

- `vacancies`: public vacancy content and admin editing.
- `applications`: drafts, submitted applications, lifecycle, status lookup.
- `documents`: metadata ownership boundary only; no upload, storage, or download behavior.

Do not create a generic `core` app by default. Shared settings, URL routing, and project configuration belong in the Django project package. A small shared module can be added later only for concrete cross-app behavior such as audit event helpers or common timestamp mixins.

## Layering

| Layer | Responsibility |
| --- | --- |
| Models | Persistence, constraints, indexes, lifecycle timestamps. |
| Serializers | API validation and response shape. |
| Views/ViewSets | HTTP mapping, authentication, throttling, status codes. |
| Services | Domain operations that change state. |
| Selectors | Read queries when they become repeated or security-sensitive. |
| Permissions | Object-level and function-level access decisions. |
| Storage | Private document save, download, deletion. |
| Audit helpers | Privacy-safe event records. |

Views stay thin. Phase 2 implements only health and read-only vacancy views. State-changing services
remain planned for later phases.

## Future Services

- `create_application_draft(vacancy, request_context)`
- `update_application_draft(draft, data)`
- `attach_document_to_draft(draft, uploaded_file)`
- `remove_document_from_draft(draft, document_id)`
- `submit_application_draft(draft)`
- `create_status_lookup_credentials(application)`
- `delete_expired_drafts(now)`

These names are illustrative. Implementation should keep functions small and testable.

## Security Boundaries

- Admin authentication is separate from anonymous candidate access.
- Production admin ingress is restricted to authorized staff and hardened separately from public candidate routes; an obscure URL is not an access control.
- Staff permissions follow least privilege, including explicit authorization before document access.
- Candidate draft authorization uses server-generated secrets, not numeric IDs.
- Anonymous draft concurrency is limited to one active draft per browser in version one.
- Primary candidate data uses explicit structured model fields rather than an unrestricted JSON form blob.
- Document access checks ownership before reading storage.
- Server-side validation remains authoritative.
- Public APIs return generic errors when disclosure would help enumeration.
- Production settings must pass Django deployment checks.

Phase 2 defaults unmarked DRF views to staff-only permission. Health and published-vacancy views are
explicitly anonymous and read-only. Candidate authentication, draft authorization, document access,
and submission permissions are not implemented.

## Validation

Validation happens in both client and server, but the server decides:

- Vacancy is active.
- Draft token is valid and not expired.
- Required fields exist.
- Field lengths and formats are acceptable.
- Upload size and type are acceptable.
- Duplicate submission is blocked.
- Duplicate submission is scoped to one normalized email per vacancy record.
- Application status is one of `submitted`, `under_review`, or `closed`.
- Consent version is current.

## Observability

Observability remains planned; no backend telemetry is implemented.

Later implementation should keep operational logs privacy-safe and audit only the events that need durable accountability:

- Application status changes.
- Authorized document access when operationally required.
- Expired-draft and document cleanup.
- Security-relevant administrative changes.

Rate-limit and error metrics may use aggregate result categories, but they are not candidate analytics or a broad event-sourcing system.

Logs must not contain full names, emails, phone numbers, CV contents, document paths, draft secrets, or status lookup secrets.

## Rejected Architecture

- Repository pattern for every model.
- Command bus.
- Dependency injection framework.
- Event bus.
- Microservices.
- Background queue in version one.

These patterns can be reconsidered only if implementation creates a real need.
