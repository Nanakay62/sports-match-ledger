import os
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from packages.database.billing_repository import (
    FREE_WATCHLIST_LIMIT,
    PRO_WATCHLIST_LIMIT,
    VALID_ACTIONS,
    VALID_WALL_IDS,
    BillingRepository,
)
from packages.database.session import get_db

from ..billing.stripe_client import StripeAPIError, StripeClient, StripeConfigError, verify_stripe_signature

router = APIRouter(prefix="/billing", tags=["billing"])

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")

PLAN_PRICE_ENV_VARS: dict[str, str] = {
    "plan_pro_monthly": "STRIPE_PRICE_ID_MONTHLY",
    "plan_pro_annual": "STRIPE_PRICE_ID_ANNUAL",
}


class BillingPlan(BaseModel):
    id: str
    name: str
    interval: str
    price_gbp: float
    price_formatted: str
    features: list[str]


class WebhookResponse(BaseModel):
    status: str
    event_id: str | None = None
    action: str
    message: str | None = None


class UserEntitlementResponse(BaseModel):
    email: str
    is_pro: bool
    plan_id: str | None
    status: str
    watchlist_limit: int
    has_realtime_alerts: bool
    has_full_history: bool
    has_export: bool


class CheckoutRequest(BaseModel):
    plan_id: str
    email: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalRequest(BaseModel):
    email: str


class PortalResponse(BaseModel):
    portal_url: str


class PaywallEventRequest(BaseModel):
    wall_id: str
    action: str
    email: str | None = None
    context: str | None = None


class PaywallEventAck(BaseModel):
    recorded: bool


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


def _entitlement_response(email: str, record: Any) -> UserEntitlementResponse:
    if record is None:
        return UserEntitlementResponse(
            email=email,
            is_pro=False,
            plan_id=None,
            status="free",
            watchlist_limit=FREE_WATCHLIST_LIMIT,
            has_realtime_alerts=False,
            has_full_history=False,
            has_export=False,
        )
    return UserEntitlementResponse(
        email=record.email,
        is_pro=record.is_pro,
        plan_id=record.plan_id,
        status=record.status,
        watchlist_limit=PRO_WATCHLIST_LIMIT if record.is_pro else FREE_WATCHLIST_LIMIT,
        has_realtime_alerts=record.is_pro,
        has_full_history=record.is_pro,
        has_export=record.is_pro,
    )


@router.get("/entitlements/{email}", response_model=UserEntitlementResponse)
def get_user_entitlements(email: str, db: Session = Depends(get_db)) -> UserEntitlementResponse:
    """Retrieve active entitlements for a given email. Reads only ever the persisted
    table the Stripe webhook writes — never trusts anything the client supplies.
    """
    record = BillingRepository.get_entitlement_by_email(db, email)
    return _entitlement_response(email, record)


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(req: CheckoutRequest) -> CheckoutResponse:
    """Creates a Stripe-hosted Checkout Session for the requested plan (Handbook §18.4)."""
    price_env_var = PLAN_PRICE_ENV_VARS.get(req.plan_id)
    if not price_env_var:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown plan_id '{req.plan_id}'")

    price_id = os.getenv(price_env_var)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Billing is not configured: {price_env_var} is not set",
        )

    try:
        client = StripeClient()
        session_obj = client.create_checkout_session(
            price_id=price_id,
            success_url=f"{FRONTEND_BASE_URL}/pro?checkout=success",
            cancel_url=f"{FRONTEND_BASE_URL}/pro?checkout=cancelled",
            customer_email=req.email,
            client_reference_id=req.email,
        )
    except StripeConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except StripeAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return CheckoutResponse(checkout_url=session_obj.url)


@router.post("/portal", response_model=PortalResponse)
def create_billing_portal(req: PortalRequest, db: Session = Depends(get_db)) -> PortalResponse:
    """Creates a Stripe Billing Portal link so a user can change or cancel their own
    subscription with no support ticket required (Handbook §18.2: never dark-pattern
    the cancellation).
    """
    record = BillingRepository.get_entitlement_by_email(db, req.email)
    if record is None or not record.stripe_customer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No billing account found for this email")

    try:
        client = StripeClient()
        portal = client.create_billing_portal_session(
            stripe_customer_id=record.stripe_customer_id,
            return_url=f"{FRONTEND_BASE_URL}/pro",
        )
    except StripeConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except StripeAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return PortalResponse(portal_url=portal.url)


@router.post("/webhook", response_model=WebhookResponse)
async def process_billing_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
) -> WebhookResponse:
    """Idempotent Stripe webhook handler. Validates the signature, then updates the
    persisted entitlement table without ever trusting a duplicate delivery twice.
    """
    raw_body = await request.body()

    if STRIPE_WEBHOOK_SECRET:
        if not verify_stripe_signature(raw_body, stripe_signature, STRIPE_WEBHOOK_SECRET):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")
    elif os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="STRIPE_WEBHOOK_SECRET is not configured")

    try:
        payload = await request.json()
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from err

    event_id = payload.get("id")
    event_type = payload.get("type", "")
    data_object = payload.get("data", {}).get("object", {})

    if not event_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook payload missing required 'id'")

    if BillingRepository.is_webhook_event_processed(db, event_id):
        return WebhookResponse(status="duplicate_ignored", event_id=event_id, action="noop", message="Event previously processed")

    action = "event_recorded"

    if event_type == "checkout.session.completed" and data_object.get("mode") == "subscription":
        email = data_object.get("customer_email") or data_object.get("customer_details", {}).get("email")
        customer_id = data_object.get("customer")
        subscription_id = data_object.get("subscription")
        if email:
            BillingRepository.upsert_entitlement(
                db,
                email=email,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                plan_id=data_object.get("client_reference_id"),
                status="active",
                is_pro=True,
            )
            action = "subscription_activated"

    elif event_type in {"customer.subscription.updated", "customer.subscription.created"}:
        customer_id = data_object.get("customer")
        sub_status = data_object.get("status", "active")
        record = BillingRepository.get_entitlement_by_stripe_customer_id(db, customer_id) if customer_id else None
        if record:
            is_pro = sub_status in {"active", "trialing"}
            BillingRepository.upsert_entitlement(
                db,
                email=record.email,
                stripe_customer_id=customer_id,
                stripe_subscription_id=data_object.get("id"),
                status=sub_status,
                is_pro=is_pro,
            )
            action = "subscription_updated"

    elif event_type == "customer.subscription.deleted":
        customer_id = data_object.get("customer")
        record = BillingRepository.get_entitlement_by_stripe_customer_id(db, customer_id) if customer_id else None
        if record:
            BillingRepository.upsert_entitlement(
                db,
                email=record.email,
                stripe_customer_id=customer_id,
                status="canceled",
                is_pro=False,
            )
            action = "subscription_canceled"

    BillingRepository.mark_webhook_event_processed(db, event_id, event_type)

    return WebhookResponse(status="success", event_id=event_id, action=action, message=f"Successfully processed {event_type}")


@router.post("/paywall-events", response_model=PaywallEventAck)
def record_paywall_event(req: PaywallEventRequest, db: Session = Depends(get_db)) -> PaywallEventAck:
    """Records a paywall impression or click for per-wall conversion measurement
    (Handbook §18.3/§18.5). wall_id and action are validated against a fixed set so a
    frontend typo fails loudly here rather than silently corrupting the conversion data.
    """
    if req.wall_id not in VALID_WALL_IDS or req.action not in VALID_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"wall_id must be one of {sorted(VALID_WALL_IDS)}, action must be one of {sorted(VALID_ACTIONS)}",
        )
    BillingRepository.record_paywall_event(db, wall_id=req.wall_id, action=req.action, email=req.email, context=req.context)
    return PaywallEventAck(recorded=True)
