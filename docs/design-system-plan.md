# Design System Plan

The coded Nuxt design system is the current source of truth. CSS tokens, components, responsive
rules, and interaction states are reviewed in the browser and through Playwright. A Figma library
may be reconstructed later when useful collaboration or editing access justifies it; it must reflect
the implemented system rather than precede it.

## Token Families

| Family               | Roles                                                                                                                                                |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Color                | Surface, ink, line, signal, danger, warning, success, focus.                                                                                         |
| Brand semantic color | Page background, surface, muted surface, text, muted text, border, primary, primary hover/active, primary text, focus, danger, warning, and success. |
| Typography           | Family, size, line-height, weight, measure, responsive usage.                                                                                        |
| Brand typography     | Body and heading font stacks selected from reviewed system-font values.                                                                              |
| Spacing              | Scale, page gutters, section spacing, and form grouping.                                                                                             |
| Radius               | Input, button, small panel, modal. Keep modest.                                                                                                      |
| Borders              | Subtle lines, focus lines, active step line.                                                                                                         |
| Shadows              | Sticky footer, modal, dropdown, upload drag state.                                                                                                   |
| Motion               | Duration, easing, reduced-motion fallback.                                                                                                           |
| Breakpoints          | Small phone, large phone, tablet, laptop, wide desktop.                                                                                              |
| Focus                | Outline color, offset, thickness, high-contrast fallback.                                                                                            |
| Status               | Error, warning, success, pending, submitted, closed.                                                                                                 |
| Container            | Reading width, form width, detail width, wide layout.                                                                                                |
| Z-index              | Skip link, sticky progress, modal, toast, upload overlay if used.                                                                                    |

## Component Inventory

- Skip link
- Header
- Footer
- Vacancy card
- Vacancy detail summary
- Step indicator
- Field group
- Text input
- Email input
- Phone input
- URL input
- Select or radio group
- Checkbox
- Tag input for skills
- Textarea with character count
- File upload
- Upload status
- Error summary
- Inline error
- Draft save status
- Review section
- Edit action
- Primary button
- Secondary button
- Link button
- Confirmation panel
- Status lookup form
- Status result
- Empty state
- Closed vacancy state

## Required States

Every interactive component must define:

- Default
- Hover
- Focus-visible
- Active
- Disabled
- Loading
- Error
- Success
- Read-only where relevant

## Form Behavior

Form components must support persistent visible labels, hints, required/optional markers, inline errors, and programmatic association through `id`, `for`, `aria-describedby`, and `aria-invalid` where relevant.

## Motion Tokens

The current interface uses one short transition duration for feedback and orientation. Reduced-motion
mode removes non-essential movement while preserving status changes through text and layout.

## Phase Boundary

Implemented token values live in `frontend/app/assets/css/main.css`. Changes require responsive,
keyboard, pointer, touch, reduced-motion, and contrast review. Figma remains optional under
[ADR 0012](decisions/0012-code-first-design-workflow.md).

Slice 7 adds a source-controlled brand configuration layer under `frontend/app/branding/`. It may
change safe public copy, display names, reviewed links, semantic tokens, and closed layout variants.
It cannot change API paths, credentials, CSRF behavior, ETag handling, required consent, upload
limits, arbitrary backend fields, or runtime JavaScript/CSS/HTML. The default ApplyFlow/Northline
configuration remains the reference appearance.

## Implementation Notes

Do not install a large component library by default. Build project-specific primitives first. If a later accessibility need justifies a primitive library, record the decision in an ADR.
