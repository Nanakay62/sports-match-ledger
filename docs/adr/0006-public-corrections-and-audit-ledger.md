# ADR-0006: Public Corrections Desk & Editorial Control Plane

## Status
Accepted

## Context
Standard news platforms and social media aggregators frequently modify articles silently or delete discredited tweets when transfer rumours prove untrue or fees are exaggerated. This destroys the historical chain of custody and conceals source inaccuracy.

In a platform whose differentiator is the Accountability Ledger, mistakes, retractions, and contradictory claims must be preserved as first-class, immutable ledger items. Furthermore, editors require an operational control plane to manage source onboarding, review disputes, and inspect cost telemetry without bypassing append-only invariants.

## Decision
1. **Public Corrections Desk (`/corrections`)**:
   - Any superseded claim, retracted statement, or event transitioned to `corrected` or `disputed` status is automatically exposed on a public, transparent corrections page.
   - Every correction record pairs the original claim, timestamp, and outlet with the superseding statement and resolution rationale.
2. **Editorial Control Plane (`/admin`)**:
   - Source onboarding must follow a state machine: `PROPOSED` $\rightarrow$ `TECHNICAL_REVIEW` $\rightarrow$ `RIGHTS_REVIEW` $\rightarrow$ `APPROVED`.
   - The Human Review Queue isolates high-risk items (allegations, numerical discrepancies, single-source leaks) for editor confirmation.
   - Editorial actions (`confirm`, `dispute`, `correct`) never perform SQL `UPDATE` on historic claim text; they record amendments, mark supersession flags, and log notes on the parent event.
3. **Database-Level Immutability**:
   - Enforce database triggers in PostgreSQL preventing `DELETE` or destructive `UPDATE` operations on `claims` and `resolutions`.

## Consequences
- **Positive**: Complete auditability and public trust; readers can inspect every correction back to the original source; editors have clear operational workflows.
- **Negative**: Database storage grows monotonically; requires structured frontends and admin routing.
