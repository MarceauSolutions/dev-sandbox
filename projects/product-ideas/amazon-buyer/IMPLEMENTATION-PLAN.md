# Amazon Buyer MCP - Implementation Plan

**Created**: 2026-01-14
**Status**: Ready for Phase 1

---

## Actionable Steps

### Immediate (This Week)

#### Step 1: Keepa API Setup ✅ ACTIONABLE NOW
1. **Sign up for Keepa API** at https://keepa.com/#!api
   - Select plan: Individual (€29/month) or Higher Volume (€99/month)
   - Get API key from dashboard

2. **Test API with sample ASIN**:
   ```bash
   curl "https://api.keepa.com/product?key=YOUR_KEY&domain=1&asin=B08N5WRWNW"
   ```

3. **Verify rate limits**:
   - Individual: 50 tokens/minute, refills at 2/second
   - Higher Volume: 100 tokens/minute

#### Step 2: Create Project Structure ✅ ACTIONABLE NOW
```bash
mkdir -p projects/amazon-buyer/src/amazon_buyer_mcp
touch projects/amazon-buyer/src/amazon_buyer_mcp/__init__.py
touch projects/amazon-buyer/src/amazon_buyer_mcp/server.py
touch projects/amazon-buyer/src/amazon_buyer_mcp/keepa_client.py
```

#### Step 3: Create Directive ✅ ACTIONABLE NOW
Create `directives/amazon-buyer.md` with:
- SOP 1: Product Lookup
- SOP 2: Price Tracking
- SOP 3: Product Comparison
- SOP 4: Deal Finding

---

### Phase 1: MVP (Keepa Only) - ~$30/month

**Goal**: Basic product lookup and price history

#### Tools to Build:

##### 1. `lookup_product` (P0)
```python
async def lookup_product(asin: str) -> dict:
    """
    Get product details and price history.

    Input: ASIN (e.g., "B08N5WRWNW")
    Output:
    - Product title, image, category
    - Current price (Amazon, 3rd party new, 3rd party used)
    - Price history (30/90/180/365 day min/max/avg)
    - Stock status
    - Rating history
    """
```

##### 2. `track_price` (P0)
```python
async def track_price(asin: str, target_price: float) -> dict:
    """
    Set up price drop notification.

    Input: ASIN, target price
    Output:
    - Current price
    - Target price set
    - Historical lowest (is target realistic?)
    - Estimated time to reach target
    """
```

##### 3. `get_price_history` (P0)
```python
async def get_price_history(asin: str, days: int = 90) -> dict:
    """
    Get detailed price history with analysis.

    Input: ASIN, days to look back
    Output:
    - Price data points
    - Min/max/average
    - Trend (rising/falling/stable)
    - Is current price a deal?
    """
```

#### Implementation Files:

**keepa_client.py**:
```python
import httpx
import os
from typing import Optional

class KeepaClient:
    BASE_URL = "https://api.keepa.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("KEEPA_API_KEY")
        if not self.api_key:
            raise ValueError("KEEPA_API_KEY required")

    async def get_product(self, asin: str, domain: int = 1) -> dict:
        """Fetch product data from Keepa."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/product",
                params={
                    "key": self.api_key,
                    "domain": domain,  # 1 = amazon.com
                    "asin": asin,
                    "history": 1,
                    "offers": 20
                }
            )
            return response.json()

    def parse_price_history(self, product: dict) -> dict:
        """Parse Keepa's price history format."""
        # Keepa uses cents and time since 2011
        # Convert to readable format
        pass
```

---

### Phase 2: Enhanced (Add PA-API) - ~$40-50/month

**Prerequisites**:
- Amazon Affiliate account (amazon.com/associates)
- PA-API access approved

#### Additional Tools:

##### 4. `compare_products` (P1)
```python
async def compare_products(asins: list[str]) -> dict:
    """
    Compare multiple products side-by-side.

    Input: List of 2-5 ASINs
    Output:
    - Price comparison
    - Feature comparison
    - Rating comparison
    - Value ranking with reasoning
    """
```

##### 5. `find_deals` (P2)
```python
async def find_deals(category: str, budget: float) -> dict:
    """
    Find best deals in a category.

    Input: Category, max budget
    Output:
    - Top 5 deals (price vs historical)
    - Deal score (% below average)
    - Recommendations
    """
```

---

### Phase 3: AI Layer - ~$10-20/month additional

#### Additional Tools:

##### 6. `analyze_reviews` (P1)
```python
async def analyze_reviews(asin: str) -> dict:
    """
    AI-powered review analysis.

    Input: ASIN
    Output:
    - Sentiment summary
    - Common praises (with quotes)
    - Common complaints (with quotes)
    - Authenticity score
    - Key insights
    """
```

##### 7. `check_seller` (P2)
```python
async def check_seller(seller_id: str) -> dict:
    """
    Check seller reliability.

    Input: Seller ID
    Output:
    - Rating history
    - Return rate estimate
    - Red flags
    - Recommendation
    """
```

---

## Cost Analysis

| Phase | Monthly Cost | Tools | Value |
|-------|-------------|-------|-------|
| Phase 1 (Keepa) | $30 | 3 | Core functionality |
| Phase 2 (+PA-API) | $40-50 | +2 | Enhanced data |
| Phase 3 (+AI) | $50-70 | +2 | Premium features |

**Break-even analysis**:
- If user saves $10/month on purchases → ROI in 3-5 months
- If avoiding 1 bad purchase ($50+)/quarter → immediate ROI

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Keepa API down | Low | High | Cache aggressively (24h TTL) |
| Rate limit hit | Medium | Medium | Implement request queuing |
| PA-API approval denied | Medium | Low | PA-API is optional enhancement |
| Keepa price increase | Low | Medium | Monitor alternatives (Rainforest API) |

---

## File Structure

```
projects/amazon-buyer/
├── exploration/
│   └── CONSOLIDATED-FINDINGS.md     ✅ Done
├── IMPLEMENTATION-PLAN.md           ✅ This file
├── src/
│   └── amazon_buyer_mcp/
│       ├── __init__.py              TODO
│       ├── server.py                TODO
│       ├── keepa_client.py          TODO
│       └── price_analyzer.py        TODO
├── pyproject.toml                   TODO
├── server.json                      TODO
├── VERSION                          TODO
├── CHANGELOG.md                     TODO
└── README.md                        TODO
```

---

## Next Immediate Actions

1. **[ ] Get Keepa API key** - Sign up at keepa.com
2. **[ ] Create directive** - `directives/amazon-buyer.md`
3. **[ ] Build keepa_client.py** - API wrapper with caching
4. **[ ] Build server.py** - MCP server with 3 tools
5. **[ ] Test locally** - Verify with real ASINs
6. **[ ] Deploy v0.1.0** - To PyPI + MCP Registry

---

## Success Criteria

**Phase 1 Complete When**:
- [ ] `lookup_product` returns valid data for any ASIN
- [ ] `get_price_history` shows correct historical prices
- [ ] `track_price` stores alert preferences
- [ ] Rate limiting doesn't cause errors
- [ ] Caching reduces API calls by 50%+

**Phase 2 Complete When**:
- [ ] PA-API integration working (if approved)
- [ ] `compare_products` ranks products intelligently
- [ ] `find_deals` surfaces actual deals

**Phase 3 Complete When**:
- [ ] Review analysis provides useful summaries
- [ ] Seller checking identifies red flags
- [ ] Users report saving money on purchases
