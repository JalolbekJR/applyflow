# Product Brief

## Summary

ApplyFlow is a portfolio project that improves the vacancy discovery and job application experience.

Product statement:

> A job application experience that respects the candidate's time.

The first version focuses on one fictional employer and a small set of vacancies. It is not a job marketplace or applicant-tracking platform.

## Fictional Company

Company name: Northline Studio

Northline Studio is a fictional software studio hiring for product, design, and engineering roles. It exists only to give the portfolio project realistic vacancy content and visual context.

Tone: direct, calm, specific, and respectful of the candidate's time.

Visual idea: editorial technology, structured typography, warm neutral surfaces, precise lines, and one signal color.

## Target Users

Primary user:

- A candidate reviewing a vacancy and deciding whether to apply.

Secondary users:

- A hiring administrator reviewing vacancies and submitted applications in Django Admin.
- Jalolbek JR, using the project as a portfolio case study and interview discussion piece.

## Candidate Goals

- Understand the vacancy quickly.
- Determine personal fit.
- Complete the application without unnecessary repetition.
- Know how much progress remains.
- Upload a CV confidently.
- Recover from mistakes.
- Understand what data is collected.
- Receive clear confirmation.
- Retain entered data after recoverable errors.

## Business Goals

- Receive structured applications.
- Reduce incomplete submissions.
- Preserve candidate trust.
- Collect only necessary information.
- Maintain reviewable vacancy content.
- Protect uploaded documents.
- Avoid duplicate applications.
- Provide operationally useful records.

## First-Version Scope

- One fictional employer with a small realistic vacancy dataset
- Vacancy index
- Vacancy detail page
- Four-step application flow
- Draft persistence
- Secure CV upload
- Review-before-submit step
- Submission confirmation
- Private application-status lookup
- Responsive mobile experience
- Public UX case-study page
- Django Admin for internal vacancy and application management

## Application Steps

1. Position: selected vacancy, summary, location, work format, employment type, essential requirements, and deadline when relevant.
2. Candidate details: full name, email, phone, profile link, preferred contact method.
3. Experience: CV upload, experience level, relevant skills, optional short message, privacy and consent acknowledgement.
4. Review and submit: summary, edit actions, privacy information, consent version, final submission, duplicate-submission protection.

The flow should not ask candidates to manually repeat large amounts of information already contained in their CV.

## Explicit Non-Goals

- Recruiter messaging
- Interview scheduling
- Video interviews
- AI candidate scoring
- Automated candidate ranking
- Automated candidate rejection
- Resume generation
- Chatbot assistant
- Social login unless later justified
- Payments
- Subscriptions
- Complex multi-company tenancy
- Recruiter analytics suite
- Native mobile application
- Job marketplace
- Public candidate profiles
- Candidate accounts
- Cross-device draft recovery
- Multiple employers
- DOC or DOCX uploads
- Complex email automation
- Custom recruiter dashboard
- Analytics dashboard
- Broad audit infrastructure
- Microservices
- Kubernetes
- Real-time sockets
- Unnecessary background queues

## Candidate And Business Trade-Offs

| Tension | Candidate Need | Business Need | First-Version Choice |
| --- | --- | --- | --- |
| Fewer fields vs structured review | Apply quickly | Compare applications consistently | Collect a small set of structured fields and rely on the CV for detail. |
| Draft persistence vs privacy | Recover after errors | Avoid storing excessive personal data | Use server-side expiring drafts and avoid localStorage for sensitive data. |
| Status lookup vs information disclosure | Know current status | Prevent enumeration | Use a readable application reference for support and a separate high-entropy lookup secret for access. |
| Upload convenience vs security | Upload a common CV format | Avoid malicious file handling | Accept PDF only in version one, inspect server-side, store privately. |

## Evidence Standard

No user research has been conducted yet.

Documents must separate observed interface issues, assumptions, proposed solutions, and planned validation. The project must not claim that candidates prefer a design, that testing proved a choice, or that analytics support a decision until real evidence exists.

## Portfolio Value

ApplyFlow should demonstrate:

- Vue 3, Nuxt, TypeScript, responsive frontend implementation, and testing.
- Python, Django, DRF, PostgreSQL, secure REST API design, Docker planning, and CI planning.
- UX process, information architecture, field reasoning, accessibility planning, design system thinking, and developer handoff.

The project should be small enough to finish and study, but specific enough to discuss seriously in interviews.
