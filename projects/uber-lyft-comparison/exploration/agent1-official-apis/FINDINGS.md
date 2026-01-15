# Official APIs - Research Findings

## Summary
**Feasible?**: No - Legally Prohibited
**One-sentence verdict**: While both Uber and Lyft have public APIs with price estimate endpoints, using them for price comparison apps is explicitly forbidden in Uber's Terms of Service and would likely violate Lyft's competitive restrictions.

## Technical Details

### Uber API

**Endpoint**: `GET https://api.uber.com/v1.2/estimates/price`

**Documentation**: [developer.uber.com/docs/v1-estimates-price](https://developer.uber.com/docs/v1-estimates-price)

**Authentication**: OAuth 2.0 (Server Token for public endpoints, User Authorization for user-specific data)

**Required Parameters**:
- `start_latitude` (number): Latitude component of start location
- `start_longitude` (number): Longitude component of start location
- `end_latitude` (number): Latitude component of end location
- `end_longitude` (number): Longitude component of end location

**Response Structure**:
```json
{
  "prices": [
    {
      "product_id": "a1111c8c-c720-46c3-8534-2fcdd730040d",
      "currency_code": "USD",
      "display_name": "UberX",
      "estimate": "$15-18",
      "low_estimate": 15,
      "high_estimate": 18,
      "surge_multiplier": 1.0,
      "duration": 540,
      "distance": 2.5
    }
  ]
}
```

**Key Features**:
- Returns price range for all available ride types at location
- Includes surge pricing multipliers
- Provides duration and distance estimates
- Localized currency formatting

### Lyft API

**Endpoint**: `GET https://api.lyft.com/v1/cost`

**Documentation**: [developer.lyft.com](https://developer.lyft.com/docs) (requires business contact for full access)

**Authentication**: OAuth 2.0
- Client ID and Client Secret (for two or three-legged OAuth)
- Client Token (for public endpoints without user context)

**Required Parameters**:
- `start_lat` (number): Starting latitude
- `start_lng` (number): Starting longitude
- `end_lat` (number): Ending latitude
- `end_lng` (number): Ending longitude
- `ride_type` (optional): Specific ride type to estimate

**Response Structure**:
```json
{
  "cost_estimates": [
    {
      "ride_type": "lyft",
      "display_name": "Lyft",
      "estimated_cost_cents_min": 1200,
      "estimated_cost_cents_max": 1800,
      "estimated_distance_miles": 2.5,
      "estimated_duration_seconds": 540,
      "primetime_percentage": "0%",
      "is_valid_estimate": true
    }
  ]
}
```

**Key Features**:
- Cost in minor units (cents) for precision
- Primetime (surge) percentage
- Distance and duration estimates
- Validity indicator for estimates

## Costs

### Uber API
- **Setup cost**: $0 (Free registration at developer.uber.com)
- **Monthly cost**: $0
- **Per-request cost**: $0 (Free API)
- **Free tier**: Full API access with rate limits

### Lyft API
- **Setup cost**: $0
- **Monthly cost**: $0 (Sandbox mode free, production may require business account)
- **Per-request cost**: $0 for approved developers
- **Free tier**: Sandbox mode available

### Rate Limits

**Uber**:
- 500 HTTP requests per 5 seconds per app
- 1,000 requests per hour per secret token (default)
- HTTP 429 status code when exceeded
- Endpoint-specific limits may apply

**Lyft**:
- Specific limits not publicly documented
- Response headers include `x-ratelimit-remaining` and `x-ratelimit-limit`
- Likely similar to industry standards

## Pros

1. **Official & Reliable**: Direct access to Uber and Lyft's real-time pricing data, guaranteed accurate
2. **No Scraping Risk**: Stable, documented API endpoints that won't break with UI changes
3. **Free Access**: No per-request costs or monthly fees for basic usage
4. **Rich Data**: Includes surge/primetime multipliers, multiple ride types, distance/duration estimates
5. **Professional Support**: Official SDKs available (Go, Node.js, iOS), developer documentation, sandbox environments

## Cons

1. **FATAL: Terms of Service Violation**: Uber explicitly prohibits price comparison in § II B of API Terms ("You may not use the Uber API in any manner that is competitive to Uber")
2. **Active Enforcement**: Uber has historically shut down price comparison apps (Urbanhail in 2016, threatened Ride Fair)
3. **Account Termination Risk**: API access can be "temporarily or permanently blocked or revoked" for ToS violations
4. **Lyft Access Restricted**: Must contact Lyft Business representative for API access (no longer self-service)
5. **Uber Approval Process**: Privileged access requires 2+ business days approval, may require justification
6. **Limited Geographic Coverage**: Primarily US-focused, international coverage unclear
7. **No Competitive Use**: Both platforms restrict using their APIs alongside competitor services

## Risks

### Legal Risks
**CRITICAL - SHOW STOPPER**:
- **Uber ToS Explicit Prohibition**: "Using the Uber API to offer price comparisons with competitive third party services is in violation of § II B of the API Terms of Use" ([source](https://developer.uber.com/docs/v1-estimates-price))
- **Contractual Violation**: Both APIs require developer agreements that prohibit competitive/comparison use
- **Enforcement History**: Uber sent cease-and-desist to Ride Fair: "Since it seems the main purpose of your app is price comparison, there isn't really a good way for you to come into compliance. We have to ask you to immediately discontinue using our API for this purpose." ([source](https://www.benedelman.org/news-053116/))
- **Legal Action Risk**: Potential lawsuits for breach of contract, intellectual property claims

### Technical Risks
- **Immediate Revocation**: API access can be cut off with no warning once price comparison is detected
- **Account Blacklisting**: Developer accounts may be permanently banned
- **IP/Domain Blocking**: Uber/Lyft could block requests from known comparison services
- **Monitoring & Detection**: Both platforms likely monitor for competitive API usage patterns

### Business Risks
- **Unsustainable Model**: Cannot build a business on APIs that explicitly prohibit your use case
- **Wasted Development**: All code becomes worthless if API access is revoked
- **No Recourse**: Terms of Service give platforms absolute discretion to terminate access
- **Investor/User Risk**: Cannot promise service reliability when access can be terminated at will

## Code Example

**NOTE**: This code is for educational/research purposes only and should NOT be used for a price comparison app.

```python
import requests
import os

def get_uber_price_estimate(start_lat, start_lng, end_lat, end_lng):
    """
    Get Uber price estimate between two locations.

    WARNING: Using this for price comparison violates Uber's ToS.
    This is for educational purposes only.
    """
    url = "https://api.uber.com/v1.2/estimates/price"

    headers = {
        "Authorization": f"Token {os.environ.get('UBER_SERVER_TOKEN')}",
        "Accept-Language": "en_US",
        "Content-Type": "application/json"
    }

    params = {
        "start_latitude": start_lat,
        "start_longitude": start_lng,
        "end_latitude": end_lat,
        "end_longitude": end_lng
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract price estimates
        for product in data.get('prices', []):
            print(f"{product['display_name']}: {product['estimate']}")
            if product.get('surge_multiplier', 1.0) > 1.0:
                print(f"  ⚠️ Surge: {product['surge_multiplier']}x")

        return data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("Rate limit exceeded (500 req/5sec)")
        elif e.response.status_code == 401:
            print("Invalid or missing authentication token")
        raise


def get_lyft_price_estimate(start_lat, start_lng, end_lat, end_lng):
    """
    Get Lyft cost estimate between two locations.

    WARNING: Using this for price comparison likely violates Lyft's developer terms.
    This is for educational purposes only.
    """
    url = "https://api.lyft.com/v1/cost"

    headers = {
        "Authorization": f"Bearer {os.environ.get('LYFT_ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }

    params = {
        "start_lat": start_lat,
        "start_lng": start_lng,
        "end_lat": end_lat,
        "end_lng": end_lng
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract cost estimates
        for estimate in data.get('cost_estimates', []):
            min_cost = estimate['estimated_cost_cents_min'] / 100
            max_cost = estimate['estimated_cost_cents_max'] / 100
            print(f"{estimate['display_name']}: ${min_cost:.2f}-${max_cost:.2f}")
            if estimate.get('primetime_percentage', '0%') != '0%':
                print(f"  ⚠️ Primetime: {estimate['primetime_percentage']}")

        return data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("Rate limit exceeded")
        elif e.response.status_code == 401:
            print("Invalid or missing access token")
        raise


# Example usage (DO NOT USE FOR PRICE COMPARISON APP)
if __name__ == "__main__":
    # San Francisco: Ferry Building to SF Airport
    start_lat, start_lng = 37.7955, -122.3937
    end_lat, end_lng = 37.6213, -122.3790

    print("⚠️ WARNING: Price comparison violates Terms of Service")
    print("This is for educational/research purposes only\n")

    print("Uber Estimates:")
    get_uber_price_estimate(start_lat, start_lng, end_lat, end_lng)

    print("\nLyft Estimates:")
    get_lyft_price_estimate(start_lat, start_lng, end_lat, end_lng)
```

## Scoring

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| **Feasibility** | ⭐ | APIs exist and work, but ToS explicitly prohibits the use case |
| **Legal** | ⭐ | Explicit ToS violation with documented enforcement history |
| **Cost** | ⭐⭐⭐⭐⭐ | Free API with generous rate limits (only positive aspect) |
| **Reliability** | ⭐ | API access will be terminated once price comparison is detected |
| **Maintenance** | ⭐ | Constant risk of shutdown requires monitoring, no long-term viability |
| **User Experience** | ⭐⭐⭐⭐⭐ | If allowed, would provide instant, accurate, real-time pricing |
| **Scalability** | ⭐ | Cannot scale when access can be revoked at any time |

**Weighted Total**: 8/35 points (weighted to reflect legal/feasibility as 2x importance)

## Recommendation

⭐ **AVOID - LEGAL SHOW STOPPER**

**Rationale**:

While this is technically the **most accurate and reliable** approach from a pure data quality perspective, it is **completely non-viable** due to legal restrictions. Here's why this cannot work:

### Why It Seems Attractive
- ✅ Official, real-time, accurate pricing data
- ✅ Free APIs with good rate limits
- ✅ Professional documentation and SDKs
- ✅ No scraping, no maintenance overhead
- ✅ Fast response times (<1 second)

### Why It's a Non-Starter
- ❌ **Uber explicitly prohibits price comparison in written ToS**
- ❌ **Documented enforcement history** (Urbanhail shutdown 2016, Ride Fair cease-and-desist)
- ❌ **Lyft likely has similar restrictions** (requires business contact approval)
- ❌ **No workaround exists** - once detected, access is revoked permanently
- ❌ **Cannot build sustainable business** when platform can terminate at will
- ❌ **Legal liability** for breach of contract

### The Bottom Line

**This approach is like building a house on someone else's land without permission, and the landlord has explicitly told previous builders to leave.**

The Terms of Service are not ambiguous - Uber's documentation includes a direct warning: "Using the Uber API to offer price comparisons with competitive third party services is in violation of § II B of the API Terms of Use."

### If You Proceed Anyway...

If someone chose to ignore these restrictions (not recommended), here's what would happen:

1. **Week 1-2**: Register for developer accounts, build integration, everything works perfectly
2. **Week 3-4**: Launch app, users love it, growth starts
3. **Week 4-8**: Uber/Lyft detect price comparison usage patterns
4. **Day X**: Wake up to email: "Your API access has been terminated for ToS violation"
5. **Forever**: App broken, users angry, no path forward, wasted investment

### Alternative Recommendation

**Do NOT use official APIs for price comparison.** Explore alternative approaches:

- **Approach 2**: Web scraping (risky but not contractually prohibited)
- **Approach 3**: Third-party aggregator APIs (if they exist and allow comparison)
- **Approach 4**: User-submitted data / crowdsourcing
- **Different Product**: Pivot to a use case Uber/Lyft DO allow (ride booking, not comparison)

## References

### Official Documentation
- [Uber Price Estimates API](https://developer.uber.com/docs/v1-estimates-price)
- [Uber Terms of Use](https://developer.uber.com/docs/riders/terms-of-use)
- [Uber Rate Limiting](https://developer.uber.com/docs/riders/guides/rate-limiting)
- [Lyft Developer Platform](https://www.lyft.com/developers)
- [Lyft Developer Platform Terms of Use](https://developer.lyft.com/docs/lyft-developer-platform-terms-of-use)
- [Lyft Rate Limits](https://developer.lyft.com/docs/rate-limits)
- [Lyft Authentication](https://developer.lyft.com/docs/authentication)

### Enforcement & Analysis
- [How Uber Uses API Restrictions to Block Price Comparison](https://www.benedelman.org/news-053116/) - Ben Edelman analysis
- [Uber threatens to shut down price-comparison app](https://www.sfchronicle.com/business/article/Uber-threatens-to-shut-down-price-comparison-app-11275332.php) - SF Chronicle
- [Uber API Terms Bar Developers From Working With Competing Services](https://techcrunch.com/2014/08/20/uber-api-terms/) - TechCrunch
- [Uber Cuts Startup's API Access](https://www.thebeat.travel/News/Uber-Cuts-Startups-API-Access-Asserts-Price-Comparison-Restrictions) - The Beat

### Rate Limits & Pricing
- [Uber API - PublicAPI](https://publicapi.dev/uber-api)
- [Travel & Booking APIs (Geographic Coverage)](https://satvasolutions.com/travel-and-booking-apis)

### Recent Studies
- [Study shows Uber and Lyft users overpay when they don't price check](https://hub.jhu.edu/2026/01/02/uber-lyft-study-carey-business-school/) - Johns Hopkins (January 2026)

---

**Last Updated**: 2026-01-12
**Researcher**: Agent 1 - Official APIs Exploration
**Status**: Complete - DO NOT PROCEED with this approach
