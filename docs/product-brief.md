# Product Brief

## Summary

ApplyFlow is a candidate-facing vacancy and application experience designed around a short,
transparent process.

Product statement:

> A job application experience that respects the candidate's time.

The first version covers one fictional employer and a small vacancy set. It is not a job marketplace
or a full applicant-tracking platform.

## Fictional Company

Northline Studio is a fictional software studio hiring for product, design, and engineering roles.
It provides coherent vacancy content without using a real employer or candidate data.

Tone: direct, calm, specific, and respectful.

Visual direction: editorial technology, structured typography, warm neutral surfaces, precise
dividers, and one signal color.

## Users

Primary user:

- A candidate reviewing a vacancy and deciding whether to apply.

Secondary users planned for the backend phase:

- Authorized hiring staff managing vacancies and reviewing submitted applications in Django Admin.
- Maintainers operating and improving the application.

## Candidate Goals

- Understand the vacancy quickly.
- Decide whether the role is relevant.
- Complete the application without unnecessary repetition.
- Know how much progress remains.
- Upload a CV confidently.
- Recover from mistakes and service failures.
- Understand what data is collected.
- Receive clear confirmation and retain private status credentials.

## Business Goals

- Receive complete, structured applications.
- Reduce avoidable incomplete submissions.
- Collect only necessary information.
- Protect uploaded documents and status access.
- Avoid duplicate applications.
- Keep vacancy and application operations reviewable.

## Current Phase 1 Scope

- Fictional vacancy index and detail pages.
- Four-step candidate application flow.
- Client-side validation and recoverable error states.
- In-memory draft behavior.
- PDF selection and metadata display without upload.
- Simulated save, submission, confirmation, and status lookup.
- Responsive layouts and automated frontend tests.

## Planned Backend Scope

- Server-side expiring drafts.
- Secure private PDF upload and authorized download.
- Atomic submission and duplicate protection.
- Private application-status lookup.
- Django Admin for internal vacancy and application management.
- PostgreSQL persistence, retention cleanup, and server-side validation.

## Application Steps

1. Position: confirm the selected vacancy and application requirements.
2. Candidate details: full name, email, optional phone and profile link, and preferred contact method.
3. Experience: CV, experience level, relevant skills, optional message, and privacy acknowledgement.
4. Review and submit: review every value, edit earlier steps, and submit once.

The flow does not ask candidates to repeat long employment histories already contained in a CV.

## Non-Goals

- Candidate accounts or cross-device draft recovery.
- Recruiter messaging, scheduling, or video calls.
- Automated candidate scoring, ranking, or rejection.
- Resume generation or chatbot assistance.
- Payments or subscriptions.
- Multiple employers or complex tenancy.
- Native mobile applications or a job marketplace.
- Recruiter analytics or a custom recruiter dashboard.
- DOC or DOCX uploads in the first version.
- Microservices, Kubernetes, real-time sockets, or unnecessary background queues.

## Candidate And Business Trade-Offs

| Tension | Candidate need | Business need | First-version choice |
| --- | --- | --- | --- |
| Fewer fields vs structured review | Apply quickly | Compare applications consistently | Collect a small set of structured fields and rely on the CV for detail. |
| Draft recovery vs privacy | Recover after errors | Avoid excessive browser storage | Use expiring server-side drafts in the backend phase and avoid localStorage for candidate data. |
| Status access vs disclosure | Check progress | Prevent enumeration | Separate the readable reference from a high-entropy status secret. |
| Upload convenience vs security | Upload a common format | Reduce malicious file risk | Accept PDF only, inspect it server-side, and store it privately. |

## Evidence Standard

No user research has been conducted yet. Documents and interface copy must distinguish observed
issues, assumptions, implemented behavior, simulated behavior, and planned work. Candidate
preferences or outcomes must not be claimed without evidence.
