#!/usr/bin/env python3
"""
tiktok_auth.py - TikTok OAuth 2.0 Authentication

Handles OAuth authentication flow for TikTok Content Posting API.

Environment Variables Required:
    TIKTOK_CLIENT_KEY - TikTok App Client Key
    TIKTOK_CLIENT_SECRET - TikTok App Client Secret
    TIKTOK_REDIRECT_URI - OAuth redirect URI (default: http://localhost:8000/callback)
    TIKTOK_ACCESS_TOKEN - (generated) Access token after auth
    TIKTOK_REFRESH_TOKEN - (generated) Refresh token for renewal

Usage:
    # First-time authorization (opens browser)
    python -m src.tiktok_auth authorize

    # Refresh existing token
    python -m src.tiktok_auth refresh

    # Check token status
    python -m src.tiktok_auth status
"""

import os
import json
import time
import webbrowser
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

from dotenv import load_dotenv
load_dotenv()

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not installed. Run: pip install requests")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """TikTok OAuth token information."""
    access_token: str
    refresh_token: str
    expires_at: str  # ISO format
    scope: str
    open_id: str  # TikTok user ID
    created_at: str


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to receive OAuth callback."""

    authorization_code = None

    def do_GET(self):
        """Handle GET request with OAuth callback."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if 'code' in params:
            OAuthCallbackHandler.authorization_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
                <html>
                <head><title>TikTok Authorization Complete</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>Authorization Complete!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            ''')
        elif 'error' in params:
            error = params.get('error', ['unknown'])[0]
            error_desc = params.get('error_description', ['No description'])[0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'''
                <html>
                <head><title>TikTok Authorization Failed</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>Authorization Failed</h1>
                    <p>Error: {error}</p>
                    <p>{error_desc}</p>
                </body>
                </html>
            '''.encode())
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress HTTP server logs."""
        pass


class TikTokAuth:
    """
    TikTok OAuth 2.0 Authentication Handler.

    Implements the authorization code flow for TikTok Content Posting API.
    """

    TOKEN_FILE = Path(__file__).parent.parent / "output" / "tiktok_tokens.json"
    AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
    TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    REVOKE_URL = "https://open.tiktokapis.com/v2/oauth/revoke/"

    def __init__(
        self,
        client_key: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ):
        """
        Initialize TikTok auth handler.

        Args:
            client_key: TikTok App Client Key (or use TIKTOK_CLIENT_KEY env var)
            client_secret: TikTok App Client Secret (or use TIKTOK_CLIENT_SECRET env var)
            redirect_uri: OAuth redirect URI (default: http://localhost:8000/callback)
        """
        self.client_key = client_key or os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = client_secret or os.getenv("TIKTOK_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv(
            "TIKTOK_REDIRECT_URI",
            "http://localhost:8000/callback"
        )
        self.token_info: Optional[TokenInfo] = None

        self._validate_credentials()
        self._load_tokens()

    def _validate_credentials(self):
        """Validate that required credentials are present."""
        missing = []
        if not self.client_key:
            missing.append("TIKTOK_CLIENT_KEY")
        if not self.client_secret:
            missing.append("TIKTOK_CLIENT_SECRET")

        if missing:
            logger.warning(f"Missing TikTok credentials: {', '.join(missing)}")
            logger.info("Get credentials at https://developers.tiktok.com/")

    def _load_tokens(self):
        """Load tokens from file."""
        if self.TOKEN_FILE.exists():
            try:
                with open(self.TOKEN_FILE) as f:
                    data = json.load(f)
                self.token_info = TokenInfo(**data)
                logger.info("Loaded TikTok tokens from file")
            except Exception as e:
                logger.warning(f"Error loading TikTok tokens: {e}")

    def _save_tokens(self):
        """Save tokens to file."""
        if self.token_info:
            self.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.TOKEN_FILE, 'w') as f:
                json.dump(asdict(self.token_info), f, indent=2)
            logger.info(f"Saved TikTok tokens to {self.TOKEN_FILE}")

    def get_authorization_url(self, state: str = "random_state") -> str:
        """
        Generate OAuth authorization URL.

        Args:
            state: State parameter for CSRF protection

        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_key": self.client_key,
            "scope": "user.info.basic,video.upload,video.publish",
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": state
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Token response data
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required. Install with: pip install requests")

        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }

        response = requests.post(
            self.TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=data
        )

        result = response.json()

        if "access_token" in result:
            expires_at = datetime.now() + timedelta(seconds=result.get("expires_in", 86400))
            self.token_info = TokenInfo(
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token", ""),
                expires_at=expires_at.isoformat(),
                scope=result.get("scope", ""),
                open_id=result.get("open_id", ""),
                created_at=datetime.now().isoformat()
            )
            self._save_tokens()
            logger.info("Successfully obtained TikTok access token")
        else:
            logger.error(f"Token exchange failed: {result}")

        return result

    def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Returns:
            Token response data
        """
        if not self.token_info or not self.token_info.refresh_token:
            raise ValueError("No refresh token available. Run authorization first.")

        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required")

        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "refresh_token": self.token_info.refresh_token,
            "grant_type": "refresh_token"
        }

        response = requests.post(
            self.TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=data
        )

        result = response.json()

        if "access_token" in result:
            expires_at = datetime.now() + timedelta(seconds=result.get("expires_in", 86400))
            self.token_info = TokenInfo(
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token", self.token_info.refresh_token),
                expires_at=expires_at.isoformat(),
                scope=result.get("scope", self.token_info.scope),
                open_id=result.get("open_id", self.token_info.open_id),
                created_at=self.token_info.created_at
            )
            self._save_tokens()
            logger.info("Successfully refreshed TikTok access token")
        else:
            logger.error(f"Token refresh failed: {result}")

        return result

    def is_token_valid(self) -> bool:
        """Check if current token is valid (not expired)."""
        if not self.token_info:
            return False

        try:
            expires_at = datetime.fromisoformat(self.token_info.expires_at)
            # Consider expired if less than 5 minutes remaining
            return datetime.now() < (expires_at - timedelta(minutes=5))
        except Exception:
            return False

    def get_access_token(self) -> Optional[str]:
        """
        Get valid access token, refreshing if necessary.

        Returns:
            Access token string or None
        """
        if not self.token_info:
            return None

        if not self.is_token_valid():
            logger.info("Token expired, attempting refresh...")
            try:
                self.refresh_access_token()
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                return None

        return self.token_info.access_token

    def authorize_interactive(self, port: int = 8000) -> bool:
        """
        Run interactive OAuth flow (opens browser).

        Args:
            port: Local port for OAuth callback server

        Returns:
            True if authorization successful
        """
        if not self.client_key or not self.client_secret:
            logger.error("Missing client credentials. Set TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET")
            return False

        # Start local server for callback
        server = HTTPServer(('localhost', port), OAuthCallbackHandler)
        OAuthCallbackHandler.authorization_code = None

        # Generate authorization URL
        auth_url = self.get_authorization_url()
        logger.info(f"Opening browser for TikTok authorization...")
        logger.info(f"URL: {auth_url}")

        # Open browser
        webbrowser.open(auth_url)

        # Wait for callback (timeout after 5 minutes)
        server.timeout = 300
        logger.info("Waiting for authorization callback...")

        while OAuthCallbackHandler.authorization_code is None:
            server.handle_request()
            if OAuthCallbackHandler.authorization_code:
                break

        server.server_close()

        if OAuthCallbackHandler.authorization_code:
            logger.info("Received authorization code, exchanging for token...")
            result = self.exchange_code_for_token(OAuthCallbackHandler.authorization_code)
            return "access_token" in result
        else:
            logger.error("No authorization code received")
            return False

    def revoke_token(self) -> bool:
        """
        Revoke current access token.

        Returns:
            True if revocation successful
        """
        if not self.token_info:
            logger.warning("No token to revoke")
            return False

        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required")

        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "token": self.token_info.access_token
        }

        response = requests.post(
            self.REVOKE_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=data
        )

        if response.status_code == 200:
            logger.info("Token revoked successfully")
            self.token_info = None
            if self.TOKEN_FILE.exists():
                self.TOKEN_FILE.unlink()
            return True
        else:
            logger.error(f"Token revocation failed: {response.text}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get current authentication status."""
        if not self.token_info:
            return {
                "authenticated": False,
                "message": "Not authenticated. Run 'authorize' command."
            }

        is_valid = self.is_token_valid()
        expires_at = datetime.fromisoformat(self.token_info.expires_at)

        return {
            "authenticated": True,
            "token_valid": is_valid,
            "open_id": self.token_info.open_id,
            "scope": self.token_info.scope,
            "expires_at": self.token_info.expires_at,
            "expires_in": str(expires_at - datetime.now()) if is_valid else "EXPIRED",
            "created_at": self.token_info.created_at
        }


def main():
    """CLI for TikTok authentication."""
    import argparse

    parser = argparse.ArgumentParser(description='TikTok OAuth Authentication')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Authorize command
    auth_parser = subparsers.add_parser('authorize', help='Start OAuth authorization flow')
    auth_parser.add_argument('--port', type=int, default=8000, help='Callback server port')

    # Refresh command
    subparsers.add_parser('refresh', help='Refresh access token')

    # Status command
    subparsers.add_parser('status', help='Show authentication status')

    # Revoke command
    subparsers.add_parser('revoke', help='Revoke access token')

    args = parser.parse_args()

    auth = TikTokAuth()

    if args.command == 'authorize':
        success = auth.authorize_interactive(port=args.port)
        if success:
            print("\nAuthorization successful!")
            print(f"Tokens saved to: {auth.TOKEN_FILE}")
        else:
            print("\nAuthorization failed!")
            return 1

    elif args.command == 'refresh':
        try:
            result = auth.refresh_access_token()
            if "access_token" in result:
                print("Token refreshed successfully!")
            else:
                print(f"Refresh failed: {result}")
                return 1
        except ValueError as e:
            print(f"Error: {e}")
            return 1

    elif args.command == 'status':
        status = auth.get_status()
        print("\nTikTok Authentication Status:")
        print("-" * 40)
        for key, value in status.items():
            print(f"  {key}: {value}")

    elif args.command == 'revoke':
        if auth.revoke_token():
            print("Token revoked successfully!")
        else:
            print("Token revocation failed!")
            return 1

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
