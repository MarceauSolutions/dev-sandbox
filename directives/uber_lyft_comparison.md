# Uber/Lyft Price Comparison Directive

## Purpose

Real-time rideshare price comparison service using proprietary rate card algorithm. Provides accurate price estimates for Uber and Lyft services without relying on unofficial API access or web scraping.

## Core Capabilities

### SOP 1: Price Comparison

**When**: User wants to compare Uber and Lyft prices for a route

**Steps**:
1. Parse origin and destination from user input
2. Geocode addresses to coordinates (using Google Maps API)
3. Calculate distance and estimated duration
4. Look up rate cards for the region
5. Apply rate card formulas to calculate prices
6. Return comparison with deep links

**Input**: Origin address, destination address, optional service type filter

**Output**: Price estimates for all available services, sorted by price

### SOP 2: Rate Card Data Collection

**When**: Adding support for a new region or updating existing rates

**Steps**:
1. Research current Uber/Lyft rates for the region
2. Create CSV file in `data/` directory following format:
   ```csv
   service_type,base_fare,per_mile,per_minute,minimum,booking_fee,region
   UberX,2.50,1.25,0.20,7.00,2.50,Naples FL
   ```
3. Add region to rate_cards.py SUPPORTED_REGIONS
4. Run accuracy tests against live prices
5. Adjust rates if accuracy <85%

**Data Sources**:
- Uber Rate Card page (official)
- Lyft Rate Card page (official)
- Manual trip booking (verify with real quotes)

### SOP 3: Accuracy Validation

**When**: After rate card updates or periodically (weekly)

**Steps**:
1. Load test routes from `data/test-routes.csv`
2. For each route:
   - Get our estimate using rate card
   - Compare against live Uber/Lyft prices (manual check)
   - Record deviation percentage
3. Flag any routes with >15% deviation
4. Update rate cards if systematic errors found

**Accuracy Target**: 85% of estimates within 15% of actual price

### SOP 4: Deep Link Generation

**When**: User wants to book a ride

**Steps**:
1. Determine provider (Uber or Lyft)
2. Generate universal deep link:
   - Uber: `uber://?action=setPickup&pickup=...&dropoff=...`
   - Lyft: `lyft://ridetype?id=...&pickup=...&destination=...`
3. Include web fallback URL
4. Track affiliate referral code

## Technical Implementation

### Rate Card Formula

```python
def calculate_price(distance_miles, duration_minutes, rate_card):
    base = rate_card.base_fare
    distance_cost = distance_miles * rate_card.per_mile
    time_cost = duration_minutes * rate_card.per_minute
    subtotal = base + distance_cost + time_cost

    # Apply minimum fare
    fare = max(subtotal, rate_card.minimum)

    # Add booking fee
    total = fare + rate_card.booking_fee

    return total
```

### Surge Handling

Surge multipliers are NOT currently supported. Rate cards reflect base rates only.

**Future Enhancement**: Track historical surge patterns and provide:
- "Usually X% surge at this time"
- "No surge right now - book now to save"

### Service Type Mapping

| Our Name | Uber | Lyft |
|----------|------|------|
| Economy | UberX | Lyft |
| Premium | UberXL | Lyft XL |
| Black | UberBlack | Lyft Lux |
| Shared | UberPool | Lyft Shared |

## Integration

### MCP Aggregator Connection

This service registers with the MCP Aggregator platform:

```python
await platform.register(
    name="rideshare-comparison",
    endpoint="http://rideshare:8001",
    category="TRANSPORTATION",
    connectivity="HTTP",
    capabilities=["price_comparison", "booking"]
)
```

### Revenue Model

- **Affiliate Commission**: 2-5% per completed booking through deep link
- **Platform Fee**: 15% to MCP Aggregator for routing

## Data Files

| File | Purpose |
|------|---------|
| `data/uber-rates-naples.csv` | Uber rate cards for Naples, FL |
| `data/lyft-rates-naples.csv` | Lyft rate cards for Naples, FL |
| `data/test-routes.csv` | Validation routes for accuracy |
| `data/surge-history.csv` | Historical surge patterns (future) |

## Error Handling

| Error | Response |
|-------|----------|
| Unknown region | "Rate cards not available for this region. Supported: Naples, FL" |
| Geocoding failed | "Could not find location. Please provide a more specific address." |
| Rate card missing | Fall back to estimated regional average |

## Testing

Run accuracy tests:
```bash
cd projects/uber-lyft-comparison
python -m pytest src/test_comparison.py -v
```

Run MCP server locally:
```bash
cd projects/uber-lyft-comparison/mcp-server
python rideshare_mcp.py
```

## Registry Information

- **Namespace**: `io.github.williammarceaujr/rideshare-comparison`
- **Registry**: https://registry.modelcontextprotocol.io/
- **Category**: Transportation
- **Status**: In Development

## Related Documentation

- [MCP Aggregator Platform](../projects/mcp-aggregator/README.md)
- [Rate Card Data Format](../projects/uber-lyft-comparison/data/README.md)
- [Accuracy Testing Guide](../projects/uber-lyft-comparison/testing/accuracy/README.md)
