# Frontend Security Contract

Every current or replacement frontend must preserve this contract.

## Same-Origin Requirement

- Browser API calls use relative `/api/v1/...` paths.
- Local Nuxt development uses a loopback proxy that preserves the complete `/api/v1/...` path.
- Production remains same-origin unless a future architecture decision explicitly changes it.
- Do not add broad CORS as a frontend convenience workaround.
- Do not hardcode production API origins into browser code.

## Draft Credential

- The draft credential is server-generated.
- The browser receives it only through the `applyflow_draft` HttpOnly cookie.
- JavaScript must never read, duplicate, store, serialize, log, or put the credential in frontend
  state.
- The credential must not appear in URLs, query parameters, localStorage, sessionStorage,
  IndexedDB, analytics, error reporting, screenshots, traces, or test snapshots.
- The backend stores only a secure hash of the raw secret.

## CSRF

- Django CSRF middleware remains enabled.
- The frontend obtains the masked token with `GET /api/v1/csrf/`.
- Unsafe requests send `X-CSRFToken`.
- Requests include cookies where required.
- Candidate APIs must not be marked CSRF-exempt.
- Do not solve CSRF failures by disabling protection, adding CORS, or exposing credentials to
  JavaScript.

## Candidate Data

- Do not store candidate data in localStorage, sessionStorage, IndexedDB, URLs, analytics, logs, or
  error-reporting payloads.
- Keep candidate data in in-memory frontend state and authorized server drafts.
- Do not add real candidate data to fixtures, screenshots, docs, or seed data.

## Version Conflicts

- Every authorized draft response returns `ETag: "draft-<version>"`.
- Every unsafe draft mutation sends `If-Match: "draft-<expected-version>"`.
- Missing `If-Match` returns `428 draft_version_required`.
- Stale versions return `409 draft_conflict`.
- A replacement frontend must not silently overwrite a conflict, merge stale data, or let an older
  response overwrite a newer local/server state.

## CV Privacy

- CV files are hostile input.
- Backend validation is authoritative; browser extension and MIME checks are usability only.
- No public CV URL exists.
- No inline PDF preview is implemented or approved.
- No antivirus or malware-scanning claim is implemented.
- The frontend must never expose storage keys, checksums, internal paths, document UUIDs, or raw CV
  contents.

## Logging And Diagnostics

Never log or send to diagnostics:

- Raw draft credential or credential hashes.
- CSRF token.
- Candidate name, email, or phone.
- Candidate request/response bodies.
- CV contents, storage key, internal path, original filename, or checksum.
- Full multipart payloads.

## Forbidden Shortcuts

- Replacing `/api/v1/...` with `/v1/...`.
- Storing the draft cookie value in JavaScript state.
- Using localStorage to survive refresh.
- Adding `django-cors-headers` to make a split-origin frontend easier.
- Marking draft or upload views CSRF-exempt.
- Removing `If-Match` because conflicts are inconvenient.
- Returning a storage URL or rendering the PDF in the browser.
- Claiming malware scanning because the backend validates PDF structure.
