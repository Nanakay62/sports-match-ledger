from fastapi.testclient import TestClient

from apps.api.app.main import app

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


def test_get_reliability_subject_profile():
    response = client.get("/api/v1/reliability/bbc-sport")
    assert response.status_code == 200
    data = response.json()
    assert data["subject_name"] == "BBC Sport"
    assert data["subject_type"] == "outlet"
    assert "total_claims" in data


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
