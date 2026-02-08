# MCP Aggregator API Documentation

**Version:** 1.0.0
**Base URL:** `https://api.mcp-aggregator.com` (production) or `http://localhost:8000` (development)

---

## Overview

The MCP Aggregator API provides rideshare price comparison services for AI agents and applications. Compare Uber and Lyft prices instantly with a single API call.

### Key Features

- **Price Comparison**: Get real-time estimates for Uber and Lyft
- **Deep Links**: Generate booking links that open Uber/Lyft apps
- **City Support**: 10 major US cities supported
- **Rate Limiting**: Tiered API access with configurable limits
- **High Availability**: 99.9% uptime SLA (production)

---

## Authentication

All API requests (except `/health`) require an API key in the header.

```bash
X-API-Key: your_api_key_here
```

### API Key Tiers

| Tier | Requests/Minute | Requests/Day | Price |
|------|-----------------|--------------|-------|
| Free | 10 | 100 | $0 |
| Basic | 60 | 1,000 | $29/mo |
| Pro | 300 | 10,000 | $99/mo |
| Enterprise | 1,000 | 100,000 | Custom |

### Test API Keys (Development)

```
Free:       test_free_key_12345
Basic:      test_basic_key_67890
Pro:        test_pro_key_11111
Enterprise: test_enterprise_key_22222
```

---

## Endpoints

### Health Check

Check if the API is operational.

```
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-12T20:00:00Z",
  "uptime_seconds": 3600,
  "services": {
    "rate_cards": "healthy",
    "comparator": "healthy"
  }
}
```

---

### Compare Prices

**Main endpoint** - Compare Uber and Lyft prices for a route.

```
POST /v1/compare
```

**Request Body:**

```json
{
  "pickup": {
    "latitude": 37.7879,
    "longitude": -122.4074,
    "address": "Union Square, San Francisco"
  },
  "dropoff": {
    "latitude": 37.6213,
    "longitude": -122.3790,
    "address": "SFO Airport"
  },
  "city": "san_francisco"  // optional, auto-detected
}
```

**Response:**

```json
{
  "request_id": "abc123",
  "timestamp": "2026-01-12T20:00:00Z",
  "city": "san_francisco",
  "distance_miles": 13.2,
  "duration_minutes": 25,
  "uber": {
    "service": "uber",
    "ride_type": "uberx",
    "estimate": 32.50,
    "low_estimate": 29.25,
    "high_estimate": 35.75,
    "surge_multiplier": 1.0,
    "distance_miles": 13.2,
    "duration_minutes": 25,
    "confidence": 0.85,
    "deep_link": "uber://?action=setPickup&...",
    "web_link": "https://m.uber.com/ul/?..."
  },
  "lyft": {
    "service": "lyft",
    "ride_type": "lyft",
    "estimate": 29.25,
    "low_estimate": 26.33,
    "high_estimate": 32.18,
    "surge_multiplier": 1.0,
    "distance_miles": 13.2,
    "duration_minutes": 25,
    "confidence": 0.85,
    "deep_link": "lyft://ridetype?id=lyft&...",
    "web_link": "https://lyft.com/ride?..."
  },
  "recommendation": "lyft",
  "savings": 3.25,
  "savings_percent": 10.0,
  "confidence": 0.85,
  "disclaimer": "Estimates based on rate cards. Actual prices may vary."
}
```

**cURL Example:**

```bash
curl -X POST "http://localhost:8000/v1/compare" \
  -H "X-API-Key: test_free_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup": {"latitude": 37.7879, "longitude": -122.4074},
    "dropoff": {"latitude": 37.6213, "longitude": -122.3790}
  }'
```

---

### List Supported Cities

Get all cities where rideshare comparison is available.

```
GET /v1/cities
```

**Response:**

```json
{
  "cities": [
    "san_francisco",
    "new_york",
    "los_angeles",
    "chicago",
    "boston",
    "seattle",
    "austin",
    "miami",
    "denver",
    "washington_dc"
  ],
  "count": 10
}
```

---

### Get City Rate Cards

Get pricing information for a specific city.

```
GET /v1/cities/{city}/rates
```

**Example:** `GET /v1/cities/san_francisco/rates`

**Response:**

```json
{
  "city": "san_francisco",
  "services": {
    "uber": {
      "uberx": {
        "base_fare": 2.55,
        "cost_per_mile": 1.75,
        "cost_per_minute": 0.30,
        "booking_fee": 2.70,
        "min_fare": 7.65
      },
      "uber_xl": {
        "base_fare": 4.50,
        "cost_per_mile": 2.85,
        "cost_per_minute": 0.50,
        "booking_fee": 3.00,
        "min_fare": 10.00
      }
    },
    "lyft": {
      "lyft": {
        "base_fare": 2.00,
        "cost_per_mile": 1.50,
        "cost_per_minute": 0.35,
        "booking_fee": 2.70,
        "min_fare": 6.00
      }
    }
  },
  "last_updated": "2026-01-12T10:00:00Z"
}
```

---

### Generate Deep Link

Generate a URL that opens Uber or Lyft app with route pre-filled.

```
GET /v1/deeplink/{service}?pickup_lat=...&pickup_lng=...&dropoff_lat=...&dropoff_lng=...
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| service | string | Yes | `uber` or `lyft` |
| pickup_lat | float | Yes | Pickup latitude |
| pickup_lng | float | Yes | Pickup longitude |
| dropoff_lat | float | Yes | Dropoff latitude |
| dropoff_lng | float | Yes | Dropoff longitude |
| mobile | bool | No | Return mobile-optimized link (default: true) |

**Response:**

```json
{
  "service": "uber",
  "app_link": "uber://?action=setPickup&pickup[latitude]=37.7879&...",
  "web_link": "https://m.uber.com/ul/?action=setPickup&...",
  "primary": "uber://?action=setPickup&..."
}
```

---

### API Statistics

Get API usage statistics (requires authentication).

```
GET /stats
```

**Response:**

```json
{
  "total_requests": 15234,
  "requests_today": 423,
  "avg_response_time_ms": 45.2,
  "cache_hit_rate": 0.75,
  "supported_cities": 10,
  "rate_cards_loaded": 20
}
```

---

## Response Headers

All responses include these headers:

| Header | Description |
|--------|-------------|
| `X-Request-ID` | Unique request identifier |
| `X-Response-Time-Ms` | Response time in milliseconds |
| `X-RateLimit-Limit-Minute` | Requests allowed per minute |
| `X-RateLimit-Remaining-Minute` | Requests remaining this minute |
| `X-RateLimit-Limit-Day` | Requests allowed per day |
| `X-RateLimit-Remaining-Day` | Requests remaining today |

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "field": "field_name"  // optional, for validation errors
  },
  "request_id": "abc123",
  "timestamp": "2026-01-12T20:00:00Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_API_KEY` | 401 | Missing or invalid API key |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INVALID_LOCATION` | 400 | Invalid coordinates |
| `UNSUPPORTED_CITY` | 400 | City not in supported list |
| `VALIDATION_ERROR` | 422 | Request body validation failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Code Examples

### Python

```python
import requests

API_KEY = "your_api_key"
BASE_URL = "http://localhost:8000"

# Compare prices
response = requests.post(
    f"{BASE_URL}/v1/compare",
    headers={"X-API-Key": API_KEY},
    json={
        "pickup": {"latitude": 37.7879, "longitude": -122.4074},
        "dropoff": {"latitude": 37.6213, "longitude": -122.3790}
    }
)

data = response.json()
print(f"Uber: ${data['uber']['estimate']:.2f}")
print(f"Lyft: ${data['lyft']['estimate']:.2f}")
print(f"Recommendation: {data['recommendation'].upper()}")
print(f"Save: ${data['savings']:.2f}")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const API_KEY = 'your_api_key';
const BASE_URL = 'http://localhost:8000';

async function comparePrices(pickup, dropoff) {
  const response = await axios.post(
    `${BASE_URL}/v1/compare`,
    { pickup, dropoff },
    { headers: { 'X-API-Key': API_KEY } }
  );

  const { uber, lyft, recommendation, savings } = response.data;

  console.log(`Uber: $${uber.estimate}`);
  console.log(`Lyft: $${lyft.estimate}`);
  console.log(`Recommendation: ${recommendation.toUpperCase()}`);
  console.log(`Save: $${savings}`);
}

comparePrices(
  { latitude: 37.7879, longitude: -122.4074 },
  { latitude: 37.6213, longitude: -122.3790 }
);
```

### cURL

```bash
# Compare prices
curl -X POST "http://localhost:8000/v1/compare" \
  -H "X-API-Key: test_free_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"pickup": {"latitude": 37.7879, "longitude": -122.4074}, "dropoff": {"latitude": 37.6213, "longitude": -122.3790}}'

# Get cities
curl "http://localhost:8000/v1/cities" \
  -H "X-API-Key: test_free_key_12345"

# Generate deep link
curl "http://localhost:8000/v1/deeplink/uber?pickup_lat=37.7879&pickup_lng=-122.4074&dropoff_lat=37.6213&dropoff_lng=-122.3790" \
  -H "X-API-Key: test_free_key_12345"
```

---

## Rate Limiting

When rate limit is exceeded, the API returns:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded (10 requests/minute)"
  }
}
```

With header:

```
Retry-After: 45
```

Wait the specified seconds before retrying.

---

## Webhooks (Coming Soon)

Subscribe to price alerts:

```json
{
  "route": {
    "pickup": {"latitude": 37.7879, "longitude": -122.4074},
    "dropoff": {"latitude": 37.6213, "longitude": -122.3790}
  },
  "threshold": 25.00,
  "webhook_url": "https://your-app.com/webhook"
}
```

---

## Support

- **API Issues**: api-support@mcp-aggregator.com
- **Documentation**: https://docs.mcp-aggregator.com
- **Status Page**: https://status.mcp-aggregator.com

---

**Last Updated:** 2026-01-12
