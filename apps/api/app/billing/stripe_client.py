"""Minimal Stripe REST client and webhook signature verification (Handbook §18.2).

Uses httpx (already a project dependency) to call Stripe's REST API directly rather
than adding the `stripe` SDK — the surface needed here (create a Checkout Session,
create a Billing Portal session, verify a webhook signature) is small and this keeps
the dependency footprint the same as the rest of the project's AI Gateway modules,
which already make raw HTTP calls (see packages/ai/translation.py).

Sandbox by default: STRIPE_SECRET_KEY should be a `sk_test_...` key during development.
Nothing here distinguishes test vs live mode — that is entirely determined by which
key is configured, exactly as Stripe intends.
"""

import hashlib
import hmac
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

STRIPE_API_BASE = "https://api.stripe.com/v1"

# Stripe tolerates minor clock drift between servers but rejects an old signed
# payload as a replay-attack defence. 5 minutes is Stripe's own documented default.
WEBHOOK_TOLERANCE_SECONDS = 300


class StripeConfigError(RuntimeError):
    """Raised when a Stripe operation is attempted without the required env var set."""


class StripeAPIError(RuntimeError):
    """Raised when the Stripe API returns a non-2xx response."""

    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Stripe API error {status_code}: {body}")


def _flatten_for_form(prefix: str, value: Any, out: dict[str, str]) -> None:
    """Stripe's API takes application/x-www-form-urlencoded bodies with bracket-nested
    keys for arrays/objects, e.g. line_items[0][price]=price_x. Flattens nested
    dict/list structures into that wire format.
    """
    if isinstance(value, dict):
        for k, v in value.items():
            _flatten_for_form(f"{prefix}[{k}]", v, out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _flatten_for_form(f"{prefix}[{i}]", v, out)
    elif value is not None:
        out[prefix] = str(value)


def encode_stripe_form(params: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in params.items():
        _flatten_for_form(key, value, out)
    return out


@dataclass
class CheckoutSession:
    session_id: str
    url: str


@dataclass
class BillingPortalSession:
    url: str


class StripeClient:
    """Thin wrapper over the Stripe REST API for subscription checkout and self-service billing."""

    def __init__(self, secret_key: str | None = None, timeout_seconds: float = 10.0):
        self.secret_key = secret_key or os.getenv("STRIPE_SECRET_KEY")
        self.timeout_seconds = timeout_seconds

    def _post(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.secret_key:
            raise StripeConfigError("STRIPE_SECRET_KEY is not configured")

        form_body = encode_stripe_form(params)
        response = httpx.post(
            f"{STRIPE_API_BASE}/{path}",
            data=form_body,
            auth=(self.secret_key, ""),
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            raise StripeAPIError(response.status_code, response.text)
        result: dict[str, Any] = response.json()
        return result

    def create_checkout_session(
        self,
        price_id: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None = None,
        client_reference_id: str | None = None,
    ) -> CheckoutSession:
        """Creates a Stripe-hosted Checkout Session for a subscription plan (Handbook §18.2/§18.4)."""
        params: dict[str, Any] = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "allow_promotion_codes": "true",
        }
        if customer_email:
            params["customer_email"] = customer_email
        if client_reference_id:
            params["client_reference_id"] = client_reference_id

        data = self._post("checkout/sessions", params)
        return CheckoutSession(session_id=data["id"], url=data["url"])

    def create_billing_portal_session(self, stripe_customer_id: str, return_url: str) -> BillingPortalSession:
        """Creates a Stripe Billing Portal session so a user can cancel or change plan
        without contacting support (Handbook §18.2: "never dark-pattern the cancellation").
        """
        data = self._post(
            "billing_portal/sessions",
            {"customer": stripe_customer_id, "return_url": return_url},
        )
        return BillingPortalSession(url=data["url"])


def verify_stripe_signature(
    payload: bytes,
    signature_header: str | None,
    webhook_secret: str,
    tolerance_seconds: int = WEBHOOK_TOLERANCE_SECONDS,
) -> bool:
    """Verifies a Stripe webhook signature per Stripe's documented scheme.

    Header format: "t=<timestamp>,v1=<signature>[,v0=<legacy signature>]"
    Signed payload: "{timestamp}.{raw_body}", HMAC-SHA256 with the webhook secret.
    Rejects payloads outside the tolerance window as a replay-attack defence.
    """
    if not signature_header:
        return False

    parts: dict[str, str] = {}
    for item in signature_header.split(","):
        if "=" not in item:
            continue
        k, _, v = item.partition("=")
        parts.setdefault(k.strip(), v.strip())

    timestamp_raw = parts.get("t")
    signature = parts.get("v1")
    if not timestamp_raw or not signature:
        return False

    try:
        timestamp = int(timestamp_raw)
    except ValueError:
        return False

    if tolerance_seconds > 0 and abs(time.time() - timestamp) > tolerance_seconds:
        return False

    signed_payload = f"{timestamp_raw}.{payload.decode('utf-8')}".encode()
    expected_signature = hmac.new(webhook_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected_signature, signature)
