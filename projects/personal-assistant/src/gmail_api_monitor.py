"""
Gmail API Integration for Email Response Monitoring

Integrates with Gmail API to automatically:
1. Monitor inbox for new responses
2. Extract email metadata and content
3. Pass to EmailResponseMonitor for processing
4. Handle OAuth authentication

Requires:
- Google Cloud project with Gmail API enabled
- OAuth 2.0 credentials (client_secrets.json)
- Token storage for persistence

Setup:
1. Go to https://console.cloud.google.com/
2. Create project and enable Gmail API
3. Create OAuth credentials (Desktop app)
4. Download client_secrets.json
5. Run this script to authenticate
"""

import os
import json
import base64
import pickle
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Try to import Gmail API libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False
    logger.warning(
        "Gmail API libraries not installed. "
        "Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
    )

from email_response_monitor import EmailResponseMonitor


# Gmail API scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.labels',
]


class GmailMonitor:
    """
    Monitors Gmail inbox using the Gmail API.

    Automatically detects responses to outreach emails and
    processes them through EmailResponseMonitor.
    """

    def __init__(self, credentials_dir: str = None):
        """
        Initialize Gmail monitor.

        Args:
            credentials_dir: Directory containing client_secrets.json and token.pickle
        """
        if not GMAIL_API_AVAILABLE:
            raise ImportError(
                "Gmail API libraries not installed. "
                "Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )

        if credentials_dir:
            self.credentials_dir = Path(credentials_dir)
        else:
            self.credentials_dir = Path.home() / ".gmail_monitor"

        self.credentials_dir.mkdir(parents=True, exist_ok=True)

        self.token_file = self.credentials_dir / "token.pickle"
        self.secrets_file = self.credentials_dir / "client_secrets.json"

        # Check for secrets file
        if not self.secrets_file.exists():
            alt_secrets = Path(__file__).parent.parent / "data" / "client_secrets.json"
            if alt_secrets.exists():
                self.secrets_file = alt_secrets

        self.service = None
        self.response_monitor = EmailResponseMonitor()

        # Track processed messages to avoid duplicates
        self.processed_file = self.credentials_dir / "processed_messages.json"
        self.processed_ids: set = self._load_processed_ids()

    def _load_processed_ids(self) -> set:
        """Load set of already processed message IDs."""
        if self.processed_file.exists():
            with open(self.processed_file, 'r') as f:
                data = json.load(f)
                return set(data.get('ids', []))
        return set()

    def _save_processed_ids(self) -> None:
        """Save processed message IDs."""
        with open(self.processed_file, 'w') as f:
            json.dump({'ids': list(self.processed_ids)}, f)

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth 2.0.

        On first run, opens browser for user authorization.
        Subsequent runs use stored token.
        """
        creds = None

        # Load existing token
        if self.token_file.exists():
            with open(self.token_file, 'rb') as f:
                creds = pickle.load(f)

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.secrets_file.exists():
                    logger.error(
                        f"client_secrets.json not found at {self.secrets_file}. "
                        "Download from Google Cloud Console."
                    )
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.secrets_file), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for next run
            with open(self.token_file, 'wb') as f:
                pickle.dump(creds, f)

        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail API authenticated successfully")
        return True

    def get_user_email(self) -> str:
        """Get the authenticated user's email address."""
        if not self.service:
            self.authenticate()

        profile = self.service.users().getProfile(userId='me').execute()
        return profile.get('emailAddress', '')

    def search_messages(
        self,
        query: str = "",
        max_results: int = 50,
        after_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Search Gmail for messages matching query.

        Args:
            query: Gmail search query (same syntax as web search)
            max_results: Maximum messages to return
            after_date: Only messages after this date

        Returns:
            List of message metadata dicts
        """
        if not self.service:
            self.authenticate()

        # Build query with date filter
        if after_date:
            date_str = after_date.strftime('%Y/%m/%d')
            query = f"after:{date_str} {query}".strip()

        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            return messages

        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return []

    def get_message_details(self, message_id: str) -> Dict[str, Any]:
        """
        Get full details of a message.

        Args:
            message_id: Gmail message ID

        Returns:
            Dict with message details
        """
        if not self.service:
            self.authenticate()

        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Extract headers
            headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}

            # Extract body
            body = self._extract_body(message.get('payload', {}))

            # Parse date
            received_at = None
            if headers.get('Date'):
                try:
                    from email.utils import parsedate_to_datetime
                    received_at = parsedate_to_datetime(headers['Date'])
                except:
                    pass

            # Parse from address
            from_header = headers.get('From', '')
            from_email, from_name = self._parse_from_header(from_header)

            return {
                'message_id': message_id,
                'thread_id': message.get('threadId', ''),
                'from_email': from_email,
                'from_name': from_name,
                'to_email': headers.get('To', ''),
                'subject': headers.get('Subject', ''),
                'body': body,
                'received_at': received_at,
                'labels': message.get('labelIds', []),
                'snippet': message.get('snippet', ''),
            }

        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}")
            return {}

    def _extract_body(self, payload: Dict) -> str:
        """Extract message body from payload."""
        body = ""

        # Try to get plain text body
        if payload.get('body', {}).get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')

        # Check parts for multipart messages
        for part in payload.get('parts', []):
            mime_type = part.get('mimeType', '')

            if mime_type == 'text/plain':
                if part.get('body', {}).get('data'):
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    break

            # Recursively check nested parts
            if part.get('parts'):
                body = self._extract_body(part)
                if body:
                    break

        return body

    def _parse_from_header(self, from_header: str) -> tuple:
        """Parse From header into (email, name)."""
        import re

        # Match "Name <email@domain.com>" format
        match = re.match(r'"?([^"<]+)"?\s*<([^>]+)>', from_header)
        if match:
            return match.group(2).strip(), match.group(1).strip()

        # Match plain email
        match = re.match(r'([^\s<>]+@[^\s<>]+)', from_header)
        if match:
            return match.group(1), ""

        return from_header, ""

    def check_inbox(
        self,
        hours_back: int = 24,
        query: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Check inbox for new responses and process them.

        Args:
            hours_back: How far back to look for messages
            query: Additional Gmail search query

        Returns:
            List of processed EmailResponse dicts
        """
        if not self.service:
            if not self.authenticate():
                return []

        # Calculate date range
        after_date = datetime.now() - timedelta(hours=hours_back)

        # Build query for potential responses
        # Look in inbox, exclude sent mail
        base_query = "in:inbox -in:sent"
        full_query = f"{base_query} {query}".strip()

        # Get messages
        messages = self.search_messages(
            query=full_query,
            max_results=100,
            after_date=after_date
        )

        logger.info(f"Found {len(messages)} messages in last {hours_back} hours")

        processed = []
        new_count = 0

        for msg_meta in messages:
            msg_id = msg_meta['id']

            # Skip already processed
            if msg_id in self.processed_ids:
                continue

            # Get full message
            msg = self.get_message_details(msg_id)
            if not msg:
                continue

            # Process through response monitor
            response = self.response_monitor.process_incoming_email(
                from_email=msg['from_email'],
                from_name=msg['from_name'],
                to_email=msg['to_email'],
                subject=msg['subject'],
                body=msg['body'],
                received_at=msg['received_at'],
                message_id=msg_id,
                thread_id=msg['thread_id']
            )

            processed.append(response.to_dict())
            new_count += 1

            # Mark as processed
            self.processed_ids.add(msg_id)

        # Save processed IDs
        if new_count > 0:
            self._save_processed_ids()
            logger.info(f"Processed {new_count} new messages")

        return processed

    def run_continuous(
        self,
        interval_minutes: int = 15,
        query: str = ""
    ) -> None:
        """
        Continuously monitor inbox at regular intervals.

        Args:
            interval_minutes: How often to check (default 15 min)
            query: Additional Gmail search query
        """
        import time

        logger.info(f"Starting continuous monitoring (every {interval_minutes} minutes)")
        logger.info("Press Ctrl+C to stop")

        while True:
            try:
                processed = self.check_inbox(
                    hours_back=interval_minutes // 60 + 1,
                    query=query
                )

                if processed:
                    for resp in processed:
                        print(f"  New response from: {resp['from_email']} ({resp['response_type']})")

                time.sleep(interval_minutes * 60)

            except KeyboardInterrupt:
                logger.info("Stopping monitor...")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait a minute before retrying


# CLI interface
if __name__ == '__main__':
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Gmail API Monitor")
    subparsers = parser.add_subparsers(dest='command')

    # Auth command
    auth_parser = subparsers.add_parser('auth', help='Authenticate with Gmail')

    # Check command
    check_parser = subparsers.add_parser('check', help='Check inbox for responses')
    check_parser.add_argument('--hours', '-H', type=int, default=24, help='Hours to look back')
    check_parser.add_argument('--query', '-q', default='', help='Additional search query')

    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Continuously monitor inbox')
    monitor_parser.add_argument('--interval', '-i', type=int, default=15, help='Check interval (minutes)')
    monitor_parser.add_argument('--query', '-q', default='', help='Additional search query')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search inbox')
    search_parser.add_argument('query', help='Gmail search query')
    search_parser.add_argument('--max', '-m', type=int, default=10, help='Max results')

    args = parser.parse_args()

    if not GMAIL_API_AVAILABLE:
        print("ERROR: Gmail API libraries not installed.")
        print("Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        exit(1)

    monitor = GmailMonitor()

    if args.command == 'auth':
        if monitor.authenticate():
            email = monitor.get_user_email()
            print(f"Successfully authenticated as: {email}")
        else:
            print("Authentication failed. Check credentials.")

    elif args.command == 'check':
        results = monitor.check_inbox(hours_back=args.hours, query=args.query)
        print(f"\nProcessed {len(results)} new responses:")
        for resp in results:
            print(f"  From: {resp['from_email']}")
            print(f"  Subject: {resp['subject']}")
            print(f"  Type: {resp['response_type']}")
            print(f"  Project: {resp['project']}")
            print()

    elif args.command == 'monitor':
        monitor.run_continuous(interval_minutes=args.interval, query=args.query)

    elif args.command == 'search':
        if not monitor.authenticate():
            exit(1)

        messages = monitor.search_messages(query=args.query, max_results=args.max)
        print(f"\nFound {len(messages)} messages:\n")

        for msg_meta in messages:
            details = monitor.get_message_details(msg_meta['id'])
            print(f"  From: {details['from_email']}")
            print(f"  Subject: {details['subject']}")
            print(f"  Date: {details['received_at']}")
            print()

    else:
        parser.print_help()
