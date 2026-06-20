# ADR 0010 - Use Django Admin Instead Of A Custom Recruiter Dashboard

Status: Accepted

## Context

The first version needs internal vacancy and application management. A custom dashboard would compete with the candidate flow for time and scope.

## Decision

Use Django Admin for internal vacancy and application management in version one.

Admin access is staff-only and least privilege. Public candidate APIs remain separate from admin views. Production deployment must restrict and harden admin ingress, and document downloads require explicit authorization even for authenticated staff.

## Consequences

- The project can focus on the candidate experience.
- Internal operations can still review vacancies, submissions, documents, and status.
- Admin permission tests are still required.
- A custom recruiter dashboard remains a non-goal until user or business need justifies it.

## Alternatives Considered

- Custom recruiter dashboard: deferred because it adds UI scope without improving the portfolio's core candidate story.
- No internal management: rejected because vacancy content and application review need an operational interface.

## Follow-Up Work

- Configure admin list displays and readonly fields during backend implementation.
- Add permission tests for status changes and uploaded document access.
- Document production admin ingress controls before deployment.
