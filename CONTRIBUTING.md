# Contributing To ApplyFlow

ApplyFlow is currently in Phase 0. Contributions should stay inside the active phase unless the maintainer explicitly opens a later phase.

## Branches

Do not work directly on `main`.

Suggested branch names:

- `phase-N-description`
- `feat/description`
- `fix/description`
- `docs/description`
- `security/description`

The current Phase 0 branch is `phase-0-product-architecture`.

## Commits

Use Conventional Commit style when commits are requested:

- `docs: update application lifecycle`
- `feat: add vacancy detail page`
- `fix: preserve form data after upload error`
- `test: cover duplicate submission`
- `security: harden document access`

Do not commit unless the user explicitly asks for a commit.

## Pull Requests

Pull requests should include:

- Purpose of the change.
- Scope and non-goals.
- Screenshots only when a real interface exists.
- Tests run and results.
- Accessibility checks when UI changes.
- Security notes when auth, uploads, documents, privacy, or admin behavior changes.
- Documentation updates.

## Phase 0 Workflow

Allowed:

- Product documentation.
- UX documentation.
- Architecture planning.
- Security planning.
- ADRs.
- Roadmap and learning notes.

Not allowed in Phase 0:

- Nuxt scaffold.
- Django scaffold.
- Docker files.
- Database migrations.
- CI workflow files.
- Package installs.
- Generated app boilerplate.
- Fake UI screenshots.

## Later Implementation Workflow

When implementation begins:

1. Define acceptance criteria.
2. Add or update tests with the behavior.
3. Keep changes scoped to the current phase.
4. Update docs and ADRs when decisions change.
5. Run the smallest meaningful checks locally.
6. Report failures honestly.

## Tests

Phase 0 has no automated tests.

Later phases should add:

- Backend pytest and pytest-django tests.
- Frontend Vitest and Vue Test Utils tests.
- Playwright end-to-end tests.
- Accessibility checks.
- Security-sensitive tests for authorization, uploads, throttling, and privacy-safe logging.

## Documentation Updates

Update documentation when a change affects:

- User flow.
- Field behavior.
- API contract.
- Data model.
- Security controls.
- Accessibility behavior.
- Test strategy.
- Deployment or operations.

## Migrations

Migrations are not allowed in Phase 0.

Later migrations must:

- Be reviewed before merging.
- Include constraints and indexes deliberately.
- Preserve data or include a documented migration strategy.
- Avoid real candidate data in examples.

## Accessibility Review

UI work must consider:

- Semantic landmarks.
- Logical headings.
- Persistent labels.
- Keyboard navigation.
- Visible focus.
- Error summary and inline errors.
- Reduced motion.
- Mobile touch targets.

## Security-Sensitive Changes

Extra review is required for:

- Authentication.
- Authorization.
- Draft tokens.
- Status lookup.
- CV upload.
- Document storage.
- Logging.
- Environment variables.
- Django Admin behavior.
- CORS, CSRF, cookies, or rate limits.

## Dependency Additions

Do not add dependencies casually.

When proposing a dependency, explain:

- Problem solved.
- Why existing tools are insufficient.
- Maintenance and security cost.
- License.
- Test impact.
- Alternative considered.

## Review Checklist

Before asking for review:

- The active phase was respected.
- Relevant docs were updated.
- Tests were added or intentionally deferred with a reason.
- Security and privacy impact was considered.
- Accessibility impact was considered.
- No secrets or real personal data were added.
- Commands and results are documented.
