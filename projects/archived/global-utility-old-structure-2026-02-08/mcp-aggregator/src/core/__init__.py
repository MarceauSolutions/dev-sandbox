"""
MCP Aggregator Platform Core

This module provides the core infrastructure for the MCP Aggregator platform:
- Registry: MCP registration and discovery
- Router: Intelligent request routing with multi-factor scoring
- Billing: Transaction logging and fee calculation (multiple pricing models)
- Database: SQLite/PostgreSQL abstraction layer

Connectivity Types:
- HTTP: Standard REST API (default)
- EMAIL: SMTP-based services
- OAUTH: OAuth2 with token refresh
- WEBHOOK: Inbound webhooks
- GRAPHQL: GraphQL queries
- ASYNC: Long-running operations (hours/days)

Pricing Models:
- PER_REQUEST: Traditional pay-per-call (default)
- SUBSCRIPTION: Monthly fee, unlimited calls
- COMMISSION: Percentage of transaction value
- TIERED: Volume-based pricing with discount tiers
- HYBRID: Base subscription + per-request charges

Scoring Profiles:
- rideshare: Fast responses (100ms excellent)
- travel: Slower acceptable (1-10s for flights/hotels)
- food_delivery: Medium latency
- async: Very slow acceptable (minutes to days)
- e_commerce: Fast responses
- default: Original thresholds

Usage:
    from src.core import Database, Registry, Router, BillingSystem
    from src.core import MCPCategory, ConnectivityType, PricingModel

    # Initialize
    db = Database(':memory:')  # or 'path/to/database.db'
    registry = Registry(db)
    router = Router(db, registry)
    billing = BillingSystem(db)

    # Register an MCP
    mcp_id = registry.register_mcp(
        developer_id='dev-123',
        name='My Service',
        slug='my-service',
        category=MCPCategory.UTILITIES,
        connectivity_type=ConnectivityType.EMAIL,
        email_address='service@example.com'
    )

    # Route a request
    result = router.route_request(RoutingRequest(
        capability='query',
        payload={'query': 'test'},
        category=MCPCategory.UTILITIES
    ))

    # Log billing
    txn_id = billing.log_transaction_with_pricing(
        pricing_model=PricingModel.COMMISSION,
        booking_value=Decimal('100.00'),
        commission_rate=Decimal('0.10'),
        ...
    )
"""

# Database
from .database import Database, DatabaseConfig, create_test_database

# Registry
from .registry import (
    MCPRegistry as Registry,
    MCP,
    MCPCategory,
    MCPStatus,
    ConnectivityType,
    MCPCapability,
    HealthCheckResult
)

# Router
from .router import (
    MCPRouter as Router,
    RoutingRequest,
    RoutingResult,
    RoutingStrategy,
    MCPScore,
    ScoringProfile,
    SCORING_PROFILES,
    CATEGORY_TO_PROFILE,
    get_scoring_profile,
    CircuitBreaker,
    CircuitState
)

# Billing
from .billing import (
    BillingSystem,
    Transaction,
    TransactionStatus,
    PricingModel,
    TierConfig,
    FeeBreakdown,
    Payout,
    PayoutStatus,
    Invoice,
    InvoiceStatus
)

__all__ = [
    # Database
    'Database',

    # Registry
    'Registry',
    'MCP',
    'MCPCategory',
    'MCPStatus',
    'ConnectivityType',
    'MCPCapability',

    # Router
    'Router',
    'RoutingRequest',
    'RoutingResult',
    'RoutingStrategy',
    'MCPScore',
    'ScoringProfile',
    'SCORING_PROFILES',
    'CATEGORY_TO_PROFILE',
    'get_scoring_profile',
    'CircuitBreaker',
    'CircuitState',

    # Billing
    'BillingSystem',
    'Transaction',
    'TransactionStatus',
    'PricingModel',
    'TierConfig',
    'FeeBreakdown',
    'Payout',
    'PayoutStatus',
    'Invoice',
    'InvoiceStatus',
]

__version__ = '1.1.0-dev'
