# Candidate Journey

## Journey Map

| Stage | Candidate Question | Product Response | Risk |
| --- | --- | --- | --- |
| Discovery | Is this role relevant to me? | Vacancy cards show role, location, work format, employment type, and short summary. | Too little detail can make every role look the same. |
| Evaluation | Do I fit the essentials? | Detail page separates essentials from nice-to-have content. | Requirements may still feel vague without careful content writing. |
| Start | How long will this take? | Application entry shows four steps and what is needed before starting. | Progress copy can become noise if repeated too often. |
| Details | What personal data is needed? | Form asks for contact fields with explicit reasons. | Asking for phone may feel unnecessary if not explained. |
| Experience | Can I upload my CV safely? | Upload control explains the 5 MB PDF requirement, privacy, progress, and retry. | Security limits may reject files candidates expect to upload. |
| Review | Did I make a mistake? | Review screen groups answers and provides edit actions. | Edit links must return users to the right step without data loss. |
| Submit | What happens now? | Confirmation gives application reference, status lookup secret, status lookup link, and privacy reminder. | Lost lookup secret prevents self-service status checks in version one. |
| Status | Has anything changed? | Private lookup returns a minimal status label. | Too much status detail may reveal internal process. |

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

## Trade-Offs

Phone number is optional in the first version because email is sufficient for ordinary follow-up. If phone is selected as the preferred contact method, a phone number must be present. Status authorization never depends on either contact field.

Relevant skills are structured, but limited. The field helps internal review without turning the form into a CV reconstruction task.

Draft recovery is same-browser only for version one. This keeps the system smaller and avoids sending email links before email security and abuse controls are designed.
