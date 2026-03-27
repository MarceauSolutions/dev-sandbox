"""
Fitness-Influencer Tower — Infra Routes
Extracted from main.py monolith. 2 routes.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

router = APIRouter()


# ============================================================================
# Rate Limiting and Quota Endpoints (v2.0)
# ============================================================================

@router.get("/api/quota/status")
@limiter.limit("60/minute")
async def get_user_quota_status(request: Request):
    """
    Get current quota status for the authenticated user.

    Returns usage counts, limits, and reset time for all quota types.
    Rate limit headers included in response.
    """
    status = await get_quota_status(request)

    # Build response with headers
    response = JSONResponse(content=status)

    # Add rate limit headers
    headers = get_rate_limit_headers(request)
    for key, value in headers.items():
        response.headers[key] = value

    return response


@router.get("/api/quota/tiers")
async def get_quota_tiers():
    """
    Get available subscription tiers and their limits.

    Returns all tiers with their quota limits and rate limits.
    """
    from backend.rate_limiter import TIER_QUOTAS, TIER_RATE_LIMITS

    tiers = {}
    for tier_name in [Tier.FREE, Tier.PRO, Tier.ENTERPRISE]:
        tiers[tier_name] = {
            "quotas": TIER_QUOTAS[tier_name],
            "rate_limit": TIER_RATE_LIMITS[tier_name]
        }

    return {
        "tiers": tiers,
        "current_tier_header": "X-User-Tier",
        "upgrade_url": "/api/upgrade"
    }


