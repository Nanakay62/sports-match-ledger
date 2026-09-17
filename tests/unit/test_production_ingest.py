import json
import time
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from packages.database.models import (
    Base,
    ClaimModel,
    DeadLetterJobModel,
    EventModel,
    QuarantinedDocumentModel,
    SourceRegistryStatus,
)
from packages.database.queue import JobQueueService
from packages.database.registry import SourceRegistryService
from packages.database.session import get_db
from workers.pipeline.adapters.rss_adapter import calculate_extraction_confidence
from workers.pipeline.circuit_breaker import CircuitState, DomainCircuitBreaker
from workers.pipeline.feed_poller import FeedPoller


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# 1. Source Registry Lifecycle: PAUSED and BLOCKED States & Metadata
# ---------------------------------------------------------------------------


def test_source_registry_operational_metadata_and_lifecycle(db_session):
    # Propose source with operational metadata
    item = SourceRegistryService.propose_source(
        session=db_session,
        source_name="Corriere dello Sport",
        feed_url="https://www.corrieredellosport.it/rss/calciomercato",
        language="it",
        authority_rank=3,
        robots_status="allowed",
        terms_review_date="2026-09-01",
        publisher_contact="legal@corrieredellosport.it",
        per_domain_rate_limit_seconds=2.5,
    )

    assert item.status == SourceRegistryStatus.PROPOSED.value
    assert item.robots_status == "allowed"
    assert item.terms_review_date is not None
    assert item.terms_review_date.isoformat().startswith("2026-09-01")
    assert item.publisher_contact == "legal@corrieredellosport.it"
    assert item.per_domain_rate_limit_seconds == 2.5

    # Cannot pause or resume from PROPOSED
    with pytest.raises(ValueError, match="Can only pause APPROVED sources"):
        SourceRegistryService.pause_source(session=db_session, registry_id=item.id)

    # Advance to APPROVED
    SourceRegistryService.run_technical_review(session=db_session, registry_id=item.id)
    SourceRegistryService.run_rights_review(session=db_session, registry_id=item.id, rights_notes="Verified public feed terms")
    approved = SourceRegistryService.approve_source(session=db_session, registry_id=item.id)
    assert approved.status == SourceRegistryStatus.APPROVED.value

    # Pause source
    paused = SourceRegistryService.pause_source(session=db_session, registry_id=item.id, pause_reason="Rate limit exceeded by upstream")
    assert paused.status == SourceRegistryStatus.PAUSED.value
    assert paused.pause_reason == "Rate limit exceeded by upstream"

    # Cannot pause already paused source
    with pytest.raises(ValueError, match="Can only pause APPROVED sources"):
        SourceRegistryService.pause_source(session=db_session, registry_id=item.id)

    # Resume source
    resumed = SourceRegistryService.resume_source(session=db_session, registry_id=item.id)
    assert resumed.status == SourceRegistryStatus.APPROVED.value
    assert resumed.pause_reason is None

    # Block source
    blocked = SourceRegistryService.block_source(session=db_session, registry_id=item.id, block_reason="DMCA takedown notice received")
    assert blocked.status == SourceRegistryStatus.BLOCKED.value
    assert blocked.block_reason == "DMCA takedown notice received"

    # Blocked source cannot be paused or resumed
    with pytest.raises(ValueError, match="Can only pause APPROVED sources"):
        SourceRegistryService.pause_source(session=db_session, registry_id=item.id)
    with pytest.raises(ValueError, match="Can only resume PAUSED sources"):
        SourceRegistryService.resume_source(session=db_session, registry_id=item.id)


def test_queue_sync_cancels_jobs_for_paused_and_blocked_sources(db_session):
    # Propose and approve source
    item = SourceRegistryService.propose_source(
        session=db_session,
        source_name="Kicker",
        feed_url="https://rss.kicker.de/news/aktuell",
        language="de",
    )
    SourceRegistryService.run_technical_review(session=db_session, registry_id=item.id)
    SourceRegistryService.run_rights_review(session=db_session, registry_id=item.id, rights_notes="Verified public feed terms")
    SourceRegistryService.approve_source(session=db_session, registry_id=item.id)

    # Sync creates a pending job
    jobs = JobQueueService.sync_approved_sources(session=db_session)
    assert len(jobs) == 1
    assert jobs[0].status == "pending"

    # Pause source and sync again -> pending job should be cancelled
    SourceRegistryService.pause_source(session=db_session, registry_id=item.id, pause_reason="Maintenance")
    JobQueueService.sync_approved_sources(session=db_session)

    all_jobs = JobQueueService.list_jobs(session=db_session)
    assert len(all_jobs) == 1
    assert all_jobs[0].status == "cancelled"


# ---------------------------------------------------------------------------
# 2. Domain Circuit Breaker Transitions
# ---------------------------------------------------------------------------


def test_circuit_breaker_lifecycle():
    cb = DomainCircuitBreaker(failure_threshold=3, cooldown_seconds=0.05)
    url = "https://failing-source.com/rss/feed.xml"

    # 1. Initially CLOSED
    assert cb.can_request(url) is True
    assert cb.get_state(url) == CircuitState.CLOSED

    # 2. Record failures below threshold
    cb.record_failure(url)
    cb.record_failure(url)
    assert cb.can_request(url) is True
    assert cb.get_state(url) == CircuitState.CLOSED

    # 3. Third failure trips to OPEN
    cb.record_failure(url)
    assert cb.get_state(url) == CircuitState.OPEN
    assert cb.can_request(url) is False

    # 4. Wait for cooldown to expire -> transitions to HALF_OPEN
    time.sleep(0.06)
    assert cb.can_request(url) is True
    assert cb.get_state(url) == CircuitState.HALF_OPEN

    # 5. Failure during probe trips immediately back to OPEN
    cb.record_failure(url)
    assert cb.get_state(url) == CircuitState.OPEN
    assert cb.can_request(url) is False

    # 6. Wait for cooldown again -> probe succeeds -> transitions to CLOSED
    time.sleep(0.06)
    assert cb.can_request(url) is True
    cb.record_success(url)
    assert cb.get_state(url) == CircuitState.CLOSED
    assert cb.can_request(url) is True


# ---------------------------------------------------------------------------
# 3. Dead-Letter Queue & Replay
# ---------------------------------------------------------------------------


def test_dead_letter_queue_and_replay(db_session):
    job = JobQueueService.enqueue_job(
        session=db_session,
        lane="feed_poller",
        payload={"registry_id": "reg-dl-test", "feed_url": "https://flaky.org/rss"},
    )

    # Attempt 1 fails
    j1 = JobQueueService.fetch_next_job(session=db_session, lane="feed_poller")
    assert j1 is not None
    JobQueueService.fail_job(session=db_session, job_id=j1.id, error_message="HTTP 500", max_attempts=3)
    assert j1.status == "pending"

    # Attempt 2 fails
    j1.scheduled_at = datetime.now(timezone.utc)
    j2 = JobQueueService.fetch_next_job(session=db_session, lane="feed_poller")
    assert j2 is not None
    JobQueueService.fail_job(session=db_session, job_id=j2.id, error_message="HTTP 502", max_attempts=3)
    assert j2.status == "pending"

    # Attempt 3 fails -> transitions to dead_letter
    j2.scheduled_at = datetime.now(timezone.utc)
    j3 = JobQueueService.fetch_next_job(session=db_session, lane="feed_poller")
    assert j3 is not None
    JobQueueService.fail_job(session=db_session, job_id=j3.id, error_message="HTTP 503 Timeout", max_attempts=3)
    assert j3.status == "dead_letter"

    # Verify dead letter entry exists
    dead_letters = JobQueueService.list_dead_letters(session=db_session)
    assert len(dead_letters) == 1
    dl = dead_letters[0]
    assert dl.job_id == job.id
    assert dl.attempts == 3
    assert "HTTP 503 Timeout" in dl.error_message
    assert dl.replayed is False

    # Replay dead letter job
    replayed_job = JobQueueService.replay_dead_letter_job(session=db_session, dead_letter_id=dl.id)
    assert replayed_job.status == "pending"
    assert replayed_job.attempts == 0
    assert dl.replayed is True
    assert dl.replayed_at is not None


# ---------------------------------------------------------------------------
# 4. Ingestion Confidence Scoring & Quarantine Pool
# ---------------------------------------------------------------------------


def test_extraction_confidence_scoring():
    # High confidence: Complete headline and substantial body
    high_score = calculate_extraction_confidence(
        headline="Arsenal agree personal terms with Mikel Merino ahead of EUR 35m transfer",
        body="Arsenal have reached a full agreement on personal terms with Spanish midfielder Mikel Merino. The Real Sociedad player is keen on the move to London.",
        author="David Ornstein",
    )
    assert high_score >= 0.90

    # Low confidence: Short/truncated body (<15 words)
    low_body_score = calculate_extraction_confidence(
        headline="Big transfer breaking news updates",
        body="Subscribe now to read the full story and analysis.",
        author="Staff",
    )
    assert low_body_score < 0.50

    # Low confidence: Error boilerplate text
    error_score = calculate_extraction_confidence(
        headline="Page Not Found - Error 404",
        body="The requested URL was not found on this server. Access denied. 403 Forbidden.",
        author=None,
    )
    assert error_score < 0.50


def test_feed_poller_quarantines_low_confidence_documents(db_session):
    # Propose and approve source
    item = SourceRegistryService.propose_source(
        session=db_session,
        source_name="Telegraph Sport",
        feed_url="https://www.telegraph.co.uk/football/rss.xml",
        language="en",
    )
    SourceRegistryService.run_technical_review(session=db_session, registry_id=item.id)
    SourceRegistryService.run_rights_review(session=db_session, registry_id=item.id, rights_notes="Verified public feed terms")
    SourceRegistryService.approve_source(session=db_session, registry_id=item.id)

    # Feed with 1 good article and 1 low-confidence article (<15 words, paywall boilerplate)
    feed_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Telegraph Football</title>
        <link>https://www.telegraph.co.uk</link>
        <item>
          <title>Real Madrid agree EUR 120m transfer package for Jude Bellingham</title>
          <link>https://www.telegraph.co.uk/football/2026/06/bellingham-deal/</link>
          <description>Real Madrid have finalised terms with Borussia Dortmund for Jude Bellingham in a deal worth up to 120 million euros. The midfielder will undergo a medical next week before signing a six-year contract.</description>
          <author>Sam Wallace</author>
          <pubDate>Mon, 01 Jun 2026 12:00:00 GMT</pubDate>
        </item>
        <item>
          <title>Breaking Transfer Update</title>
          <link>https://www.telegraph.co.uk/football/2026/06/stub-paywall/</link>
          <description>Subscribe to read the full story on our website.</description>
          <author>Newsdesk</author>
          <pubDate>Mon, 01 Jun 2026 12:30:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    poller = FeedPoller(session_factory=lambda: db_session)
    result = poller.poll_source_by_registry_id(registry_id=item.id, feed_content=feed_xml, session=db_session)

    assert result["status"] == "success"
    assert result["items_fetched"] == 2
    assert result["claims_created"] == 1
    assert result["quarantined"] == 1

    # Check that quarantined doc was persisted in quarantined_documents
    qdocs = db_session.execute(select(QuarantinedDocumentModel)).scalars().all()
    assert len(qdocs) == 1
    assert qdocs[0].source_name == "Telegraph Sport"
    assert "stub-paywall" in qdocs[0].source_url
    assert qdocs[0].confidence_score < 0.50
    assert "Low confidence" in qdocs[0].rejection_reason

    # Verify that the quarantined article DID NOT create a claim or event in the ledger
    claims = db_session.execute(select(ClaimModel)).scalars().all()
    assert len(claims) == 1
    assert "Bellingham" in claims[0].claim_text

    events = db_session.execute(select(EventModel)).scalars().all()
    assert len(events) == 1


# ---------------------------------------------------------------------------
# 5. Admin API Endpoints for Hardening Features
# ---------------------------------------------------------------------------


def test_admin_api_endpoints_hardening(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        headers = {"X-Admin-Key": "dev-admin-ledger-secret-key"}

        # Propose and approve a source
        item = SourceRegistryService.propose_source(
            session=db_session,
            source_name="Sky Sports",
            feed_url="https://www.skysports.com/rss/football",
            language="en",
        )
        SourceRegistryService.run_technical_review(session=db_session, registry_id=item.id)
        SourceRegistryService.run_rights_review(session=db_session, registry_id=item.id, rights_notes="Verified public feed terms")
        SourceRegistryService.approve_source(session=db_session, registry_id=item.id)
        db_session.commit()

        # 1. Pause source
        resp_pause = client.post(f"/api/v1/admin/sources/{item.id}/pause", json={"reason": "Test pause"}, headers=headers)
        assert resp_pause.status_code == 200
        assert resp_pause.json()["status"] == "paused"

        # 2. Resume source
        resp_resume = client.post(f"/api/v1/admin/sources/{item.id}/resume", headers=headers)
        assert resp_resume.status_code == 200
        assert resp_resume.json()["status"] == "resumed"

        # 3. Block source
        resp_block = client.post(f"/api/v1/admin/sources/{item.id}/block", json={"reason": "Persistent terms breach"}, headers=headers)
        assert resp_block.status_code == 200
        assert resp_block.json()["status"] == "blocked"

        # 4. Dead letter listing & replay via Admin API
        dlj = DeadLetterJobModel(
            id="dlj-admin-test-1",
            job_id="job-flaky-99",
            lane="feed_poller",
            payload=json.dumps({"source": "flaky"}),
            attempts=3,
            error_message="Connection reset by peer",
            last_failed_at=datetime.now(timezone.utc),
            replayed=False,
        )
        db_session.add(dlj)
        db_session.commit()

        resp_dl = client.get("/api/v1/admin/dead-letters", headers=headers)
        assert resp_dl.status_code == 200
        assert len(resp_dl.json()) >= 1
        assert resp_dl.json()[0]["job_id"] == "job-flaky-99"

        resp_replay = client.post(f"/api/v1/admin/dead-letters/{dlj.id}/replay", headers=headers)
        assert resp_replay.status_code == 200
        assert resp_replay.json()["status"] == "replayed"

        # 5. Quarantine pool listing via Admin API
        qdoc = QuarantinedDocumentModel(
            id="qdoc-admin-test-1",
            source_name="Spam Outlet",
            source_url="https://spam.org/123",
            raw_payload="{}",
            rejection_reason="Confidence 0.12 < 0.50",
            confidence_score=0.12,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(qdoc)
        db_session.commit()

        resp_q = client.get("/api/v1/admin/quarantine", headers=headers)
        assert resp_q.status_code == 200
        assert len(resp_q.json()) >= 1
        assert resp_q.json()[0]["source_name"] == "Spam Outlet"
    finally:
        app.dependency_overrides.clear()
