# MCP Aggregator - Claude Skill Definition

**Skill Name**: `mcp-aggregator`
**Category**: Infrastructure / Platform
**Status**: Development
**Target Deployment**: Month 2 (production launch)

---

## Skill Purpose

Enable Claude (and other AI agents) to access 100+ service categories through a single integration point, with intelligent routing to the best MCP server based on reliability, latency, and cost.

**Position**: Tier 2 Aggregation Layer - the middleware between AI agents and service providers.

---

## Capabilities

### 1. Service Discovery & Routing

**What it does**: Automatically find and route to the best MCP for any user request

**Example Usage**:
```
User: "I need a ride to the airport"
Claude: [Uses mcp-aggregator skill]
Claude: "Lyft is cheaper at $19 (vs Uber at $24). Would you like me to open the Lyft app?"
```

**Behind the scenes**:
- Parse intent: `rideshare_booking`
- Find MCPs: RideshareComparison_v1, UberOnly_MCP, etc.
- Score MCPs: reliability (40%), latency (30%), cost (20%), user pref (10%)
- Execute on best MCP
- Return comparison + deep links

### 2. Price Comparison

**What it does**: Compare prices across competing services (Uber vs Lyft, airlines, hotels)

**Example Usage**:
```
User: "What's cheaper for getting downtown?"
Claude: [Uses rideshare comparison]
Claude: "Uber: ~$15 ($14-16 range)
        Lyft: ~$12 ($11-13 range)
        Savings: $3 with Lyft"
```

**Accuracy**: 85%+ within ±20% of actual price

### 3. Deep Link Generation

**What it does**: Open service apps with user's request pre-filled

**Example Usage**:
```
User: "Book the Lyft"
Claude: [Generates deep link]
[Opens Lyft app with pickup/dropoff already entered]
```

**Legal Status**: ✅ Explicitly allowed by Uber/Lyft (affiliate programs)

### 4. Multi-Category Support

**Available Categories** (Phase 1):
- Rideshare (Uber, Lyft)
- *Flights (coming Month 3)*
- *Hotels (coming Month 3)*
- *Food delivery (coming Month 4)*
- *Restaurants (coming Month 4)*

**Future Expansion**: 100+ categories via 3rd party MCP developers

---

## Tools Provided

### Tool 1: `compare_rideshare_prices`

**Description**: Compare Uber and Lyft prices between two locations

**Input**:
```json
{
  "pickup_address": "Union Square, San Francisco",
  "dropoff_address": "SFO Airport"
}
```

**Output**:
```json
{
  "uber": {
    "estimate": "$24",
    "range": "$22-26",
    "deep_link": "uber://?action=setPickup&..."
  },
  "lyft": {
    "estimate": "$19",
    "range": "$17-21",
    "deep_link": "lyft://ridetype?id=lyft&..."
  },
  "recommendation": "lyft",
  "savings": "$5",
  "confidence": "85%"
}
```

### Tool 2: `route_to_best_mcp`

**Description**: Generic routing - find best MCP for any request (future expansion)

**Input**:
```json
{
  "query": "Find flights to NYC",
  "category": "travel",
  "optimize_for": "price"  // or "speed", "reliability"
}
```

**Output**:
```json
{
  "intent": "flight_search",
  "mcp_used": "FlightComparison_v1",
  "result": { /* flight results */ },
  "latency_ms": 245
}
```

### Tool 3: `open_service_app`

**Description**: Generate deep link to open service app

**Input**:
```json
{
  "service": "lyft",
  "action": "book_ride",
  "params": {
    "pickup_lat": 37.7749,
    "pickup_lng": -122.4194,
    "dropoff_lat": 37.6213,
    "dropoff_lng": -122.3790
  }
}
```

**Output**:
```json
{
  "deep_link": "lyft://ridetype?id=lyft&pickup[latitude]=37.7749&...",
  "fallback_url": "https://lyft.com/ride?pickup=...",
  "instructions": "Opens Lyft app on mobile, or Lyft website on desktop"
}
```

---

## Integration Guide

### For Claude Desktop

**Installation**:
1. Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "mcp-aggregator": {
      "command": "node",
      "args": ["/path/to/mcp-aggregator/dist/index.js"],
      "env": {
        "API_KEY": "your_api_key_here"
      }
    }
  }
}
```

2. Restart Claude Desktop

3. Test:
```
User: "Compare Uber and Lyft from my home to the office"
```

### For Other AI Platforms (ChatGPT, Gemini)

**REST API Integration**:
```bash
curl -X POST https://api.mcp-aggregator.com/v1/route \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Book cheapest ride to airport",
    "context": {
      "user_id": "user_123",
      "optimize_for": "price"
    }
  }'
```

**Response**:
```json
{
  "intent": "rideshare_booking",
  "mcp_used": "RideshareComparison_v1",
  "result": {
    "uber": {"estimate": "$24", ...},
    "lyft": {"estimate": "$19", ...},
    "recommendation": "lyft"
  },
  "latency_ms": 145
}
```

---

## Performance

**Latency**:
- Routing decision: <50ms
- Rideshare comparison: <200ms total (including MCP execution)
- Deep link generation: <10ms

**Accuracy**:
- Rideshare estimates: 85%+ within ±20% of actual price
- Routing selection: 95%+ picks best MCP

**Uptime**: 99.9% target (AWS multi-region deployment)

---

## Pricing

### For AI Platforms
- Per-request fee: MCP cost + 15% platform fee
- Example: Rideshare comparison ($0.02) + platform fee ($0.003) = $0.023 per request
- Monthly minimum: $1,000/month (waived for first 6 months)

### For End Users
- Free (cost passed through AI platform subscription)

---

## Roadmap

**Phase 1** (Month 1-2): Rideshare comparison only
**Phase 2** (Month 3-6): 10+ categories (flights, hotels, food, etc.)
**Phase 3** (Month 7-12): 100+ categories via marketplace

---

## Security & Privacy

**Data Collection** (Minimal):
- Query intent (for routing)
- Transaction metadata (for billing)
- Performance metrics (for quality control)

**NOT Collected**:
- User identity (anonymized)
- Exact locations (hashed after routing)
- Personal information

**Compliance**:
- GDPR compliant (EU data residency)
- CCPA compliant (California privacy rights)
- SOC 2 Type II (in progress)

---

## Support

**Documentation**: https://docs.mcp-aggregator.com (coming soon)
**API Reference**: https://api.mcp-aggregator.com/docs (coming soon)
**Developer Portal**: https://developers.mcp-aggregator.com (coming soon)

**Issues**:
- Technical issues: support@mcp-aggregator.com
- MCP developer questions: developers@mcp-aggregator.com
- Partnership inquiries: partnerships@mcp-aggregator.com

---

## Legal

**Terms of Service**: https://mcp-aggregator.com/terms (coming soon)
**Privacy Policy**: https://mcp-aggregator.com/privacy (coming soon)
**Developer Agreement**: https://developers.mcp-aggregator.com/terms (coming soon)

**Trade Secrets**: Routing algorithm, pricing formulas, surge prediction model
**Copyright**: © 2026 MCP Aggregator, Inc.

---

**Status**: Active Development (v1.0.0-dev)
**Target Launch**: Month 2 (break-even goal)
**Position**: Tier 2 Aggregation Layer
**Vision**: The "Amazon for AI Agent Services"
