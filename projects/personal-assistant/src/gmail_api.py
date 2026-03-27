"""
Personal Assistant Gmail API - Tower-specific Gmail operations.

Extracted from monolithic agent_bridge_api.py to restore tower independence.
Provides Gmail functionality for personal-assistant tower only.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Auto-load .env from repo root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")
except ImportError:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail service singleton
_gmail_service = None

FULL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
]


def get_gmail_service():
    """Get or create Gmail API service for personal-assistant tower.

    Loads the token WITHOUT forcing specific scopes so it works with
    whatever scopes the token already has (e.g. gmail.readonly only).
    Only triggers a re-auth flow if the token file is missing entirely.
    """
    global _gmail_service
    if _gmail_service is not None:
        return _gmail_service

    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = None
        token_path = Path(__file__).resolve().parent.parent.parent.parent / "token.json"
        creds_path = Path(__file__).resolve().parent.parent.parent.parent / "credentials.json"

        if token_path.exists():
            # Load WITHOUT specifying scopes — use whatever the token has
            creds = Credentials.from_authorized_user_file(str(token_path))

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            elif creds_path.exists():
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), FULL_SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            else:
                logger.error("Gmail credentials not found")
                return None

        _gmail_service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail service initialized for personal-assistant tower")
        return _gmail_service

    except Exception as e:
        logger.error(f"Gmail service initialization failed: {e}")
        return None


def has_send_scope() -> bool:
    """Check if the current token has gmail.send scope."""
    token_path = Path(__file__).resolve().parent.parent.parent.parent / "token.json"
    if not token_path.exists():
        return False
    try:
        import json
        with open(token_path) as f:
            token_data = json.load(f)
        scopes = token_data.get("scopes", [])
        return "https://www.googleapis.com/auth/gmail.send" in scopes
    except Exception:
        return False


def list_emails(max_results: int = 10, query: str = "", label_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    List emails from Gmail inbox.

    Args:
        max_results: Maximum number of emails to return
        query: Gmail search query
        label_ids: List of label IDs to filter by

    Returns:
        Dict with success status and email list
    """
    service = get_gmail_service()
    if not service:
        return {"success": False, "error": "Gmail service not available"}

    try:
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=query,
            labelIds=label_ids or ['INBOX']
        ).execute()

        messages = results.get('messages', [])
        emails = []

        for msg in messages[:max_results]:
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata'
            ).execute()

            headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}

            emails.append({
                "id": msg['id'],
                "thread_id": msg_data.get('threadId'),
                "snippet": msg_data.get('snippet', ''),
                "from": headers.get('From', ''),
                "to": headers.get('To', ''),
                "subject": headers.get('Subject', ''),
                "date": headers.get('Date', ''),
                "labels": msg_data.get('labelIds', [])
            })

        return {
            "success": True,
            "emails": emails,
            "count": len(emails),
            "query": query
        }

    except Exception as e:
        logger.error(f"Failed to list emails: {e}")
        return {"success": False, "error": str(e)}


def read_email(message_id: str) -> Dict[str, Any]:
    """
    Read a specific email by ID.

    Args:
        message_id: Gmail message ID

    Returns:
        Dict with email content
    """
    service = get_gmail_service()
    if not service:
        return {"success": False, "error": "Gmail service not available"}

    try:
        msg = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}

        body = ''
        payload = msg.get('payload', {})

        if 'body' in payload and payload['body'].get('data'):
            import base64
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                    import base64
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break

        return {
            "success": True,
            "email": {
                "id": message_id,
                "thread_id": msg.get('threadId'),
                "from": headers.get('From', ''),
                "to": headers.get('To', ''),
                "subject": headers.get('Subject', ''),
                "date": headers.get('Date', ''),
                "body": body,
                "labels": msg.get('labelIds', [])
            }
        }

    except Exception as e:
        logger.error(f"Failed to read email {message_id}: {e}")
        return {"success": False, "error": str(e)}


def send_email(to: str, subject: str = "", body: str = "", cc: str = "", bcc: str = "") -> Dict[str, Any]:
    """
    Send an email via Gmail SMTP.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
        cc: CC recipients
        bcc: BCC recipients

    Returns:
        Dict with send status
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USERNAME')
        smtp_pass = os.getenv('SMTP_PASSWORD')
        sender_email = os.getenv('SENDER_EMAIL', smtp_user)

        if not smtp_user or not smtp_pass:
            return {"success": False, "error": "SMTP credentials not configured"}

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to
        msg['Subject'] = subject
        if cc:
            msg['Cc'] = cc
        if bcc:
            msg['Bcc'] = bcc

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        return {
            "success": True,
            "method": "smtp",
            "to": to,
            "subject": subject
        }

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {"success": False, "error": str(e)}


def create_draft(to: str, subject: str = "", body: str = "", cc: str = "", bcc: str = "") -> Dict[str, Any]:
    """
    Create a draft email in Gmail.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
        cc: CC recipients
        bcc: BCC recipients

    Returns:
        Dict with draft creation status
    """
    service = get_gmail_service()
    if not service:
        return {"success": False, "error": "Gmail service not available"}

    try:
        import base64
        from email.mime.text import MIMEText

        msg = MIMEText(body)
        msg['To'] = to
        msg['Subject'] = subject
        if cc:
            msg['Cc'] = cc
        if bcc:
            msg['Bcc'] = bcc

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        draft = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw}}
        ).execute()

        return {
            "success": True,
            "draft_id": draft['id'],
            "message_id": draft['message']['id'],
            "to": to,
            "subject": subject
        }

    except Exception as e:
        logger.error(f"Failed to create draft: {e}")
        return {"success": False, "error": str(e)}


def search_emails(query: str, max_results: int = 20) -> Dict[str, Any]:
    """
    Search emails with Gmail query syntax.

    Args:
        query: Gmail search query
        max_results: Maximum results to return

    Returns:
        Dict with search results
    """
    service = get_gmail_service()
    if not service:
        return {"success": False, "error": "Gmail service not available"}

    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        emails = []

        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata'
            ).execute()

            headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}

            emails.append({
                "id": msg['id'],
                "snippet": msg_data.get('snippet', ''),
                "from": headers.get('From', ''),
                "subject": headers.get('Subject', ''),
                "date": headers.get('Date', '')
            })

        return {
            "success": True,
            "query": query,
            "emails": emails,
            "count": len(emails)
        }

    except Exception as e:
        logger.error(f"Failed to search emails: {e}")
        return {"success": False, "error": str(e)}


def search_all_accounts(query: str, accounts: str = "all", max_results: int = 10) -> Dict[str, Any]:
    """
    Search emails across ALL registered Gmail accounts (business + personal).

    Uses multi_gmail_search.py subprocess for multi-account support.

    Args:
        query: Gmail search query
        accounts: "all", "business", "personal", or comma-separated aliases
        max_results: Max results per account

    Returns:
        Dict with search results from all accounts
    """
    import subprocess
    import sys
    import json

    if not query:
        return {"success": False, "error": "query is required"}

    try:
        search_script = Path(__file__).resolve().parent.parent.parent.parent / "execution" / "multi_gmail_search.py"
        cmd = [
            sys.executable, '-W', 'ignore', str(search_script),
            '--query', query,
            '--accounts', accounts,
            '--max-results', str(max_results),
            '--json-output'
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            cwd=str(search_script.parent.parent)
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip()}

        emails = json.loads(result.stdout) if result.stdout.strip() else []
        return {
            "success": True,
            "query": query,
            "accounts": accounts,
            "emails": emails,
            "count": len(emails),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Search timed out after 30s"}
    except Exception as e:
        logger.error(f"Failed to search all accounts: {e}")
        return {"success": False, "error": str(e)}


# Tower interface functions for CLAUDE.md compliance
def get_tower_capabilities() -> Dict[str, Any]:
    """Return tower capabilities for Gmail operations."""
    return {
        "name": "personal-assistant-gmail",
        "description": "Gmail integration for personal assistant automation",
        "functions": [
            "list_emails",
            "read_email",
            "send_email",
            "create_draft",
            "search_emails",
            "search_all_accounts"
        ],
        "protocols": ["direct_import", "mcp_server"]
    }


def get_mcp_server_config() -> Dict[str, Any]:
    """Return MCP server configuration for tower integration."""
    return {
        "name": "personal-assistant-gmail",
        "version": "1.0.0",
        "capabilities": get_tower_capabilities(),
        "endpoints": {
            "list": "/gmail/list",
            "read": "/gmail/read",
            "send": "/gmail/send",
            "draft": "/gmail/draft",
            "search": "/gmail/search"
        }
    }


if __name__ == "__main__":
    # Test the Gmail API extraction
    print("Testing personal-assistant Gmail API extraction...")

    # Test service initialization
    service = get_gmail_service()
    if service:
        print("✓ Gmail service initialized")
    else:
        print("✗ Gmail service failed - check credentials")

    # Test capabilities
    caps = get_tower_capabilities()
    print(f"✓ Tower capabilities: {caps['name']}")

    print("Gmail API extraction test completed")