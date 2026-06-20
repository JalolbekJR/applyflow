# Implementation Roadmap

This roadmap keeps ApplyFlow small enough to finish and deep enough to explain.

## Phase 0 - Product And Architecture Foundation

Objective: define product scope, UX direction, architecture, security model, testing strategy, and documentation standards.

Deliverables:

- Product and UX documents.
- Architecture documents.
- Security, privacy, upload, and threat-model documents.
- ADRs.
- Phase 1 prompt and acceptance criteria.

Acceptance criteria:

- No application source code.
- No package installs.
- No generated boilerplate.
- Required docs and ADRs exist.
- Decisions are specific and internally consistent.

Required tests: documentation review only.

Security considerations: no secrets, no real personal data, no fake security claims.

Learning goals: understand scope, decisions, and why version one is intentionally small.

Non-goals: implementation, deployment, Figma file creation, fake UI screenshots.

## Phase 1 - UX Foundations And Figma Preparation

Objective: turn Phase 0 product direction into low-fidelity UX artifacts and manual Figma preparation.

Deliverables:

- Final fictional company direction.
- Reviewed field inventory draft ready for later user validation.
- Low-fidelity page structure.
- Complete user flow.
- Mobile-first layout decisions.
- Design-token proposal.
- Component inventory.
- Error and upload state sketches.
- Accessibility annotations.
- Figma task checklist.

Acceptance criteria:

- Northline Studio identity is refined but not overbuilt.
- Every field still has a reason.
- Step routes match the information architecture or a new ADR explains changes.
- Mobile layouts are designed before desktop polish.
- Error, empty, loading, upload, and confirmation states are represented.
- Accessibility annotations cover headings, focus, labels, errors, and keyboard path.
- No production application code unless Phase 1 is later explicitly expanded.

Required tests: low-fidelity usability review plan and heuristic review; no automated tests.

Security considerations: upload and privacy copy must remain visible in the flow.

Learning goals: user flow, IA, field reasoning, wireframes, design tokens, accessibility annotations.

Non-goals: Nuxt scaffold, Django scaffold, high-fidelity UI, implemented components.

## Phase 2 - High-Fidelity Design System

Objective: create polished desktop and mobile Figma screens and component variants.

Deliverables:

- Design tokens.
- Component variants.
- Desktop screens.
- Mobile screens.
- Interactive prototype.
- Accessibility annotations.
- Developer handoff notes.

Acceptance criteria:

- Form states are complete.
- Upload states are complete.
- Review and confirmation screens are complete.
- Mobile flow is not a compressed desktop layout.
- Prototype can support usability testing.

Required tests: usability test or clearly labeled heuristic review; accessibility design review.

Security considerations: no real candidate data in designs; application-reference, status-secret, and CV examples are fictional.

Learning goals: component variants, prototyping, visual hierarchy, responsive design.

Non-goals: frontend implementation, backend implementation, fake user findings.

## Phase 3 - Nuxt Foundation

Objective: scaffold the frontend and implement public page foundations.

Deliverables:

- Nuxt project.
- TypeScript configuration.
- Nuxt 4 `frontend/app/` structure with only the directories needed by implemented responsibilities.
- Route structure.
- Layouts.
- CSS token foundation.
- Vacancy index/detail static or mocked API integration.
- Test foundation.

Acceptance criteria:

- Public pages are responsive.
- Semantic landmarks and skip link exist.
- No giant application form component.
- Checks run locally and are reported honestly.

Required tests: lint/typecheck/build where configured, basic component tests.

Security considerations: no candidate data storage; no secrets in frontend.

Learning goals: Nuxt pages, layouts, SSR, hydration, TypeScript, CSS architecture.

Non-goals: complete application flow, Django API, production deployment.

## Phase 4 - Application Flow

Objective: implement frontend application steps with validation, progress, review, and recoverable errors.

Deliverables:

- Position, details, experience, and review routes.
- Client validation.
- Draft serialization adapters.
- Upload UI states without final backend storage if backend is not ready.
- Review/edit behavior.
- Accessibility behavior.

Acceptance criteria:

- Keyboard users can complete the flow with mocked API responses.
- Form data is preserved after recoverable API errors.
- Upload failure and retry states are visible.
- Reduced-motion preference is respected.

Required tests: unit/component tests and Playwright happy path with mocked backend.

Security considerations: no localStorage for personal data or tokens.

Learning goals: form state, props/emits, composables, API error mapping, accessibility testing.

Non-goals: real document storage, final submission persistence.

## Phase 5 - Django And DRF Foundation

Objective: scaffold backend and implement vacancy/application domain foundation.

Deliverables:

- Django project.
- Apps for vacancies, applications, documents.
- PostgreSQL configuration.
- Models and migrations.
- DRF serializers/views.
- Django Admin setup.
- Backend tests.

Acceptance criteria:

- Vacancy list/detail API works.
- Admin can manage fictional vacancies.
- Draft and application primary candidate data use explicit structured fields.
- Application status is limited to `submitted`, `under_review`, and `closed`.
- Server-side validation exists.
- Tests use PostgreSQL.

Required tests: pytest, Ruff, migration checks, Django system checks.

Security considerations: admin auth, CSRF, settings separation, no DEBUG in production settings.

Learning goals: models, migrations, serializers, permissions, ViewSets, tests.

Non-goals: full upload security, deployed infrastructure.

## Phase 6 - Drafts And Secure Upload

Objective: implement anonymous drafts and private CV upload.

Deliverables:

- Draft model and authorization.
- Draft cleanup command.
- Private document storage.
- Upload validation.
- Document delete.
- Upload tests.

Acceptance criteria:

- Draft secret is high entropy and not stored in localStorage.
- Unauthorized draft/document access fails.
- Non-PDF uploads and invalid sizes fail.
- Starting a second anonymous draft requires continue-or-abandon handling.
- Expired drafts and documents can be cleaned up.

Required tests: draft auth, upload validation, document access, cleanup.

Security considerations: uploaded files treated as hostile; no public media access.

Learning goals: file storage, transactions, throttling, privacy-safe logs.

Non-goals: malware scanning unless explicitly added.

## Phase 7 - Integrated Submission And Status Lookup

Objective: connect frontend and backend for final submission and private status lookup.

Deliverables:

- Atomic draft submission.
- Duplicate protection.
- Application reference generation.
- Status lookup secret generation and hashing.
- Status lookup endpoint and UI.
- Integrated API error handling.
- End-to-end tests.

Acceptance criteria:

- Duplicate submissions are blocked.
- Duplicate protection is enforced atomically for one normalized email per vacancy record.
- Confirmation shows a fictional application reference and a separate status lookup secret.
- Status lookup reveals only minimal status.
- Invalid lookup returns a generic response.

Required tests: backend integration, frontend integration, Playwright submission and status flow.

Security considerations: enumeration resistance, rate limiting, status lookup secret hashing, no lookup-secret logging.

Learning goals: transactions, idempotency, REST contracts, end-to-end testing.

Non-goals: email automation, candidate accounts.

## Phase 8 - Security, Accessibility And Quality Hardening

Objective: verify the implemented system against Phase 0 requirements.

Deliverables:

- Threat-model verification.
- Accessibility audit.
- Permission tests.
- Rate limit review.
- Performance review.
- Error-state hardening.

Acceptance criteria:

- Critical flows pass keyboard-only testing.
- Upload and draft controls have negative tests.
- Logs are reviewed for personal data.
- Durable audit events remain limited to status changes, authorized document access when required, cleanup, and security-relevant administrative changes.
- Known risks are documented.

Required tests: full test suite, Playwright flows, accessibility scan, manual review.

Security considerations: fix high-risk auth, upload, and privacy issues before deployment.

Learning goals: defensive review, accessibility QA, performance discipline.

Non-goals: adding new product scope before hardening.

## Phase 9 - Docker, CI/CD And Deployment

Objective: package and deploy the implemented system safely.

Deliverables:

- Docker files.
- Compose for local development.
- GitHub Actions.
- Environment validation.
- Deployment plan.
- Backup and restore plan.
- Runbook.

Acceptance criteria:

- CI runs frontend and backend checks.
- Docker images build.
- Production settings pass deployment checks.
- No deployment secrets are committed.

Required tests: CI checks, Docker build, deployment smoke tests.

Security considerations: HTTPS, secure cookies, secret injection, restricted and hardened admin ingress, least-privilege staff access, backups.

Learning goals: Docker, CI/CD, deployment checks, rollback.

Non-goals: Kubernetes, microservices, unnecessary queues.

## Phase 10 - Case Study And Portfolio Release

Objective: prepare public portfolio presentation based on real implemented work.

Deliverables:

- Case-study page.
- Final screenshots from actual app.
- Demo data.
- Technical walkthrough.
- Interview package.
- Public release notes.

Acceptance criteria:

- Case study separates assumptions, work completed, and real findings.
- Screenshots are from the implemented app.
- Demo data is fictional.
- Known limitations are disclosed.

Required tests: release smoke test, link check, accessibility pass on public pages.

Security considerations: no real candidate data, no secrets, no exposed admin paths in screenshots.

Learning goals: product storytelling, technical explanation, release hygiene.

Non-goals: fabricated metrics, fabricated testimonials, invented user research.

## Phase 1 Copy-Ready Prompt

```text
You are working inside D:\AI_FACTORY_CODEX\portfolio-projects\applyflow on branch phase-0-product-architecture.

Start Phase 1 only: UX foundations and Figma preparation for ApplyFlow. Do not scaffold Nuxt, Django, Docker, CI, database migrations, package files, or application source code.

First inspect the repository, read AGENTS.md, README.md, docs/product-brief.md, docs/problem-audit.md, docs/assumptions-and-validation.md, docs/field-inventory.md, docs/information-architecture.md, docs/design-direction.md, docs/design-system-plan.md, docs/figma-structure.md, docs/accessibility.md, and docs/implementation-roadmap.md.

Then produce Phase 1 documentation updates only:

1. Refine the fictional Northline Studio direction without overbuilding brand lore.
2. Validate and tighten the field inventory.
3. Create low-fidelity page-structure notes for home, vacancy index, vacancy detail, four application steps, submitted confirmation, status lookup, privacy, accessibility, and case study.
4. Create a complete user-flow and mobile-first layout plan.
5. Define a design-token proposal for Figma.
6. Define a component inventory with required states.
7. Define upload, error, empty, loading, success, and draft-save states.
8. Add accessibility annotations for headings, focus order, keyboard path, labels, hints, errors, upload status, and reduced motion.
9. Create a manual Figma task checklist for Jalolbek JR.
10. Do not claim that a Figma file, prototype, app, tests, or user research exists.

Before finishing, run git status, git diff --stat, and git diff --check. Review changed docs for fabricated research, generic filler, broken links, contradictions, and phase-boundary violations. Do not commit or push.
```
