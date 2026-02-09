"""
MCP Aggregator REST API Server

Production-ready FastAPI server for rideshare price comparison.

Usage:
    uvicorn server:app --host 0.0.0.0 --port 8000

Environment Variables:
    MCP_HOST: Server host (default: 0.0.0.0)
    MCP_PORT: Server port (default: 8000)
    MCP_DEBUG: Debug mode (default: false)
    MCP_LOG_LEVEL: Logging level (default: INFO)
"""

import sys
import time
import uuid
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add rideshare MCP path
sys.path.insert(0, "/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/src/mcps/rideshare")

# Local imports
from models import (
    CompareRequest,
    CompareResponse,
    FareEstimateResponse,
    CityResponse,
    RateCardResponse,
    HealthResponse,
    StatsResponse,
    ErrorResponse,
    ErrorDetail,
    NaturalLanguageRequest
)
from config import get_config, ERROR_CODES
from auth import validate_api_key, optional_api_key, APIKeyData, get_rate_limiter

# Import rideshare MCP components
from comparison import RideshareComparison, Location, FareEstimate
from rate_cards import RateCardDB
from deep_links import generate_smart_link

# === Logging Setup ===

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-api")


# === Global State ===

class AppState:
    """Application state container"""
    def __init__(self):
        self.start_time: float = time.time()
        self.total_requests: int = 0
        self.requests_today: int = 0
        self.last_reset_date: str = datetime.now().strftime("%Y-%m-%d")
        self.response_times: list = []  # Last 1000 response times
        self.cache_hits: int = 0
        self.cache_misses: int = 0

    def record_request(self, response_time_ms: float):
        """Record a request for stats"""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.last_reset_date:
            self.requests_today = 0
            self.last_reset_date = today

        self.total_requests += 1
        self.requests_today += 1

        self.response_times.append(response_time_ms)
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.start_time

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total


app_state = AppState()
rate_card_db: Optional[RateCardDB] = None
comparator: Optional[RideshareComparison] = None


# === Lifespan ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global rate_card_db, comparator

    logger.info("Starting MCP Aggregator API...")

    # Initialize rate card database
    rate_card_db = RateCardDB()
    logger.info(f"Loaded rate cards for {len(rate_card_db.get_supported_cities())} cities")

    # Initialize comparator
    comparator = RideshareComparison(rate_card_db)
    logger.info("RideshareComparison initialized")

    yield

    logger.info("Shutting down MCP Aggregator API...")


# === FastAPI App ===

config = get_config()

app = FastAPI(
    title=config.api_title,
    description=config.api_description,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# === Middleware ===

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_tracking(request: Request, call_next):
    """Add request ID and timing to all requests"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # Add request ID to state
    request.state.request_id = request_id

    # Process request
    response: Response = await call_next(request)

    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000
    app_state.record_request(response_time_ms)

    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{response_time_ms:.2f}"

    # Add rate limit headers if present
    if hasattr(request.state, "rate_limit_headers"):
        for key, value in request.state.rate_limit_headers.items():
            response.headers[key] = value

    return response


# === Exception Handlers ===

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    request_id = getattr(request.state, "request_id", "unknown")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, dict) else {
                "code": "HTTP_ERROR",
                "message": str(exc.detail)
            },
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unexpected errors"""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(f"Unexpected error in request {request_id}: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            },
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
    )


# === Helper Functions ===

def location_to_internal(loc_input) -> Location:
    """Convert API location input to internal Location object"""
    return Location(
        latitude=loc_input.latitude,
        longitude=loc_input.longitude,
        address=loc_input.address
    )


def fare_to_response(fare: FareEstimate, pickup_lat: float, pickup_lng: float,
                     dropoff_lat: float, dropoff_lng: float) -> FareEstimateResponse:
    """Convert internal FareEstimate to API response"""
    links = generate_smart_link(
        fare.service,
        pickup_lat, pickup_lng,
        dropoff_lat, dropoff_lng
    )

    return FareEstimateResponse(
        service=fare.service,
        ride_type=fare.ride_type,
        estimate=fare.estimate,
        low_estimate=fare.low_estimate,
        high_estimate=fare.high_estimate,
        surge_multiplier=fare.surge_multiplier,
        distance_miles=fare.distance_miles,
        duration_minutes=fare.duration_minutes,
        confidence=fare.confidence,
        deep_link=links["app_link"],
        web_link=links["web_link"]
    )


# === API Endpoints ===

# --- Health & Info ---

@app.get("/", tags=["Info"])
async def root():
    """API root - returns basic info"""
    return {
        "name": "MCP Aggregator API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint

    Returns service status and uptime information.
    No authentication required.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(),
        uptime_seconds=app_state.uptime_seconds,
        services={
            "rate_cards": "healthy" if rate_card_db else "unavailable",
            "comparator": "healthy" if comparator else "unavailable"
        }
    )


@app.get("/stats", response_model=StatsResponse, tags=["Health"])
async def get_stats(key_data: APIKeyData = Depends(validate_api_key)):
    """
    Get API statistics

    Requires authentication.
    """
    return StatsResponse(
        total_requests=app_state.total_requests,
        requests_today=app_state.requests_today,
        avg_response_time_ms=app_state.avg_response_time,
        cache_hit_rate=app_state.cache_hit_rate,
        supported_cities=len(rate_card_db.get_supported_cities()) if rate_card_db else 0,
        rate_cards_loaded=rate_card_db.get_stats()["total_rate_cards"] if rate_card_db else 0
    )


# --- Cities ---

@app.get("/v1/cities", response_model=CityResponse, tags=["Cities"])
async def get_supported_cities(key_data: APIKeyData = Depends(validate_api_key)):
    """
    Get list of supported cities

    Returns all cities where rideshare comparison is available.
    """
    if not rate_card_db:
        raise HTTPException(status_code=503, detail="Rate card database not initialized")

    cities = rate_card_db.get_supported_cities()
    return CityResponse(
        cities=cities,
        count=len(cities)
    )


@app.get("/v1/cities/{city}/rates", tags=["Cities"])
async def get_city_rates(
    city: str,
    key_data: APIKeyData = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    Get rate cards for a specific city

    Returns pricing information for all ride types in the specified city.
    """
    if not rate_card_db:
        raise HTTPException(status_code=503, detail="Rate card database not initialized")

    # Check if city is supported
    if city not in rate_card_db.get_supported_cities():
        raise HTTPException(
            status_code=400,
            detail={
                "code": "UNSUPPORTED_CITY",
                "message": f"City '{city}' is not supported. Use GET /v1/cities for list.",
                "field": "city"
            }
        )

    # Get rates for both services
    result = {
        "city": city,
        "services": {}
    }

    for service in ["uber", "lyft"]:
        ride_types = rate_card_db.get_supported_ride_types(city, service)
        if ride_types:
            result["services"][service] = {}
            for ride_type in ride_types:
                rates = rate_card_db.get_rates(city, service, ride_type)
                if rates:
                    result["services"][service][ride_type] = rates

    result["last_updated"] = rate_card_db.last_updated.isoformat()

    return result


# --- Comparison (Main Feature) ---

@app.post("/v1/compare", response_model=CompareResponse, tags=["Comparison"])
async def compare_prices(
    request: Request,
    compare_request: CompareRequest,
    key_data: APIKeyData = Depends(validate_api_key)
):
    """
    Compare Uber and Lyft prices

    Main endpoint for rideshare price comparison. Returns fare estimates
    for both services along with a recommendation.

    **Request Body:**
    - `pickup`: Pickup location (lat, lng, optional address)
    - `dropoff`: Dropoff location (lat, lng, optional address)
    - `city`: Optional city override (auto-detected from coordinates)

    **Response:**
    - Fare estimates for Uber and Lyft
    - Recommendation (cheaper option)
    - Deep links to book directly
    - Confidence score
    """
    if not comparator:
        raise HTTPException(status_code=503, detail="Comparison service not initialized")

    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])

    # Convert to internal types
    pickup = location_to_internal(compare_request.pickup)
    dropoff = location_to_internal(compare_request.dropoff)

    try:
        # Run comparison
        result = comparator.compare_prices(
            pickup=pickup,
            dropoff=dropoff,
            city=compare_request.city
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "COMPARISON_ERROR",
                "message": str(e)
            }
        )

    # Convert to response format
    uber_response = fare_to_response(
        result["uber"],
        compare_request.pickup.latitude,
        compare_request.pickup.longitude,
        compare_request.dropoff.latitude,
        compare_request.dropoff.longitude
    )

    lyft_response = fare_to_response(
        result["lyft"],
        compare_request.pickup.latitude,
        compare_request.pickup.longitude,
        compare_request.dropoff.latitude,
        compare_request.dropoff.longitude
    )

    # Calculate savings percentage
    cheaper = min(result["uber"].estimate, result["lyft"].estimate)
    expensive = max(result["uber"].estimate, result["lyft"].estimate)
    savings_percent = ((expensive - cheaper) / expensive) * 100 if expensive > 0 else 0

    return CompareResponse(
        request_id=request_id,
        timestamp=datetime.now(),
        city=result["city"],
        distance_miles=result["distance_miles"],
        duration_minutes=result["duration_minutes"],
        uber=uber_response,
        lyft=lyft_response,
        recommendation=result["recommendation"],
        savings=result["savings"],
        savings_percent=round(savings_percent, 1),
        confidence=min(result["uber"].confidence, result["lyft"].confidence)
    )


@app.post("/v1/route", tags=["Comparison"])
async def route_query(
    request: Request,
    query_request: NaturalLanguageRequest,
    key_data: APIKeyData = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    Natural language route query

    Accepts natural language queries like "Compare Uber and Lyft from
    Union Square SF to SFO airport" and returns price comparison.

    Note: This is a simplified endpoint. Full natural language processing
    would require integration with an LLM for entity extraction.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])

    # For now, return a helpful message about the structured endpoint
    # In production, this would parse the query and call compare_prices
    return {
        "request_id": request_id,
        "message": "Natural language processing is in development. Please use POST /v1/compare with structured coordinates.",
        "hint": "Use Google Maps to get coordinates, then call /v1/compare with lat/lng values.",
        "example": {
            "endpoint": "POST /v1/compare",
            "body": {
                "pickup": {"latitude": 37.7879, "longitude": -122.4074},
                "dropoff": {"latitude": 37.6213, "longitude": -122.3790}
            }
        }
    }


# --- Deep Links ---

@app.get("/v1/deeplink/{service}", tags=["Deep Links"])
async def get_deep_link(
    service: str,
    pickup_lat: float,
    pickup_lng: float,
    dropoff_lat: float,
    dropoff_lng: float,
    mobile: bool = True,
    key_data: APIKeyData = Depends(validate_api_key)
) -> Dict[str, str]:
    """
    Generate deep link for a rideshare service

    Returns URLs to open Uber or Lyft app with route pre-filled.
    """
    if service.lower() not in ["uber", "lyft"]:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SERVICE",
                "message": "Service must be 'uber' or 'lyft'",
                "field": "service"
            }
        )

    links = generate_smart_link(
        service.lower(),
        pickup_lat, pickup_lng,
        dropoff_lat, dropoff_lng,
        mobile=mobile
    )

    return {
        "service": service.lower(),
        "app_link": links["app_link"],
        "web_link": links["web_link"],
        "primary": links["primary"]
    }


# === Main ===

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        workers=1 if config.debug else config.workers,
        log_level=config.log_level.lower()
    )
