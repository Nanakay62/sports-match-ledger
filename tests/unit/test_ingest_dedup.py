import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from packages.database.models import Base, ClaimEvidenceModel, ClaimModel
from packages.database.session import get_db

# Isolated in-memory SQLite database for dedup test suite
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(bind=engine)


def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()


def test_exact_duplicate_resubmission():
    """Exact duplicate submission with identical URL and timestamp returns HTTP 200 idempotently."""
    payload = {
        "outlet": "The Athletic",
        "author": "David Ornstein",
        "source_url": "https://theathletic.example/football/osei-scoop",
        "published_at": "2026-06-01T12:00:00Z",
        "headline": "Arsenal agree terms for Emeka Osei",
        "body": "Arsenal have agreed personal terms with Sporting CP winger Emeka Osei ahead of a proposed summer transfer.",
        "language": "en",
    }

    # First submission: created as new claim
    resp1 = client.post("/api/v1/ingest/claim", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "success"
    claim_id_1 = data1["claim_id"]
    event_id_1 = data1["event_id"]

    # Second submission: exact resubmission should return 200 with already_recorded status
    resp2 = client.post("/api/v1/ingest/claim", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "already_recorded"
    assert data2["claim_id"] == claim_id_1
    assert data2["event_id"] == event_id_1

    # Verify database state: claims table has not duplicated
    session = TestingSessionLocal()
    try:
        claims = session.query(ClaimModel).filter(ClaimModel.original_url == payload["source_url"]).all()
        assert len(claims) == 1
    finally:
        session.close()


def test_near_duplicate_via_syndication():
    """Syndicated wire copy from another outlet with different URL is attached as supporting evidence."""
    # Outlet A: original exclusive report
    original_payload = {
        "outlet": "The Athletic",
        "author": "David Ornstein",
        "source_url": "https://theathletic.example/football/exclusive-osei-deal",
        "published_at": "2026-06-02T10:00:00Z",
        "headline": "Arsenal reach agreement for Sporting winger Emeka Osei",
        "body": "Arsenal have reached full agreement with Sporting CP for the transfer of winger Emeka Osei with a £64m fee structure in place.",
        "language": "en",
    }

    resp1 = client.post("/api/v1/ingest/claim", json=original_payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    root_claim_id = data1["claim_id"]
    event_id = data1["event_id"]

    # Outlet B: syndicated wire pickup copying the report text under a different URL and new outlet
    syndicated_payload = {
        "outlet": "Sky Sports",
        "author": "Kaveh Solhekol",
        "source_url": "https://skysports.example/news/syndicated-osei-deal",
        "published_at": "2026-06-02T11:15:00Z",
        "headline": "Arsenal reach agreement for Sporting winger Emeka Osei",
        "body": "Arsenal have reached full agreement with Sporting CP for the transfer of winger Emeka Osei with a £64m fee structure in place.",
        "language": "en",
    }

    resp2 = client.post("/api/v1/ingest/claim", json=syndicated_payload)
    assert resp2.status_code == 200
    data2 = resp2.json()

    # Must attach to existing claim, NOT create a second claim row
    assert data2["status"] == "evidence_attached"
    assert data2["claim_id"] == root_claim_id
    assert data2["event_id"] == event_id
    assert data2["similarity_to_root"] == 1.0

    session = TestingSessionLocal()
    try:
        # Claims count under this event must remain 1
        claims = session.query(ClaimModel).filter(ClaimModel.event_id == event_id).all()
        assert len(claims) == 1

        # Supporting evidence count must be 2 (root + syndicated)
        evidence = session.query(ClaimEvidenceModel).filter(ClaimEvidenceModel.claim_id == root_claim_id).all()
        assert len(evidence) == 2
        outlets = {ev.source.name for ev in evidence if ev.source}
        assert "The Athletic" in outlets
        assert "Sky Sports" in outlets
    finally:
        session.close()


def test_near_duplicate_via_edited_timestamp_and_copy():
    """An article republished with an updated timestamp and minor punctuation tweaks is caught as near-duplicate."""
    payload_v1 = {
        "outlet": "The Guardian",
        "author": "Nick Ames",
        "source_url": "https://theguardian.example/sport/mbappe-madrid-talks",
        "published_at": "2026-06-03T08:00:00Z",
        "headline": "Real Madrid in advanced negotiations with Kylian Mbappe",
        "body": "Real Madrid are in advanced negotiations with Kylian Mbappe regarding personal terms ahead of a high-profile summer switch.",
        "language": "en",
    }

    resp1 = client.post("/api/v1/ingest/claim", json=payload_v1)
    assert resp1.status_code == 200
    claim_id_v1 = resp1.json()["claim_id"]
    event_id = resp1.json()["event_id"]

    # Updated version: 2 hours later with minor punctuation edit
    payload_v2 = {
        "outlet": "The Guardian",
        "author": "Nick Ames",
        "source_url": "https://theguardian.example/sport/mbappe-madrid-talks?updated=true",
        "published_at": "2026-06-03T10:30:00Z",
        "headline": "Real Madrid in advanced negotiations with Kylian Mbappe",
        "body": "Real Madrid are in advanced negotiations with Kylian Mbappe regarding personal terms ahead of a high-profile summer switch!",
        "language": "en",
    }

    resp2 = client.post("/api/v1/ingest/claim", json=payload_v2)
    assert resp2.status_code == 200
    data2 = resp2.json()

    assert data2["status"] == "evidence_attached"
    assert data2["claim_id"] == claim_id_v1
    assert data2["event_id"] == event_id
    assert data2["similarity_to_root"] >= 0.85


def test_distinct_events_sharing_two_entities():
    """Two stories sharing entities (Arsenal, Chelsea) but with distinct factual content are separate claims."""
    transfer_story = {
        "outlet": "BBC Sport",
        "author": "Simon Stone",
        "source_url": "https://bbc.example/sport/arsenal-chelsea-transfer-fee",
        "published_at": "2026-06-04T09:00:00Z",
        "headline": "Arsenal agree fee with Chelsea for winger transfer",
        "body": "Arsenal have agreed a £25m fee with Chelsea to complete the permanent signing of the winger on a long term contract.",
        "language": "en",
    }

    match_story = {
        "outlet": "BBC Sport",
        "author": "Phil McNulty",
        "source_url": "https://bbc.example/sport/arsenal-chelsea-derby-draw",
        "published_at": "2026-06-04T15:00:00Z",
        "headline": "Arsenal held to 1-1 draw by Chelsea at Stamford Bridge",
        "body": "Arsenal were held to a 1-1 draw against Chelsea in a dramatic Premier League derby fixture under intense pressure.",
        "language": "en",
    }

    resp1 = client.post("/api/v1/ingest/claim", json=transfer_story)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "success"
    claim_id_1 = data1["claim_id"]

    resp2 = client.post("/api/v1/ingest/claim", json=match_story)
    assert resp2.status_code == 200
    data2 = resp2.json()
    # Story 2 is recognized as a distinct factual assertion, creating its own claim
    assert data2["status"] == "success"
    claim_id_2 = data2["claim_id"]

    assert claim_id_1 != claim_id_2
