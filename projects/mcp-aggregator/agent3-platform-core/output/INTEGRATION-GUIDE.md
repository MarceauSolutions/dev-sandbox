# MCP Aggregator Platform - Integration Guide

How to integrate with and use the MCP Aggregator Platform.

---

## Quick Start

### 1. Setup Database

```bash
# See DATABASE-SETUP.md for full instructions
createdb mcp_aggregator
psql mcp_aggregator < workspace/schema.sql
psql mcp_aggregator < workspace/seed_data.sql
```

### 2. Run Tests

```bash
cd workspace
pip install pytest
pytest test_platform.py -v
```

### 3. Use the Platform

```python
from database import create_test_database
from registry import MCPRegistry, MCPCategory
from router import MCPRouter, RoutingRequest
from billing import BillingSystem

# Initialize (use create_test_database for testing)
db = create_test_database()
registry = MCPRegistry(db)
router = MCPRouter(db)
billing = BillingSystem(db)
```

---

## Registering an MCP

### Basic Registration

```python
from registry import MCPRegistry, MCPCategory, MCPCapability

registry = MCPRegistry(db)

mcp_id = registry.register_mcp(
    developer_id='your-developer-uuid',
    name='My Weather Service',
    slug='my-weather-service',
    category=MCPCategory.UTILITIES,
    endpoint_url='https://api.example.com/weather',
    description='Get current weather for any location',
    fee_per_request=0.01,
    tags=['weather', 'forecast', 'geolocation'],
    supported_regions=['us', 'eu']
)

# Activate the MCP (required before it can receive traffic)
registry.activate_mcp(mcp_id)
```

### With Capabilities

```python
mcp_id = registry.register_mcp(
    developer_id='...',
    name='Rideshare Comparison',
    slug='rideshare-compare',
    category=MCPCategory.RIDESHARE,
    endpoint_url='https://api.example.com/rideshare',
    capabilities=[
        MCPCapability(
            name='compare_prices',
            description='Compare Uber and Lyft prices',
            input_schema={
                'type': 'object',
                'required': ['pickup', 'dropoff'],
                'properties': {
                    'pickup': {'type': 'object'},
                    'dropoff': {'type': 'object'}
                }
            },
            output_schema={
                'type': 'object',
                'properties': {
                    'uber': {'type': 'object'},
                    'lyft': {'type': 'object'},
                    'recommendation': {'type': 'string'}
                }
            }
        ),
        MCPCapability(
            name='get_supported_cities',
            description='List cities with coverage'
        )
    ]
)
```

---

## Discovering MCPs

### Find by Category

```python
# Get all active rideshare MCPs
mcps = registry.find_mcps(category=MCPCategory.RIDESHARE)

for mcp in mcps:
    print(f"{mcp.name}: ${mcp.fee_per_request}/request, rating: {mcp.avg_rating}")
```

### Find by Capability

```python
# Find MCPs that can compare prices
mcps = registry.find_by_capability('compare_prices')
```

### Advanced Search

```python
mcps = registry.find_mcps(
    category=MCPCategory.UTILITIES,
    search='weather',           # Search name/description
    tags=['geolocation'],       # Filter by tags
    region='us',                # Filter by region
    min_rating=4.0,             # Minimum rating
    max_response_time_ms=500,   # Maximum latency
    limit=10
)
```

---

## Routing Requests

### Automatic Routing

The router automatically selects the best MCP based on scoring.

```python
from router import MCPRouter, RoutingRequest, MCPCategory

router = MCPRouter(db)

result = router.route_request(RoutingRequest(
    capability='compare_prices',
    payload={
        'pickup': {'latitude': 37.7879, 'longitude': -122.4074},
        'dropoff': {'latitude': 37.6213, 'longitude': -122.3790}
    },
    category=MCPCategory.RIDESHARE,
    timeout_ms=5000
))

if result.success:
    print(f"Response: {result.response}")
    print(f"MCP used: {result.mcp_name}")
    print(f"Latency: {result.response_time_ms}ms")
    print(f"Cost: ${result.cost}")
else:
    print(f"Error: {result.error}")
    print(f"Attempts: {result.attempts}")
```

### With Constraints

```python
result = router.route_request(RoutingRequest(
    capability='compare_prices',
    payload={...},
    category=MCPCategory.RIDESHARE,
    max_latency_ms=200,     # Require fast response
    max_cost=0.01,          # Budget constraint
    preferred_mcp_id='...'  # Prefer specific MCP
))
```

### Direct Execution

Bypass routing to call a specific MCP.

```python
result = router.execute_mcp(
    mcp_id='specific-mcp-uuid',
    payload={'location': 'San Francisco'},
    timeout_ms=3000
)
```

### Scoring Breakdown

See why MCPs are ranked the way they are.

```python
scores = router.get_routing_scores('compare_prices', MCPCategory.RIDESHARE)

for score in scores:
    print(f"{score['mcp_name']}:")
    print(f"  Total: {score['total_score']}")
    print(f"  Health: {score['health_score']}")
    print(f"  Performance: {score['performance_score']}")
    print(f"  Cost: {score['cost_score']}")
    print(f"  Rating: {score['rating_score']}")
    print(f"  Eligible: {score['is_eligible']}")
```

---

## Billing

### Log a Transaction

```python
from billing import BillingSystem
from decimal import Decimal

billing = BillingSystem(db)

# 1. Log transaction before MCP execution
txn_id = billing.log_transaction(
    ai_platform_id='claude-platform-uuid',
    mcp_id='rideshare-mcp-uuid',
    developer_id='developer-uuid',
    request_id='req_abc123',  # Idempotency key
    capability_name='compare_prices',
    request_payload={'pickup': {...}},
    gross_amount=Decimal('0.02')
)

# 2. Execute MCP (your logic here)
response = execute_mcp(...)

# 3a. On success
billing.complete_transaction(
    txn_id,
    response={'uber': '$42', 'lyft': '$38'},
    response_time_ms=145
)

# 3b. On failure
billing.fail_transaction(txn_id, "MCP timeout")
```

### Fee Calculation

```python
fees = billing.calculate_fees(Decimal('0.10'))

print(f"Gross: ${fees.gross_amount}")
print(f"Platform fee (20%): ${fees.platform_fee}")
print(f"Developer payout (80%): ${fees.developer_payout}")
```

### Invoices

```python
from datetime import date, timedelta

# Generate invoice for AI platform
invoice = billing.generate_invoice(
    ai_platform_id='claude-uuid',
    period_start=date(2026, 1, 1),
    period_end=date(2026, 1, 31),
    tax_rate=Decimal('0.0'),
    due_days=30
)

print(f"Invoice {invoice.id}: ${invoice.total}")
print(f"Due: {invoice.due_date}")

# Send invoice
billing.send_invoice(invoice.id)

# Mark as paid
billing.mark_invoice_paid(invoice.id, stripe_invoice_id='inv_xxx')
```

### Payouts

```python
# Calculate developer earnings
payout = billing.process_payouts(
    developer_id='dev-uuid',
    period_start=date(2026, 1, 1),
    period_end=date(2026, 1, 31)
)

print(f"Payout {payout.id}: ${payout.amount}")

# Execute payout
billing.execute_payout(payout.id, stripe_transfer_id='tr_xxx')
```

### Reports

```python
# Platform revenue summary
summary = billing.get_platform_revenue_summary(
    start_date=date(2026, 1, 1),
    end_date=date(2026, 1, 31)
)

print(f"Gross revenue: ${summary['gross_revenue']}")
print(f"Platform revenue: ${summary['platform_revenue']}")
print(f"Requests: {summary['total_requests']}")
print(f"Success rate: {summary['success_rate_percent']}%")

# Developer earnings
earnings = billing.get_developer_earnings(
    developer_id='dev-uuid',
    start_date=date(2026, 1, 1),
    end_date=date(2026, 1, 31)
)
```

---

## Health Monitoring

### Check MCP Health

```python
status = registry.get_health_status(mcp_id)

print(f"Status: {status['status']}")
print(f"Is healthy: {status['is_healthy']}")
print(f"Circuit breaker: {status['circuit_breaker_state']}")
print(f"Avg latency: {status['avg_response_time_ms']}ms")
print(f"Error rate: {status['error_rate_percent']}%")
print(f"Uptime: {status['uptime_percent']}%")
```

### Record Health Check

```python
from registry import HealthCheckResult

registry.record_health_check(HealthCheckResult(
    mcp_id=mcp_id,
    is_healthy=True,
    response_time_ms=120,
    status_code=200
))
```

---

## Custom MCP Executor

By default, the router uses a mock executor for testing. Provide your own for production.

```python
import requests

def real_executor(mcp, payload):
    """Execute actual HTTP request to MCP"""
    response = requests.post(
        mcp.endpoint_url,
        json=payload,
        timeout=mcp.timeout_ms / 1000
    )
    response.raise_for_status()
    return response.json()

router = MCPRouter(db, executor=real_executor)
```

---

## Error Handling

### Routing Errors

```python
result = router.route_request(...)

if not result.success:
    if 'No MCPs found' in result.error:
        # No MCPs can handle this capability
        pass
    elif 'circuit breaker' in result.error.lower():
        # All MCPs are failing
        pass
    elif 'timed out' in result.error.lower():
        # Request took too long
        pass
    elif result.fallback_used:
        # Primary failed, fallback also failed
        pass
```

### Duplicate Transactions

```python
try:
    billing.log_transaction(request_id='req_123', ...)
except ValueError as e:
    if 'Duplicate request_id' in str(e):
        # This request was already processed
        existing = billing.get_transaction_by_request_id('req_123')
```

---

## Testing with SQLite

The platform automatically uses SQLite for testing (no PostgreSQL required).

```python
from database import create_test_database

# Creates in-memory SQLite database with schema
db = create_test_database()

# Use normally
registry = MCPRegistry(db)
router = MCPRouter(db)
billing = BillingSystem(db)

# Clean up
db.close()
```

---

## Environment Configuration

Set `DATABASE_URL` for PostgreSQL:

```bash
# Local development
export DATABASE_URL="postgresql://postgres@localhost:5432/mcp_aggregator"

# With credentials
export DATABASE_URL="postgresql://user:password@host:5432/database"

# Heroku-style
export DATABASE_URL="postgres://user:pass@host:5432/db"
```

The platform auto-detects and parses the URL format.

---

## Best Practices

1. **Use request IDs for idempotency**
   ```python
   billing.log_transaction(request_id=f"req_{uuid.uuid4()}", ...)
   ```

2. **Always activate MCPs after registration**
   ```python
   mcp_id = registry.register_mcp(...)
   registry.activate_mcp(mcp_id)
   ```

3. **Handle routing failures gracefully**
   ```python
   result = router.route_request(...)
   if not result.success and result.attempts > 1:
       # Multiple MCPs tried and failed
       log_critical_error(result.error)
   ```

4. **Monitor circuit breaker state**
   ```python
   status = registry.get_health_status(mcp_id)
   if status['circuit_breaker_state'] == 'open':
       alert_ops_team(mcp_id)
   ```

5. **Use transactions for critical operations**
   ```python
   with db.transaction():
       # Multiple related operations
       billing.log_transaction(...)
       registry.increment_request_count(...)
   ```

---

**Questions?** See `ARCHITECTURE.md` for system design or `DATABASE-SETUP.md` for setup.
