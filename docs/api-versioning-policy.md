# Public API Versioning and Deprecation Policy

**Sports News AI — Public Claims API**
**Document Version:** 1.0.0

Handbook §18.4 requires "versioning from day one with a written deprecation policy" for the public API. `/api/v1` prefixing has existed since Phase 1; this document is the policy that was missing.

## 1. Versioning scheme

The API is versioned in the URL path (`/api/v1/...`), not via a header or content-type parameter. A version is a major version only — there is no `v1.1` or `v1.2`.

## 2. What does not require a new version

- Adding a new optional field to a response.
- Adding a new endpoint.
- Adding a new optional query parameter.
- Relaxing a validation rule (accepting input the previous version rejected).
- Bug fixes that bring behaviour in line with the documented contract.

## 3. What requires a new version (e.g. `/api/v2`)

- Removing or renaming a response field.
- Changing the type or meaning of an existing field.
- Removing an endpoint or a query parameter.
- Tightening a validation rule (rejecting input the previous version accepted).
- Any change to authentication or rate-limiting that would break an existing integration.

## 4. Deprecation process

1. A field, endpoint or parameter being deprecated is announced in this document's changelog (§6) with the deprecation date and the planned removal date.
2. Deprecated fields remain present and functional in responses for a minimum of **6 months** from the announcement date.
3. Once a new major version ships, the previous version is supported for a minimum of **12 months** before it may be shut down, per Handbook §2.1's API tier commitments to paying customers.
4. Breaking changes are never introduced into an existing version number — a breaking change always means a new version, never a silent change to `/api/v1`.

## 5. Communicating a deprecation to API customers

- Design-partner and paying customers (Handbook §2.1, Growth/Pro/Custom tiers) are notified by email at announcement and again 30 days before removal.
- The free-tier changelog (§6 of this document) is the source of truth for self-serve customers.

## 6. Changelog

| Date | Version | Change |
|---|---|---|
| — | v1 | Initial public API surface: `/events`, `/claims`, `/reliability`, `/entities/search`, `/billing`. No deprecations yet. |
