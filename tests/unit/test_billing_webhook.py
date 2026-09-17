import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.routers.billing import PADDLE_WEBHOOK_SECRET


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _compute_signature(payload_bytes: bytes, secret: str = PADDLE_WEBHOOK_SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def test_billing_plans_list(client):
    resp = client.get("/api/v1/billing/plans")
    assert resp.status_code == 200
    plans = resp.json()
    assert len(plans) == 2
    assert any(p["id"] == "plan_pro_monthly" and p["price_gbp"] == 6.00 for p in plans)
    assert any(p["id"] == "plan_pro_annual" and p["price_gbp"] == 45.00 for p in plans)


def test_default_free_entitlements(client):
    resp = client.get("/api/v1/billing/entitlements/new_user_123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_pro"] is False
    assert data["watchlist_limit"] == 3
    assert data["has_realtime_alerts"] is False
    assert data["has_export"] is False


def test_billing_webhook_subscription_flow_and_idempotency(client):
    customer_id = "cust_verified_pro_user"
    event_id = "evt_paddle_sub_created_999"

    payload = {
        "event_id": event_id,
        "event_type": "subscription.created",
        "data": {
            "customer_id": customer_id,
            "email": "subscriber@example.com",
            "plan_id": "plan_pro_annual",
        },
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = _compute_signature(payload_bytes)

    # 1. Invalid signature rejected
    bad_resp = client.post(
        "/api/v1/billing/webhook",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "Paddle-Signature": "invalid_sig_abc"},
    )
    assert bad_resp.status_code == 401
    assert "Invalid webhook signature" in bad_resp.json()["detail"]

    # 2. Valid webhook processes successfully
    good_resp = client.post(
        "/api/v1/billing/webhook",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "Paddle-Signature": sig},
    )
    assert good_resp.status_code == 200
    assert good_resp.json()["status"] == "success"
    assert good_resp.json()["action"] == "subscription_activated"

    # 3. Customer entitlement upgraded
    ent_resp = client.get(f"/api/v1/billing/entitlements/{customer_id}")
    assert ent_resp.status_code == 200
    assert ent_resp.json()["is_pro"] is True
    assert ent_resp.json()["plan_id"] == "plan_pro_annual"
    assert ent_resp.json()["has_realtime_alerts"] is True
    assert ent_resp.json()["has_export"] is True

    # 4. Replaying identical event is idempotent no-op
    replay_resp = client.post(
        "/api/v1/billing/webhook",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "Paddle-Signature": sig},
    )
    assert replay_resp.status_code == 200
    assert replay_resp.json()["status"] == "duplicate_ignored"
    assert replay_resp.json()["action"] == "noop"

    # 5. Cancellation event downgrades customer
    cancel_payload = {
        "event_id": "evt_paddle_sub_canceled_1000",
        "event_type": "subscription.canceled",
        "data": {
            "customer_id": customer_id,
        },
    }
    cancel_bytes = json.dumps(cancel_payload).encode("utf-8")
    cancel_sig = _compute_signature(cancel_bytes)

    cancel_resp = client.post(
        "/api/v1/billing/webhook",
        content=cancel_bytes,
        headers={"Content-Type": "application/json", "Paddle-Signature": cancel_sig},
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["action"] == "subscription_canceled"

    # Verify downgraded
    ent_resp2 = client.get(f"/api/v1/billing/entitlements/{customer_id}")
    assert ent_resp2.json()["is_pro"] is False
    assert ent_resp2.json()["status"] == "canceled"
