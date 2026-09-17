import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from packages.database.models import Base, ClaimModel, EventModel, SourceModel
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


@pytest.fixture(autouse=True)
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    app.dependency_overrides.clear()


def test_public_rss_feed_generation():
    """Verifies that the /events/feed.rss endpoint produces valid RSS 2.0 XML with receipts metadata."""
    with TestSession() as session:
        src = SourceModel(id="src-bbc", name="BBC Sport", source_type="outlet")
        ev1 = EventModel(
            id="e-rss-01",
            headline="Arsenal & Sporting agree terms for Emeka Osei",
            status="confirmed",
            sport="Football",
            competition="Premier League",
            summary="Arsenal have completed terms with Sporting CP for Emeka Osei.",
            source_url="https://example.com/rss1",
            first_reported_outlet="BBC Sport",
            first_reported_lead_minutes=15,
            independent_sources=3,
        )
        cl1 = ClaimModel(
            id="c-rss-01",
            event_id="e-rss-01",
            source_id="src-bbc",
            claim_text="Arsenal agree terms for Emeka Osei.",
            attribution="first_party",
            original_url="https://example.com/rss1",
        )
        session.add_all([src, ev1, cl1])
        session.commit()

    resp = client.get("/api/v1/events/feed.rss")
    assert resp.status_code == 200
    assert "application/rss+xml" in resp.headers["content-type"]

    xml_text = resp.text
    assert '<rss version="2.0"' in xml_text
    assert "<channel>" in xml_text
    assert "Sports News AI · Accountability Ledger" in xml_text

    # Parse with ElementTree to verify syntactical XML correctness
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    assert channel is not None

    items = channel.findall("item")
    assert len(items) >= 1

    item0 = items[0]
    title = item0.find("title")
    assert title is not None and "Arsenal & Sporting agree terms" in title.text

    link = item0.find("link")
    assert link is not None and "e-rss-01" in link.text

    guid = item0.find("guid")
    assert guid is not None and guid.text == "e-rss-01"

    desc = item0.find("description")
    assert desc is not None
    assert "Status: CONFIRMED" in desc.text
    assert "Independent Sources: 3" in desc.text
    assert "First reported by: BBC Sport" in desc.text


def test_rss_feed_handles_empty_events():
    """Verifies that the RSS feed produces a valid empty channel when no events exist."""
    resp = client.get("/api/v1/events/feed.rss")
    assert resp.status_code == 200
    root = ET.fromstring(resp.text)
    channel = root.find("channel")
    assert channel is not None
    items = channel.findall("item")
    assert len(items) == 0
