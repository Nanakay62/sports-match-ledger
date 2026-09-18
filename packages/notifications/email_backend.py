"""Pluggable email delivery for watchlist alerts (Handbook §18.1: "Alerts | Daily
digest | Real-time"). No email-sending infrastructure existed anywhere in this
codebase before this module — no SMTP, no third-party provider integration.

Defaults to a safe, credential-free ConsoleEmailBackend so the alert pipeline is
fully real and testable without needing an email provider account. A real
SMTPEmailBackend is available and activates automatically once SMTP_HOST is set
in the environment — the same "safe by default, real once configured" pattern
used for Stripe billing (see docs/adr/0017).
"""

import logging
import os
import smtplib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.message import EmailMessage as MimeEmailMessage
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)

OUTBOX_DIR = Path("data/emails")


@dataclass
class EmailMessage:
    to: str
    subject: str
    body_text: str
    sent_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EmailBackend(Protocol):
    def send(self, message: EmailMessage) -> bool: ...


class ConsoleEmailBackend:
    """Default backend: writes each email to data/emails/ and keeps an in-memory
    record. Never fails, never requires credentials — safe for development and
    for every environment until a real provider is configured.
    """

    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> bool:
        self.sent.append(message)
        try:
            OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
            safe_ts = message.sent_at.strftime("%Y%m%dT%H%M%S%f")
            path = OUTBOX_DIR / f"{safe_ts}_{message.to.replace('@', '_at_')}.txt"
            path.write_text(f"To: {message.to}\nSubject: {message.subject}\n\n{message.body_text}\n", encoding="utf-8")
        except Exception as exc:
            logger.warning(f"ConsoleEmailBackend failed to write outbox file: {exc}")
        return True


class SMTPEmailBackend:
    """Real SMTP delivery. Activated only when SMTP_HOST is configured — see
    SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD/SMTP_FROM_ADDRESS in .env.example.
    """

    def __init__(
        self,
        host: str,
        port: int = 587,
        username: str | None = None,
        password: str | None = None,
        from_address: str | None = None,
        use_tls: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_address = from_address or username or "alerts@localhost"
        self.use_tls = use_tls

    def send(self, message: EmailMessage) -> bool:
        mime_message = MimeEmailMessage()
        mime_message["Subject"] = message.subject
        mime_message["From"] = self.from_address
        mime_message["To"] = message.to
        mime_message.set_content(message.body_text)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(mime_message)
            return True
        except Exception as exc:
            logger.error(f"SMTPEmailBackend failed to send to {message.to}: {exc}")
            return False


_default_backend: EmailBackend | None = None


def get_default_email_backend() -> EmailBackend:
    """Returns the process-wide default backend: SMTP if SMTP_HOST is set, else
    the console backend. Cached so ConsoleEmailBackend's in-memory `sent` list is
    stable across calls within a process (tests rely on this).
    """
    global _default_backend
    if _default_backend is not None:
        return _default_backend

    smtp_host = os.getenv("SMTP_HOST")
    if smtp_host:
        _default_backend = SMTPEmailBackend(
            host=smtp_host,
            port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USER"),
            password=os.getenv("SMTP_PASSWORD"),
            from_address=os.getenv("SMTP_FROM_ADDRESS"),
        )
    else:
        _default_backend = ConsoleEmailBackend()
    return _default_backend


def reset_default_email_backend() -> None:
    """Test-only: clears the cached backend so a new one is constructed on next use."""
    global _default_backend
    _default_backend = None
