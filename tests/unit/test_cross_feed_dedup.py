import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from packages.database.models import (
    Base,
    ClaimEvidenceModel,
    ClaimModel,
    EventModel,
)
from workers.pipeline.dedup import (
    is_near_duplicate,
    lead_paragraph_similarity,
    strip_boilerplate,
)
from workers.pipeline.speed_lane import SpeedLaneWorker


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_strip_boilerplate_removes_datelines_and_trailers():
    """Verifies that wire datelines, trailing RSS notes, and credits are stripped."""
    raw_text = (
        "LONDON (Reuters) - Arsenal have reached full agreement with Sporting CP for the transfer of "
        "winger Emeka Osei with a structured fee package. Read more on BBC Sport. Photo credit: Reuters"
    )
    cleaned = strip_boilerplate(raw_text)
    assert not cleaned.startswith("LONDON")
    assert "Reuters -" not in cleaned
    assert "Read more on BBC" not in cleaned
    assert "Photo credit" not in cleaned
    assert "Arsenal have reached full agreement" in cleaned


def test_strip_boilerplate_italian_and_spanish():
    """Verifies stripping of Italian and Spanish syndication boilerplate."""
    it_text = (
        "MILAN (ANSA) - Il Milan ha chiuso l'accordo per l'attaccante nigeriano per venti milioni. "
        "Per saperne di piu segui tutti gli aggiornamenti su Sky Sport."
    )
    it_cleaned = strip_boilerplate(it_text)
    assert "MILAN" not in it_cleaned
    assert "Per saperne di piu" not in it_cleaned
    assert "Il Milan ha chiuso" in it_cleaned

    es_text = "MADRID (EFE) : El Real Madrid acelera las conversaciones por el delantero estrella. Mas informacion en nuestra web oficial."
    es_cleaned = strip_boilerplate(es_text)
    assert "MADRID" not in es_cleaned
    assert "Mas informacion" not in es_cleaned
    assert "El Real Madrid acelera" in es_cleaned


def test_lead_paragraph_similarity():
    """Verifies that lead paragraph similarity catches shared opening ledes."""
    text1 = (
        "Arsenal have reached full agreement with Sporting CP for the transfer of winger Emeka Osei. "
        "The deal is expected to be finalized before the weekend."
    )
    text2 = (
        "Arsenal have reached full agreement with Sporting CP for the transfer of winger Emeka Osei. "
        "Personal terms were agreed last month according to sources in Lisbon."
    )
    sim = lead_paragraph_similarity(text1, text2, max_words=20)
    assert sim >= 0.75

    is_match, score = is_near_duplicate(text1, text2)
    assert is_match is True
    assert score >= 0.75


def test_cross_outlet_syndication_creates_one_event_and_one_claim(db_session):
    """Wire story published by Sky Sport Italia and syndicated by La Gazzetta dello Sport

    collapses into 1 event, 1 claim, and 2 evidence rows.
    """
    worker = SpeedLaneWorker(session=db_session)

    # First publication: Sky Sport Italia
    payload_sky = {
        "outlet": "Sky Sport Italia",
        "author": "Gianluca Di Marzio",
        "source_url": "https://sport.sky.it/calciomercato/osei-arsenal-accordo",
        "published_at": "2026-09-10T09:00:00Z",
        "headline": "Arsenal e Sporting, accordo totale per Emeka Osei",
        "body": "Arsenal e Sporting CP hanno raggiunto l'accordo totale per il trasferimento di Emeka Osei.",
        "language": "it",
    }
    res_1 = worker.process_raw_article(payload_sky)
    assert res_1["action"] == "claim_created"
    event_id_1 = res_1["event_id"]
    claim_id_1 = res_1["claim_id"]

    # Second publication: La Gazzetta dello Sport republishing the exact wire copy with different headline/URL
    payload_gazzetta = {
        "outlet": "La Gazzetta dello Sport",
        "author": "Redazione",
        "source_url": "https://gazzetta.it/calcio/mercato/osei-va-all-arsenal",
        "published_at": "2026-09-10T09:45:00Z",
        "headline": "Osei verso i Gunners: c'e l'intesa con lo Sporting",
        "body": "Arsenal e Sporting CP hanno raggiunto l'accordo totale per il trasferimento di Emeka Osei.",
        "language": "it",
    }
    res_2 = worker.process_raw_article(payload_gazzetta)

    # Must NOT create a second event or second claim
    assert res_2["action"] == "evidence_attached"
    assert res_2["event_id"] == event_id_1
    assert res_2["claim_id"] == claim_id_1
    assert res_2["similarity_to_root"] == 1.0

    # Verify database counts
    events = db_session.execute(select(EventModel)).scalars().all()
    assert len(events) == 1
    assert events[0].independent_sources == 2

    claims = db_session.execute(select(ClaimModel)).scalars().all()
    assert len(claims) == 1

    evidence = db_session.execute(select(ClaimEvidenceModel)).scalars().all()
    assert len(evidence) == 2
    outlets = {ev.source.name for ev in evidence if ev.source}
    assert "Sky Sport Italia" in outlets
    assert "La Gazzetta dello Sport" in outlets


def test_cross_outlet_syndication_with_boilerplate_variation(db_session):
    """Wire story republished with trailing boilerplate and photo credits attaches cleanly."""
    worker = SpeedLaneWorker(session=db_session)

    # First publication: clean report
    payload_guardian = {
        "outlet": "The Guardian",
        "author": "David Hytner",
        "source_url": "https://theguardian.com/football/mbappe-madrid-talks-advancing",
        "published_at": "2026-09-10T10:00:00Z",
        "headline": "Real Madrid close to finalizing personal terms with Kylian Mbappe",
        "body": "Real Madrid are in advanced discussions to finalize personal terms with Kylian Mbappe ahead of a proposed summer move.",
        "language": "en",
    }
    res_1 = worker.process_raw_article(payload_guardian)
    assert res_1["action"] == "claim_created"
    claim_id_1 = res_1["claim_id"]

    # Second publication: syndicated wire pickup with trailing RSS footer
    payload_bbc = {
        "outlet": "BBC Sport",
        "author": "Nizaar Kinsella",
        "source_url": "https://bbc.com/sport/football/mbappe-talks-real-madrid-update",
        "published_at": "2026-09-10T10:30:00Z",
        "headline": "Real Madrid close in on Mbappe agreement",
        "body": (
            "Real Madrid are in advanced discussions to finalize personal terms with Kylian Mbappe ahead of a proposed summer move. "
            "Read more on BBC Sport. Photo credit: Reuters"
        ),
        "language": "en",
    }
    res_2 = worker.process_raw_article(payload_bbc)

    assert res_2["action"] == "evidence_attached"
    assert res_2["claim_id"] == claim_id_1
    assert res_2["similarity_to_root"] >= 0.85

    claims = db_session.execute(select(ClaimModel)).scalars().all()
    assert len(claims) == 1

    evidence = db_session.execute(select(ClaimEvidenceModel)).scalars().all()
    assert len(evidence) == 2


def test_cross_feed_dedup_across_orphan_fallback_events(db_session):
    """Stories without recognized entities would previously mint separate e-misc-* events.

    With cross-feed dedup, the second story adopts the first story's e-misc-* event.
    """
    worker = SpeedLaneWorker(session=db_session)

    # Story with zero known entity graph matches
    payload_1 = {
        "outlet": "Reuters",
        "source_url": "https://reuters.example/sports/unknown-federation-ruling",
        "published_at": "2026-09-10T11:00:00Z",
        "headline": "International Archery Council confirms annual budget reallocation",
        "body": "The International Archery Council has confirmed a 10 percent budget reallocation across junior divisions for next season.",
        "language": "en",
    }
    res_1 = worker.process_raw_article(payload_1)
    assert res_1["action"] == "claim_created"
    assert res_1["event_id"].startswith("e-misc-")

    # Second outlet republishes the same wire report with a modified headline
    payload_2 = {
        "outlet": "Associated Press",
        "source_url": "https://apnews.example/sports/archery-budget-changes",
        "published_at": "2026-09-10T11:20:00Z",
        "headline": "Archery Council passes junior division funding reallocation",
        "body": "The International Archery Council has confirmed a 10 percent budget reallocation across junior divisions for next season.",
        "language": "en",
    }
    res_2 = worker.process_raw_article(payload_2)

    # Must adopt existing e-misc-* event, not mint a new orphan event
    assert res_2["action"] == "evidence_attached"
    assert res_2["event_id"] == res_1["event_id"]
    assert res_2["claim_id"] == res_1["claim_id"]

    events = db_session.execute(select(EventModel)).scalars().all()
    assert len(events) == 1


def test_syndication_with_secondary_attribution_cue(db_session):
    """Article citing an existing scoop attaches as secondary evidence to root claim."""
    worker = SpeedLaneWorker(session=db_session)

    payload_orig = {
        "outlet": "The Athletic",
        "author": "David Ornstein",
        "source_url": "https://theathletic.example/football/ornstein-exclusive-osei",
        "published_at": "2026-09-10T08:00:00Z",
        "headline": "Arsenal agree terms for Sporting winger Emeka Osei",
        "body": "Arsenal have agreed terms with Sporting CP for Emeka Osei with a 64m fee agreed, our sources understand.",
        "language": "en",
    }
    res_1 = worker.process_raw_article(payload_orig)
    assert res_1["action"] == "claim_created"
    assert res_1["attribution_type"] == "first_party"

    payload_citing = {
        "outlet": "Sky Sports",
        "author": "Kaveh Solhekol",
        "source_url": "https://skysports.example/news/arsenal-osei-athletic-report",
        "published_at": "2026-09-10T08:30:00Z",
        "headline": "Arsenal in talks for Emeka Osei, according to The Athletic",
        "body": "Sporting CP forward Emeka Osei is wanted by Arsenal, reported by The Athletic.",
        "language": "en",
    }
    res_2 = worker.process_raw_article(payload_citing)

    assert res_2["action"] == "evidence_attached"
    assert res_2["claim_id"] == res_1["claim_id"]
    assert res_2["attribution_type"] == "secondary"

    claims = db_session.execute(select(ClaimModel)).scalars().all()
    assert len(claims) == 1

    evidence = db_session.execute(select(ClaimEvidenceModel)).scalars().all()
    assert len(evidence) == 2


def test_distinct_stories_remain_separate(db_session):
    """Two genuinely distinct reports produce 2 separate events and 2 claims."""
    worker = SpeedLaneWorker(session=db_session)

    payload_transfer = {
        "outlet": "BBC Sport",
        "author": "Simon Stone",
        "source_url": "https://bbc.example/sport/arsenal-osei-fee",
        "published_at": "2026-09-10T12:00:00Z",
        "headline": "Arsenal agree fee with Sporting CP for Emeka Osei",
        "body": "Arsenal have agreed a £64m fee with Sporting CP to complete the permanent signing of Emeka Osei.",
        "language": "en",
    }
    res_1 = worker.process_raw_article(payload_transfer)
    assert res_1["action"] == "claim_created"

    payload_derby = {
        "outlet": "Sky Sports",
        "author": "Adam Bate",
        "source_url": "https://skysports.example/football/sporting-porto-derby",
        "published_at": "2026-09-10T14:00:00Z",
        "headline": "Sporting CP defeat Porto in dramatic Lisbon derby",
        "body": "Sporting CP secured a vital 2-1 victory over rivals Porto in a heated Portuguese league encounter at Estadio Jose Alvalade.",
        "language": "en",
    }
    res_2 = worker.process_raw_article(payload_derby)
    assert res_2["action"] == "claim_created"

    assert res_1["event_id"] != res_2["event_id"]
    assert res_1["claim_id"] != res_2["claim_id"]

    events = db_session.execute(select(EventModel)).scalars().all()
    assert len(events) == 2

    claims = db_session.execute(select(ClaimModel)).scalars().all()
    assert len(claims) == 2
