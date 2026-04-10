#!/usr/bin/env python3
"""
Amazon SP-API Refresh Token Generator

This script helps you generate a refresh token for Amazon SP-API by:
1. Generating an authorization URL for you to visit
2. Accepting the authorization code from the redirect
3. Exchanging it for a refresh token
4. Automatically updating your .env file

Usage:
    python execution/amazon_get_refresh_token.py
"""

import os
import sys
import requests
import secrets
from urllib.parse import urlencode, parse_qs, urlparse
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

# SP-API Configuration
LWA_APP_ID = os.getenv('AMAZON_LWA_APP_ID')
LWA_CLIENT_SECRET = os.getenv('AMAZON_LWA_CLIENT_SECRET')
LWA_TOKEN_URL = 'https://api.amazon.com/auth/o2/token'

# Authorization endpoint
AUTHORIZATION_URL = 'https://sellercentral.amazon.com/apps/authorize/consent'

def generate_authorization_url():
    """Generate the authorization URL for the user to visit."""

    if not LWA_APP_ID:
        print("❌ ERROR: AMAZON_LWA_APP_ID not found in .env file")
        sys.exit(1)

    # Generate a random state for CSRF protection
    state = secrets.token_urlsafe(32)

    params = {
        'application_id': LWA_APP_ID,
        'state': state,
        'version': 'beta'
    }

    auth_url = f"{AUTHORIZATION_URL}?{urlencode(params)}"

    return auth_url, state

def exchange_code_for_token(auth_code):
    """Exchange the authorization code for a refresh token."""

    if not LWA_APP_ID or not LWA_CLIENT_SECRET:
        print("❌ ERROR: LWA credentials not found in .env file")
        sys.exit(1)

    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'client_id': LWA_APP_ID,
        'client_secret': LWA_CLIENT_SECRET
    }

    try:
        response = requests.post(LWA_TOKEN_URL, data=data)
        response.raise_for_status()
        token_data = response.json()

        return token_data.get('refresh_token')

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR exchanging code for token: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        sys.exit(1)

def update_env_file(refresh_token):
    """Update the .env file with the refresh token."""

    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

    try:
        set_key(env_path, 'AMAZON_REFRESH_TOKEN', refresh_token)
        print(f"✓ Updated {env_path} with refresh token")
        return True
    except Exception as e:
        print(f"❌ ERROR updating .env file: {e}")
        return False

def main():
    print("=" * 70)
    print("Amazon SP-API Refresh Token Generator")
    print("=" * 70)
    print()

    # Step 1: Generate authorization URL
    print("STEP 1: Authorization")
    print("-" * 70)
    auth_url, state = generate_authorization_url()

    print("Please visit this URL in your browser to authorize the app:")
    print()
    print(auth_url)
    print()
    print("After you authorize, you'll be redirected to a URL that looks like:")
    print("https://example.com/?spapi_oauth_code=XXXXXX&state=YYYYYY")
    print()
    print("(The redirect might show an error page - that's OK! We just need the URL)")
    print("-" * 70)
    print()

    # Step 2: Get the authorization code
    print("STEP 2: Authorization Code")
    print("-" * 70)

    while True:
        redirect_url = input("Paste the FULL redirect URL here: ").strip()

        if not redirect_url:
            print("❌ Please provide a redirect URL")
            continue

        try:
            parsed = urlparse(redirect_url)
            params = parse_qs(parsed.query)

            auth_code = params.get('spapi_oauth_code', [None])[0]
            returned_state = params.get('state', [None])[0]

            if not auth_code:
                print("❌ Could not find 'spapi_oauth_code' in the URL")
                print("   Make sure you copied the complete redirect URL")
                continue

            if returned_state != state:
                print("⚠️  WARNING: State parameter doesn't match (possible security issue)")
                confirm = input("Continue anyway? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("Aborting.")
                    sys.exit(0)

            break

        except Exception as e:
            print(f"❌ Error parsing URL: {e}")
            continue

    print(f"✓ Found authorization code: {auth_code[:20]}...")
    print()

    # Step 3: Exchange code for refresh token
    print("STEP 3: Exchange for Refresh Token")
    print("-" * 70)
    print("Exchanging authorization code for refresh token...")

    refresh_token = exchange_code_for_token(auth_code)

    if not refresh_token:
        print("❌ ERROR: Did not receive a refresh token")
        sys.exit(1)

    print(f"✓ Received refresh token: {refresh_token[:20]}...")
    print()

    # Step 4: Update .env file
    print("STEP 4: Update .env File")
    print("-" * 70)

    if update_env_file(refresh_token):
        print()
        print("=" * 70)
        print("✓ SUCCESS! Your Amazon SP-API is now fully configured!")
        print("=" * 70)
        print()
        print("You can now use the Amazon SP-API wrapper:")
        print("  python execution/amazon_sp_api.py")
        print()
        print("Or run inventory optimization:")
        print("  python execution/amazon_inventory_optimizer.py")
        print()
    else:
        print()
        print("⚠️  Could not automatically update .env file")
        print("Please manually add this to your .env file:")
        print()
        print(f"AMAZON_REFRESH_TOKEN={refresh_token}")
        print()

if __name__ == '__main__':
    main()
