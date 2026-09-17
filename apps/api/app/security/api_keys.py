import os
from dataclasses import dataclass
from enum import StrEnum

from fastapi import Header, HTTPException, status


class APIKeyTier(StrEnum):
    ANONYMOUS = "anonymous"
    DEVELOPER = "developer"
    COMMERCIAL_PRO = "commercial_pro"


@dataclass
class APIClient:
    api_key: str | None
    tier: APIKeyTier
    rate_limit_per_minute: int
    monthly_quota: int
    is_authenticated: bool


KNOWN_KEYS: dict[str, APIKeyTier] = {
    "dev_test_key_123": APIKeyTier.DEVELOPER,
    "pro_test_key_456": APIKeyTier.COMMERCIAL_PRO,
}

# Allow adding keys via environment variable comma-separated pairs: KEY:TIER
env_keys = os.getenv("API_KEYS_CONFIG", "")
if env_keys:
    for item in env_keys.split(","):
        if ":" in item:
            k, t = item.strip().split(":", 1)
            if t == "commercial_pro":
                KNOWN_KEYS[k] = APIKeyTier.COMMERCIAL_PRO
            elif t == "developer":
                KNOWN_KEYS[k] = APIKeyTier.DEVELOPER


def get_api_client(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> APIClient:
    """FastAPI dependency to extract and validate caller API key and tier.
    Preserves free unauthenticated access for standard clients while enforcing
    tier metadata on authenticated requests.
    """
    if not x_api_key:
        return APIClient(
            api_key=None,
            tier=APIKeyTier.ANONYMOUS,
            rate_limit_per_minute=60,
            monthly_quota=1000,
            is_authenticated=False,
        )

    # Check known keys dict or prefix patterns
    tier = KNOWN_KEYS.get(x_api_key)
    if not tier:
        if x_api_key.startswith("sk_pro_"):
            tier = APIKeyTier.COMMERCIAL_PRO
        elif x_api_key.startswith("sk_dev_"):
            tier = APIKeyTier.DEVELOPER
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key provided in X-API-Key header",
            )

    if tier == APIKeyTier.COMMERCIAL_PRO:
        return APIClient(
            api_key=x_api_key,
            tier=tier,
            rate_limit_per_minute=1200,
            monthly_quota=50000,
            is_authenticated=True,
        )
    else:
        return APIClient(
            api_key=x_api_key,
            tier=tier,
            rate_limit_per_minute=300,
            monthly_quota=3000,
            is_authenticated=True,
        )
