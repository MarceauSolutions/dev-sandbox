# MCP Aggregator API - Testing Guide

**Author:** Agent 1 (Autonomous Mode)
**Date:** 2026-01-12

---

## Overview

This guide covers how to test the MCP Aggregator API. The test suite includes unit tests, integration tests, and examples for manual testing.

---

## Test Suite Structure

```
workspace/
├── test_api.py          # All tests (59 test cases)
├── server.py            # Main FastAPI application
├── models.py            # Pydantic models
├── config.py            # Configuration
└── auth.py              # Authentication
```

### Test Categories

| Category | Test Class | Tests |
|----------|------------|-------|
| Health | `TestHealthEndpoints` | 3 |
| Authentication | `TestAuthentication` | 5 |
| Cities | `TestCitiesEndpoint` | 3 |
| Comparison | `TestComparisonEndpoint` | 7 |
| Deep Links | `TestDeepLinks` | 4 |
| Natural Language | `TestNaturalLanguageRoute` | 1 |
| Stats | `TestStatsEndpoint` | 2 |
| Models (Unit) | `TestModels` | 4 |
| Config (Unit) | `TestConfig` | 3 |
| Auth (Unit) | `TestAuthModule` | 3 |

---

## Running Tests

### Prerequisites

```bash
# Navigate to workspace
cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent1-rest-api/workspace

# Ensure dependencies are installed
pip install -r requirements.txt

# Set Python path for rideshare MCP
export PYTHONPATH="/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/src/mcps/rideshare:$PYTHONPATH"
```

### Run All Tests

```bash
pytest test_api.py -v
```

**Expected Output:**
```
test_api.py::TestHealthEndpoints::test_root_endpoint PASSED
test_api.py::TestHealthEndpoints::test_health_check PASSED
test_api.py::TestHealthEndpoints::test_health_no_auth_required PASSED
test_api.py::TestAuthentication::test_missing_api_key PASSED
...
========== 35 passed in 2.50s ==========
```

### Run Specific Test Class

```bash
# Health endpoints only
pytest test_api.py::TestHealthEndpoints -v

# Comparison endpoint only
pytest test_api.py::TestComparisonEndpoint -v

# Authentication tests only
pytest test_api.py::TestAuthentication -v
```

### Run with Coverage

```bash
# Generate coverage report
pytest test_api.py -v --cov=. --cov-report=html

# Open HTML report (macOS)
open htmlcov/index.html
```

### Run with Verbose Output

```bash
# Show all output
pytest test_api.py -v -s

# Show test durations
pytest test_api.py -v --durations=10
```

---

## Test API Keys

For testing, use these pre-configured keys:

| Key | Tier | Rate Limit |
|-----|------|------------|
| `test_free_key_12345` | Free | 10/min, 100/day |
| `test_basic_key_67890` | Basic | 60/min, 1000/day |
| `test_pro_key_11111` | Pro | 300/min, 10000/day |
| `test_enterprise_key_22222` | Enterprise | 1000/min, 100000/day |

---

## Manual Testing

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-12T...",
  "uptime_seconds": 123.45,
  "services": {
    "rate_cards": "healthy",
    "comparator": "healthy"
  }
}
```

### 2. Authentication Test

```bash
# Without API key (should fail)
curl http://localhost:8000/v1/cities

# Expected: 401 Unauthorized
# {"error": {"code": "INVALID_API_KEY", "message": "API key required"}}

# With valid API key
curl -H "X-API-Key: test_free_key_12345" http://localhost:8000/v1/cities

# Expected: 200 OK with cities list
```

### 3. Price Comparison

```bash
curl -X POST http://localhost:8000/v1/compare \
  -H "X-API-Key: test_free_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup": {"latitude": 37.7879, "longitude": -122.4074},
    "dropoff": {"latitude": 37.6213, "longitude": -122.3790}
  }'
```

**Check Response Fields:**
- `uber.estimate` - Should be a positive number
- `lyft.estimate` - Should be a positive number
- `recommendation` - Should be "uber" or "lyft"
- `savings` - Should equal `|uber.estimate - lyft.estimate|`
- `deep_link` - Should start with `uber://` or `lyft://`

### 4. Rate Limiting Test

```bash
# Make 11 requests quickly (free tier allows 10/min)
for i in {1..11}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "X-API-Key: test_free_key_12345" \
    http://localhost:8000/v1/cities
done

# Expected: First 10 return 200, 11th returns 429
```

### 5. Invalid Input Tests

```bash
# Invalid latitude (out of range)
curl -X POST http://localhost:8000/v1/compare \
  -H "X-API-Key: test_free_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"pickup": {"latitude": 999, "longitude": -122}, "dropoff": {"latitude": 37, "longitude": -122}}'

# Expected: 422 Validation Error

# Missing required field
curl -X POST http://localhost:8000/v1/compare \
  -H "X-API-Key: test_free_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"dropoff": {"latitude": 37, "longitude": -122}}'

# Expected: 422 Validation Error

# Unsupported city
curl -H "X-API-Key: test_free_key_12345" \
  http://localhost:8000/v1/cities/invalid_city/rates

# Expected: 400 UNSUPPORTED_CITY
```

---

## Test Routes by City

### San Francisco (Default Test City)

```bash
# Union Square to SFO Airport
curl -X POST http://localhost:8000/v1/compare \
  -H "X-API-Key: test_free_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup": {"latitude": 37.7879, "longitude": -122.4074},
    "dropoff": {"latitude": 37.6213, "longitude": -122.3790}
  }'
```

### New York

```bash
# Times Square to JFK Airport
curl -X POST http://localhost:8000/v1/compare \
  -H "X-API-Key: test_free_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup": {"latitude": 40.7580, "longitude": -73.9855},
    "dropoff": {"latitude": 40.6413, "longitude": -73.7781}
  }'
```

### Los Angeles

```bash
# Hollywood to LAX
curl -X POST http://localhost:8000/v1/compare \
  -H "X-API-Key: test_free_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup": {"latitude": 34.0928, "longitude": -118.3287},
    "dropoff": {"latitude": 33.9425, "longitude": -118.4081}
  }'
```

---

## Performance Testing

### Response Time Benchmark

```bash
# Install httpie if not available
pip install httpie

# Time a request
time http POST http://localhost:8000/v1/compare \
  X-API-Key:test_pro_key_11111 \
  pickup:='{"latitude": 37.7879, "longitude": -122.4074}' \
  dropoff:='{"latitude": 37.6213, "longitude": -122.3790}'
```

**Target:** < 100ms response time

### Load Testing

```bash
# Install hey
brew install hey

# Run load test (100 requests, 10 concurrent)
hey -n 100 -c 10 \
  -H "X-API-Key: test_enterprise_key_22222" \
  -H "Content-Type: application/json" \
  -m POST \
  -d '{"pickup":{"latitude":37.7879,"longitude":-122.4074},"dropoff":{"latitude":37.6213,"longitude":-122.3790}}' \
  http://localhost:8000/v1/compare
```

**Target Metrics:**
- 99th percentile < 200ms
- Zero errors
- 100+ requests/second

---

## Common Test Failures

### Issue: Import Error

```
ModuleNotFoundError: No module named 'comparison'
```

**Fix:**
```bash
export PYTHONPATH="/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/src/mcps/rideshare:$PYTHONPATH"
```

### Issue: Rate Limit During Tests

```
FAILED test_api.py::TestComparisonEndpoint::test_compare_prices_valid - AssertionError: assert 429 == 200
```

**Fix:**
- Use different API keys for different test classes
- Add delay between tests
- Or disable rate limiting: `MCP_ENABLE_RATE_LIMITING=false pytest`

### Issue: Server Not Started

```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Fix:**
- Tests use TestClient, server start not needed
- But if running manual tests, ensure server is running

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd agent1-rest-api/workspace
          pip install -r requirements.txt

      - name: Run tests
        run: |
          cd agent1-rest-api/workspace
          export PYTHONPATH="${{ github.workspace }}/src/mcps/rideshare:$PYTHONPATH"
          pytest test_api.py -v --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./agent1-rest-api/workspace/coverage.xml
```

---

## Checklist

Before deployment, verify:

- [ ] All pytest tests pass
- [ ] Health endpoint returns "healthy"
- [ ] Authentication works (401 without key)
- [ ] Rate limiting works (429 after limit)
- [ ] Price comparison returns valid estimates
- [ ] Deep links are properly formatted
- [ ] Error responses have correct format
- [ ] Response headers include X-Request-ID
- [ ] Response times < 100ms

---

**Created by:** Agent 1 (REST API)
**Date:** 2026-01-12
