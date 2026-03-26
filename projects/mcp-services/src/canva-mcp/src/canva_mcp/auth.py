"""
Canva OAuth 2.0 Authentication with PKCE.

Handles the full OAuth flow:
1. Generate code verifier and challenge (SHA-256)
2. Build authorization URL
3. Exchange authorization code for tokens
4. Refresh expired tokens (4-hour expiry)
"""

import base64
import hashlib
import secrets
import json
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import httpx

# Canva OAuth endpoints
CANVA_AUTH_URL = "https://www.canva.com/api/oauth/authorize"
CANVA_TOKEN_URL = "https://www.canva.com/api/oauth/token"

# Default scopes for full access
DEFAULT_SCOPES = [
    "design:content:read",
    "design:content:write",
    "design:meta:read",
    "asset:read",
    "asset:write",
    "brandtemplate:content:read",
    "brandtemplate:meta:read",
    "folder:read",
    "folder:write",
    "profile:read",
]


def generate_code_verifier(length: int = 64) -> str:
    """Generate a cryptographically random code verifier (43-128 chars)."""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_code_challenge(verifier: str) -> str:
    """Generate SHA-256 code challenge from verifier (base64url encoded)."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to receive OAuth callback."""

    authorization_code = None
    state = None
    error = None

    def log_message(self, format, *args):
        """Suppress logging."""
        pass

    def do_GET(self):
        """Handle OAuth callback GET request."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.authorization_code = params["code"][0]
            OAuthCallbackHandler.state = params.get("state", [None])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Canva Authorization Success</title></head>
                <body style="font-family: system-ui; text-align: center; padding: 50px;">
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        elif "error" in params:
            OAuthCallbackHandler.error = params.get("error_description", params["error"])[0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            error_msg = OAuthCallbackHandler.error
            self.wfile.write(f"""
                <html>
                <head><title>Authorization Failed</title></head>
                <body style="font-family: system-ui; text-align: center; padding: 50px;">
                    <h1>Authorization Failed</h1>
                    <p>{error_msg}</p>
                </body>
                </html>
            """.encode())
        else:
            self.send_response(400)
            self.end_headers()


class CanvaAuth:
    """Manages Canva OAuth authentication and token lifecycle."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8765/callback",
        token_file: str | Path | None = None,
        scopes: list[str] | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or DEFAULT_SCOPES

        # Token storage
        self.token_file = Path(token_file) if token_file else Path.home() / ".canva_tokens.json"
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.expires_at: datetime | None = None

        # PKCE state
        self._code_verifier: str | None = None
        self._state: str | None = None

        # Load existing tokens
        self._load_tokens()

    def _load_tokens(self) -> bool:
        """Load tokens from file if they exist."""
        if self.token_file.exists():
            try:
                data = json.loads(self.token_file.read_text())
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                if data.get("expires_at"):
                    self.expires_at = datetime.fromisoformat(data["expires_at"])
                return True
            except (json.JSONDecodeError, KeyError):
                return False
        return False

    def _save_tokens(self):
        """Save tokens to file."""
        data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
        self.token_file.write_text(json.dumps(data, indent=2))
        self.token_file.chmod(0o600)

    def get_authorization_url(self) -> str:
        """Generate authorization URL with PKCE challenge."""
        self._code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(self._code_verifier)
        self._state = secrets.token_urlsafe(32)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": self._state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{CANVA_AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, authorization_code: str) -> dict:
        """Exchange authorization code for access token."""
        if not self._code_verifier:
            raise ValueError("No code verifier - call get_authorization_url first")

        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "code_verifier": self._code_verifier,
            "redirect_uri": self.redirect_uri,
        }

        response = httpx.post(
            CANVA_TOKEN_URL,
            data=data,
            auth=(self.client_id, self.client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()

        token_data = response.json()
        self._update_tokens(token_data)
        return token_data

    def refresh_access_token(self) -> dict:
        """Refresh the access token using refresh token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available - need to re-authenticate")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        response = httpx.post(
            CANVA_TOKEN_URL,
            data=data,
            auth=(self.client_id, self.client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()

        token_data = response.json()
        self._update_tokens(token_data)
        return token_data

    def _update_tokens(self, token_data: dict):
        """Update internal token state and save to file."""
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token", self.refresh_token)

        # Calculate expiry (typically 4 hours, subtract 5 min buffer)
        expires_in = token_data.get("expires_in", 14400)
        self.expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

        self._save_tokens()

    def is_token_valid(self) -> bool:
        """Check if current access token is valid (not expired)."""
        if not self.access_token or not self.expires_at:
            return False
        return datetime.now() < self.expires_at

    def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if self.is_token_valid():
            return self.access_token

        if self.refresh_token:
            try:
                self.refresh_access_token()
                return self.access_token
            except httpx.HTTPStatusError:
                pass

        raise ValueError("No valid token - need to re-authenticate")

    def authenticate_interactive(self, port: int = 8765) -> str:
        """Run interactive OAuth flow with local callback server."""
        OAuthCallbackHandler.authorization_code = None
        OAuthCallbackHandler.state = None
        OAuthCallbackHandler.error = None

        server = HTTPServer(("localhost", port), OAuthCallbackHandler)
        server_thread = threading.Thread(target=server.handle_request)
        server_thread.start()

        auth_url = self.get_authorization_url()
        print(f"\nOpening browser for Canva authorization...")
        print(f"If browser doesn't open, visit:\n{auth_url}\n")
        webbrowser.open(auth_url)

        server_thread.join(timeout=300)
        server.server_close()

        if OAuthCallbackHandler.error:
            raise ValueError(f"Authorization failed: {OAuthCallbackHandler.error}")

        if not OAuthCallbackHandler.authorization_code:
            raise ValueError("Authorization timed out or was cancelled")

        if OAuthCallbackHandler.state != self._state:
            raise ValueError("State mismatch - possible CSRF attack")

        self.exchange_code(OAuthCallbackHandler.authorization_code)
        print("Authorization successful! Tokens saved.")

        return self.access_token
