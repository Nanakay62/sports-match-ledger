"""Persisted Pro entitlement state and webhook idempotency (Handbook §18.1/§18.5).

Deliberately separate from LedgerRepository: billing is not part of the
Accountability Ledger's append-only claim/evidence/resolution domain, and keeping
it isolated means a billing schema change can never touch ledger invariants.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import CustomerEntitlementModel, ProcessedWebhookEventModel

FREE_WATCHLIST_LIMIT = 3
PRO_WATCHLIST_LIMIT = 99999


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
