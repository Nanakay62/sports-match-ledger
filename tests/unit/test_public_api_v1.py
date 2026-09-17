from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from packages.database.models import Base, ClaimModel, EventModel, SourceModel
from packages.database.repository import LedgerRepository
from packages.database.session import get_db

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=test_engine)
    LedgerRepository.init_db(test_engine)

    with TestingSessionLocal() as db:
        # Seed test source
        src = SourceModel(
            id="src-bbc-sport",
            name="BBC Sport",
            source_type="outlet",
            sample_size=20,
            correct_count=18,
            wilson_lower_bound=0.72,
        )
        db.add(src)

        # Seed test event
        ev = EventModel(
            id="ev-mbappe-madrid",
            headline="Mbappé completes transfer to Real Madrid",
            summary="Real Madrid officially confirm the signing of Kylian Mbappé on a five-year contract.",
            status="Confirmed",
            sport="Football",
            competition="La Liga",
            source_url="https://bbc.com/sport/football/123",
            first_reported_outlet="BBC Sport",
        )
        db.add(ev)

        # Seed test claims
        c1 = ClaimModel(
            id="cl-mbappe-1",
            event_id="ev-mbappe-madrid",
            source_id="src-bbc-sport",
            reporter="David Ornstein",
            claim_text="Real Madrid reach agreement with Kylian Mbappé",
            subject_id="ent-player-mbappe",
            predicate="official_signing",
            object_id="ent-club-real-madrid",
            evidence_span="Real Madrid reach agreement with Kylian Mbappé",
            resolvable=True,
            resolution_class="binary",
            schema_version="5.2.0",
            attribution="original",
            attribution_type="first_party",
            language="en",
            original_url="https://bbc.com/sport/football/123",
            timestamp=datetime.now(timezone.utc),
        )
        db.add(c1)
        db.commit()

    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_public_claims_endpoint(client):
    # Query all claims
    resp = client.get("/api/v1/claims")
    assert resp.status_code == 200
    claims = resp.json()
    assert len(claims) >= 1
    assert claims[0]["id"] == "cl-mbappe-1"
    assert claims[0]["subject_id"] == "ent-player-mbappe"
    assert claims[0]["predicate"] == "official_signing"

    # Filter by predicate
    resp_pred = client.get("/api/v1/claims?predicate=official_signing")
    assert resp_pred.status_code == 200
    assert len(resp_pred.json()) == 1

    # Filter by non-matching predicate
    resp_empty = client.get("/api/v1/claims?predicate=transfer_denied")
    assert resp_empty.status_code == 200
    assert len(resp_empty.json()) == 0


def test_entities_search_and_lookup(client):
    # Search entity by name
    resp = client.get("/api/v1/entities/search?q=Arsenal")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["id"] == "ent-club-arsenal"

    # Search entity by alias
    resp_alias = client.get("/api/v1/entities/search?q=Gunners")
    assert resp_alias.status_code == 200
    assert any(e["id"] == "ent-club-arsenal" for e in resp_alias.json())

    # Filter by type
    resp_club = client.get("/api/v1/entities/search?q=Sporting&type=club")
    assert resp_club.status_code == 200
    assert len(resp_club.json()) >= 1
    assert resp_club.json()[0]["type"] == "club"

    # Get by entity ID
    resp_id = client.get("/api/v1/entities/ent-club-arsenal")
    assert resp_id.status_code == 200
    assert resp_id.json()["name"] == "Arsenal"

    # Not found entity ID
    resp_404 = client.get("/api/v1/entities/ent-unknown-999")
    assert resp_404.status_code == 404


def test_reliability_by_id_endpoints(client):
    # Lookup source reliability by canonical ID
    resp_src = client.get("/api/v1/reliability/sources/src-bbc-sport")
    assert resp_src.status_code == 200
    data = resp_src.json()
    assert data["subject_name"] == "BBC Sport"
    assert data["sample_size"] == 20
    assert data["wilson_lower_bound"] == pytest.approx(0.699, abs=0.01)


def test_api_key_scoping_and_tiers(client):
    # Unauthenticated caller -> Anonymous tier allowed
    resp_anon = client.get("/api/v1/claims")
    assert resp_anon.status_code == 200

    # Developer key
    resp_dev = client.get("/api/v1/claims", headers={"X-API-Key": "dev_test_key_123"})
    assert resp_dev.status_code == 200

    # Commercial key prefix
    resp_pro = client.get("/api/v1/claims", headers={"X-API-Key": "sk_pro_live_token_777"})
    assert resp_pro.status_code == 200

    # Invalid key -> 401 Unauthorized
    resp_invalid = client.get("/api/v1/claims", headers={"X-API-Key": "invalid_bogus_key"})
    assert resp_invalid.status_code == 401
    assert "Invalid API key" in resp_invalid.json()["detail"]
