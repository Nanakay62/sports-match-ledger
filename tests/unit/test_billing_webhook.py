import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.billing.stripe_client import CheckoutSession, verify_stripe_signature
from apps.api.app.main import app
from apps.api.app.routers import billing as billing_router
from packages.database.models import Base
from packages.database.session import get_db

TEST_WEBHOOK_SECRET = "whsec_test_secret_for_ci"

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)


def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database(monkeypatch):
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(billing_router, "STRIPE_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
    yield
    app.dependency_overrides.clear()


def _stripe_signature_header(payload_bytes: bytes, secret: str = TEST_WEBHOOK_SECRET, timestamp: int | None = None) -> str:
    ts = timestamp if timestamp is not None else int(time.time())
    signed_payload = f"{ts}.{payload_bytes.decode('utf-8')}".encode()
    sig = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _checkout_completed_event(event_id: str, email: str, customer_id: str, subscription_id: str) -> dict:
    return {
        "id": event_id,
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "mode": "subscription",
                "customer": customer_id,
                "subscription": subscription_id,
                "customer_email": email,
                "client_reference_id": "plan_pro_annual",
            }
        },
    }


def _subscription_deleted_event(event_id: str, customer_id: str) -> dict:
    return {
        "id": event_id,
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": customer_id, "status": "canceled"}},
    }


def test_billing_plans_list():
    resp = client.get("/api/v1/billing/plans")
    assert resp.status_code == 200
    plans = resp.json()
    assert len(plans) == 2
    assert any(p["id"] == "plan_pro_monthly" and p["price_gbp"] == 6.00 for p in plans)
    assert any(p["id"] == "plan_pro_annual" and p["price_gbp"] == 45.00 for p in plans)


def test_default_free_entitlements():
    resp = client.get("/api/v1/billing/entitlements/new_user@example.com")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_pro"] is False
    assert data["watchlist_limit"] == 3
    assert data["has_realtime_alerts"] is False
    assert data["has_export"] is False


def test_verify_stripe_signature_accepts_valid_and_rejects_tampered():
    payload = json.dumps({"id": "evt_1", "type": "ping"}).encode("utf-8")
    header = _stripe_signature_header(payload)

    assert verify_stripe_signature(payload, header, TEST_WEBHOOK_SECRET) is True
    assert verify_stripe_signature(payload, header, "wrong_secret") is False
    assert verify_stripe_signature(b'{"id": "evt_1", "type": "tampered"}', header, TEST_WEBHOOK_SECRET) is False
    assert verify_stripe_signature(payload, "t=123,v1=not_a_real_signature", TEST_WEBHOOK_SECRET) is False
    assert verify_stripe_signature(payload, None, TEST_WEBHOOK_SECRET) is False


def test_verify_stripe_signature_rejects_stale_timestamp_replay():
    payload = json.dumps({"id": "evt_replay"}).encode("utf-8")
    old_header = _stripe_signature_header(payload, timestamp=int(time.time()) - 3600)
    assert verify_stripe_signature(payload, old_header, TEST_WEBHOOK_SECRET) is False


def test_webhook_rejects_invalid_signature():
    payload = _checkout_completed_event("evt_bad_sig", "user@example.com", "cus_1", "sub_1")
    payload_bytes = json.dumps(payload).encode("utf-8")

    resp = client.post(
        "/api/v1/billing/webhook",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "Stripe-Signature": "t=1,v1=invalid"},
    )
    assert resp.status_code == 401


def test_webhook_subscription_lifecycle_and_idempotency():
    email = "subscriber@example.com"
    customer_id = "cus_verified_pro_user"
    subscription_id = "sub_abc123"

    payload = _checkout_completed_event("evt_checkout_completed_999", email, customer_id, subscription_id)
    payload_bytes = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Stripe-Signature": _stripe_signature_header(payload_bytes)}

    # 1. Valid webhook processes successfully
    good_resp = client.post("/api/v1/billing/webhook", content=payload_bytes, headers=headers)
    assert good_resp.status_code == 200
    assert good_resp.json()["status"] == "success"
    assert good_resp.json()["action"] == "subscription_activated"

    # 2. Entitlement upgraded, looked up by email
    ent_resp = client.get(f"/api/v1/billing/entitlements/{email}")
    assert ent_resp.status_code == 200
    assert ent_resp.json()["is_pro"] is True
    assert ent_resp.json()["has_realtime_alerts"] is True
    assert ent_resp.json()["has_export"] is True

    # 3. Replaying the identical event is an idempotent no-op
    replay_resp = client.post("/api/v1/billing/webhook", content=payload_bytes, headers=headers)
    assert replay_resp.status_code == 200
    assert replay_resp.json()["status"] == "duplicate_ignored"
    assert replay_resp.json()["action"] == "noop"

    # 4. Subscription deleted downgrades the same customer
    cancel_payload = _subscription_deleted_event("evt_sub_deleted_1000", customer_id)
    cancel_bytes = json.dumps(cancel_payload).encode("utf-8")
    cancel_headers = {"Content-Type": "application/json", "Stripe-Signature": _stripe_signature_header(cancel_bytes)}

    cancel_resp = client.post("/api/v1/billing/webhook", content=cancel_bytes, headers=cancel_headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["action"] == "subscription_canceled"

    ent_resp2 = client.get(f"/api/v1/billing/entitlements/{email}")
    assert ent_resp2.json()["is_pro"] is False
    assert ent_resp2.json()["status"] == "canceled"


def test_checkout_requires_configured_price_id(monkeypatch):
    monkeypatch.delenv("STRIPE_PRICE_ID_MONTHLY", raising=False)
    resp = client.post("/api/v1/billing/checkout", json={"plan_id": "plan_pro_monthly", "email": "a@example.com"})
    assert resp.status_code == 503


def test_checkout_creates_session_via_stripe_client(monkeypatch):
    monkeypatch.setenv("STRIPE_PRICE_ID_MONTHLY", "price_test_monthly_123")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_dummy")

    captured: dict = {}

    def fake_create_checkout_session(self, price_id, success_url, cancel_url, customer_email=None, client_reference_id=None):
        captured["price_id"] = price_id
        captured["customer_email"] = customer_email
        return CheckoutSession(session_id="cs_test_123", url="https://checkout.stripe.com/test-session")

    monkeypatch.setattr(
        "apps.api.app.routers.billing.StripeClient.create_checkout_session",
        fake_create_checkout_session,
    )

    resp = client.post("/api/v1/billing/checkout", json={"plan_id": "plan_pro_monthly", "email": "buyer@example.com"})
    assert resp.status_code == 200
    assert resp.json()["checkout_url"] == "https://checkout.stripe.com/test-session"
    assert captured["price_id"] == "price_test_monthly_123"
    assert captured["customer_email"] == "buyer@example.com"


def test_portal_requires_existing_customer():
    resp = client.post("/api/v1/billing/portal", json={"email": "never-subscribed@example.com"})
    assert resp.status_code == 404
