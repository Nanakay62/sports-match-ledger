import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from packages.database.billing_repository import BillingRepository
from packages.database.models import Base, ClaimModel, EventModel, SourceModel
from packages.database.session import get_db

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine)

client = TestClient(app)
ADMIN_HEADERS = {"X-Admin-Key": "dev-admin-ledger-secret-key"}


def override_get_db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    app.dependency_overrides.clear()


def _seed_event_and_claim(session, event_id="evt-export-1", source_id="src-export-1"):
    src = SourceModel(id=source_id, name="Export Outlet", source_type="outlet")
    ev = EventModel(
        id=event_id,
        headline="Star forward set for medical",
        status="developing",
        independent_sources=1,
        sport="Football",
        competition="Premier League",
        summary="Developing transfer story.",
        source_url="https://example.com",
    )
    cl = ClaimModel(
        id=f"{event_id}-clm-1",
        event_id=event_id,
        source_id=source_id,
        claim_text="The forward is reportedly close to a move.",
        attribution="first_party",
        original_url="https://example.com/story",
        reporter="Jane Reporter",
    )
    session.add_all([src, ev, cl])
    session.commit()


# --- Paywall event tracking ---------------------------------------------------


def test_paywall_event_rejects_unknown_wall_id():
    resp = client.post("/api/v1/billing/paywall-events", json={"wall_id": "made_up", "action": "shown"})
    assert resp.status_code == 400


def test_paywall_event_rejects_unknown_action():
    resp = client.post("/api/v1/billing/paywall-events", json={"wall_id": "export", "action": "purchased"})
    assert resp.status_code == 400


def test_paywall_event_records_shown_and_clicked():
    resp1 = client.post("/api/v1/billing/paywall-events", json={"wall_id": "export", "action": "shown", "context": "evt-1"})
    assert resp1.status_code == 200
    assert resp1.json()["recorded"] is True

    resp2 = client.post("/api/v1/billing/paywall-events", json={"wall_id": "export", "action": "clicked", "context": "evt-1"})
    assert resp2.status_code == 200


def test_admin_paywall_conversion_requires_auth():
    resp = client.get("/api/v1/admin/paywall-conversion")
    assert resp.status_code == 401


def test_admin_paywall_conversion_summary_per_wall():
    # 3 impressions, 1 click on "archive_depth"; 1 impression, 1 click on "export"
    for _ in range(3):
        client.post("/api/v1/billing/paywall-events", json={"wall_id": "archive_depth", "action": "shown"})
    client.post("/api/v1/billing/paywall-events", json={"wall_id": "archive_depth", "action": "clicked"})
    client.post("/api/v1/billing/paywall-events", json={"wall_id": "export", "action": "shown"})
    client.post("/api/v1/billing/paywall-events", json={"wall_id": "export", "action": "clicked"})

    resp = client.get("/api/v1/admin/paywall-conversion", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    rows = {r["wall_id"]: r for r in resp.json()}

    assert rows["archive_depth"]["shown"] == 3
    assert rows["archive_depth"]["clicked"] == 1
    assert rows["archive_depth"]["conversion_rate"] == pytest.approx(1 / 3, rel=1e-3)

    assert rows["export"]["shown"] == 1
    assert rows["export"]["clicked"] == 1
    assert rows["export"]["conversion_rate"] == 1.0


# --- Claim ledger export -------------------------------------------------------


def test_export_requires_event_id_or_subject_slug():
    resp = client.get("/api/v1/claims/export", params={"email": "someone@example.com"})
    assert resp.status_code == 400


def test_export_rejects_free_tier_email():
    with TestSession() as session:
        _seed_event_and_claim(session)

    resp = client.get("/api/v1/claims/export", params={"email": "free-user@example.com", "event_id": "evt-export-1"})
    assert resp.status_code == 403
    assert "Pro feature" in resp.json()["detail"]


def test_export_allows_pro_email_and_returns_csv():
    with TestSession() as session:
        _seed_event_and_claim(session)
        BillingRepository.upsert_entitlement(session, email="pro-user@example.com", status="active", is_pro=True)

    resp = client.get(
        "/api/v1/claims/export",
        params={"email": "pro-user@example.com", "event_id": "evt-export-1", "format": "csv"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers["content-disposition"]
    body = resp.text
    assert "Export Outlet" in body
    assert "The forward is reportedly close to a move." in body


def test_export_allows_pro_email_and_returns_json():
    with TestSession() as session:
        _seed_event_and_claim(session)
        BillingRepository.upsert_entitlement(session, email="pro-user2@example.com", status="active", is_pro=True)

    resp = client.get(
        "/api/v1/claims/export",
        params={"email": "pro-user2@example.com", "event_id": "evt-export-1", "format": "json"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["outlet"] == "Export Outlet"


def test_export_by_subject_slug():
    with TestSession() as session:
        _seed_event_and_claim(session, event_id="evt-export-2", source_id="src-export-2")
        BillingRepository.upsert_entitlement(session, email="pro-user3@example.com", status="active", is_pro=True)

    resp = client.get(
        "/api/v1/claims/export",
        params={"email": "pro-user3@example.com", "subject_slug": "export-outlet", "format": "json"},
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) >= 1
