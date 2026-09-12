import json
import logging
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.database.models import PipelineJobModel, SourceRegistryModel, SourceRegistryStatus
from packages.database.queue import JobQueueService
from packages.database.session import SessionLocal

from .adapters.feed_parser import parse_feed_xml
from .speed_lane import SpeedLaneWorker

logger = logging.getLogger(__name__)

USER_AGENT = "SportsNewsAI-Ledger/1.0 (+https://github.com/sports-news-ai)"


class FeedPoller:
    """Scheduled poller consuming feed_poller jobs from the Postgres-backed queue.

    Preserves provenance, runs deterministically at Rung L0, and enforces idempotency.
    """

    def __init__(self, session_factory: Callable[[], Session] = SessionLocal):
        self.session_factory = session_factory

    @staticmethod
    def fetch_feed_content(feed_url: str, timeout: float = 10.0) -> bytes:
        """Fetches feed XML content over HTTP with strict timeout and custom user-agent."""
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

            # Fetch content if not provided directly
            raw_xml = feed_content if feed_content is not None else self.fetch_feed_content(source.feed_url)

            # Parse RSS 2.0 or Atom items
            articles = parse_feed_xml(
                content=raw_xml,
                outlet_name=source.source_name,
                default_language=source.language,
            )

            claims_created = 0
            idempotent_noops = 0
            evidence_attached = 0
            errors = 0

            worker = SpeedLaneWorker(session=db)

            for item in articles:
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

            db.commit()
            return {
                "status": "success",
                "source_name": source.source_name,
                "registry_id": source.id,
                "items_fetched": len(articles),
                "claims_created": claims_created,
                "idempotent_noops": idempotent_noops,
                "evidence_attached": evidence_attached,
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
