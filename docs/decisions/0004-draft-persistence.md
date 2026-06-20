# ADR 0004 - Use Anonymous Server-Side Drafts

Status: Accepted

## Context

Candidates should not lose progress after recoverable errors, but requiring an account would make the first version heavier than necessary. Sensitive candidate data should not be stored casually in persistent browser storage.

## Decision

Use anonymous server-side drafts protected by a server-generated high-entropy secret.

Version one supports one active anonymous application draft per browser at a time. The preferred implementation is a same-origin secure HttpOnly cookie containing the active draft secret, with a non-sensitive draft identifier used in API paths. If the implementation later uses a token in a request body or header, it must avoid URL logging and localStorage.

Drafts expire automatically. CV documents are deleted when a draft is abandoned or when expired-draft cleanup runs.

## Consequences

- Candidates can recover progress in the same browser without creating an account.
- Starting the same vacancy restores the active draft. Starting another vacancy must ask the candidate to continue or abandon the current draft.
- Continuing restores the existing draft and never creates another.
- Abandoning the current draft deletes draft data and draft documents, then clears the active-draft cookie.
- Submitting the draft clears the active-draft cookie and creates separate status lookup credentials.
- Sensitive draft data stays server-side.
- Device switching is not supported in version one unless a later ADR adds a secure resume flow.
- Cookie loss, credential loss, or draft expiration means the candidate cannot restore that draft through self-service in version one.
- Invalid or expired draft credentials must return generic responses.
- Cleanup jobs or management commands are needed later.

## Alternatives Considered

- Client-only temporary draft: lower backend cost, but poor recovery and higher privacy risk if sensitive data is persisted locally.
- Authenticated account-based draft: useful for a larger hiring platform, but too much friction for version one.
- No persistent draft: simplest, but poor candidate experience when upload or API errors happen.

## Follow-Up Work

- Define cookie attributes and token hashing in backend implementation.
- Add tests for draft authorization, expiration, and cleanup.
- Keep detailed behavior aligned with [draft persistence](../draft-persistence.md).
