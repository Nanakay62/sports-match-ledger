import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from packages.database.models import Base, SourceModel, SourceRegistryStatus
from packages.database.registry import SourceRegistryService, seed_initial_source_registry
from packages.database.repository import LedgerRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_source_propose_initial_state(db_session):
    """Verifies that proposing a source starts in PROPOSED status with reviews pending."""
    item = SourceRegistryService.propose_source(
        session=db_session,
        source_name="Tuttosport",
        feed_url="https://www.tuttosport.com/rss/calciomercato",
        language="it",
        coverage_category="transfer_specific",
        authority_rank=3,
    )

    assert item.status == SourceRegistryStatus.PROPOSED.value
    assert item.technical_check_passed is False
    assert item.rights_review_passed is False
    assert item.approved_at is None


def test_cannot_approve_unreviewed_source(db_session):
    """Guards against approving a source that has not completed technical and rights reviews."""
    item = SourceRegistryService.propose_source(
        session=db_session,
        source_name="Unreviewed Outlet",
        feed_url="https://unreviewed.example/rss",
        language="en",
    )

    # Cannot approve directly from PROPOSED
    with pytest.raises(ValueError, match="TECHNICAL_REVIEW not passed"):
        SourceRegistryService.approve_source(session=db_session, registry_id=item.id)

    # Complete technical review only
    SourceRegistryService.run_technical_review(session=db_session, registry_id=item.id)

    # Cannot approve without RIGHTS_REVIEW
    with pytest.raises(ValueError, match="RIGHTS_REVIEW not passed"):
        SourceRegistryService.approve_source(session=db_session, registry_id=item.id)


def test_full_workflow_happy_path(db_session):
    """Tests the full progression: PROPOSED -> TECHNICAL_REVIEW -> RIGHTS_REVIEW -> APPROVED."""
    # 1. PROPOSED
    item = SourceRegistryService.propose_source(
        session=db_session,
        source_name="Gazzetta Test",
        feed_url="https://gazzetta-test.example/rss",
        language="it",
        coverage_category="transfer_specific",
        authority_rank=3,
    )
    assert item.status == SourceRegistryStatus.PROPOSED.value

    # 2. TECHNICAL_REVIEW
    sample_xml = "<rss><channel><title>Gazzetta</title><item><title>Deal</title></item></channel></rss>"
    item = SourceRegistryService.run_technical_review(
        session=db_session,
        registry_id=item.id,
        feed_content=sample_xml,
    )
    assert item.status == SourceRegistryStatus.TECHNICAL_REVIEW.value
    assert item.technical_check_passed is True

    # 3. RIGHTS_REVIEW
    item = SourceRegistryService.run_rights_review(
        session=db_session,
        registry_id=item.id,
        rights_notes="Terms of service cleared. Editorial attribution preserved.",
    )
    assert item.status == SourceRegistryStatus.RIGHTS_REVIEW.value
    assert item.rights_review_passed is True

    # 4. APPROVED
    item = SourceRegistryService.approve_source(
        session=db_session,
        registry_id=item.id,
    )
    assert item.status == SourceRegistryStatus.APPROVED.value
    assert item.approved_at is not None

    # Verify that approval synchronized a record in the primary sources table
    source = db_session.execute(select(SourceModel).where(SourceModel.name == "Gazzetta Test")).scalar_one()
    assert source.source_type == "outlet"
    assert source.sample_size == 0


def test_technical_review_detects_invalid_feed(db_session):
    """Verifies that non-XML or itemless payloads fail technical review."""
    item = SourceRegistryService.propose_source(
        session=db_session,
        source_name="Invalid Feed Outlet",
        feed_url="https://invalid.example/feed",
    )

    bad_html = "<html><body><h1>Not an RSS feed</h1></body></html>"
    item = SourceRegistryService.run_technical_review(
        session=db_session,
        registry_id=item.id,
        feed_content=bad_html,
    )

    assert item.technical_check_passed is False
    assert "Failed" in item.technical_notes


def test_reject_source(db_session):
    """Verifies that a source can be rejected with recorded rationale."""
    item = SourceRegistryService.propose_source(
        session=db_session,
        source_name="Scraper Required Blog",
        feed_url="https://blog.example/feed",
    )

    item = SourceRegistryService.reject_source(
        session=db_session,
        registry_id=item.id,
        reason="Requires unauthorized web scraping in violation of robots.txt.",
    )

    assert item.status == SourceRegistryStatus.REJECTED.value
    assert "Rejection reason" in item.technical_notes


def test_seed_initial_source_registry_and_coverage(db_session):
    """Verifies initial multilingual seed sources across it, es, pt, de, tr, and official feeds."""
    approved_list = seed_initial_source_registry(session=db_session)
    assert len(approved_list) == 15

    # Verify all are in APPROVED status
    for item in approved_list:
        assert item.status == SourceRegistryStatus.APPROVED.value
        assert item.technical_check_passed is True
        assert item.rights_review_passed is True
        assert item.approved_at is not None

    # Check multilingual coverage
    languages = {item.language for item in approved_list}
    assert "it" in languages  # Italian (Gazzetta dello Sport, Sky Sport Italia)
    assert "es" in languages  # Spanish (Marca, AS, Mundo Deportivo)
    assert "pt" in languages  # Portuguese (Record, Maisfutebol)
    assert "de" in languages  # German (Kicker)
    assert "tr" in languages  # Turkish (Fotomaç, AA Spor)
    assert "en" in languages  # English (UEFA, FIFA, BBC Sport, The Guardian)

    # Check official feeds have Rank 1 authority per §5.3
    uefa = next(i for i in approved_list if i.source_name == "UEFA Official")
    assert uefa.authority_rank == 1
    assert uefa.coverage_category == "official"

    fifa = next(i for i in approved_list if i.source_name == "FIFA Official")
    assert fifa.authority_rank == 1
    assert fifa.coverage_category == "official"

    # Verify that is_approved_outlet recognizes all seeded sources
    assert LedgerRepository.is_approved_outlet(db_session, "La Gazzetta dello Sport") is True
    assert LedgerRepository.is_approved_outlet(db_session, "Marca") is True
    assert LedgerRepository.is_approved_outlet(db_session, "Record") is True
    assert LedgerRepository.is_approved_outlet(db_session, "Kicker Bundesliga") is True
    assert LedgerRepository.is_approved_outlet(db_session, "Fotomaç") is True
    assert LedgerRepository.is_approved_outlet(db_session, "UEFA Official") is True
