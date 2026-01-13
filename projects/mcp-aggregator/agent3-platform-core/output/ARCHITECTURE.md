# MCP Aggregator Platform - Architecture

System design documentation for the Universal MCP Aggregation Platform.

---

## Overview

The MCP Aggregator Platform is a marketplace that connects AI agents (Claude, ChatGPT) with service providers through Model Context Protocol (MCP) servers.

```
┌─────────────────────────────────────────────────────────────────┐
│                        TIER 1: AI AGENTS                        │
│                  (Claude, ChatGPT, Gemini, etc.)                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TIER 2: MCP AGGREGATOR (US)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Registry │  │  Router  │  │ Billing  │  │ Monitor  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                  │
│  Features:                                                       │
│  - MCP discovery & registration                                  │
│  - Intelligent request routing                                   │
│  - Transaction billing (10-20% fee)                              │
│  - Quality monitoring & SLAs                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     TIER 3: MCP SERVERS                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │   Rideshare    │  │    Weather     │  │    Flights     │    │
│  │  Comparison    │  │    Lookup      │  │    Search      │    │
│  │  (Flagship)    │  │   (3rd Party)  │  │   (3rd Party)  │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TIER 4: SERVICE PROVIDERS                     │
│              (Uber, Lyft, Airlines, Hotels, etc.)               │
│                      [Commoditized Layer]                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Database Layer (`database.py`)

**Purpose:** Unified database access for SQLite (testing) and PostgreSQL (production).

**Key Features:**
- Connection pooling for PostgreSQL
- Query helpers with parameterized queries
- Transaction support with rollback
- Health checks
- Schema introspection

**Usage:**
```python
from database import Database, DatabaseConfig, create_test_database

# Testing (SQLite)
db = create_test_database()

# Production (PostgreSQL)
db = Database(DatabaseConfig.from_env())
db.connect()

# Query
rows = db.fetch_all("SELECT * FROM mcps WHERE status = ?", ('active',))
```

---

### 2. MCP Registry (`registry.py`)

**Purpose:** Discovery and management of MCP servers.

**Key Features:**
- MCP registration with validation
- Multi-criteria discovery (category, capability, tags)
- Health monitoring and status tracking
- Rating management
- Circuit breaker integration

**Data Model:**
```
MCP
├── id (UUID)
├── developer_id (FK)
├── name, slug, description
├── category (rideshare, flights, hotels, etc.)
├── endpoint_url
├── fee_per_request ($0.01-$0.10)
├── developer_share (80%)
├── status (active, inactive, suspended)
├── avg_response_time_ms
├── avg_rating (0-5)
├── uptime_percent
└── capabilities[] (name, input_schema, output_schema)
```

**Usage:**
```python
from registry import MCPRegistry, MCPCategory, MCPCapability

registry = MCPRegistry(db)

# Register
mcp_id = registry.register_mcp(
    developer_id='...',
    name='Weather Lookup',
    slug='weather-lookup',
    category=MCPCategory.UTILITIES,
    endpoint_url='http://localhost:8000/weather',
    capabilities=[
        MCPCapability(name='current_weather', description='...')
    ]
)

# Discover
mcps = registry.find_mcps(category=MCPCategory.RIDESHARE)
mcps = registry.find_by_capability('compare_prices')

# Health
status = registry.get_health_status(mcp_id)
```

---

### 3. Routing Engine (`router.py`)

**Purpose:** Intelligently route requests to the best available MCP.

**Key Features:**
- Multi-factor scoring algorithm
- Circuit breaker pattern (fault tolerance)
- Automatic fallback to alternatives
- Configurable routing strategies
- Request execution with timeouts

**Scoring Algorithm:**
```
Total Score =
    Health Score (30%) +
    Performance Score (25%) +
    Cost Score (20%) +
    Rating Score (25%)
```

**Circuit Breaker States:**
```
CLOSED ──(5 failures)──> OPEN ──(30s timeout)──> HALF_OPEN
   ▲                                                  │
   └──────────────(success)───────────────────────────┘
```

**Usage:**
```python
from router import MCPRouter, RoutingRequest, MCPCategory

router = MCPRouter(db)

# Route request (automatic selection)
result = router.route_request(RoutingRequest(
    capability='compare_prices',
    payload={'pickup': {...}, 'dropoff': {...}},
    category=MCPCategory.RIDESHARE,
    max_latency_ms=5000
))

if result.success:
    print(f"Response: {result.response}")
    print(f"Latency: {result.response_time_ms}ms")
    print(f"Cost: ${result.cost}")

# Direct execution (bypass routing)
result = router.execute_mcp(mcp_id, payload, timeout_ms=5000)

# Get scoring breakdown
scores = router.get_routing_scores('compare_prices')
```

---

### 4. Billing System (`billing.py`)

**Purpose:** Handle all financial transactions.

**Key Features:**
- Per-request transaction logging
- Fee calculation (platform vs developer split)
- Invoice generation for AI platforms
- Payout processing for developers
- Revenue reporting

**Fee Structure:**
```
Gross Amount: $0.02 per request (charged to AI platform)
├── Platform Fee: $0.004 (20%)
└── Developer Payout: $0.016 (80%)
```

**Usage:**
```python
from billing import BillingSystem
from decimal import Decimal

billing = BillingSystem(db)

# Log transaction (before execution)
txn_id = billing.log_transaction(
    ai_platform_id='...',
    mcp_id='...',
    developer_id='...',
    request_id='req_123',
    capability_name='compare_prices',
    request_payload={...},
    gross_amount=Decimal('0.02')
)

# Complete (after success)
billing.complete_transaction(txn_id, response={...}, response_time_ms=150)

# Or fail
billing.fail_transaction(txn_id, "Error message")

# Generate invoice
invoice = billing.generate_invoice(
    ai_platform_id='...',
    period_start=date(2026, 1, 1),
    period_end=date(2026, 1, 31)
)

# Process payout
payout = billing.process_payouts(
    developer_id='...',
    period_start=date(2026, 1, 1),
    period_end=date(2026, 1, 31)
)

# Reports
summary = billing.get_platform_revenue_summary(start_date, end_date)
```

---

## Database Schema

**Core Tables:**

| Table | Purpose |
|-------|---------|
| `developers` | MCP developers/companies |
| `ai_platforms` | AI clients (Claude, ChatGPT) |
| `mcps` | Registered MCP servers |
| `mcp_capabilities` | What each MCP can do |
| `circuit_breaker_state` | Fault tolerance state |
| `transactions` | Every billable API call |
| `rate_cards` | Rideshare pricing data |
| `health_checks` | MCP health history |
| `daily_stats` | Aggregated metrics |
| `payouts` | Developer payments |
| `invoices` | Platform invoices |

**Views:**
- `mcp_directory` - Public-facing MCP info
- `revenue_summary` - Admin dashboard
- `developer_dashboard` - Developer stats

See `schema.sql` for complete schema.

---

## Request Flow

```
1. AI Agent sends request
   └── POST /v1/route
       { "capability": "compare_prices", "payload": {...} }

2. Router finds candidates
   └── MCPs with matching capability
   └── Filter by category, cost, latency

3. Router scores candidates
   └── Health: 30%
   └── Performance: 25%
   └── Cost: 20%
   └── Rating: 25%

4. Router executes best MCP
   └── Check circuit breaker
   └── Send request with timeout
   └── On failure: try fallback

5. Billing records transaction
   └── Log transaction (pending)
   └── Complete on success
   └── Update daily stats

6. Response returned to AI Agent
   └── { "success": true, "response": {...}, "cost": 0.02 }
```

---

## Error Handling

**Circuit Breaker Pattern:**
```python
# Automatic protection against failing MCPs

if failures >= 5:
    state = OPEN  # Reject requests for 30s

after 30 seconds:
    state = HALF_OPEN  # Allow 1 test request

if test succeeds:
    state = CLOSED  # Resume normal operation
else:
    state = OPEN  # Keep rejecting
```

**Fallback Strategy:**
```python
# Try MCPs in order of score until one succeeds

for mcp in sorted_by_score:
    try:
        return mcp.execute(payload)
    except:
        continue  # Try next MCP

raise AllMCPsFailed()
```

---

## Security

**Authentication:**
- API key hashing (bcrypt)
- Request ID for idempotency
- Row-level security (prepared for RLS)

**Data Protection:**
- Parameterized queries (SQL injection prevention)
- Input validation in registry
- Sensitive fields hashed, not stored plaintext

---

## Monitoring

**Metrics Collected:**
- Response time (avg, p95, p99)
- Error rate
- Uptime percentage
- Request volume
- Revenue per MCP/developer

**Health Checks:**
- Periodic ping to MCP endpoints
- Status code verification
- Latency measurement

---

## Scaling Considerations

**Current Design (MVP):**
- Single PostgreSQL database
- Synchronous request handling
- In-process circuit breakers

**Future Improvements:**
1. **Database:** Read replicas, connection pooling
2. **Caching:** Redis for routing decisions
3. **Queue:** Async transaction logging
4. **Distribution:** Consistent hashing for circuit breakers
5. **Rate Limiting:** Per-platform request limits

---

## File Structure

```
agent3-platform-core/
├── workspace/
│   ├── schema.sql           # PostgreSQL schema
│   ├── seed_data.sql        # Initial data
│   ├── database.py          # Connection layer
│   ├── registry.py          # MCP registry
│   ├── router.py            # Routing engine
│   ├── billing.py           # Billing system
│   ├── test_platform.py     # Test suite
│   └── test_connection.py   # PostgreSQL test
│
└── output/
    ├── DATABASE-SETUP.md    # Setup guide
    ├── ARCHITECTURE.md      # This file
    ├── INTEGRATION-GUIDE.md # API usage
    ├── HUMAN-TODO.md        # Setup tasks
    └── FINDINGS.md          # Development notes
```

---

## Next Steps

1. **API Layer:** REST endpoints for AI platforms
2. **Developer Portal:** MCP registration UI
3. **Stripe Integration:** Real payment processing
4. **Monitoring Dashboard:** Real-time metrics

---

**Questions?** See `INTEGRATION-GUIDE.md` for API usage or `DATABASE-SETUP.md` for setup.
