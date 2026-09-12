from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.database.models import Base, SourceRegistryModel, SourceRegistryStatus
from packages.database.queue import JobQueueService


def setup_in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def test_enqueue_and_fetch_job():
    session = setup_in_memory_db()

    job = JobQueueService.enqueue_job(
        session=session,
        lane="feed_poller",
        payload={"source": "test", "interval": 15},
    )
    assert job.id.startswith("job-")
    assert job.status == "pending"
    assert job.attempts == 0

    fetched = JobQueueService.fetch_next_job(session=session, lane="feed_poller")
    assert fetched is not None
    assert fetched.id == job.id
    assert fetched.status == "running"
    assert fetched.attempts == 1

    # No more pending jobs ready
    second_fetch = JobQueueService.fetch_next_job(session=session, lane="feed_poller")
    assert second_fetch is None


def test_complete_job_reschedules():
    session = setup_in_memory_db()

    JobQueueService.enqueue_job(
        session=session,
        lane="feed_poller",
        payload={"registry_id": "reg-test-source"},
    )
    fetched = JobQueueService.fetch_next_job(session=session, lane="feed_poller")
    assert fetched is not None

    completed = JobQueueService.complete_job(
        session=session,
        job_id=fetched.id,
        reschedule_interval_minutes=10,
    )
    assert completed.status == "completed"

    jobs = JobQueueService.list_jobs(session=session, lane="feed_poller")
    assert len(jobs) == 2
    statuses = {j.status for j in jobs}
    assert statuses == {"completed", "pending"}


def test_fail_job_retries_and_terminates():
    session = setup_in_memory_db()

    JobQueueService.enqueue_job(
        session=session,
        lane="feed_poller",
        payload={"registry_id": "reg-fail-test"},
    )

    # First attempt fails -> pending retry
    fetched = JobQueueService.fetch_next_job(session=session, lane="feed_poller")
    assert fetched is not None
    retrying = JobQueueService.fail_job(session, fetched.id, "Network timeout", max_attempts=2)
    assert retrying.status == "pending"

    # Second attempt fails -> permanently failed
    fetched2 = JobQueueService.fetch_next_job(session=session, lane="feed_poller")
    if fetched2:
        failed = JobQueueService.fail_job(session, fetched2.id, "Network timeout again", max_attempts=2)
        assert failed.status == "failed"


def test_sync_approved_sources():
    session = setup_in_memory_db()

    # Create approved source
    s1 = SourceRegistryModel(
        id="reg-approved-1",
        source_name="Approved Source 1",
        feed_url="https://example.com/rss1.xml",
        feed_format="rss2",
        language="en",
        coverage_category="general",
        authority_rank=3,
        status=SourceRegistryStatus.APPROVED.value,
        polling_interval_minutes=10,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    # Create proposed source (should not be queued)
    s2 = SourceRegistryModel(
        id="reg-proposed-2",
        source_name="Proposed Source 2",
        feed_url="https://example.com/rss2.xml",
        feed_format="rss2",
        language="es",
        coverage_category="general",
        authority_rank=3,
        status=SourceRegistryStatus.PROPOSED.value,
        polling_interval_minutes=15,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add_all([s1, s2])
    session.flush()

    created = JobQueueService.sync_approved_sources(session)
    assert len(created) == 1
    assert "reg-approved-1" in created[0].payload

    # Re-sync should not create duplicate jobs
    created_again = JobQueueService.sync_approved_sources(session)
    assert len(created_again) == 0
