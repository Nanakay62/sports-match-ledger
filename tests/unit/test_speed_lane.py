from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.database.models import Base
from workers.pipeline.adapters.rss_adapter import ProvenanceError
from workers.pipeline.speed_lane import SpeedLaneWorker


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_speed_lane_processes_valid_rumour(db_session):
    worker = SpeedLaneWorker(session=db_session)
    payload = {
        "outlet": "The Woodwork",
        "author": "Tom Whitcombe",
        "source_url": "https://thewoodwork.example/osei-talks",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Arsenal open talks for Emeka Osei with Sporting Lisbon",
        "body": "Arsenal have approached Sporting CP regarding a potential transfer for Emeka Osei.",
        "language": "en",
    }

    res = worker.process_raw_article(payload)

    assert res["lane"] == "speed_lane"
    assert "Arsenal" in res["entities"]
    assert "Sporting CP" in res["entities"]
    assert "Emeka Osei" in res["entities"]
    assert res["status"] == "rumour"
    assert res["latency_ms"] < 1000.0  # Speed lane SLA check


def test_speed_lane_rejects_missing_provenance(db_session):
    worker = SpeedLaneWorker(session=db_session)
    # Missing source_url
    bad_payload = {
        "outlet": "The Woodwork",
        "headline": "Unattributed rumour without source URL",
        "body": "Unverified claim without original link.",
        "published_at": datetime.now(timezone.utc).isoformat(),
    }

    with pytest.raises(ProvenanceError):
        worker.process_raw_article(bad_payload)
