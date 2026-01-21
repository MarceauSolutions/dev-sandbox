#!/usr/bin/env python3
"""
User OAuth Flow for Gmail/Sheets Access
Allows individual users to connect their Google accounts.

This module handles:
1. Generating OAuth authorization URLs for users
2. Handling OAuth callbacks and exchanging codes for tokens
3. Storing and retrieving user tokens securely
4. Refreshing expired tokens automatically
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Scopes for Gmail and Sheets access
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/calendar.readonly'
]

# Storage directory for user tokens
USER_TOKENS_DIR = Path(__file__).parent / "user_tokens"
USER_TOKENS_DIR.mkdir(exist_ok=True)

# OAuth state storage (in production, use Redis or database)
OAUTH_STATES: Dict[str, Dict[str, Any]] = {}


def get_oauth_config() -> dict:
    """Get OAuth configuration from environment or file."""
    # Try environment variable first (for Railway deployment)
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'https://web-production-44ade.up.railway.app/api/oauth/callback')

    if client_id and client_secret:
        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }

    # Fall back to credentials file
    creds_path = Path(__file__).parent / "credentials_web.json"
    if creds_path.exists():
        with open(creds_path, 'r') as f:
            return json.load(f)

    raise ValueError("No OAuth credentials configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")


def generate_user_id(email: str) -> str:
    """Generate a unique user ID from email."""
    return hashlib.sha256(email.lower().encode()).hexdigest()[:16]


def get_token_path(user_id: str) -> Path:
    """Get the token file path for a user."""
    return USER_TOKENS_DIR / f"token_{user_id}.json"


def create_authorization_url(user_email: str) -> Dict[str, str]:
    """
    Create OAuth authorization URL for a user.

    Args:
        user_email: User's email address for identification

    Returns:
        Dict with 'url' (authorization URL) and 'state' (CSRF token)
    """
    config = get_oauth_config()
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'https://web-production-44ade.up.railway.app/api/oauth/callback')

    flow = Flow.from_client_config(
        config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state with user info (expires in 10 minutes)
    OAUTH_STATES[state] = {
        'email': user_email,
        'user_id': generate_user_id(user_email),
        'created': datetime.utcnow().isoformat(),
        'expires': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    }

    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=state,
        prompt='consent'  # Force consent to get refresh token
    )

    return {
        'url': authorization_url,
        'state': state,
        'user_id': generate_user_id(user_email)
    }


def handle_oauth_callback(code: str, state: str) -> Dict[str, Any]:
    """
    Handle OAuth callback and exchange code for tokens.

    Args:
        code: Authorization code from Google
        state: State token for CSRF verification

    Returns:
        Dict with user_id and success status
    """
    # Verify state
    if state not in OAUTH_STATES:
        raise ValueError("Invalid or expired state token")

    state_data = OAUTH_STATES[state]

    # Check expiration
    expires = datetime.fromisoformat(state_data['expires'])
    if datetime.utcnow() > expires:
        del OAUTH_STATES[state]
        raise ValueError("State token expired")

    user_id = state_data['user_id']
    user_email = state_data['email']

    # Exchange code for tokens
    config = get_oauth_config()
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'https://web-production-44ade.up.railway.app/api/oauth/callback')

    flow = Flow.from_client_config(
        config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Save token for user
    token_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': list(credentials.scopes),
        'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
        'user_email': user_email,
        'connected_at': datetime.utcnow().isoformat()
    }

    token_path = get_token_path(user_id)
    with open(token_path, 'w') as f:
        json.dump(token_data, f, indent=2)

    # Clean up state
    del OAUTH_STATES[state]

    return {
        'success': True,
        'user_id': user_id,
        'email': user_email,
        'scopes': list(credentials.scopes)
    }


def get_user_credentials(user_id: str) -> Optional[Credentials]:
    """
    Get credentials for a user, refreshing if necessary.

    Args:
        user_id: User's unique ID

    Returns:
        Google Credentials object or None if not connected
    """
    token_path = get_token_path(user_id)

    if not token_path.exists():
        return None

    with open(token_path, 'r') as f:
        token_data = json.load(f)

    credentials = Credentials(
        token=token_data['token'],
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data['token_uri'],
        client_id=token_data['client_id'],
        client_secret=token_data['client_secret'],
        scopes=token_data['scopes']
    )

    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

        # Update stored token
        token_data['token'] = credentials.token
        token_data['expiry'] = credentials.expiry.isoformat() if credentials.expiry else None

        with open(token_path, 'w') as f:
            json.dump(token_data, f, indent=2)

    return credentials


def is_user_connected(user_id: str) -> bool:
    """Check if a user has connected their Google account."""
    return get_token_path(user_id).exists()


def disconnect_user(user_id: str) -> bool:
    """
    Disconnect a user's Google account.

    Args:
        user_id: User's unique ID

    Returns:
        True if disconnected, False if wasn't connected
    """
    token_path = get_token_path(user_id)

    if token_path.exists():
        token_path.unlink()
        return True

    return False


def get_user_gmail_service(user_id: str):
    """Get Gmail API service for a user."""
    credentials = get_user_credentials(user_id)
    if not credentials:
        raise ValueError(f"User {user_id} not connected")

    return build('gmail', 'v1', credentials=credentials)


def get_user_sheets_service(user_id: str):
    """Get Sheets API service for a user."""
    credentials = get_user_credentials(user_id)
    if not credentials:
        raise ValueError(f"User {user_id} not connected")

    return build('sheets', 'v4', credentials=credentials)


def get_user_calendar_service(user_id: str):
    """Get Calendar API service for a user."""
    credentials = get_user_credentials(user_id)
    if not credentials:
        raise ValueError(f"User {user_id} not connected")

    return build('calendar', 'v3', credentials=credentials)


def get_user_email_digest(user_id: str, hours_back: int = 24) -> Dict[str, Any]:
    """
    Get email digest for a connected user.

    Args:
        user_id: User's unique ID
        hours_back: Number of hours to look back

    Returns:
        Dict with email summary and categorization
    """
    service = get_user_gmail_service(user_id)

    # Calculate time filter
    import time
    after_timestamp = int(time.time()) - (hours_back * 3600)
    query = f"after:{after_timestamp}"

    # Get messages
    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=50
    ).execute()

    messages = results.get('messages', [])

    email_data = []
    categories = {
        'urgent': [],
        'business': [],
        'personal': [],
        'promotional': [],
        'other': []
    }

    for msg in messages[:20]:  # Limit to 20 for performance
        msg_detail = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()

        headers = {h['name']: h['value'] for h in msg_detail.get('payload', {}).get('headers', [])}

        email_info = {
            'id': msg['id'],
            'from': headers.get('From', 'Unknown'),
            'subject': headers.get('Subject', 'No Subject'),
            'date': headers.get('Date', ''),
            'snippet': msg_detail.get('snippet', '')[:100]
        }

        email_data.append(email_info)

        # Simple categorization based on keywords
        subject_lower = email_info['subject'].lower()
        from_lower = email_info['from'].lower()

        if any(word in subject_lower for word in ['urgent', 'asap', 'important', 'action required']):
            categories['urgent'].append(email_info)
        elif any(word in from_lower for word in ['invoice', 'payment', 'business', 'contract']):
            categories['business'].append(email_info)
        elif any(word in from_lower for word in ['promo', 'sale', 'offer', 'discount', 'unsubscribe']):
            categories['promotional'].append(email_info)
        else:
            categories['other'].append(email_info)

    return {
        'total_emails': len(messages),
        'analyzed': len(email_data),
        'hours_back': hours_back,
        'categories': {k: len(v) for k, v in categories.items()},
        'urgent_emails': categories['urgent'],
        'recent_emails': email_data[:10]
    }


def get_user_sheets_data(user_id: str, spreadsheet_id: str, range_name: str = 'Sheet1!A:Z') -> Dict[str, Any]:
    """
    Get spreadsheet data for a connected user.

    Args:
        user_id: User's unique ID
        spreadsheet_id: Google Sheets ID
        range_name: Range to read (default: all of Sheet1)

    Returns:
        Dict with spreadsheet data
    """
    service = get_user_sheets_service(user_id)

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get('values', [])

    return {
        'spreadsheet_id': spreadsheet_id,
        'range': range_name,
        'row_count': len(values),
        'headers': values[0] if values else [],
        'data': values[1:] if len(values) > 1 else [],
        'raw_values': values
    }


def list_connected_users() -> list:
    """List all connected user IDs."""
    users = []
    for token_file in USER_TOKENS_DIR.glob("token_*.json"):
        user_id = token_file.stem.replace("token_", "")
        with open(token_file, 'r') as f:
            data = json.load(f)
        users.append({
            'user_id': user_id,
            'email': data.get('user_email', 'Unknown'),
            'connected_at': data.get('connected_at', 'Unknown'),
            'scopes': data.get('scopes', [])
        })
    return users
