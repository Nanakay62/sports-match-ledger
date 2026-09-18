"""Persisted Pro entitlement state and webhook idempotency (Handbook §18.1/§18.5).

Deliberately separate from LedgerRepository: billing is not part of the
Accountability Ledger's append-only claim/evidence/resolution domain, and keeping
it isolated means a billing schema change can never touch ledger invariants.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import CustomerEntitlementModel, PaywallEventModel, ProcessedWebhookEventModel

FREE_WATCHLIST_LIMIT = 3
PRO_WATCHLIST_LIMIT = 99999
FREE_ARCHIVE_WINDOW_DAYS = 30
FREE_REPORTER_INDEX_LIMIT = 20

VALID_WALL_IDS = {"watchlist_limit", "archive_depth", "reporter_history", "reporter_index", "export"}
VALID_ACTIONS = {"shown", "clicked"}


class BillingRepository:
    @staticmethod
    def get_entitlement_by_email(session: Session, email: str) -> CustomerEntitlementModel | None:
        stmt = select(CustomerEntitlementModel).where(CustomerEntitlementModel.email == email.strip().lower())
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_entitlement_by_stripe_customer_id(session: Session, stripe_customer_id: str) -> CustomerEntitlementModel | None:
        stmt = select(CustomerEntitlementModel).where(CustomerEntitlementModel.stripe_customer_id == stripe_customer_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def upsert_entitlement(
        session: Session,
        email: str,
        *,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
        plan_id: str | None = None,
        status: str,
        is_pro: bool,
        current_period_end: datetime | None = None,
    ) -> CustomerEntitlementModel:
        """Idempotent upsert keyed on email. The webhook handler is the only caller —
        entitlement state is never accepted from a client request.
        """
        normalized_email = email.strip().lower()
        record = BillingRepository.get_entitlement_by_email(session, normalized_email)
        if record is None:
            record = CustomerEntitlementModel(id=f"cust_{uuid.uuid4().hex[:16]}", email=normalized_email)
            session.add(record)

        if stripe_customer_id is not None:
            record.stripe_customer_id = stripe_customer_id
        if stripe_subscription_id is not None:
            record.stripe_subscription_id = stripe_subscription_id
        if plan_id is not None:
            record.plan_id = plan_id
        record.status = status
        record.is_pro = is_pro
        record.current_period_end = current_period_end

        session.commit()
        session.refresh(record)
        return record

    @staticmethod
    def is_webhook_event_processed(session: Session, event_id: str) -> bool:
        stmt = select(ProcessedWebhookEventModel).where(ProcessedWebhookEventModel.event_id == event_id)
        return session.execute(stmt).scalar_one_or_none() is not None

    @staticmethod
    def mark_webhook_event_processed(session: Session, event_id: str, event_type: str) -> None:
        session.add(ProcessedWebhookEventModel(event_id=event_id, event_type=event_type))
        session.commit()

    @staticmethod
    def record_paywall_event(
        session: Session,
        wall_id: str,
        action: str,
        email: str | None = None,
        context: str | None = None,
    ) -> PaywallEventModel:
        """Records a single paywall impression or click for per-wall conversion measurement.

        Does not itself validate wall_id/action — the API layer checks those against
        VALID_WALL_IDS/VALID_ACTIONS before calling this, so a frontend typo fails the
        request loudly (400) instead of silently corrupting the conversion data.
        """
        record = PaywallEventModel(
            wall_id=wall_id,
            action=action,
            email=email.strip().lower() if email else None,
            context=context,
        )
        session.add(record)
        session.commit()
        return record

    @staticmethod
    def get_paywall_conversion_summary(session: Session) -> list[dict[str, Any]]:
        """Per-wall shown/clicked counts and conversion rate (Handbook §18.3/§18.5:
        "measure the conversion rate of each wall separately").
        """
        stmt = select(
            PaywallEventModel.wall_id,
            PaywallEventModel.action,
            func.count(PaywallEventModel.id),
        ).group_by(PaywallEventModel.wall_id, PaywallEventModel.action)
        rows = session.execute(stmt).all()

        by_wall: dict[str, dict[str, int]] = {}
        for wall_id, action, count in rows:
            by_wall.setdefault(wall_id, {"shown": 0, "clicked": 0})[action] = count

        summary = []
        for wall_id, counts in sorted(by_wall.items()):
            shown = counts.get("shown", 0)
            clicked = counts.get("clicked", 0)
            summary.append(
                {
                    "wall_id": wall_id,
                    "shown": shown,
                    "clicked": clicked,
                    "conversion_rate": round(clicked / shown, 4) if shown else 0.0,
                }
            )
        return summary
