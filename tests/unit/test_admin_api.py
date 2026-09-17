import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from packages.database.models import (
    Base,
    ClaimModel,
    DeadLetterJobModel,
    EventModel,
    PipelineJobModel,
    SourceModel,
)
from packages.database.registry import SourceRegistryService
from packages.database.session import get_db

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=test_engine)
TestSession = sessionmaker(bind=test_engine)


def override_get_db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


client = TestClient(app)
ADMIN_HEADERS = {"X-Admin-Key": "dev-admin-ledger-secret-key"}


@pytest.fixture(autouse=True)
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    app.dependency_overrides.clear()


def test_admin_endpoints_require_auth():
    """Verify that unauthenticated requests without X-Admin-Key are rejected."""
    resp = client.get("/api/v1/admin/overview")
    assert resp.status_code == 401
    assert "X-Admin-Key" in resp.json()["detail"]


def test_admin_overview_stats():
    resp = client.get("/api/v1/admin/overview", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_events" in data
    assert "total_claims" in data
    assert "pending_source_reviews" in data
    assert "total_inference_spend_eur" in data


def test_admin_review_queue_and_resolve():
    with TestSession() as session:
        src = SourceModel(id="src-test", name="Test Outlet", source_type="outlet", sample_size=1, correct_count=1)
        ev = EventModel(
            id="e-flagged-01",
            headline="Player set to join Rival FC",
            status="disputed",
            independent_sources=1,
            sport="Football",
            competition="Premier League",
            summary="Disputed transfer claim.",
            source_url="https://example.com",
        )
        cl = ClaimModel(
            id="c-flagged-01",
            event_id="e-flagged-01",
            source_id="src-test",
            claim_text="Player has signed preliminary terms.",
            attribution="first_party",
            original_url="https://example.com",
        )
        session.add_all([src, ev, cl])
        session.commit()

    # Query review queue
    q_resp = client.get("/api/v1/admin/review-queue", headers=ADMIN_HEADERS)
    assert q_resp.status_code == 200
    queue = q_resp.json()
    assert len(queue) >= 1
    assert queue[0]["event_id"] == "e-flagged-01"

    # Action: confirm
    action_resp = client.post(
        "/api/v1/admin/review-queue/c-flagged-01/resolve",
        headers=ADMIN_HEADERS,
        json={"action": "confirm", "notes": "Official press release confirmed deal."},
    )
    assert action_resp.status_code == 200
    assert action_resp.json()["new_event_status"] == "confirmed"


def test_admin_source_workflow_advance():
    with TestSession() as session:
        SourceRegistryService.propose_source(
            session=session,
            source_name="Newspaper Test",
            feed_url="https://example.com/rss",
            language="en",
        )
        session.commit()

    resp = client.post("/api/v1/admin/sources/reg-newspaper-test/advance", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "technical_review"


def test_admin_cost_telemetry():
    resp = client.get("/api/v1/admin/costs", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "inference_pool_spend_eur" in data
    assert "cost_per_thousand_events_eur" in data
    assert "rung_breakdown" in data
    assert "L0_Deterministic" in data["rung_breakdown"]


def test_admin_entities_and_alias():
    resp = client.get("/api/v1/admin/entities", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    entities = resp.json()
    assert len(entities) > 0

    target = entities[0]
    add_resp = client.post(
        "/api/v1/admin/entities/alias",
        headers=ADMIN_HEADERS,
        json={"entity_id": target["id"], "alias": "Custom Test Nickname"},
    )
    assert add_resp.status_code == 200
    assert "Custom Test Nickname" in add_resp.json()["aliases"]


def test_claims_corrections_endpoint():
    with TestSession() as session:
        src = SourceModel(id="src-corr", name="Corr Outlet", source_type="outlet", sample_size=1, correct_count=0)
        ev = EventModel(
            id="e-corr-01",
            headline="False claim was corrected",
            status="corrected",
            independent_sources=1,
            sport="Football",
            competition="La Liga",
            summary="Original story retracted after official denial.",
            source_url="https://example.com/corr",
        )
        cl = ClaimModel(
            id="c-corr-01",
            event_id="e-corr-01",
            source_id="src-corr",
            claim_text="Reported fee was incorrect.",
            attribution="first_party",
            original_url="https://example.com/corr",
            is_superseded=True,
        )
        session.add_all([src, ev, cl])
        session.commit()

    resp = client.get("/api/v1/claims/corrections")
    assert resp.status_code == 200
    corrections = resp.json()
    assert len(corrections) >= 1
    assert corrections[0]["claim"]["id"] == "c-corr-01"


def test_admin_quarantine_and_dead_letters():
    from packages.database.models import DeadLetterJobModel, QuarantinedDocumentModel

    with TestSession() as session:
        session.add(
            QuarantinedDocumentModel(
                id="quar-test-01",
                source_name="Test Unreliable Wire",
                source_url="https://example.com/quar",
                raw_payload='{"text": "paywall"}',
                rejection_reason="Truncated payload",
                confidence_score=0.25,
            )
        )
        session.add(
            DeadLetterJobModel(
                id="dl-test-01",
                job_id="job-999",
                lane="speed",
                payload='{"action": "test"}',
                attempts=3,
                error_message="Connection timed out",
                replayed=False,
            )
        )
        session.commit()

    # Overview includes resilience counts
    ov_resp = client.get("/api/v1/admin/overview", headers=ADMIN_HEADERS)
    assert ov_resp.status_code == 200
    ov_data = ov_resp.json()
    assert ov_data["quarantined_documents"] >= 1
    assert ov_data["dead_letter_jobs"] >= 1

    # Quarantine endpoint
    q_resp = client.get("/api/v1/admin/quarantine", headers=ADMIN_HEADERS)
    assert q_resp.status_code == 200
    assert len(q_resp.json()) >= 1
    assert q_resp.json()[0]["id"] == "quar-test-01"

    # Dead letters endpoint
    dl_resp = client.get("/api/v1/admin/dead-letters", headers=ADMIN_HEADERS)
    assert dl_resp.status_code == 200
    assert len(dl_resp.json()) >= 1
    assert dl_resp.json()[0]["id"] == "dl-test-01"


def test_admin_clusters_list_and_detail():
    with TestSession() as session:
        src = SourceModel(id="src-cluster-test", name="Sky Sports", source_type="outlet")
        ev1 = EventModel(
            id="e-cluster-01",
            headline="Arsenal submit bid for Emeka Osei",
            status="Disputed",
            sport="Football",
            competition="Premier League",
            summary="Arsenal bid reported.",
            source_url="https://example.com/ev1",
            disputed_by_event_id="e-cluster-02",
            dispute_status="active",
        )
        ev2 = EventModel(
            id="e-cluster-02",
            headline="Arsenal deny move for Emeka Osei",
            status="Disputed",
            sport="Football",
            competition="Premier League",
            summary="Arsenal denial reported.",
            source_url="https://example.com/ev2",
            disputed_by_event_id="e-cluster-01",
            dispute_status="active",
        )
        cl1 = ClaimModel(
            id="c-cluster-01",
            event_id="e-cluster-01",
            source_id="src-cluster-test",
            claim_text="Arsenal submit formal bid.",
            predicate="submits_bid",
            subject_id="ent-club-arsenal",
            object_id="ent-player-emeka-osei",
            evidence_span="Arsenal submit formal bid",
            attribution="first_party",
            original_url="https://example.com/cl1",
        )
        session.add_all([src, ev1, ev2, cl1])
        session.commit()

    # List clusters
    clusters_resp = client.get("/api/v1/admin/clusters", headers=ADMIN_HEADERS)
    assert clusters_resp.status_code == 200
    clusters = clusters_resp.json()
    assert len(clusters) >= 2
    ev1_summary = next(c for c in clusters if c["event_id"] == "e-cluster-01")
    assert ev1_summary["status"] == "Disputed"
    assert ev1_summary["dispute_status"] == "active"
    assert ev1_summary["disputed_by_event_id"] == "e-cluster-02"
    assert ev1_summary["claims_count"] == 1

    # Get cluster detail
    detail_resp = client.get("/api/v1/admin/clusters/e-cluster-01", headers=ADMIN_HEADERS)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["event_id"] == "e-cluster-01"
    assert detail["dispute_target"]["event_id"] == "e-cluster-02"
    assert len(detail["claims"]) == 1
    assert detail["claims"][0]["predicate"] == "submits_bid"

    # Non-existent cluster
    resp_404 = client.get("/api/v1/admin/clusters/non-existent-id", headers=ADMIN_HEADERS)
    assert resp_404.status_code == 404


def test_admin_queue_stats():
    with TestSession() as session:
        j1 = PipelineJobModel(
            id="job-test-1",
            lane="speed_lane",
            status="pending",
            payload="{}",
        )
        j2 = PipelineJobModel(
            id="job-test-2",
            lane="evidence_lane",
            status="completed",
            payload="{}",
        )
        dl = DeadLetterJobModel(
            id="dl-test-1",
            job_id="job-orig-1",
            lane="speed_lane",
            payload="{}",
            attempts=3,
            error_message="Feed timeout",
        )
        session.add_all([j1, j2, dl])
        session.commit()

    resp = client.get("/api/v1/admin/queue/stats", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_jobs"] == 2
    assert data["pending_jobs"] == 1
    assert data["completed_jobs"] == 1
    assert data["dead_letter_jobs"] == 1
    assert data["backlog_by_job_type"].get("speed_lane") == 1
    assert data["sla_10min_breached"] is False
    assert "timestamp" in data
