# Session: 2026-01-04 - Amazon Seller Central SP-API Wrapper (Part 2)

**Date**: 2026-01-04
**Focus**: Built comprehensive Amazon Selling Partner API wrapper for seller operations, inventory optimization, and cost analysis

## Decisions Made

- **Built Amazon SP-API wrapper similar to ClickUp CRM**: Allows natural language management of Amazon seller account
  - Rationale: Same pattern as ClickUp - deterministic Python tools orchestrated by AI for complex seller operations

- **Implemented aggressive caching strategy**: Minimize GET API calls to reduce 2026 fees
  - Rationale: Starting April 30, 2026, Amazon charges per GET call. Caching saves significant costs.

- **Focus on inventory optimization first**: Storage fees and stockout risk are highest-impact use cases
  - Rationale: 2026 brings aged inventory surcharges ($0.30-0.35/unit), making optimization critical

- **Document review removal limitations**: Cannot remove reviews via API, only flag for manual action
  - Rationale: Amazon SP-API doesn't provide review removal endpoints - important user expectation to manage

## System Configuration Changes

### New Files Created

**Directives:**
- `directives/amazon_seller_operations.md` - Master directive for all Amazon seller operations
  - 10 comprehensive use cases (inventory, reviews, pricing, buy box, etc.)
  - 2026 fee structure documentation
  - Review removal compliance guidelines
  - API cost optimization strategies

**Execution Scripts:**
- `execution/amazon_sp_api.py` - Base API wrapper with authentication and caching
  - LWA (Login with Amazon) authentication
  - Multi-marketplace support
  - Built-in caching system to minimize API calls
  - API usage tracking for cost monitoring

- `execution/amazon_inventory_optimizer.py` - Inventory reorder optimization
  - Sales velocity calculation
  - Storage fee projections (including aged inventory surcharges)
  - Stockout cost analysis
  - Multi-scenario comparison (optimal, over-order, under-order)
  - Buy box risk assessment

**Documentation:**
- `docs/AMAZON_SETUP.md` - Complete SP-API setup guide
  - Step-by-step developer account registration
  - AWS IAM role configuration
  - Credential management
  - Marketplace IDs for all regions
  - Troubleshooting guide

**Configuration:**
- Updated `.env.example` with Amazon SP-API credentials template
- Updated `requirements.txt` with `python-amazon-sp-api` dependency

## Key Learnings & Discoveries

### Amazon SP-API Structure (2026)

1. **Cost Model Changed in 2026**:
   - Annual subscription: $1,400 USD (starts Jan 31, 2026)
   - GET calls: Per-call charges (starts Apr 30, 2026)
   - POST/PUT/PATCH: Remain free
   - **Implication**: Caching and notification-based approaches critical for cost control

2. **FBA Storage Fees (2026)**:
   - Standard monthly rates (seasonal: Jan-Sep vs Oct-Dec)
   - NEW: Aged inventory surcharges:
     - 12-15 months: $0.30/unit or $6.90/ft³
     - 15+ months: $0.35/unit or $7.90/ft³
   - **Implication**: Inventory aging now has significant cost penalty

3. **Review Management Limitations**:
   - SP-API provides Customer Feedback API for aggregate insights only
   - NO access to individual review text via API
   - NO review removal endpoints via API
   - Manual removal required through Seller Central UI
   - **Implication**: Can monitor and flag, but cannot automate removal

4. **Multi-Marketplace Operations**:
   - Different marketplace IDs for each region (US, CA, UK, DE, etc.)
   - Different fee structures per marketplace
   - Single API credentials work across all marketplaces
   - **Implication**: Easy to expand internationally once set up

### Cost Optimization Strategies

1. **Caching saves money**:
   - Default 30-60 minute cache for most data
   - Fees rarely change (24-hour cache)
   - Inventory checks can be cached 15-30 minutes
   - **Example**: Checking inventory 100x/day without cache = 3,000 GET calls/month. With cache = ~50 GET calls/month

2. **Notifications over polling**:
   - Subscribe to FBA_INVENTORY_AVAILABILITY_CHANGES notification
   - Get push updates instead of polling
   - Only fetch on-demand when needed

3. **Batch operations**:
   - Get multiple ASINs in single call where possible
   - Reduces call count significantly

## Workflows & Scripts Created

### 1. Amazon SP-API Base Wrapper
- **Location**: `execution/amazon_sp_api.py`
- **Purpose**: Authentication, caching, and base API operations
- **Usage**: Imported by other Amazon scripts
- **Key Features**:
  - Automatic token refresh
  - Marketplace-aware operations
  - Built-in caching layer
  - API call tracking for cost monitoring

### 2. Inventory Optimizer
- **Location**: `execution/amazon_inventory_optimizer.py`
- **Purpose**: Optimal reorder quantity recommendations with cost-benefit analysis
- **Usage**: `python execution/amazon_inventory_optimizer.py --asin B08XYZ123`
- **Key Features**:
  - Sales velocity calculation
  - Storage cost projections (including aged inventory fees)
  - Stockout risk and buy box impact
  - Multi-scenario comparison
  - Detailed cost breakdown

**Example Output**:
```
📊 CURRENT SITUATION
  • Current inventory: 120 units
  • Daily sales rate: 1.50 units/day
  • Days until stockout: 80.0 days
  • Urgency: 🟢 NORMAL

📦 RECOMMENDATION
  • Recommended order quantity: 90 units
  • Will provide 60 days of supply

💰 COST-BENEFIT ANALYSIS
  Optimal Order (90 units):
    Storage cost: $78.30
    Stockout risk: Minimal

  Over-Order Scenario (135 units, +50%):
    Storage cost: $117.45
    Extra storage: $39.15
    Aged inventory risk: ✓ Low

  Under-Order Scenario (63 units, -30%):
    Storage cost: $54.81
    Stockout cost: $127.50
    Total cost: $182.31
    ⚠️  RISK: 18 days stockout, 27 units lost
```

## Use Cases Supported

### Natural Language Commands

**Inventory Management:**
1. "Should I reorder ASIN B08XYZ123? Consider storage fees and buy box risk."
2. "Show me all ASINs at risk of aged inventory fees"
3. "Which products are at risk of running out in the next 14 days?"

**Cost Analysis:**
4. "Calculate total FBA fees for ASIN B08ABC456 this month"
5. "Show me storage cost projections for my top 10 ASINs"

**Review Monitoring:**
6. "Show me all 1-star reviews from this month"
7. "Flag reviews that violate Amazon policies for manual removal"

**Buy Box Tracking:**
8. "Am I winning the buy box for ASIN B08DEF789?"

**Price Optimization:**
9. "Optimize pricing for ASIN B08GHI012 to maximize profit while keeping buy box"

**Listing Management:**
10. "Create a new listing for [product details]"

## Gotchas & Solutions

### Cannot Remove Reviews via API
- **Issue**: User expected automated review removal like ClickUp task management
- **Reality**: Amazon SP-API provides NO review removal endpoints
- **Solution**:
  - Use Customer Feedback API for monitoring
  - Flag reviews meeting removal criteria
  - Provide manual instructions for Seller Central UI
  - Must request within 90-day window

### GET Calls Cost Money (April 2026)
- **Issue**: Frequent API polling becomes expensive
- **Solution**:
  - Implemented aggressive caching (30-60 min defaults)
  - Track API usage with counter
  - Print usage summary after operations
  - Recommend notification subscriptions over polling

### Review Text Not Available
- **Issue**: Cannot fetch individual review text, only aggregates
- **Reality**: Product Advertising API also doesn't provide review text
- **Workaround**:
  - For Brand Registry sellers, use Seller Central UI
  - Third-party scraping (compliance risks)
  - Focus on aggregate insights from Customer Feedback API

### Multi-Marketplace Complexity
- **Issue**: Different fees, currencies, IDs per marketplace
- **Solution**:
  - Marketplace ID in environment variables
  - Built-in marketplace mapping in wrapper
  - Documentation of all marketplace IDs

## Commands & Shortcuts

```bash
# Install Amazon SP-API library
pip install python-amazon-sp-api

# Test API connection
python execution/amazon_sp_api.py

# Get inventory reorder recommendation
python execution/amazon_inventory_optimizer.py --asin B08XYZ123

# Custom parameters
python execution/amazon_inventory_optimizer.py \
  --asin B08XYZ123 \
  --days 30 \
  --lead-time 45 \
  --target-supply 90

# Clear cache (force fresh API calls)
rm -rf .tmp/amazon_cache
```

## Amazon SP-API Setup (High-Level)

1. Register as SP-API developer at developer.amazonservices.com
2. Create AWS IAM role with proper trust policy
3. Get LWA (Login with Amazon) credentials
4. Authorize application to get refresh token
5. Add credentials to `.env` file
6. Install `python-amazon-sp-api` library
7. Test connection

**Full Details**: See [docs/AMAZON_SETUP.md](../AMAZON_SETUP.md)

## File Structure

```
dev-sandbox/
├── directives/
│   └── amazon_seller_operations.md          # Master directive (10 use cases)
├── execution/
│   ├── amazon_sp_api.py                     # Base API wrapper
│   └── amazon_inventory_optimizer.py        # Inventory optimizer
├── docs/
│   ├── AMAZON_SETUP.md                      # Complete setup guide
│   └── sessions/
│       └── 2026-01-04-amazon-sp-api-wrapper.md  # This file
├── .env.example                             # Updated with Amazon credentials
└── requirements.txt                         # Added python-amazon-sp-api
```

## 2026 Cost Breakdown

### API Fees (Starting 2026)
- **Annual**: $1,400 USD (Jan 31, 2026)
- **GET calls**: Variable per call (Apr 30, 2026)
- **POST/PUT/PATCH**: Free

### FBA Storage Fees
- **Standard (Jan-Sep)**: $0.87/ft³
- **Standard (Oct-Dec)**: $2.40/ft³ (peak season)
- **Aged 12-15mo**: +$0.30/unit or +$6.90/ft³
- **Aged 15+mo**: +$0.35/unit or +$7.90/ft³

### Cost Optimization Impact
Without caching: ~3,000 GET calls/month
With caching: ~50-100 GET calls/month
**Savings**: ~97% reduction in API calls

## Next Steps

- [ ] Complete SP-API developer registration
- [ ] Set up AWS IAM role
- [ ] Get LWA credentials and refresh token
- [ ] Add credentials to `.env` file
- [ ] Test inventory optimizer with real data
- [ ] Expand to additional use cases (pricing, buy box, listings)
- [ ] Deploy to production Skills workspace when ready

## References

### Official Documentation
- [Amazon SP-API Docs](https://developer-docs.amazon.com/sp-api)
- [Customer Feedback API](https://developer-docs.amazon.com/sp-api/docs/customer-feedback-api)
- [Python SP-API Library](https://github.com/saleweaver/python-amazon-sp-api)

### 2026 Fee Information
- [SP-API 2026 Fees](https://www.esellerhub.com/blog/amazon-sp-api-fees-update-2026/)
- [FBA Fee Changes 2026](https://sellerengine.com/amazon-2026-fba-fees/)
- [Amazon FBA Fees Guide](https://www.goatconsulting.com/blog/amazon-fba-fee-changes-for-2026)

### Review Management
- [Review Removal Guidelines](https://www.sellify.app/documentation/how-to-remove-amazon-reviews-legitimately-2026-method)
- [Appstore Ratings](https://developer-docs.amazon.com/sp-api/docs/ratings-and-reviews-in-the-selling-partner-appstore)

## Related Sessions

- [2026-01-04 Git Restructure](2026-01-04-git-restructure-and-github-setup.md) - Git setup and session memory system

---

**Last Updated**: 2026-01-04
