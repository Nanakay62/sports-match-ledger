from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.database.models import (
    Base,
    ClaimEvidenceModel,
    ClaimModel,
    EventModel,
    SourceModel,
    SourceRegistryModel,
    SourceRegistryStatus,
)
from workers.pipeline.feed_poller import FeedPoller

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>The Athletic Football</title>
    <link>https://theathletic.com</link>
    <item>
      <title>Arsenal agree terms for Emeka Osei</title>
      <link>https://theathletic.com/osei-exclusive-123</link>
      <description>Sporting CP winger Emeka Osei has agreed personal terms with Arsenal ahead of a summer switch.</description>
      <dc:creator>David Ornstein</dc:creator>
      <pubDate>Mon, 09 Sep 2024 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

WIRE_SYNDICATION_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>The Athletic Wire</title>
    <link>https://theathletic.com</link>
    <item>
      <title>Arsenal agree terms for Emeka Osei (Update)</title>
      <link>https://theathletic.com/syndicated-wire-osei-456</link>
      <description>Sporting CP winger Emeka Osei has agreed personal terms with Arsenal ahead of a summer switch.</description>
      <pubDate>Mon, 09 Sep 2024 10:45:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def setup_test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory


def test_feed_poller_creates_claims_and_resolves_reporter():
    session_factory = setup_test_db()
    db = session_factory()

    # Seed approved source in registry
    source_reg = SourceRegistryModel(
        id="reg-the-athletic",
        source_name="The Athletic",
        feed_url="https://theathletic.com/rss",
        feed_format="rss2",
        language="en",
        coverage_category="general",
        authority_rank=3,
        status=SourceRegistryStatus.APPROVED.value,
        polling_interval_minutes=15,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    # Seed primary source in sources table
    source_primary = SourceModel(
        id="src-the-athletic",
        name="The Athletic",
        source_type="outlet",
        sample_size=0,
        correct_count=0,
    )
    db.add_all([source_reg, source_primary])
    db.commit()

    poller = FeedPoller(session_factory=session_factory)
    result = poller.poll_source_by_registry_id(
        registry_id="reg-the-athletic",
        feed_content=SAMPLE_RSS.encode("utf-8"),
        session=db,
    )

    assert result["status"] == "success"
    assert result["items_fetched"] == 1
    assert result["claims_created"] == 1
    assert result["idempotent_noops"] == 0

    # Verify event and claim created
    events = list(db.query(EventModel).all())
    assert len(events) == 1

    claims = list(db.query(ClaimModel).all())
    assert len(claims) == 1
    assert claims[0].reporter == "David Ornstein"
    assert claims[0].reporter_id == "rep-david-ornstein"


def test_feed_poller_idempotency_on_repoll():
    session_factory = setup_test_db()
    db = session_factory()

    source_reg = SourceRegistryModel(
        id="reg-the-athletic",
        source_name="The Athletic",
        feed_url="https://theathletic.com/rss",
        status=SourceRegistryStatus.APPROVED.value,
        polling_interval_minutes=15,
    )
    source_primary = SourceModel(
        id="src-the-athletic",
        name="The Athletic",
        source_type="outlet",
    )
    db.add_all([source_reg, source_primary])
    db.commit()

    poller = FeedPoller(session_factory=session_factory)

    # First poll: creates claim
    res1 = poller.poll_source_by_registry_id(
        registry_id="reg-the-athletic",
        feed_content=SAMPLE_RSS.encode("utf-8"),
        session=db,
    )
    assert res1["claims_created"] == 1

    # Second poll with identical content: should be idempotent no-op
    res2 = poller.poll_source_by_registry_id(
        registry_id="reg-the-athletic",
        feed_content=SAMPLE_RSS.encode("utf-8"),
        session=db,
    )
    assert res2["claims_created"] == 0
    assert res2["idempotent_noops"] == 1

    # Total claims in database remains 1
    claims = list(db.query(ClaimModel).all())
    assert len(claims) == 1


def test_feed_poller_near_duplicate_wire_syndication():
    session_factory = setup_test_db()
    db = session_factory()

    source_reg = SourceRegistryModel(
        id="reg-the-athletic",
        source_name="The Athletic",
        feed_url="https://theathletic.com/rss",
        status=SourceRegistryStatus.APPROVED.value,
        polling_interval_minutes=15,
    )
    source_primary = SourceModel(
        id="src-the-athletic",
        name="The Athletic",
        source_type="outlet",
    )
    db.add_all([source_reg, source_primary])
    db.commit()

    poller = FeedPoller(session_factory=session_factory)

    # First poll original exclusive
    poller.poll_source_by_registry_id(
        registry_id="reg-the-athletic",
        feed_content=SAMPLE_RSS.encode("utf-8"),
        session=db,
    )

    # Second poll wire syndication with same body, different URL/timestamp
    res_wire = poller.poll_source_by_registry_id(
        registry_id="reg-the-athletic",
        feed_content=WIRE_SYNDICATION_RSS.encode("utf-8"),
        session=db,
    )

    assert res_wire["claims_created"] == 0
    assert res_wire["evidence_attached"] == 1

    # Claim count remains 1; evidence count is 2 (root evidence + wire syndication)
    assert db.query(ClaimModel).count() == 1
    assert db.query(ClaimEvidenceModel).count() == 2


def test_unapproved_source_is_skipped():
    session_factory = setup_test_db()
    db = session_factory()

    source_reg = SourceRegistryModel(
        id="reg-unapproved",
        source_name="Unapproved Outlet",
        feed_url="https://unapproved.example/rss",
        status=SourceRegistryStatus.PROPOSED.value,
        polling_interval_minutes=15,
    )
    db.add(source_reg)
    db.commit()

    poller = FeedPoller(session_factory=session_factory)
    result = poller.poll_source_by_registry_id(
        registry_id="reg-unapproved",
        feed_content=SAMPLE_RSS.encode("utf-8"),
        session=db,
    )
    assert result["status"] == "skipped"
    assert "proposed" in result["reason"].lower()
    assert db.query(ClaimModel).count() == 0
