# Runbook Outline

The Nuxt candidate draft path now uses the Django vacancy, anonymous draft, employment-entry, and
private CV metadata/upload APIs. Final submission and private status lookup remain Phase 4. Phase 2
adds the Django backend foundation, DRF configuration, database-backed domain models, migrations,
Django Admin registration, health endpoint, read-only public vacancy API, and
environment-driven PostgreSQL-ready settings. Local migrations and tests use SQLite; PostgreSQL
runtime behavior has not been verified.

This remains an outline because final submission, private status lookup APIs, cleanup automation,
deployment, monitoring, backup, and operational procedures are not implemented. Exact operational
procedures belong to the Phase 6 packaging and deployment work.

## Purpose

The runbook should help maintainers operate the application safely and recover from common issues.

## Planned Sections

1. System overview.
2. Environments.
3. Required secrets.
4. Deployment steps.
5. Rollback steps.
6. Database migration procedure.
7. Backup procedure.
8. Restore procedure.
9. Draft cleanup procedure.
10. Document deletion procedure.
11. Admin access procedure.
12. Incident checklist.
13. Log review.
14. Smoke tests.
15. Known limitations.

## Smoke Test Checklist

Later deployment smoke tests should verify:

- Home page loads.
- Vacancy index loads.
- Vacancy detail loads.
- Application draft can be created.
- Form validation works.
- Valid CV upload succeeds.
- Invalid upload fails safely.
- Final submission remains disabled until Phase 4.
- Status lookup remains unavailable until Phase 4.
- Admin login works only for staff.
- No public, candidate, or ordinary staff document download exists in Phase 3.

## Incident Checklist

If something goes wrong later:

1. Identify affected environment.
2. Stop making changes.
3. Capture request IDs and timestamps.
4. Check recent deployment or migration.
5. Check logs without exposing personal data in reports.
6. Roll back if user data or submission integrity is at risk.
7. Document cause and follow-up.

## Data Handling

The runbook must remind maintainers:

- Do not use real candidate data in demos.
- Do not paste CV contents into issues or logs.
- Do not expose environment secrets.
- Do not email or publish status lookup secrets.

## Not Ready Yet

The runbook cannot include backend, migration, deployment, backup, or rollback commands until those
systems and their target environment exist.
