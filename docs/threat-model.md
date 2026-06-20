# Threat Model

Scope: first public version of ApplyFlow with anonymous candidate flow, Django Admin, server-side drafts, private CV upload, and private status lookup.

## Assets

- Candidate personal data.
- CV documents.
- Draft secrets.
- Application references.
- Status lookup secrets.
- Admin sessions.
- Vacancy content.
- Environment secrets.
- Audit logs.

## Threats And Controls

| Threat | Asset | Attacker Goal | Attack Path | Preventive Controls | Detective Controls | Residual Risk | Phase |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Unauthorized document access | CV documents | Read private CVs | Guess URL or document ID | Private storage, authorization before download, no public media URLs | Aggregate denied-access security monitoring | Admin account compromise still exposes documents | 6 |
| Predictable draft tokens | Draft data | Read or alter drafts | Guess token or ID | High-entropy server secret, hash at rest, non-sensitive ID not proof | Failed authorization counters | Token theft from browser remains possible | 6 |
| Application enumeration | Applications | Learn who applied | Status lookup guessing | High-entropy status lookup secret, generic failures, rate limits | Lookup attempt rate monitoring | Targeted guessing may still cause noise | 7 |
| Vacancy scraping abuse | Vacancy content | Scrape public data | Automated requests | Cache headers, basic throttling if needed | Traffic logs by category | Public data cannot be fully protected | 8 |
| Submission spam | Application records | Flood admin review | Automated submissions | Rate limits, server validation, optional CAPTCHA only if needed | Submission rate alerts | CAPTCHA may hurt real users if added poorly | 7 |
| Upload abuse | Storage and app | Store harmful or huge files | File upload endpoint | 5 MB limit, PDF extension allowlist, signature/content inspection, private storage, throttling | Rejection counts by reason | Content inspection is not malware scanning | 6 |
| Oversized requests | Backend availability | Exhaust resources | Large body upload | Request size limits at proxy and app | 413 counts | Proxy misconfig could weaken control | 9 |
| Malicious filenames | Storage | Path traversal or confusing download | Crafted filename | Generated storage name, metadata escaping | Upload rejection logs | Staff UI must escape filename display | 6 |
| Misleading MIME types | Upload validation | Bypass type checks | Spoof header | Do not trust browser MIME; inspect PDF signature and content server-side | Type mismatch counts | Detection libraries have limits | 6 |
| Duplicate submissions | Application integrity | Create repeated entries | Submit same draft/email | Atomic submit and PostgreSQL constraint for one normalized email per vacancy record | Conflict event | Candidate may use a different email | 7 |
| CSRF | Candidate/admin actions | Trigger unwanted requests | Cross-site form/request | SameSite cookies, CSRF protection for unsafe methods | CSRF failure logs | Same-origin setup must be tested | 5 |
| XSS through vacancy content | Candidate browser/admin | Run script | Unsafe rich text | Escape by default, restrict rich text, sanitize if enabled | CSP report later if configured | Admin-entered content still needs care | 5 |
| Unsafe rich text | Vacancy content | Inject scripts/links | Admin content fields | Prefer plain text/structured fields first | Admin review | Rich text sanitizer may be added later | 5 |
| Excessive error details | Privacy/system info | Learn internals | API error response | Consistent safe error shape | Error response review | Debug mode in production is a severe risk | 5 |
| Personal data in logs | Privacy | Expose candidate data | Logging request bodies | Logging policy, filters, request IDs | Log review | Third-party logs need review before use | 5 |
| Leaked environment secrets | Secrets | Gain system access | Committed `.env` or logs | `.gitignore`, secret scanning guidance, env injection | Secret scan in CI later | Local developer mistakes remain possible | 9 |
| Insecure production settings | App | Exploit weak config | DEBUG, weak hosts, no HTTPS | Django deployment checks, env validation | Deployment checklist | Misconfigured host can still fail | 9 |
| Dependency compromise | App integrity | Run malicious code | Package install/update | Pin versions later, dependency review guidance | Dependabot/dependency review later | Supply-chain risk remains | 9 |
| Broken object-level auth | Drafts/documents | Access another record | ID tampering | Object permissions, tests for cross-draft access | 403/404 logs | New endpoints can forget checks | 6 |
| Broken function-level auth | Admin actions | Change status without rights | Direct endpoint call | Staff permissions, admin-only views | Admin audit events | Overbroad staff roles remain risk | 8 |
| Insecure Django Admin exposure | Admin | Brute force or abuse admin | Reach or abuse admin login | Restrict production admin ingress, least-privilege staff permissions, strong authentication, secure cookies, rate limits | Failed login and security-relevant admin monitoring | Admin remains a high-value target | 9 |

## Follow-Up Security Work

- Add permission tests with cross-record attempts.
- Add upload validation tests.
- Add status lookup throttling tests.
- Add Django deployment checks before production.
- Add dependency and secret scanning to CI when workflows are created.
