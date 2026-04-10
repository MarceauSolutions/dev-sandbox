#!/usr/bin/env python3
"""
Manually refresh Amazon SP-API access token using the refresh token.
This can help diagnose token issues.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

print("Amazon SP-API Token Refresh")
print("=" * 60)

# Get credentials
refresh_token = os.getenv('AMAZON_REFRESH_TOKEN')
lwa_app_id = os.getenv('AMAZON_LWA_APP_ID')
lwa_client_secret = os.getenv('AMAZON_LWA_CLIENT_SECRET')

if not all([refresh_token, lwa_app_id, lwa_client_secret]):
    print("✗ Missing required credentials in .env")
    exit(1)

# LWA token endpoint
token_url = "https://api.amazon.com/auth/o2/token"

# Request new access token
payload = {
    'grant_type': 'refresh_token',
    'refresh_token': refresh_token,
    'client_id': lwa_app_id,
    'client_secret': lwa_client_secret,
}

print("\n→ Requesting new access token from Amazon LWA...")
try:
    response = requests.post(token_url, data=payload)

    if response.status_code == 200:
        token_data = response.json()
        print("✓ Successfully obtained new access token!")
        print(f"\nToken Details:")
        print(f"  • Access Token: {token_data.get('access_token', '')[:20]}...")
        print(f"  • Token Type: {token_data.get('token_type')}")
        print(f"  • Expires In: {token_data.get('expires_in')} seconds")

        if 'refresh_token' in token_data:
            print(f"  • New Refresh Token: {token_data.get('refresh_token')[:20]}...")
            print("\n⚠ Note: If a new refresh token was provided, update your .env file")

        print("\n✓ Your refresh token is valid!")
        print("  The sp-api library should handle token refresh automatically.")

    else:
        print(f"✗ Token refresh failed!")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text}")

        if response.status_code == 400:
            error_data = response.json()
            if error_data.get('error') == 'invalid_grant':
                print("\n⚠ Your refresh token is invalid or expired!")
                print("  You need to regenerate it using:")
                print("    python execution/amazon_get_refresh_token.py")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
