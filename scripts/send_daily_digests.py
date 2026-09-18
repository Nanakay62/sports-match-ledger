"""Sports News AI — Daily Alert Digest Sender (Handbook §18.1: Free tier = "Daily digest")

Batches every free-tier subscriber's pending watchlist status-change notifications
(queued by packages/notifications/dispatcher.py whenever a Pro-ineligible
subscriber's watched event changes status) into one email per subscriber, sends
it via the configured email backend, and marks those items sent so they are
never included in a future digest.

Run once daily (cron/scheduled task) — this script does not schedule itself.

Usage: PYTHONPATH=. python scripts/send_daily_digests.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.database.notifications_repository import NotificationsRepository
from packages.database.session import SessionLocal
from packages.notifications.email_backend import EmailMessage, get_default_email_backend


def build_digest_body(items) -> str:
    lines = [f"Your watchlist digest — {len(items)} update{'s' if len(items) != 1 else ''} today:", ""]
    for item in items:
        lines.append(f"- {item.headline}: {item.old_status} -> {item.new_status} (/event/{item.event_id})")
    lines.append("")
    lines.append("Want these the moment they happen instead of once a day? Upgrade to Pro at /pro.")
    return "\n".join(lines)


def main() -> int:
    backend = get_default_email_backend()
    sent_count = 0

    with SessionLocal() as session:
        emails = NotificationsRepository.get_pending_digest_emails(session)
        for email in emails:
            items = NotificationsRepository.get_pending_digest_items(session, email)
            if not items:
                continue

            message = EmailMessage(
                to=email,
                subject=f"Matchday Ledger: {len(items)} watchlist update{'s' if len(items) != 1 else ''}",
                body_text=build_digest_body(items),
            )
            if backend.send(message):
                NotificationsRepository.mark_digest_items_sent(session, item_ids=[i.id for i in items], sent_at=datetime.now(timezone.utc))
                sent_count += 1

    print(f"Sent {sent_count} daily digest email(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
