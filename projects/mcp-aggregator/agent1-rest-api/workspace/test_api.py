"""
Test Suite for MCP Aggregator API

Run with: pytest test_api.py -v

These tests can be run without starting the server using FastAPI's TestClient.
"""

import sys
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add workspace to path for imports
sys.path.insert(0, "/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent1-rest-api/workspace")
sys.path.insert(0, "/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/src/mcps/rideshare")

from fastapi.testclient import TestClient


# === Fixtures ===

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test to prevent 429 errors"""
    from auth import get_rate_limiter
    limiter = get_rate_limiter()
    limiter.usage.clear()
    yield


@pytest.fixture
def client():
    """Create test client with mocked dependencies"""
    # Import here to avoid import errors during collection
    from server import app, rate_card_db, comparator
    import server

    # Initialize dependencies if not already done (lifespan may not trigger in tests)
    if server.rate_card_db is None:
        from rate_cards import RateCardDB
        from comparison import RideshareComparison
        server.rate_card_db = RateCardDB()
        server.comparator = RideshareComparison(server.rate_card_db)

    return TestClient(app)


@pytest.fixture
def api_key():
    """Test API key"""
    return "test_free_key_12345"


@pytest.fixture
def auth_headers(api_key):
    """Headers with API key"""
    return {"X-API-Key": api_key}


@pytest.fixture
def sample_compare_request():
    """Sample comparison request body"""
    return {
        "pickup": {
            "latitude": 37.7879,
            "longitude": -122.4074,
            "address": "Union Square, San Francisco"
        },
        "dropoff": {
            "latitude": 37.6213,
            "longitude": -122.3790,
            "address": "SFO Airport"
        }
    }


# === Test: Root & Health ===

class TestHealthEndpoints:
    """Tests for health check endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "MCP Aggregator API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "operational"
        assert "docs" in data

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "services" in data

    def test_health_no_auth_required(self, client):
        """Health check should work without authentication"""
        response = client.get("/health")
        assert response.status_code == 200


# === Test: Authentication ===

class TestAuthentication:
    """Tests for API key authentication"""

    def test_missing_api_key(self, client):
        """Request without API key should fail"""
        response = client.get("/v1/cities")
        assert response.status_code == 401

        data = response.json()
        assert data["error"]["code"] == "INVALID_API_KEY"

    def test_invalid_api_key(self, client):
        """Request with invalid API key should fail"""
        response = client.get(
            "/v1/cities",
            headers={"X-API-Key": "invalid_key_12345"}
        )
        assert response.status_code == 401

    def test_valid_api_key(self, client, auth_headers):
        """Request with valid API key should succeed"""
        response = client.get("/v1/cities", headers=auth_headers)
        assert response.status_code == 200

    def test_request_id_in_response(self, client, auth_headers):
        """Response should include request ID header"""
        response = client.get("/v1/cities", headers=auth_headers)
        assert "X-Request-ID" in response.headers

    def test_response_time_header(self, client, auth_headers):
        """Response should include response time header"""
        response = client.get("/v1/cities", headers=auth_headers)
        assert "X-Response-Time-Ms" in response.headers


# === Test: Cities Endpoint ===

class TestCitiesEndpoint:
    """Tests for cities endpoints"""

    def test_get_supported_cities(self, client, auth_headers):
        """Test getting list of supported cities"""
        response = client.get("/v1/cities", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "cities" in data
        assert "count" in data
        assert isinstance(data["cities"], list)
        assert len(data["cities"]) == data["count"]
        assert "san_francisco" in data["cities"]

    def test_get_city_rates(self, client, auth_headers):
        """Test getting rate cards for a city"""
        response = client.get(
            "/v1/cities/san_francisco/rates",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["city"] == "san_francisco"
        assert "services" in data
        assert "uber" in data["services"]
        assert "lyft" in data["services"]

    def test_get_invalid_city_rates(self, client, auth_headers):
        """Test getting rates for unsupported city"""
        response = client.get(
            "/v1/cities/invalid_city/rates",
            headers=auth_headers
        )
        assert response.status_code == 400

        data = response.json()
        assert data["error"]["code"] == "UNSUPPORTED_CITY"


# === Test: Comparison Endpoint ===

class TestComparisonEndpoint:
    """Tests for price comparison endpoint"""

    def test_compare_prices_valid(self, client, auth_headers, sample_compare_request):
        """Test price comparison with valid request"""
        response = client.post(
            "/v1/compare",
            json=sample_compare_request,
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        # Check required fields
        assert "request_id" in data
        assert "timestamp" in data
        assert "city" in data
        assert "distance_miles" in data
        assert "duration_minutes" in data
        assert "uber" in data
        assert "lyft" in data
        assert "recommendation" in data
        assert "savings" in data
        assert "confidence" in data

    def test_compare_prices_uber_response(self, client, auth_headers, sample_compare_request):
        """Test Uber fare response structure"""
        response = client.post(
            "/v1/compare",
            json=sample_compare_request,
            headers=auth_headers
        )
        data = response.json()

        uber = data["uber"]
        assert uber["service"] == "uber"
        assert uber["ride_type"] == "uberx"
        assert uber["estimate"] > 0
        assert uber["low_estimate"] > 0
        assert uber["high_estimate"] >= uber["estimate"]
        assert "deep_link" in uber
        assert "web_link" in uber
        assert uber["deep_link"].startswith("uber://")

    def test_compare_prices_lyft_response(self, client, auth_headers, sample_compare_request):
        """Test Lyft fare response structure"""
        response = client.post(
            "/v1/compare",
            json=sample_compare_request,
            headers=auth_headers
        )
        data = response.json()

        lyft = data["lyft"]
        assert lyft["service"] == "lyft"
        assert lyft["ride_type"] == "lyft"
        assert lyft["estimate"] > 0
        assert "deep_link" in lyft
        assert lyft["deep_link"].startswith("lyft://")

    def test_compare_recommendation(self, client, auth_headers, sample_compare_request):
        """Test that recommendation is the cheaper option"""
        response = client.post(
            "/v1/compare",
            json=sample_compare_request,
            headers=auth_headers
        )
        data = response.json()

        if data["uber"]["estimate"] < data["lyft"]["estimate"]:
            assert data["recommendation"] == "uber"
        else:
            assert data["recommendation"] == "lyft"

    def test_compare_missing_pickup(self, client, auth_headers):
        """Test comparison with missing pickup"""
        response = client.post(
            "/v1/compare",
            json={
                "dropoff": {"latitude": 37.6213, "longitude": -122.3790}
            },
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error

    def test_compare_invalid_coordinates(self, client, auth_headers):
        """Test comparison with invalid coordinates"""
        response = client.post(
            "/v1/compare",
            json={
                "pickup": {"latitude": 999, "longitude": -122.4074},
                "dropoff": {"latitude": 37.6213, "longitude": -122.3790}
            },
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_compare_with_city_override(self, client, auth_headers, sample_compare_request):
        """Test comparison with explicit city"""
        request = sample_compare_request.copy()
        request["city"] = "san_francisco"

        response = client.post(
            "/v1/compare",
            json=request,
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["city"] == "san_francisco"


# === Test: Deep Links ===

class TestDeepLinks:
    """Tests for deep link generation"""

    def test_uber_deep_link(self, client, auth_headers):
        """Test Uber deep link generation"""
        response = client.get(
            "/v1/deeplink/uber",
            params={
                "pickup_lat": 37.7879,
                "pickup_lng": -122.4074,
                "dropoff_lat": 37.6213,
                "dropoff_lng": -122.3790
            },
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "uber"
        assert "uber://" in data["app_link"]
        assert "https://" in data["web_link"]

    def test_lyft_deep_link(self, client, auth_headers):
        """Test Lyft deep link generation"""
        response = client.get(
            "/v1/deeplink/lyft",
            params={
                "pickup_lat": 37.7879,
                "pickup_lng": -122.4074,
                "dropoff_lat": 37.6213,
                "dropoff_lng": -122.3790
            },
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "lyft"
        assert "lyft://" in data["app_link"]

    def test_invalid_service(self, client, auth_headers):
        """Test deep link with invalid service"""
        response = client.get(
            "/v1/deeplink/invalid",
            params={
                "pickup_lat": 37.7879,
                "pickup_lng": -122.4074,
                "dropoff_lat": 37.6213,
                "dropoff_lng": -122.3790
            },
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_mobile_vs_desktop_link(self, client, auth_headers):
        """Test mobile vs desktop link preference"""
        # Mobile
        response = client.get(
            "/v1/deeplink/uber",
            params={
                "pickup_lat": 37.7879,
                "pickup_lng": -122.4074,
                "dropoff_lat": 37.6213,
                "dropoff_lng": -122.3790,
                "mobile": True
            },
            headers=auth_headers
        )
        data = response.json()
        assert data["primary"] == data["app_link"]

        # Desktop
        response = client.get(
            "/v1/deeplink/uber",
            params={
                "pickup_lat": 37.7879,
                "pickup_lng": -122.4074,
                "dropoff_lat": 37.6213,
                "dropoff_lng": -122.3790,
                "mobile": False
            },
            headers=auth_headers
        )
        data = response.json()
        assert data["primary"] == data["web_link"]


# === Test: Natural Language Route ===

class TestNaturalLanguageRoute:
    """Tests for natural language query endpoint"""

    def test_route_query(self, client, auth_headers):
        """Test natural language route query"""
        response = client.post(
            "/v1/route",
            json={"query": "Compare Uber and Lyft from Union Square SF to SFO airport"},
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "request_id" in data
        assert "message" in data
        assert "hint" in data
        assert "example" in data


# === Test: Stats Endpoint ===

class TestStatsEndpoint:
    """Tests for stats endpoint"""

    def test_stats_requires_auth(self, client):
        """Stats endpoint should require authentication"""
        response = client.get("/stats")
        assert response.status_code == 401

    def test_stats_with_auth(self, client, auth_headers):
        """Stats should return metrics"""
        response = client.get("/stats", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "total_requests" in data
        assert "requests_today" in data
        assert "avg_response_time_ms" in data
        assert "cache_hit_rate" in data
        assert "supported_cities" in data


# === Test: Models (Unit Tests) ===

class TestModels:
    """Unit tests for Pydantic models"""

    def test_location_input_valid(self):
        """Test valid location input"""
        from models import LocationInput

        loc = LocationInput(latitude=37.7879, longitude=-122.4074)
        assert loc.latitude == 37.7879
        assert loc.longitude == -122.4074

    def test_location_input_with_address(self):
        """Test location input with address"""
        from models import LocationInput

        loc = LocationInput(
            latitude=37.7879,
            longitude=-122.4074,
            address="Union Square"
        )
        assert loc.address == "Union Square"

    def test_location_input_invalid_latitude(self):
        """Test invalid latitude"""
        from models import LocationInput
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LocationInput(latitude=999, longitude=-122.4074)

    def test_location_input_invalid_longitude(self):
        """Test invalid longitude"""
        from models import LocationInput
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LocationInput(latitude=37.7879, longitude=-999)


# === Test: Config (Unit Tests) ===

class TestConfig:
    """Unit tests for configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        from config import Config

        config = Config()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.debug is False
        assert len(config.supported_cities) == 10

    def test_rate_limit_tiers(self):
        """Test rate limit tiers exist"""
        from config import Config

        config = Config()
        assert "free" in config.rate_limits
        assert "basic" in config.rate_limits
        assert "pro" in config.rate_limits
        assert "enterprise" in config.rate_limits

    def test_get_rate_limit(self):
        """Test getting rate limit for tier"""
        from config import Config

        config = Config()

        free_limits = config.get_rate_limit("free")
        assert free_limits.requests_per_minute == 10
        assert free_limits.requests_per_day == 100

        pro_limits = config.get_rate_limit("pro")
        assert pro_limits.requests_per_minute == 300


# === Test: Auth (Unit Tests) ===

class TestAuthModule:
    """Unit tests for authentication module"""

    def test_api_key_validator(self):
        """Test API key validation"""
        from auth import APIKeyValidator

        validator = APIKeyValidator()

        # Valid key
        valid, data, error = validator.validate_key("test_free_key_12345")
        assert valid is True
        assert data is not None
        assert data.tier == "free"

        # Invalid key
        valid, data, error = validator.validate_key("invalid")
        assert valid is False
        assert error is not None

    def test_rate_limiter(self):
        """Test rate limiting logic"""
        from auth import RateLimiter
        from config import RateLimitConfig

        limiter = RateLimiter()
        limits = RateLimitConfig(
            requests_per_minute=5,
            requests_per_day=100,
            burst_limit=10  # High burst limit to test per-minute limit
        )

        # First 5 requests should pass (within per-minute limit)
        for i in range(5):
            allowed, error, headers = limiter.check_rate_limit("test_key", limits)
            assert allowed is True, f"Request {i+1} should be allowed"

        # 6th request should be blocked (hit per-minute limit of 5)
        allowed, error, headers = limiter.check_rate_limit("test_key", limits)
        assert allowed is False, "Request 6 should be blocked (per-minute limit)"

    def test_generate_api_key(self):
        """Test API key generation"""
        from auth import generate_api_key

        key = generate_api_key()
        assert key.startswith("mcp_")
        assert len(key) == 36  # mcp_ + 32 hex chars

        key2 = generate_api_key(prefix="test")
        assert key2.startswith("test_")


# === Run Tests ===

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
