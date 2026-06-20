# User Flow

## Public Flow

```mermaid
flowchart TD
    Home["Home"] --> Vacancies["Vacancy index"]
    Vacancies --> Detail["Vacancy detail"]
    Detail --> DraftCheck["Active draft check"]
    DraftCheck --> Start["Apply: position step"]
    Start --> Details["Candidate details"]
    Details --> Experience["Experience and CV"]
    Experience --> Review["Review and submit"]
    Review --> Submitted["Confirmation"]
    Submitted --> Status["Private status lookup"]
    Home --> CaseStudy["Case study"]
    Home --> Privacy["Privacy"]
    Home --> Accessibility["Accessibility"]
```

## Application Step Flow

```mermaid
flowchart TD
    A["Open vacancy"] --> B{"Vacancy active?"}
    B -- "No" --> C["Show closed vacancy state"]
    B -- "Yes" --> D{"Active draft in this browser?"}
    D -- "No" --> E["Create draft"]
    D -- "Yes" --> M{"Draft for this vacancy?"}
    M -- "Yes" --> R["Restore current draft"]
    M -- "No" --> N{"Continue existing or abandon it?"}
    N -- "Continue" --> R
    N -- "Abandon" --> O["Delete draft and document; clear credential"]
    O --> E
    E --> F["Step 1: Position"]
    R --> Q{"First incomplete step?"}
    Q -- "Position" --> F
    Q -- "Candidate details" --> G
    Q -- "Experience" --> H
    Q -- "Review" --> I
    F --> G["Step 2: Candidate details"]
    G --> H["Step 3: Experience"]
    H --> I["Step 4: Review"]
    I --> J{"Server accepts submission?"}
    J -- "Yes" --> K["Submitted confirmation"]
    J -- "Recoverable error" --> L["Show error and preserve fields"]
    L --> I
    J -- "Duplicate" --> P["Show existing submission guidance"]
```

## Error Paths

- Closed vacancy: the apply action is disabled and the page explains that applications are no longer accepted.
- Expired, missing, or invalid draft credential: return a generic safe response, do not reveal whether another draft exists, and offer a new start when appropriate.
- Invalid field: inline error appears, the error summary links to the field, and focus moves to the summary after failed step submission.
- Invalid upload: the selected file is rejected before submission, with format and size guidance.
- Upload interruption: candidate can cancel, retry, or remove the file.
- Duplicate submission: final submission is blocked when the normalized email already has a submitted application for the same vacancy record.
- Status lookup miss: response is generic and does not reveal whether the application reference or status lookup secret exists.

## Confirmation Flow

The confirmation page shows:

- Application received message.
- Submitted vacancy.
- Human-readable application reference.
- Status lookup secret shown once for candidate retention.
- Status lookup link.
- Reminder that the status lookup secret is private and the application reference is not proof of ownership.
- Privacy and retention note.

It does not expose internal notes or promise response timelines that the fictional company cannot guarantee.
