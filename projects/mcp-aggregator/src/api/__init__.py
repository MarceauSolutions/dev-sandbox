"""
MCP Aggregator REST API

FastAPI-based REST API for the MCP Aggregator platform.

Endpoints:
- /health: Health check
- /v1/cities: List supported cities
- /v1/cities/{city}/rates: Get rate cards
- /v1/compare: Compare prices across services
- /v1/deeplink/{service}: Generate deep links
- /v1/route: Natural language routing
- /stats: API statistics

Usage:
    # Start server
    uvicorn src.api.server:app --reload

    # Or with Docker
    cd src/api && docker-compose up
"""

from .server import app
from .models import (
    Location,
    CompareRequest,
    CompareResponse,
    RateCard,
    DeepLink
)
from .config import Settings, get_settings
from .auth import verify_api_key, APIKeyAuth

__all__ = [
    'app',
    'Location',
    'CompareRequest',
    'CompareResponse',
    'RateCard',
    'DeepLink',
    'Settings',
    'get_settings',
    'verify_api_key',
    'APIKeyAuth'
]
