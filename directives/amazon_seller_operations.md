# Directive: Amazon Seller Central Operations

## Goal

Provide natural language interface to Amazon Seller Central via SP-API for inventory management, cost optimization, review management, and seller operations.

## Context

Amazon's Selling Partner API (SP-API) allows programmatic access to seller account data and operations. This directive establishes the foundation for managing an Amazon seller account through AI orchestration.

### Important 2026 Changes
- **Annual Fee**: $1,400 USD (starting January 31, 2026)
- **GET Call Fees**: Charged per call (starting April 30, 2026)
- **Free Operations**: POST, PUT, PATCH calls remain free

## Available SP-API Capabilities

### Inventory Management
- Real-time inventory levels across all warehouses
- FBA inventory availability notifications
- Multi-location inventory (MLI) tracking
- Low inventory level monitoring
- Aged inventory tracking (12-15 months, 15+ months)

### Pricing & Listings
- Dynamic price adjustments
- Product listing creation/management
- Competitive pricing data
- Buy Box status monitoring

### Order & Fulfillment
- Real-time order status
- Fulfillment operations management
- Multi-marketplace sync

### Financial Data
- Payment reports
- Fee breakdowns (FBA, storage, referral)
- Cost analysis per ASIN

### Customer Feedback
- Customer Feedback API (v2024-06-01)
- Review insights at ASIN level
- Return insights at browse node level
- Solicitations API (request reviews)

**IMPORTANT LIMITATION**: Amazon SP-API does NOT provide direct access to individual product review text, titles, or reviewer information. Review removal must be done through Seller Central UI.

## Inputs

### Required Credentials
- `AMAZON_CLIENT_ID` - SP-API application client ID
- `AMAZON_CLIENT_SECRET` - SP-API application secret
- `AMAZON_REFRESH_TOKEN` - OAuth refresh token
- `AMAZON_SELLER_ID` - Your seller/merchant ID
- `AMAZON_MARKETPLACE_ID` - Marketplace identifier (e.g., ATVPDKIKX0DER for US)
- `AMAZON_REGION` - API region (e.g., us-east-1)

### Operation-Specific Inputs
- **Inventory Reorder**: Product ASIN, current inventory level, sales velocity
- **Cost Analysis**: ASIN, time period, fee types to analyze
- **Review Management**: ASIN, review criteria
- **Price Optimization**: ASIN, target margin, competitor data

## Tools

### Core Scripts
- `execution/amazon_sp_api.py` - Base API wrapper for authentication and common operations
- `execution/amazon_inventory_optimizer.py` - Inventory reorder recommendations with cost-benefit analysis
- `execution/amazon_review_monitor.py` - Review monitoring and flagging (cannot remove via API)
- `execution/amazon_fee_calculator.py` - FBA fee calculations and storage cost projections
- `execution/amazon_listing_manager.py` - Product listing creation and updates

## Use Cases

### 1. Inventory Reorder Optimization

**Natural Language Request**: "Should I reorder ASIN B08XYZ123? Consider storage fees and buy box risk."

**Process**:
1. Get current inventory level for ASIN
2. Calculate sales velocity (units/day)
3. Project days until stockout
4. Calculate storage fees for different order quantities
5. Factor in aged inventory surcharges (12-15mo: $0.30/unit, 15+mo: $0.35/unit)
6. Compare cost of:
   - Over-ordering → higher storage fees
   - Under-ordering → losing buy box + lost sales
7. Recommend optimal order quantity with cost breakdown

**Output**: Recommendation with:
- Optimal order quantity
- Days of supply this provides
- Total storage cost projection
- Risk of stockout vs. excess inventory
- Break-even analysis

### 2. Storage Cost Analysis

**Natural Language Request**: "Show me all ASINs at risk of aged inventory fees"

**Process**:
1. Get FBA inventory age report
2. Identify ASINs with 10+ months inventory
3. Calculate current storage fees
4. Project aged inventory surcharges if unsold
5. Recommend actions (price reduction, removal, liquidation)

### 3. Fee Optimization

**Natural Language Request**: "Calculate total FBA fees for ASIN B08ABC456 this month"

**Process**:
1. Get order data for ASIN
2. Calculate per-unit fees:
   - FBA fulfillment fee
   - Monthly storage fee
   - Referral fee
   - Low inventory fee (if applicable)
   - Aged inventory fee (if applicable)
3. Aggregate total costs
4. Calculate profit margin

### 4. Review Monitoring

**Natural Language Request**: "Show me all 1-star reviews from this month"

**Process**:
1. Use Customer Feedback API to get review insights
2. Filter by rating and date
3. Flag reviews that may violate Amazon policies:
   - Product arrived damaged (fulfillment issue, not product issue)
   - Wrong item received (Amazon error)
   - Reviews mentioning competitor products
   - Reviews with prohibited content
4. **Output manual instructions** for removal via Seller Central (cannot be done via API)

**IMPORTANT**: Review removal MUST be done manually through Seller Central. API can only monitor and flag.

### 5. Buy Box Monitoring

**Natural Language Request**: "Am I winning the buy box for ASIN B08DEF789?"

**Process**:
1. Get competitive pricing data
2. Check current buy box status
3. Monitor inventory availability
4. Track fulfillment metrics
5. Alert if buy box lost

### 6. Multi-Marketplace Sync

**Natural Language Request**: "Update inventory across all marketplaces to match US levels"

**Process**:
1. Get US marketplace inventory
2. Compare with EU, CA, MX marketplaces
3. Update inventory levels to sync
4. Account for marketplace-specific storage limits

### 7. Price Optimization

**Natural Language Request**: "Optimize pricing for ASIN B08GHI012 to maximize profit while keeping buy box"

**Process**:
1. Get current competitive prices
2. Calculate minimum profitable price (cost + fees + margin)
3. Determine buy box price threshold
4. Recommend price that balances profit and competitiveness

### 8. Low Inventory Alerts

**Natural Language Request**: "Which products are at risk of running out in the next 14 days?"

**Process**:
1. Get current inventory levels
2. Calculate sales velocity (last 30 days)
3. Project stockout date
4. Alert on items with <14 days supply
5. Recommend reorder quantities

### 9. Listing Management

**Natural Language Request**: "Create a new listing for [product details]"

**Process**:
1. Extract product details (title, description, bullets, images)
2. Determine category and browse nodes
3. Set pricing
4. Create listing via Listings API
5. Monitor listing approval status

### 10. Returns Analysis

**Natural Language Request**: "Why are customers returning ASIN B08JKL345?"

**Process**:
1. Get return insights via Customer Feedback API
2. Analyze return reasons at browse node level
3. Identify patterns
4. Recommend product or listing improvements

## Storage Fee Calculations (2026)

### Monthly Storage Fees
- **Standard-size**: Varies by season
- **Oversize**: Higher rates
- **Aged Inventory Surcharges**:
  - 12-15 months: $0.30/unit or $6.90/ft³
  - 15+ months: $0.35/unit or $7.90/ft³

### Cost Optimization Strategies
1. Use Amazon Warehousing & Distribution (AWD) - no inbound fees
2. Maintain tight inventory forecasting to avoid Low Inventory Level fees
3. Monitor aged inventory thresholds
4. Calculate break-even on storage vs stockout risk

## Review Removal Compliance

### Legitimate Removal Reasons (per Amazon policy)
1. **Fulfillment Issues**: Product arrived damaged, wrong item, late delivery
2. **Prohibited Content**: Profanity, personal information, competitor mentions
3. **Not a Product Review**: Questions, seller feedback (not product review)
4. **Promotional Content**: Reviews offering incentives or violating FTC guidelines

### Process (Manual - Not API)
1. **Monitor**: Use API to identify potentially violating reviews
2. **Flag**: Create report of reviews meeting removal criteria
3. **Manual Action Required**: Submit removal request via Seller Central
4. **90-Day Window**: Requests must be within 90 days of review submission
5. **Track**: Monitor ODR (Order Defect Rate) - must stay under 1%

**CRITICAL**: There is NO SP-API endpoint for removing reviews. This must be done manually.

## Edge Cases

### API Rate Limits
- **GET calls are metered** (charged starting April 30, 2026)
- Implement caching to minimize API calls
- Batch operations where possible
- Use webhooks/notifications instead of polling

### Multi-Marketplace Operations
- Different marketplace IDs for US, CA, UK, DE, etc.
- Different fee structures per marketplace
- Currency conversions required

### Inventory Sync Delays
- FBA inventory updates may lag by hours
- Use notification subscriptions for real-time updates
- Don't rely on immediate consistency

### Review Monitoring Limitations
- Cannot retrieve full review text via API
- Can only get aggregate insights (not individual reviews)
- Manual verification required in Seller Central

### Authentication Token Expiry
- Refresh tokens periodically
- Handle 401/403 errors gracefully
- Re-authenticate automatically

## API Cost Optimization

### Minimize GET Calls (to reduce fees)
1. **Cache aggressively** - store frequently accessed data locally
2. **Use notifications** - subscribe to inventory/order change events instead of polling
3. **Batch requests** - get multiple ASINs in single call where possible
4. **Strategic polling** - only fetch critical data frequently
5. **Use free operations** - POST/PUT/PATCH for updates don't incur fees

### Example: Instead of polling inventory every hour (720 GET calls/month):
- Subscribe to FBA_INVENTORY_AVAILABILITY_CHANGES notification
- Only GET inventory on-demand when needed
- Cache results for non-critical queries

## Outputs

### Inventory Recommendations
- Reorder quantity with cost-benefit analysis
- Storage fee projections
- Stockout risk assessment
- Optimal reorder timing

### Review Reports
- List of flagged reviews with removal criteria
- Manual action instructions for Seller Central
- ODR impact analysis

### Financial Reports
- Fee breakdowns by ASIN
- Profit margin analysis
- Cost optimization recommendations

### Alerts
- Low inventory warnings
- Buy box status changes
- Aged inventory approaching surcharge thresholds
- Price competitiveness alerts

## Success Criteria

1. Can execute natural language requests for inventory, pricing, reviews
2. Provides cost-benefit analysis for inventory decisions
3. Accurately calculates FBA fees including 2026 changes
4. Monitors review compliance (flags for manual removal)
5. Optimizes API call usage to minimize 2026 fees
6. Maintains authentication seamlessly
7. Handles multi-marketplace operations

## References

- [Amazon SP-API Documentation](https://developer-docs.amazon.com/sp-api)
- [Customer Feedback API](https://developer-docs.amazon.com/sp-api/docs/customer-feedback-api)
- [SP-API 2026 Fee Changes](https://www.esellerhub.com/blog/amazon-sp-api-fees-update-2026/)
- [Amazon 2026 FBA Fees](https://sellerengine.com/amazon-2026-fba-fees/)
- [Review Removal Guidelines](https://www.sellify.app/documentation/how-to-remove-amazon-reviews-legitimately-2026-method)

## Next Steps

1. Set up Amazon SP-API developer account
2. Create LWA (Login with Amazon) credentials
3. Implement base API wrapper (`amazon_sp_api.py`)
4. Build inventory optimizer with cost calculations
5. Create review monitoring with compliance flagging
6. Test with real seller account data
7. Deploy to production Skills workspace
