"""
Test Suite for MCP Aggregator Platform

Uses SQLite for testing - no external database required.

Run with: pytest test_platform.py -v

Tests cover:
- Database connection layer
- MCP Registry (registration, discovery, health)
- Routing Engine (scoring, execution, circuit breaker)
- Billing System (transactions, invoices, payouts)
"""

import pytest
import uuid
import json
import time
from datetime import date, datetime, timedelta
from decimal import Decimal

# Import platform modules
from database import Database, DatabaseConfig, SQLiteSchema, create_test_database, Row
from registry import MCPRegistry, MCP, MCPCategory, MCPStatus, MCPCapability, HealthCheckResult
from router import MCPRouter, RoutingRequest, RoutingStrategy, CircuitBreaker, CircuitState
from billing import BillingSystem, TransactionStatus, PayoutStatus, InvoiceStatus


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def db():
    """Create fresh test database for each test"""
    database = create_test_database()
    yield database
    database.close()


@pytest.fixture
def developer(db):
    """Create test developer"""
    dev_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO developers (id, email, display_name, api_key_hash, is_verified, is_active)
        VALUES (?, ?, ?, ?, 1, 1)
        """,
        (dev_id, 'test@example.com', 'Test Developer', 'hash123')
    )
    return dev_id


@pytest.fixture
def ai_platform(db):
    """Create test AI platform"""
    platform_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO ai_platforms (id, name, api_key_hash, is_active)
        VALUES (?, ?, ?, 1)
        """,
        (platform_id, 'Test Platform', 'hash456')
    )
    return platform_id


@pytest.fixture
def registry(db):
    """Create MCP Registry"""
    return MCPRegistry(db)


@pytest.fixture
def router(db):
    """Create MCP Router"""
    return MCPRouter(db)


@pytest.fixture
def billing(db):
    """Create Billing System"""
    return BillingSystem(db)


# ============================================
# DATABASE TESTS
# ============================================

class TestDatabase:
    """Tests for database connection layer"""

    def test_create_sqlite_config(self):
        """Test SQLite config creation"""
        config = DatabaseConfig.sqlite(':memory:')
        assert config.db_type.value == 'sqlite'
        assert config.sqlite_path == ':memory:'

    def test_create_postgresql_config(self):
        """Test PostgreSQL config creation"""
        config = DatabaseConfig.postgresql(
            host='localhost',
            port=5432,
            database='test_db',
            user='postgres'
        )
        assert config.db_type.value == 'postgresql'
        assert config.host == 'localhost'
        assert config.database == 'test_db'

    def test_parse_postgres_url(self):
        """Test PostgreSQL URL parsing"""
        config = DatabaseConfig._parse_postgres_url(
            'postgresql://user:pass@localhost:5432/mydb'
        )
        assert config.host == 'localhost'
        assert config.port == 5432
        assert config.database == 'mydb'
        assert config.user == 'user'
        assert config.password == 'pass'

    def test_connection(self, db):
        """Test database connection"""
        assert db is not None
        health = db.health_check()
        assert health['status'] == 'healthy'

    def test_execute_and_fetch(self, db):
        """Test basic CRUD operations"""
        dev_id = str(uuid.uuid4())

        # Insert
        db.execute(
            "INSERT INTO developers (id, email, display_name, api_key_hash) VALUES (?, ?, ?, ?)",
            (dev_id, 'test@test.com', 'Test', 'hash')
        )

        # Fetch one
        row = db.fetch_one("SELECT * FROM developers WHERE id = ?", (dev_id,))
        assert row is not None
        assert row['email'] == 'test@test.com'
        assert row.email == 'test@test.com'  # Attribute access

        # Fetch all
        rows = db.fetch_all("SELECT * FROM developers")
        assert len(rows) == 1

        # Update
        db.execute(
            "UPDATE developers SET display_name = ? WHERE id = ?",
            ('Updated', dev_id)
        )
        row = db.fetch_one("SELECT * FROM developers WHERE id = ?", (dev_id,))
        assert row['display_name'] == 'Updated'

        # Delete
        db.execute("DELETE FROM developers WHERE id = ?", (dev_id,))
        rows = db.fetch_all("SELECT * FROM developers")
        assert len(rows) == 0

    def test_transaction_rollback(self, db):
        """Test transaction rollback on error"""
        dev_id = str(uuid.uuid4())

        try:
            with db.transaction():
                db.execute(
                    "INSERT INTO developers (id, email, display_name, api_key_hash) VALUES (?, ?, ?, ?)",
                    (dev_id, 'test@test.com', 'Test', 'hash')
                )
                # Force an error
                raise Exception("Simulated error")
        except Exception:
            pass

        # Should be rolled back
        row = db.fetch_one("SELECT * FROM developers WHERE id = ?", (dev_id,))
        assert row is None

    def test_table_exists(self, db):
        """Test table existence check"""
        assert db.table_exists('developers') is True
        assert db.table_exists('nonexistent_table') is False

    def test_get_table_columns(self, db):
        """Test getting table columns"""
        columns = db.get_table_columns('developers')
        assert 'id' in columns
        assert 'email' in columns
        assert 'display_name' in columns


# ============================================
# REGISTRY TESTS
# ============================================

class TestMCPRegistry:
    """Tests for MCP Registry"""

    def test_register_mcp(self, registry, developer):
        """Test MCP registration"""
        mcp_id = registry.register_mcp(
            developer_id=developer,
            name='Weather MCP',
            slug='weather-mcp',
            category=MCPCategory.UTILITIES,
            endpoint_url='http://localhost:8000/weather',
            description='Get weather information',
            fee_per_request=0.01,
            tags=['weather', 'forecast']
        )

        assert mcp_id is not None
        mcp = registry.get_mcp(mcp_id)
        assert mcp.name == 'Weather MCP'
        assert mcp.slug == 'weather-mcp'
        assert mcp.category == MCPCategory.UTILITIES
        assert mcp.status == MCPStatus.PENDING_REVIEW

    def test_register_mcp_with_capabilities(self, registry, developer):
        """Test MCP registration with capabilities"""
        mcp_id = registry.register_mcp(
            developer_id=developer,
            name='Weather MCP',
            slug='weather-caps',
            category=MCPCategory.UTILITIES,
            endpoint_url='http://localhost:8000/weather',
            capabilities=[
                MCPCapability(
                    name='current_weather',
                    description='Get current weather',
                    input_schema={'type': 'object', 'properties': {'location': {'type': 'string'}}},
                    output_schema={'type': 'object'}
                ),
                MCPCapability(
                    name='forecast',
                    description='Get 7-day forecast',
                    input_schema={'type': 'object'},
                    output_schema={'type': 'object'}
                )
            ]
        )

        mcp = registry.get_mcp(mcp_id)
        assert len(mcp.capabilities) == 2
        assert mcp.capabilities[0].name == 'current_weather'

    def test_duplicate_slug_rejected(self, registry, developer):
        """Test that duplicate slugs are rejected"""
        registry.register_mcp(
            developer_id=developer,
            name='MCP 1',
            slug='unique-slug',
            category=MCPCategory.UTILITIES,
            endpoint_url='http://localhost:8001'
        )

        with pytest.raises(ValueError, match="Slug 'unique-slug' already exists"):
            registry.register_mcp(
                developer_id=developer,
                name='MCP 2',
                slug='unique-slug',
                category=MCPCategory.UTILITIES,
                endpoint_url='http://localhost:8002'
            )

    def test_activate_mcp(self, registry, developer):
        """Test MCP activation"""
        mcp_id = registry.register_mcp(
            developer_id=developer,
            name='Test MCP',
            slug='test-activate',
            category=MCPCategory.UTILITIES,
            endpoint_url='http://localhost:8000'
        )

        assert registry.get_mcp(mcp_id).status == MCPStatus.PENDING_REVIEW

        registry.activate_mcp(mcp_id)
        assert registry.get_mcp(mcp_id).status == MCPStatus.ACTIVE

    def test_find_mcps_by_category(self, registry, developer):
        """Test finding MCPs by category"""
        # Register MCPs in different categories
        registry.register_mcp(
            developer_id=developer,
            name='Rideshare 1',
            slug='rideshare-1',
            category=MCPCategory.RIDESHARE,
            endpoint_url='http://localhost:8001'
        )
        registry.register_mcp(
            developer_id=developer,
            name='Utility 1',
            slug='utility-1',
            category=MCPCategory.UTILITIES,
            endpoint_url='http://localhost:8002'
        )

        # Activate both
        for mcp in registry.find_mcps(status=MCPStatus.PENDING_REVIEW):
            registry.activate_mcp(mcp.id)

        # Find by category
        rideshare_mcps = registry.find_mcps(category=MCPCategory.RIDESHARE)
        utility_mcps = registry.find_mcps(category=MCPCategory.UTILITIES)

        assert len(rideshare_mcps) == 1
        assert rideshare_mcps[0].name == 'Rideshare 1'
        assert len(utility_mcps) == 1
        assert utility_mcps[0].name == 'Utility 1'

    def test_find_by_capability(self, registry, developer):
        """Test finding MCPs by capability"""
        mcp_id = registry.register_mcp(
            developer_id=developer,
            name='Price Compare',
            slug='price-compare',
            category=MCPCategory.RIDESHARE,
            endpoint_url='http://localhost:8000',
            capabilities=[
                MCPCapability(name='compare_prices', description='Compare prices')
            ]
        )
        registry.activate_mcp(mcp_id)

        mcps = registry.find_by_capability('compare_prices')
        assert len(mcps) == 1
        assert mcps[0].id == mcp_id

    def test_update_rating(self, registry, developer):
        """Test rating update"""
        mcp_id = registry.register_mcp(
            developer_id=developer,
            name='Test MCP',
            slug='test-rating',
            category=MCPCategory.UTILITIES,
            endpoint_url='http://localhost:8000'
        )

        registry.update_rating(mcp_id, 4.5)
        mcp = registry.get_mcp(mcp_id)
        assert mcp.avg_rating == 4.5

    def test_health_status(self, registry, developer, db):
        """Test health status tracking"""
        mcp_id = registry.register_mcp(
            developer_id=developer,
            name='Test MCP',
            slug='test-health',
            category=MCPCategory.UTILITIES,
            endpoint_url='http://localhost:8000'
        )
        registry.activate_mcp(mcp_id)

        # Record health check
        registry.record_health_check(HealthCheckResult(
            mcp_id=mcp_id,
            is_healthy=True,
            response_time_ms=150
        ))

        status = registry.get_health_status(mcp_id)
        assert status is not None
        assert status['is_healthy'] is True
        assert status['circuit_breaker_state'] == 'closed'


# ============================================
# ROUTER TESTS
# ============================================

class TestMCPRouter:
    """Tests for MCP Routing Engine"""

    def test_route_request_success(self, db, developer):
        """Test successful request routing"""
        registry = MCPRegistry(db)

        # Create and activate MCP
        mcp_id = registry.register_mcp(
            developer_id=developer,
            name='Test Router MCP',
            slug='test-router',
            category=MCPCategory.RIDESHARE,
            endpoint_url='http://localhost:8000',
            capabilities=[
                MCPCapability(name='compare_prices', description='Compare')
            ]
        )
        registry.activate_mcp(mcp_id)
        registry.update_rating(mcp_id, 4.5)

        # Create router
        router = MCPRouter(db)

        # Route request
        result = router.route_request(RoutingRequest(
            capability='compare_prices',
            payload={'test': 'data'},
            category=MCPCategory.RIDESHARE
        ))

        assert result.success is True
        assert result.mcp_id == mcp_id
        assert result.attempts == 1

    def test_route_request_no_candidates(self, db, developer):
        """Test routing when no MCPs available"""
        router = MCPRouter(db)

        result = router.route_request(RoutingRequest(
            capability='nonexistent_capability',
            payload={}
        ))

        assert result.success is False
        assert 'No MCPs found' in result.error

    def test_scoring_algorithm(self, db, developer):
        """Test MCP scoring"""
        registry = MCPRegistry(db)

        # Create two MCPs with different characteristics
        mcp1_id = registry.register_mcp(
            developer_id=developer,
            name='Expensive but Fast',
            slug='expensive-fast',
            category=MCPCategory.RIDESHARE,
            endpoint_url='http://localhost:8001',
            fee_per_request=0.05,
            capabilities=[MCPCapability(name='compare', description='')]
        )
        registry.activate_mcp(mcp1_id)
        registry.update_rating(mcp1_id, 4.8)

        mcp2_id = registry.register_mcp(
            developer_id=developer,
            name='Cheap but Slower',
            slug='cheap-slow',
            category=MCPCategory.RIDESHARE,
            endpoint_url='http://localhost:8002',
            fee_per_request=0.01,
            capabilities=[MCPCapability(name='compare', description='')]
        )
        registry.activate_mcp(mcp2_id)
        registry.update_rating(mcp2_id, 4.2)

        # Get scores
        router = MCPRouter(db)
        scores = router.get_routing_scores('compare', MCPCategory.RIDESHARE)

        assert len(scores) == 2
        # Both should be eligible
        assert all(s['is_eligible'] for s in scores)

    def test_circuit_breaker(self, db, developer):
        """Test circuit breaker opens after failures"""
        registry = MCPRegistry(db)
        cb = CircuitBreaker(failure_threshold=3)

        mcp_id = registry.register_mcp(
            developer_id=developer,
            name='Flaky MCP',
            slug='flaky-mcp',
            category=MCPCategory.UTILITIES,
            endpoint_url='http://localhost:8000'
        )
        registry.activate_mcp(mcp_id)

        # Initially closed
        assert cb.get_state(db, mcp_id) == CircuitState.CLOSED

        # Record failures
        for _ in range(3):
            cb.record_failure(db, mcp_id, "Test failure")

        # Should be open
        assert cb.get_state(db, mcp_id) == CircuitState.OPEN
        assert cb.is_allowed(db, mcp_id) is False

    def test_circuit_breaker_recovery(self, db, developer):
        """Test circuit breaker recovery after success"""
        registry = MCPRegistry(db)
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0)

        mcp_id = registry.register_mcp(
            developer_id=developer,
            name='Recovery MCP',
            slug='recovery-mcp',
            category=MCPCategory.UTILITIES,
            endpoint_url='http://localhost:8000'
        )
        registry.activate_mcp(mcp_id)

        # Open circuit
        for _ in range(3):
            cb.record_failure(db, mcp_id, "Test failure")

        assert cb.get_state(db, mcp_id) == CircuitState.OPEN

        # With recovery_timeout=0, should immediately go to half-open
        time.sleep(0.1)
        state = cb.get_state(db, mcp_id)
        assert state == CircuitState.HALF_OPEN

        # Record success
        cb.record_success(db, mcp_id)
        assert cb.get_state(db, mcp_id) == CircuitState.CLOSED

    def test_fallback_to_alternative(self, db, developer):
        """Test fallback when primary MCP fails"""
        registry = MCPRegistry(db)

        # Create two MCPs
        mcp1_id = registry.register_mcp(
            developer_id=developer,
            name='Primary MCP',
            slug='primary-mcp',
            category=MCPCategory.RIDESHARE,
            endpoint_url='http://localhost:8001',
            capabilities=[MCPCapability(name='compare', description='')]
        )
        registry.activate_mcp(mcp1_id)
        registry.update_rating(mcp1_id, 5.0)

        mcp2_id = registry.register_mcp(
            developer_id=developer,
            name='Backup MCP',
            slug='backup-mcp',
            category=MCPCategory.RIDESHARE,
            endpoint_url='http://localhost:8002',
            capabilities=[MCPCapability(name='compare', description='')]
        )
        registry.activate_mcp(mcp2_id)
        registry.update_rating(mcp2_id, 4.0)

        # Create router with failing executor for first MCP
        call_count = [0]

        def failing_executor(mcp, payload):
            call_count[0] += 1
            if mcp.id == mcp1_id:
                raise Exception("Primary failed")
            return {'success': True, 'from': mcp.name}

        router = MCPRouter(db, executor=failing_executor)

        result = router.route_request(RoutingRequest(
            capability='compare',
            payload={},
            category=MCPCategory.RIDESHARE
        ))

        # Should succeed with fallback
        assert result.success is True
        assert result.mcp_id == mcp2_id
        assert result.fallback_used is True
        assert result.attempts == 2


# ============================================
# BILLING TESTS
# ============================================

class TestBillingSystem:
    """Tests for Billing System"""

    def test_fee_calculation(self, billing):
        """Test fee breakdown calculation"""
        fees = billing.calculate_fees(Decimal('0.10'))

        assert fees.gross_amount == Decimal('0.10')
        assert fees.developer_payout == Decimal('0.0800')  # 80%
        assert fees.platform_fee == Decimal('0.0200')  # 20%

    def test_fee_calculation_custom_share(self, billing):
        """Test fee calculation with custom developer share"""
        fees = billing.calculate_fees(Decimal('1.00'), developer_share=Decimal('0.70'))

        assert fees.developer_payout == Decimal('0.7000')
        assert fees.platform_fee == Decimal('0.3000')

    def test_log_transaction(self, db, billing, developer, ai_platform):
        """Test transaction logging"""
        mcp_id = str(uuid.uuid4())
        db.execute(
            """
            INSERT INTO mcps (id, developer_id, name, slug, category, endpoint_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (mcp_id, developer, 'Test MCP', 'test-mcp', 'utilities', 'http://localhost')
        )

        txn_id = billing.log_transaction(
            ai_platform_id=ai_platform,
            mcp_id=mcp_id,
            developer_id=developer,
            request_id='req_001',
            capability_name='test_capability',
            request_payload={'test': 'data'},
            gross_amount=Decimal('0.02')
        )

        assert txn_id is not None
        txn = billing.get_transaction(txn_id)
        assert txn.status == TransactionStatus.PENDING
        assert txn.gross_amount == Decimal('0.02')

    def test_duplicate_request_rejected(self, db, billing, developer, ai_platform):
        """Test that duplicate request IDs are rejected"""
        mcp_id = str(uuid.uuid4())
        db.execute(
            """
            INSERT INTO mcps (id, developer_id, name, slug, category, endpoint_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (mcp_id, developer, 'Test MCP', 'test-dup', 'utilities', 'http://localhost')
        )

        billing.log_transaction(
            ai_platform_id=ai_platform,
            mcp_id=mcp_id,
            developer_id=developer,
            request_id='req_duplicate',
            capability_name='test',
            request_payload={},
            gross_amount=Decimal('0.01')
        )

        with pytest.raises(ValueError, match="Duplicate request_id"):
            billing.log_transaction(
                ai_platform_id=ai_platform,
                mcp_id=mcp_id,
                developer_id=developer,
                request_id='req_duplicate',
                capability_name='test',
                request_payload={},
                gross_amount=Decimal('0.01')
            )

    def test_complete_transaction(self, db, billing, developer, ai_platform):
        """Test transaction completion"""
        mcp_id = str(uuid.uuid4())
        db.execute(
            """
            INSERT INTO mcps (id, developer_id, name, slug, category, endpoint_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (mcp_id, developer, 'Test MCP', 'test-complete', 'utilities', 'http://localhost')
        )

        txn_id = billing.log_transaction(
            ai_platform_id=ai_platform,
            mcp_id=mcp_id,
            developer_id=developer,
            request_id='req_complete',
            capability_name='test',
            request_payload={},
            gross_amount=Decimal('0.02')
        )

        result = billing.complete_transaction(
            txn_id,
            response={'result': 'success'},
            response_time_ms=100
        )

        assert result is True
        txn = billing.get_transaction(txn_id)
        assert txn.status == TransactionStatus.COMPLETED
        assert txn.response_time_ms == 100

    def test_fail_transaction(self, db, billing, developer, ai_platform):
        """Test transaction failure"""
        mcp_id = str(uuid.uuid4())
        db.execute(
            """
            INSERT INTO mcps (id, developer_id, name, slug, category, endpoint_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (mcp_id, developer, 'Test MCP', 'test-fail', 'utilities', 'http://localhost')
        )

        txn_id = billing.log_transaction(
            ai_platform_id=ai_platform,
            mcp_id=mcp_id,
            developer_id=developer,
            request_id='req_fail',
            capability_name='test',
            request_payload={},
            gross_amount=Decimal('0.02')
        )

        result = billing.fail_transaction(txn_id, "Test error message")

        assert result is True
        txn = billing.get_transaction(txn_id)
        assert txn.status == TransactionStatus.FAILED
        assert 'Test error message' in txn.error_message

    def test_generate_invoice(self, db, billing, developer, ai_platform):
        """Test invoice generation"""
        mcp_id = str(uuid.uuid4())
        db.execute(
            """
            INSERT INTO mcps (id, developer_id, name, slug, category, endpoint_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (mcp_id, developer, 'Test MCP', 'test-invoice', 'utilities', 'http://localhost')
        )

        # Log and complete a transaction
        txn_id = billing.log_transaction(
            ai_platform_id=ai_platform,
            mcp_id=mcp_id,
            developer_id=developer,
            request_id='req_invoice',
            capability_name='test',
            request_payload={},
            gross_amount=Decimal('0.50')
        )
        billing.complete_transaction(txn_id, response={}, response_time_ms=100)

        # Generate invoice
        today = date.today()
        invoice = billing.generate_invoice(
            ai_platform_id=ai_platform,
            period_start=today - timedelta(days=30),
            period_end=today
        )

        assert invoice is not None
        assert invoice.subtotal == Decimal('0.50')
        assert invoice.total == Decimal('0.50')
        assert invoice.status == InvoiceStatus.DRAFT

    def test_process_payout(self, db, billing, developer, ai_platform):
        """Test payout processing"""
        mcp_id = str(uuid.uuid4())
        db.execute(
            """
            INSERT INTO mcps (id, developer_id, name, slug, category, endpoint_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (mcp_id, developer, 'Test MCP', 'test-payout', 'utilities', 'http://localhost')
        )

        # Log and complete transactions
        for i in range(3):
            txn_id = billing.log_transaction(
                ai_platform_id=ai_platform,
                mcp_id=mcp_id,
                developer_id=developer,
                request_id=f'req_payout_{i}',
                capability_name='test',
                request_payload={},
                gross_amount=Decimal('1.00')
            )
            billing.complete_transaction(txn_id, response={}, response_time_ms=100)

        # Process payout
        today = date.today()
        payout = billing.process_payouts(
            developer_id=developer,
            period_start=today - timedelta(days=30),
            period_end=today
        )

        assert payout is not None
        assert payout.amount == Decimal('2.40')  # 3 * $1.00 * 80%
        assert payout.status == PayoutStatus.PENDING

    def test_revenue_summary(self, db, billing, developer, ai_platform):
        """Test revenue summary report"""
        mcp_id = str(uuid.uuid4())
        db.execute(
            """
            INSERT INTO mcps (id, developer_id, name, slug, category, endpoint_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (mcp_id, developer, 'Test MCP', 'test-revenue', 'utilities', 'http://localhost')
        )

        # Log and complete transactions
        for i in range(5):
            txn_id = billing.log_transaction(
                ai_platform_id=ai_platform,
                mcp_id=mcp_id,
                developer_id=developer,
                request_id=f'req_revenue_{i}',
                capability_name='test',
                request_payload={},
                gross_amount=Decimal('0.10')
            )
            billing.complete_transaction(txn_id, response={}, response_time_ms=100)

        # Get summary
        today = date.today()
        summary = billing.get_platform_revenue_summary(
            start_date=today - timedelta(days=30),
            end_date=today
        )

        assert summary['gross_revenue'] == 0.50  # 5 * $0.10
        assert summary['platform_revenue'] == 0.10  # 20% of $0.50
        assert summary['total_requests'] == 5


# ============================================
# INTEGRATION TESTS
# ============================================

class TestIntegration:
    """End-to-end integration tests"""

    def test_full_request_flow(self, db, developer, ai_platform):
        """Test complete flow: registration -> routing -> billing"""
        registry = MCPRegistry(db)
        router = MCPRouter(db)
        billing = BillingSystem(db)

        # 1. Register and activate MCP
        mcp_id = registry.register_mcp(
            developer_id=developer,
            name='Integration Test MCP',
            slug='integration-test',
            category=MCPCategory.RIDESHARE,
            endpoint_url='http://localhost:8000',
            fee_per_request=0.02,
            capabilities=[
                MCPCapability(name='compare_prices', description='Compare prices')
            ]
        )
        registry.activate_mcp(mcp_id)

        # 2. Route request
        result = router.route_request(RoutingRequest(
            capability='compare_prices',
            payload={'pickup': {'lat': 37.7879}, 'dropoff': {'lat': 37.6213}},
            category=MCPCategory.RIDESHARE
        ))

        assert result.success is True
        assert result.mcp_id == mcp_id

        # 3. Log billing transaction
        txn_id = billing.log_transaction(
            ai_platform_id=ai_platform,
            mcp_id=mcp_id,
            developer_id=developer,
            request_id=f'req_{uuid.uuid4()}',
            capability_name='compare_prices',
            request_payload={'pickup': {'lat': 37.7879}},
            gross_amount=Decimal('0.02')
        )
        billing.complete_transaction(txn_id, response=result.response, response_time_ms=result.response_time_ms)

        # 4. Verify billing
        txn = billing.get_transaction(txn_id)
        assert txn.status == TransactionStatus.COMPLETED
        assert txn.developer_payout == Decimal('0.0160')  # 80% of $0.02

    def test_multiple_mcps_routing(self, db, developer):
        """Test routing across multiple MCPs"""
        registry = MCPRegistry(db)
        router = MCPRouter(db)

        # Create 3 MCPs with different ratings
        for i, rating in enumerate([4.0, 4.5, 4.2]):
            mcp_id = registry.register_mcp(
                developer_id=developer,
                name=f'MCP {i+1}',
                slug=f'mcp-{i+1}',
                category=MCPCategory.RIDESHARE,
                endpoint_url=f'http://localhost:{8000+i}',
                fee_per_request=0.02 - (i * 0.005),  # Varying prices
                capabilities=[
                    MCPCapability(name='compare_prices', description='')
                ]
            )
            registry.activate_mcp(mcp_id)
            registry.update_rating(mcp_id, rating)

        # Get scores
        scores = router.get_routing_scores('compare_prices', MCPCategory.RIDESHARE)

        assert len(scores) == 3
        # Highest rated should be first
        assert scores[0]['mcp_name'] == 'MCP 2'  # Rating 4.5


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short'])
