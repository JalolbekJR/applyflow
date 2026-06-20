# ApplyFlow Agent Contract

This repository is currently in Phase 0: product definition, UX direction, architecture, security planning, testing strategy, documentation standards, and implementation roadmap.

No production application has been implemented yet.

## Before Editing

Every future agent must:

1. Inspect the repository before editing.
2. Check the active branch and working tree.
3. Read the relevant documentation and ADRs.
4. Respect the active phase.
5. Write a short plan before changing files.
6. Define acceptance criteria for the task.
7. Preserve existing architecture decisions unless the task explicitly changes them.
8. Keep changes small and reviewable.

## Phase Boundary

Stop at the current phase boundary.

Do not start Nuxt, Django, Docker, CI, database, deployment, or Figma implementation work unless the user explicitly moves the project into that phase.

For Phase 0:

- Documentation and ADRs are allowed.
- Root governance files are allowed.
- Application source code is not allowed.
- Generated boilerplate is not allowed.
- Package lockfiles are not allowed.
- Fake screenshots or fake test results are not allowed.

## Development Rules

Future implementation work must:

- Avoid unrelated refactors.
- Explain every dependency addition.
- Add or update tests with behavior changes.
- Update documentation when behavior changes.
- Preserve architecture decisions or create a superseding ADR.
- Keep views/controllers thin.
- Enforce permissions server-side.
- Treat uploaded files as hostile input.
- Preserve accessibility in every feature.
- Implement loading, empty, error, and success states.
- Run checks before reporting completion.
- Report exact commands and failures honestly.
- Never weaken validation, security, or tests simply to make CI pass.
- Never commit or push unless explicitly instructed.

## Project Anti-Patterns

Avoid:

- One giant multi-step form component.
- Hidden labels.
- Generic cards everywhere.
- Authentication tokens in localStorage.
- Frontend-only authorization.
- Extension-only file validation.
- Predictable status identifiers.
- Real personal data in fixtures, tests, screenshots, or demo data.
- Invented usability findings.
- Generic AI-generated copy.
- Premature state libraries.
- Unnecessary microservices.
- Custom recruiter dashboards before Django Admin has been used.
- WebGL or excessive visual effects for the application flow.

## Documentation Rules

Documentation must:

- Separate observed issues from assumptions.
- State when no user research has been conducted.
- Avoid fabricated metrics, interviews, analytics, and findings.
- Use direct language and concrete decisions.
- Link to relevant ADRs when decisions matter.
- Mark unresolved choices clearly.

## Security Rules

Security-sensitive changes require extra care:

- Draft access must use high-entropy server-generated secrets.
- Candidate authorization must not rely on numeric IDs.
- CV uploads must be validated server-side.
- Browser-supplied MIME types are not trusted.
- Uploaded documents must not be public by default.
- Logs must avoid personal data and uploaded file contents.
- Django Admin access must remain separate from candidate access.
- Production secrets must stay out of the repository.

## Reporting Completion

When finishing a task, report:

- What changed.
- Files changed.
- Commands run.
- Results.
- Risks.
- Manual confirmation still needed.
- Whether any commit, push, branch change, deployment, migration, package install, or external action occurred.
