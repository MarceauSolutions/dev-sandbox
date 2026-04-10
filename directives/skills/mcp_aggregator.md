# MCP Aggregator - Platform Directive

**Project**: Universal MCP Aggregation Platform
**Code Name**: `mcp-aggregator`
**Position**: Tier 2 Aggregation Layer
**Vision**: The "Amazon for AI Agent Services"
**Status**: Active Development
**Version**: 1.0.0-dev

---

## Core Capability

**What This Platform Does**: Sits between AI agents (Claude, ChatGPT, Gemini) and service providers (Uber, Lyft, airlines, hotels), providing intelligent routing, discovery, billing, and quality control for MCP servers.

**Value Proposition**:
- **For AI Platforms**: One integration → access to 100+ MCPs across all categories
- **For MCP Developers**: Instant distribution across all AI platforms
- **For End Users**: Best service automatically selected (cheapest, fastest, most reliable)
- **For Us**: 10-20% transaction fee on every request

**Position in Ecosystem**:
```
Tier 1: AI Agents (Claude, ChatGPT) - Controls user interface
Tier 2: US (MCP Aggregator) - Controls marketplace ← WE OWN THIS
Tier 3: MCP Servers - Provide specific services
Tier 4: Services (Uber, Lyft) - Fulfillment layer
```

---

## Architecture: DOE Layers

### Layer 1: Directive (This Document)
- Platform capabilities and SOPs
- Trade secret protection guidelines
- Edge cases and error handling
- Business logic and decision rules

### Layer 2: Orchestration (Claude)
- Read this directive
- Make routing decisions
- Handle errors and edge cases
- Update this directive with learnings

### Layer 3: Execution (Code in `projects/mcp-aggregator/src/`)
- MCP Registry (`core/registry.py`)
- Routing Engine (`core/router.py`)
- Billing System (`core/billing.py`)
- Flagship MCPs (`mcps/rideshare/`)
- REST API (`api/routes.py`)

---

## Standard Operating Procedures

### SOP 1: Register New MCP (3rd Party Developer)

**Trigger**: Developer submits MCP via `POST /v1/mcps/register`

**Process**:
1. **Validation**:
   - Check required fields (name, category, endpoint, pricing, SLA)
   - Verify unique name (no duplicates)
   - Validate endpoint is reachable (health check)

2. **Automated Testing**:
   - Send 10 test requests to endpoint
   - Measure latency (must be <500ms p95)
   - Check error rate (must be <1%)
   - Verify response format matches schema

3. **Security Review**:
   - Check for SQL injection attempts
   - Verify HTTPS endpoint (not HTTP)
   - Rate limit testing (ensure they have limits)

4. **Manual Review** (if automated tests pass):
   - Code review (if source provided)
   - Quality assessment
   - Category appropriateness

5. **Approval**:
   - Status: `pending` → `active`
   - Add to registry database
   - Notify developer (email)
   - Make available for routing

6. **Monitoring**:
   - Track uptime, latency, error rate
   - Downgrade/suspend if SLA violated

**Edge Cases**:
- **Duplicate name**: Reject with suggestion to version (e.g., `FlightMCP_v2`)
- **Endpoint down**: Status = `pending`, retry health check in 1 hour
- **Poor performance**: Status = `under_review`, notify developer to optimize
- **ToS violation detected**: Immediate suspension, manual investigation

**Success Criteria**:
- 95% of submissions approved within 2-3 business days
- <1% false positives (good MCPs rejected)
- <0.1% false negatives (bad MCPs approved)

---

### SOP 2: Route User Request

**Trigger**: AI agent sends `POST /v1/route` with user query

**Process**:
1. **Parse Intent**:
   - Extract intent from natural language query
   - Examples:
     - "Book cheapest ride to airport" → `rideshare_booking`
     - "Find flights to NYC" → `flight_search`
     - "Hotel near Times Square" → `hotel_search`

2. **Find Candidate MCPs**:
   - Query registry for MCPs matching intent/category
   - Filter by status = `active`
   - Minimum: Need at least 1 MCP, ideal: 3+ for redundancy

3. **Score MCPs** (weighted algorithm):
   ```python
   score = (reliability * 0.40) +
           (latency * 0.30) +
           (cost * 0.20) +
           (user_preference * 0.10)

   where:
   - reliability = uptime_percentage / 100
   - latency = 1 - (avg_latency_ms / 1000)
   - cost = 1 - (price_per_request / max_price)
   - user_preference = historical_choice_frequency
   ```

4. **Select Best MCP**:
   - Pick highest scoring MCP
   - Keep 2nd and 3rd best for fallback

5. **Execute Request**:
   - Send request to selected MCP
   - Set timeout: 5 seconds (rideshare), 10 seconds (flights)
   - Track latency

6. **Handle Response**:
   - **Success**: Log transaction, return result to AI agent
   - **Failure**: Automatic fallback to 2nd best MCP
   - **All Fail**: Return error to AI agent with explanation

7. **Log Transaction**:
   - Save to `transactions` table
   - Track: timestamp, AI agent, MCP used, latency, success/failure
   - Calculate fees (platform margin)

**Edge Cases**:
- **No MCPs available**: Return error "Service category not yet supported"
- **All MCPs down**: Return error "Service temporarily unavailable, try again"
- **Ambiguous intent**: Ask AI agent to clarify (return multiple options)
- **MCP timeout**: Circuit breaker (after 3 failures in 1 min, stop routing to that MCP for 5 min)
- **Rate limit hit**: Return 429 error to AI agent

**Success Criteria**:
- 95%+ routing accuracy (picks best MCP)
- <200ms routing decision time (excluding MCP execution)
- <0.1% requests fail due to routing errors
- 99.9% requests handled (even if MCP fails, we respond)

---

### SOP 3: Handle MCP Failure (Circuit Breaker)

**Trigger**: MCP fails 3 times within 1 minute

**Process**:
1. **Detect Failure Pattern**:
   - Track failures per MCP (rolling 1-minute window)
   - Failure = timeout, 5xx error, or malformed response

2. **Open Circuit Breaker**:
   - Mark MCP status: `active` → `degraded`
   - Stop routing new requests to this MCP
   - Route to fallback MCPs instead

3. **Notify**:
   - Alert MCP developer (email)
   - Alert our monitoring (Slack)
   - Log incident for review

4. **Retry Logic**:
   - After 5 minutes: Send 1 health check request
   - **Success**: Status = `degraded` → `active`, resume routing
   - **Failure**: Wait another 5 minutes, retry
   - After 3 retry failures (15 min total): Status = `suspended`

5. **Suspended MCPs**:
   - Manual review required
   - Contact developer for root cause
   - Don't resume until issue confirmed fixed

6. **Recovery**:
   - Developer fixes issue
   - Submits status check request
   - We verify (10 test requests)
   - If pass: Status = `suspended` → `active`

**Edge Cases**:
- **Only 1 MCP for category**: Return error to user "Service degraded, try again later"
- **Intermittent failures**: Don't open circuit if <3 failures in 1 min
- **False positive**: Developer can appeal, we manually verify
- **Malicious actor**: Suspend permanently if ToS violation detected

**Success Criteria**:
- <5 minute recovery time (circuit auto-closes)
- 100% of incidents logged
- <1% false positives (good MCPs suspended)

---

### SOP 4: Calculate Billing (Monthly)

**Trigger**: 1st day of each month (automated cron job)

**Process**:
1. **Query Transactions**:
   - SELECT * FROM transactions WHERE created_at >= last_month
   - Group by: ai_agent_id, mcp_id

2. **Calculate MCP Developer Payouts**:
   ```python
   for each MCP:
       total_requests = count(*)
       total_revenue = sum(mcp_cost)
       our_fee = total_revenue * 0.15  # 15% platform fee
       developer_payout = total_revenue - our_fee
   ```

3. **Calculate AI Platform Invoices**:
   ```python
   for each AI agent/platform:
       total_requests = count(*)
       total_mcp_cost = sum(mcp_cost)
       platform_fee = sum(platform_fee)
       total_invoice = total_mcp_cost + platform_fee
   ```

4. **Generate Invoices**:
   - Create PDF invoices (breakdown by category)
   - Email to AI platform billing contact
   - Example format:
     ```
     Claude Desktop - January 2026
     - 10,000 rideshare requests × $0.02 = $200.00
     - 5,000 flight searches × $0.05 = $250.00
     - Platform fee (15%): $67.50
     Total: $517.50
     ```

5. **Process Payouts**:
   - Transfer funds to MCP developers (Stripe Connect or direct deposit)
   - Send payout receipts

6. **Reconciliation**:
   - Verify: (AI platform payments) - (MCP payouts) = our revenue
   - Check for discrepancies
   - Update financial dashboard

**Edge Cases**:
- **Developer payment fails**: Retry 3 times, then manual follow-up
- **AI platform disputes charge**: Provide transaction logs, work with support
- **MCP suspended mid-month**: Still pay for requests fulfilled before suspension
- **Fractional cents**: Round up to benefit developer (goodwill)

**Success Criteria**:
- 100% billing accuracy (no missed transactions)
- Invoices sent within 24 hours of month end
- Payouts processed within 7 days
- <0.1% reconciliation errors

---

### SOP 5: Update Rideshare Rate Cards (Monthly)

**Trigger**: 15th of each month (automated job)

**Process**:
1. **Scrape Rate Cards**:
   - Visit Uber.com/cities/[city] for each tracked city
   - Visit Lyft.com/pricing/[city]
   - Extract: base_fare, cost_per_mile, cost_per_minute, booking_fee, min_fare

2. **Validate Data**:
   - Check for reasonable ranges (e.g., base_fare between $1-$5)
   - Compare with previous month (alert if >20% change)
   - Verify all fields present

3. **Update Database**:
   ```sql
   UPDATE rate_cards
   SET base_fare = new_value,
       cost_per_mile = new_value,
       updated_at = NOW()
   WHERE city = 'san_francisco'
     AND service = 'uber'
     AND ride_type = 'uberx';
   ```

4. **Verify Accuracy**:
   - Generate 10 test estimates using new rates
   - Compare with actual Uber/Lyft quotes (manual check)
   - Acceptable: within ±20% of actual

5. **Deploy**:
   - If validation passes: Rates go live
   - If fails: Alert for manual review

6. **Monitor Impact**:
   - Track estimate accuracy for next 7 days
   - Watch for user feedback about incorrect prices
   - Roll back if accuracy drops below 80%

**Edge Cases**:
- **Scraping fails**: Use previous month's rates, alert for manual update
- **City rate structure changes**: Manual review required, may need code update
- **New cities added**: Research rate structure, add to database
- **Rate card not found**: Remove city from supported list temporarily

**Success Criteria**:
- 100% of cities updated monthly
- Scraping success rate: 95%+
- Estimate accuracy maintained: 85%+ within ±20%
- <24 hour rollback if issues detected

---

## Trade Secret Protection

**Critical Assets (Trade Secrets)**:

1. **Routing Algorithm**:
   - Scoring weights (40% reliability, 30% latency, etc.)
   - Fallback logic
   - Circuit breaker thresholds
   - **Protection**: Mark code as CONFIDENTIAL, obfuscate in production

2. **Rideshare Pricing Algorithm**:
   - Fare calculation formulas
   - Surge prediction model
   - City-specific adjustments
   - **Protection**: Don't publish algorithm details, NDA for team

3. **Rate Card Database**:
   - Compiled pricing data for 50+ cities
   - Update automation scripts
   - Validation rules
   - **Protection**: Database access restricted, encrypted at rest

4. **MCP Scoring Models**:
   - How we evaluate MCP quality
   - Suspension triggers
   - Quality standards
   - **Protection**: Internal documentation only

**Security Measures**:
- All production code obfuscated (minified, encrypted)
- Source code marked: `# CONFIDENTIAL - TRADE SECRET`
- Team members sign NDAs
- Need-to-know access (not all team members see all code)
- Regular security audits

---

## Edge Cases & Error Handling

### User-Facing Errors

**Scenario**: No MCPs available for requested category
- **Error**: "This service category is not yet available. Check back soon!"
- **Action**: Log request for analytics (shows demand), add to roadmap

**Scenario**: All MCPs down for category
- **Error**: "Service temporarily unavailable. Please try again in a few minutes."
- **Action**: Alert ops team, activate incident response

**Scenario**: MCP returns unexpected response format
- **Error**: "Sorry, we encountered an error. Our team has been notified."
- **Action**: Log error, fallback to backup MCP, alert developer

### Developer-Facing Errors

**Scenario**: MCP registration rejected (performance too slow)
- **Error**: "MCP rejected: Average latency 850ms exceeds limit (500ms)"
- **Action**: Provide optimization suggestions, allow resubmission

**Scenario**: MCP suspended for ToS violation
- **Error**: "MCP suspended: Detected price scraping from Uber API (violates ToS)"
- **Action**: Permanent suspension, no appeal (contractual violation)

### AI Platform Errors

**Scenario**: Rate limit exceeded
- **Error**: 429 Too Many Requests
- **Action**: Return retry-after header, suggest upgrading plan

**Scenario**: Invalid API key
- **Error**: 401 Unauthorized
- **Action**: Provide docs link for API key generation

---

## Business Rules

### Pricing

**Transaction Fees**:
- Standard: 15% of MCP request cost
- High-volume (>1M req/month): 10%
- Enterprise partners: Negotiated (minimum 5%)

**MCP Developer Fees**:
- Free tier: First 1,000 requests/month
- Standard: $99/month + 15% transaction fee
- Pro: $499/month + 10% transaction fee (priority support)

**AI Platform Fees**:
- Per-request: MCP cost + platform fee (15%)
- Monthly minimum: $1,000/month (waived for first 6 months)

### Quality Standards

**MCP Approval Criteria**:
- Uptime SLA: 99.5% minimum
- Latency: <500ms p95
- Error rate: <1%
- Security: HTTPS only, API key auth required
- Documentation: Clear API docs, response schema

**MCP Suspension Triggers**:
- Uptime < 95% for 7 consecutive days
- Error rate > 5% for 24 hours
- ToS violation detected
- Security vulnerability reported
- Developer non-responsive (3+ days)

### Data Retention

**Transaction Logs**: 2 years (compliance, auditing)
**MCP Performance Metrics**: 90 days (recent history for scoring)
**User Query Data**: 30 days (privacy, debugging)
**Financial Records**: 7 years (tax compliance)

---

## Integration Patterns

### AI Platform Integration (Claude Desktop Example)

**MCP Server Manifest** (`mcp-server.json`):
```json
{
  "name": "universal-service-aggregator",
  "version": "1.0.0",
  "tools": [
    {
      "name": "compare_rideshare_prices",
      "description": "Compare Uber and Lyft prices between two locations",
      "input_schema": {
        "type": "object",
        "properties": {
          "pickup_address": {"type": "string"},
          "dropoff_address": {"type": "string"}
        }
      }
    },
    {
      "name": "route_to_best_mcp",
      "description": "Generic routing - automatically find best MCP for any request",
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {"type": "string"},
          "category": {"type": "string"}
        }
      }
    }
  ]
}
```

**Authentication**: API keys in request headers
```
Authorization: Bearer sk_live_abc123xyz789
```

**Request Flow**:
1. User in Claude Desktop: "I need a ride to the airport"
2. Claude calls `compare_rideshare_prices` tool
3. Tool hits our API: `POST /v1/route`
4. We route to best rideshare MCP
5. Return comparison: Uber $24, Lyft $19
6. Claude presents to user
7. User books via deep link

---

## Monitoring & Alerts

### Key Metrics (Dashboard)

**Technical**:
- Request volume (requests/hour)
- Latency p50, p95, p99
- Error rate %
- MCP uptime %
- API availability (99.9% target)

**Business**:
- Revenue per day
- Active MCPs count
- Active AI platform partnerships
- MCP developer signups
- Transaction value

### Alert Thresholds

**Critical (PagerDuty)**:
- API error rate > 5% for 5 minutes
- All MCPs down for any category
- Database connection lost
- Payment processing failure

**Warning (Slack)**:
- API error rate > 1% for 15 minutes
- Latency p95 > 500ms
- MCP suspended
- Daily revenue < 50% of 7-day average

**Info (Email)**:
- New MCP registered
- Monthly billing completed
- Rate cards updated
- New AI platform partnership

---

## Learnings & Updates

**Last Updated**: 2026-01-12

**Key Learnings**:
1. (To be added as we build and deploy)

**Changelog**:
- 2026-01-12: Initial directive created following SOP 1

---

## Quick Reference

**When to Use This Directive**:
- Before implementing new features (check business rules)
- When handling errors (follow SOPs)
- When making routing decisions (use scoring algorithm)
- When updating pricing (follow trade secret protection)

**Related Documentation**:
- Implementation plan: `~/.claude/plans/universal-mcp-platform.md`
- Code: `projects/mcp-aggregator/src/`
- Workflows: `projects/mcp-aggregator/workflows/`
- Testing: `projects/mcp-aggregator/testing/`

---

**Status**: Active Development (v1.0.0-dev)
**Architecture**: DOE (Directive-Orchestration-Execution)
**Position**: Tier 2 Aggregation Layer
**Vision**: The "Amazon for AI Agent Services"
