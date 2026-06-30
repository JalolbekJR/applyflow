# Frontend Testing Contract

Use the smallest test set that matches the change, then expand when integration behavior changes.

## Visual-Only Changes

Run from `frontend/`:

```powershell
npm run format:check
npm run lint
npm run typecheck
npm run test
npm run build
npm run test:e2e
```

Also review responsive layout, keyboard/focus behavior, and reduced-motion behavior for affected
pages.

## Integration-Layer Changes

Run everything above, plus:

```powershell
npm run test:e2e:fullstack
```

The full-stack path must cover:

- Real Django CSRF bootstrap.
- Same-origin Nuxt proxy preserving `/api/v1/...`.
- Cookie-based draft creation and restoration.
- Candidate persistence.
- Experience persistence.
- Experience-entry create/update/delete where affected.
- CV upload, replacement, deletion, progress/cancel behavior where affected.
- Refresh restoration.
- Active-draft conflict and abandonment.
- Network/error preservation and version-conflict behavior where affected.

## Complete Frontend Replacement

Required before cutover:

- Full existing frontend contract suite.
- No frontend runtime fixture fallback for implemented APIs.
- Real backend integration.
- Supported viewport checks, including 320px and desktop.
- Keyboard and focus review.
- Security checklist from [security contract](security-contract.md).
- No localStorage/sessionStorage candidate data.
- No credential exposure.
- No public document URL.
- Review-page parity with the current frontend.
- Confirmation that submission and status lookup remain truthful and deferred.
- Side-by-side behavior comparison with the previous frontend.

## Backend Verification When Backend Contract Changes

Run from `backend/`:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe -m pytest
```

Frontend-only work should not require these except as regression evidence after coordinated API or
security changes.

## Test Types

| Type                                 | Current command or source                                      |
| ------------------------------------ | -------------------------------------------------------------- |
| Unit/component tests                 | `npm run test`                                                 |
| Mocked browser smoke                 | `npm run test:e2e`                                             |
| Real Django full-stack browser smoke | `npm run test:e2e:fullstack`                                   |
| Production frontend build            | `npm run build`                                                |
| Backend unit/API/security regression | `.\.venv\Scripts\python.exe -m pytest`                         |
| Manual accessibility                 | Keyboard, screen-reader, zoom, contrast, reduced-motion review |

## Unavailable Or Unverified

PostgreSQL runtime/concurrency validation, production deployment, CI, monitoring, backups,
scheduled cleanup, final submission, and private status lookup remain future work.
