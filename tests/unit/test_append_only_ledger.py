import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.database.models import Base
from packages.database.repository import LedgerRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_append_claim_creates_record(db_session):
    claim = LedgerRepository.append_claim(
        session=db_session,
        claim_id="c-test-01",
        event_id="e-test-01",
        outlet_name="The Woodwork",
        claim_text="Arsenal are preparing an opening bid.",
        original_url="https://thewoodwork.example/article-1",
        reporter="Tom Whitcombe",
    )
    db_session.commit()

    assert claim.id == "c-test-01"
    assert claim.source.name == "The Woodwork"
    assert claim.source.sample_size == 1
    # Sample size < 10, so Wilson lower bound remains None
    assert claim.source.wilson_lower_bound is None


def test_append_only_invariant_prevents_duplicate_or_overwrite(db_session):
    LedgerRepository.append_claim(
        session=db_session,
        claim_id="c-test-immutable",
        event_id="e-test-01",
        outlet_name="The Woodwork",
        claim_text="Original unalterable report.",
        original_url="https://thewoodwork.example/article-2",
    )
    db_session.commit()

    # Attempting to re-insert or overwrite the same claim must fail
    with pytest.raises(ValueError, match="is already recorded and immutable"):
        LedgerRepository.append_claim(
            session=db_session,
            claim_id="c-test-immutable",
            event_id="e-test-01",
            outlet_name="The Woodwork",
            claim_text="Tampered claim text.",
            original_url="https://thewoodwork.example/article-2",
        )
