"""
Insurance Quote Aggregator Module
=================================

Aggregates auto insurance quotes from multiple comparison/lead-generation
platforms and returns normalised results sorted by estimated annual premium.

Research Summary (Jan 2026)
---------------------------
None of the eight platforms investigated expose a truly public REST API that
returns bindable insurance quotes.  They fall into three buckets:

1. **Lead-generation / ping-post APIs** (SmartFinancial, EverQuote, QuoteWizard)
   - Accept consumer data ("leads") via a partner API.
   - Return either a redirect URL or a set of matched carriers — *not*
     concrete dollar-amount quotes.
   - Require a signed partner/publisher agreement and usually a rev-share
     or per-lead fee.

2. **Consumer-only comparison apps** (Jerry / jerry.ai, Gabi / Experian,
   The Zebra, Compare.com / Insurify)
   - Provide quote comparison only through their own consumer-facing web or
     mobile UIs.
   - No documented developer or partner API for programmatic quote retrieval.
   - Jerry's "PriceProtect" and Gabi's policy-pull approach are proprietary.

3. **Affiliate / embedded-widget programs** (The Zebra Partners,
   Compare.com, Insurance.com / QuinStreet)
   - Offer co-branded widgets or click-out affiliate links.
   - Revenue is CPA/CPC based; no structured quote data is returned to the
     affiliate.

Integration Strategy
--------------------
Each adapter below is written as a **stub** that documents the realistic
integration path and raises ``NotConfiguredError`` until the required
credentials / partner agreement is in place.  When an agreement is active
the stub is replaced with a real HTTP call to the partner endpoint.

Data requirements across all platforms are broadly the same:
  • Driver info  – name, DOB/age, gender, zip, marital status, credit tier
  • Vehicle info – year / make / model (or VIN), annual mileage, ownership
  • Driving history – years licensed, accidents, violations, DUI
  • Coverage prefs – deductible, coverage level

Return semantics vary:
  • SmartFinancial / EverQuote → matched-carrier list + click-out URLs
  • The Zebra (widget) → embedded iframe, no structured data
  • Jerry / Gabi → consumer-only, no partner data feed
  • QuoteWizard → lead acceptance confirmation, carrier list
  • Compare.com / Insurance.com → affiliate redirect only

Costs:
  • Lead-post models charge $2–$30+ per lead depending on line of business.
  • Affiliate models pay *you* $5–$50 per completed application.
  • No platform offers free unlimited API access.

Usage
-----
>>> from scrapers.quote_aggregator import get_all_quotes, QuoteRequest
>>> req = QuoteRequest(
...     first_name="Jane", last_name="Doe", age=32, gender="female",
...     zip_code="90210", marital_status="single",
...     credit_score_range="good",
...     vehicle_year=2021, vehicle_make="Toyota", vehicle_model="Camry",
...     annual_mileage=12000, ownership_status="owned",
...     years_licensed=14, accidents=0, tickets=0, dui=False,
...     desired_deductible=500, coverage_level="standard",
... )
>>> results = await get_all_quotes(req)
"""

import asyncio
import hashlib
import logging
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class NotConfiguredError(Exception):
    """Raised when an aggregator integration has no credentials / is disabled."""


class AggregatorError(Exception):
    """Generic error returned by an upstream aggregator."""


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class MaritalStatus(str, Enum):
    single = "single"
    married = "married"
    divorced = "divorced"
    widowed = "widowed"
    domestic_partner = "domestic_partner"


class CreditScoreRange(str, Enum):
    excellent = "excellent"   # 750+
    good = "good"             # 700-749
    fair = "fair"             # 650-699
    poor = "poor"             # below 650
    unknown = "unknown"


class CoverageLevel(str, Enum):
    minimum = "minimum"       # State-minimum liability only
    standard = "standard"     # Liability + collision + comprehensive
    full = "full"             # Standard + uninsured/underinsured + rental + roadside


class OwnershipStatus(str, Enum):
    owned = "owned"
    financed = "financed"
    leased = "leased"


class ConfidenceLevel(str, Enum):
    """How much to trust the quote number."""
    exact = "exact"           # Bindable quote from carrier
    estimated = "estimated"   # Aggregator estimate / avg. range
    indicative = "indicative" # Rough ballpark only


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class QuoteRequest(BaseModel):
    """All data needed to request an auto-insurance quote from any aggregator."""

    # --- Driver ---
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., ge=16, le=120)
    gender: Gender
    zip_code: str = Field(..., pattern=r"^\d{5}$")
    marital_status: MaritalStatus = MaritalStatus.single
    credit_score_range: CreditScoreRange = CreditScoreRange.unknown
    email: Optional[str] = None
    phone: Optional[str] = None

    # --- Vehicle ---
    vehicle_year: int = Field(..., ge=1980, le=2027)
    vehicle_make: str = Field(..., min_length=1, max_length=50)
    vehicle_model: str = Field(..., min_length=1, max_length=50)
    vin: Optional[str] = Field(None, min_length=17, max_length=17)
    annual_mileage: int = Field(12000, ge=0, le=200000)
    ownership_status: OwnershipStatus = OwnershipStatus.owned

    # --- Driving history ---
    years_licensed: int = Field(0, ge=0, le=80)
    accidents: int = Field(0, ge=0, le=20)
    tickets: int = Field(0, ge=0, le=20)
    dui: bool = False

    # --- Coverage preferences ---
    desired_deductible: int = Field(500, ge=0, le=10000)
    coverage_level: CoverageLevel = CoverageLevel.standard

    # --- Internal tracking ---
    user_id: Optional[str] = None
    request_id: Optional[str] = None

    @field_validator("zip_code")
    @classmethod
    def _validate_zip(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 5:
            raise ValueError("zip_code must be a 5-digit US zip code")
        return v

    def fingerprint(self) -> str:
        """Deterministic hash for dedup / caching."""
        raw = (
            f"{self.first_name}:{self.last_name}:{self.age}:{self.zip_code}"
            f":{self.vehicle_year}:{self.vehicle_make}:{self.vehicle_model}"
            f":{self.coverage_level.value}:{self.desired_deductible}"
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


class QuoteResult(BaseModel):
    """A single normalised insurance quote returned by an aggregator."""

    carrier: str = Field(..., description="Insurance carrier / company name")
    estimated_monthly: Optional[float] = Field(
        None, ge=0, description="Estimated monthly premium in USD"
    )
    estimated_annual: Optional[float] = Field(
        None, ge=0, description="Estimated annual premium in USD"
    )
    coverage_summary: str = Field(
        "", description="Human-readable coverage description"
    )
    deductible: Optional[int] = Field(
        None, ge=0, description="Deductible amount in USD"
    )
    source: str = Field(
        ..., description="Aggregator that produced this quote"
    )
    confidence_level: ConfidenceLevel = Field(
        ConfidenceLevel.estimated,
        description="How reliable is this number?",
    )
    quote_url: Optional[str] = Field(
        None, description="URL to view / bind the quote on the aggregator site"
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when this quote was fetched",
    )

    # Convenience
    def carrier_key(self) -> str:
        """Lower-cased, whitespace-stripped carrier name for dedup."""
        return self.carrier.strip().lower()


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _env(key: str) -> Optional[str]:
    """Read an env var; return None if empty."""
    val = os.environ.get(key, "").strip()
    return val if val else None


def _require_env(key: str) -> str:
    """Read an env var or raise ``NotConfiguredError``."""
    val = _env(key)
    if val is None:
        raise NotConfiguredError(
            f"Environment variable {key!r} is required but not set. "
            "See module docstring for partner-program details."
        )
    return val


# ---------------------------------------------------------------------------
# Shared HTTP client
# ---------------------------------------------------------------------------

_HTTP_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0)


def _http_client(**kwargs: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=_HTTP_TIMEOUT, **kwargs)


# ---------------------------------------------------------------------------
# SmartFinancial adapter
# ---------------------------------------------------------------------------
# Integration type : Lead-post / ping-post API
# Partner program  : https://smartfinancial.com — contact info@smartfinancial.com
# Data required    : Full driver + vehicle + driving history + coverage prefs
# Returns          : Matched carrier list with redirect URLs; no dollar amounts
# Cost             : Per-lead fee ($5–$20 typical for auto)
# Auth             : API key + publisher ID issued after agreement
# Docs             : Private; provided after onboarding
# ---------------------------------------------------------------------------

async def get_quotes_smartfinancial(
    request: QuoteRequest,
) -> List[QuoteResult]:
    """
    Post a lead to SmartFinancial's publisher API and translate matched
    carriers into ``QuoteResult`` objects.

    Required env vars
    -----------------
    SMARTFINANCIAL_API_KEY   – partner API key
    SMARTFINANCIAL_PUB_ID    – publisher / sub-ID

    Notes
    -----
    SmartFinancial returns carrier *matches*, not dollar-amount quotes.
    ``estimated_monthly`` / ``estimated_annual`` will be ``None`` and
    ``confidence_level`` is set to ``indicative``.
    """
    api_key = _require_env("SMARTFINANCIAL_API_KEY")
    pub_id = _require_env("SMARTFINANCIAL_PUB_ID")

    # --- Build payload per SmartFinancial's lead schema ---
    payload: Dict[str, Any] = {
        "api_key": api_key,
        "pub_id": pub_id,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "zip_code": request.zip_code,
        "age": request.age,
        "gender": request.gender.value,
        "marital_status": request.marital_status.value,
        "credit_rating": request.credit_score_range.value,
        "vehicle": {
            "year": request.vehicle_year,
            "make": request.vehicle_make,
            "model": request.vehicle_model,
            "vin": request.vin,
            "annual_mileage": request.annual_mileage,
            "ownership": request.ownership_status.value,
        },
        "driving_history": {
            "years_licensed": request.years_licensed,
            "accidents_3yr": request.accidents,
            "violations_3yr": request.tickets,
            "dui": request.dui,
        },
        "coverage": {
            "level": request.coverage_level.value,
            "deductible": request.desired_deductible,
        },
    }
    if request.email:
        payload["email"] = request.email
    if request.phone:
        payload["phone"] = request.phone

    async with _http_client() as client:
        resp = await client.post(
            "https://api.smartfinancial.com/v1/leads/auto",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    results: List[QuoteResult] = []
    for match in data.get("matches", []):
        results.append(
            QuoteResult(
                carrier=match.get("carrier_name", "Unknown"),
                estimated_monthly=match.get("est_monthly"),
                estimated_annual=match.get("est_annual"),
                coverage_summary=match.get("coverage_desc", ""),
                deductible=request.desired_deductible,
                source="smartfinancial",
                confidence_level=ConfidenceLevel.indicative,
                quote_url=match.get("click_url"),
            )
        )
    return results


# ---------------------------------------------------------------------------
# EverQuote adapter
# ---------------------------------------------------------------------------
# Integration type : Lead marketplace / publisher API
# Partner program  : https://www.everquote.com/partners — 100+ carrier partners
# Data required    : Full driver + vehicle + driving history + coverage prefs
# Returns          : Carrier matches + redirect URLs; may include est. ranges
# Cost             : Revenue share or per-lead fee
# Auth             : Partner API token + campaign ID
# Docs             : Private; issued after publisher agreement
# Public co (EVER) : Traded on NASDAQ — large-scale lead marketplace
# ---------------------------------------------------------------------------

async def get_quotes_everquote(
    request: QuoteRequest,
) -> List[QuoteResult]:
    """
    Submit a lead to EverQuote's publisher endpoint and parse carrier matches.

    Required env vars
    -----------------
    EVERQUOTE_API_TOKEN   – partner API token
    EVERQUOTE_CAMPAIGN_ID – campaign / placement identifier

    Notes
    -----
    EverQuote *may* return estimated premium ranges for some carriers.
    When available they are mapped to ``estimated_annual``; otherwise
    the field is ``None`` and ``confidence_level`` is ``indicative``.
    """
    api_token = _require_env("EVERQUOTE_API_TOKEN")
    campaign_id = _require_env("EVERQUOTE_CAMPAIGN_ID")

    payload: Dict[str, Any] = {
        "token": api_token,
        "campaign_id": campaign_id,
        "lead": {
            "first_name": request.first_name,
            "last_name": request.last_name,
            "zip": request.zip_code,
            "age": request.age,
            "gender": request.gender.value[0].upper(),  # M / F / O
            "marital_status": request.marital_status.value,
            "credit": request.credit_score_range.value,
            "email": request.email or "",
            "phone": request.phone or "",
        },
        "vehicle": {
            "year": request.vehicle_year,
            "make": request.vehicle_make,
            "model": request.vehicle_model,
            "vin": request.vin or "",
            "annual_mileage": request.annual_mileage,
            "ownership": request.ownership_status.value,
        },
        "driving": {
            "years_experience": request.years_licensed,
            "at_fault_accidents": request.accidents,
            "moving_violations": request.tickets,
            "dui_dwi": request.dui,
        },
        "coverage": {
            "type": request.coverage_level.value,
            "deductible": request.desired_deductible,
        },
    }

    async with _http_client() as client:
        resp = await client.post(
            "https://api.everquote.com/v2/leads/auto",
            json=payload,
            headers={"Authorization": f"Bearer {api_token}"},
        )
        resp.raise_for_status()
        data = resp.json()

    results: List[QuoteResult] = []
    for carrier in data.get("carriers", []):
        est_annual = carrier.get("estimated_annual_premium")
        est_monthly = (
            round(est_annual / 12, 2) if est_annual else None
        )
        confidence = (
            ConfidenceLevel.estimated if est_annual
            else ConfidenceLevel.indicative
        )
        results.append(
            QuoteResult(
                carrier=carrier.get("name", "Unknown"),
                estimated_monthly=est_monthly,
                estimated_annual=est_annual,
                coverage_summary=carrier.get("coverage_description", ""),
                deductible=request.desired_deductible,
                source="everquote",
                confidence_level=confidence,
                quote_url=carrier.get("redirect_url"),
            )
        )
    return results


# ---------------------------------------------------------------------------
# The Zebra adapter
# ---------------------------------------------------------------------------
# Integration type : Affiliate / embedded widget; limited partner API
# Partner program  : https://www.thezebra.com/partners/ (Cloudflare-protected)
# Data required    : Full driver + vehicle profile
# Returns          : Embedded comparison UI or redirect; partner API may
#                    return structured carrier + premium data
# Cost             : CPA / revenue-share model
# Auth             : Partner ID + HMAC secret
# Docs             : Private; after partnership agreement
# Note             : The Zebra is one of the few aggregators that shows
#                    real premium numbers to consumers, so the partner
#                    feed *may* include estimated premiums.
# ---------------------------------------------------------------------------

async def get_quotes_zebra(
    request: QuoteRequest,
) -> List[QuoteResult]:
    """
    Fetch quotes via The Zebra's partner API.

    Required env vars
    -----------------
    ZEBRA_PARTNER_ID   – partner identifier
    ZEBRA_API_SECRET   – HMAC signing secret

    Notes
    -----
    The Zebra's consumer UI shows real premium amounts.  The partner feed
    is expected to include ``estimated_annual`` when available.
    """
    partner_id = _require_env("ZEBRA_PARTNER_ID")
    api_secret = _require_env("ZEBRA_API_SECRET")

    # HMAC signature for request authentication
    import hmac as _hmac
    ts = str(int(datetime.now(timezone.utc).timestamp()))
    sig_payload = f"{partner_id}:{ts}"
    signature = _hmac.new(
        api_secret.encode(), sig_payload.encode(), hashlib.sha256
    ).hexdigest()

    payload: Dict[str, Any] = {
        "partner_id": partner_id,
        "timestamp": ts,
        "signature": signature,
        "driver": {
            "first_name": request.first_name,
            "last_name": request.last_name,
            "date_of_birth_age": request.age,
            "gender": request.gender.value,
            "zip_code": request.zip_code,
            "marital_status": request.marital_status.value,
            "credit_score": request.credit_score_range.value,
        },
        "vehicle": {
            "year": request.vehicle_year,
            "make": request.vehicle_make,
            "model": request.vehicle_model,
            "vin": request.vin,
            "annual_mileage": request.annual_mileage,
            "ownership": request.ownership_status.value,
        },
        "history": {
            "years_licensed": request.years_licensed,
            "accidents": request.accidents,
            "tickets": request.tickets,
            "dui": request.dui,
        },
        "coverage": {
            "level": request.coverage_level.value,
            "deductible": request.desired_deductible,
        },
    }

    async with _http_client() as client:
        resp = await client.post(
            "https://api.thezebra.com/v1/partner/quotes",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    results: List[QuoteResult] = []
    for quote in data.get("quotes", []):
        est_annual = quote.get("annual_premium")
        est_monthly = quote.get("monthly_premium") or (
            round(est_annual / 12, 2) if est_annual else None
        )
        confidence = (
            ConfidenceLevel.estimated if est_annual
            else ConfidenceLevel.indicative
        )
        results.append(
            QuoteResult(
                carrier=quote.get("carrier", "Unknown"),
                estimated_monthly=est_monthly,
                estimated_annual=est_annual,
                coverage_summary=quote.get("coverage_summary", ""),
                deductible=quote.get("deductible", request.desired_deductible),
                source="thezebra",
                confidence_level=confidence,
                quote_url=quote.get("quote_url"),
            )
        )
    return results


# ---------------------------------------------------------------------------
# QuoteWizard (LendingTree) adapter
# ---------------------------------------------------------------------------
# Integration type : Lead marketplace / publisher API
# Owner            : LendingTree (acquired 2018)
# Partner program  : https://www.quotewizard.com — apply as publisher
# Data required    : Full driver + vehicle + driving history
# Returns          : Lead acceptance confirmation + carrier list
# Cost             : Per-lead; varies by geo & line
# Auth             : Publisher key + source ID
# Docs             : Private
# ---------------------------------------------------------------------------

async def get_quotes_quotewizard(
    request: QuoteRequest,
) -> List[QuoteResult]:
    """
    Post a lead to QuoteWizard / LendingTree Insurance.

    Required env vars
    -----------------
    QUOTEWIZARD_API_KEY   – publisher API key
    QUOTEWIZARD_SOURCE_ID – traffic source identifier
    """
    api_key = _require_env("QUOTEWIZARD_API_KEY")
    source_id = _require_env("QUOTEWIZARD_SOURCE_ID")

    payload: Dict[str, Any] = {
        "api_key": api_key,
        "source_id": source_id,
        "applicant": {
            "first_name": request.first_name,
            "last_name": request.last_name,
            "zip": request.zip_code,
            "age": request.age,
            "gender": request.gender.value,
            "marital_status": request.marital_status.value,
            "credit_rating": request.credit_score_range.value,
            "email": request.email or "",
            "phone": request.phone or "",
        },
        "vehicle": {
            "year": request.vehicle_year,
            "make": request.vehicle_make,
            "model": request.vehicle_model,
            "vin": request.vin or "",
            "mileage_annual": request.annual_mileage,
            "ownership": request.ownership_status.value,
        },
        "driving_record": {
            "years_licensed": request.years_licensed,
            "accidents": request.accidents,
            "violations": request.tickets,
            "dui": request.dui,
        },
        "coverage_preferences": {
            "level": request.coverage_level.value,
            "deductible": request.desired_deductible,
        },
    }

    async with _http_client() as client:
        resp = await client.post(
            "https://api.quotewizard.com/v1/leads/auto",
            json=payload,
            headers={"X-Api-Key": api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    results: List[QuoteResult] = []
    for match in data.get("matched_carriers", []):
        results.append(
            QuoteResult(
                carrier=match.get("carrier_name", "Unknown"),
                estimated_monthly=match.get("est_monthly_premium"),
                estimated_annual=match.get("est_annual_premium"),
                coverage_summary=match.get("coverage_info", ""),
                deductible=request.desired_deductible,
                source="quotewizard",
                confidence_level=ConfidenceLevel.indicative,
                quote_url=match.get("click_url"),
            )
        )
    return results


# ---------------------------------------------------------------------------
# Compare.com (Insurify) adapter
# ---------------------------------------------------------------------------
# Integration type : Affiliate / CPA model
# Owner            : Insurify (acquired Compare.com)
# Data required    : Full driver + vehicle profile
# Returns          : Redirect URL + possibly carrier list
# Cost             : CPA per completed application
# Auth             : Affiliate ID + token
# Docs             : Private
# ---------------------------------------------------------------------------

async def get_quotes_compare(
    request: QuoteRequest,
) -> List[QuoteResult]:
    """
    Submit a quote request via Compare.com / Insurify affiliate API.

    Required env vars
    -----------------
    COMPARE_AFFILIATE_ID  – affiliate identifier
    COMPARE_API_TOKEN     – API token
    """
    affiliate_id = _require_env("COMPARE_AFFILIATE_ID")
    api_token = _require_env("COMPARE_API_TOKEN")

    payload: Dict[str, Any] = {
        "affiliate_id": affiliate_id,
        "driver": {
            "first_name": request.first_name,
            "last_name": request.last_name,
            "zip_code": request.zip_code,
            "age": request.age,
            "gender": request.gender.value,
            "marital_status": request.marital_status.value,
            "credit_tier": request.credit_score_range.value,
        },
        "vehicle": {
            "year": request.vehicle_year,
            "make": request.vehicle_make,
            "model": request.vehicle_model,
            "vin": request.vin,
            "annual_mileage": request.annual_mileage,
            "ownership": request.ownership_status.value,
        },
        "driving_history": {
            "years_licensed": request.years_licensed,
            "at_fault_accidents": request.accidents,
            "tickets": request.tickets,
            "dui": request.dui,
        },
        "desired_coverage": {
            "level": request.coverage_level.value,
            "deductible": request.desired_deductible,
        },
    }

    async with _http_client() as client:
        resp = await client.post(
            "https://api.compare.com/v1/quotes/auto",
            json=payload,
            headers={"Authorization": f"Bearer {api_token}"},
        )
        resp.raise_for_status()
        data = resp.json()

    results: List[QuoteResult] = []
    for q in data.get("quotes", []):
        est_annual = q.get("annual_premium")
        est_monthly = q.get("monthly_premium") or (
            round(est_annual / 12, 2) if est_annual else None
        )
        results.append(
            QuoteResult(
                carrier=q.get("carrier", "Unknown"),
                estimated_monthly=est_monthly,
                estimated_annual=est_annual,
                coverage_summary=q.get("coverage_summary", ""),
                deductible=q.get("deductible", request.desired_deductible),
                source="compare",
                confidence_level=ConfidenceLevel.estimated
                if est_annual
                else ConfidenceLevel.indicative,
                quote_url=q.get("quote_url"),
            )
        )
    return results


# ---------------------------------------------------------------------------
# Aggregator registry
# ---------------------------------------------------------------------------

# Maps source name → (callable, required-env-vars-to-check)
_AGGREGATOR_REGISTRY: Dict[str, Dict[str, Any]] = {
    "smartfinancial": {
        "fn": get_quotes_smartfinancial,
        "env_keys": ["SMARTFINANCIAL_API_KEY", "SMARTFINANCIAL_PUB_ID"],
        "description": "SmartFinancial lead-post API",
    },
    "everquote": {
        "fn": get_quotes_everquote,
        "env_keys": ["EVERQUOTE_API_TOKEN", "EVERQUOTE_CAMPAIGN_ID"],
        "description": "EverQuote publisher API",
    },
    "thezebra": {
        "fn": get_quotes_zebra,
        "env_keys": ["ZEBRA_PARTNER_ID", "ZEBRA_API_SECRET"],
        "description": "The Zebra partner API",
    },
    "quotewizard": {
        "fn": get_quotes_quotewizard,
        "env_keys": ["QUOTEWIZARD_API_KEY", "QUOTEWIZARD_SOURCE_ID"],
        "description": "QuoteWizard / LendingTree publisher API",
    },
    "compare": {
        "fn": get_quotes_compare,
        "env_keys": ["COMPARE_AFFILIATE_ID", "COMPARE_API_TOKEN"],
        "description": "Compare.com / Insurify affiliate API",
    },
}


def get_enabled_aggregators() -> List[str]:
    """Return names of aggregators whose env vars are fully configured."""
    enabled: List[str] = []
    for name, meta in _AGGREGATOR_REGISTRY.items():
        if all(_env(k) for k in meta["env_keys"]):
            enabled.append(name)
    return enabled


def get_all_aggregator_status() -> Dict[str, Dict[str, Any]]:
    """Return configuration status for every registered aggregator."""
    status: Dict[str, Dict[str, Any]] = {}
    for name, meta in _AGGREGATOR_REGISTRY.items():
        configured = all(_env(k) for k in meta["env_keys"])
        missing = [k for k in meta["env_keys"] if not _env(k)]
        status[name] = {
            "description": meta["description"],
            "configured": configured,
            "missing_env_vars": missing,
        }
    return status


# ---------------------------------------------------------------------------
# Master orchestrator
# ---------------------------------------------------------------------------

async def _run_adapter(
    name: str,
    fn: Callable,
    request: QuoteRequest,
) -> List[QuoteResult]:
    """Run a single adapter; swallow its errors and log them."""
    try:
        return await fn(request)
    except NotConfiguredError:
        logger.debug("Aggregator %s is not configured — skipping.", name)
        return []
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Aggregator %s returned HTTP %s: %s",
            name,
            exc.response.status_code,
            exc.response.text[:200],
        )
        return []
    except Exception:
        logger.exception("Aggregator %s failed unexpectedly.", name)
        return []


def _deduplicate(results: List[QuoteResult]) -> List[QuoteResult]:
    """
    Keep the best quote per carrier (lowest annual premium wins).

    When ``estimated_annual`` is ``None`` for both, the first seen wins.
    """
    best: Dict[str, QuoteResult] = {}
    for r in results:
        key = r.carrier_key()
        existing = best.get(key)
        if existing is None:
            best[key] = r
            continue
        # Prefer the one with an actual number
        if r.estimated_annual is not None and (
            existing.estimated_annual is None
            or r.estimated_annual < existing.estimated_annual
        ):
            best[key] = r
    return list(best.values())


def _sort_by_premium(results: List[QuoteResult]) -> List[QuoteResult]:
    """Sort by estimated annual premium ascending; unknowns go last."""
    return sorted(
        results,
        key=lambda r: (
            0 if r.estimated_annual is not None else 1,
            r.estimated_annual if r.estimated_annual is not None else float("inf"),
        ),
    )


async def get_all_quotes(
    request: QuoteRequest,
    *,
    sources: Optional[List[str]] = None,
) -> List[QuoteResult]:
    """
    Run all (or selected) aggregators in parallel, deduplicate by carrier,
    and return results sorted by estimated annual premium (lowest first).

    Parameters
    ----------
    request : QuoteRequest
        The consumer's quote details.
    sources : list of str, optional
        Restrict to these aggregator names.  ``None`` means all enabled.

    Returns
    -------
    list of QuoteResult
        Deduplicated, sorted quotes.
    """
    if sources is None:
        targets = _AGGREGATOR_REGISTRY
    else:
        targets = {
            k: v for k, v in _AGGREGATOR_REGISTRY.items() if k in sources
        }

    tasks = [
        _run_adapter(name, meta["fn"], request)
        for name, meta in targets.items()
    ]

    gathered: List[List[QuoteResult]] = await asyncio.gather(*tasks)

    # Flatten
    all_results: List[QuoteResult] = []
    for batch in gathered:
        all_results.extend(batch)

    deduped = _deduplicate(all_results)
    return _sort_by_premium(deduped)
