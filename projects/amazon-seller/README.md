# Amazon Seller Operations AI Assistant

AI-powered Amazon Seller Central automation for inventory management, fee calculation, listing optimization, and business analytics via SP-API.

## Status: Development

**Production URL:** Not yet deployed

## Features

| Feature | Script | Cost |
|---------|--------|------|
| SP-API Integration | `amazon_sp_api.py` | FREE |
| FBA Fee Calculator | `amazon_fee_calculator.py` | FREE |
| Inventory Optimizer | `amazon_inventory_optimizer.py` | FREE |
| OAuth Authentication | `amazon_oauth_server.py` | FREE |
| Token Refresh | `refresh_amazon_token.py` | FREE |
| Auth Setup Wizard | `setup_amazon_auth.py` | FREE |
| Connection Test | `test_amazon_connection.py` | FREE |

## Directory Structure

```
amazon-seller/
├── src/                              # Python execution scripts
│   ├── amazon_sp_api.py              # Core SP-API client
│   ├── amazon_fee_calculator.py      # FBA fee calculations
│   ├── amazon_inventory_optimizer.py # Restock recommendations
│   ├── amazon_oauth_server.py        # OAuth server for auth
│   ├── amazon_get_refresh_token.py   # Get refresh token
│   ├── refresh_amazon_token.py       # Refresh access token
│   ├── setup_amazon_auth.py          # Setup wizard
│   ├── test_amazon_connection.py     # Test connection
│   └── test_sp_api_simple.py         # Simple API test
├── docs/                             # Documentation
├── frontend/                         # Web interface (TODO)
└── README.md
```

## Quick Start

### 1. Setup Amazon Credentials
```bash
python src/setup_amazon_auth.py
```

### 2. Test Connection
```bash
python src/test_amazon_connection.py
```

### 3. Calculate Fees
```bash
python src/amazon_fee_calculator.py --asin B0XXXXXXXX
```

### 4. Get Inventory Recommendations
```bash
python src/amazon_inventory_optimizer.py --days 30
```

## Environment Variables

```env
# Amazon SP-API
AMAZON_SELLER_ID=your_seller_id
AMAZON_MARKETPLACE_ID=ATVPDKIKX0DER  # US marketplace
AMAZON_CLIENT_ID=your_client_id
AMAZON_CLIENT_SECRET=your_client_secret
AMAZON_REFRESH_TOKEN=your_refresh_token

# AWS (for SP-API signing)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret

# Shared Services (from ../shared/)
XAI_API_KEY=your_xai_key              # For AI features
ANTHROPIC_API_KEY=your_anthropic_key  # For AI analysis
```

## Shared Utilities Used

This project uses shared utilities from `projects/shared/`:

| Utility | Purpose |
|---------|---------|
| `shared/google/gmail_monitor.py` | Monitor supplier emails |
| `shared/analytics/revenue_analytics.py` | Revenue tracking |
| `shared/communication/twilio_sms.py` | Inventory alerts |

## Skill Configuration

Located at: `.claude/skills/amazon-seller-operations/SKILL.md`

Trigger phrases:
- "check Amazon inventory"
- "calculate FBA fees"
- "optimize Amazon listings"
- "restock recommendations"

## Related Documentation

- Main directive: `directives/amazon_seller_operations.md`
- Setup guide: `docs/AMAZON_SETUP.md`
- Quick start: `docs/AMAZON_QUICK_START.md`

## Planned Features

- [ ] Automated repricing based on competition
- [ ] Buy Box tracking and alerts
- [ ] Review monitoring and sentiment analysis
- [ ] PPC campaign optimization
- [ ] Multi-marketplace support (EU, UK, CA)
