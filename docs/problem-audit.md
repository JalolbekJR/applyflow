# Problem Audit

This audit is based on supplied problem-context screenshots and common interface patterns in long application forms. The screenshots are not copied. No company name, logo, visual identity, vacancy copy, layout, colors, illustrations, or proprietary wording should be reused.

No user research has been conducted yet.

## Observed Issues

These are visible in the supplied context or generally observable in the interface pattern:

- Long application forms can hide how many steps remain.
- Candidates are often asked to retype information already present in the CV.
- Required fields can appear without enough explanation.
- Errors may appear late, after the candidate has invested effort.
- File upload controls often do not explain size, format, progress, or recovery.
- Privacy and consent text can appear as legal filler instead of practical explanation.
- Confirmation screens can fail to give a useful next step.
- Application status may require contacting the company manually.
- Mobile forms can feel like a compressed desktop layout.
- Focus states, keyboard behavior, and error summaries are often under-designed.

## Assumptions

These are hypotheses and require validation:

- Candidates value a short form when a CV is already required.
- A visible four-step structure will reduce anxiety compared with one long page.
- Review-before-submit will catch mistakes without adding too much friction.
- Server-side draft recovery is worth the privacy and implementation cost.
- A private status lookup will reduce uncertainty after submission.
- Candidates can handle a separate application reference and status lookup secret if the confirmation page explains the difference clearly.

## Proposed Solutions

- Split the application into four meaningful steps.
- Show progress and step names without making the UI noisy.
- Use persistent field labels, concise hints, inline errors, and an error summary.
- Ask for only the fields needed to route and review the application.
- Treat the CV as the detailed experience source.
- Save drafts server-side with expiration.
- Provide clear upload states: selected, uploading, uploaded, failed, canceled, and retrying.
- Add a review step with edit links back to individual sections.
- Show a confirmation page with application reference, status lookup secret, status lookup link, and privacy reminder.
- Use original Northline Studio content instead of copied vacancy text.

## Planned Validation

Later usability testing should examine:

- Whether candidates understand the four-step flow.
- Whether field labels and hints answer common questions.
- Whether candidates can recover from an invalid upload.
- Whether the review step catches errors.
- Whether status lookup feels private and understandable.
- Whether mobile users can complete the flow without horizontal scrolling or covered fields.
- Whether keyboard-only completion works.

No findings exist yet.

## Anti-Copying Notes

The supplied screenshots are problem context only. ApplyFlow must create an original fictional company, visual system, page structure, content, and interaction model.
