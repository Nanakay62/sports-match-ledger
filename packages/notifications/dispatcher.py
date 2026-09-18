"""Routes a watched event's status change to either an immediate email (Pro,
"real-time") or the daily digest queue (Free) — Handbook §18.1's Alerts row is
the last of the five paywall walls (Handbook §18.3) that previously had no real
feature behind it at all; see docs/adr/0018 for that history.
"""

from sqlalchemy.orm import Session

from packages.database.billing_repository import BillingRepository
from packages.database.notifications_repository import NotificationsRepository

from .email_backend import EmailBackend, EmailMessage, get_default_email_backend


class NotificationDispatcher:
    def __init__(self, email_backend: EmailBackend | None = None):
        self.email_backend = email_backend or get_default_email_backend()

    def dispatch_status_change(
        self,
        session: Session,
        event_id: str,
        headline: str,
        old_status: str,
        new_status: str,
    ) -> dict[str, int]:
        """Notifies every subscriber to event_id that its status changed.

        Pro subscribers (has_realtime_alerts) are emailed immediately. Everyone
        else — including a subscriber with no entitlement record at all, which
        fails safe to Free — is queued for the next daily digest.
        """
        if old_status == new_status:
            return {"immediate": 0, "queued": 0}

        subscriber_emails = NotificationsRepository.get_subscriber_emails(session, event_id)
        immediate_count = 0
        queued_count = 0

        for email in subscriber_emails:
            record = BillingRepository.get_entitlement_by_email(session, email)
            is_realtime = bool(record and record.is_pro and record.status == "active")

            if is_realtime:
                message = EmailMessage(
                    to=email,
                    subject=f"[Matchday Ledger] Status update: {headline}",
                    body_text=(
                        f"{headline}\n\nStatus changed: {old_status} -> {new_status}\n\nView the full evidence trail: /event/{event_id}"
                    ),
                )
                if self.email_backend.send(message):
                    immediate_count += 1
            else:
                NotificationsRepository.queue_digest_item(
                    session,
                    email=email,
                    event_id=event_id,
                    headline=headline,
                    old_status=old_status,
                    new_status=new_status,
                )
                queued_count += 1

        return {"immediate": immediate_count, "queued": queued_count}
