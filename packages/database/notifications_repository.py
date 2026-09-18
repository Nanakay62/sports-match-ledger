"""Persisted alert subscriptions and the free-tier digest queue (Handbook §18.1).

Deliberately separate from LedgerRepository and BillingRepository, matching the
pattern set in packages/database/billing_repository.py: each bounded domain gets
its own small repository rather than one growing god-class.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AlertSubscriptionModel, DigestQueueItemModel


class NotificationsRepository:
    @staticmethod
    def subscribe(session: Session, email: str, event_id: str) -> AlertSubscriptionModel:
        """Idempotent: subscribing twice for the same (email, event_id) is a no-op."""
        normalized_email = email.strip().lower()
        existing = session.execute(
            select(AlertSubscriptionModel).where(
                AlertSubscriptionModel.email == normalized_email,
                AlertSubscriptionModel.event_id == event_id,
            )
        ).scalar_one_or_none()
        if existing:
            return existing

        record = AlertSubscriptionModel(id=f"asub_{uuid.uuid4().hex[:16]}", email=normalized_email, event_id=event_id)
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    @staticmethod
    def unsubscribe(session: Session, email: str, event_id: str) -> bool:
        normalized_email = email.strip().lower()
        existing = session.execute(
            select(AlertSubscriptionModel).where(
                AlertSubscriptionModel.email == normalized_email,
                AlertSubscriptionModel.event_id == event_id,
            )
        ).scalar_one_or_none()
        if not existing:
            return False
        session.delete(existing)
        session.commit()
        return True

    @staticmethod
    def get_subscriber_emails(session: Session, event_id: str) -> list[str]:
        rows = session.execute(select(AlertSubscriptionModel.email).where(AlertSubscriptionModel.event_id == event_id)).all()
        return [r[0] for r in rows]

    @staticmethod
    def get_subscribed_event_ids(session: Session, email: str) -> list[str]:
        normalized_email = email.strip().lower()
        rows = session.execute(select(AlertSubscriptionModel.event_id).where(AlertSubscriptionModel.email == normalized_email)).all()
        return [r[0] for r in rows]

    @staticmethod
    def queue_digest_item(
        session: Session,
        email: str,
        event_id: str,
        headline: str,
        old_status: str,
        new_status: str,
    ) -> DigestQueueItemModel:
        record = DigestQueueItemModel(
            id=f"dq_{uuid.uuid4().hex[:16]}",
            email=email.strip().lower(),
            event_id=event_id,
            headline=headline,
            old_status=old_status,
            new_status=new_status,
        )
        session.add(record)
        session.commit()
        return record

    @staticmethod
    def get_pending_digest_emails(session: Session) -> list[str]:
        """Distinct emails with at least one unsent digest item — the set send_daily_digests.py iterates."""
        rows = session.execute(select(DigestQueueItemModel.email).where(DigestQueueItemModel.sent_at.is_(None)).distinct()).all()
        return [r[0] for r in rows]

    @staticmethod
    def get_pending_digest_items(session: Session, email: str) -> list[DigestQueueItemModel]:
        normalized_email = email.strip().lower()
        return list(
            session.execute(
                select(DigestQueueItemModel)
                .where(DigestQueueItemModel.email == normalized_email, DigestQueueItemModel.sent_at.is_(None))
                .order_by(DigestQueueItemModel.created_at.asc())
            )
            .scalars()
            .all()
        )

    @staticmethod
    def mark_digest_items_sent(session: Session, item_ids: list[str], sent_at: datetime) -> None:
        if not item_ids:
            return
        items = session.execute(select(DigestQueueItemModel).where(DigestQueueItemModel.id.in_(item_ids))).scalars().all()
        for item in items:
            item.sent_at = sent_at
        session.commit()
