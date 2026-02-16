"""
Insurance Quote API Routes
==========================

FastAPI router providing endpoints for:
  • Submitting a quote request and receiving comparison results
  • Retrieving quote history for a user
  • Auto-filling a quote from a stored user profile
  • Checking aggregator integration status

All routes are mounted under ``/api/quotes``.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

# --- Internal imports ---
# Adjust the import path to match your project layout.  If running with
# ``uvicorn src.main:app`` from the project root, the following should work.
# Otherwise adapt to your PYTHONPATH / package structure.
try:
    from src.scrapers.quote_aggregator import (
        ConfidenceLevel,
        CoverageLevel,
        CreditScoreRange,
        Gender,
        MaritalStatus,
        OwnershipStatus,
        QuoteRequest,
        QuoteResult,
        get_all_aggregator_status,
        get_all_quotes,
        get_enabled_aggregators,
    )
except ImportError:
    # Fallback: flat package or installed as ``scrapers``
    from scrapers.quote_aggregator import (  # type: ignore[no-redef]
        ConfidenceLevel,
        CoverageLevel,
        CreditScoreRange,
        Gender,
        MaritalStatus,
        OwnershipStatus,
        QuoteRequest,
        QuoteResult,
        get_all_aggregator_status,
        get_all_quotes,
        get_enabled_aggregators,
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quotes", tags=["quotes"])

# ---------------------------------------------------------------------------
# In-memory stores (replace with a real DB in production)
# ---------------------------------------------------------------------------

# user_id → list of past QuoteSession
_quote_history: Dict[str, List["QuoteSession"]] = {}

# user_id → saved profile (simplified)
_user_profiles: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# API-level models
# ---------------------------------------------------------------------------


class QuoteRequestBody(BaseModel):
    """
    Public-facing request body for ``POST /api/quotes/``.

    Maps 1-to-1 with the internal ``QuoteRequest`` but lets us version the
    external schema independently.
    """

    # Driver
    first_name: str = Field(..., min_length=1, max_length=50, example="Jane")
    last_name: str = Field(..., min_length=1, max_length=50, example="Doe")
    age: int = Field(..., ge=16, le=120, example=32)
    gender: Gender = Field(..., example="female")
    zip_code: str = Field(..., pattern=r"^\d{5}$", example="90210")
    marital_status: MaritalStatus = Field(
        MaritalStatus.single, example="single"
    )
    credit_score_range: CreditScoreRange = Field(
        CreditScoreRange.unknown, example="good"
    )
    email: Optional[str] = Field(None, example="jane@example.com")
    phone: Optional[str] = Field(None, example="+12125551234")

    # Vehicle
    vehicle_year: int = Field(..., ge=1980, le=2027, example=2021)
    vehicle_make: str = Field(..., min_length=1, max_length=50, example="Toyota")
    vehicle_model: str = Field(
        ..., min_length=1, max_length=50, example="Camry"
    )
    vin: Optional[str] = Field(
        None, min_length=17, max_length=17, example="4T1BF1FK5CU012345"
    )
    annual_mileage: int = Field(12000, ge=0, le=200000, example=12000)
    ownership_status: OwnershipStatus = Field(
        OwnershipStatus.owned, example="owned"
    )

    # Driving history
    years_licensed: int = Field(0, ge=0, le=80, example=14)
    accidents: int = Field(0, ge=0, le=20, example=0)
    tickets: int = Field(0, ge=0, le=20, example=1)
    dui: bool = Field(False, example=False)

    # Coverage
    desired_deductible: int = Field(500, ge=0, le=10000, example=500)
    coverage_level: CoverageLevel = Field(
        CoverageLevel.standard, example="standard"
    )

    # Optional tracking
    user_id: Optional[str] = Field(
        None, description="Associate results with a user account"
    )

    def to_internal(self) -> QuoteRequest:
        """Convert to the internal aggregator request model."""
        return QuoteRequest(**self.dict())


class QuoteResultResponse(BaseModel):
    """Single quote in the API response."""

    carrier: str
    estimated_monthly: Optional[float] = None
    estimated_annual: Optional[float] = None
    coverage_summary: str = ""
    deductible: Optional[int] = None
    source: str
    confidence_level: ConfidenceLevel = ConfidenceLevel.estimated
    quote_url: Optional[str] = None
    retrieved_at: datetime


class QuoteComparisonResponse(BaseModel):
    """Full response for a quote comparison request."""

    request_id: str = Field(..., description="Unique ID for this request")
    user_id: Optional[str] = None
    quotes: List[QuoteResultResponse] = Field(default_factory=list)
    quote_count: int = 0
    sources_queried: List[str] = Field(default_factory=list)
    sources_enabled: List[str] = Field(default_factory=list)
    requested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    duration_ms: Optional[float] = None


class QuoteSession(BaseModel):
    """A stored quote-comparison session for history."""

    request_id: str
    request_summary: str = ""
    quote_count: int = 0
    lowest_annual: Optional[float] = None
    highest_annual: Optional[float] = None
    sources: List[str] = Field(default_factory=list)
    requested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    quotes: List[QuoteResultResponse] = Field(default_factory=list)


class QuoteHistoryResponse(BaseModel):
    """Response for the history endpoint."""

    user_id: str
    total_sessions: int = 0
    sessions: List[QuoteSession] = Field(default_factory=list)


class AggregatorStatusResponse(BaseModel):
    """Status of all registered aggregators."""

    enabled: List[str] = Field(default_factory=list)
    details: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ProfileQuoteRequestBody(BaseModel):
    """Optional overrides when quoting from a stored profile."""

    coverage_level: Optional[CoverageLevel] = None
    desired_deductible: Optional[int] = Field(None, ge=0, le=10000)
    sources: Optional[List[str]] = Field(
        None,
        description="Restrict to specific aggregator sources",
    )


# ---------------------------------------------------------------------------
# Helper: persist a quote session to history
# ---------------------------------------------------------------------------

def _save_to_history(
    user_id: Optional[str],
    request_id: str,
    request: QuoteRequest,
    results: List[QuoteResult],
) -> None:
    if not user_id:
        return

    annuals = [
        r.estimated_annual for r in results if r.estimated_annual is not None
    ]
    session = QuoteSession(
        request_id=request_id,
        request_summary=(
            f"{request.vehicle_year} {request.vehicle_make} "
            f"{request.vehicle_model} — {request.zip_code} — "
            f"{request.coverage_level.value}"
        ),
        quote_count=len(results),
        lowest_annual=min(annuals) if annuals else None,
        highest_annual=max(annuals) if annuals else None,
        sources=list({r.source for r in results}),
        quotes=[QuoteResultResponse(**r.dict()) for r in results],
    )

    _quote_history.setdefault(user_id, []).append(session)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=QuoteComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a quote request",
    description=(
        "Submit driver, vehicle, and coverage details to receive insurance "
        "quote comparisons from all configured aggregator sources.  Results "
        "are deduplicated by carrier and sorted by estimated annual premium "
        "(lowest first)."
    ),
)
async def create_quote_comparison(
    body: QuoteRequestBody,
    sources: Optional[str] = Query(
        None,
        description=(
            "Comma-separated aggregator names to query "
            "(e.g. 'smartfinancial,everquote').  Omit for all enabled."
        ),
    ),
) -> QuoteComparisonResponse:
    """Run a multi-source quote comparison."""
    request_id = uuid.uuid4().hex[:12]
    internal_request = body.to_internal()
    internal_request.request_id = request_id

    # Parse optional source filter
    source_list: Optional[List[str]] = None
    if sources:
        source_list = [s.strip().lower() for s in sources.split(",") if s.strip()]

    enabled = get_enabled_aggregators()
    start = datetime.now(timezone.utc)

    try:
        results = await get_all_quotes(internal_request, sources=source_list)
    except Exception:
        logger.exception("Quote comparison failed for request %s", request_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="One or more aggregators failed.  Please try again.",
        )

    duration_ms = (
        datetime.now(timezone.utc) - start
    ).total_seconds() * 1000

    # Persist to history
    _save_to_history(body.user_id, request_id, internal_request, results)

    return QuoteComparisonResponse(
        request_id=request_id,
        user_id=body.user_id,
        quotes=[QuoteResultResponse(**r.dict()) for r in results],
        quote_count=len(results),
        sources_queried=source_list or list(get_all_aggregator_status().keys()),
        sources_enabled=enabled,
        requested_at=start,
        duration_ms=round(duration_ms, 1),
    )


@router.get(
    "/history/{user_id}",
    response_model=QuoteHistoryResponse,
    summary="Get quote history",
    description="Retrieve all previous quote-comparison sessions for a user.",
)
async def get_quote_history(
    user_id: str,
    limit: int = Query(20, ge=1, le=100, description="Max sessions to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> QuoteHistoryResponse:
    """Return paginated quote history for a user."""
    sessions = _quote_history.get(user_id, [])
    # Most recent first
    sessions_sorted = sorted(
        sessions, key=lambda s: s.requested_at, reverse=True
    )
    page = sessions_sorted[offset : offset + limit]

    return QuoteHistoryResponse(
        user_id=user_id,
        total_sessions=len(sessions),
        sessions=page,
    )


@router.post(
    "/from-profile/{user_id}",
    response_model=QuoteComparisonResponse,
    summary="Quote from saved profile",
    description=(
        "Auto-fill a quote request from the user's stored profile and "
        "immediately run a comparison.  Optional overrides for coverage "
        "level and deductible can be provided in the request body."
    ),
)
async def quote_from_profile(
    user_id: str,
    body: Optional[ProfileQuoteRequestBody] = None,
) -> QuoteComparisonResponse:
    """Build a QuoteRequest from the user's profile and run comparison."""
    profile = _user_profiles.get(user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No saved profile found for user '{user_id}'.  "
            "Please create a profile first or use POST /api/quotes/ directly.",
        )

    # Merge profile data with any overrides
    overrides: Dict[str, Any] = {}
    if body:
        if body.coverage_level is not None:
            overrides["coverage_level"] = body.coverage_level
        if body.desired_deductible is not None:
            overrides["desired_deductible"] = body.desired_deductible

    try:
        merged = {**profile, **overrides, "user_id": user_id}
        request_body = QuoteRequestBody(**merged)
    except Exception as exc:
        logger.error("Failed to build quote from profile %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Stored profile is incomplete or invalid: {exc}",
        )

    # Delegate to the main endpoint logic
    source_list: Optional[List[str]] = None
    if body and body.sources:
        source_list = body.sources

    request_id = uuid.uuid4().hex[:12]
    internal_request = request_body.to_internal()
    internal_request.request_id = request_id
    internal_request.user_id = user_id

    enabled = get_enabled_aggregators()
    start = datetime.now(timezone.utc)

    try:
        results = await get_all_quotes(internal_request, sources=source_list)
    except Exception:
        logger.exception(
            "Profile-based quote comparison failed for user %s", user_id
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="One or more aggregators failed.  Please try again.",
        )

    duration_ms = (
        datetime.now(timezone.utc) - start
    ).total_seconds() * 1000

    _save_to_history(user_id, request_id, internal_request, results)

    return QuoteComparisonResponse(
        request_id=request_id,
        user_id=user_id,
        quotes=[QuoteResultResponse(**r.dict()) for r in results],
        quote_count=len(results),
        sources_queried=source_list or list(get_all_aggregator_status().keys()),
        sources_enabled=enabled,
        requested_at=start,
        duration_ms=round(duration_ms, 1),
    )


# ---------------------------------------------------------------------------
# Utility / admin routes
# ---------------------------------------------------------------------------


@router.get(
    "/status",
    response_model=AggregatorStatusResponse,
    summary="Aggregator status",
    description="Check which aggregator integrations are configured and ready.",
)
async def aggregator_status() -> AggregatorStatusResponse:
    """Return configuration status of all registered aggregators."""
    return AggregatorStatusResponse(
        enabled=get_enabled_aggregators(),
        details=get_all_aggregator_status(),
    )


@router.delete(
    "/history/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear quote history",
    description="Delete all stored quote history for a user.",
)
async def clear_quote_history(user_id: str) -> None:
    """Remove all quote sessions for a user."""
    _quote_history.pop(user_id, None)


# ---------------------------------------------------------------------------
# Profile management (minimal — production would live in a separate router)
# ---------------------------------------------------------------------------


@router.put(
    "/profile/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Save / update user profile",
    description=(
        "Store driver and vehicle details so future quotes can be "
        "auto-filled via ``POST /api/quotes/from-profile/{user_id}``."
    ),
)
async def save_profile(
    user_id: str,
    body: QuoteRequestBody,
) -> Dict[str, str]:
    """Persist a user profile (in-memory for now)."""
    _user_profiles[user_id] = body.dict()
    return {"status": "saved", "user_id": user_id}


@router.get(
    "/profile/{user_id}",
    response_model=QuoteRequestBody,
    summary="Get user profile",
    description="Retrieve the stored profile for a user.",
)
async def get_profile(user_id: str) -> QuoteRequestBody:
    """Return the stored profile."""
    profile = _user_profiles.get(user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No profile found for user '{user_id}'.",
        )
    return QuoteRequestBody(**profile)
