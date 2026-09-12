from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from packages.database.models import Base
from packages.database.session import get_db

# Create in-memory test database with StaticPool so all connections share the same database
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


@pytest.fixture(autouse=True)
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    app.dependency_overrides.clear()


def test_vertical_slice_end_to_end_flow():
    # 1. Ingest a raw transfer rumour from an adapter
    payload = {
        "outlet": "The Woodwork",
        "author": "Tom Whitcombe",
        "source_url": "https://thewoodwork.example/football/osei-talks-live",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Arsenal open discussions for Emeka Osei with Sporting CP",
        "body": "Arsenal have opened discussions with Sporting CP regarding a deal for Emeka Osei with €64m fee cited.",
        "language": "en",
    }

    ingest_resp = client.post("/api/v1/ingest/claim", json=payload)
    assert ingest_resp.status_code == 200
    ingest_data = ingest_resp.json()

    event_id = ingest_data["event_id"]
    claim_id = ingest_data["claim_id"]
    assert event_id.startswith("e-")
    assert claim_id.startswith("c-")
    assert ingest_data["event_status"] == "rumour"
    assert len(ingest_data["evidence_bullets"]) > 0

    # 2. Query the public events feed
    feed_resp = client.get("/api/v1/events")
    assert feed_resp.status_code == 200
    events = feed_resp.json()
    assert len(events) >= 1

    event = next(e for e in events if e["id"] == event_id)
    assert event["headline"] == payload["headline"]
    assert event["status"] == "rumour"
    assert event["source_url"] == payload["source_url"]

    entity_names = {ent["name"] for ent in event["entities"]}
    assert "Arsenal" in entity_names
    assert "Sporting CP" in entity_names
    assert "Emeka Osei" in entity_names

    # 3. Query the detailed event endpoint with evidence rationale
    detail_resp = client.get(f"/api/v1/events/{event_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["evidence_rationale"]) > 0

    # 4. Query claims timeline for the event
    claims_resp = client.get(f"/api/v1/claims/by-event/{event_id}")
    assert claims_resp.status_code == 200
    claims = claims_resp.json()
    assert len(claims) == 1
    assert claims[0]["outlet"] == "The Woodwork"
    assert claims[0]["reporter"] == "Tom Whitcombe"
    assert claims[0]["url"] == payload["source_url"]

    # 5. Query reliability scorecard for the outlet
    rel_resp = client.get("/api/v1/reliability/the-woodwork")
    assert rel_resp.status_code == 200
    rel = rel_resp.json()
    assert rel["subject_name"] == "The Woodwork"
    assert rel["sample_size"] == 1
    assert rel["is_insufficient_record"] is True
