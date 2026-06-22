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

- Custom recruiter dashboard: deferred because it adds staff-interface scope before the core workflow is validated.
- No internal management: rejected because vacancy content and application review need an operational interface.

## Follow-Up Work

- Configure admin list displays and readonly fields during backend implementation.
- Add permission tests for status changes and uploaded document access.
- Document production admin ingress controls before deployment.

## Current Status

Phase 2 registers vacancies, drafts, submitted applications, and document metadata with practical
list columns, filters, searches, and readonly identifiers. Credential hashes and storage keys are
excluded. Staff workflow validation, object-level document authorization, and production ingress
hardening remain unimplemented.
