from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from packages.database.models import Base, ClaimModel, ReporterModel, SourceModel
from workers.pipeline.speed_lane import SpeedLaneWorker


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_known_reporter_alias_resolution(db_session):
    """Verifies that alias variants of known reporters resolve to canonical ID."""
    worker = SpeedLaneWorker(session=db_session)
    payload = {
        "outlet": "Sky Sports",
        "author": "Fabrizio Romano, Correspondent",
        "source_url": "https://skysports.example/transfer-osei-update",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Arsenal make breakthrough in Emeka Osei discussions",
        "body": "Arsenal are advancing in discussions with Sporting CP for Emeka Osei.",
        "language": "en",
    }

    res = worker.process_raw_article(payload)

    assert res["action"] == "claim_created"
    assert res["reporter"] == "Fabrizio Romano"
    assert res["reporter_id"] == "rep-fabrizio-romano"
    assert res["attribution_type"] == "first_party"

    # Verify claim stored in ledger with canonical reporter
    claim = db_session.execute(select(ClaimModel).where(ClaimModel.id == res["claim_id"])).scalar_one()
    assert claim.reporter == "Fabrizio Romano"
    assert claim.reporter_id == "rep-fabrizio-romano"
    assert claim.attribution_type == "first_party"


def test_new_reporter_auto_creation_in_approved_source(db_session):
    """Verifies auto-creation of a genuinely new reporter from an approved source with 0 claims."""
    worker = SpeedLaneWorker(session=db_session)
    payload = {
        "outlet": "The Athletic",
        "author": "Kofi Mensah",
        "source_url": "https://theathletic.example/mensah-exclusive-osei",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Exclusive: Arsenal open talks for Emeka Osei",
        "body": "Arsenal can exclusively reveal talks have begun with Sporting CP for Emeka Osei.",
        "language": "en",
    }

    res = worker.process_raw_article(payload)

    assert res["action"] == "claim_created"
    assert res["reporter"] == "Kofi Mensah"
    assert res["reporter_id"] == "rep-kofi-mensah"

    # Verify reporter entity in database
    reporter = db_session.execute(select(ReporterModel).where(ReporterModel.id == "rep-kofi-mensah")).scalar_one()
    assert reporter.name == "Kofi Mensah"
    assert reporter.slug == "kofi-mensah"

    # Verify corresponding source record for reliability scoring
    source = db_session.execute(select(SourceModel).where(SourceModel.name == "Kofi Mensah")).scalar_one()
    assert source.source_type == "reporter"
    assert source.sample_size == 1  # 1 recorded claim
    assert source.correct_count == 0  # 0 resolved claims yet
    assert source.wilson_lower_bound is None  # Insufficient record state strictly enforced


def test_repetition_vs_original_attribution(db_session):
    """Verifies detection of secondary repetition versus original reporting."""
    worker = SpeedLaneWorker(session=db_session)

    # First report: original scoop from The Athletic
    payload_original = {
        "outlet": "The Athletic",
        "author": "David Ornstein",
        "source_url": "https://theathletic.example/ornstein-osei-bid",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Arsenal submit official bid for Emeka Osei",
        "body": "Arsenal have submitted an opening bid to Sporting CP for Emeka Osei, our sources understand.",
        "language": "en",
    }
    res_orig = worker.process_raw_article(payload_original)
    assert res_orig["attribution_type"] == "first_party"

    # Second report: repetition citing The Athletic
    payload_repetition = {
        "outlet": "Sky Sports",
        "author": "News Desk",
        "source_url": "https://skysports.example/arsenal-osei-rep",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Arsenal bid for Sporting striker Emeka Osei, according to The Athletic",
        "body": "Sporting CP forward Emeka Osei is the subject of a bid from Arsenal, reported by The Athletic.",
        "language": "en",
    }
    res_rep = worker.process_raw_article(payload_repetition)
    assert res_rep["attribution_type"] == "secondary"

    # Third report: wire syndication credit line
    payload_wire = {
        "outlet": "The Woodwork",
        "source_url": "https://thewoodwork.example/wire-osei",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Arsenal in discussions for Emeka Osei with Sporting CP",
        "body": "Talks continue between Arsenal and Sporting CP for striker Emeka Osei.\nSource: Sky Sports",
        "language": "en",
    }
    res_wire = worker.process_raw_article(payload_wire)
    assert res_wire["attribution_type"] == "secondary"


def test_outlet_with_no_byline(db_session):
    """Verifies that an outlet reporting without a byline safely leaves reporter as None."""
    worker = SpeedLaneWorker(session=db_session)
    payload = {
        "outlet": "BBC Sport",
        "author": None,
        "source_url": "https://bbcsport.example/football/osei-talks",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Arsenal in contact with Sporting CP over Emeka Osei",
        "body": "Arsenal have established formal contact with Sporting CP for striker Emeka Osei.",
        "language": "en",
    }

    res = worker.process_raw_article(payload)

    assert res["action"] == "claim_created"
    assert res["reporter"] is None
    assert res["reporter_id"] is None

    claim = db_session.execute(select(ClaimModel).where(ClaimModel.id == res["claim_id"])).scalar_one()
    assert claim.reporter is None
    assert claim.reporter_id is None


def test_generic_byline_filtered_out(db_session):
    """Verifies that generic outlet tokens like 'Staff' or 'Editorial' are not treated as reporters."""
    worker = SpeedLaneWorker(session=db_session)
    payload = {
        "outlet": "The Athletic",
        "author": "The Athletic Staff",
        "source_url": "https://theathletic.example/staff-roundup-osei",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Transfer notebook: Latest on Arsenal and Emeka Osei",
        "body": "A roundup of transfer activity concerning Arsenal and Sporting CP forward Emeka Osei.",
        "language": "en",
    }

    res = worker.process_raw_article(payload)

    assert res["reporter"] is None
    assert res["reporter_id"] is None


def test_byline_extracted_from_body_text(db_session):
    """Verifies extraction of author from body text when author field is omitted."""
    worker = SpeedLaneWorker(session=db_session)
    payload = {
        "outlet": "The Daily Telegraph",
        "author": None,
        "source_url": "https://telegraph.example/ducker-osei-report",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Arsenal step up pursuit of Sporting striker Emeka Osei",
        "body": "By James Ducker, Northern Football Correspondent\nArsenal are intensifying their pursuit of Emeka Osei.",
        "language": "en",
    }

    res = worker.process_raw_article(payload)

    assert res["reporter"] == "James Ducker"
    assert res["reporter_id"] == "rep-james-ducker"
