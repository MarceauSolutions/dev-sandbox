#!/usr/bin/env python3
"""
Interactive Amazon SP-API Authentication Setup
Diagnoses issues and guides you through fixing them.
"""

import os
import sys
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def print_step(num, text):
    """Print a step number."""
    print(f"\n[Step {num}] {text}")
    print("-" * 70)

def check_env_credentials():
    """Check if all required credentials are in .env"""
    print_step(1, "Checking .env Credentials")

    required = {
        'AMAZON_REFRESH_TOKEN': None,
        'AMAZON_LWA_APP_ID': None,
        'AMAZON_LWA_CLIENT_SECRET': None,
        'AMAZON_AWS_ACCESS_KEY': None,
        'AMAZON_AWS_SECRET_KEY': None,
        'AMAZON_ROLE_ARN': None,
        'AMAZON_MARKETPLACE_ID': 'ATVPDKIKX0DER',  # Optional, has default
    }

    all_present = True
    for key, default in required.items():
        value = os.getenv(key, default)
        if value:
            masked = value[:15] + "..." if len(value) > 15 else value
            print(f"  ✅ {key}: {masked}")
        else:
            print(f"  ❌ {key}: MISSING")
            all_present = False

    if not all_present:
        print("\n⚠️  Some credentials are missing!")
        print("  Add them to your .env file")
        print("  See docs/AMAZON_SETUP.md for how to get them")
        return False

    print("\n✅ All credentials present in .env")
    return True

def test_token_refresh():
    """Test if refresh token can generate new access tokens."""
    print_step(2, "Testing Token Refresh")

    refresh_token = os.getenv('AMAZON_REFRESH_TOKEN')
    lwa_app_id = os.getenv('AMAZON_LWA_APP_ID')
    lwa_client_secret = os.getenv('AMAZON_LWA_CLIENT_SECRET')

    if not all([refresh_token, lwa_app_id, lwa_client_secret]):
        print("❌ Missing LWA credentials, skipping test")
        return False

    token_url = "https://api.amazon.com/auth/o2/token"
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': lwa_app_id,
        'client_secret': lwa_client_secret,
    }

    try:
        print("  → Requesting new access token...")
        response = requests.post(token_url, data=payload, timeout=10)

        if response.status_code == 200:
            token_data = response.json()
            print(f"  ✅ Token refresh successful!")
            print(f"     Access token: {token_data.get('access_token', '')[:20]}...")
            print(f"     Expires in: {token_data.get('expires_in')} seconds")

            if 'refresh_token' in token_data:
                new_refresh = token_data.get('refresh_token')
                print(f"\n  ⚠️  Amazon provided a NEW refresh token!")
                print(f"     New token: {new_refresh[:20]}...")
                print(f"\n  ACTION REQUIRED:")
                print(f"     Update your .env file with:")
                print(f"     AMAZON_REFRESH_TOKEN={new_refresh}")

            return True

        else:
            print(f"  ❌ Token refresh failed!")
            print(f"     Status: {response.status_code}")
            print(f"     Error: {response.json()}")

            if response.status_code == 400:
                error = response.json().get('error')
                if error == 'invalid_grant':
                    print("\n  🔧 FIX: Your refresh token is expired/revoked")
                    print("     You need to re-authorize your app:")
                    print("     1. Run: python execution/amazon_get_refresh_token.py")
                    print("     2. Or visit your app authorization URL")

            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_sp_api_connection():
    """Test actual SP-API connection."""
    print_step(3, "Testing SP-API Connection")

    try:
        from sp_api.api import Orders
        from sp_api.base import Marketplaces
        from datetime import datetime, timedelta

        credentials = {
            'refresh_token': os.getenv('AMAZON_REFRESH_TOKEN'),
            'lwa_app_id': os.getenv('AMAZON_LWA_APP_ID'),
            'lwa_client_secret': os.getenv('AMAZON_LWA_CLIENT_SECRET'),
            'aws_access_key': os.getenv('AMAZON_AWS_ACCESS_KEY'),
            'aws_secret_key': os.getenv('AMAZON_AWS_SECRET_KEY'),
            'role_arn': os.getenv('AMAZON_ROLE_ARN'),
        }

        print("  → Creating Orders API client...")
        orders_api = Orders(credentials=credentials, marketplace=Marketplaces.US)

        print("  → Attempting to fetch orders...")
        created_after = (datetime.now() - timedelta(days=7)).isoformat()

        result = orders_api.get_orders(
            CreatedAfter=created_after,
            MarketplaceIds=[Marketplaces.US.marketplace_id]
        )

        print("  ✅ SP-API connection successful!")
        orders = result.payload.get('Orders', []) if hasattr(result, 'payload') else []
        print(f"     Retrieved {len(orders)} orders from last 7 days")
        return True

    except Exception as e:
        error_str = str(e)
        print(f"  ❌ SP-API connection failed!")
        print(f"     Error: {error_str}")

        if 'Unauthorized' in error_str or 'access token' in error_str.lower():
            print("\n  🔧 DIAGNOSIS: Authorization Issue")
            print("     Possible causes:")
            print("     1. App needs re-authorization in Seller Central")
            print("     2. IAM role ARN is incorrect")
            print("     3. IAM role doesn't have proper trust policy")
            print("\n  📋 RECOMMENDED FIXES:")
            print("     Option A - Re-authorize app:")
            print("       Run: python execution/amazon_get_refresh_token.py")
            print("\n     Option B - Check IAM role:")
            print("       1. Go to AWS IAM Console")
            print("       2. Find role in AMAZON_ROLE_ARN")
            print("       3. Check 'Trust relationships' tab")
            print("       4. Verify it trusts Amazon's SP-API principal")
            print("\n     See: .claude/AMAZON_AUTH_SETUP.md for detailed steps")

        elif 'Invalid signature' in error_str:
            print("\n  🔧 DIAGNOSIS: AWS Credentials Issue")
            print("     Your AWS access keys are invalid or lack permissions")
            print("\n  📋 RECOMMENDED FIX:")
            print("     1. Verify keys in .env are correct")
            print("     2. Check IAM user has 'sts:AssumeRole' permission")

        return False

def main():
    print_header("Amazon SP-API Authentication Setup & Diagnosis")

    print("This tool will:")
    print("  1. Check your .env credentials")
    print("  2. Test token refresh capability")
    print("  3. Test SP-API connection")
    print("  4. Provide specific fix instructions if needed")

    # Step 1: Check credentials
    if not check_env_credentials():
        print("\n❌ Setup cannot continue without credentials")
        print("   Add missing credentials to .env and run again")
        return 1

    # Step 2: Test token refresh
    token_works = test_token_refresh()

    # Step 3: Test SP-API
    api_works = test_sp_api_connection()

    # Summary
    print_header("Summary")

    if token_works and api_works:
        print("🎉 SUCCESS! Everything is configured correctly!")
        print("\nYou can now use:")
        print("  python execution/amazon_inventory_optimizer.py --asin YOUR_ASIN")
        return 0

    elif token_works and not api_works:
        print("⚠️  Token refresh works, but SP-API calls fail")
        print("\nThis usually means:")
        print("  • IAM role configuration issue")
        print("  • App not authorized in Seller Central")
        print("\nNext steps:")
        print("  1. Read: .claude/AMAZON_AUTH_SETUP.md")
        print("  2. Try: python execution/amazon_get_refresh_token.py")
        return 1

    elif not token_works:
        print("❌ Token refresh failed")
        print("\nYour refresh token is invalid/expired")
        print("\nNext steps:")
        print("  1. Run: python execution/amazon_get_refresh_token.py")
        print("  2. Follow prompts to re-authorize")
        print("  3. Update .env with new refresh token")
        return 1

    else:
        print("❌ Multiple issues detected")
        print("\nSee error messages above for specific fixes")
        print("Or read: .claude/AMAZON_AUTH_SETUP.md")
        return 1

if __name__ == "__main__":
    exit(main())
