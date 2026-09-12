import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from packages.database.models import Base, ClaimModel, EventModel, SourceModel
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
