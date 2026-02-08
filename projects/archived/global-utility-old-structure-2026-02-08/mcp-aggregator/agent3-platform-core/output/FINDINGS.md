# Agent 3: Platform Core - Development Findings

Notes and decisions made during autonomous development.

---

## Development Context

**Agent:** Agent 3 - Platform Infrastructure
**Task:** Build complete platform core (database, registry, routing, billing)
**Mode:** Autonomous (minimal human intervention)
**Date:** 2026-01-12

---

## Key Design Decisions

### 1. Database Abstraction Layer

**Decision:** Created unified `Database` class that works with both SQLite and PostgreSQL.

**Rationale:**
- Allows testing without PostgreSQL setup
- Same code works in dev (SQLite) and production (PostgreSQL)
- Simplifies CI/CD (no database dependencies for tests)

**Trade-offs:**
- Some PostgreSQL-specific features can't be used (e.g., JSONB operators)
- Minor query syntax differences handled by parameter conversion

### 2. Circuit Breaker Implementation

**Decision:** Implemented circuit breaker at database level, not in-memory.

**Rationale:**
- State persists across process restarts
- Multiple instances share the same state
- Easier debugging (can query database directly)

**Parameters chosen:**
- `failure_threshold = 5` (5 failures to open)
- `recovery_timeout = 30` seconds
- `half_open_max_calls = 1` (single test request)

### 3. Scoring Algorithm Weights

**Decision:** Multi-factor scoring with these weights:

| Factor | Weight | Rationale |
|--------|--------|-----------|
| Health | 30% | Most important - avoid failing MCPs |
| Performance | 25% | User experience critical |
| Rating | 25% | Crowd-sourced quality signal |
| Cost | 20% | Important but not primary factor |

**Rationale:** Health is weighted highest because routing to a failing MCP wastes time on retries. Performance and rating are equal as both impact UX. Cost is lowest because most MCPs will have similar pricing.

### 4. Fee Structure

**Decision:** Default 80/20 split (developer gets 80%).

**Rationale:**
- Competitive with typical marketplace fees
- Enough margin to cover infrastructure costs
- Attractive to developers to encourage registration

**Flexibility:** `developer_share` can be customized per-MCP for premium partnerships.

### 5. Transaction Logging Approach

**Decision:** Log transaction BEFORE MCP execution, then update status.

**Rationale:**
- Ensures all requests are tracked, even failures
- Request ID provides idempotency
- Supports refund workflow

**Flow:**
1. `log_transaction()` → status='pending'
2. Execute MCP
3. `complete_transaction()` or `fail_transaction()`

---

## Technical Choices

### SQLite Schema Differences

PostgreSQL schema uses:
- `UUID` type → SQLite uses `TEXT`
- `ENUM` types → SQLite uses `TEXT` with CHECK
- `JSONB` → SQLite uses `TEXT` (JSON string)
- `TIMESTAMP WITH TIME ZONE` → SQLite uses `TIMESTAMP`
- Array types → SQLite uses JSON array strings

Handled in `SQLiteSchema` class with compatible DDL.

### Connection Pooling

For PostgreSQL, using `psycopg2.pool.ThreadedConnectionPool`:
- `min_connections = 2`
- `max_connections = 10`

SQLite uses single connection (thread-safe with `check_same_thread=False`).

### Query Parameter Conversion

SQLite uses `?` placeholders, PostgreSQL uses `%s`.

Handled in `_convert_params()` method with simple string replacement.

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `schema.sql` | 450+ | PostgreSQL schema |
| `seed_data.sql` | 300+ | Initial data |
| `database.py` | 500+ | Database abstraction |
| `registry.py` | 550+ | MCP registry |
| `router.py` | 600+ | Routing engine |
| `billing.py` | 600+ | Billing system |
| `test_platform.py` | 700+ | Test suite |
| `test_connection.py` | 200+ | PostgreSQL test |

**Total:** ~3,900 lines of Python code

---

## Integration Points

### With Existing Rideshare MCP

The rideshare MCP at `src/mcps/rideshare/comparison.py` can integrate as:

```python
# In comparison.py
from agent3_platform.router import MCPRouter
from agent3_platform.billing import BillingSystem

# Register capability
registry.register_mcp(
    name='Rideshare Price Comparison',
    slug='rideshare-comparison',
    category=MCPCategory.RIDESHARE,
    endpoint_url='http://localhost:8000/v1/mcps/rideshare/compare',
    capabilities=[
        MCPCapability(name='compare_prices', ...)
    ]
)
```

### With Future API Layer

The platform is designed for REST API integration:

```python
# Example API endpoint
@app.post("/v1/route")
async def route_request(request: RouteRequest):
    result = router.route_request(RoutingRequest(
        capability=request.capability,
        payload=request.payload
    ))
    return result
```

---

## Known Limitations

1. **No real HTTP executor:** Mock executor used for testing. Production needs real HTTP client.

2. **No Stripe integration:** Billing system logs transactions but doesn't connect to Stripe API.

3. **No rate limiting:** Platform doesn't enforce rate limits (would need Redis).

4. **No caching:** Routing decisions not cached (could add Redis/memcached).

5. **Single database:** No read replicas or sharding.

---

## Future Improvements

### Short Term
- Add real HTTP executor using `httpx` or `aiohttp`
- Implement Stripe Connect for payouts
- Add API layer (FastAPI recommended)

### Medium Term
- Add Redis for rate limiting and caching
- Implement webhook notifications
- Build developer portal

### Long Term
- Database sharding for scale
- Geographic distribution
- ML-based surge prediction

---

## Testing Notes

Test suite uses SQLite for speed and portability:

```bash
pytest test_platform.py -v
# ~50 tests, runs in ~2 seconds
```

Tests cover:
- Database operations
- MCP registration and discovery
- Routing and circuit breaker
- Billing calculations
- End-to-end integration

---

## Security Considerations

1. **API Keys:** Stored as bcrypt hashes, never plaintext
2. **SQL Injection:** Prevented with parameterized queries
3. **Input Validation:** Registry validates all inputs
4. **RLS:** Schema prepared for row-level security (policies commented)

---

## Lessons Learned

1. **SQLite/PostgreSQL compatibility** is achievable but requires careful schema design

2. **Circuit breaker in database** works well for this scale but would need distributed solution at larger scale

3. **Decimal for money** is essential - avoid float precision issues

4. **Idempotency keys** (request_id) prevent duplicate charges

---

**Agent 3 autonomous work complete. Database setup required by human (see HUMAN-TODO.md).**
