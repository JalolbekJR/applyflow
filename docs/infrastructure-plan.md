# Infrastructure Plan

Phase 0 documents infrastructure only. No Docker files or deployment configuration are created in this phase.

## Local Development Services

Planned later services:

- Frontend: Nuxt development server.
- Backend: Django development server.
- Database: PostgreSQL.
- Private document storage: local private directory served only through authorized Django views.

Redis and Celery are not planned for version one. Cleanup can start as a Django management command until a real queue requirement appears.

## Production Topology

```mermaid
flowchart TD
    Browser["Candidate browser"] --> Proxy["HTTPS reverse proxy"]
    Proxy --> Nuxt["Nuxt frontend"]
    Proxy --> Django["Django API and Admin"]
    Django --> Postgres["PostgreSQL"]
    Django --> Storage["Private document storage"]
    Admin["Authorized staff browser"] --> AdminIngress["Restricted admin ingress"]
    AdminIngress --> Proxy
```

## Deployment Approach

Prefer same-origin deployment. See [ADR 0009](decisions/0009-same-origin-deployment.md).

Planned concerns:

- HTTPS termination.
- Secure cookies.
- CSRF protection.
- Static assets.
- Private media/document access.
- Restricted and hardened Django Admin ingress; an obscure path is not an access control.
- Least-privilege staff permissions and explicit document authorization.
- Environment validation.
- Database migrations.
- Health checks.
- Backup and restore.
- Log retention.

## Docker Planning

Docker files are deferred until Phase 9.

Planned requirements:

- Multi-stage builds.
- Pinned base image versions.
- Non-root runtime where practical.
- `.dockerignore`.
- Separate development and production configuration.
- Health checks.
- Explicit environment variables.
- No secrets baked into images.

## Environment Variables

`.env.example` is present for local development shape only. Real secrets must not be committed.

Likely future variables:

- `APP_ENV`
- `DEBUG`
- `DATABASE_URL`
- `DJANGO_SECRET_KEY`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `CORS_ALLOWED_ORIGINS` only if split-origin dev needs it
- `DOCUMENT_STORAGE_BACKEND`
- `DOCUMENT_MAX_UPLOAD_MB`
- `SECURE_COOKIE_SETTINGS`

## Backup And Restore

Before real recruitment use, define:

- PostgreSQL backup schedule.
- Document storage backup schedule.
- Restore drill.
- Retention policy.
- Deletion handling.

For portfolio demo data, keep backups small and do not include real personal data.

## Runbook Link

Operational procedures are outlined in [runbook outline](runbook-outline.md).
