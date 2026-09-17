import hashlib
import hmac
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/billing", tags=["billing"])

PADDLE_WEBHOOK_SECRET = os.getenv("PADDLE_WEBHOOK_SECRET", "test_webhook_secret_xyz")

# Memory/Cache store of processed webhook event IDs for idempotency
_PROCESSED_WEBHOOK_EVENT_IDS: set[str] = set()

# In-memory mock entitlement table: customer_id/email -> entitlement record
_CUSTOMER_ENTITLEMENTS: dict[str, dict[str, Any]] = {}


class BillingPlan(BaseModel):
    id: str
    name: str
    interval: str
    price_gbp: float
    price_formatted: str
    features: list[str]


class WebhookResponse(BaseModel):
    status: str
    event_id: str
    action: str
    message: str | None = None


class UserEntitlementResponse(BaseModel):
    customer_id: str
    email: str | None
    is_pro: bool
    plan_id: str | None
    status: str
    watchlist_limit: int
    has_realtime_alerts: bool
    has_full_history: bool
    has_export: bool


@router.get("/plans", response_model=list[BillingPlan])
def get_billing_plans() -> list[BillingPlan]:
    """Returns available Pro subscription plans matching handbook economics (§3)."""
    return [
        BillingPlan(
            id="plan_pro_monthly",
            name="Pro Monthly",
            interval="month",
            price_gbp=6.00,
            price_formatted="£6.00/month",
            features=[
                "Unlimited watchlist topics",
                "Real-time alerts via push & email",
                "Full rumour lifecycle archive (unlimited history)",
                "Data export (CSV & JSON)",
                "Original-language source viewing",
            ],
        ),
        BillingPlan(
            id="plan_pro_annual",
            name="Pro Annual",
            interval="year",
            price_gbp=45.00,
            price_formatted="£45.00/year (< 8 months billing)",
            features=[
                "All Pro Monthly features",
                "4.5 months free compared to monthly",
                "Founding member badge",
                "Priority human review request",
            ],
        ),
    ]


@router.get("/entitlements/{customer_id}", response_model=UserEntitlementResponse)
def get_user_entitlements(customer_id: str) -> UserEntitlementResponse:
    """Retrieve active entitlements for a given customer or email."""
    record = _CUSTOMER_ENTITLEMENTS.get(customer_id)
    if not record:
        # Default Free tier
        return UserEntitlementResponse(
            customer_id=customer_id,
            email=None,
            is_pro=False,
            plan_id=None,
            status="free",
            watchlist_limit=3,
            has_realtime_alerts=False,
            has_full_history=False,
            has_export=False,
        )

    return UserEntitlementResponse(
        customer_id=customer_id,
        email=record.get("email"),
        is_pro=record.get("is_pro", False),
        plan_id=record.get("plan_id"),
        status=record.get("status", "active"),
        watchlist_limit=99999 if record.get("is_pro") else 3,
        has_realtime_alerts=record.get("is_pro", False),
        has_full_history=record.get("is_pro", False),
        has_export=record.get("is_pro", False),
    )


@router.post("/webhook", response_model=WebhookResponse)
async def process_billing_webhook(
    request: Request,
    paddle_signature: str | None = Header(default=None, alias="Paddle-Signature"),
) -> WebhookResponse:
    """Idempotent merchant-of-record webhook handler.
    Validates HMAC signature and updates customer entitlements without duplicates.
    """
    raw_body = await request.body()

    # Verify HMAC-SHA256 signature if secret is configured and not testing bypass
    if PADDLE_WEBHOOK_SECRET and paddle_signature:
        expected_sig = hmac.new(
            PADDLE_WEBHOOK_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, paddle_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )
    elif PADDLE_WEBHOOK_SECRET and not paddle_signature and os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Paddle-Signature header",
        )

    try:
        payload = await request.json()
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from err

    event_id = payload.get("event_id")
    event_type = payload.get("event_type", "subscription.created")
    data = payload.get("data", {})

    if not event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook payload missing required 'event_id'",
        )

    # Idempotency check: if event_id has already been processed, exit safely
    if event_id in _PROCESSED_WEBHOOK_EVENT_IDS:
        return WebhookResponse(
            status="duplicate_ignored",
            event_id=event_id,
            action="noop",
            message="Webhook event previously processed",
        )

    # Process entitlement update based on event_type
    customer_id = data.get("customer_id") or data.get("email") or "cust_default"
    email = data.get("email")
    plan_id = data.get("plan_id", "plan_pro_monthly")

    if event_type in {"subscription.created", "subscription.updated", "subscription.activated"}:
        _CUSTOMER_ENTITLEMENTS[customer_id] = {
            "customer_id": customer_id,
            "email": email,
            "is_pro": True,
            "plan_id": plan_id,
            "status": "active",
        }
        action = "subscription_activated"
    elif event_type in {"subscription.canceled", "subscription.expired"}:
        if customer_id in _CUSTOMER_ENTITLEMENTS:
            _CUSTOMER_ENTITLEMENTS[customer_id]["is_pro"] = False
            _CUSTOMER_ENTITLEMENTS[customer_id]["status"] = "canceled"
        action = "subscription_canceled"
    else:
        action = "event_recorded"

    _PROCESSED_WEBHOOK_EVENT_IDS.add(event_id)

    return WebhookResponse(
        status="success",
        event_id=event_id,
        action=action,
        message=f"Successfully processed {event_type}",
    )
