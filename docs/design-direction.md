# Design Direction

## Mood

ApplyFlow should feel calm, structured, and human. The interface should look designed for careful reading and confident completion, not for spectacle.

Keywords:

- Editorial technology
- Structured typography
- Warm neutral surfaces
- Architectural grid systems
- Precise lines
- Restrained motion
- Clear progress

## Fictional Identity

Company: Northline Studio

Description: a fictional software studio hiring for product roles.

Tone: plain-spoken, respectful, specific.

Signal concept: a thin active line that moves with the candidate through the process. It appears in progress indicators, focus treatment, and confirmation accents.

## Color Strategy

The implemented frontend uses a warm neutral canvas and surface system, near-black primary text,
muted secondary text, precise dividers, and one controlled green signal family. Separate focus,
danger, warning, success, and pending colors communicate interaction and status. Current values are
defined as custom properties in `frontend/app/assets/css/main.css`; contrast still requires manual
review across supported environments.

## Typography

Interface text uses a system sans-serif stack. Headings use an installed editorial serif stack with
Georgia as the broad fallback, avoiding a font download and its associated layout shift. Fluid
heading sizes and bounded reading, form, and content widths provide the current hierarchy.

## Layout

- Mobile-first.
- Clear content width limits.
- Grid-based vacancy detail and review pages.
- Forms split by meaning, not decorative cards.
- Step progress visible without covering fields.
- Long text should scan well on desktop and remain readable on phones.

Current grid columns, breakpoints, gutters, and reading widths are implemented as CSS tokens and
responsive rules. Browser and Playwright review remain required when those values change.

## Surfaces And Radius

Use radius sparingly. Inputs and small controls may use modest radius. Avoid making every section a floating card.

## Shadows And Depth

Borders provide the primary separation. The current frontend avoids decorative shadows and uses
sticky positioning only where it supports vacancy context on larger screens.

## Photography And Illustration

Do not use stock office photos, generic illustrations, or invented team imagery in the first version. Keep attention on the vacancy content and application flow.

## Icons

Use icons only when they clarify common actions or states. Icon-only controls require accessible labels and visible tooltips where appropriate.

## Motion

Motion should support orientation, not delay interaction. Use restrained CSS transitions for ordinary state changes and respect reduced-motion preferences. No animation dependency is planned for version one.

## Explicit Rejections

- Purple SaaS gradients.
- Glassmorphism.
- Animated blobs, glowing AI orbs, or random particles.
- Excessive 3D or visual effects.
- Stock-team photography and invented team imagery.
- Fake statistics or testimonials.
- Generic card walls or every section inside a rounded container.
- Decorative motion that delays vacancy reading or application tasks.

## Confirmation Experience

The confirmation page should feel resolved and useful:

- Clear submitted state.
- Human-readable application reference and private status lookup secret.
- Next action.
- Privacy reminder.
- No fake celebration, fake countdown, or dramatic animation.
