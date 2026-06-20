# Accessibility Plan

ApplyFlow should align with WCAG 2.2 principles: perceivable, operable, understandable, and robust. This is a plan, not a conformance claim.

Reference: [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/).

## Planned Requirements

- Semantic landmarks for header, main, navigation, and footer.
- Logical heading order.
- Skip link that becomes visible on focus.
- Visible focus for all interactive controls.
- Keyboard navigation through every application step.
- Accessible step indicator with current step announced in text.
- Focus moved to the new step heading after route changes.
- Persistent labels for every input.
- Hints and errors connected to fields.
- Error summary that links to invalid fields.
- Focus moved to the error summary after failed validation.
- Live-region announcements for draft save, upload status, and submission result where appropriate.
- Upload control with keyboard operation and file status announcements.
- Sufficient contrast for text, borders, focus, and status indicators.
- No color-only status communication.
- Reduced-motion support.
- Mobile touch targets sized for reliable tapping.
- Meaningful page titles.
- Route-change announcements where needed.

## Phase Acceptance Criteria

| Phase | Accessibility Criteria |
| --- | --- |
| Phase 1 | Low-fidelity wireframes annotate heading structure, focus targets, error summary, and mobile touch areas. |
| Phase 2 | Figma components include focus-visible, error, disabled, loading, and reduced-motion notes. |
| Phase 3 | Nuxt foundation includes landmarks, skip link, page titles, and responsive layout. |
| Phase 4 | Application flow is completable with keyboard only in frontend tests. |
| Phase 5 | Backend errors can map to field-level and summary-level messages. |
| Phase 6 | Upload control supports keyboard, status text, retry, cancellation, and accessible errors. |
| Phase 7 | Confirmation and status lookup expose clear status text without relying on color. |
| Phase 8 | Full keyboard pass, reduced-motion pass, and automated accessibility scan are run. |

## Manual Review Checklist

- Can a keyboard user complete the full flow?
- Does focus stay visible after every route change and error?
- Are labels visible when fields contain values?
- Does the error summary link to each invalid field?
- Can a screen-reader user understand the current step?
- Does mobile zoom or the on-screen keyboard cover the active field?
- Are upload failures announced and recoverable?
- Does reduced motion preserve orientation without animation?

## Known Limitations

No interface exists yet, so accessibility has not been tested.
