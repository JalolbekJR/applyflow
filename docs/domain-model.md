# Domain Model

Phase 2 implements the vacancy, application draft, submitted application, and document-metadata
schema with UUID identifiers and initial migrations. SQLite was used for local migration and test
validation; PostgreSQL configuration is present but runtime behavior was not tested.

## Diagram

```mermaid
erDiagram
    Vacancy ||--o{ ApplicationDraft : starts
    Vacancy ||--o{ Application : receives
    ApplicationDraft ||--o| ApplicationDocument : owns_before_submit
    Application ||--o| ApplicationDocument : owns_after_submit

    Vacancy {
        uuid id
        string title
        string slug
        text summary
        text description
        string status
        datetime published_at
        datetime closing_at
    }

    ApplicationDraft {
        uuid id
        uuid vacancy_id
        string secret_hash
        string full_name
        string email
        string email_normalized
        string phone
        string portfolio_url
        string preferred_contact_method
        string experience_level
        string_array skills
        text optional_message
        string consent_version
        boolean consent_acknowledged
        datetime expires_at
        datetime created_at
        datetime updated_at
        datetime submitted_at
    }

    Application {
        uuid id
        uuid vacancy_id
        string full_name
        string email
        string email_normalized
        string phone
        string portfolio_url
        string preferred_contact_method
        string experience_level
        string_array skills
        text optional_message
        string consent_version
        datetime consented_at
        string status
        string application_reference
        string status_lookup_secret_hash
        datetime submitted_at
        datetime created_at
        datetime updated_at
    }

    ApplicationDocument {
        uuid id
        uuid draft_id
        uuid application_id
        string original_name_display
        string storage_key
        string detected_content_type
        integer size
        datetime uploaded_at
        datetime deleted_at
    }

    AuditEvent {
        uuid id
        string target_type
        string target_identifier
        string event_type
        string actor_type
        datetime created_at
    }
```

## Vacancy

Implemented fields:

- `id`
- `title`
- `slug`
- `summary`
- `description`
- `responsibilities`
- `requirements`
- `benefits`
- `location`
- `work_format`
- `employment_type`
- `status` (`draft`, `published`, or `closed`)
- `published_at`
- `closing_at`
- `created_at`
- `updated_at`

Constraints and indexes:

- Unique slug.
- Index active and closing date for public lists.
- Closing date may be null.
- The current read-only API returns only published vacancies that have not passed their closing
  time. Closed-vacancy publication behavior can be reconsidered with frontend integration.

One vacancy record represents one publication in version one. A materially changed or reopened role is represented by a new vacancy record rather than a publication-cycle entity.

## ApplicationDraft

Use a separate draft model because drafts expire and can be abandoned, while submitted applications have different immutability and retention rules.

Primary candidate data uses explicit structured fields:

- `vacancy`
- `secret_hash`
- `full_name`
- `email`
- `email_normalized`
- `phone`
- `portfolio_url`
- `preferred_contact_method`
- `experience_level`
- `skills`
- `optional_message`
- `consent_version`
- `consent_acknowledged`
- `expires_at`
- `created_at`
- `updated_at`
- `submitted_at`

Do not place these fields in an unrestricted JSON blob. A small schema-bounded JSON field may be considered later for genuinely optional metadata, but it is not a version-one requirement.

Only a secure hash of a draft credential can be stored. Credential generation, cookie delivery,
authorization, one-active-draft-per-browser enforcement, and invalidation workflows are not yet
implemented.

## Application

The submitted application stores the copied structured candidate fields. The draft acknowledgement becomes an immutable `consented_at` timestamp paired with `consent_version`. It also stores:

- `status`
- `application_reference`
- `status_lookup_secret_hash`
- `consented_at`
- `submitted_at`
- lifecycle timestamps

Constraints and indexes:

- PostgreSQL unique constraint on `vacancy` plus `email_normalized`.
- Unique `application_reference`.
- Index vacancy and status for authorized admin review.
- Status is limited to `submitted`, `under_review`, or `closed`.
- Django Admin treats submitted candidate fields as read-only. Domain-service immutability and
  audited status changes remain future work.

The product rule is one submitted application per normalized email and vacancy record. The constraint is authoritative and submission occurs in an atomic transaction. A frontend pre-check is not sufficient protection.

## Skills

Do not create a reusable skill taxonomy in version one. Store a bounded structured list of normalized labels with the field limits defined in [field inventory](field-inventory.md). A separate skill entity is justified only by later filtering or taxonomy requirements.

## ApplicationDocument

The Phase 2 model stores document metadata and enforces exactly one owner plus at most one active
record per owner. It does not upload, save, inspect, expose, or delete file contents.

Planned rules:

- Exactly one owner: draft or application.
- At most one active document per owner.
- Generated private storage key; no user-controlled path fragments.
- Original filename retained only as sanitized display metadata when staff need it.
- Maximum 5 MB and PDF-only validation before persistence.
- Object-level authorization before download.
- Draft ownership transfers to the application inside the submission transaction.
- Abandoned and expired draft documents are deleted with the draft.
- Submitted documents follow the reviewed retention policy.

Do not add a scan-status field unless a scanner is actually integrated. Version one does not claim malware scanning.

## AuditEvent

Keep durable audit events narrow:

- Application-status changes.
- Authorized document access when operationally required.
- Expired-draft and document cleanup.
- Security-relevant administrative changes.

Audit records contain event category, actor type, target identifier, timestamp, and schema-bounded non-personal metadata only. They must not contain candidate contact data, document contents or paths, draft credentials, or status lookup credentials. ApplyFlow does not require event sourcing or analytics infrastructure.
