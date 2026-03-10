#!/usr/bin/env python3
"""
TikTok OAuth Credential Generator (with PKCE)

Run this script to get your TIKTOK_ACCESS_TOKEN and TIKTOK_REFRESH_TOKEN.
It will open a browser for TikTok authentication.
"""

import os
import webbrowser
import secrets
import hashlib
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import requests

# Load from environment or use defaults
CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY', 'awztj4k9iysxawwy')
CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET', 'Ca7BQ5gUFcfls2vc1piJTMePkVRt2F6T')
REDIRECT_URI = 'http://localhost:8080/callback'

# Scopes needed for TikTok Content Posting API
SCOPES = 'user.info.basic,video.upload,video.list'


def generate_code_verifier():
    """Generate a code verifier for PKCE."""
    return secrets.token_urlsafe(32)


def generate_code_challenge(verifier):
    """Generate a code challenge from the verifier using S256."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode()


class OAuthHandler(BaseHTTPRequestHandler):
    """Handle the OAuth callback."""

    def do_GET(self):
        """Handle GET request from TikTok OAuth redirect."""
        parsed = urlparse(self.path)

        if parsed.path == '/callback':
            query_params = parse_qs(parsed.query)

            if 'code' in query_params:
                auth_code = query_params['code'][0]
                self.server.auth_code = auth_code

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'''
                    <html>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1>Authorization Successful!</h1>
                        <p>You can close this window and return to the terminal.</p>
                    </body>
                    </html>
                ''')
            else:
                error = query_params.get('error', ['Unknown error'])[0]
                error_desc = query_params.get('error_description', [''])[0]
                self.server.auth_code = None

                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f'''
                    <html>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1>Authorization Failed</h1>
                        <p>Error: {error}</p>
                        <p>{error_desc}</p>
                    </body>
                    </html>
                '''.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress logging."""
        pass


def get_auth_url(code_challenge):
    """Build the TikTok authorization URL with PKCE."""
    params = {
        'client_key': CLIENT_KEY,
        'response_type': 'code',
        'scope': SCOPES,
        'redirect_uri': REDIRECT_URI,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    return f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"


def exchange_code_for_token(auth_code, code_verifier):
    """Exchange authorization code for access token with PKCE."""
    response = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'client_key': CLIENT_KEY,
            'client_secret': CLIENT_SECRET,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'code_verifier': code_verifier,
        }
    )
    return response.json()


def main():
    print("="*60)
    print("TikTok OAuth Credential Generator (with PKCE)")
    print("="*60)
    print()
    print(f"Client Key: {CLIENT_KEY}")
    print(f"Redirect URI: {REDIRECT_URI}")
    print()

    # Generate PKCE codes
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    print(f"Generated PKCE code verifier and challenge")
    print()

    # Build auth URL
    auth_url = get_auth_url(code_challenge)

    print("Opening browser for TikTok authorization...")
    print()
    print("If the browser doesn't open, visit this URL manually:")
    print(auth_url)
    print()

    # Open browser
    webbrowser.open(auth_url)

    # Start local server to receive callback
    print("Waiting for authorization callback...")
    server = HTTPServer(('localhost', 8080), OAuthHandler)
    server.auth_code = None
    server.handle_request()  # Handle single request

    if server.auth_code:
        print()
        print("Authorization code received! Exchanging for tokens...")
        print()

        # Exchange code for tokens
        token_response = exchange_code_for_token(server.auth_code, code_verifier)

        if 'access_token' in token_response:
            print("="*60)
            print("SUCCESS! Here are your credentials:")
            print("="*60)
            print()
            print("Add these to your .env file:")
            print()
            print(f'TIKTOK_ACCESS_TOKEN={token_response["access_token"]}')
            print(f'TIKTOK_REFRESH_TOKEN={token_response.get("refresh_token", "")}')
            print()
            print(f'Token expires in: {token_response.get("expires_in", "unknown")} seconds')
            print(f'Refresh token expires in: {token_response.get("refresh_expires_in", "unknown")} seconds')
            print()
            print("="*60)
        else:
            print("ERROR: Failed to get tokens")
            print(f"Response: {token_response}")
    else:
        print("ERROR: No authorization code received")


if __name__ == "__main__":
    main()
