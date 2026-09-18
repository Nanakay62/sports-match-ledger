import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from packages.ai.budget import CostTracker
from packages.database.billing_repository import BillingRepository
from packages.database.models import Base, ClaimModel, EventModel, SourceModel
from packages.database.notifications_repository import NotificationsRepository
from packages.database.session import get_db
from packages.notifications.dispatcher import NotificationDispatcher
from packages.notifications.email_backend import ConsoleEmailBackend
from workers.pipeline.evidence_lane import EvidenceLaneWorker

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine)

client = TestClient(app)


def override_get_db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    app.dependency_overrides.clear()


def _seed_event(session, event_id="evt-alert-1", headline="Star forward to sign"):
    ev = EventModel(
        id=event_id,
        headline=headline,
        status="rumour",
        independent_sources=1,
        sport="Football",
        competition="Premier League",
        summary="A developing story.",
        source_url="https://example.com",
    )
    session.add(ev)
    session.commit()
    return ev


# --- Email backend --------------------------------------------------------


def test_console_backend_records_and_writes_outbox(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    backend = ConsoleEmailBackend()
    from packages.notifications.email_backend import EmailMessage

    msg = EmailMessage(to="reader@example.com", subject="Test", body_text="Hello")
    assert backend.send(msg) is True
    assert len(backend.sent) == 1
    assert backend.sent[0].to == "reader@example.com"
    assert (tmp_path / "data" / "emails").exists()


# --- Repository -------------------------------------------------------------


def test_subscribe_is_idempotent():
    with TestSession() as session:
        _seed_event(session)
        rec1 = NotificationsRepository.subscribe(session, "reader@example.com", "evt-alert-1")
        rec2 = NotificationsRepository.subscribe(session, "READER@example.com", "evt-alert-1")
        assert rec1.id == rec2.id
        assert NotificationsRepository.get_subscriber_emails(session, "evt-alert-1") == ["reader@example.com"]


def test_unsubscribe_removes_subscription():
    with TestSession() as session:
        _seed_event(session)
        NotificationsRepository.subscribe(session, "reader@example.com", "evt-alert-1")
        removed = NotificationsRepository.unsubscribe(session, "reader@example.com", "evt-alert-1")
        assert removed is True
        assert NotificationsRepository.get_subscriber_emails(session, "evt-alert-1") == []


# --- Dispatcher: the core behaviour ------------------------------------------


def test_dispatcher_sends_immediately_to_pro_subscriber():
    backend = ConsoleEmailBackend()
    dispatcher = NotificationDispatcher(email_backend=backend)

    with TestSession() as session:
        _seed_event(session)
        NotificationsRepository.subscribe(session, "pro-reader@example.com", "evt-alert-1")
        BillingRepository.upsert_entitlement(session, email="pro-reader@example.com", status="active", is_pro=True)

        result = dispatcher.dispatch_status_change(
            session, event_id="evt-alert-1", headline="Star forward to sign", old_status="rumour", new_status="confirmed"
        )

    assert result == {"immediate": 1, "queued": 0}
    assert len(backend.sent) == 1
    assert backend.sent[0].to == "pro-reader@example.com"
    assert "confirmed" in backend.sent[0].body_text


def test_dispatcher_queues_digest_for_free_subscriber():
    backend = ConsoleEmailBackend()
    dispatcher = NotificationDispatcher(email_backend=backend)

    with TestSession() as session:
        _seed_event(session)
        NotificationsRepository.subscribe(session, "free-reader@example.com", "evt-alert-1")
        # No entitlement record at all — must fail safe to Free, not fail open to Pro.

        result = dispatcher.dispatch_status_change(
            session, event_id="evt-alert-1", headline="Star forward to sign", old_status="rumour", new_status="confirmed"
        )

    assert result == {"immediate": 0, "queued": 1}
    assert len(backend.sent) == 0

    with TestSession() as session:
        pending = NotificationsRepository.get_pending_digest_items(session, "free-reader@example.com")
        assert len(pending) == 1
        assert pending[0].new_status == "confirmed"


def test_dispatcher_no_op_when_status_unchanged():
    dispatcher = NotificationDispatcher(email_backend=ConsoleEmailBackend())
    with TestSession() as session:
        _seed_event(session)
        NotificationsRepository.subscribe(session, "reader@example.com", "evt-alert-1")
        result = dispatcher.dispatch_status_change(session, event_id="evt-alert-1", headline="x", old_status="rumour", new_status="rumour")
    assert result == {"immediate": 0, "queued": 0}


def test_dispatcher_past_due_pro_treated_as_free():
    """A lapsed Pro subscription (status != active) must not get real-time delivery."""
    backend = ConsoleEmailBackend()
    dispatcher = NotificationDispatcher(email_backend=backend)

    with TestSession() as session:
        _seed_event(session)
        NotificationsRepository.subscribe(session, "lapsed@example.com", "evt-alert-1")
        BillingRepository.upsert_entitlement(session, email="lapsed@example.com", status="past_due", is_pro=True)

        result = dispatcher.dispatch_status_change(
            session, event_id="evt-alert-1", headline="x", old_status="rumour", new_status="confirmed"
        )

    assert result == {"immediate": 0, "queued": 1}


# --- API endpoints ------------------------------------------------------------


def test_subscribe_and_list_endpoint():
    with TestSession() as session:
        _seed_event(session)

    resp = client.post("/api/v1/alerts/subscribe", json={"email": "api-reader@example.com", "event_id": "evt-alert-1"})
    assert resp.status_code == 200
    assert resp.json()["subscribed"] is True

    list_resp = client.get("/api/v1/alerts/subscriptions/api-reader@example.com")
    assert list_resp.status_code == 200
    assert list_resp.json()["event_ids"] == ["evt-alert-1"]


def test_unsubscribe_endpoint():
    with TestSession() as session:
        _seed_event(session)

    client.post("/api/v1/alerts/subscribe", json={"email": "api-reader2@example.com", "event_id": "evt-alert-1"})
    resp = client.post("/api/v1/alerts/unsubscribe", json={"email": "api-reader2@example.com", "event_id": "evt-alert-1"})
    assert resp.status_code == 200
    assert resp.json()["unsubscribed"] is True

    list_resp = client.get("/api/v1/alerts/subscriptions/api-reader2@example.com")
    assert list_resp.json()["event_ids"] == []


# --- End-to-end: the evidence lane actually triggers a real dispatch ---------


def test_evidence_lane_status_change_notifies_subscribers():
    """The wiring in workers/pipeline/evidence_lane.py, not just the dispatcher in isolation."""
    with TestSession() as session:
        source = SourceModel(id="src-e2e-alert", name="Club Official", source_type="official", wilson_lower_bound=0.98)
        session.add(source)
        session.flush()

        event = EventModel(
            id="evt-e2e-alert",
            headline="Star forward completes move",
            summary="Developing",
            status="rumour",
            sport="football",
            competition="Premier League",
            source_url="https://example.com/e2e",
        )
        session.add(event)
        session.flush()

        claim = ClaimModel(
            id="clm-e2e-alert",
            event_id="evt-e2e-alert",
            source_id=source.id,
            source=source,
            claim_text="Club officially confirms the signing.",
            subject_id="Player",
            predicate="official_signing",
            object_id="Club",
            evidence_span="Club officially confirms the signing.",
            attribution="Club Official",
            attribution_type="first_party",
            original_url="https://example.com/e2e-1",
        )
        session.add(claim)
        session.commit()

        NotificationsRepository.subscribe(session, "watcher@example.com", "evt-e2e-alert")
        BillingRepository.upsert_entitlement(session, email="watcher@example.com", status="active", is_pro=True)

        backend = ConsoleEmailBackend()
        worker = EvidenceLaneWorker(
            session=session,
            cost_tracker=CostTracker(),
            notification_dispatcher=NotificationDispatcher(email_backend=backend),
        )
        result = worker.evaluate_and_publish_event(event_id="evt-e2e-alert", trace_id="trc-e2e-alert")

        assert result["status"] != "rumour"
        assert len(backend.sent) == 1
        assert backend.sent[0].to == "watcher@example.com"


# --- The daily digest script itself ------------------------------------------


def test_send_daily_digests_script_batches_and_marks_sent(monkeypatch):
    import scripts.send_daily_digests as digest_script

    monkeypatch.setattr(digest_script, "SessionLocal", TestSession)
    backend = ConsoleEmailBackend()
    monkeypatch.setattr(digest_script, "get_default_email_backend", lambda: backend)

    with TestSession() as session:
        _seed_event(session, event_id="evt-digest-1", headline="Story A")
        _seed_event(session, event_id="evt-digest-2", headline="Story B")
        NotificationsRepository.queue_digest_item(
            session,
            email="digest-reader@example.com",
            event_id="evt-digest-1",
            headline="Story A",
            old_status="rumour",
            new_status="confirmed",
        )
        NotificationsRepository.queue_digest_item(
            session,
            email="digest-reader@example.com",
            event_id="evt-digest-2",
            headline="Story B",
            old_status="developing",
            new_status="disputed",
        )

    exit_code = digest_script.main()
    assert exit_code == 0
    assert len(backend.sent) == 1  # one batched email, not two
    assert "Story A" in backend.sent[0].body_text
    assert "Story B" in backend.sent[0].body_text

    with TestSession() as session:
        assert NotificationsRepository.get_pending_digest_items(session, "digest-reader@example.com") == []
