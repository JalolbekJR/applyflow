# Field Inventory

Every candidate-facing field needs a reason. The form should not recreate a full CV.

## Validation Timing

- Basic format validation after blur.
- Step validation before continuing.
- Complete validation before final submission.
- Authoritative validation on the server.

Do not validate aggressively on every keystroke unless a field has a strict format and the feedback is not disruptive.

## Fields

| Field | Purpose | Required | Client Validation | Server Validation | Error Style | Privacy | Persistence | Logging |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Selected vacancy | Anchor the application to one role. | Yes | Slug exists in current route. | Active vacancy exists and accepts applications. | Page-level error if closed or missing. | Public plus application metadata. | Server draft. | Log vacancy id, not candidate data. |
| Full name | Identify the candidate for staff review. | Yes | Non-empty, reasonable length. | Trimmed, length limit, character sanity check. | Inline plus summary. | Personal data. | Server draft. | Do not log value. |
| Email | Contact and duplicate-submission checks. | Yes | Email format after blur. | Normalized, valid length, duplicate rules. | Inline plus summary. | Personal data. | Server draft. | Do not log value. |
| Phone | Optional alternate contact. | No | Length and phone-friendly characters when present. | Normalize where practical, length limit. | Inline. | Personal data. | Server draft. | Do not log value. |
| Portfolio, GitHub, or LinkedIn | Let candidate provide one relevant profile without many fields. | No | URL format when present. | URL scheme allowlist, length limit. | Inline. | Personal data. | Server draft. | Do not log value. |
| Preferred contact method | Avoid contacting the candidate through an unwanted channel. | Yes | Email or phone selected; phone requires a phone number. | Choice in allowlist and cross-field phone requirement. | Inline. | Preference data. | Server draft. | Log only validation failure type if needed. |
| CV upload | Primary experience evidence. | Yes | File selected, size shown, PDF extension hint. | PDF extension allowlist, maximum 5 MB, file-signature and content inspection, generated private storage name. | Upload-specific state plus summary. | Sensitive document. | Private server storage. | Never log contents, original name, or storage path. |
| Experience level | Give staff a rough review category. | Yes | Choice selected. | Choice in allowlist. | Inline. | Application data. | Server draft. | Safe to log validation category only. |
| Relevant skills | Provide structured signals without retyping a CV. | Yes | 1 to 12 tags, length limit. | Normalize labels, deduplicate, length limit. | Inline. | Application data. | Server draft. | Avoid full values in logs. |
| Optional short message | Candidate-specific context not obvious in the CV. | No | Character counter and max length. | Length limit, plain text only. | Inline. | Personal/application data. | Server draft. | Do not log value. |
| Privacy and consent acknowledgement | Record consent version before submission. | Yes | Checkbox checked. | Consent version required and current. | Inline plus summary. | Consent record. | Server draft and submitted record. | Log consent version, not full form. |

## Local Storage Policy

Do not place candidate personal data, draft secrets, status lookup secrets, application references, or CV metadata in localStorage.

Acceptable browser storage in version one:

- In-memory form state while the page is open.
- HttpOnly secure cookies set by the backend for draft authorization.
- Session-only UI preferences if needed, such as dismissed non-sensitive tips.

Sensitive data should live in the server draft until submitted or expired.

## Error Message Style

Errors should:

- Name the field.
- Explain what changed.
- Tell the candidate how to fix it.
- Avoid blame.
- Avoid exposing server internals.

Example:

> Upload a PDF file under 5 MB.

Not:

> Validation failed: unsupported MIME.

## Upload States

The upload control must support:

- Empty
- File selected
- Uploading
- Uploaded
- Failed
- Canceled
- Retrying
- Removed

Each state needs visible text and screen-reader announcement where appropriate.
