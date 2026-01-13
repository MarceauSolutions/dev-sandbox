"""
Pydantic Models for MCP Aggregator API

Request/Response schemas with validation for all endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# === Enums ===

class Service(str, Enum):
    """Rideshare services"""
    UBER = "uber"
    LYFT = "lyft"


class RideType(str, Enum):
    """Available ride types"""
    UBERX = "uberx"
    UBER_XL = "uber_xl"
    LYFT = "lyft"
    LYFT_XL = "lyft_xl"


# === Location Models ===

class LocationInput(BaseModel):
    """Location input for API requests"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, max_length=500, description="Human-readable address")

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 37.7879,
                "longitude": -122.4074,
                "address": "Union Square, San Francisco"
            }
        }


# === Request Models ===

class CompareRequest(BaseModel):
    """Request model for price comparison"""
    pickup: LocationInput = Field(..., description="Pickup location")
    dropoff: LocationInput = Field(..., description="Dropoff location")
    city: Optional[str] = Field(None, description="City override (auto-detected if not provided)")
    ride_types: Optional[List[str]] = Field(
        default=None,
        description="Specific ride types to compare (defaults to all available)"
    )

    class Config:
        json_schema_extra = {
            "example": {
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
        }


class NaturalLanguageRequest(BaseModel):
    """Request model for natural language queries"""
    query: str = Field(..., min_length=10, max_length=500, description="Natural language query")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Compare Uber and Lyft from Union Square SF to SFO airport"
            }
        }


# === Response Models ===

class FareEstimateResponse(BaseModel):
    """Fare estimate for a single service/ride type"""
    service: str = Field(..., description="Service name (uber or lyft)")
    ride_type: str = Field(..., description="Ride type (uberx, lyft, etc.)")
    estimate: float = Field(..., ge=0, description="Best estimate in USD")
    low_estimate: float = Field(..., ge=0, description="Low end of price range")
    high_estimate: float = Field(..., ge=0, description="High end of price range")
    surge_multiplier: float = Field(..., ge=0.5, description="Current surge/primetime multiplier")
    distance_miles: float = Field(..., ge=0, description="Trip distance in miles")
    duration_minutes: float = Field(..., ge=0, description="Estimated duration in minutes")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    deep_link: str = Field(..., description="URL to open app with route pre-filled")
    web_link: str = Field(..., description="Web fallback URL")

    class Config:
        json_schema_extra = {
            "example": {
                "service": "uber",
                "ride_type": "uberx",
                "estimate": 32.50,
                "low_estimate": 29.25,
                "high_estimate": 35.75,
                "surge_multiplier": 1.0,
                "distance_miles": 13.2,
                "duration_minutes": 25,
                "confidence": 0.85,
                "deep_link": "uber://?action=setPickup&...",
                "web_link": "https://m.uber.com/ul/?..."
            }
        }


class CompareResponse(BaseModel):
    """Response model for price comparison"""
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(..., description="Response timestamp")

    # Route info
    city: str = Field(..., description="Detected/provided city")
    distance_miles: float = Field(..., ge=0, description="Trip distance")
    duration_minutes: float = Field(..., ge=0, description="Estimated duration")

    # Fare estimates
    uber: FareEstimateResponse = Field(..., description="Uber fare estimate")
    lyft: FareEstimateResponse = Field(..., description="Lyft fare estimate")

    # Recommendation
    recommendation: str = Field(..., description="Recommended service (uber or lyft)")
    savings: float = Field(..., ge=0, description="Potential savings in USD")
    savings_percent: float = Field(..., ge=0, description="Savings as percentage")

    # Meta
    confidence: float = Field(..., ge=0, le=1, description="Overall confidence score")
    disclaimer: str = Field(
        default="Estimates based on rate cards. Actual prices may vary due to demand and route.",
        description="Legal disclaimer"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_abc123",
                "timestamp": "2026-01-12T20:00:00Z",
                "city": "san_francisco",
                "distance_miles": 13.2,
                "duration_minutes": 25,
                "uber": {"...": "..."},
                "lyft": {"...": "..."},
                "recommendation": "lyft",
                "savings": 3.25,
                "savings_percent": 10.0,
                "confidence": 0.85,
                "disclaimer": "Estimates based on rate cards..."
            }
        }


class CityResponse(BaseModel):
    """Response model for supported cities"""
    cities: List[str] = Field(..., description="List of supported city codes")
    count: int = Field(..., ge=0, description="Number of supported cities")


class RateCardResponse(BaseModel):
    """Response model for rate card information"""
    city: str
    service: str
    ride_type: str
    base_fare: float
    cost_per_mile: float
    cost_per_minute: float
    booking_fee: float
    min_fare: float
    last_updated: datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current time")
    uptime_seconds: float = Field(..., description="Server uptime")
    services: Dict[str, str] = Field(..., description="Status of dependent services")


class StatsResponse(BaseModel):
    """API statistics response"""
    total_requests: int = Field(..., ge=0)
    requests_today: int = Field(..., ge=0)
    avg_response_time_ms: float = Field(..., ge=0)
    cache_hit_rate: float = Field(..., ge=0, le=1)
    supported_cities: int = Field(..., ge=0)
    rate_cards_loaded: int = Field(..., ge=0)


# === Error Models ===

class ErrorDetail(BaseModel):
    """Error detail model"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: ErrorDetail
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "INVALID_LOCATION",
                    "message": "Pickup location is outside supported cities",
                    "field": "pickup"
                },
                "request_id": "req_abc123",
                "timestamp": "2026-01-12T20:00:00Z"
            }
        }


# === API Key Models ===

class APIKeyInfo(BaseModel):
    """API key information (for admin endpoints)"""
    key_id: str
    name: str
    tier: str
    rate_limit: int
    requests_today: int
    created_at: datetime
    last_used: Optional[datetime]
