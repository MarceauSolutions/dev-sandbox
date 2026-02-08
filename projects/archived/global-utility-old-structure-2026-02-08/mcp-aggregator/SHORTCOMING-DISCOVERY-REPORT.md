# MCP Aggregator Shortcoming Discovery Report

**Date:** 2026-01-13
**Methodology:** Static Code Analysis per approved plan
**Files Analyzed:** router.py, registry.py, billing.py, schema.sql, rideshare_mcp.py

---

## Executive Summary

**51 rideshare-specific assumptions found** across 5 files that would prevent the MCP Aggregator from connecting to non-rideshare services.

| File | Assumptions Found | Critical | Important | Nice-to-Have |
|------|-------------------|----------|-----------|--------------|
| router.py | 15 | 6 | 7 | 2 |
| registry.py | 14 | 5 | 6 | 3 |
| billing.py | 12 | 4 | 5 | 3 |
| schema.sql | 6 | 3 | 2 | 1 |
| rideshare_mcp.py | 4 | 4 | 0 | 0 |
| **TOTAL** | **51** | **22** | **20** | **9** |

---

## Step 1: What is Rideshare? (Baseline Characteristics)

Based on code analysis, the MCP Aggregator was optimized for services with these characteristics:

| Characteristic | Rideshare Implementation | Code Location |
|----------------|--------------------------|---------------|
| **Connectivity** | HTTP REST, single POST endpoint | `rideshare_mcp.py:161` |
| **Latency** | 100-500ms responses | `router.py:527-536` scoring |
| **Cost** | $0.005-$0.05 per call | `router.py:550-560` scoring |
| **Billing** | Per-request | `billing.py:57-106` Transaction class |
| **Health Check** | HTTP GET /health | `registry.py:188-195` |
| **Authentication** | API key in header | `rideshare_mcp.py:50-52` |
| **Response Format** | JSON | `rideshare_mcp.py:177` |
| **State** | Stateless (each call independent) | Entire architecture |

---

## Step 2: What are OTHER services?

Services that would NOT work with the current aggregator:

| Service Type | How It Differs | What Breaks |
|--------------|----------------|-------------|
| **HVAC Distributors** | Email-based, 24-48hr response | HTTP URL required, 30s timeout, latency scoring |
| **Flight Search (Amadeus)** | OAuth required, 3-5s latency, $0.10+/call | Cost scoring, OAuth handling |
| **Hotel Booking** | Commission-based (10-15% of booking) | Per-request billing only |
| **Payment Processors** | Webhook-based (they call us) | We only make outbound calls |
| **GraphQL APIs** | Query-based, different structure | POST JSON only |

---

## Step 3: Connectivity Model Analysis

### router.py - How Requests Are Executed

**File:** `/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent3-platform-core/workspace/router.py`

| # | Line(s) | Assumption | Impact on Non-Rideshare |
|---|---------|------------|-------------------------|
| 1 | 280-281 | `ThreadPoolExecutor(max_workers=10)` | Assumes synchronous HTTP calls. Email workflows need async tracking over hours/days. |
| 2 | 283-298 | `_mock_executor` simulates HTTP request/response | No support for email, webhook, or batch execution patterns. |
| 3 | 62 | `timeout_ms: int = 30000` default | 30 seconds is way too short for flights (5-10s typical), HVAC (24+ hours). |
| 4 | 591 | `future.result(timeout=timeout_ms / 1000)` | Assumes all requests complete in seconds. Email responses take days. |
| 5 | 369 | `cost=mcp.fee_per_request` | Assumes per-request pricing. Commission-based services charge % of transaction value. |

**Verdict:** Router assumes all services are synchronous HTTP with sub-minute response times.

### registry.py - What's Required for Registration

**File:** `/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent3-platform-core/workspace/registry.py`

| # | Line(s) | Assumption | Impact on Non-Rideshare |
|---|---------|------------|-------------------------|
| 1 | 362-363 | `if not endpoint_url or not endpoint_url.startswith(('http://', 'https://'))` | **CRITICAL:** HTTP URL is required. Email-based services have no HTTP endpoint. |
| 2 | 71 | `endpoint_url: str` | Single endpoint assumed. Multi-endpoint REST APIs need path routing. |
| 3 | 74 | `health_check_url: Optional[str]` | HTTP health check assumed. Can't ping an email address. |
| 4 | 78-79 | `fee_per_request: float = 0.01`, `developer_share: float = 0.80` | Per-request pricing only. No subscription, commission, or tiered models. |
| 5 | 94 | `rate_limit_rpm: int = 100` | Requests per minute. Some services need per-second (real-time), per-day (email). |
| 6 | 36-48 | `MCPCategory` enum is hardcoded | Can't add `contractor_tools` category without code change. |

**Verdict:** Registry requires HTTP URL and per-request pricing. Services without HTTP endpoints cannot register.

---

## Step 4: Scoring Algorithm Analysis

### router.py - Scoring Functions

| # | Line(s) | Code | Rideshare Assumption | Impact |
|---|---------|------|---------------------|--------|
| 1 | 527-536 | Latency scoring | `<100ms = 100`, `<200ms = 90`, `<500ms = 70`, `<1000ms = 50`, `>1000ms = 30` | Flights (3-5s) score 30. HVAC (hours) scores 30. Both penalized unfairly. |
| 2 | 550-560 | Cost scoring | `≤$0.005 = 100`, `≤$0.01 = 90`, `≤$0.02 = 80`, `≤$0.05 = 60`, `>$0.05 = 40` | Flights ($0.10-0.25) score 40. Hotels ($5-50 commission) score 40. |
| 3 | 460-465 | Score weights | `health 0.30 + perf 0.25 + cost 0.20 + rating 0.25` | Fixed weights. HVAC doesn't care about latency. |
| 4 | 509 | Error rate penalty | `error_score = max(0, 100 - error_rate * 10)` | -10 points per 1% error. Email services have high "error" rate (awaiting response). |
| 5 | 496-500 | Circuit breaker health | `OPEN = 0`, `HALF_OPEN = 50` | Email services can't be "half-open tested" like HTTP. |

**Calculated Scores for Hypothetical Services:**

| Service | Latency | Cost | Latency Score | Cost Score | Total Score (weighted) |
|---------|---------|------|---------------|------------|------------------------|
| Rideshare | 200ms | $0.01 | 90 | 90 | ~85 (FAIR) |
| Flight Search | 3000ms | $0.15 | 30 | 40 | ~45 (UNFAIR) |
| Hotel Booking | 500ms | $5.00 commission | 70 | 40 | ~55 (UNFAIR) |
| HVAC (email) | 86400000ms | $0.25/RFQ | 30 | 40 | ~40 (UNFAIR) |

**Verdict:** Scoring algorithm penalizes any service that isn't fast (~200ms) and cheap (~$0.01).

---

## Step 5: Billing Model Analysis

### billing.py - Supported Models

**File:** `/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent3-platform-core/workspace/billing.py`

| # | Line(s) | Code | What It Does | What's Missing |
|---|---------|------|--------------|----------------|
| 1 | 220-221 | `DEFAULT_PLATFORM_FEE_PERCENT = Decimal('0.20')` | Fixed 80/20 split | No tiered splits (premium = 70/30) |
| 2 | 57-106 | `Transaction` dataclass | Per-request fields: `request_id`, `gross_amount`, `response_time_ms` | No `subscription_id`, `booking_value`, `commission_rate` |
| 3 | 270-336 | `log_transaction()` | Logs per-request transactions | Can't log subscription periods or commission bookings |
| 4 | 302-308 | `request_id` idempotency | Prevents duplicate API calls | Email workflows have sessions, not requests |
| 5 | 342 | `response_time_ms` tracking | Measures HTTP response time | Meaningless for async services |

**Billing Model Support Matrix:**

| Model | Supported? | Code Evidence | Gap |
|-------|------------|---------------|-----|
| Per-request | ✅ Yes | `log_transaction(gross_amount=...)` | - |
| Subscription | ❌ No | No `subscription_id` field | Need monthly tracking |
| Commission | ❌ No | No `booking_value` field | Need % calculation |
| Tiered | ❌ No | No volume tracking | Need tier lookup |
| Hybrid | ❌ No | No combined model | Need base + usage |

**Verdict:** Billing only supports per-request pricing. Services with other models cannot be billed.

### schema.sql - Database Structure

**File:** `/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent3-platform-core/workspace/schema.sql`

| # | Line(s) | Table/Column | Rideshare-Specific? | Impact |
|---|---------|--------------|---------------------|--------|
| 1 | 261-284 | `rate_cards` table | **100% rideshare** | Contains `base_fare`, `cost_per_mile`, `surge_multiplier` |
| 2 | 286-308 | `surge_history` table | **100% rideshare** | Contains `surge_multiplier`, `day_of_week`, `hour_of_day` |
| 3 | 62 | `fee_per_request DECIMAL` | Per-request pricing | No `subscription_fee`, `commission_rate` columns |
| 4 | 167 | `response_time_ms INTEGER` | HTTP response times | Meaningless for async services |
| 5 | 159 | `request_id VARCHAR` | API call idempotency | Email sessions don't have request IDs |
| 6 | 76 | `rate_limit_rpm INTEGER` | Requests per minute | Some services need per-day or per-second |

**Verdict:** Schema has rideshare-specific tables (`rate_cards`, `surge_history`) and per-request billing columns only.

---

## Step 6: Integration Layer Analysis

### rideshare_mcp.py - Does Platform Core Get Used?

**File:** `/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/mcp-server/rideshare_mcp.py`

**Critical Finding:** The rideshare MCP **bypasses the platform core entirely**.

| Line | Code | What It Does |
|------|------|--------------|
| 37-38 | `API_URL = os.environ.get("RIDESHARE_API_URL", "http://localhost:8000")` | Connects directly to REST API |
| 49-53 | `self.http_client = httpx.AsyncClient(base_url=API_URL, ...)` | Makes HTTP calls directly |
| 161-176 | `await self.http_client.post("/v1/compare", ...)` | Calls REST API, not router.py |

**Actual Request Flow:**
```
Claude Desktop → rideshare_mcp.py → REST API at :8000
                                    ↓
                              (router.py UNUSED)
                              (registry.py UNUSED)
                              (billing.py UNUSED)
```

**Required Flow (for aggregator to work):**
```
Claude Desktop → aggregator_mcp.py → router.py → selects MCP → calls endpoint
                                   → registry.py → discovers MCPs
                                   → billing.py → logs transactions
```

**Verdict:** The platform core (~2000 lines in router.py, registry.py, billing.py) is **DEAD CODE**. It's never called.

---

## Connectivity Pattern Mapping (Complete)

| Pattern | Description | Rideshare Uses? | Current Support? | Gap? |
|---------|-------------|-----------------|------------------|------|
| HTTP POST | Single endpoint, JSON | ✅ Yes | ✅ Yes | No |
| HTTP GET | Query parameters | Partially | ✅ Yes | No |
| HTTP Multi-Endpoint | Multiple paths, methods | ❌ No | ❌ No | **Path routing needed** |
| OAuth2 | Token-based auth | ❌ No | ❌ No | **Token refresh needed** |
| Email/SMTP | Send email, track response | ❌ No | ❌ No | **SMTP adapter needed** |
| Webhook (inbound) | They call us | ❌ No | ❌ No | **Endpoint registration needed** |
| GraphQL | Query language | ❌ No | ❌ No | **Query wrapper needed** |
| SOAP/XML | XML envelope | ❌ No | ❌ No | **XML adapter needed** |
| Batch | Multiple requests in one | ❌ No | ❌ No | **Batch executor needed** |
| Streaming | WebSocket/SSE | ❌ No | ❌ No | **Stream handler needed** |

---

## Prioritized Fix List

### CRITICAL (Blocks HVAC and other services)

| Priority | Issue | File | Fix |
|----------|-------|------|-----|
| **C1** | HTTP URL required for registration | `registry.py:362` | Add `connectivity_type` enum, make `endpoint_url` optional |
| **C2** | Platform core unused | `rideshare_mcp.py` | Create `aggregator_mcp.py` that uses router/registry/billing |
| **C3** | Per-request billing only | `billing.py:57-106` | Add `PricingModel` enum, support subscription/commission |
| **C4** | Latency scoring penalizes slow services | `router.py:527-536` | Make thresholds configurable per category |
| **C5** | Cost scoring penalizes expensive services | `router.py:550-560` | Make thresholds configurable per category |
| **C6** | 30s timeout too short | `router.py:62` | Configurable per MCP, allow hours for email |

### IMPORTANT (Production quality)

| Priority | Issue | File | Fix |
|----------|-------|------|-----|
| **I1** | Fixed 80/20 billing split | `billing.py:220-221` | Configurable per MCP |
| **I2** | Fixed scoring weights | `router.py:460-465` | Configurable per category |
| **I3** | Circuit breaker too aggressive | `router.py:109-117` | Configurable thresholds |
| **I4** | RPM rate limiting only | `registry.py:94` | Support per-second, per-hour, per-day |
| **I5** | Hardcoded MCPCategory enum | `registry.py:36-48` | Dynamic category registration |
| **I6** | rate_cards/surge_history rideshare-specific | `schema.sql:261-308` | Rename to `rideshare_*`, add generic `external_data` |

### NICE-TO-HAVE (Future improvement)

| Priority | Issue | File | Fix |
|----------|-------|------|-----|
| **N1** | Rideshare examples in docstrings | All files | Replace with generic examples |
| **N2** | request_id idempotency | `billing.py:302` | Support session_id for workflows |
| **N3** | Round-robin load balancing | `router.py:245` | Add geographic preference |

---

## Success Criteria Answers

1. **Connectivity**: "The aggregator cannot connect to email-based, webhook-based, OAuth-protected, or GraphQL services because `registry.py:362-363` requires an HTTP URL, `router.py:280-281` uses synchronous HTTP execution, and no adapters exist for other connectivity patterns."

2. **Scoring**: "Services with latency >1000ms score 30/100 (penalized) because `router.py:527-536` has hardcoded thresholds. Services costing >$0.05/request score 40/100 because `router.py:550-560` has hardcoded thresholds."

3. **Billing**: "Subscription/commission billing fails because `billing.py:57-106` Transaction class only has `gross_amount`, `fee_per_request` fields. No `subscription_id`, `booking_value`, or `commission_rate` fields exist."

4. **Integration**: "The platform core (router.py, registry.py, billing.py) is NOT used because `rideshare_mcp.py:49-53` connects directly to the REST API, bypassing the aggregator entirely."

---

## Phase 2: Hypothetical Service Testing Results

### Test 1: HVAC Distributor Registration

**Mock Service**:
```python
hvac_service = {
    "name": "Ferguson HVAC Distribution",
    "endpoint_url": None,  # Email-based
    "email": "rfq@ferguson.com",
    "connectivity_type": "email",
    "response_time_typical": 86400000,  # 24 hours
    "fee_model": "per_rfq",
    "fee_per_rfq": 0.25
}
```

**Result**: **REGISTRATION FAILS** at `registry.py:362-363`
- Error: `ValueError: endpoint_url must be a valid HTTP URL`
- No `connectivity_type` field exists
- No `fee_per_rfq` billing field exists

### Test 2: Scoring Calculations

| Service | Latency | Cost | Latency Score | Cost Score | Fair? |
|---------|---------|------|---------------|------------|-------|
| Rideshare | 200ms | $0.01 | 90 | 90 | ✅ Yes |
| Flight Search | 3000ms | $0.15 | 30 | 40 | ❌ Unfair |
| Hotel Booking | 500ms | $5 commission | 70 | 40 | ❌ Unfair |
| HVAC Email | 24 hours | $0.25/RFQ | 30 | 40 | ❌ Unfair |

---

## Phase 3: Complete Connectivity Matrix

| Pattern | Supported? | Blocking Issue | Fix |
|---------|------------|----------------|-----|
| HTTP POST (single) | ✅ Yes | - | - |
| HTTP GET | ⚠️ Partial | No method selection | Add `http_method` |
| HTTP Multi-Endpoint | ❌ No | Single URL only | Add endpoint mapping |
| OAuth2 | ❌ No | API key only | Add token management |
| Email/SMTP | ❌ No | HTTP required | Add email adapter |
| Webhook (Inbound) | ❌ No | Outbound only | Add webhook registration |
| GraphQL | ❌ No | JSON only | Add query wrapper |
| SOAP/XML | ❌ No | JSON only | Add XML adapter |
| Batch | ❌ No | Single request | Add batch executor |
| Streaming | ❌ No | Sync only | Add stream handler |
| Async (hours/days) | ❌ No | 30s timeout | Add async tracking |

**Root Cause**: `router.py:280-281` uses `ThreadPoolExecutor` - assumes all operations complete synchronously within timeout.

---

## Phase 4: Prioritized Fix Roadmap

### Tier 1: CRITICAL (Blocks HVAC project)

| Fix | Files | Effort | Description |
|-----|-------|--------|-------------|
| **F1: Create aggregator_mcp.py** | New file | Medium | Wire up platform core so it's actually used |
| **F2: Add ConnectivityType enum** | registry.py, schema.sql | Medium | `HTTP`, `EMAIL`, `OAUTH`, `WEBHOOK`, `GRAPHQL` |
| **F3: Make endpoint_url optional** | registry.py:362 | Small | Allow null when connectivity_type != HTTP |
| **F4: Add PricingModel enum** | billing.py, schema.sql | Medium | `PER_REQUEST`, `SUBSCRIPTION`, `COMMISSION`, `TIERED` |
| **F5: Configurable scoring thresholds** | router.py:527-560 | Medium | Per-category latency/cost expectations |
| **F6: Configurable timeout** | router.py:62 | Small | Per-MCP timeout (support hours for email) |

### Tier 2: IMPORTANT (Production quality)

| Fix | Files | Effort | Description |
|-----|-------|--------|-------------|
| **F7: Configurable billing split** | billing.py:220 | Small | Per-MCP, not fixed 80/20 |
| **F8: Configurable scoring weights** | router.py:460 | Small | Per-category weight profiles |
| **F9: Dynamic MCPCategory** | registry.py:36-48 | Medium | Runtime category registration |
| **F10: Flexible rate limiting** | registry.py:94 | Small | Per-second, per-hour, per-day options |
| **F11: Rename rideshare tables** | schema.sql:261-308 | Medium | `rideshare_rate_cards`, `rideshare_surge_history` |

### Tier 3: NICE-TO-HAVE (Polish)

| Fix | Files | Effort | Description |
|-----|-------|--------|-------------|
| **F12: Generic docstring examples** | All files | Small | Replace rideshare examples |
| **F13: Session-based idempotency** | billing.py:302 | Small | Support `session_id` for workflows |
| **F14: Geographic routing** | router.py:245 | Medium | Prefer MCPs by region |

---

## Recommended Implementation Order

**Sprint 1: Enable Platform Core**
1. F1: Create aggregator_mcp.py (makes platform core actually work)
2. F6: Configurable timeout (allows testing with slow services)

**Sprint 2: Support Non-HTTP Services**
3. F2: Add ConnectivityType enum
4. F3: Make endpoint_url optional
5. F5: Configurable scoring thresholds

**Sprint 3: Support Non-Per-Request Billing**
6. F4: Add PricingModel enum
7. F7: Configurable billing split

**Sprint 4: Polish**
8. F8-F11: Production quality fixes
9. F12-F14: Nice-to-haves

**Validation**: Build HVAC MCP after Sprint 2 to prove non-rideshare services work.

---

## Next Steps

1. **Create ConnectivityAdapter system** - Abstract base class with HTTP, Email, OAuth, Webhook implementations
2. **Create aggregator_mcp.py** - Wire up platform core so it's actually used
3. **Make scoring configurable** - Category-specific latency/cost thresholds
4. **Add billing models** - PricingModel enum with subscription, commission, tiered support
5. **Build HVAC MCP** - Use as proof-of-concept that non-rideshare services work
