#!/usr/bin/env python3
"""
Rate Limiting and User Quotas for Fitness Influencer AI v2.0

Tier-based rate limiting with Redis persistence and quota management.

Tiers:
    - Free: 5 video jobs/day, 10 captions/day, 20 exports/day
    - Pro: 50 video jobs/day, unlimited captions, unlimited exports
    - Enterprise: Unlimited everything

Usage:
    from backend.rate_limiter import limiter, check_quota, get_rate_limit_headers

    @app.post("/api/video/caption")
    @limiter.limit("10/minute")
    async def caption_video(request: Request):
        await check_quota(request, "caption")
        ...
"""

import os
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from functools import wraps

from fastapi import Request, HTTPException, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.logging_config import get_logger

logger = get_logger(__name__)

# Redis connection for rate limiting state
REDIS_URL = os.getenv("REDIS_URL", None)


# ============================================================================
# Tier Definitions
# ============================================================================

class Tier:
    """User subscription tier."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Quota limits per tier (per day)
# -1 means unlimited
TIER_QUOTAS = {
    Tier.FREE: {
        "video_jobs": 5,      # Video processing jobs (caption, reframe, export)
        "caption_jobs": 10,   # Caption-only jobs
        "export_jobs": 20,    # Platform export jobs
        "transcription_jobs": 10,
        "image_generation": 5,
    },
    Tier.PRO: {
        "video_jobs": 50,
        "caption_jobs": -1,   # Unlimited
        "export_jobs": -1,
        "transcription_jobs": 100,
        "image_generation": 50,
    },
    Tier.ENTERPRISE: {
        "video_jobs": -1,
        "caption_jobs": -1,
        "export_jobs": -1,
        "transcription_jobs": -1,
        "image_generation": -1,
    }
}

# Rate limits per tier (requests per minute)
TIER_RATE_LIMITS = {
    Tier.FREE: "10/minute",
    Tier.PRO: "60/minute",
    Tier.ENTERPRISE: "300/minute",
}


# ============================================================================
# User Key Extraction
# ============================================================================

def get_user_key(request: Request) -> str:
    """
    Extract user identifier for rate limiting.

    Priority:
    1. X-User-ID header
    2. Authorization token (hashed)
    3. Client IP address
    """
    # Check for user ID header
    user_id = request.headers.get("X-User-ID")
    if user_id:
        return f"user:{user_id}"

    # Check for auth token (hash it for privacy)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        token_hash = hashlib.md5(auth_header.encode()).hexdigest()[:12]
        return f"token:{token_hash}"

    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


def get_user_tier(request: Request) -> str:
    """
    Get user's subscription tier.

    In production, this would look up the user's tier from database.
    For now, uses X-User-Tier header or defaults to free.
    """
    tier = request.headers.get("X-User-Tier", Tier.FREE)
    if tier not in [Tier.FREE, Tier.PRO, Tier.ENTERPRISE]:
        tier = Tier.FREE
    return tier


# ============================================================================
# Rate Limiter Setup
# ============================================================================

# Initialize SlowAPI limiter
limiter = Limiter(
    key_func=get_user_key,
    default_limits=["100/minute"],
    storage_uri=REDIS_URL if REDIS_URL else None,  # Falls back to in-memory
    strategy="fixed-window"
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.

    Returns 429 with retry information.
    """
    # Parse retry-after from limit string
    retry_after = 60  # Default to 1 minute

    logger.warning(
        "Rate limit exceeded",
        extra={
            "user_key": get_user_key(request),
            "endpoint": str(request.url.path),
            "metadata": {
                "limit": str(exc.detail),
                "retry_after": retry_after
            }
        }
    )

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Too many requests. Please retry after {retry_after} seconds.",
            "retry_after": retry_after,
            "limit": str(exc.detail)
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(exc.detail),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time()) + retry_after)
        }
    )


# ============================================================================
# Quota Management
# ============================================================================

class QuotaManager:
    """
    Manages daily quotas per user.

    Uses Redis for persistence if available, otherwise in-memory.
    Quotas reset at midnight UTC.
    """

    def __init__(self):
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._redis_client = None

        # Try to connect to Redis
        if REDIS_URL:
            try:
                import redis
                self._redis_client = redis.from_url(REDIS_URL)
                self._redis_client.ping()
                logger.info("QuotaManager connected to Redis")
            except Exception as e:
                logger.warning(f"QuotaManager falling back to in-memory: {e}")
                self._redis_client = None

    def _get_quota_key(self, user_key: str, quota_type: str) -> str:
        """Generate Redis key for quota tracking."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return f"quota:{user_key}:{quota_type}:{today}"

    def _get_ttl_until_midnight(self) -> int:
        """Calculate seconds until midnight UTC."""
        now = datetime.utcnow()
        midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return int((midnight - now).total_seconds())

    def get_usage(self, user_key: str, quota_type: str) -> int:
        """Get current usage count for a quota type."""
        key = self._get_quota_key(user_key, quota_type)

        if self._redis_client:
            try:
                value = self._redis_client.get(key)
                return int(value) if value else 0
            except Exception as e:
                logger.error(f"Redis get failed: {e}")

        # Fallback to memory
        return self._memory_store.get(key, 0)

    def increment_usage(self, user_key: str, quota_type: str) -> int:
        """Increment usage count and return new value."""
        key = self._get_quota_key(user_key, quota_type)
        ttl = self._get_ttl_until_midnight()

        if self._redis_client:
            try:
                pipe = self._redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, ttl)
                results = pipe.execute()
                return results[0]
            except Exception as e:
                logger.error(f"Redis incr failed: {e}")

        # Fallback to memory
        current = self._memory_store.get(key, 0)
        self._memory_store[key] = current + 1
        return current + 1

    def check_quota(
        self,
        user_key: str,
        quota_type: str,
        tier: str
    ) -> Tuple[bool, int, int]:
        """
        Check if user is within quota.

        Returns:
            Tuple of (allowed, remaining, limit)
        """
        limit = TIER_QUOTAS.get(tier, TIER_QUOTAS[Tier.FREE]).get(quota_type, 0)

        # Unlimited
        if limit == -1:
            return (True, -1, -1)

        current = self.get_usage(user_key, quota_type)
        remaining = max(0, limit - current)
        allowed = current < limit

        return (allowed, remaining, limit)

    def get_all_quotas(self, user_key: str, tier: str) -> Dict[str, Dict[str, int]]:
        """Get status of all quotas for a user."""
        quotas = {}
        tier_limits = TIER_QUOTAS.get(tier, TIER_QUOTAS[Tier.FREE])

        for quota_type, limit in tier_limits.items():
            if limit == -1:
                quotas[quota_type] = {
                    "used": self.get_usage(user_key, quota_type),
                    "limit": -1,
                    "remaining": -1,
                    "unlimited": True
                }
            else:
                used = self.get_usage(user_key, quota_type)
                quotas[quota_type] = {
                    "used": used,
                    "limit": limit,
                    "remaining": max(0, limit - used),
                    "unlimited": False
                }

        return quotas


# Global quota manager instance
quota_manager = QuotaManager()


# ============================================================================
# Quota Checking Utilities
# ============================================================================

async def check_quota(
    request: Request,
    quota_type: str,
    increment: bool = True
) -> Dict[str, int]:
    """
    Check if request is within quota and optionally increment.

    Raises HTTPException with 429 if quota exceeded.

    Args:
        request: FastAPI request object
        quota_type: Type of quota to check (video_jobs, caption_jobs, etc.)
        increment: Whether to increment the counter

    Returns:
        Dict with remaining and limit info
    """
    user_key = get_user_key(request)
    tier = get_user_tier(request)

    allowed, remaining, limit = quota_manager.check_quota(user_key, quota_type, tier)

    if not allowed:
        # Calculate reset time (midnight UTC)
        now = datetime.utcnow()
        midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        retry_after = int((midnight - now).total_seconds())

        logger.warning(
            "Quota exceeded",
            extra={
                "user_key": user_key,
                "quota_type": quota_type,
                "tier": tier,
                "metadata": {
                    "limit": limit,
                    "retry_after": retry_after
                }
            }
        )

        raise HTTPException(
            status_code=429,
            detail={
                "error": "quota_exceeded",
                "message": f"Daily {quota_type} quota exceeded. Resets at midnight UTC.",
                "quota_type": quota_type,
                "limit": limit,
                "retry_after": retry_after,
                "upgrade_url": "/api/upgrade"  # Future upgrade endpoint
            },
            headers={
                "Retry-After": str(retry_after),
                "X-Quota-Limit": str(limit),
                "X-Quota-Remaining": "0",
                "X-Quota-Reset": midnight.isoformat() + "Z"
            }
        )

    # Increment usage
    if increment:
        quota_manager.increment_usage(user_key, quota_type)
        remaining = max(0, remaining - 1)

    return {
        "remaining": remaining,
        "limit": limit,
        "unlimited": limit == -1
    }


def get_rate_limit_headers(
    request: Request,
    quota_type: str = None
) -> Dict[str, str]:
    """
    Generate rate limit headers for response.

    Args:
        request: FastAPI request object
        quota_type: Optional quota type for quota headers

    Returns:
        Dict of header name -> value
    """
    user_key = get_user_key(request)
    tier = get_user_tier(request)

    headers = {
        "X-RateLimit-Tier": tier,
    }

    if quota_type:
        allowed, remaining, limit = quota_manager.check_quota(
            user_key, quota_type, tier
        )

        # Calculate reset time
        now = datetime.utcnow()
        midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        headers.update({
            "X-Quota-Type": quota_type,
            "X-Quota-Limit": str(limit) if limit != -1 else "unlimited",
            "X-Quota-Remaining": str(remaining) if remaining != -1 else "unlimited",
            "X-Quota-Reset": midnight.isoformat() + "Z"
        })

    return headers


# ============================================================================
# Decorator for Quota-Protected Endpoints
# ============================================================================

def require_quota(quota_type: str):
    """
    Decorator to require quota for an endpoint.

    Usage:
        @app.post("/api/video/caption")
        @require_quota("caption_jobs")
        async def caption_video(request: Request, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Check and increment quota
            quota_info = await check_quota(request, quota_type)

            # Add quota info to request state for response headers
            request.state.quota_info = quota_info
            request.state.quota_type = quota_type

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# Quota Status Endpoint Helper
# ============================================================================

async def get_quota_status(request: Request) -> Dict[str, Any]:
    """
    Get full quota status for current user.

    Returns dict suitable for /api/quota/status endpoint.
    """
    user_key = get_user_key(request)
    tier = get_user_tier(request)

    quotas = quota_manager.get_all_quotas(user_key, tier)

    # Calculate reset time
    now = datetime.utcnow()
    midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    return {
        "user_key": user_key.split(":", 1)[1] if ":" in user_key else user_key,
        "tier": tier,
        "quotas": quotas,
        "reset_at": midnight.isoformat() + "Z",
        "seconds_until_reset": int((midnight - now).total_seconds()),
        "rate_limit": TIER_RATE_LIMITS.get(tier, TIER_RATE_LIMITS[Tier.FREE])
    }
