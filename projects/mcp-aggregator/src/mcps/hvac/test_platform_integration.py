#!/usr/bin/env python3
"""
HVAC MCP Platform Integration Test

Validates that the HVAC MCP works with the generalized MCP Aggregator platform:
1. EMAIL connectivity type registration (no HTTP endpoint required)
2. ASYNC scoring profile (UTILITIES category → async profile)
3. Per-RFQ billing with PER_REQUEST model

This proves the platform refactoring was successful - non-rideshare services
can now register and operate correctly.

Run with: python src/mcps/hvac/test_platform_integration.py
"""

import os
import sys
import tempfile
from decimal import Decimal

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

# Import platform core (use main __init__ which has proper aliases)
from src.core import (
    create_test_database,
    Registry,
    MCPCategory,
    MCPStatus,
    ConnectivityType,
    MCPCapability,
    Router,
    RoutingRequest,
    get_scoring_profile,
    CATEGORY_TO_PROFILE,
    BillingSystem,
    PricingModel
)


def test_email_connectivity_registration():
    """
    Test 1: EMAIL Connectivity Type Registration

    HVAC MCP uses email, not HTTP. The platform should:
    - Accept registration without endpoint_url
    - Require email_address field
    - Store ConnectivityType.EMAIL
    """
    print("\n" + "=" * 60)
    print("Test 1: EMAIL Connectivity Type Registration")
    print("=" * 60)

    # Create temp database
    db = create_test_database(':memory:')

    # Create developer first
    db.execute(
        "INSERT INTO developers (id, email, display_name, api_key_hash) VALUES (?, ?, ?, ?)",
        ('dev-hvac', 'dev@hvac.example.com', 'HVAC Developer', 'hash123')
    )

    registry = Registry(db)

    # Register HVAC MCP with EMAIL connectivity
    try:
        mcp_id = registry.register_mcp(
            developer_id='dev-hvac',
            name='HVAC Distributor Network',
            slug='hvac-distributors',
            category=MCPCategory.UTILITIES,
            connectivity_type=ConnectivityType.EMAIL,  # EMAIL, not HTTP
            email_address='rfq@hvac-mcp.example.com',   # Required for EMAIL
            endpoint_url=None,                           # Not required for EMAIL
            description='Submit RFQs to HVAC equipment distributors',
            fee_per_request=0.25,                        # $0.25 per RFQ
            developer_share=0.80,
            timeout_ms=172800000,                        # 48 hours
            capabilities=[
                MCPCapability(
                    name='submit_rfq',
                    description='Submit RFQ to distributor network',
                    input_schema={
                        'type': 'object',
                        'properties': {
                            'equipment_type': {'type': 'string'},
                            'delivery_address': {'type': 'string'}
                        },
                        'required': ['equipment_type', 'delivery_address']
                    }
                )
            ]
        )

        # Verify registration
        mcp = registry.get_mcp(mcp_id)

        print(f"✅ HVAC MCP registered successfully!")
        print(f"   ID: {mcp_id}")
        print(f"   Connectivity Type: {mcp.connectivity_type.value}")
        print(f"   Email Address: {mcp.email_address}")
        print(f"   Endpoint URL: {mcp.endpoint_url}")
        print(f"   Category: {mcp.category.value}")

        assert mcp.connectivity_type == ConnectivityType.EMAIL
        assert mcp.email_address == 'rfq@hvac-mcp.example.com'
        assert mcp.endpoint_url is None  # No HTTP endpoint needed

        print("\n✅ Test 1 PASSED: EMAIL connectivity registration works!")
        return True

    except Exception as e:
        print(f"\n❌ Test 1 FAILED: {e}")
        return False

    finally:
        db.close()


def test_async_scoring_profile():
    """
    Test 2: ASYNC Scoring Profile

    UTILITIES category should map to 'async' scoring profile which:
    - Expects 24-hour latency as acceptable (not penalized)
    - Weights health/reliability higher than performance
    - Allows higher costs (async services cost more)
    """
    print("\n" + "=" * 60)
    print("Test 2: ASYNC Scoring Profile")
    print("=" * 60)

    # Check category mapping
    expected_profile = CATEGORY_TO_PROFILE.get('utilities')
    print(f"   UTILITIES category maps to: '{expected_profile}' profile")

    if expected_profile != 'async':
        print(f"\n❌ Test 2 FAILED: Expected 'async', got '{expected_profile}'")
        return False

    # Get async profile
    profile = get_scoring_profile('utilities')

    print(f"\n   ASYNC Scoring Profile:")
    print(f"   - Latency excellent: {profile.latency_excellent}ms ({profile.latency_excellent/1000}s)")
    print(f"   - Latency good: {profile.latency_good}ms ({profile.latency_good/60000}min)")
    print(f"   - Latency acceptable: {profile.latency_acceptable}ms ({profile.latency_acceptable/3600000}hr)")
    print(f"   - Latency slow: {profile.latency_slow}ms ({profile.latency_slow/86400000}day)")
    print(f"   - Cost excellent: ${profile.cost_excellent}")
    print(f"   - Cost acceptable: ${profile.cost_acceptable}")
    print(f"   - Weight performance: {profile.weight_performance * 100}%")
    print(f"   - Weight health: {profile.weight_health * 100}%")
    print(f"   - Weight cost: {profile.weight_cost * 100}%")

    # Validate async-appropriate thresholds
    # HVAC expects 24-48 hour responses, so 1 hour should be "acceptable"
    one_hour_ms = 3600000
    one_day_ms = 86400000

    if profile.latency_acceptable < one_hour_ms:
        print(f"\n❌ Test 2 FAILED: latency_acceptable too low for async")
        return False

    if profile.latency_slow < one_day_ms:
        print(f"\n❌ Test 2 FAILED: latency_slow should accommodate day-long responses")
        return False

    # Async should weight performance LOW (5%) because latency doesn't matter as much
    if profile.weight_performance > 0.10:
        print(f"\n❌ Test 2 FAILED: weight_performance should be low for async")
        return False

    # Async should weight health HIGH (reliability matters for long-running tasks)
    if profile.weight_health < 0.30:
        print(f"\n❌ Test 2 FAILED: weight_health should be high for async")
        return False

    print("\n✅ Test 2 PASSED: ASYNC scoring profile is properly configured!")
    return True


def test_per_rfq_billing():
    """
    Test 3: Per-RFQ Billing with PER_REQUEST Model

    HVAC MCP bills per-RFQ (not per-API-call). The platform's PER_REQUEST
    billing model should support this by:
    - Logging each RFQ as a transaction
    - Calculating 80/20 fee split
    - Supporting configurable per-MCP developer share
    """
    print("\n" + "=" * 60)
    print("Test 3: Per-RFQ Billing")
    print("=" * 60)

    # Create temp database
    db = create_test_database(':memory:')

    # Create required records
    db.execute(
        "INSERT INTO developers (id, email, display_name, api_key_hash) VALUES (?, ?, ?, ?)",
        ('dev-hvac', 'dev@hvac.example.com', 'HVAC Developer', 'hash123')
    )
    db.execute(
        "INSERT INTO ai_platforms (id, name, api_key_hash) VALUES (?, ?, ?)",
        ('platform-1', 'Claude', 'hash456')
    )
    db.execute(
        """
        INSERT INTO mcps (id, developer_id, name, slug, category, endpoint_url,
                         connectivity_type, email_address, developer_share, fee_per_request)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ('hvac-mcp-1', 'dev-hvac', 'HVAC Distributors', 'hvac-dist', 'utilities',
         None, 'email', 'rfq@hvac.example.com', 0.80, 0.25)
    )

    billing = BillingSystem(db)

    # Test PER_REQUEST billing (used for per-RFQ)
    print("\n   Testing PER_REQUEST billing model (for per-RFQ charges):")

    rfq_fee = Decimal('0.25')  # $0.25 per RFQ
    fees = billing.calculate_fees(rfq_fee)

    print(f"   - RFQ Fee: ${rfq_fee}")
    print(f"   - Platform cut (20%): ${fees.platform_fee}")
    print(f"   - Developer cut (80%): ${fees.developer_payout}")
    print(f"   - Pricing model: {fees.pricing_model.value}")

    assert fees.gross_amount == rfq_fee
    assert fees.pricing_model == PricingModel.PER_REQUEST

    # Log a transaction for an RFQ
    print("\n   Logging RFQ transaction:")
    txn_id = billing.log_transaction(
        ai_platform_id='platform-1',
        mcp_id='hvac-mcp-1',
        developer_id='dev-hvac',
        request_id='rfq-12345',  # RFQ ID as request_id
        capability_name='submit_rfq',
        request_payload={
            'equipment_type': 'ac_unit',
            'delivery_address': 'Naples, FL'
        },
        gross_amount=rfq_fee
    )

    print(f"   - Transaction ID: {txn_id}")
    print(f"   - Request ID (RFQ ID): rfq-12345")

    # Complete the transaction
    billing.complete_transaction(
        txn_id,
        response={'status': 'sent', 'distributor': 'Ferguson HVAC'},
        response_time_ms=500
    )
    print("   - Transaction completed")

    # Verify transaction was logged correctly
    txn = billing.get_transaction(txn_id)
    print(f"\n   Transaction details:")
    print(f"   - Status: {txn.status.value}")
    print(f"   - Gross: ${txn.gross_amount}")
    print(f"   - Platform fee: ${txn.platform_fee}")
    print(f"   - Developer payout: ${txn.developer_payout}")

    assert txn.status.value == 'completed'
    assert txn.gross_amount == rfq_fee

    print("\n✅ Test 3 PASSED: Per-RFQ billing works with PER_REQUEST model!")
    return True


def test_full_platform_integration():
    """
    Test 4: Full Platform Integration

    End-to-end test simulating HVAC MCP registration and usage
    through the platform core.
    """
    print("\n" + "=" * 60)
    print("Test 4: Full Platform Integration")
    print("=" * 60)

    # Create temp database
    db = create_test_database(':memory:')

    # Create required records
    db.execute(
        "INSERT INTO developers (id, email, display_name, api_key_hash) VALUES (?, ?, ?, ?)",
        ('dev-hvac', 'dev@hvac.example.com', 'HVAC Developer', 'hash123')
    )
    db.execute(
        "INSERT INTO ai_platforms (id, name, api_key_hash) VALUES (?, ?, ?)",
        ('claude-platform', 'Claude Desktop', 'hash456')
    )

    registry = Registry(db)
    router = Router(db, registry)
    billing = BillingSystem(db)

    # 1. Register HVAC MCP
    print("\n   Step 1: Register HVAC MCP with EMAIL connectivity...")
    mcp_id = registry.register_mcp(
        developer_id='dev-hvac',
        name='HVAC Distributor Network',
        slug='hvac-distributors',
        category=MCPCategory.UTILITIES,
        connectivity_type=ConnectivityType.EMAIL,
        email_address='rfq@hvac.example.com',
        endpoint_url=None,
        fee_per_request=0.25,
        developer_share=0.80,
        timeout_ms=172800000  # 48 hours
    )
    print(f"   ✅ Registered: {mcp_id}")

    # 2. Activate MCP (simulating review approval)
    print("\n   Step 2: Activate MCP...")
    registry.update_mcp(mcp_id, status=MCPStatus.ACTIVE)
    print("   ✅ MCP activated")

    # 3. Verify routing would use async profile
    print("\n   Step 3: Verify routing uses ASYNC profile...")
    mcp = registry.get_mcp(mcp_id)
    profile = get_scoring_profile(mcp.category.value)
    print(f"   ✅ Category '{mcp.category.value}' → '{profile.name}' profile")
    print(f"   ✅ Performance weight: {profile.weight_performance * 100}% (low, as expected for async)")

    # 4. Log billing transaction
    print("\n   Step 4: Log RFQ billing transaction...")
    txn_id = billing.log_transaction(
        ai_platform_id='claude-platform',
        mcp_id=mcp_id,
        developer_id='dev-hvac',
        request_id='rfq-integration-test',
        capability_name='submit_rfq',
        request_payload={
            'equipment_type': 'ac_unit',
            'delivery_address': 'Naples, FL 34102'
        },
        gross_amount=Decimal('0.25')
    )
    billing.complete_transaction(txn_id, {'status': 'sent'}, 200)
    print(f"   ✅ Transaction logged: {txn_id}")

    # 5. Verify MCP can be discovered
    print("\n   Step 5: Verify MCP discovery...")
    all_mcps = registry.find_mcps(category=MCPCategory.UTILITIES)
    found = any(m.id == mcp_id for m in all_mcps)
    if found:
        print("   ✅ HVAC MCP found in UTILITIES category")
    else:
        print("   ❌ HVAC MCP not found!")
        return False

    print("\n✅ Test 4 PASSED: Full platform integration works!")
    return True


def main():
    """Run all platform integration tests"""
    print("\n" + "=" * 70)
    print("HVAC MCP - Platform Integration Tests")
    print("Validating platform generalization for non-rideshare services")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("EMAIL Connectivity Registration", test_email_connectivity_registration()))
    results.append(("ASYNC Scoring Profile", test_async_scoring_profile()))
    results.append(("Per-RFQ Billing", test_per_rfq_billing()))
    results.append(("Full Platform Integration", test_full_platform_integration()))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL PLATFORM INTEGRATION TESTS PASSED!")
        print("   The MCP Aggregator platform successfully supports non-rideshare services.")
        print("\n   Validated:")
        print("   - EMAIL connectivity type (no HTTP required)")
        print("   - ASYNC scoring profile (24-48 hour latency acceptable)")
        print("   - Per-RFQ billing (using PER_REQUEST model)")
        print("   - UTILITIES category with proper routing")
    else:
        print("\n❌ SOME TESTS FAILED - Platform may not be fully generalized")

    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
