# ADR-0016: API Versioning and Deprecation Policy

## Status
Accepted

## Context
Handbook §18.4 requires the public claims API to ship with "versioning from day one with a written deprecation policy." `/api/v1` path prefixing (`apps/api/app/main.py`) has existed since Phase 1, but auditing for this ADR found no deprecation policy document anywhere in the repository — `docs/OBJECTIVES_CHECKLIST.md` had marked this item verified, which was not accurate; only the versioning half existed.

## Decision
All routers are mounted under `/api/v1` (`apps/api/app/main.py`), and every future breaking change gets a new version prefix rather than a silent change to an existing one. `docs/api-versioning-policy.md` is the written policy the handbook asks for: what counts as a breaking vs. non-breaking change, a minimum 6-month deprecation notice before a field or endpoint is removed, a minimum 12-month support window for a superseded major version once a successor ships, and how design-partner/paying customers (per the API tiers in Handbook §2.1) are notified.

## Consequences
- **Positive**: there is now an actual answer, written down, to "can we remove this field" or "how long do we have to support v1 once v2 ships" — before this ADR that question had no documented answer at all.
- **Negative**: the policy is untested by a real deprecation — the 6-month/12-month windows are the handbook's stated commercial commitment translated into a process, not something validated against an actual API customer relationship yet, since the API currently has none.
