# ApplyFlow Development Contract

ApplyFlow is currently in Phase 3: secure drafts, private CV upload, and frontend integration.
The frontend now uses real vacancy, draft, experience, employment-entry, CV, conflict, and
abandonment APIs. Final submission, private status lookup, cleanup scheduling, PostgreSQL runtime
validation, deployment, CI, monitoring, and backups remain future work.

## Before Editing

1. Inspect the repository, active branch, and working tree.
2. Read the documentation and ADRs relevant to the task.
3. Confirm that the work fits the active phase.
4. Write a short plan and acceptance criteria.
5. Preserve accepted architecture unless the task explicitly changes it.
6. Keep changes small and reviewable.

## Phase Boundary

Phase 3 allows same-origin Nuxt-to-Django integration, anonymous draft API usage, CSRF bootstrap,
candidate and experience persistence, employment-entry CRUD, private singleton CV
metadata/upload/replacement/deletion, conflict handling, abandonment, directly affected tests, and
directly affected documentation.

Do not add real final submission, real private status lookup, candidate accounts, cleanup scheduling,
PostgreSQL service setup, Docker, CI, deployment, monitoring, backups, or production infrastructure
during this phase. Figma work remains deferred while the connected plan prevents useful canvas
operations.

## Development Rules

- Preserve working behavior and avoid unrelated refactors.
- Explain every dependency addition before making it.
- Add or update tests when behavior changes.
- Keep route pages focused and components responsibility-specific.
- Keep implemented vacancy, draft, experience, entry, CV, and abandonment behavior backed by real
  APIs; keep final submission and status lookup clearly disabled or deferred.
- Implement loading, empty, error, unavailable, and success states where the workflow needs them.
- Preserve semantic HTML, keyboard behavior, visible focus, reduced motion, and mobile reflow.
- Treat client validation as user feedback, never as a security boundary.
- Treat uploaded files as hostile input; server-side PDF validation and private storage are
  authoritative, and browser validation is only usability feedback.
- Keep secrets and real personal data out of source, fixtures, tests, screenshots, and logs.
- Never weaken validation, security rules, or tests to make a check pass.

## Code And Documentation Authorship

- Write code, comments, documentation, and interface copy in the maintainer's direct voice.
- Describe product behavior and engineering decisions, not the process used to produce the text.
- Do not use portfolio-pitch, authorship-provenance, prompt-history, or generated-tutorial language in
  normal product documentation.
- Keep comments concise and use them only for non-obvious business rules, accessibility intent,
  security boundaries, compatibility constraints, or meaningful trade-offs.
- Make capability claims truthful. Distinguish implemented behavior, simulated behavior, planned
  work, assumptions, and observed evidence.
- Do not invent research, metrics, interviews, analytics, screenshots, test results, or security
  guarantees.

## Interaction Quality

Every major UI phase must recheck representative interactions in a browser or Playwright. Keep one
consistent, restrained, product-specific state language across responsive layouts, hover-capable
pointer hover, pressed or active feedback, focus-visible, disabled, loading or pending, touch, and
reduced-motion behavior. Interaction feedback must not shift layout, and touch users must never
depend on hover to understand or operate a control.

## Architecture And Security Rules

- Use separate routes for the four application steps.
- Use composables for shared application state and typed services for external boundaries.
- Do not add a state library without a demonstrated need and a superseding ADR.
- Do not store candidate data or authorization credentials in localStorage.
- Candidate authorization must never rely on numeric identifiers.
- Draft access uses high-entropy server-generated secrets through the protected HttpOnly ownership
  cookie; the frontend must never read, duplicate, or persist the raw credential.
- CV validation is server-side and does not trust browser MIME types or extensions alone.
- Uploaded documents must remain private by default.
- Django Admin access must remain separate from candidate access.

## Frontend Replacement Rule

- Read `docs/frontend-integration/README.md` before frontend architecture or integration changes.
- Visual changes may stay frontend-only when they preserve the documented API and security
  contracts.
- Integration changes must preserve relative `/api/v1/` paths, cookies, CSRF, `ETag`/`If-Match`,
  error semantics, private CV metadata, and deferred submission/status behavior.
- Models, migrations, draft credential rules, CSRF middleware, private storage, and PDF validation
  are outside frontend-only scope.
- Never rewrite both frontend and backend in one task unless explicitly authorized.
- Prefer a parallel `frontend-v2` for major redesigns.
- Never declare frontend replacement complete without real Django full-stack tests.
- Never remove the old frontend until the replacement passes the documented cutover checks.
- Do not use fixture fallback to hide API failures.
- Do not add CORS or disable CSRF as a shortcut.
- Backend contract changes must update frontend contract documentation and tests in the same task.

## Command And Change Reporting

- Run the relevant formatting, lint, type, test, build, and browser checks before completion.
- Report exact commands and their real results, including warnings and non-zero exits.
- Report retries, replacement commands, timeouts, blocked tools, parser errors, and changed
  approaches; do not hide failed attempts behind a later success.
- Do not claim completion while a required check is skipped or failing.
- Do not stage, commit, push, merge, deploy, migrate data, install packages, or modify external
  services unless the user explicitly approves that action.

## Completion Report

Report what changed, files changed, commands run, results, remaining risks, manual confirmation still
needed, and whether any branch change, staging, commit, push, merge, deployment, migration, package
install, or external action occurred.
