# Amazon Seller Operations AI Assistant

AI-powered Amazon Seller Central automation for inventory management, fee calculation, and listing optimization via SP-API.

## Status: Development

## Features

| Feature | Script | Description |
|---------|--------|-------------|
| SP-API Integration | `amazon_sp_api.py` | Core Amazon API client |
| Fee Calculator | `amazon_fee_calculator.py` | Calculate FBA fees and margins |
| Inventory Optimizer | `amazon_inventory_optimizer.py` | Restock recommendations |
| OAuth Server | `amazon_oauth_server.py` | Handle SP-API authentication |
| Auth Setup | `setup_amazon_auth.py` | Initial credential configuration |

## Directory Structure

```
amazon-seller/
├── src/
│   ├── amazon_sp_api.py
│   ├── amazon_fee_calculator.py
│   ├── amazon_inventory_optimizer.py
│   ├── amazon_oauth_server.py
│   └── setup_amazon_auth.py
├── docs/
└── README.md
```

## Environment Variables

```env
AMAZON_SELLER_ID=your_seller_id
AMAZON_MARKETPLACE_ID=ATVPDKIKX0DER  # US marketplace
AMAZON_CLIENT_ID=your_client_id
AMAZON_CLIENT_SECRET=your_client_secret
AMAZON_REFRESH_TOKEN=your_refresh_token
```

## Skill Configuration

Located at: `.claude/skills/amazon-seller-operations/SKILL.md`

## Related Documentation

- Main directive: `directives/amazon_seller_operations.md`
- Setup guide: `docs/AMAZON_SETUP.md`
