# Design System Plan

Phase 0 defines the planned system. Tokens and components will be designed manually in Figma during Phase 1 and Phase 2, then implemented later.

## Token Families

| Family | Planned Tokens |
| --- | --- |
| Color | Surface, ink, line, signal, danger, warning, success, focus. |
| Typography | Family, size, line-height, weight, measure, responsive usage. |
| Spacing | Scale, page gutters, section spacing, and form grouping to be defined during design work. |
| Radius | Input, button, small panel, modal. Keep modest. |
| Borders | Subtle lines, focus lines, active step line. |
| Shadows | Sticky footer, modal, dropdown, upload drag state. |
| Motion | Duration, easing, reduced-motion fallback. |
| Breakpoints | Small phone, large phone, tablet, laptop, wide desktop. |
| Focus | Outline color, offset, thickness, high-contrast fallback. |
| Status | Error, warning, success, pending, submitted, closed. |
| Container | Reading width, form width, detail width, wide layout. |
| Z-index | Skip link, sticky progress, modal, toast, upload overlay if used. |

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

Phase 1 and Phase 2 should define a small duration and easing set for feedback and orientation. Phase 0 does not select final timing values. Reduced-motion mode should remove non-essential movement and preserve status changes through text and layout.

## Phase Boundary

Final typography, color values, spacing measurements, radii, shadows, breakpoints, and layout measurements are intentionally unresolved until Phase 1 and Phase 2 design work can evaluate them together.

## Implementation Notes

Do not install a large component library by default. Build project-specific primitives first. If a later accessibility need justifies a primitive library, record the decision in an ADR.
