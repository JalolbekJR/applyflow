# White-Label UI Architecture

ApplyFlow supports one reviewed frontend deployment per employer. Slice 7 adds a source-controlled
brand and presentation configuration layer; it does not implement runtime tenant onboarding,
multi-tenancy, arbitrary page building, or company-authored backend fields.

## Implemented Boundary

The frontend keeps five concerns separate:

1. `frontend/app/api/`: relative `/api/v1/**` transport, CSRF bootstrap, ETags, response guards,
   upload transport, and backend field mapping.
2. `frontend/app/composables/`: in-memory draft state, mutation serialization, active-draft
   restoration, and feature orchestration.
3. `frontend/app/pages/`: route-level flow and accessibility focus behavior.
4. `frontend/app/components/`: presentation-only controls and layout pieces.
5. `frontend/app/branding/`: source-controlled brand identity, safe copy, semantic token values,
   capability flags, and closed layout variants.

Branding code does not import or configure API endpoints, cookies, headers, CSRF, ETags, upload
limits, field payloads, or authorization behavior. API modules do not import Vue components or
brand configuration.

## Brand Configuration

The bundled default configuration preserves the current ApplyFlow/Northline Studio reference
experience. A fictional alternate brand exists only as architectural proof.

Supported values include:

- product and company display names;
- short name and descriptor;
- logo asset reference and alternative text;
- safe support, legal, accessibility, and footer links;
- page title suffix;
- public copy snippets;
- semantic colors, radius, shadow, and system-font stacks;
- closed variants for header, application layout, vacancy list, and progress presentation;
- capability flags currently set to `finalSubmission: false` and `statusLookup: false`.

Configuration is TypeScript-typed and validated at runtime/startup. Links must be relative internal
paths or explicit HTTPS URLs. Text is rendered as text.

## Forbidden Customization

Brand configuration cannot provide:

- raw HTML or `v-html`;
- arbitrary JavaScript, inline event handlers, script URLs, or data URLs;
- arbitrary CSS strings or external font imports;
- tenant-controlled endpoint paths, headers, credentials, or payload fields;
- a way to disable required consent, CSRF, ownership cookies, ETags, conflict handling, or upload
  restrictions;
- generated application references, status lookup secrets, or fake submitted states.

New company-specific application questions require explicit backend schema, API, validation,
privacy, accessibility, and migration work. They are not accepted as arbitrary frontend JSON.

## Review Requirements

Every new brand deployment must repeat:

- validation of the brand config;
- keyboard and focus review;
- color contrast and forced-colors review;
- 320px, 390px, 768px, 1024px, and 1440px layout checks;
- upload, conflict, abandonment, deferred final submit, and status-unavailable state review;
- security search for unsafe HTML, browser persistence, public document URLs, and fake submission
  behavior.

Runtime multi-company SaaS configuration remains future scope.
