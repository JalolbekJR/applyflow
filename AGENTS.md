# ApplyFlow Development Contract

ApplyFlow is currently in Phase 2: Django backend foundation. Phase 1 delivered the candidate-facing
Nuxt frontend, which still uses fixtures and simulated services. The backend now provides schema,
admin, health, and read-only vacancy foundations but is not integrated with the frontend.

## Before Editing

1. Inspect the repository, active branch, and working tree.
2. Read the documentation and ADRs relevant to the task.
3. Confirm that the work fits the active phase.
4. Write a short plan and acceptance criteria.
5. Preserve accepted architecture unless the task explicitly changes it.
6. Keep changes small and reviewable.

## Phase Boundary

Phase 2 allows Django and DRF configuration, PostgreSQL-ready settings, domain models, migrations,
Django Admin registration, read-only vacancy APIs, backend tests, and directly affected
documentation.

Do not add candidate authentication, draft authorization workflows, CV upload or storage, frontend
API integration, Docker, CI, deployment, monitoring, or production infrastructure during this
phase. Figma work remains deferred while the connected plan prevents useful canvas operations.

## Development Rules

- Preserve working behavior and avoid unrelated refactors.
- Explain every dependency addition before making it.
- Add or update tests when behavior changes.
- Keep route pages focused and components responsibility-specific.
- Keep fixture-backed save, upload, submission, and status behavior clearly labeled as simulated.
- Implement loading, empty, error, unavailable, and success states where the workflow needs them.
- Preserve semantic HTML, keyboard behavior, visible focus, reduced motion, and mobile reflow.
- Treat client validation as user feedback, never as a security boundary.
- Treat uploaded files as hostile input in the planned backend.
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
- Future draft access must use high-entropy server-generated secrets.
- Future CV validation must be server-side and must not trust browser MIME types or extensions alone.
- Uploaded documents must remain private by default.
- Django Admin access must remain separate from candidate access.

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
