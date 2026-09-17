import ipaddress
import json
import logging
import socket
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.database.models import (
    PipelineJobModel,
    QuarantinedDocumentModel,
    SourceRegistryModel,
    SourceRegistryStatus,
)
from packages.database.queue import JobQueueService
from packages.database.session import SessionLocal

from .adapters.feed_parser import parse_feed_xml
from .adapters.rss_adapter import calculate_extraction_confidence
from .circuit_breaker import DomainCircuitBreaker, default_circuit_breaker
from .speed_lane import SpeedLaneWorker

logger = logging.getLogger(__name__)

USER_AGENT = "SportsNewsAI-Ledger/1.0 (+https://github.com/sports-news-ai)"


def is_safe_public_url(url: str) -> tuple[bool, str]:
    """Validates that a URL does not resolve to private, loopback, link-local, or cloud metadata IP addresses (SSRF protection).

    Returns (is_safe, message).
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"Unsupported scheme '{parsed.scheme}': only HTTP/HTTPS permitted"

        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname in URL"

        # Check if hostname is directly an IP literal
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or not ip.is_global:
                return False, f"Blocked private/reserved IP: {ip}"
            return True, str(ip)
        except ValueError:
            pass  # Domain name, resolve via DNS

        # Block localhost directly
        if hostname.lower() in ("localhost", "localhost.localdomain"):
            return False, f"Blocked localhost hostname: {hostname}"

        # Resolve hostname via socket.getaddrinfo
        addr_info = socket.getaddrinfo(hostname, None)
        if not addr_info:
            return False, f"DNS resolution failed for hostname '{hostname}'"

        for item in addr_info:
            ip_str = item[4][0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or not ip.is_global:
                return False, f"Hostname '{hostname}' resolved to blocked private/reserved IP: {ip}"

        return True, "valid"
    except Exception as exc:
        return False, f"URL security validation error: {exc}"


class FeedPoller:
    """Scheduled poller consuming feed_poller jobs from the Postgres-backed queue.

    Preserves provenance, runs deterministically at Rung L0, and enforces idempotency.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session] = SessionLocal,
        circuit_breaker: DomainCircuitBreaker | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.circuit_breaker = circuit_breaker or default_circuit_breaker

    @staticmethod
    def fetch_feed_content(feed_url: str, timeout: float = 10.0) -> bytes:
        """Fetches feed XML content over HTTP with strict timeout, SSRF protection, and custom user-agent."""
        is_safe, msg = is_safe_public_url(feed_url)
        if not is_safe:
            raise PermissionError(f"SSRF Protection: {msg}")

        req = urllib.request.Request(
            feed_url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ConnectionError(f"Failed to fetch feed at {feed_url}: {exc}") from exc

    def poll_source_by_registry_id(
        self,
        registry_id: str,
        feed_content: bytes | None = None,
        session: Session | None = None,
    ) -> dict[str, Any]:
        """Polls an approved source, parses articles, and submits to the Speed Lane."""
        owns_session = session is None
        db = self.session_factory() if owns_session else session
        assert db is not None

        try:
            source = db.execute(select(SourceRegistryModel).where(SourceRegistryModel.id == registry_id)).scalar_one_or_none()

            if not source:
                return {"status": "error", "error": f"Source {registry_id} not found"}

            if source.status != SourceRegistryStatus.APPROVED.value:
                return {
                    "status": "skipped",
                    "reason": f"Source {registry_id} status is '{source.status}', not APPROVED",
                }

            # Check circuit breaker before making any network request
            if feed_content is None and not self.circuit_breaker.can_request(source.feed_url):
                return {
                    "status": "circuit_open",
                    "reason": f"Circuit breaker OPEN for domain of {source.feed_url}. Cooling down.",
                }

            # Fetch content if not provided directly
            try:
                raw_xml = feed_content if feed_content is not None else self.fetch_feed_content(source.feed_url)
                if feed_content is None:
                    self.circuit_breaker.record_success(source.feed_url)
            except PermissionError as sec_exc:
                qdoc = QuarantinedDocumentModel(
                    id=f"qdoc-{uuid.uuid4().hex[:12]}",
                    source_name=source.source_name,
                    source_url=source.feed_url,
                    raw_payload=json.dumps({"error": str(sec_exc), "feed_url": source.feed_url}),
                    rejection_reason=f"Security Violation (SSRF): {sec_exc}",
                    confidence_score=0.0,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(qdoc)
                db.commit()
                return {
                    "status": "security_quarantine",
                    "reason": str(sec_exc),
                    "registry_id": registry_id,
                }
            except Exception:
                if feed_content is None:
                    self.circuit_breaker.record_failure(source.feed_url)
                raise

            # Parse RSS 2.0 or Atom items
            articles = parse_feed_xml(
                content=raw_xml,
                outlet_name=source.source_name,
                default_language=source.language,
            )

            claims_created = 0
            idempotent_noops = 0
            evidence_attached = 0
            quarantined_count = 0
            errors = 0

            worker = SpeedLaneWorker(session=db)

            for item in articles:
                # Deterministic confidence evaluation & quarantine gate
                headline = str(item.get("headline", ""))
                body = str(item.get("body", ""))
                confidence = calculate_extraction_confidence(
                    headline=headline,
                    body=body,
                    author=item.get("author"),
                )
                body_words = len(body.split())

                if confidence < 0.50 or body_words < 15:
                    qdoc = QuarantinedDocumentModel(
                        id=f"qdoc-{uuid.uuid4().hex[:12]}",
                        source_name=source.source_name,
                        source_url=item.get("source_url", ""),
                        raw_payload=json.dumps(item, default=str),
                        rejection_reason=f"Low confidence ({confidence:.2f}) or short body ({body_words} words)",
                        confidence_score=confidence,
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(qdoc)
                    quarantined_count += 1
                    continue

                try:
                    result = worker.process_raw_article(item)
                    action = result.get("action")
                    if action == "idempotent_noop":
                        idempotent_noops += 1
                    elif action in {"evidence_attached", "corroborating_evidence_attached"}:
                        evidence_attached += 1
                    else:
                        claims_created += 1
                except Exception as exc:
                    logger.warning("Error ingesting article %s: %s", item.get("source_url"), exc)
                    errors += 1
                    qdoc = QuarantinedDocumentModel(
                        id=f"qdoc-{uuid.uuid4().hex[:12]}",
                        source_name=source.source_name,
                        source_url=item.get("source_url", ""),
                        raw_payload=json.dumps(item, default=str),
                        rejection_reason=f"Ingestion processing failure: {exc}",
                        confidence_score=0.0,
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(qdoc)
                    quarantined_count += 1

            db.commit()
            return {
                "status": "success",
                "source_name": source.source_name,
                "registry_id": source.id,
                "items_fetched": len(articles),
                "claims_created": claims_created,
                "idempotent_noops": idempotent_noops,
                "evidence_attached": evidence_attached,
                "quarantined": quarantined_count,
                "errors": errors,
            }
        except Exception as exc:
            db.rollback()
            return {"status": "failed", "error": str(exc)}
        finally:
            if owns_session:
                db.close()

    def process_job(self, job_id: str, session: Session) -> dict[str, Any]:
        """Processes a single feed_poller job, updating queue state and rescheduling."""
        job = session.execute(select(PipelineJobModel).where(PipelineJobModel.id == job_id)).scalar_one_or_none()

        if not job:
            return {"status": "error", "error": f"Job {job_id} not found"}

        try:
            payload = json.loads(job.payload)
            registry_id = payload["registry_id"]
            interval_minutes = int(payload.get("polling_interval_minutes", 15))

            poll_result = self.poll_source_by_registry_id(registry_id=registry_id, session=session)

            if poll_result.get("status") in {"success", "skipped"}:
                JobQueueService.complete_job(
                    session=session,
                    job_id=job.id,
                    reschedule_interval_minutes=interval_minutes,
                )
                session.commit()
                return {"status": "completed", "poll_result": poll_result}
            elif poll_result.get("status") == "circuit_open":
                # Reschedule without consuming attempt counts
                job.status = "pending"
                job.scheduled_at = datetime.now(timezone.utc) + timedelta(minutes=5)
                session.commit()
                return {"status": "circuit_open", "reason": poll_result.get("reason")}
            else:
                err_msg = poll_result.get("error", "Unknown polling failure")
                JobQueueService.fail_job(session=session, job_id=job.id, error_message=err_msg)
                session.commit()
                return {"status": "failed", "error": err_msg}
        except Exception as exc:
            session.rollback()
            JobQueueService.fail_job(session=session, job_id=job.id, error_message=str(exc))
            session.commit()
            return {"status": "failed", "error": str(exc)}

    def run_once(self) -> int:
        """Runs a single polling cycle: syncs approved sources and processes all ready jobs."""
        with self.session_factory() as session:
            # Sync approved sources to ensure every approved source has a job
            JobQueueService.sync_approved_sources(session)
            session.commit()

            processed_count = 0
            while True:
                job = JobQueueService.fetch_next_job(session, lane="feed_poller")
                if not job:
                    break
                session.commit()

                self.process_job(job_id=job.id, session=session)
                processed_count += 1

            return processed_count
