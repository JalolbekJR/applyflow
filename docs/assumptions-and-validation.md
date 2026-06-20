# Assumptions And Validation

No user research has been conducted yet. This document keeps assumptions visible so later work can test them instead of presenting them as facts.

## Assumption Register

| Assumption | Why It Matters | Risk If Wrong | Planned Validation |
| --- | --- | --- | --- |
| Candidates may not want to repeat CV details. | Drives the short field inventory. | The business may receive too little structured information. | Usability test and hiring-admin review of sample submissions. |
| Four steps feel clearer than one long form. | Drives route and progress design. | Step changes may feel slower than a single page. | Compare task completion and comments in moderated tests. |
| Server-side drafts are worth the added backend work. | Drives draft model and cleanup work. | Privacy or implementation cost may be too high for the prototype. | Test recoverable-error scenarios and review retention needs. |
| Candidates can distinguish a readable application reference from a private status lookup secret. | Drives private status lookup. | Candidates may expose or lose the secret, or treat the reference as authorization. | Test confirmation comprehension and status lookup task. |
| Django Admin is enough for internal review. | Keeps version one focused. | Admin workflow may be awkward for portfolio demonstration. | Staff-review walkthrough with fictional applications. |
| A restrained editorial visual style fits the product. | Drives design direction. | The UI may feel too quiet for portfolio presentation. | Design critique in Phase 1 and Phase 2. |

## Usability Test Plan

Purpose: identify friction in the planned vacancy discovery and application flow before implementation hardens the design.

Participants: 4 to 6 people who have applied for software, design, or junior technical roles in the last year. If real participants are unavailable, run an internal heuristic review and clearly label it as such.

Prototype level: low-fidelity in Phase 1, high-fidelity in Phase 2.

Tasks:

1. Find a vacancy that fits your background.
2. Decide whether the role is worth applying for.
3. Start the application.
4. Complete candidate details.
5. Upload a valid CV.
6. Recover from an invalid upload.
7. Review and edit one answer.
8. Submit the application.
9. Find the private status lookup path.

Observations to capture:

- Where the participant hesitates.
- Questions they ask.
- Misread labels or hints.
- Errors they can and cannot recover from.
- Mobile viewport issues.
- Keyboard and focus issues.

Do not record:

- Real CV files.
- Real contact details.
- Sensitive employment history.

## Success Signals

These are planned evaluation signals, not current metrics:

- Candidate can explain what information will be collected.
- Candidate can identify current step and remaining steps.
- Candidate can recover from upload failure without losing entered fields.
- Candidate can submit using keyboard only.
- Candidate can explain how to check status later.
- Candidate can explain why the application reference is not the private lookup credential.
- Candidate does not need to copy details from the CV into long free-text fields.

## Research Output Rules

Future findings must include:

- Date.
- Method.
- Participant count or reviewer role.
- Prototype version.
- Observed behavior.
- Limitation.
- Design implication.

Avoid broad claims from tiny samples.
