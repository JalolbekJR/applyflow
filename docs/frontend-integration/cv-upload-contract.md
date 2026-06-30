# CV Upload Contract

The current frontend-facing CV contract is PDF-only singleton metadata/upload/replacement/deletion
for the active draft.

## Verified Limits

| Limit             | Value                              | Source                                     |
| ----------------- | ---------------------------------- | ------------------------------------------ |
| File type         | PDF only                           | `backend/apps/documents/pdf_validation.py` |
| Maximum file size | `5,242,880` bytes, shown as 5 MB   | `backend/config/settings.py`               |
| Page count        | 1 through 10 pages                 | `backend/apps/documents/pdf_validation.py` |
| Request fields    | Exactly one multipart `file` field | `backend/apps/documents/views.py`          |

Browser validation is advisory. Backend validation is authoritative.

## Transport

- Endpoint: `PUT /api/v1/application-drafts/{draft_id}/documents/cv/`.
- Content type: `multipart/form-data`.
- Field: `file`.
- Required cookies: draft ownership cookie and CSRF cookie as managed by the browser.
- Required headers: `X-CSRFToken`, `If-Match`, `Accept: application/json`.
- Current frontend transport: `XMLHttpRequest` so upload progress and cancellation are available.
- Cancellation aborts the XHR and preserves the previous CV metadata in the UI.

## Metadata

Successful upload or replacement returns the draft aggregate with:

```json
{
  "original_name_display": "avery-example-cv.pdf",
  "detected_content_type": "application/pdf",
  "size": 42137,
  "uploaded_at": "2026-06-24T00:00:00Z"
}
```

No public URL, storage key, checksum, internal path, document UUID, or file bytes are returned.
The frontend does not render the PDF.

## Replacement

`PUT` creates the first CV with `201` and replaces an existing CV with `200`. Failed replacement must
not cause the frontend to assume the previous CV was deleted. The backend preserves the old active
document until the new file validates, stores, and commits.

## Deletion

`DELETE /api/v1/application-drafts/{draft_id}/documents/cv/` requires CSRF and `If-Match`. It returns
`204` and a fresh `ETag`. The frontend clears local document metadata only after the server confirms
success. Physical storage cleanup is backend-owned and retryable.

## Error Behavior

| Scenario                | Expected frontend behavior                                                               |
| ----------------------- | ---------------------------------------------------------------------------------------- |
| File too large          | Show "Upload a PDF file under 5 MB."; preserve other form values and previous CV if any. |
| Incorrect extension     | Treat browser rejection as advisory; backend may return `415 unsupported_file_type`.     |
| Misleading browser MIME | Backend rejects if declared or inspected content is not accepted.                        |
| Malformed PDF           | Show a recoverable invalid-PDF message; preserve current draft values.                   |
| Encrypted PDF           | Backend rejects as invalid PDF.                                                          |
| Page count over 10      | Backend rejects as invalid PDF.                                                          |
| Upload cancelled        | Show cancelled/network-style message; previous CV remains visible if one existed.        |
| Network failure         | Preserve local values and previous CV metadata; candidate can retry.                     |
| Server storage failure  | Show temporary service failure; do not claim upload succeeded.                           |
| Replacement failure     | Keep previous metadata visible; do not assume deletion.                                  |
| Deletion failure        | Keep metadata visible and explain the CV could not be removed.                           |
| Version conflict        | Stop unsafe mutation queue and show recoverable conflict state.                          |

Do not claim malware scanning. The backend performs size, extension, MIME, signature, structure, page
count, and active-content checks, but it is not an antivirus system.
