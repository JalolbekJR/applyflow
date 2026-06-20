# ADR 0007 - Store CV Documents Privately With Server-Generated Names

Status: Accepted

## Context

CV upload is a security-sensitive subsystem. CV files contain personal data and may be intentionally malformed or malicious.

## Decision

Store uploaded CV documents in private storage using server-generated storage names. Preserve the original filename only as sanitized display metadata when staff need it. Do not serve uploads from a public executable media directory.

The first version accepts PDF only with a fixed 5 MB maximum. Server-side validation must check the extension allowlist, inspect the PDF signature and content, and control storage key construction. Browser-supplied MIME type is not trusted.

## Consequences

- Document access requires authorization.
- The backend controls storage keys and download headers.
- Local development can use private filesystem storage behind Django views.
- Production can later swap to private object storage without changing API behavior.
- Malware scanning is not part of the first local prototype unless explicitly added later.
- DOC and DOCX support is deferred because archive and parser behavior expands the validation and security surface.

## Alternatives Considered

- Public media URLs: rejected because private CV documents should not be publicly addressable.
- Original filename as storage path: rejected because filenames are user input.
- Extension-only validation: rejected because it is insufficient.
- DOC/DOCX in version one: rejected until dedicated validation, storage, and security work exists.

## Follow-Up Work

- Add upload tests for size, extension, signature/content mismatch, malformed PDF input, path traversal attempts, and authorization.
- Document retention and deletion behavior in implementation.
