# Frontend Replacement Runbook

Use this runbook when modifying the current frontend, building `frontend-v2`, or moving to another
frontend framework.

## Strategy A: Modify The Existing Frontend

Use for branding, components, layouts, animations, content presentation, accessibility presentation,
or responsive behavior. Keep API calls in `frontend/app/api/` and state orchestration in
composables. Run the visual or integration test set from [testing contract](testing-contract.md)
based on the scope.

The current employment-entry UI supports adding, editing, and removing entries. It preserves the
backend `position` field for deterministic ordering, but it does not expose drag-and-drop or manual
reordering controls.

## Strategy B: Parallel `frontend-v2`

Recommended for a major redesign.

1. Keep the current frontend intact.
2. Create a separate `frontend-v2/` directory or branch.
3. Reuse the documented `/api/v1/` contract.
4. Build typed API clients.
5. Implement CSRF and cookie handling first.
6. Implement vacancy reads.
7. Implement draft bootstrap.
8. Implement candidate and experience persistence.
9. Implement experience entries.
10. Implement CV upload, replacement, deletion, progress, and cancellation.
11. Implement conflict, expired, unavailable, validation, network, and storage-error states.
12. Run contract tests.
13. Run real Django full-stack browser tests.
14. Compare behavior with the current frontend.
15. Switch entry points only after verification passes.

## Strategy C: Different Framework

React, Next.js, SvelteKit, plain Vue, mobile clients, or another framework may be used later. The
replacement must preserve same-origin or an explicitly approved equivalent security model, cookies,
CSRF, `/api/v1/` paths, `ETag`/`If-Match`, multipart upload behavior, accessibility, error
semantics, and no client-side credential storage.

## Change Scope Table

| Change                                       | Frontend only                                      | API coordination required  | Backend change required | Migration required                      |
| -------------------------------------------- | -------------------------------------------------- | -------------------------- | ----------------------- | --------------------------------------- |
| Color and typography changes                 | Yes                                                | No                         | No                      | No                                      |
| New component library                        | Yes, if accessibility and API behavior remain      | No                         | No                      | No                                      |
| New page layout                              | Yes                                                | No                         | No                      | No                                      |
| Reordering visual sections                   | Yes                                                | No                         | No                      | No                                      |
| Renaming frontend component                  | Yes                                                | No                         | No                      | No                                      |
| New frontend route using existing API data   | Usually                                            | Maybe for route policy     | No                      | No                                      |
| Changing request field names                 | No                                                 | Yes                        | Yes                     | Maybe                                   |
| Changing endpoint paths                      | No                                                 | Yes                        | Yes                     | No if view-only, maybe if model-related |
| Adding a persisted candidate field           | No                                                 | Yes                        | Yes                     | Yes                                     |
| Changing draft expiration                    | No                                                 | Yes                        | Yes                     | Maybe                                   |
| Changing maximum CV size                     | No                                                 | Yes                        | Yes                     | No migration, but settings/tests change |
| Adding DOCX support                          | No                                                 | Yes                        | Yes                     | Maybe                                   |
| Adding dedicated employment-entry reorder UI | Maybe, if it uses the existing `position` contract | Maybe, if semantics change | Maybe                   | Maybe                                   |
| Adding public CV preview                     | No                                                 | Yes                        | Yes                     | Maybe                                   |
| Replacing cookie authorization               | No                                                 | Yes                        | Yes                     | Maybe                                   |
| Changing database constraints                | No                                                 | Yes                        | Yes                     | Yes                                     |

## Rollback Plan

- Keep the old frontend runnable until the replacement passes the cutover checks.
- Keep backend API behavior unchanged during frontend cutover.
- Switch routing or deployment entry point back to the previous frontend if contract tests fail.
- Do not delete the old frontend until full-stack tests, accessibility spot checks, and security
  checklist pass.
- Preserve database schema and private storage behavior during rollback.
