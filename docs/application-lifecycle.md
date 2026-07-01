# Application Lifecycle

Application drafts have their own expiration and submission behavior. They are not part of the submitted-application status lifecycle.

## Version-One States

| Internal State | Candidate-Facing Label | Meaning                                                     |
| -------------- | ---------------------- | ----------------------------------------------------------- |
| `submitted`    | Received               | The atomic submission completed.                            |
| `under_review` | Under review           | Authorized staff started review.                            |
| `closed`       | Closed                 | The application is no longer active in the review workflow. |

Candidate-facing responses remain minimal and never expose internal notes, ranking, staff identity, or rejection reasoning.

## Transitions

| From           | To             | Actor            | Notes                                               |
| -------------- | -------------- | ---------------- | --------------------------------------------------- |
| none           | `submitted`    | Candidate/API    | Created only by successful atomic draft submission. |
| `submitted`    | `under_review` | Authorized admin | Staff review starts.                                |
| `submitted`    | `closed`       | Authorized admin | Review closes without exposing an internal reason.  |
| `under_review` | `closed`       | Authorized admin | Review closes without exposing an internal reason.  |

Invalid transitions fail server-side. Privacy-safe audit events remain future operational work.

## Draft Outcomes

- Create: produce one server-side draft and protected credential when no active draft exists.
- Restore: return the existing draft for the same vacancy.
- Continue: restore the existing draft; never create another draft.
- Abandon: revoke the draft credential, make attached draft documents unavailable, then clear the
  credential cookie.
- Expire: reject future access immediately and let cleanup revoke, scrub, retry private storage
  deletion, and hard-delete the shell only after physical cleanup is confirmed.
- Submit: atomically create the application, transfer the document, mark the draft submitted, and invalidate its credential so it cannot be submitted again.

## Immutable After Submission

After submission, the candidate cannot edit:

- Vacancy
- Full name
- Email
- Phone
- Profile URL
- Preferred contact method
- Experience level
- Skills
- Optional message
- Consent version
- Submitted CV document

Authorized administrative corrections, if later permitted, require an explicit policy and audit event.

## Duplicate Submission

Allow one submitted application per normalized email and vacancy record. Enforce the rule with a PostgreSQL database constraint inside the atomic submission transaction. A materially changed or reopened role uses a new vacancy record, not a publication-cycle entity.

The API returns a generic conflict with useful status-lookup guidance without exposing another candidate's information.

## Document Behavior

- Draft document: deleted when the candidate removes it, abandons the draft, or the draft expires.
- Submitted document: retained and deleted according to the reviewed operational policy.
- Document download: deferred until explicit authorized staff access checks and a reviewed
  streaming response exist.

## Deferred States And Workflows

The following are not version-one states or requirements: `shortlisted`, `withdrawn`, `archived`, candidate-visible rejection reasons, candidate self-withdrawal, ranking, automated decisions, and candidate-visible internal notes. Adding any of them requires product, privacy, lifecycle, and test updates.

## Audit Expectations

For status changes, record actor type, timestamp, previous state, new state, and a non-personal reason category when required. Do not store email values, document paths, draft credentials, or status lookup credentials in audit logs.
