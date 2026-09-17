import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import DeadLetterJobModel, PipelineJobModel, SourceRegistryModel, SourceRegistryStatus


class JobQueueService:
    """Manages scheduled jobs on the pipeline_jobs table."""

    @staticmethod
    def enqueue_job(
        session: Session,
        lane: str,
        payload: dict[str, Any],
        scheduled_at: datetime | None = None,
        job_id: str | None = None,
    ) -> PipelineJobModel:
        """Enqueues a job into pipeline_jobs with pending status."""
        if scheduled_at is None:
            scheduled_at = datetime.now(timezone.utc)
        elif scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

        actual_id = job_id or f"job-{uuid.uuid4().hex[:12]}"
        job = PipelineJobModel(
            id=actual_id,
            lane=lane,
            status="pending",
            payload=json.dumps(payload),
            attempts=0,
            scheduled_at=scheduled_at,
            created_at=datetime.now(timezone.utc),
        )
        session.add(job)
        session.flush()
        return job

    @staticmethod
    def sync_approved_sources(session: Session) -> list[PipelineJobModel]:
        """Ensures every approved source in the registry has an active or pending polling job."""
        approved_stmt = select(SourceRegistryModel).where(SourceRegistryModel.status == SourceRegistryStatus.APPROVED.value)
        approved_sources = list(session.execute(approved_stmt).scalars().all())

        created_jobs: list[PipelineJobModel] = []
        now = datetime.now(timezone.utc)

        for source in approved_sources:
            # Check for existing pending or running job for this source
            existing_jobs = list(
                session.execute(
                    select(PipelineJobModel).where(
                        PipelineJobModel.lane == "feed_poller",
                        PipelineJobModel.status.in_(["pending", "running"]),
                    )
                )
                .scalars()
                .all()
            )

            has_active_job = False
            for j in existing_jobs:
                try:
                    p = json.loads(j.payload)
                    if p.get("registry_id") == source.id or p.get("feed_url") == source.feed_url:
                        has_active_job = True
                        break
                except Exception:
                    continue

            if not has_active_job:
                payload = {
                    "registry_id": source.id,
                    "source_name": source.source_name,
                    "feed_url": source.feed_url,
                    "feed_format": source.feed_format,
                    "language": source.language,
                    "authority_rank": source.authority_rank,
                    "polling_interval_minutes": source.polling_interval_minutes,
                }
                job_id = f"job-poll-{source.id[4:] if source.id.startswith('reg-') else source.id}-{uuid.uuid4().hex[:6]}"
                new_job = PipelineJobModel(
                    id=job_id,
                    lane="feed_poller",
                    status="pending",
                    payload=json.dumps(payload),
                    attempts=0,
                    scheduled_at=now,
                    created_at=now,
                )
                session.add(new_job)
                created_jobs.append(new_job)

        # Cancel any pending jobs for sources that are paused, blocked, or rejected
        non_approved_stmt = select(SourceRegistryModel.id).where(
            SourceRegistryModel.status.in_(
                [
                    SourceRegistryStatus.PAUSED.value,
                    SourceRegistryStatus.BLOCKED.value,
                    SourceRegistryStatus.PROPOSED.value,
                    SourceRegistryStatus.REJECTED.value,
                ]
            )
        )
        non_approved_ids = set(session.execute(non_approved_stmt).scalars().all())
        if non_approved_ids:
            pending_jobs = list(
                session.execute(
                    select(PipelineJobModel).where(
                        PipelineJobModel.lane == "feed_poller",
                        PipelineJobModel.status == "pending",
                    )
                )
                .scalars()
                .all()
            )
            for pj in pending_jobs:
                try:
                    p_data = json.loads(pj.payload)
                    if p_data.get("registry_id") in non_approved_ids:
                        pj.status = "cancelled"
                except Exception:
                    continue

        session.flush()
        return created_jobs

    @staticmethod
    def fetch_next_job(session: Session, lane: str = "feed_poller") -> PipelineJobModel | None:
        """Pulls the next ready job for the given lane, marking it running."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(PipelineJobModel)
            .where(
                PipelineJobModel.lane == lane,
                PipelineJobModel.status == "pending",
                PipelineJobModel.scheduled_at <= now,
            )
            .order_by(PipelineJobModel.scheduled_at.asc())
        )

        # Apply row-level lock if supported by the database dialect
        bind = session.get_bind()
        if bind is not None and bind.dialect.name == "postgresql":
            stmt = stmt.with_for_update(skip_locked=True)

        job = session.execute(stmt).scalars().first()
        if not job:
            return None

        job.status = "running"
        job.attempts += 1
        session.flush()
        return job

    @staticmethod
    def complete_job(
        session: Session,
        job_id: str,
        reschedule_interval_minutes: int | None = None,
    ) -> PipelineJobModel:
        """Marks a job as completed and optionally enqueues the next scheduled cycle."""
        job = session.execute(select(PipelineJobModel).where(PipelineJobModel.id == job_id)).scalar_one_or_none()

        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = "completed"
        now = datetime.now(timezone.utc)

        if reschedule_interval_minutes and reschedule_interval_minutes > 0:
            next_run = now + timedelta(minutes=reschedule_interval_minutes)
            payload_data = json.loads(job.payload)
            next_id = f"job-poll-{payload_data.get('registry_id', 'src')}-{uuid.uuid4().hex[:6]}"
            next_job = PipelineJobModel(
                id=next_id,
                lane=job.lane,
                status="pending",
                payload=job.payload,
                attempts=0,
                scheduled_at=next_run,
                created_at=now,
            )
            session.add(next_job)

        session.flush()
        return job

    @staticmethod
    def fail_job(
        session: Session,
        job_id: str,
        error_message: str,
        max_attempts: int = 3,
        retry_delay_minutes: int = 5,
    ) -> PipelineJobModel:
        """Handles job failure: retries with backoff or transitions to dead_letter status."""
        job = session.execute(select(PipelineJobModel).where(PipelineJobModel.id == job_id)).scalar_one_or_none()

        if not job:
            raise ValueError(f"Job {job_id} not found")

        now = datetime.now(timezone.utc)
        if job.attempts >= max_attempts:
            job.status = "dead_letter"
            dlj = DeadLetterJobModel(
                id=f"dlj-{uuid.uuid4().hex[:12]}",
                job_id=job.id,
                lane=job.lane,
                payload=job.payload,
                attempts=job.attempts,
                error_message=error_message,
                last_failed_at=now,
                replayed=False,
                replayed_at=None,
            )
            session.add(dlj)
        else:
            job.status = "pending"
            job.scheduled_at = now + timedelta(minutes=retry_delay_minutes)

        session.flush()
        return job

    @staticmethod
    def replay_dead_letter_job(session: Session, dead_letter_id: str) -> PipelineJobModel:
        """Re-enqueues an exhausted dead-letter job for execution and marks the dead-letter record as replayed."""
        dlj = session.execute(select(DeadLetterJobModel).where(DeadLetterJobModel.id == dead_letter_id)).scalar_one_or_none()
        if not dlj:
            raise ValueError(f"Dead letter job {dead_letter_id} not found")

        now = datetime.now(timezone.utc)
        new_job = PipelineJobModel(
            id=f"job-replayed-{uuid.uuid4().hex[:10]}",
            lane=dlj.lane,
            status="pending",
            payload=dlj.payload,
            attempts=0,
            scheduled_at=now,
            created_at=now,
        )
        session.add(new_job)
        dlj.replayed = True
        dlj.replayed_at = now
        session.flush()
        return new_job

    @staticmethod
    def list_dead_letters(session: Session, limit: int = 50) -> list[DeadLetterJobModel]:
        """Lists dead letter entries ordered by last failure time."""
        stmt = select(DeadLetterJobModel).order_by(DeadLetterJobModel.last_failed_at.desc()).limit(limit)
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def list_jobs(
        session: Session,
        lane: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[PipelineJobModel]:
        """Lists pipeline jobs with optional lane and status filters."""
        stmt = select(PipelineJobModel)
        if lane:
            stmt = stmt.where(PipelineJobModel.lane == lane)
        if status:
            stmt = stmt.where(PipelineJobModel.status == status)
        stmt = stmt.order_by(PipelineJobModel.scheduled_at.desc()).limit(limit)
        return list(session.execute(stmt).scalars().all())
