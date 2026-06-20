# ADR 0005 - Do Not Require Candidate Accounts In Version One

Status: Accepted

## Context

ApplyFlow should reduce friction for candidates. The planned first version only needs vacancy browsing, anonymous application submission, and private status lookup.

## Decision

Do not require candidate accounts in version one.

Candidate access is anonymous and draft-specific. Django Admin authentication remains separate for internal users.

## Consequences

- The application flow stays shorter.
- There is no account recovery, password reset, or social login work in version one.
- Draft and status authorization must be designed carefully because there is no logged-in candidate identity.
- Admin permissions must never be inferred from candidate routes.

## Alternatives Considered

- Candidate accounts: deferred because they add auth flows, support burden, and privacy obligations.
- Social login: rejected unless later validation proves the value is worth the privacy and integration cost.
- Magic links: possible later for draft resume or status updates, but not needed for the first public version.

## Follow-Up Work

- Add rate limits and generic failure responses for anonymous endpoints.
- Revisit authentication only after usability validation or real product need.
