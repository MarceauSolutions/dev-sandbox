#!/usr/bin/env python3
"""
Amazon SP-API OAuth Server

This script starts a local web server to handle the OAuth callback and automatically
exchange the authorization code for a refresh token.

Usage:
    python execution/amazon_oauth_server.py
"""

import os
import sys
import requests
import secrets
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

# SP-API Configuration
LWA_APP_ID = os.getenv('AMAZON_LWA_APP_ID')
LWA_CLIENT_SECRET = os.getenv('AMAZON_LWA_CLIENT_SECRET')
LWA_TOKEN_URL = 'https://api.amazon.com/auth/o2/token'
AUTHORIZATION_URL = 'https://sellercentral.amazon.com/apps/authorize/consent'

# Local server configuration
REDIRECT_URI = 'http://localhost:3000/callback'
PORT = 3000

# Global state
oauth_state = None
auth_code = None
server_running = True


class OAuthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback"""

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

    def do_GET(self):
        """Handle GET requests from Amazon OAuth redirect"""
        global auth_code, server_running

        parsed_path = urlparse(self.path)

        if parsed_path.path == '/callback':
            # Parse query parameters
            params = parse_qs(parsed_path.query)

            returned_code = params.get('spapi_oauth_code', [None])[0]
            returned_state = params.get('state', [None])[0]
            error = params.get('error', [None])[0]

            if error:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html = f"""
                <html>
                <head><title>Authorization Failed</title></head>
                <body style="font-family: Arial; padding: 50px; text-align: center;">
                    <h1 style="color: #d32f2f;">❌ Authorization Failed</h1>
                    <p>Error: {error}</p>
                    <p>You can close this window and check the terminal for details.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())
                server_running = False
                return

            if not returned_code:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html = """
                <html>
                <head><title>Missing Code</title></head>
                <body style="font-family: Arial; padding: 50px; text-align: center;">
                    <h1 style="color: #d32f2f;">❌ Missing Authorization Code</h1>
                    <p>No authorization code was received from Amazon.</p>
                    <p>You can close this window and try again.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())
                server_running = False
                return

            if returned_state != oauth_state:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html = """
                <html>
                <head><title>Security Error</title></head>
                <body style="font-family: Arial; padding: 50px; text-align: center;">
                    <h1 style="color: #d32f2f;">⚠️ Security Error</h1>
                    <p>State parameter mismatch. Possible CSRF attack.</p>
                    <p>You can close this window and try again.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())
                server_running = False
                return

            # Success! Store the auth code
            auth_code = returned_code

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html>
            <head><title>Authorization Successful</title></head>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1 style="color: #4caf50;">✓ Authorization Successful!</h1>
                <p>Your Amazon SP-API app has been authorized.</p>
                <p>Please return to the terminal to complete the setup.</p>
                <p style="color: #666; margin-top: 30px;">You can close this window now.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            server_running = False

        else:
            # Unknown path
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html>
            <head><title>Not Found</title></head>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1>404 - Not Found</h1>
            </body>
            </html>
            """
            self.wfile.write(html.encode())


def generate_authorization_url():
    """Generate the authorization URL with localhost redirect"""
    global oauth_state

    if not LWA_APP_ID:
        print("❌ ERROR: AMAZON_LWA_APP_ID not found in .env file")
        sys.exit(1)

    oauth_state = secrets.token_urlsafe(32)

    params = {
        'application_id': LWA_APP_ID,
        'redirect_uri': REDIRECT_URI,
        'state': oauth_state,
        'version': 'beta'
    }

    return f"{AUTHORIZATION_URL}?{urlencode(params)}"


def exchange_code_for_token(code):
    """Exchange the authorization code for a refresh token"""

    if not LWA_APP_ID or not LWA_CLIENT_SECRET:
        print("❌ ERROR: LWA credentials not found in .env file")
        sys.exit(1)

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': LWA_APP_ID,
        'client_secret': LWA_CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI
    }

    try:
        print("→ Exchanging authorization code for refresh token...")
        response = requests.post(LWA_TOKEN_URL, data=data)
        response.raise_for_status()
        token_data = response.json()

        return token_data.get('refresh_token'), token_data.get('access_token')

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR exchanging code for token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)


def update_env_file(refresh_token):
    """Update the .env file with the refresh token"""

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
    print("Amazon SP-API OAuth Server")
    print("=" * 70)
    print()

    # Step 1: Start local server
    print("STEP 1: Starting Local OAuth Server")
    print("-" * 70)
    print(f"Starting server on {REDIRECT_URI}...")

    server = HTTPServer(('localhost', PORT), OAuthHandler)
    print(f"✓ Server running on port {PORT}")
    print()

    # Step 2: Generate authorization URL
    print("STEP 2: Authorization")
    print("-" * 70)
    auth_url = generate_authorization_url()

    print("Opening authorization URL in your browser...")
    print()
    print("If the browser doesn't open automatically, visit this URL:")
    print(auth_url)
    print()
    print("→ Please authorize the app in your browser")
    print("→ You'll be redirected back to localhost automatically")
    print("-" * 70)
    print()

    # Open browser
    try:
        webbrowser.open(auth_url)
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print("Please copy and paste the URL above into your browser.")
        print()

    # Step 3: Wait for callback
    print("Waiting for authorization callback...")
    print("(Press Ctrl+C to cancel)")
    print()

    try:
        while server_running:
            server.handle_request()
    except KeyboardInterrupt:
        print("\n\n❌ Authorization cancelled by user")
        sys.exit(0)

    if not auth_code:
        print("\n❌ ERROR: No authorization code received")
        sys.exit(1)

    print(f"✓ Received authorization code: {auth_code[:20]}...")
    print()

    # Step 4: Exchange code for refresh token
    print("STEP 3: Exchange for Refresh Token")
    print("-" * 70)

    refresh_token, access_token = exchange_code_for_token(auth_code)

    if not refresh_token:
        print("❌ ERROR: Did not receive a refresh token")
        sys.exit(1)

    print(f"✓ Received refresh token: {refresh_token[:20]}...")
    print(f"✓ Received access token: {access_token[:20]}...")
    print()

    # Step 5: Update .env file
    print("STEP 4: Update .env File")
    print("-" * 70)

    if update_env_file(refresh_token):
        print()
        print("=" * 70)
        print("✓ SUCCESS! Your Amazon SP-API is now fully configured!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Test the connection:")
        print("     python execution/amazon_sp_api.py")
        print()
        print("  2. Run inventory optimization:")
        print("     python execution/amazon_inventory_optimizer.py")
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
