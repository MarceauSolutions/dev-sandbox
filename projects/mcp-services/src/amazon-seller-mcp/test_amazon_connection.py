#!/usr/bin/env python3
"""
Test Amazon SP-API connection and diagnose authentication issues.
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("Amazon SP-API Connection Test")
print("=" * 60)

# Check credentials
print("\n✓ Checking .env credentials...")
creds = {
    'AMAZON_REFRESH_TOKEN': os.getenv('AMAZON_REFRESH_TOKEN'),
    'AMAZON_LWA_APP_ID': os.getenv('AMAZON_LWA_APP_ID'),
    'AMAZON_LWA_CLIENT_SECRET': os.getenv('AMAZON_LWA_CLIENT_SECRET'),
    'AMAZON_AWS_ACCESS_KEY': os.getenv('AMAZON_AWS_ACCESS_KEY'),
    'AMAZON_AWS_SECRET_KEY': os.getenv('AMAZON_AWS_SECRET_KEY'),
    'AMAZON_ROLE_ARN': os.getenv('AMAZON_ROLE_ARN'),
    'AMAZON_MARKETPLACE_ID': os.getenv('AMAZON_MARKETPLACE_ID', 'ATVPDKIKX0DER'),
}

for key, value in creds.items():
    if value:
        # Show first 10 chars for security
        masked = value[:10] + "..." if len(value) > 10 else value
        print(f"  ✓ {key}: {masked}")
    else:
        print(f"  ✗ {key}: MISSING")

# Try to initialize API
print("\n✓ Testing SP-API connection...")
try:
    from amazon_sp_api import AmazonSPAPI

    api = AmazonSPAPI()
    print(f"  ✓ API initialized successfully")
    print(f"  ✓ Marketplace: {api.marketplace.marketplace_id}")

    # Try a simple API call
    print("\n✓ Testing API call (get_orders)...")
    orders = api.get_orders(days_back=7, use_cache=False)

    if orders is not None:
        print(f"  ✓ API call successful!")
        print(f"  ✓ Retrieved {len(orders)} orders")
    else:
        print("  ⚠ API call returned None (may indicate auth issue)")

except Exception as e:
    print(f"  ✗ Error: {e}")
    print("\nDiagnosis:")
    print("  - Your refresh token may be expired or revoked")
    print("  - You may need to regenerate it using:")
    print("    python execution/amazon_get_refresh_token.py")

print("\n" + "=" * 60)
