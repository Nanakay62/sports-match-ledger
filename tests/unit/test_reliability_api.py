from fastapi.testclient import TestClient

from apps.api.app.main import app
from packages.database.repository import LedgerRepository
from packages.database.session import engine

LedgerRepository.init_db(engine)
client = TestClient(app)


def test_get_reliability_directory():
    response = client.get("/api/v1/reliability")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Verify structure
    first = data[0]
    assert "subject_name" in first
    assert "slug" in first
    assert "subject_type" in first
    assert "sample_size" in first
    assert "correct_count" in first
    assert "total_claims" in first
    assert "original_reporting" in first
    assert "aggregation_repetition" in first
    assert "sample_size" in first["original_reporting"]
    assert "sample_size" in first["aggregation_repetition"]


def test_get_reliability_subject_profile():
    response = client.get("/api/v1/reliability/bbc-sport")
    assert response.status_code == 200
    data = response.json()
    assert data["subject_name"] == "BBC Sport"
    assert data["subject_type"] == "outlet"
    assert "total_claims" in data
    assert "original_reporting" in data
    assert "aggregation_repetition" in data
    assert "component_accuracy" in data
    assert "entity_accuracy" in data["component_accuracy"]
    assert "direction_accuracy" in data["component_accuracy"]
    assert "timing_accuracy" in data["component_accuracy"]
    assert "fee_accuracy" in data["component_accuracy"]


def test_get_claims_by_source():
    response = client.get("/api/v1/claims/by-source/bbc-sport")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        item = data[0]
        assert "claim" in item
        assert "event" in item
        assert item["claim"]["outlet"] == "BBC Sport"
