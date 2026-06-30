# Upload Security

CV upload is security-sensitive. A CV file contains personal data and may also contain malicious content.

Reference: [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).

## Implemented Slice 5 And 6 Controls

- Strict maximum file size: 5 MiB (`5,242,880` bytes); future proxy request ceiling 6 MiB for
  multipart overhead.
- One file per request, empty-file rejection, and chunked reads that stop at the limit.
- Allowed extension for version one: PDF only.
- Server-side extension validation.
- Declared MIME must be `application/pdf`, but browser-supplied MIME is not trusted.
- `%PDF-` must begin at byte zero.
- Strict structural parsing must find a coherent document with 1-10 pages and reject encryption,
  malformed structure, embedded files, JavaScript, `/OpenAction`, `/AA`, file-attachment
  annotations, RichMedia, Movie, Sound, Screen, and 3D annotations, plus active forms or automatic
  actions where detected.
- Do not render, execute, extract text, extract images, follow links, or invoke an external
  program.
- Server-generated storage names.
- Original filename normalized with basename extraction, Unicode NFKC, control removal, whitespace
  collapse, and a 120-character cap for escaped display metadata only.
- No user-controlled path fragments.
- Private storage through the application-owned document storage interface.
- No public executable upload directory.
- No candidate, public, or staff download endpoint in Phase 3.
- Abandoned-draft logical document retirement and post-commit physical deletion attempt.
- Logical deletion before retryable physical deletion.
- SHA-256 integrity metadata that is never returned or logged.
- Privacy-safe logs.
- Safe error responses.

Slice 5 pins `pypdf==6.14.1` after reviewing the exact release metadata. The base wheel is
BSD-3-Clause, supports Python 3.11 through `Requires-Python: >=3.9`, and has no runtime dependency
on Python 3.11 when installed without extras. Do not install `pypdf[crypto]`, `pypdf[full]`,
image, font, OCR, rendering, antivirus, or external-binary packages for this validator.

## Storage Naming

Do not use the original filename as a storage path.

Use a generated storage key such as:

```text
drafts/{draft_uuid}/{document_uuid}.pdf
```

This is illustrative. The final implementation must ensure candidates cannot control path fragments.

Slice 4 implements this canonical draft CV key shape. Both UUIDs are supplied by trusted server
code, rendered in lowercase canonical form, and validated again by every storage adapter before
filesystem access. The key excludes original filenames, names, emails, vacancy slugs, and other
candidate data.

## Validation Order

1. Confirm draft authorization, CSRF, active state, vacancy, and optimistic version.
2. Check request and file limits, reject declared size above 5 MiB, and still enforce the limit
   while streaming regardless of client metadata.
3. Check file presence and reject zero bytes.
4. Check extension and declared MIME allowlists.
5. Check the PDF signature.
6. Parse structure with the reviewed server-side library and reject malformed, encrypted,
   zero-page, over-ten-page, embedded, scripted, open-action, automatic-action, and forbidden
   annotation content.
7. Normalize display metadata, calculate SHA-256, and generate the storage key.
8. Store privately using bounded chunked temporary-file handling and clean temporary objects after
   every rejected or failed operation.
9. Persist metadata. Compensate by deleting the object if persistence fails.

The Slice 5 backend includes a standalone validation service. Slice 6 uses that service from the
authorized singleton CV endpoint and stores exactly the validated bytes that produced the checksum.
The validator uses `PdfReader(..., strict=True)`, rejects encrypted PDFs instead of decrypting them,
catches expected parser failures, returns only generic validation errors, and never extracts text,
images, fonts, attachments, XMP, or rendered content.

## Error Responses

Candidate-facing errors should be specific enough to recover and vague enough to avoid implementation details.

Examples:

- Upload a PDF file under 5 MB.
- We could not read that file type. Try exporting your CV as a PDF.
- The upload did not finish. Your form answers are still saved.

## Malware Scanning Limitation

Malware scanning is not part of the first local prototype unless explicitly implemented later. The project must not claim antivirus scanning exists before it does.

Slice 6 adds the metadata/upload/replacement/delete API and retryable deletion-attempt metadata.
Slice 8 adds the manual cleanup command for expired drafts, pending deletions, and stale orphans. It
does not add throttling infrastructure, public or staff download, cleanup scheduling, or malware
scanning. The storage layer guarantees bounded chunked copying and private key handling, not parser
sandboxing or antivirus protection.

The Slice 5 validator runs in process. Its size, page-count, strict parsing, object traversal, and
temporary-file limits reduce risk from hostile input, but they are not a sandbox and do not
guarantee protection from unknown parser vulnerabilities. Production hardening may later add
process or operating-system isolation after a separate review.

## Deferred File Types

DOC and DOCX are possible later extensions only after dedicated validation, storage, and security work. They are excluded from version one because they expand parser, archive-format, download, and rendering edge cases.

If scanning is later added, document:

- Engine or service.
- Failure mode.
- Quarantine behavior.
- Staff review flow.
- False-positive handling.
- Retention impact.

## Phase 3 Access Boundary

Phase 3 returns authorized document metadata only. It does not expose candidate, public, or staff
document content and never returns a storage URL. Django Admin shows metadata without a file link.

The implemented storage interface has no public URL method and returns no filesystem path. The local
private adapter stores only canonical keys beneath the configured private root, rejects traversal and
symlink escape attempts before access, rejects duplicate saves, cleans temporary files after failed
writes, and enumerates only canonical relative keys for cleanup work.

A future staff download requires authenticated object-level permission, an attachment-only
streaming response, safe response filename, `nosniff`, no public storage URL, and a privacy-safe
audit event. That work requires a later review and is not implied by upload implementation.

## Replacement And Deletion

- Receive into private temporary storage.
- Enforce the streaming byte limit.
- Calculate SHA-256.
- Validate the PDF.
- Write to a new opaque final key.
- Lock the draft and active document.
- Atomically activate new metadata and retire old metadata.
- Commit the transaction.
- Delete the retired object after commit.
- Retain retryable deletion metadata when physical deletion fails.
- Delete the newly stored object when database activation fails.
- A failed replacement leaves the old document active, and the previous valid object is never
  deleted before the new object is committed.

## Implemented Test Coverage

- Oversized upload rejected.
- Unsupported extension rejected.
- Browser MIME, extension, signature, or inspected-content mismatch rejected.
- Missing or invalid PDF signature rejected.
- Malformed or unreadable PDF rejected by the selected inspection library.
- Empty, encrypted, embedded-file, JavaScript, open-action, automatic-action, active-form,
  file-attachment-annotation, zero-page, and over-ten-page PDFs rejected.
- Malicious filename does not affect storage path.
- Unauthorized document access blocked.
- No public, candidate, or staff content route exists in Phase 3.
- Deleted draft document metadata is unavailable before physical cleanup.
- Valid upload persists metadata.
- Failed replacement preserves the old active document.
- Storage or metadata failure does not create an untracked live object.
- Logs and cleanup command output do not include file contents or storage keys.

Cleanup tests cover stale-orphan grace-period behavior, repeated cleanup runs, storage-failure
retry, and privacy-safe aggregate output. PostgreSQL-specific row-lock and concurrent replacement
behavior remains a separate production-readiness track.
