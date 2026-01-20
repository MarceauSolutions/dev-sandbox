"""
MCP Routing Engine

Intelligently routes requests to the best available MCP based on:
- Capability matching
- Health/availability
- Performance (latency)
- Cost
- User preferences

Features:
- Multi-factor scoring algorithm
- Circuit breaker pattern for fault tolerance
- Automatic fallback to alternatives
- Request execution with retries
"""

import time
import uuid
import logging
import json
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from .database import Database, Row
from .registry import MCPRegistry, MCP, MCPCategory, MCPStatus, HealthCheckResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if recovered


class RoutingStrategy(Enum):
    """MCP selection strategies"""
    BEST_SCORE = "best_score"       # Use scoring algorithm (default)
    LOWEST_COST = "lowest_cost"     # Cheapest option
    FASTEST = "fastest"             # Lowest latency
    ROUND_ROBIN = "round_robin"     # Distribute evenly
    RANDOM = "random"               # Random selection


@dataclass
class RoutingRequest:
    """Request to be routed to an MCP"""
    capability: str                 # Required capability name
    payload: Dict[str, Any]         # Request data
    category: Optional[MCPCategory] = None  # Filter by category
    preferred_mcp_id: Optional[str] = None  # Prefer specific MCP
    max_latency_ms: Optional[int] = None    # Latency requirement
    max_cost: Optional[float] = None        # Cost budget
    strategy: RoutingStrategy = RoutingStrategy.BEST_SCORE
    timeout_ms: Optional[int] = None        # Request timeout (None = use MCP's configured timeout)


@dataclass
class MCPScore:
    """Scoring result for an MCP"""
    mcp: MCP
    total_score: float
    health_score: float
    performance_score: float
    cost_score: float
    rating_score: float
    circuit_state: CircuitState
    is_eligible: bool
    reason: str = ""


@dataclass
class RoutingResult:
    """Result of routing a request"""
    success: bool
    mcp_id: Optional[str]
    mcp_name: Optional[str]
    response: Optional[Dict[str, Any]]
    error: Optional[str]
    response_time_ms: int
    cost: float
    attempts: int
    fallback_used: bool


@dataclass
class ScoringProfile:
    """
    Category-specific scoring thresholds.

    Different service categories have different performance expectations:
    - Rideshare: Sub-second responses expected
    - Travel: Multi-second responses acceptable (complex API aggregation)
    - Async: Minutes to hours acceptable (batch processing, HVAC scheduling)

    This allows fair scoring across different service types.
    """
    name: str

    # Latency thresholds (ms) -> score
    latency_excellent: int = 100      # Score 100 if below this
    latency_good: int = 200           # Score 90 if below this
    latency_acceptable: int = 500     # Score 70 if below this
    latency_slow: int = 1000          # Score 50 if below this
    # Else score 30

    # Cost thresholds ($) -> score
    cost_excellent: float = 0.005     # Score 100 if below this
    cost_good: float = 0.01           # Score 90 if below this
    cost_acceptable: float = 0.02     # Score 80 if below this
    cost_moderate: float = 0.05       # Score 60 if below this
    # Else score 40

    # Scoring weights (must sum to 1.0)
    weight_health: float = 0.30
    weight_performance: float = 0.25
    weight_cost: float = 0.20
    weight_rating: float = 0.25


# Default scoring profiles for different service categories
SCORING_PROFILES: Dict[str, ScoringProfile] = {
    # Rideshare: Fast responses, low per-request cost expected
    "rideshare": ScoringProfile(
        name="rideshare",
        latency_excellent=100,
        latency_good=200,
        latency_acceptable=500,
        latency_slow=1000,
        cost_excellent=0.005,
        cost_good=0.01,
        cost_acceptable=0.02,
        cost_moderate=0.05,
    ),

    # Travel: Slower responses acceptable (flight/hotel APIs are complex)
    "travel": ScoringProfile(
        name="travel",
        latency_excellent=1000,       # 1s is excellent for flights
        latency_good=3000,            # 3s is good
        latency_acceptable=5000,      # 5s is acceptable
        latency_slow=10000,           # 10s is slow
        cost_excellent=0.05,          # Travel APIs cost more
        cost_good=0.10,
        cost_acceptable=0.20,
        cost_moderate=0.50,
    ),

    # Food delivery: Medium latency, medium cost
    "food_delivery": ScoringProfile(
        name="food_delivery",
        latency_excellent=200,
        latency_good=500,
        latency_acceptable=1000,
        latency_slow=2000,
        cost_excellent=0.01,
        cost_good=0.02,
        cost_acceptable=0.03,
        cost_moderate=0.05,
    ),

    # Async services: Very long latency acceptable (HVAC, batch processing)
    "async": ScoringProfile(
        name="async",
        latency_excellent=60000,      # 1 minute is "excellent"
        latency_good=300000,          # 5 minutes is "good"
        latency_acceptable=3600000,   # 1 hour is acceptable
        latency_slow=86400000,        # 1 day is slow
        cost_excellent=0.10,          # Async can cost more
        cost_good=0.25,
        cost_acceptable=0.50,
        cost_moderate=1.00,
        weight_performance=0.05,      # Latency matters less for async
        weight_health=0.40,           # Reliability matters more
        weight_cost=0.30,             # Cost matters more
        weight_rating=0.25,
    ),

    # E-commerce: Fast responses expected, variable cost
    "e_commerce": ScoringProfile(
        name="e_commerce",
        latency_excellent=150,
        latency_good=300,
        latency_acceptable=600,
        latency_slow=1200,
        cost_excellent=0.01,
        cost_good=0.02,
        cost_acceptable=0.05,
        cost_moderate=0.10,
    ),

    # Default: Original hardcoded values
    "default": ScoringProfile(name="default"),
}

# Map MCPCategory enum values to profile names
# See registry.py MCPCategory for available categories:
# RIDESHARE, FLIGHTS, HOTELS, RESTAURANTS, FOOD_DELIVERY,
# EVENTS, SHOPPING, FINANCE, HEALTHCARE, UTILITIES, OTHER
CATEGORY_TO_PROFILE: Dict[str, str] = {
    "rideshare": "rideshare",
    "food_delivery": "food_delivery",
    "flights": "travel",              # Flight APIs are slow, use travel profile
    "hotels": "travel",               # Hotel APIs similar to flights
    "restaurants": "food_delivery",   # Similar latency to food delivery
    "events": "travel",               # Event APIs can be slow
    "shopping": "e_commerce",
    "finance": "default",             # Finance needs fast, accurate responses
    "healthcare": "async",            # Healthcare scheduling can be async
    "utilities": "async",             # HVAC, electric scheduling is async
    "other": "default",
}


def get_scoring_profile(category: Optional['MCPCategory']) -> ScoringProfile:
    """
    Get the appropriate scoring profile for an MCP category.

    Args:
        category: MCP category enum value

    Returns:
        ScoringProfile for that category
    """
    if category is None:
        return SCORING_PROFILES["default"]

    category_name = category.value if hasattr(category, 'value') else str(category)
    profile_name = CATEGORY_TO_PROFILE.get(category_name, "default")
    return SCORING_PROFILES.get(profile_name, SCORING_PROFILES["default"])


class CircuitBreaker:
    """
    Circuit breaker for an MCP.

    States:
    - CLOSED: Normal, requests pass through
    - OPEN: Failing, requests rejected immediately
    - HALF_OPEN: Testing, one request allowed through

    Transitions:
    - CLOSED -> OPEN: After `failure_threshold` consecutive failures
    - OPEN -> HALF_OPEN: After `recovery_timeout` seconds
    - HALF_OPEN -> CLOSED: On success
    - HALF_OPEN -> OPEN: On failure
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,  # seconds
        half_open_max_calls: int = 1
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

    def get_state(self, db: Database, mcp_id: str) -> CircuitState:
        """Get current circuit state for an MCP"""
        row = db.fetch_one(
            "SELECT * FROM circuit_breaker_state WHERE mcp_id = ?",
            (mcp_id,)
        )

        if not row:
            return CircuitState.CLOSED

        state = CircuitState(row['state'])

        # Check if OPEN should transition to HALF_OPEN
        if state == CircuitState.OPEN and row['opened_at']:
            opened_at = row['opened_at']
            if isinstance(opened_at, str):
                opened_at = datetime.fromisoformat(opened_at)

            if datetime.now() - opened_at > timedelta(seconds=self.recovery_timeout):
                # Transition to half-open
                db.execute(
                    """
                    UPDATE circuit_breaker_state
                    SET state = 'half_open', half_opened_at = CURRENT_TIMESTAMP
                    WHERE mcp_id = ?
                    """,
                    (mcp_id,)
                )
                return CircuitState.HALF_OPEN

        return state

    def is_allowed(self, db: Database, mcp_id: str) -> bool:
        """Check if request is allowed through the circuit"""
        state = self.get_state(db, mcp_id)
        return state != CircuitState.OPEN

    def record_success(self, db: Database, mcp_id: str):
        """Record successful request"""
        state = self.get_state(db, mcp_id)

        if state == CircuitState.HALF_OPEN:
            # Success in half-open -> close circuit
            db.execute(
                """
                UPDATE circuit_breaker_state
                SET state = 'closed',
                    failure_count = 0,
                    success_count = success_count + 1,
                    last_success_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE mcp_id = ?
                """,
                (mcp_id,)
            )
            logger.info(f"Circuit breaker CLOSED for MCP {mcp_id}")
        else:
            db.execute(
                """
                UPDATE circuit_breaker_state
                SET failure_count = 0,
                    success_count = success_count + 1,
                    last_success_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE mcp_id = ?
                """,
                (mcp_id,)
            )

    def record_failure(self, db: Database, mcp_id: str, error: str = ""):
        """Record failed request"""
        state = self.get_state(db, mcp_id)
        row = db.fetch_one(
            "SELECT failure_count FROM circuit_breaker_state WHERE mcp_id = ?",
            (mcp_id,)
        )

        failure_count = (row['failure_count'] if row else 0) + 1

        if state == CircuitState.HALF_OPEN:
            # Failure in half-open -> open circuit
            db.execute(
                """
                UPDATE circuit_breaker_state
                SET state = 'open',
                    failure_count = ?,
                    last_failure_at = CURRENT_TIMESTAMP,
                    opened_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE mcp_id = ?
                """,
                (failure_count, mcp_id)
            )
            logger.warning(f"Circuit breaker OPENED (from half-open) for MCP {mcp_id}: {error}")

        elif failure_count >= self.failure_threshold:
            # Threshold reached -> open circuit
            db.execute(
                """
                UPDATE circuit_breaker_state
                SET state = 'open',
                    failure_count = ?,
                    last_failure_at = CURRENT_TIMESTAMP,
                    opened_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE mcp_id = ?
                """,
                (failure_count, mcp_id)
            )
            logger.warning(f"Circuit breaker OPENED for MCP {mcp_id}: {error}")

        else:
            db.execute(
                """
                UPDATE circuit_breaker_state
                SET failure_count = ?,
                    last_failure_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE mcp_id = ?
                """,
                (failure_count, mcp_id)
            )


class MCPRouter:
    """
    Intelligent routing engine for MCP requests.

    Usage:
        router = MCPRouter(db)

        # Route a request
        result = router.route_request(RoutingRequest(
            capability='compare_prices',
            payload={'pickup': {...}, 'dropoff': {...}},
            category=MCPCategory.RIDESHARE
        ))

        if result.success:
            print(f"Response: {result.response}")
        else:
            print(f"Error: {result.error}")
    """

    def __init__(
        self,
        db: Database,
        executor: Callable[[MCP, Dict[str, Any]], Dict[str, Any]] = None
    ):
        """
        Initialize router.

        Args:
            db: Database connection
            executor: Function to execute MCP requests.
                      Signature: (mcp, payload) -> response_dict
                      If None, uses mock executor for testing.
        """
        self.db = db
        self.registry = MCPRegistry(db)
        self.circuit_breaker = CircuitBreaker()
        self.executor = executor or self._mock_executor
        self._thread_pool = ThreadPoolExecutor(max_workers=10)

    def _mock_executor(self, mcp: MCP, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mock executor for testing (simulates MCP response)"""
        import random
        time.sleep(random.uniform(0.05, 0.2))  # Simulate latency

        # 5% chance of failure for testing
        if random.random() < 0.05:
            raise Exception("Simulated MCP failure")

        return {
            'success': True,
            'mcp_id': mcp.id,
            'mcp_name': mcp.name,
            'data': f"Mock response from {mcp.name}",
            'payload_received': payload
        }

    def route_request(self, request: RoutingRequest) -> RoutingResult:
        """
        Route a request to the best available MCP.

        Args:
            request: Routing request with capability and payload

        Returns:
            RoutingResult with response or error
        """
        start_time = time.time()
        attempts = 0
        fallback_used = False

        # Find eligible MCPs
        candidates = self._find_candidates(request)

        if not candidates:
            return RoutingResult(
                success=False,
                mcp_id=None,
                mcp_name=None,
                response=None,
                error=f"No MCPs found for capability '{request.capability}'",
                response_time_ms=int((time.time() - start_time) * 1000),
                cost=0,
                attempts=0,
                fallback_used=False
            )

        # Score and rank candidates
        scored = self.score_and_select(candidates, request)
        eligible = [s for s in scored if s.is_eligible]

        if not eligible:
            return RoutingResult(
                success=False,
                mcp_id=None,
                mcp_name=None,
                response=None,
                error="All MCPs are unavailable (circuit breakers open)",
                response_time_ms=int((time.time() - start_time) * 1000),
                cost=0,
                attempts=0,
                fallback_used=False
            )

        # Sort by score (highest first)
        eligible.sort(key=lambda s: s.total_score, reverse=True)

        # Try MCPs in order until success
        last_error = None
        for score in eligible:
            attempts += 1
            mcp = score.mcp

            try:
                result = self._execute_mcp(mcp, request.payload, request.timeout_ms)

                # Success!
                response_time_ms = int((time.time() - start_time) * 1000)

                return RoutingResult(
                    success=True,
                    mcp_id=mcp.id,
                    mcp_name=mcp.name,
                    response=result,
                    error=None,
                    response_time_ms=response_time_ms,
                    cost=mcp.fee_per_request,
                    attempts=attempts,
                    fallback_used=fallback_used
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(f"MCP {mcp.name} failed: {e}")

                # Record failure in circuit breaker
                self.circuit_breaker.record_failure(self.db, mcp.id, str(e))

                # Mark for fallback
                fallback_used = True
                continue

        # All MCPs failed
        return RoutingResult(
            success=False,
            mcp_id=None,
            mcp_name=None,
            response=None,
            error=f"All MCPs failed. Last error: {last_error}",
            response_time_ms=int((time.time() - start_time) * 1000),
            cost=0,
            attempts=attempts,
            fallback_used=fallback_used
        )

    def _find_candidates(self, request: RoutingRequest) -> List[MCP]:
        """Find MCPs that can handle the request"""
        # First, try to find by capability
        candidates = self.registry.find_by_capability(request.capability)

        # If category specified, filter
        if request.category:
            candidates = [m for m in candidates if m.category == request.category]

        # If preferred MCP specified, prioritize it
        if request.preferred_mcp_id:
            preferred = [m for m in candidates if m.id == request.preferred_mcp_id]
            others = [m for m in candidates if m.id != request.preferred_mcp_id]
            candidates = preferred + others

        # Apply cost filter
        if request.max_cost is not None:
            candidates = [m for m in candidates if m.fee_per_request <= request.max_cost]

        # Apply latency filter
        if request.max_latency_ms is not None:
            candidates = [
                m for m in candidates
                if m.avg_response_time_ms <= request.max_latency_ms
            ]

        return candidates

    def score_and_select(
        self,
        candidates: List[MCP],
        request: RoutingRequest,
        profile: Optional[ScoringProfile] = None
    ) -> List[MCPScore]:
        """
        Score MCPs using multi-factor algorithm with configurable profiles.

        Scoring weights vary by category profile:
        - Default: Health 30%, Performance 25%, Cost 20%, Rating 25%
        - Async: Health 40%, Performance 5%, Cost 30%, Rating 25%
        - etc.

        Args:
            candidates: List of candidate MCPs
            request: Routing request
            profile: Optional scoring profile (auto-detected from category if None)

        Returns:
            List of MCPScore objects
        """
        scores = []

        # Get scoring profile for this category
        if profile is None:
            profile = get_scoring_profile(request.category)

        for mcp in candidates:
            # Get circuit breaker state
            circuit_state = self.circuit_breaker.get_state(self.db, mcp.id)

            # Calculate component scores (0-100) using profile thresholds
            health_score = self._score_health(mcp, circuit_state)
            performance_score = self._score_performance(mcp, request.max_latency_ms, profile)
            cost_score = self._score_cost(mcp, request.max_cost, profile)
            rating_score = self._score_rating(mcp)

            # Weighted total using profile weights
            total_score = (
                health_score * profile.weight_health +
                performance_score * profile.weight_performance +
                cost_score * profile.weight_cost +
                rating_score * profile.weight_rating
            )

            # Determine eligibility
            is_eligible = (
                circuit_state != CircuitState.OPEN and
                mcp.status == MCPStatus.ACTIVE
            )

            reason = ""
            if not is_eligible:
                if circuit_state == CircuitState.OPEN:
                    reason = "Circuit breaker open"
                elif mcp.status != MCPStatus.ACTIVE:
                    reason = f"MCP status: {mcp.status.value}"

            scores.append(MCPScore(
                mcp=mcp,
                total_score=round(total_score, 2),
                health_score=round(health_score, 2),
                performance_score=round(performance_score, 2),
                cost_score=round(cost_score, 2),
                rating_score=round(rating_score, 2),
                circuit_state=circuit_state,
                is_eligible=is_eligible,
                reason=reason
            ))

        return scores

    def _score_health(self, mcp: MCP, circuit_state: CircuitState) -> float:
        """Score MCP health (0-100)"""
        if circuit_state == CircuitState.OPEN:
            return 0

        if circuit_state == CircuitState.HALF_OPEN:
            return 50

        # Based on uptime and error rate
        uptime_score = mcp.uptime_percent

        error_rate = 0
        if mcp.total_requests > 0:
            error_rate = (mcp.total_errors / mcp.total_requests) * 100

        error_score = max(0, 100 - error_rate * 10)  # -10 points per 1% error rate

        return (uptime_score * 0.6 + error_score * 0.4)

    def _score_performance(
        self,
        mcp: MCP,
        max_latency: Optional[int],
        profile: ScoringProfile = None
    ) -> float:
        """
        Score MCP performance/latency (0-100) using profile thresholds.

        Uses category-specific thresholds:
        - Rideshare: 100ms=excellent, 1000ms=slow
        - Travel: 1000ms=excellent, 10000ms=slow
        - Async: 60000ms=excellent, 86400000ms=slow

        Args:
            mcp: MCP to score
            max_latency: Optional user-specified latency requirement
            profile: Scoring profile with latency thresholds

        Returns:
            Score from 0-100
        """
        if profile is None:
            profile = SCORING_PROFILES["default"]

        avg_latency = mcp.avg_response_time_ms

        if max_latency:
            # Score relative to user-specified requirement
            if avg_latency <= max_latency * 0.5:
                return 100
            elif avg_latency <= max_latency:
                return 70 + 30 * (1 - (avg_latency - max_latency * 0.5) / (max_latency * 0.5))
            else:
                return max(0, 50 * (1 - (avg_latency - max_latency) / max_latency))
        else:
            # Absolute scoring using profile thresholds
            if avg_latency < profile.latency_excellent:
                return 100
            elif avg_latency < profile.latency_good:
                return 90
            elif avg_latency < profile.latency_acceptable:
                return 70
            elif avg_latency < profile.latency_slow:
                return 50
            else:
                return 30

    def _score_cost(
        self,
        mcp: MCP,
        max_cost: Optional[float],
        profile: ScoringProfile = None
    ) -> float:
        """
        Score MCP cost (0-100) using profile thresholds.

        Uses category-specific thresholds:
        - Rideshare: $0.005=excellent, $0.05=moderate
        - Travel: $0.05=excellent, $0.50=moderate
        - Async: $0.10=excellent, $1.00=moderate

        Args:
            mcp: MCP to score
            max_cost: Optional user-specified cost budget
            profile: Scoring profile with cost thresholds

        Returns:
            Score from 0-100
        """
        if profile is None:
            profile = SCORING_PROFILES["default"]

        cost = mcp.fee_per_request

        if max_cost:
            # Score relative to user-specified budget
            if cost <= max_cost * 0.5:
                return 100
            elif cost <= max_cost:
                return 60 + 40 * (1 - (cost - max_cost * 0.5) / (max_cost * 0.5))
            else:
                return 0
        else:
            # Absolute scoring using profile thresholds (lower is better)
            if cost <= profile.cost_excellent:
                return 100
            elif cost <= profile.cost_good:
                return 90
            elif cost <= profile.cost_acceptable:
                return 80
            elif cost <= profile.cost_moderate:
                return 60
            else:
                return 40

    def _score_rating(self, mcp: MCP) -> float:
        """Score MCP rating (0-100)"""
        # Rating is 0-5, convert to 0-100
        return mcp.avg_rating * 20

    def _execute_mcp(
        self,
        mcp: MCP,
        payload: Dict[str, Any],
        timeout_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute request on MCP.

        Args:
            mcp: MCP to execute
            payload: Request payload
            timeout_ms: Timeout in milliseconds (None = use MCP's configured timeout)

        Returns:
            Response dict from MCP

        Raises:
            Exception: On timeout or execution error

        Note:
            Each MCP can have its own timeout configured (mcp.timeout_ms).
            This allows async services (email, HVAC) to have hours-long timeouts
            while real-time services (rideshare) have sub-minute timeouts.
        """
        start_time = time.time()

        # Use MCP's configured timeout if not explicitly specified
        # This allows per-MCP timeout configuration (e.g., 30s for rideshare, hours for async)
        effective_timeout_ms = timeout_ms if timeout_ms is not None else mcp.timeout_ms

        try:
            # Execute with timeout
            future = self._thread_pool.submit(self.executor, mcp, payload)
            result = future.result(timeout=effective_timeout_ms / 1000)

            # Record success
            response_time_ms = int((time.time() - start_time) * 1000)
            self.circuit_breaker.record_success(self.db, mcp.id)
            self.registry.increment_request_count(mcp.id, success=True)
            self.registry.update_response_time(mcp.id, response_time_ms)

            return result

        except FuturesTimeoutError:
            self.circuit_breaker.record_failure(self.db, mcp.id, "Timeout")
            self.registry.increment_request_count(mcp.id, success=False)
            raise Exception(f"Request timed out after {effective_timeout_ms}ms")

        except Exception as e:
            self.circuit_breaker.record_failure(self.db, mcp.id, str(e))
            self.registry.increment_request_count(mcp.id, success=False)
            raise

    def execute_mcp(
        self,
        mcp_id: str,
        payload: Dict[str, Any],
        timeout_ms: Optional[int] = None
    ) -> RoutingResult:
        """
        Execute request on a specific MCP (bypass routing).

        Args:
            mcp_id: MCP ID
            payload: Request payload
            timeout_ms: Timeout in milliseconds (None = use MCP's configured timeout)

        Returns:
            RoutingResult
        """
        start_time = time.time()

        mcp = self.registry.get_mcp(mcp_id)
        if not mcp:
            return RoutingResult(
                success=False,
                mcp_id=mcp_id,
                mcp_name=None,
                response=None,
                error=f"MCP not found: {mcp_id}",
                response_time_ms=0,
                cost=0,
                attempts=0,
                fallback_used=False
            )

        # Check circuit breaker
        if not self.circuit_breaker.is_allowed(self.db, mcp_id):
            return RoutingResult(
                success=False,
                mcp_id=mcp_id,
                mcp_name=mcp.name,
                response=None,
                error="Circuit breaker is open",
                response_time_ms=0,
                cost=0,
                attempts=0,
                fallback_used=False
            )

        try:
            result = self._execute_mcp(mcp, payload, timeout_ms)
            response_time_ms = int((time.time() - start_time) * 1000)

            return RoutingResult(
                success=True,
                mcp_id=mcp.id,
                mcp_name=mcp.name,
                response=result,
                error=None,
                response_time_ms=response_time_ms,
                cost=mcp.fee_per_request,
                attempts=1,
                fallback_used=False
            )

        except Exception as e:
            return RoutingResult(
                success=False,
                mcp_id=mcp.id,
                mcp_name=mcp.name,
                response=None,
                error=str(e),
                response_time_ms=int((time.time() - start_time) * 1000),
                cost=0,
                attempts=1,
                fallback_used=False
            )

    def get_routing_scores(
        self,
        capability: str,
        category: Optional[MCPCategory] = None
    ) -> List[Dict[str, Any]]:
        """
        Get scoring breakdown for all MCPs that can handle a capability.

        Useful for debugging and transparency.

        Args:
            capability: Capability name
            category: Optional category filter

        Returns:
            List of scoring dicts
        """
        request = RoutingRequest(
            capability=capability,
            payload={},
            category=category
        )

        candidates = self._find_candidates(request)
        scores = self.score_and_select(candidates, request)

        return [
            {
                'mcp_id': s.mcp.id,
                'mcp_name': s.mcp.name,
                'total_score': s.total_score,
                'health_score': s.health_score,
                'performance_score': s.performance_score,
                'cost_score': s.cost_score,
                'rating_score': s.rating_score,
                'circuit_state': s.circuit_state.value,
                'is_eligible': s.is_eligible,
                'reason': s.reason
            }
            for s in sorted(scores, key=lambda x: x.total_score, reverse=True)
        ]


# Example usage
if __name__ == "__main__":
    from database import create_test_database
    from registry import MCPCapability

    # Create test database
    db = create_test_database()

    # Set up test data
    dev_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO developers (id, email, display_name, api_key_hash) VALUES (?, ?, ?, ?)",
        (dev_id, 'test@example.com', 'Test Developer', 'hash123')
    )

    # Create registry and add MCPs
    registry = MCPRegistry(db)

    mcp1_id = registry.register_mcp(
        developer_id=dev_id,
        name="Rideshare Compare v1",
        slug="rideshare-v1",
        category=MCPCategory.RIDESHARE,
        endpoint_url="http://localhost:8001/compare",
        fee_per_request=0.02,
        capabilities=[
            MCPCapability(name='compare_prices', description='Compare rideshare prices')
        ]
    )
    registry.activate_mcp(mcp1_id)
    registry.update_rating(mcp1_id, 4.5)

    mcp2_id = registry.register_mcp(
        developer_id=dev_id,
        name="Rideshare Compare v2",
        slug="rideshare-v2",
        category=MCPCategory.RIDESHARE,
        endpoint_url="http://localhost:8002/compare",
        fee_per_request=0.01,
        capabilities=[
            MCPCapability(name='compare_prices', description='Compare rideshare prices')
        ]
    )
    registry.activate_mcp(mcp2_id)
    registry.update_rating(mcp2_id, 4.8)

    # Create router
    router = MCPRouter(db)

    # Route a request
    print("=== Routing Request ===")
    result = router.route_request(RoutingRequest(
        capability='compare_prices',
        payload={'pickup': {'lat': 37.7879, 'lon': -122.4074}},
        category=MCPCategory.RIDESHARE
    ))

    print(f"Success: {result.success}")
    print(f"MCP: {result.mcp_name}")
    print(f"Response time: {result.response_time_ms}ms")
    print(f"Cost: ${result.cost}")
    print(f"Attempts: {result.attempts}")

    # Get scoring breakdown
    print("\n=== Scoring Breakdown ===")
    scores = router.get_routing_scores('compare_prices', MCPCategory.RIDESHARE)
    for score in scores:
        print(f"{score['mcp_name']}: total={score['total_score']}, "
              f"health={score['health_score']}, perf={score['performance_score']}, "
              f"cost={score['cost_score']}, rating={score['rating_score']}")

    db.close()
