import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from packages.ai.budget import CostTracker
from packages.ai.cache import SemanticCache
from packages.ai.translation import (
    DeterministicTranslationValidator,
    TranslationService,
)
from packages.common.entities import GLOSSARY_VERSION, default_entity_graph
from packages.database.models import (
    Base,
    ClaimModel,
    EventModel,
    EventTranslationModel,
    SourceModel,
)
from packages.database.session import get_db

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(bind=engine)


def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()


def test_glossary_enforcement_prevents_munich_bavaria():
    """Verifies that club names come strictly from the entity graph and prevents 'Munich Bavaria' error."""
    glossary = default_entity_graph.get_localized_glossary(["Bayern München"], target_lang="en")
    assert glossary.get("Bayern München") == "Bayern Munich"
    assert glossary.get("FC Bayern") == "Bayern Munich"

    it_glossary = default_entity_graph.get_localized_glossary(["Bayern München"], target_lang="it")
    assert it_glossary.get("Bayern München") == "Bayern Monaco"

    # Test validator catches banned "Munich Bavaria" error
    banned_text = "Arsenal will face Munich Bavaria in the quarter-finals."
    is_valid, reasons = DeterministicTranslationValidator.validate(
        source_text="Arsenal trifft auf Bayern München im Viertelfinale.",
        translated_text=banned_text,
        glossary=glossary,
    )
    assert is_valid is False
    assert any("munich bavaria" in r.lower() for r in reasons)


def test_milan_and_inter_distinction():
    """Verifies AC Milan and Inter Milan are disambiguated properly in target language."""
    glossary_milan = default_entity_graph.get_localized_glossary(["AC Milan"], target_lang="en")
    assert glossary_milan.get("Milan") == "AC Milan"

    glossary_inter = default_entity_graph.get_localized_glossary(["Inter Milan"], target_lang="en")
    assert glossary_inter.get("Inter") == "Inter Milan"


def test_deterministic_number_preservation_rejects_altered_figures():
    """Handbook §15.4: A translation that alters numbers or fees is rejected automatically."""
    source_text = "Arsenal have agreed a £64m fee with Sporting CP for Emeka Osei."
    altered_text = "Arsenal have agreed a £70m fee with Sporting CP for Emeka Osei."

    glossary = default_entity_graph.get_localized_glossary(["Sporting CP", "Arsenal"], target_lang="en")
    is_valid, reasons = DeterministicTranslationValidator.validate(
        source_text=source_text,
        translated_text=altered_text,
        glossary=glossary,
    )
    assert is_valid is False
    assert any("Invented numbers" in r for r in reasons)


def test_translation_service_same_language_zero_cost():
    """Translating text into its own language returns immediately at Rung L0 with EUR 0.00 cost."""
    service = TranslationService()
    result = service.translate_event_summary(
        event_id="e-test-1",
        headline="Arsenal agree terms for Osei",
        summary="Arsenal have agreed terms with Sporting CP for winger Emeka Osei.",
        source_lang="en",
        target_lang="en",
    )
    assert result.cache_hit is True
    assert result.cost_eur == 0.0
    assert result.model_id == "rung-l0-deterministic"


def test_translation_service_caching_behavior():
    """Verifies that second translation request hits semantic cache with EUR 0.00 cost."""
    cost_tracker = CostTracker()
    cache = SemanticCache()
    service = TranslationService(cost_tracker=cost_tracker, cache=cache)

    # First call: translated and cost recorded
    res1 = service.translate_event_summary(
        event_id="e-test-cache",
        headline="Arsenal e Sporting, accordo totale per Emeka Osei",
        summary="Arsenal e Sporting CP hanno raggiunto l'accordo totale per il trasferimento di Emeka Osei.",
        source_lang="it",
        target_lang="en",
        entity_ids=["Sporting CP", "Arsenal"],
    )
    assert res1.cache_hit is False
    assert res1.cost_eur > 0.0
    assert "full agreement for the transfer of" in res1.translated_text

    # Second call with identical summary: hits cache
    res2 = service.translate_event_summary(
        event_id="e-test-cache",
        headline="Arsenal e Sporting, accordo totale per Emeka Osei",
        summary="Arsenal e Sporting CP hanno raggiunto l'accordo totale per il trasferimento di Emeka Osei.",
        source_lang="it",
        target_lang="en",
        entity_ids=["Sporting CP", "Arsenal"],
    )
    assert res2.cache_hit is True
    assert res2.cost_eur == 0.0
    assert res2.translated_text == res1.translated_text


def test_glossary_version_bumping_invalidates_cache():
    """Handbook §6.2: Bumping glossary version deliberately invalidates the translation cache."""
    cache = SemanticCache()
    service = TranslationService(cache=cache)

    key_v1 = service.compute_translation_cache_key("Summary text", "en", glossary_version="v1")
    key_v2 = service.compute_translation_cache_key("Summary text", "en", glossary_version="v2")

    assert key_v1 != key_v2


def test_events_api_endpoint_with_lang_query():
    """Verifies that GET /api/v1/events?lang=en returns localized headline and summary."""
    session = TestingSessionLocal()
    try:
        # Create an Italian event and claim in database
        event = EventModel(
            id="e-it-event-1",
            headline="Arsenal e Sporting, accordo totale per Emeka Osei",
            status="rumour",
            independent_sources=1,
            sport="Football",
            competition="Premier League",
            summary="Arsenal e Sporting CP hanno raggiunto l'accordo totale per il trasferimento di Emeka Osei.",
            source_url="https://skyitalia.example/osei",
            first_reported_outlet="Sky Sport Italia",
        )
        session.add(event)
        session.flush()

        source = SourceModel(
            id="src-sky-it",
            name="Sky Sport Italia",
            source_type="outlet",
        )
        session.add(source)
        session.flush()

        claim = ClaimModel(
            id="c-it-claim-1",
            event_id=event.id,
            source_id=source.id,
            claim_text="Arsenal e Sporting CP hanno raggiunto l'accordo totale per il trasferimento di Emeka Osei.",
            original_url="https://skyitalia.example/osei",
            attribution="original",
            attribution_type="first_party",
            language="it",
        )
        session.add(claim)
        session.commit()
    finally:
        session.close()

    # Query API with target language = en
    resp = client.get("/api/v1/events?lang=en")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 1
    ev = events[0]
    assert ev["is_translated"] is True
    assert ev["original_language"] == "it"
    assert ev["language"] == "en"
    assert "full agreement" in ev["summary"].lower()

    # Query single event endpoint
    resp_single = client.get(f"/api/v1/events/{ev['id']}?lang=en")
    assert resp_single.status_code == 200
    single_ev = resp_single.json()
    assert single_ev["is_translated"] is True
    assert single_ev["original_headline"] == "Arsenal e Sporting, accordo totale per Emeka Osei"

    # Verify database stored EventTranslationModel
    session = TestingSessionLocal()
    try:
        translations = session.query(EventTranslationModel).filter(EventTranslationModel.event_id == "e-it-event-1").all()
        assert len(translations) == 1
        assert translations[0].language == "en"
        assert translations[0].glossary_version == GLOSSARY_VERSION
    finally:
        session.close()
