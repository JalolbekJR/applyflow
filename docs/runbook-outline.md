# Runbook Outline

This is an outline for Phase 9. It is not an operational runbook yet because the application is not implemented or deployed.

## Purpose

The runbook should help Jalolbek JR operate the demo safely, recover from common issues, and explain operational thinking in interviews.

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
- Submission succeeds.
- Duplicate submission is blocked.
- Status lookup works for a valid application reference and status lookup secret.
- Invalid status lookup does not disclose information.
- Admin login works only for staff.
- Uploaded document download requires authorization.

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

The runbook cannot include exact commands until the app, Docker setup, CI, and deployment target exist.
