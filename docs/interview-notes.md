# Architecture Rationale

This document explains the main product and technical choices. Implemented frontend behavior and
future backend work are identified separately.

## Why Nuxt Instead Of Plain Vue?

The implemented frontend uses Nuxt because public vacancy pages benefit from server-rendered HTML,
metadata, file-based routing, and route-level data loading. Separate routes also give each
application step meaningful browser history, page metadata, and focus behavior.

## Why Django REST Framework?

The planned backend needs serializer validation, explicit permissions, throttling, and a staff
workflow backed by Django Admin. DRF keeps those API responsibilities close to Django models and
domain services. Backend implementation has not started.

## Why PostgreSQL?

The planned submission workflow needs transactions, indexes, and a database constraint for
duplicate protection. PostgreSQL is the intended development and production database once backend
work begins.

## Why No Candidate Account?

Accounts would add friction and scope to a flow that needs only anonymous draft protection,
submission, and private status lookup. Cross-device recovery can be reconsidered if evidence shows
that candidates need it.

## How Will Drafts Be Protected?

The planned backend uses a server-generated high-entropy draft secret, stored securely and delivered
through a same-origin HttpOnly secure cookie. A readable or numeric identifier is never proof of
ownership. The current frontend keeps a simulated draft in memory only.

## How Will CV Uploads Be Secured?

The planned server accepts PDF only with a 5 MB limit, validates extension, signature, and content,
generates storage names, stores documents privately, and authorizes every download. Browser MIME
types are not trusted. The current frontend reads file metadata but does not upload file contents.

## How Will Duplicate Submission Be Prevented?

The current frontend blocks repeated activation while its simulated submission is pending. The
future backend remains responsible for idempotent handling, atomic submission, and the PostgreSQL
constraint that enforces one submitted application per normalized email and vacancy.

## How Does Status Lookup Stay Private?

The planned flow separates a readable application reference from a high-entropy status secret. The
reference supports communication but does not authorize access. The backend will hash the secret,
avoid logging it, rate-limit requests, and return generic failures and minimal status data.

## Why Use Django Admin?

Django Admin is sufficient for the first staff workflow. A custom staff interface would expand the
scope before the vacancy and application operations have been validated.

## How Are Recoverable Errors Handled?

The frontend keeps entered values visible after validation, upload, and simulated save failures.
Error summaries and page-level feedback move focus to a visible recovery point. Future server errors
must map back to the same field and summary model.

## Why Is Pinia Not Used?

Route state, local component state, a focused application composable, and typed services cover the
current ownership needs. A state library requires a demonstrated cross-route problem and a new ADR.
