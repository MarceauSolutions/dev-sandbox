"""
LinkedIn Company Page OAuth 2.0 Authentication Flow
For posting to Marceau Solutions LLC company page via Community Management API
"""

import os
import requests
import webbrowser
from urllib.parse import urlencode, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv, set_key
from pathlib import Path

# Load environment variables
load_dotenv()

# OAuth configuration for COMPANY POSTING APP
# This is the SECOND app (Marceau Solutions Company Posting)
CLIENT_ID = os.getenv("LINKEDIN_COMPANY_CLIENT_ID")  # Will be: 78gy4q6d5k2e3d
CLIENT_SECRET = os.getenv("LINKEDIN_COMPANY_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"

# Scopes for company page posting (Community Management API)
SCOPE = "w_organization_social r_organization_social"

# Will store auth code from callback
auth_code = None


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP server to handle OAuth callback."""

    def do_GET(self):
        """Handle GET request from LinkedIn OAuth redirect."""
        global auth_code

        # Parse query parameters
        query = parse_qs(self.path.split('?')[1])

        if 'code' in query:
            auth_code = query['code'][0]

            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        else:
            # Error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                <h1>Authorization Failed</h1>
                <p>No authorization code received.</p>
                </body>
                </html>
            """)

    def log_message(self, format, *args):
        """Suppress server log messages."""
        pass


def get_authorization_code():
    """Step 1: Get authorization code via browser."""
    global auth_code

    # Build authorization URL
    auth_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE
    }

    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(auth_params)}"

    print("🌐 Opening browser for LinkedIn authorization...")
    print(f"If browser doesn't open, visit: {auth_url}\n")

    # Open browser
    webbrowser.open(auth_url)

    # Start local server to handle callback
    print("⏳ Waiting for authorization (listening on http://localhost:8000)...")
    server = HTTPServer(('localhost', 8000), OAuthCallbackHandler)
    server.handle_request()  # Handle one request then stop

    if auth_code:
        print("✅ Authorization code received")
        return auth_code
    else:
        raise Exception("Failed to get authorization code")


def exchange_code_for_tokens(code):
    """Step 2: Exchange authorization code for access token."""

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"

    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    response = requests.post(token_url, data=payload)

    if response.status_code != 200:
        raise Exception(f"Token exchange failed: {response.text}")

    tokens = response.json()

    access_token = tokens.get('access_token')
    expires_in = tokens.get('expires_in')  # Usually 60 days

    print(f"✅ Access token received (expires in {expires_in} seconds / {expires_in // 86400} days)")

    return access_token


def save_tokens_to_env(access_token):
    """Save tokens to .env file."""

    env_path = Path("/Users/williammarceaujr./dev-sandbox/.env")

    set_key(env_path, "LINKEDIN_COMPANY_ACCESS_TOKEN", access_token)

    print(f"✅ Saved LINKEDIN_COMPANY_ACCESS_TOKEN to {env_path}")


def main():
    """Run OAuth flow to get LinkedIn company posting access token."""

    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Error: LINKEDIN_COMPANY_CLIENT_ID and LINKEDIN_COMPANY_CLIENT_SECRET must be set in .env")
        print("\nSteps to fix:")
        print("1. Go to https://www.linkedin.com/developers/apps/")
        print("2. Open 'Marceau Solutions Company Posting' app")
        print("3. Go to Auth tab")
        print("4. Copy Client ID and Client Secret")
        print("5. Add to .env file:")
        print("   LINKEDIN_COMPANY_CLIENT_ID=\"78gy4q6d5k2e3d\"")
        print("   LINKEDIN_COMPANY_CLIENT_SECRET=\"your_client_secret\"")
        return

    print("🔐 LinkedIn Company Page OAuth 2.0 Authentication Flow\n")
    print("📄 App: Marceau Solutions Company Posting")
    print("🏢 Company Page: https://www.linkedin.com/company/marceau-solutions-llc/")
    print("🔑 Scopes: w_organization_social r_organization_social\n")

    try:
        # Step 1: Get authorization code
        code = get_authorization_code()

        # Step 2: Exchange for access token
        access_token = exchange_code_for_tokens(code)

        # Step 3: Save to .env
        save_tokens_to_env(access_token)

        print("\n✅ LinkedIn company page authentication complete!")
        print("\nNext steps:")
        print("1. Get organization ID: python -m src.linkedin_company_api get-org-id")
        print("2. Test posting: python -m src.linkedin_company_api test")

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")


if __name__ == "__main__":
    main()
