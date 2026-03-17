#!/usr/bin/env python3
"""
ClickUp OAuth Authentication Flow

This script handles the OAuth flow to get an access token using Client ID and Secret.

Usage:
    python clickup_oauth.py
"""

import requests
import os
from dotenv import load_dotenv
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser
import threading

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv('CLICKUP_CLIENT_ID')
CLIENT_SECRET = os.getenv('CLICKUP_CLIENT_SECRET')
REDIRECT_URI = "http://localhost:8080/oauth/callback"

# Store the authorization code
auth_code = None
server_running = True


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""

    def do_GET(self):
        global auth_code, server_running

        # Parse the authorization code from the callback
        query_components = parse_qs(urlparse(self.path).query)

        if 'code' in query_components:
            auth_code = query_components['code'][0]

            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to your terminal.</p>
                </body>
                </html>
            """)

            # Stop the server
            server_running = False
        else:
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
        """Suppress log messages"""
        pass


def start_oauth_flow():
    """Start the OAuth authorization flow"""

    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Error: CLICKUP_CLIENT_ID and CLICKUP_CLIENT_SECRET must be set in .env file")
        return None

    # Step 1: Build authorization URL
    auth_url = f"https://app.clickup.com/api?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"

    print("🔐 Starting ClickUp OAuth flow...")
    print(f"\n📋 Client ID: {CLIENT_ID}")
    print(f"📋 Redirect URI: {REDIRECT_URI}")
    print("\n⏳ Opening browser for authorization...")
    print(f"\nIf the browser doesn't open automatically, visit this URL:")
    print(f"\n{auth_url}\n")

    # Step 2: Start local server to receive callback
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)

    # Open browser
    webbrowser.open(auth_url)

    # Wait for callback
    print("⏳ Waiting for authorization... (authorize in your browser)")

    while server_running:
        server.handle_request()

    if not auth_code:
        print("❌ Failed to get authorization code")
        return None

    print(f"\n✅ Authorization code received!")

    # Step 3: Exchange code for access token
    print("🔄 Exchanging code for access token...")

    token_url = "https://api.clickup.com/api/v2/oauth/token"

    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code
    }

    try:
        response = requests.post(token_url, json=payload)
        response.raise_for_status()

        token_data = response.json()
        access_token = token_data.get('access_token')

        if access_token:
            print("\n✅ Access token obtained successfully!")
            print(f"\n📝 Add this to your .env file:")
            print(f"\nCLICKUP_API_TOKEN={access_token}")

            # Optionally save to .env
            print("\n💾 Would you like to automatically add this to your .env file? (y/n)")
            choice = input().strip().lower()

            if choice == 'y':
                env_path = '.env'
                with open(env_path, 'r') as f:
                    env_contents = f.read()

                # Replace or add the token
                if 'CLICKUP_API_TOKEN=' in env_contents:
                    # Replace existing
                    lines = env_contents.split('\n')
                    new_lines = []
                    for line in lines:
                        if line.startswith('CLICKUP_API_TOKEN='):
                            new_lines.append(f'CLICKUP_API_TOKEN={access_token}')
                        else:
                            new_lines.append(line)
                    env_contents = '\n'.join(new_lines)
                else:
                    # Add new
                    env_contents += f'\nCLICKUP_API_TOKEN={access_token}\n'

                with open(env_path, 'w') as f:
                    f.write(env_contents)

                print(f"✅ Token saved to {env_path}")

            return access_token
        else:
            print("❌ No access token in response")
            print(f"Response: {token_data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting access token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("ClickUp OAuth Authentication")
    print("=" * 60)

    access_token = start_oauth_flow()

    if access_token:
        print("\n" + "=" * 60)
        print("🎉 Setup Complete!")
        print("=" * 60)
        print("\nYou can now use the ClickUp API with your access token.")
        print("Test it by running:")
        print("  python execution/clickup_api.py list-workspaces")
    else:
        print("\n❌ OAuth flow failed. Please try again.")
