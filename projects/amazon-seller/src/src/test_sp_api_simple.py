#!/usr/bin/env python3
"""
Simple test of sp-api library with direct credentials.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from sp_api.api import Orders
from sp_api.base import Marketplaces
from datetime import datetime, timedelta

print("Testing SP-API Library Directly")
print("=" * 60)

# Build credentials dict
credentials = {
    'refresh_token': os.getenv('AMAZON_REFRESH_TOKEN'),
    'lwa_app_id': os.getenv('AMAZON_LWA_APP_ID'),
    'lwa_client_secret': os.getenv('AMAZON_LWA_CLIENT_SECRET'),
    'aws_access_key': os.getenv('AMAZON_AWS_ACCESS_KEY'),
    'aws_secret_key': os.getenv('AMAZON_AWS_SECRET_KEY'),
    'role_arn': os.getenv('AMAZON_ROLE_ARN'),
}

print("\n→ Credentials loaded:")
for key in credentials:
    val = credentials[key]
    if val:
        print(f"  ✓ {key}: {val[:15]}...")
    else:
        print(f"  ✗ {key}: MISSING")

print("\n→ Creating Orders API instance...")
try:
    orders_api = Orders(
        credentials=credentials,
        marketplace=Marketplaces.US
    )
    print("  ✓ Orders API created")

    # Try to get orders
    print("\n→ Fetching orders from last 7 days...")
    created_after = (datetime.now() - timedelta(days=7)).isoformat()

    result = orders_api.get_orders(
        CreatedAfter=created_after,
        MarketplaceIds=[Marketplaces.US.marketplace_id]
    )

    print(f"  ✓ API call successful!")
    print(f"  Result type: {type(result)}")
    print(f"  Has payload: {hasattr(result, 'payload')}")

    if hasattr(result, 'payload'):
        orders = result.payload.get('Orders', [])
        print(f"  ✓ Retrieved {len(orders)} orders")
    else:
        print(f"  Result: {result}")

except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
