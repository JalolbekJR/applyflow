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

The direction is warm neutral surfaces, near-black text, precise dividers, and one controlled signal color. Phase 0 defines semantic roles only: surface, raised surface, primary and secondary ink, divider, signal, focus, danger, warning, and success. Exact colors and contrast pairs must be selected and tested during Phase 1 and Phase 2.

## Typography

Use a practical type system with strong hierarchy and good multilingual fallback.

Planned direction:

- System UI or a licensed open-source sans-serif for interface text.
- Optional editorial serif only if licensing, performance, and readability are acceptable.
- No font should be chosen only because it is fashionable.
- Font loading must avoid layout shift.

No final typeface, scale, weight set, or measure is selected in Phase 0.

## Layout

- Mobile-first.
- Clear content width limits.
- Grid-based vacancy detail and review pages.
- Forms split by meaning, not decorative cards.
- Step progress visible without covering fields.
- Long text should scan well on desktop and remain readable on phones.

Exact grid columns, breakpoints, gutters, and reading widths belong to Phase 1 and Phase 2.

## Surfaces And Radius

Use radius sparingly. Inputs and small controls may use modest radius. Avoid making every section a floating card.

## Shadows And Depth

Depth should clarify layering, such as a sticky step footer or upload status. Avoid heavy shadows and glass effects.

## Photography And Illustration

Do not use stock office photos, generic illustrations, or invented team imagery in the first version. The portfolio focus is the flow, content, and system design.

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
