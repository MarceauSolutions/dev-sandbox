# Agent 3: PricingModel System Implementation

## Summary

Added comprehensive multi-pricing model support to the MCP Aggregator billing system. This enables MCPs to use different billing strategies beyond the original per-request model.

## Files Modified

### 1. billing.py

**New Enum: `PricingModel`** (line 39-54)
```python
class PricingModel(Enum):
    PER_REQUEST = "per_request"       # Current model: $X per API call
    SUBSCRIPTION = "subscription"      # Monthly fee, unlimited calls
    COMMISSION = "commission"          # % of transaction value
    TIERED = "tiered"                  # Volume-based pricing
    HYBRID = "hybrid"                  # Base fee + per-request
```

**Updated `Transaction` dataclass** (line 74-108)
- Added `pricing_model: PricingModel = PricingModel.PER_REQUEST`
- Added `subscription_id: Optional[str] = None`
- Added `booking_value: Optional[Decimal] = None`
- Added `commission_rate: Optional[Decimal] = None`
- Added `tier_name: Optional[str] = None`
- Updated `from_row()` method to parse these new fields

**New dataclass: `TierConfig`** (line 228-235)
```python
@dataclass
class TierConfig:
    name: str  # e.g., "starter", "growth", "enterprise"
    min_requests: int
    max_requests: Optional[int]
    fee_per_request: Decimal
    developer_share: Decimal
```

**Updated `FeeBreakdown` dataclass** (line 238-251)
- Added `pricing_model: PricingModel = PricingModel.PER_REQUEST`
- Added `booking_value`, `commission_rate`, `tier_name`, `subscription_id` for context

**New fee calculation methods in `BillingSystem`:**

1. `calculate_commission_fees()` (line 390-444)
   - Calculates fees based on booking_value * commission_rate
   - Splits commission between platform and developer

2. `calculate_subscription_fees()` (line 446-470)
   - Returns $0 per-call (subscription charged separately)
   - Tracks subscription_id for audit

3. `calculate_tiered_fees()` (line 472-524)
   - Looks up tier based on monthly request volume
   - Applies tier-specific rate and developer share

4. `calculate_hybrid_fees()` (line 526-567)
   - Combines subscription with per-request component

5. `get_mcp_developer_share()` (line 578-598)
   - Retrieves per-MCP developer share from database
   - Enables configurable billing splits

**New transaction logging method:**
- `log_transaction_with_pricing()` (line 649-800)
  - Handles all pricing models with appropriate parameters
  - Validates required parameters per model
  - Auto-calculates fees based on pricing model

**Default tier configuration** (line 313-343)
```python
DEFAULT_TIERS = [
    TierConfig(name="starter",    min_requests=0,      fee_per_request=0.02,  developer_share=0.80),
    TierConfig(name="growth",     min_requests=1001,   fee_per_request=0.015, developer_share=0.82),
    TierConfig(name="scale",      min_requests=10001,  fee_per_request=0.01,  developer_share=0.85),
    TierConfig(name="enterprise", min_requests=100001, fee_per_request=0.005, developer_share=0.88),
]
```

### 2. schema.sql

**New enum type: `pricing_model`** (line 36-42)
```sql
CREATE TYPE pricing_model AS ENUM (
    'per_request', 'subscription', 'commission', 'tiered', 'hybrid'
);
```

**Updated `mcps` table** (line 82-87)
- Added `pricing_model pricing_model DEFAULT 'per_request'`
- Added `commission_rate DECIMAL(5, 4)`
- Added `subscription_fee DECIMAL(10, 2)`

**Updated `transactions` table** (line 198-203)
- Added `pricing_model pricing_model DEFAULT 'per_request'`
- Added `subscription_id VARCHAR(255)`
- Added `booking_value DECIMAL(12, 4)`
- Added `commission_rate DECIMAL(5, 4)`
- Added `tier_name VARCHAR(50)`

**New tables:**

1. `subscriptions` (line 345-369)
   - Tracks active subscriptions per AI platform/MCP
   - Includes plan_name, monthly_fee, included_requests
   - Stripe integration fields

2. `pricing_tiers` (line 371-391)
   - Per-MCP tier configuration
   - Overrides default tiers when present
   - Includes tier_order for selection priority

**New indexes** (line 398-429)
- `idx_mcps_pricing_model` - Filter MCPs by pricing model
- `idx_transactions_pricing_model` - Query transactions by model
- `idx_transactions_subscription` - Lookup subscription transactions
- `idx_subscriptions_*` - Subscription lookups
- `idx_pricing_tiers_mcp` - Tier configuration lookup

**New triggers** (line 476-480)
- `update_subscriptions_timestamp`
- `update_pricing_tiers_timestamp`

**Documentation comments** (line 587-608)
- Added comments for all new columns explaining their purpose

## Success Criteria Met

1. **PricingModel enum exists with 5 types** - Yes
2. **Transaction dataclass has commission/subscription fields** - Yes
3. **Fee calculation handles at least PER_REQUEST and COMMISSION** - Yes (handles all 5)
4. **Billing split is configurable per-MCP** - Yes (via `developer_share` column and `get_mcp_developer_share()`)

## Backward Compatibility

- All new fields have defaults (`pricing_model DEFAULT 'per_request'`)
- Original `log_transaction()` method still works (delegates to new method)
- Original `calculate_fees()` method unchanged
- Existing transactions continue to work with default per_request model

## Usage Examples

### Commission-based transaction (e.g., booking service)
```python
billing.log_transaction_with_pricing(
    ai_platform_id='...',
    mcp_id='...',
    developer_id='...',
    request_id='req_booking_001',
    capability_name='book_ride',
    request_payload={...},
    pricing_model=PricingModel.COMMISSION,
    booking_value=Decimal('45.00'),
    commission_rate=Decimal('0.10'),  # 10%
    developer_share=Decimal('0.70')   # 70/30 split
)
```

### Tiered pricing (auto-selects tier)
```python
billing.log_transaction_with_pricing(
    ai_platform_id='...',
    mcp_id='...',
    developer_id='...',
    request_id='req_api_001',
    capability_name='query_data',
    request_payload={...},
    pricing_model=PricingModel.TIERED
    # Automatically looks up current month requests and selects tier
)
```

### Custom developer share
```python
# Set per-MCP in database
UPDATE mcps SET developer_share = 0.70 WHERE id = 'premium-mcp-id';

# Billing automatically uses MCP's configured share
dev_share = billing.get_mcp_developer_share(mcp_id)
fees = billing.calculate_fees(Decimal('0.02'), developer_share=dev_share)
```
