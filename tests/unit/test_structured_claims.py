from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.ai.claim_validator import ClaimSchemaValidator
from packages.database.models import (
    Base,
    ClaimEvidenceModel,
    ClaimModel,
    EventModel,
    PipelineJobModel,
    ReporterModel,
    ResolutionModel,
    SourceModel,
)
from workers.pipeline.claim_extractor import StructuredClaimExtractor
from workers.pipeline.outcome_resolver import OutcomeResolverWorker
from workers.pipeline.speed_lane import SpeedLaneWorker


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_claim_extractor_fee_and_duration():
    text = "Arsenal will pay €65m fee on a 5-year deal until June 2030."
    fee = StructuredClaimExtractor.extract_fee(text)
    duration = StructuredClaimExtractor.extract_contract_duration(text)

    assert fee == 65.0
    assert duration == 5


def test_claim_extractor_gbp_conversion():
    text = "Chelsea submitted £50m bid for the midfielder."
    fee = StructuredClaimExtractor.extract_fee(text)
    assert fee == round(50.0 * 1.18, 2)


def test_claim_extractor_verbatim_evidence_span():
    body = "Arsenal have agreed personal terms with Emeka Osei on a long-term contract."
    headline = "Arsenal agree personal terms with Emeka Osei"
    triple = StructuredClaimExtractor.extract_structured_claim(headline=headline, body=body)

    assert triple.predicate == "agrees_terms"
    assert triple.evidence_span is not None
    assert triple.evidence_span in body
    assert triple.resolvable is True


def test_claim_extractor_multilingual_predicates():
    # Spanish
    es_headline = "El Arsenal ha fichado por 70 millones a Emeka Osei"
    es_triple = StructuredClaimExtractor.extract_structured_claim(headline=es_headline, body=es_headline)
    assert es_triple.predicate == "official_signing"

    # German
    de_headline = "Bayern München schließt Wechsel von Osei aus"
    de_triple = StructuredClaimExtractor.extract_structured_claim(headline=de_headline, body=de_headline)
    assert de_triple.predicate == "transfer_denied"


def test_speed_lane_extracts_and_persists_structured_triple(db_session):
    worker = SpeedLaneWorker(session=db_session)
    payload = {
        "outlet": "The Athletic",
        "author": "David Ornstein",
        "source_url": "https://theathletic.example/osei-arsenal-bid",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Arsenal submit £45m bid for Emeka Osei",
        "body": "Arsenal have submitted a formal bid for Sporting CP winger Emeka Osei worth €55m.",
        "language": "en",
    }

    res = worker.process_raw_article(payload)
    assert res["status"] == "rumour"

    # Verify claim in ledger has §5.2 structured triple fields populated
    claim = db_session.query(ClaimModel).first()
    assert claim is not None
    assert claim.predicate in {"submits_bid", "agrees_terms", "transfer_linked"}
    assert claim.evidence_span is not None
    assert claim.evidence_span in payload["body"] or claim.evidence_span in payload["headline"]
    assert claim.resolvable is True
    assert claim.schema_version.startswith("5.2")


def test_outcome_resolver_rank_1_official_signing(db_session):
    # Setup outlet source
    outlet = SourceModel(
        id="src-athletic",
        name="The Athletic",
        source_type="outlet",
        sample_size=9,
        correct_count=7,
        wilson_lower_bound=0.45,
    )
    # Setup reporter source for Wilson scoring
    rep_source = SourceModel(
        id="src-ornstein",
        name="David Ornstein",
        source_type="reporter",
        sample_size=9,
        correct_count=7,
        wilson_lower_bound=0.45,
    )
    # Setup reporter entity linked to source
    reporter = ReporterModel(
        id="rep-ornstein",
        name="David Ornstein",
        slug="david-ornstein",
        primary_source_id="src-ornstein",
    )
    # Setup pending rumours
    event = EventModel(
        id="evt-osei-transfer",
        headline="Emeka Osei transfer saga",
        status="rumour",
        sport="football",
        competition="Premier League",
        summary="Transfer saga coverage.",
        source_url="https://theathletic.example/osei",
    )
    claim_correct = ClaimModel(
        id="clm-rumour-1",
        event_id=event.id,
        source_id=outlet.id,
        reporter_id=reporter.id,
        claim_text="Arsenal agree terms for Emeka Osei",
        attribution="direct_quote",
        attribution_type="first_party",
        original_url="https://theathletic.example/osei-1",
        subject_id="ent-player-osei",
        predicate="agrees_terms",
        object_id="ent-club-arsenal",
        resolvable=True,
    )
    claim_denial = ClaimModel(
        id="clm-denial-2",
        event_id=event.id,
        source_id=outlet.id,
        reporter_id=reporter.id,
        claim_text="Sporting deny Osei transfer to Arsenal",
        attribution="direct_quote",
        attribution_type="first_party",
        original_url="https://theathletic.example/osei-2",
        subject_id="ent-player-osei",
        predicate="transfer_denied",
        object_id="ent-club-arsenal",
        resolvable=True,
    )
    db_session.add_all([outlet, rep_source, reporter, event, claim_correct, claim_denial])
    db_session.commit()

    # Authoritative Rank 1 announcement: Official Signing
    announcement_headline = "Emeka Osei signs for Arsenal"
    announcement_body = "Arsenal Football Club is delighted to announce that Emeka Osei has completed transfer to Arsenal."

    result = OutcomeResolverWorker.resolve_from_authoritative_announcement(
        session=db_session,
        headline=announcement_headline,
        body=announcement_body,
        authority_source_url="https://www.arsenal.com/news/osei-signing",
        authority_rank=1,
    )

    assert result["status"] == "success"
    assert result["claims_resolved"] == 2

    # Check resolutions
    res1 = db_session.query(ResolutionModel).filter(ResolutionModel.claim_id == "clm-rumour-1").one()
    assert res1.outcome == "correct"
    assert res1.authority_rank == 1

    res2 = db_session.query(ResolutionModel).filter(ResolutionModel.claim_id == "clm-denial-2").one()
    assert res2.outcome == "incorrect"
    assert res2.authority_rank == 1

    # Check updated Wilson score for outlet (initial 9 sample, 7 correct -> +1 correct +1 incorrect = 11 sample, 8 correct)
    db_session.refresh(outlet)
    assert outlet.sample_size == 11
    assert outlet.correct_count == 8
    assert outlet.wilson_lower_bound is not None


def test_outcome_resolver_skips_aggregation_claims(db_session):
    outlet = SourceModel(
        id="src-aggregator",
        name="Transfer Aggregator News",
        source_type="outlet",
        sample_size=5,
        correct_count=4,
        wilson_lower_bound=0.35,
    )
    event = EventModel(
        id="evt-transfer",
        headline="Transfer saga",
        status="rumour",
        sport="football",
        competition="Premier League",
        summary="Aggregated transfer news.",
        source_url="https://aggregator.example/summary",
    )
    agg_claim = ClaimModel(
        id="clm-agg-1",
        event_id=event.id,
        source_id=outlet.id,
        claim_text="Aggregator reports Osei to Arsenal",
        attribution="indirect_quote",
        attribution_type="aggregation",
        original_url="https://aggregator.example/rumours",
        subject_id="ent-player-osei",
        predicate="agrees_terms",
        object_id="ent-club-arsenal",
        resolvable=True,
    )
    db_session.add_all([outlet, event, agg_claim])
    db_session.commit()

    OutcomeResolverWorker.resolve_claim(
        session=db_session,
        claim=agg_claim,
        outcome="correct",
        authority_rank=1,
        authority_source_url="https://arsenal.com/announcement",
    )

    # Per §5.2, aggregation claims never update primary reliability scores
    db_session.refresh(outlet)
    assert outlet.sample_size == 5
    assert outlet.correct_count == 4
    # But they do update aggregation_repetition counters
    assert outlet.sample_size_aggregation == 1
    assert outlet.correct_count_aggregation == 1


def test_outcome_resolver_persists_component_correctness(db_session):
    outlet = SourceModel(id="src-comp-test", name="Component Test Outlet", source_type="outlet")
    event = EventModel(
        id="evt-comp-test",
        headline="Osei joins Arsenal",
        status="rumour",
        sport="football",
        competition="Premier League",
        summary="Osei signs deal.",
        source_url="https://athletic.example/1",
    )
    claim = ClaimModel(
        id="clm-comp-test",
        event_id=event.id,
        source_id=outlet.id,
        claim_text="Arsenal have officially signed Emeka Osei.",
        attribution="first_party",
        original_url="https://athletic.example/1",
        subject_id="ent-player-osei",
        predicate="official_signing",
        object_id="ent-club-arsenal",
    )
    db_session.add_all([outlet, event, claim])
    db_session.commit()

    res = OutcomeResolverWorker.resolve_claim(
        session=db_session,
        claim=claim,
        outcome="correct",
        authority_rank=1,
        authority_source_url="https://arsenal.com/official",
        entity_correct=True,
        direction_correct=True,
        timing_correct=True,
        fee_correct=False,
    )
    assert res.entity_correct is True
    assert res.direction_correct is True
    assert res.timing_correct is True
    assert res.fee_correct is False

    db_session.refresh(outlet)
    assert outlet.sample_size == 1
    assert outlet.correct_count == 1
    assert outlet.sample_size_original == 1
    assert outlet.correct_count_original == 1
    assert outlet.sample_size_aggregation == 0


def test_outcome_resolver_rejects_rank_3_auto_resolution(db_session):
    res = OutcomeResolverWorker.resolve_from_authoritative_announcement(
        session=db_session,
        headline="Emeka Osei officially joins Arsenal",
        body="Arsenal confirms signing.",
        authority_source_url="https://tabloid.example/rumours",
        authority_rank=3,
    )
    assert res["status"] == "skipped"
    assert "Auto-resolution requires Authority Rank 1 or 2" in res["reason"]


def test_claim_schema_validator_rules():
    # Valid triple
    valid_triple = {
        "subject_id": "ent-player-osei",
        "predicate": "official_signing",
        "object_id": "ent-club-arsenal",
        "evidence_span": "Arsenal have officially signed Emeka Osei.",
        "confidence": 1.0,
    }
    res = ClaimSchemaValidator.validate_claim_triple(valid_triple, source_text="Breaking: Arsenal have officially signed Emeka Osei.")
    assert res.is_valid is True
    assert len(res.reasons) == 0

    # Missing predicate
    no_pred = dict(valid_triple)
    no_pred["predicate"] = ""
    res_no_pred = ClaimSchemaValidator.validate_claim_triple(no_pred)
    assert res_no_pred.is_valid is False
    assert any("predicate" in r for r in res_no_pred.reasons)

    # Invalid predicate
    bad_pred = dict(valid_triple)
    bad_pred["predicate"] = "scores_goal"
    res_bad_pred = ClaimSchemaValidator.validate_claim_triple(bad_pred)
    assert res_bad_pred.is_valid is False
    assert any("Invalid predicate" in r for r in res_bad_pred.reasons)

    # Missing subject entity
    no_subj = dict(valid_triple)
    no_subj["subject_id"] = None
    no_subj["subject_name"] = None
    res_no_subj = ClaimSchemaValidator.validate_claim_triple(no_subj)
    assert res_no_subj.is_valid is False
    assert any("subject entity" in r for r in res_no_subj.reasons)

    # Non-verbatim evidence span
    res_non_verbatim = ClaimSchemaValidator.validate_claim_triple(
        valid_triple, source_text="Completely different article body with no quote."
    )
    assert res_non_verbatim.is_valid is False
    assert any("not a verbatim substring" in r for r in res_non_verbatim.reasons)

    # Low confidence
    low_conf = dict(valid_triple)
    low_conf["confidence"] = 0.35
    res_low_conf = ClaimSchemaValidator.validate_claim_triple(low_conf)
    assert res_low_conf.is_valid is False
    assert any("below threshold" in r for r in res_low_conf.reasons)


def test_speed_lane_stores_evidence_span_not_raw_body(db_session):
    worker = SpeedLaneWorker(session=db_session)
    full_body = (
        "Arsenal have submitted a formal bid for Sporting CP winger Emeka Osei worth €55m. "
        "The Portuguese international has been a target for Mikel Arteta all summer long. "
        "Negotiations are expected to continue throughout next week with personal terms agreed. "
        "The player is keen on moving to north London and has rejected alternative proposals."
    )
    payload = {
        "outlet": "The Athletic",
        "author": "David Ornstein",
        "source_url": "https://theathletic.example/osei-arsenal-span-check",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Arsenal submit £45m bid for Emeka Osei",
        "body": full_body,
        "language": "en",
    }

    worker.process_raw_article(payload)

    claim = db_session.query(ClaimModel).filter(ClaimModel.original_url == payload["source_url"]).first()
    assert claim is not None
    # claim_text must be the concise evidence span, not the 4-sentence raw article body
    assert claim.claim_text == claim.evidence_span
    assert len(claim.claim_text) < len(full_body)
    assert "Arsenal have submitted a formal bid" in claim.claim_text


def test_outcome_resolver_rank_3_consensus(db_session):
    outlet1 = SourceModel(id="src-sky", name="Sky Sports", source_type="outlet")
    outlet2 = SourceModel(id="src-ath", name="The Athletic", source_type="outlet")
    outlet3 = SourceModel(id="src-bbc", name="BBC Sport", source_type="outlet")
    event = EventModel(
        id="e-test-r3",
        headline="Osei joins Arsenal",
        status="rumour",
        sport="Football",
        competition="Premier League",
        summary="Osei agreed terms.",
        source_url="https://sky.example/1",
    )
    # Claim created 8 hours ago
    claim_time = datetime.now(timezone.utc) - timedelta(hours=8)
    claim = ClaimModel(
        id="c-r3-test",
        event_id=event.id,
        source_id=outlet1.id,
        claim_text="Emeka Osei agrees Arsenal deal.",
        attribution="first_party",
        original_url="https://sky.example/1",
        timestamp=claim_time,
    )
    db_session.add_all([outlet1, outlet2, outlet3, event, claim])
    db_session.commit()

    # 1. With only 1 outlet, consensus is insufficient
    res1 = OutcomeResolverWorker.check_rank3_consensus(session=db_session, claim=claim)
    assert res1["status"] == "insufficient_corroboration"
    assert res1["independent_count"] == 1

    # 2. Add 2 independent corroborating outlets as evidence
    ev1 = ClaimEvidenceModel(
        id="ev-ath",
        claim_id=claim.id,
        source_id=outlet2.id,
        source_url="https://theathletic.example/ev",
        attribution_type="first_party",
        published_at=datetime.now(timezone.utc),
        content_hash="h1",
    )
    ev2 = ClaimEvidenceModel(
        id="ev-bbc",
        claim_id=claim.id,
        source_id=outlet3.id,
        source_url="https://bbc.example/ev",
        attribution_type="first_party",
        published_at=datetime.now(timezone.utc),
        content_hash="h2",
    )
    db_session.add_all([ev1, ev2])
    db_session.commit()

    # 3. Now 3 independent outlets exist and age > 6 hours -> eligible
    res_eligible = OutcomeResolverWorker.check_rank3_consensus(session=db_session, claim=claim)
    assert res_eligible["status"] == "eligible"
    assert res_eligible["independent_count"] == 3

    # 4. Resolve at Rank 3
    resolution = OutcomeResolverWorker.resolve_rank3_consensus(session=db_session, claim=claim)
    assert resolution.authority_rank == 3
    assert resolution.outcome == "correct"


def test_outcome_resolver_rank_4_escalation(db_session):
    outlet = SourceModel(id="src-lone", name="Lone Tabloid", source_type="outlet")
    event = EventModel(
        id="e-test-r4",
        headline="Uncorroborated rumour",
        status="rumour",
        sport="Football",
        competition="Premier League",
        summary="Single source report.",
        source_url="https://lone.example/1",
    )
    claim = ClaimModel(
        id="c-r4-test",
        event_id=event.id,
        source_id=outlet.id,
        claim_text="Secret clause agreed in contract.",
        attribution="first_party",
        original_url="https://lone.example/1",
    )
    db_session.add_all([outlet, event, claim])
    db_session.commit()

    job = OutcomeResolverWorker.escalate_to_human_queue(
        session=db_session,
        claim=claim,
        reason="Sole uncorroborated source reporting sensitive contract details.",
    )
    assert isinstance(job, PipelineJobModel)
    assert job.lane == "human_review"
    assert job.status == "pending"
    assert "c-r4-test" in job.payload


def test_outcome_resolver_rank_5_deadline_expiry(db_session):
    outlet = SourceModel(id="src-exp", name="Summer Outlet", source_type="outlet")
    event = EventModel(
        id="e-test-r5",
        headline="Transfer rumour from June",
        status="rumour",
        sport="Football",
        competition="Premier League",
        summary="Old rumour.",
        source_url="https://exp.example/1",
    )
    # Claim from 10 days ago (within 30 day window)
    recent_claim = ClaimModel(
        id="c-recent",
        event_id=event.id,
        source_id=outlet.id,
        claim_text="Player linked with summer move.",
        attribution="first_party",
        original_url="https://exp.example/1",
        timestamp=datetime.now(timezone.utc) - timedelta(days=10),
    )
    # Claim from 35 days ago (expired past 30 day window)
    expired_claim = ClaimModel(
        id="c-expired",
        event_id=event.id,
        source_id=outlet.id,
        claim_text="Player will sign before deadline.",
        attribution="first_party",
        original_url="https://exp.example/2",
        timestamp=datetime.now(timezone.utc) - timedelta(days=35),
    )
    db_session.add_all([outlet, event, recent_claim, expired_claim])
    db_session.commit()

    # Recent claim should remain pending
    res_recent = OutcomeResolverWorker.resolve_expired_deadline(session=db_session, claim=recent_claim, deadline_days=30)
    assert res_recent["status"] == "pending"
    assert res_recent["days_remaining"] > 0

    # Expired claim must auto-resolve to did_not_occur at Authority Rank 5
    res_expired = OutcomeResolverWorker.resolve_expired_deadline(session=db_session, claim=expired_claim, deadline_days=30)
    assert res_expired["status"] == "resolved"
    assert res_expired["outcome"] == "did_not_occur"
    assert res_expired["authority_rank"] == 5
