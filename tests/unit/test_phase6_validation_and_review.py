import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from packages.common.models import EventStatus
from packages.common.validation import (
    REPORTER_SCORE_CAP,
    DeterministicValidationEngine,
    ValidationClaimInput,
)
from packages.database.models import (
    Base,
    ClaimModel,
    EventModel,
    SourceModel,
)
from packages.database.session import get_db
from workers.pipeline.review_router import HumanReviewRouter

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
ADMIN_HEADERS = {"X-Admin-Key": "dev-admin-ledger-secret-key"}


@pytest.fixture(autouse=True)
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    app.dependency_overrides.clear()


def test_8_factor_validation_confirmed_status():
    claims = [
        ValidationClaimInput(
            claim_id="clm-1",
            outlet_name="Arsenal FC Official",
            authority_rank=1,
            predicate="official_signing",
            fee_eur=60.0,
        ),
        ValidationClaimInput(
            claim_id="clm-2",
            outlet_name="BBC Sport",
            authority_rank=3,
            predicate="official_signing",
            fee_eur=60.0,
        ),
    ]

    res = DeterministicValidationEngine.evaluate(claims)
    assert res.status == EventStatus.CONFIRMED
    assert res.is_confirmed is True
    assert res.has_contradiction is False
    assert res.factors["official_confirmation"] == 1.0
    assert any("Official confirmation on record" in b["text"] for b in res.rationale_bullets)


def test_8_factor_validation_well_corroborated_vs_rumour():
    # 3 independent sources -> Well Corroborated
    three_sources = [
        ValidationClaimInput(claim_id="c1", outlet_name="The Athletic", authority_rank=3, predicate="agrees_terms"),
        ValidationClaimInput(claim_id="c2", outlet_name="Sky Sports", authority_rank=3, predicate="agrees_terms"),
        ValidationClaimInput(claim_id="c3", outlet_name="L Equipe", authority_rank=3, predicate="agrees_terms"),
    ]
    res_three = DeterministicValidationEngine.evaluate(three_sources)
    assert res_three.status == EventStatus.WELL_CORROBORATED
    assert res_three.independent_roots == 3

    # Single source -> Rumour
    single_source = [
        ValidationClaimInput(claim_id="c1", outlet_name="The Sun", authority_rank=4, predicate="agrees_terms"),
    ]
    res_single = DeterministicValidationEngine.evaluate(single_source)
    assert res_single.status == EventStatus.RUMOUR
    assert res_single.independent_roots == 1


def test_8_factor_validation_contradiction_disputed():
    claims = [
        ValidationClaimInput(claim_id="c1", outlet_name="The Athletic", predicate="agrees_terms"),
        ValidationClaimInput(claim_id="c2", outlet_name="Sporting Lisbon Official", predicate="transfer_denied"),
    ]
    res = DeterministicValidationEngine.evaluate(claims)
    assert res.status == EventStatus.DISPUTED
    assert res.has_contradiction is True
    assert res.factors["contradiction"] == 1.0
    assert any("Direct contradiction on record" in b["text"] for b in res.rationale_bullets)


def test_reporter_score_strictly_capped_at_085():
    # Reputation must never substitute for evidence per Handbook §13
    claims = [
        ValidationClaimInput(
            claim_id="c1",
            outlet_name="The Athletic",
            reporter_wilson_score=0.98,
        ),
    ]
    res = DeterministicValidationEngine.evaluate(claims)
    assert res.factors["reporter_record"] <= REPORTER_SCORE_CAP
    assert res.factors["reporter_record"] == 0.85


def test_human_review_router_sensitive_taxonomies():
    # 1. Allegations & legal
    d1 = HumanReviewRouter.classify_text("Police have arrested the Premier League player following an assault investigation.")
    assert d1.requires_review is True
    assert d1.trigger_category == "allegations_legal"
    assert d1.priority == "critical"

    # 2. Disciplinary action
    d2 = HumanReviewRouter.classify_text("FA charges manager with misconduct, handed a 3-match suspension.")
    assert d2.requires_review is True
    assert d2.trigger_category == "disciplinary_action"
    assert d2.priority == "high"

    # 3. Medical / death
    d3 = HumanReviewRouter.classify_text("Midfielder collapsed during training and remains in intensive care.")
    assert d3.requires_review is True
    assert d3.trigger_category == "medical_injury"
    assert d3.priority == "critical"

    # 4. Minor
    d4 = HumanReviewRouter.classify_text("Chelsea open talks with 16-year-old academy talent.")
    assert d4.requires_review is True
    assert d4.trigger_category == "minor"
    assert d4.priority == "critical"

    # 5. Sensitive personal
    d5 = HumanReviewRouter.classify_text("Striker granted compassionate leave due to family bereavement.")
    assert d5.requires_review is True
    assert d5.trigger_category == "sensitive_personal"
    assert d5.priority == "critical"


def test_human_review_router_contextual_and_numerical_triggers():
    # First-time source (sample_size == 0)
    d_fts = HumanReviewRouter.classify_claim_context(
        claim_text="Arsenal target Bundesliga winger.",
        source_sample_size=0,
    )
    assert d_fts.requires_review is True
    assert d_fts.trigger_category == "first_time_source"

    # Low extraction confidence (< 0.70)
    d_lc = HumanReviewRouter.classify_claim_context(
        claim_text="Arsenal target winger.",
        extraction_confidence=0.60,
    )
    assert d_lc.requires_review is True
    assert d_lc.trigger_category == "low_confidence"

    # Numerical conflict (>20% gap between €50m and €70m = 40% gap)
    d_num = HumanReviewRouter.detect_numerical_conflicts([50.0, 70.0])
    assert d_num.requires_review is True
    assert d_num.trigger_category == "numerical_conflict"
    assert d_num.priority == "high"


def test_editorial_decision_logging_and_api():
    with TestSession() as session:
        src = SourceModel(id="src-bbc", name="BBC Sport", source_type="outlet")
        event = EventModel(
            id="evt-review-1",
            headline="Controversial transfer report",
            status="rumour",
            sport="football",
            competition="Premier League",
            summary="Review item test.",
            source_url="https://bbc.example/story",
        )
        claim = ClaimModel(
            id="clm-rev-1",
            event_id=event.id,
            source_id=src.id,
            claim_text="Midfielder banned for 3 matches after disciplinary investigation.",
            attribution="direct_quote",
            original_url="https://bbc.example/story",
        )
        session.add_all([src, event, claim])
        session.commit()

    # Verify review queue returns taxonomy category and priority
    resp_queue = client.get("/api/v1/admin/review-queue", headers=ADMIN_HEADERS)
    assert resp_queue.status_code == 200
    queue_items = resp_queue.json()
    assert len(queue_items) > 0
    item = next(i for i in queue_items if i["id"] == "clm-rev-1")
    assert item["trigger_category"] in {"disciplinary_action", "allegations_legal"}
    assert item["priority"] in {"critical", "high"}

    # Execute editorial decision: Confirm
    resp_resolve = client.post(
        "/api/v1/admin/review-queue/clm-rev-1/resolve",
        json={"action": "confirm", "notes": "Official FA regulatory ruling verified"},
        headers=ADMIN_HEADERS,
    )
    assert resp_resolve.status_code == 200
    res_data = resp_resolve.json()
    assert res_data["status"] == "success"
    assert res_data["new_event_status"] == "confirmed"
    assert "evaluation_log_id" in res_data

    # Verify evaluation log entry exists
    resp_logs = client.get("/api/v1/admin/evaluation-logs", headers=ADMIN_HEADERS)
    assert resp_logs.status_code == 200
    logs = resp_logs.json()
    assert len(logs) > 0
    logged = logs[0]
    assert logged["claim_id"] == "clm-rev-1"
    assert logged["action"] == "confirm"
    assert "Official FA regulatory ruling verified" in logged["editor_notes"]
