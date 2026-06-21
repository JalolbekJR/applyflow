# Figma Structure

Figma work is deferred. The connected plan currently prevents useful canvas operations, so the
running Nuxt frontend and browser screenshots are the active design-review surface under
[ADR 0012](decisions/0012-code-first-design-workflow.md).

If a shared design file becomes useful later, use this structure:

1. `00 - Cover and index`
2. `01 - Product assumptions`
3. `02 - Candidate journey and user flow`
4. `03 - Content and validation`
5. `04 - Design tokens`
6. `05 - Components and variants`
7. `06 - Desktop screens`
8. `07 - Mobile screens`
9. `08 - Accessibility annotations`
10. `09 - Research plan and findings`
11. `10 - Developer handoff`

## Source Of Truth

- Implemented behavior is defined by the Nuxt frontend and its tests.
- Product and architecture boundaries are defined by the accepted documentation and ADRs.
- Browser screenshots are review evidence, not usability findings.
- A future design file must reflect the approved coded system instead of inventing a parallel one.

## Future Design-File Checklist

- Record actual color, typography, spacing, radius, and motion tokens.
- Build variants for default, hover, focus-visible, active, disabled, loading, error, success, and
  read-only states where relevant.
- Include 320px mobile and representative desktop screens.
- Annotate heading structure, focus targets, keyboard order, hints, errors, live regions, and touch
  targets.
- Keep upload, save failure, unavailable vacancy, confirmation, and status failure states visible.
- Use only fictional data.
- Record research findings only after real research has occurred.
