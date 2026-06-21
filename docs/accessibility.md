# Accessibility

ApplyFlow is designed around WCAG 2.2 principles. This document records implemented behavior and
remaining review work; it is not a conformance claim.

Reference: [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/).

## Implemented In The Frontend

- Header, navigation, main, footer, article, section, and complementary landmarks.
- Logical page headings and one meaningful `h1` for unavailable routes.
- A skip link that becomes visible on focus.
- Visible focus for links, buttons, fields, field groups, and recovery regions.
- Route-heading focus for meaningful path navigation without overriding hash or query behavior.
- Persistent labels and stable hint and error identifiers.
- Error summaries that receive focus and link to invalid destinations.
- `fieldset` and `legend` semantics for radio and consent groups.
- `aria-describedby` and `aria-invalid` relationships for invalid controls.
- Text announcements for save, upload, submission, copy, and status behavior.
- Keyboard-operable file selection, application navigation, and submission.
- Reduced-motion handling and mobile targets sized toward 44 CSS pixels.
- Responsive layouts from 320px upward without CSS reordering that conflicts with DOM order.

## Automated Coverage

Vitest checks error-summary focus and targets, file-selection states, and credential copy recovery.
Playwright checks keyboard navigation, route focus, grouped-field relationships, save-failure focus,
mobile vacancy order, footer target height, and 320px horizontal reflow.

## Manual Review Still Required

- Screen-reader passes with current VoiceOver, NVDA, and TalkBack combinations.
- Browser zoom and text-spacing review.
- Contrast measurement for every state and platform font rendering.
- Touch review on physical mobile devices.
- High-contrast and forced-colors review.
- Full reduced-motion review outside automated assertions.

No accessibility conformance certification or participant study has been completed.
