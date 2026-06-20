# Upload Security

CV upload is security-sensitive. A CV file contains personal data and may also contain malicious content.

Reference: [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).

## Planned Controls

- Strict maximum size. Planned first limit: 5 MB.
- Allowed extension for version one: PDF only.
- Server-side extension validation.
- Server-side PDF file-signature and content inspection.
- Browser-supplied MIME type is not trusted.
- Server-generated storage names.
- Original filename retained only as sanitized display metadata when staff need it.
- No user-controlled path fragments.
- Private storage.
- No public executable upload directory.
- Safe download headers.
- Authorization before file access.
- Upload throttling.
- Abandoned-draft cleanup.
- Deletion behavior tied to retention policy.
- Privacy-safe logs.
- Safe error responses.

## Storage Naming

Do not use the original filename as a storage path.

Use a generated storage key such as:

```text
applications/{year}/{month}/{uuid}/{generated-name}
```

This is illustrative. The final implementation must ensure candidates cannot control path fragments.

## Validation Order

1. Check request size limits.
2. Confirm draft authorization.
3. Check file presence.
4. Check size.
5. Check extension allowlist.
6. Inspect the PDF signature and content structure with the selected server-side library; reject mismatches or unreadable content.
7. Generate storage key.
8. Store privately.
9. Persist metadata.

## Error Responses

Candidate-facing errors should be specific enough to recover and vague enough to avoid implementation details.

Examples:

- Upload a PDF file under 5 MB.
- We could not read that file type. Try exporting your CV as a PDF.
- The upload did not finish. Your form answers are still saved.

## Malware Scanning Limitation

Malware scanning is not part of the first local prototype unless explicitly implemented later. The project must not claim antivirus scanning exists before it does.

## Deferred File Types

DOC and DOCX are possible later extensions only after dedicated validation, storage, and security work. They are excluded from version one because they expand parser, archive-format, download, and rendering edge cases.

If scanning is later added, document:

- Engine or service.
- Failure mode.
- Quarantine behavior.
- Staff review flow.
- False-positive handling.
- Retention impact.

## Download Behavior

Only authenticated staff with explicit object-level permission should download submitted CVs.

Downloads should use:

- Authorization check before storage access.
- Non-inline content disposition unless a reviewed preview feature is added.
- Safe filename for the response.
- Audit event without raw path or candidate personal data.

## Tests Required Later

- Oversized upload rejected.
- Unsupported extension rejected.
- Browser MIME, extension, signature, or inspected-content mismatch rejected.
- Missing or invalid PDF signature rejected.
- Malformed or unreadable PDF rejected by the selected inspection library.
- Malicious filename does not affect storage path.
- Unauthorized document access blocked.
- Staff without document permission cannot download a CV.
- Deleted draft document is not downloadable.
- Valid upload persists metadata.
- Logs do not include file contents or storage keys.
