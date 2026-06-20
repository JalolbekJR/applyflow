# ADR 0006 - Separate Application References From Status Lookup Secrets

Status: Accepted

## Context

Candidates need a private way to check application status without exposing data through predictable identifiers. The first version should avoid complex email automation and should not treat email as a secret.

## Decision

Generate two separate values at submission:

- `application_reference`: a short human-readable, non-confidential identifier for confirmation, support, and staff discussion.
- `status_lookup_secret`: a high-entropy server-generated credential for status access.

Deliver the raw `status_lookup_secret` only in the no-store submission response for immediate confirmation display and store only its secure hash. Do not put it in a URL or persistent browser storage. The readable application reference is not an authorization credential, and email is not treated as a secret.

The API returns a generic failure response for invalid combinations and a minimal status response for valid combinations.

## Consequences

- Numeric application IDs are never proof of ownership.
- Enumeration is harder because the status credential is high entropy and rate limited.
- The status page can work without user accounts.
- Losing the status lookup secret means the candidate cannot self-serve status in version one.
- Rate limiting is required.
- The lookup secret must never be logged.

## Alternatives Considered

- Application reference plus email: rejected because email is not a secret and a short readable reference is not strong enough to authorize status access.
- Random reference only: rejected because a human-readable value is better for support and should not double as a secret.
- Email verification: stronger, but requires email delivery and abuse handling that are out of scope for version one.
- Expiring signed links: useful for emailed status links, but out of scope without email automation.

## Follow-Up Work

- Define application-reference format and status-secret length in backend implementation.
- Hash the status lookup secret at rest.
- Add throttling, enumeration-resistance tests, and privacy-safe aggregate security monitoring.
- Keep response content minimal.
