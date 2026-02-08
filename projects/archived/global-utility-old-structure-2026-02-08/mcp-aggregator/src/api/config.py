"""
Configuration Module for MCP Aggregator API

Handles environment variables, rate limits, and service configuration.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import timedelta


@dataclass
class RateLimitConfig:
    """Rate limiting configuration per tier"""
    requests_per_minute: int
    requests_per_day: int
    burst_limit: int


@dataclass
class Config:
    """Application configuration"""

    # === Server Settings ===
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 4
    log_level: str = "INFO"

    # === API Settings ===
    api_version: str = "v1"
    api_title: str = "MCP Aggregator API"
    api_description: str = "Universal MCP Aggregation Platform - Rideshare Comparison"

    # === Security ===
    api_key_header: str = "X-API-Key"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])

    # === Rate Limits by Tier ===
    rate_limits: Dict[str, RateLimitConfig] = field(default_factory=lambda: {
        "free": RateLimitConfig(
            requests_per_minute=10,
            requests_per_day=100,
            burst_limit=5
        ),
        "basic": RateLimitConfig(
            requests_per_minute=60,
            requests_per_day=1000,
            burst_limit=20
        ),
        "pro": RateLimitConfig(
            requests_per_minute=300,
            requests_per_day=10000,
            burst_limit=100
        ),
        "enterprise": RateLimitConfig(
            requests_per_minute=1000,
            requests_per_day=100000,
            burst_limit=500
        )
    })

    # === Supported Cities ===
    supported_cities: List[str] = field(default_factory=lambda: [
        "san_francisco",
        "new_york",
        "los_angeles",
        "chicago",
        "boston",
        "seattle",
        "austin",
        "miami",
        "denver",
        "washington_dc"
    ])

    # === Caching ===
    cache_ttl_seconds: int = 300  # 5 minutes
    cache_max_size: int = 10000

    # === Timeouts ===
    request_timeout_seconds: int = 30

    # === Paths ===
    rideshare_mcp_path: str = "/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/src/mcps/rideshare"

    # === Feature Flags ===
    enable_metrics: bool = True
    enable_caching: bool = True
    enable_rate_limiting: bool = True

    @classmethod
    def from_env(cls) -> "Config":
        """
        Load configuration from environment variables

        Environment variables override defaults:
        - MCP_HOST: Server host
        - MCP_PORT: Server port
        - MCP_DEBUG: Debug mode (true/false)
        - MCP_WORKERS: Number of workers
        - MCP_LOG_LEVEL: Logging level
        - MCP_CORS_ORIGINS: Comma-separated CORS origins
        - MCP_CACHE_TTL: Cache TTL in seconds
        - MCP_ENABLE_RATE_LIMITING: Enable rate limiting (true/false)
        """
        config = cls()

        # Server settings
        config.host = os.getenv("MCP_HOST", config.host)
        config.port = int(os.getenv("MCP_PORT", str(config.port)))
        config.debug = os.getenv("MCP_DEBUG", "false").lower() == "true"
        config.workers = int(os.getenv("MCP_WORKERS", str(config.workers)))
        config.log_level = os.getenv("MCP_LOG_LEVEL", config.log_level)

        # CORS
        cors_env = os.getenv("MCP_CORS_ORIGINS")
        if cors_env:
            config.cors_origins = [origin.strip() for origin in cors_env.split(",")]

        # Caching
        config.cache_ttl_seconds = int(os.getenv("MCP_CACHE_TTL", str(config.cache_ttl_seconds)))

        # Features
        config.enable_rate_limiting = os.getenv("MCP_ENABLE_RATE_LIMITING", "true").lower() == "true"
        config.enable_metrics = os.getenv("MCP_ENABLE_METRICS", "true").lower() == "true"
        config.enable_caching = os.getenv("MCP_ENABLE_CACHING", "true").lower() == "true"

        return config

    def get_rate_limit(self, tier: str) -> RateLimitConfig:
        """Get rate limit configuration for a tier"""
        return self.rate_limits.get(tier, self.rate_limits["free"])


# === Test API Keys (for development) ===
# In production, these would be stored in a database

TEST_API_KEYS: Dict[str, Dict] = {
    "test_free_key_12345": {
        "name": "Test Free User",
        "tier": "free",
        "active": True
    },
    "test_basic_key_67890": {
        "name": "Test Basic User",
        "tier": "basic",
        "active": True
    },
    "test_pro_key_11111": {
        "name": "Test Pro User",
        "tier": "pro",
        "active": True
    },
    "test_enterprise_key_22222": {
        "name": "Test Enterprise User",
        "tier": "enterprise",
        "active": True
    },
    # Master key for internal use
    "mcp_master_key_secret": {
        "name": "MCP Internal",
        "tier": "enterprise",
        "active": True,
        "internal": True
    }
}


# === Error Codes ===

ERROR_CODES = {
    "INVALID_API_KEY": ("Invalid or missing API key", 401),
    "RATE_LIMIT_EXCEEDED": ("Rate limit exceeded. Please try again later.", 429),
    "INVALID_LOCATION": ("Invalid location coordinates", 400),
    "UNSUPPORTED_CITY": ("City not supported", 400),
    "INVALID_REQUEST": ("Invalid request format", 400),
    "INTERNAL_ERROR": ("Internal server error", 500),
    "SERVICE_UNAVAILABLE": ("Service temporarily unavailable", 503),
    "VALIDATION_ERROR": ("Request validation failed", 422)
}


# === Singleton Config Instance ===

_config: Optional[Config] = None


def get_config() -> Config:
    """Get singleton config instance"""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


# Example usage
if __name__ == "__main__":
    config = get_config()
    print(f"Server: {config.host}:{config.port}")
    print(f"Debug: {config.debug}")
    print(f"Supported Cities: {', '.join(config.supported_cities)}")
    print(f"Rate Limits (free): {config.get_rate_limit('free')}")
    print(f"Rate Limits (pro): {config.get_rate_limit('pro')}")
