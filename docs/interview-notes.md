# Architecture Rationale

This document explains the main product and technical choices. Implemented frontend and backend
behavior are identified separately from future submission, status lookup, and operational work.

## Why Nuxt Instead Of Plain Vue?

The implemented frontend uses Nuxt for file-based routing, application structure, runtime
configuration, composables, build tooling, and page metadata. Slice 7 is currently client-rendered
because `ssr: false` is configured. SSR or hybrid rendering can be reconsidered later through an
explicit frontend architecture task. Separate routes still give each application step meaningful
browser history, page metadata, and focus behavior.

## Why Django REST Framework?

The backend uses Django REST Framework for serializer validation, explicit permissions and draft
authorization, and consistent API views and responses backed by Django models and domain services.
Scoped throttling remains future work where status lookup, upload abuse controls, or deployment
requirements need it. Django Admin remains the staff workflow.

## Why PostgreSQL?

The backend is PostgreSQL-ready, but local validation still uses SQLite. Future submission work
needs transaction coverage, indexes, and a database constraint for duplicate protection that must be
validated on PostgreSQL before production use.

## Why No Candidate Account?

Accounts would add friction and scope to a flow that needs only anonymous draft protection,
submission, and private status lookup. Cross-device recovery can be reconsidered if evidence shows
that candidates need it.

## How Will Drafts Be Protected?

Drafts are protected with a server-generated high-entropy draft secret, stored as a hash and
delivered through a same-origin HttpOnly ownership cookie. A readable or numeric identifier is never
proof of ownership, and the frontend does not read or persist the raw credential.

## How Will CV Uploads Be Secured?

The server accepts PDF only with a 5 MB limit, validates extension, MIME type, signature, structure,
and unsafe content indicators, generates storage names, stores documents privately, and exposes only
authorized metadata and mutation endpoints. Browser MIME types are not trusted.

## How Will Duplicate Submission Be Prevented?

Final submission remains deferred. The future submission backend remains responsible for idempotent
handling, atomic submission, and the PostgreSQL constraint that enforces one submitted application
per normalized email and vacancy.

## How Does Status Lookup Stay Private?

Private status lookup remains deferred. The planned flow separates a readable application reference
from a high-entropy status secret. The reference supports communication but does not authorize
access. The backend must hash the secret, avoid logging it, rate-limit requests, and return generic
failures and minimal status data.

## Why Use Django Admin?

Django Admin is sufficient for the first staff workflow. A custom staff interface would expand the
scope before the vacancy and application operations have been validated.

## How Are Recoverable Errors Handled?

The frontend keeps entered values visible after validation, upload, save, and conflict failures.
Error summaries and page-level feedback move focus to a visible recovery point. Server errors map
back to the same field and summary model.

## Why Is Pinia Not Used?

Route state, local component state, a focused application composable, and typed services cover the
current ownership needs. A state library requires a demonstrated cross-route problem and a new ADR.
