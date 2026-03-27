"""
Authentication Module for MCP Aggregator API

Handles API key validation, rate limiting, and usage tracking.
"""

import time
import hashlib
from typing import Optional, Dict, Tuple
from datetime import datetime, date
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps

from fastapi import HTTPException, Header, Request
from fastapi.security import APIKeyHeader

from config import get_config, TEST_API_KEYS, ERROR_CODES, RateLimitConfig


@dataclass
class APIKeyData:
    """Data associated with an API key"""
    key_id: str
    name: str
    tier: str
    active: bool
    internal: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None


@dataclass
class UsageRecord:
    """Usage tracking for an API key"""
    requests_today: int = 0
    requests_this_minute: int = 0
    minute_window_start: float = 0.0
    last_request_time: float = 0.0
    total_requests: int = 0


class RateLimiter:
    """
    In-memory rate limiter with per-key tracking

    Note: In production, use Redis for distributed rate limiting
    """

    def __init__(self):
        self.usage: Dict[str, UsageRecord] = defaultdict(UsageRecord)
        self.daily_reset_date: date = date.today()

    def _reset_daily_if_needed(self):
        """Reset daily counters at midnight"""
        today = date.today()
        if today > self.daily_reset_date:
            for record in self.usage.values():
                record.requests_today = 0
            self.daily_reset_date = today

    def _reset_minute_if_needed(self, record: UsageRecord) -> None:
        """Reset minute window if 60 seconds have passed"""
        now = time.time()
        if now - record.minute_window_start >= 60:
            record.requests_this_minute = 0
            record.minute_window_start = now

    def check_rate_limit(
        self,
        key_id: str,
        limits: RateLimitConfig
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Check if request is within rate limits

        Args:
            key_id: API key identifier
            limits: Rate limit configuration for this key's tier

        Returns:
            (allowed, error_message, headers)
            - allowed: True if request should proceed
            - error_message: None if allowed, error description if blocked
            - headers: Rate limit headers to include in response
        """
        self._reset_daily_if_needed()

        record = self.usage[key_id]
        self._reset_minute_if_needed(record)

        now = time.time()

        # Check daily limit
        if record.requests_today >= limits.requests_per_day:
            return (
                False,
                f"Daily limit exceeded ({limits.requests_per_day} requests/day)",
                self._rate_limit_headers(record, limits, blocked=True)
            )

        # Check per-minute limit
        if record.requests_this_minute >= limits.requests_per_minute:
            return (
                False,
                f"Rate limit exceeded ({limits.requests_per_minute} requests/minute)",
                self._rate_limit_headers(record, limits, blocked=True)
            )

        # Check burst limit (requests in last second)
        if now - record.last_request_time < 0.1 and record.requests_this_minute >= limits.burst_limit:
            return (
                False,
                f"Burst limit exceeded. Please slow down.",
                self._rate_limit_headers(record, limits, blocked=True)
            )

        # Increment counters
        record.requests_today += 1
        record.requests_this_minute += 1
        record.last_request_time = now
        record.total_requests += 1

        return (
            True,
            None,
            self._rate_limit_headers(record, limits, blocked=False)
        )

    def _rate_limit_headers(
        self,
        record: UsageRecord,
        limits: RateLimitConfig,
        blocked: bool
    ) -> Dict[str, str]:
        """Generate rate limit headers for response"""
        headers = {
            "X-RateLimit-Limit-Minute": str(limits.requests_per_minute),
            "X-RateLimit-Remaining-Minute": str(max(0, limits.requests_per_minute - record.requests_this_minute)),
            "X-RateLimit-Limit-Day": str(limits.requests_per_day),
            "X-RateLimit-Remaining-Day": str(max(0, limits.requests_per_day - record.requests_today)),
        }

        if blocked:
            # Calculate retry-after
            seconds_until_minute_reset = max(0, 60 - (time.time() - record.minute_window_start))
            headers["Retry-After"] = str(int(seconds_until_minute_reset) + 1)

        return headers

    def get_usage(self, key_id: str) -> UsageRecord:
        """Get usage record for a key"""
        return self.usage.get(key_id, UsageRecord())


class APIKeyValidator:
    """
    API key validation and management

    Note: In production, use a database for key storage
    """

    def __init__(self):
        self.keys: Dict[str, APIKeyData] = {}
        self._load_test_keys()

    def _load_test_keys(self):
        """Load test API keys from config"""
        for key, data in TEST_API_KEYS.items():
            self.keys[key] = APIKeyData(
                key_id=self._hash_key(key),
                name=data["name"],
                tier=data["tier"],
                active=data["active"],
                internal=data.get("internal", False)
            )

    def _hash_key(self, key: str) -> str:
        """Generate consistent key ID from API key"""
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def validate_key(self, api_key: str) -> Tuple[bool, Optional[APIKeyData], Optional[str]]:
        """
        Validate an API key

        Args:
            api_key: The API key to validate

        Returns:
            (valid, key_data, error_message)
        """
        if not api_key:
            return (False, None, "API key required")

        # Check if key exists
        key_data = self.keys.get(api_key)
        if not key_data:
            return (False, None, "Invalid API key")

        # Check if key is active
        if not key_data.active:
            return (False, None, "API key is deactivated")

        # Update last used
        key_data.last_used = datetime.now()

        return (True, key_data, None)

    def get_key_info(self, api_key: str) -> Optional[APIKeyData]:
        """Get information about an API key"""
        return self.keys.get(api_key)

    def add_key(self, api_key: str, name: str, tier: str) -> APIKeyData:
        """Add a new API key (for admin use)"""
        key_data = APIKeyData(
            key_id=self._hash_key(api_key),
            name=name,
            tier=tier,
            active=True
        )
        self.keys[api_key] = key_data
        return key_data

    def deactivate_key(self, api_key: str) -> bool:
        """Deactivate an API key"""
        if api_key in self.keys:
            self.keys[api_key].active = False
            return True
        return False


# === Global Instances ===

_rate_limiter: Optional[RateLimiter] = None
_key_validator: Optional[APIKeyValidator] = None


def get_rate_limiter() -> RateLimiter:
    """Get singleton rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def get_key_validator() -> APIKeyValidator:
    """Get singleton key validator instance"""
    global _key_validator
    if _key_validator is None:
        _key_validator = APIKeyValidator()
    return _key_validator


# === FastAPI Dependencies ===

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(
    request: Request,
    api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> APIKeyData:
    """
    FastAPI dependency for API key validation and rate limiting

    Usage:
        @app.get("/endpoint")
        async def endpoint(key_data: APIKeyData = Depends(validate_api_key)):
            ...
    """
    config = get_config()
    validator = get_key_validator()
    limiter = get_rate_limiter()

    # Validate key
    valid, key_data, error = validator.validate_key(api_key)
    if not valid:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_API_KEY",
                "message": error
            }
        )

    # Check rate limits (if enabled)
    if config.enable_rate_limiting:
        limits = config.get_rate_limit(key_data.tier)
        allowed, error_msg, headers = limiter.check_rate_limit(key_data.key_id, limits)

        # Add rate limit headers to response
        request.state.rate_limit_headers = headers

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": error_msg
                },
                headers=headers
            )

    return key_data


async def optional_api_key(
    api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[APIKeyData]:
    """
    Optional API key validation (for endpoints that work with/without auth)

    Usage:
        @app.get("/endpoint")
        async def endpoint(key_data: Optional[APIKeyData] = Depends(optional_api_key)):
            if key_data:
                # Authenticated request
            else:
                # Anonymous request (apply stricter limits)
    """
    if not api_key:
        return None

    validator = get_key_validator()
    valid, key_data, _ = validator.validate_key(api_key)

    return key_data if valid else None


# === Utility Functions ===

def generate_api_key(prefix: str = "mcp") -> str:
    """
    Generate a new API key

    Format: {prefix}_{random_32_chars}
    Example: mcp_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
    """
    import secrets
    random_part = secrets.token_hex(16)
    return f"{prefix}_{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage (never store raw keys)"""
    return hashlib.sha256(api_key.encode()).hexdigest()


# Example usage
if __name__ == "__main__":
    # Test key validation
    validator = get_key_validator()

    print("Testing API Key Validation")
    print("=" * 50)

    # Test valid key
    valid, data, error = validator.validate_key("test_free_key_12345")
    print(f"test_free_key_12345: valid={valid}, tier={data.tier if data else None}")

    # Test invalid key
    valid, data, error = validator.validate_key("invalid_key")
    print(f"invalid_key: valid={valid}, error={error}")

    # Test rate limiting
    limiter = get_rate_limiter()
    config = get_config()
    limits = config.get_rate_limit("free")

    print("\nTesting Rate Limiting")
    print("=" * 50)

    for i in range(15):
        allowed, error, headers = limiter.check_rate_limit("test_key", limits)
        print(f"Request {i+1}: allowed={allowed}, remaining={headers.get('X-RateLimit-Remaining-Minute')}")

    # Generate new key
    print("\nGenerate New Key")
    print("=" * 50)
    new_key = generate_api_key()
    print(f"New key: {new_key}")
    print(f"Hashed: {hash_api_key(new_key)[:32]}...")
