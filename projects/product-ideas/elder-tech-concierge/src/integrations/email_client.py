#!/usr/bin/env python3
"""
email_client.py - Gmail Integration for Elder Tech Concierge

WHAT: Read and summarize emails for elderly users
WHY: Allow seniors to hear their emails without navigating Gmail
"""

import os
import sys
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from email.utils import parsedate_to_datetime

# Add parent directory to path for imports
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("WARNING: Google API libraries not installed")
    print("Install with: pip install google-auth google-auth-oauthlib google-api-python-client")
    Request = None
    Credentials = None
    InstalledAppFlow = None
    HttpError = Exception

from config import config


class EmailClient:
    """
    Gmail client for reading and summarizing emails.

    Features:
    - Fetch recent emails
    - Parse email content
    - Filter by importance
    - Senior-friendly summaries
    """

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    # Priority senders (family, doctors, important contacts)
    PRIORITY_DOMAINS = ['doctor', 'medical', 'hospital', 'pharmacy', 'health']
    PRIORITY_KEYWORDS = ['urgent', 'important', 'appointment', 'reminder', 'prescription']

    def __init__(
        self,
        credentials_path: str = None,
        token_path: str = None
    ):
        """
        Initialize Gmail client.

        Args:
            credentials_path: Path to OAuth credentials (defaults to config)
            token_path: Path to token file (defaults to config)
        """
        self.credentials_path = credentials_path or config.google_credentials_path
        self.token_path = token_path or config.google_token_path
        self.service = None

        # Build list of priority senders from contacts
        self.priority_senders = set()
        for contact in config.get_all_contacts():
            if contact.email:
                self.priority_senders.add(contact.email.lower())

    def is_available(self) -> bool:
        """Check if Gmail API is available."""
        return Credentials is not None and os.path.exists(self.credentials_path)

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API.

        Returns:
            True if authentication successful
        """
        if not self.is_available():
            return False

        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            except Exception:
                pass

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_path):
                    return False

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception:
                    return False

            # Save token
            try:
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception:
                pass

        try:
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except Exception:
            return False

    def get_recent_emails(
        self,
        hours_back: int = 24,
        max_results: int = 10,
        priority_only: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch recent emails.

        Args:
            hours_back: Hours to look back (default 24)
            max_results: Maximum emails to fetch
            priority_only: Only fetch priority emails

        Returns:
            Dict with emails list and spoken summary
        """
        if not self.service:
            if not self.authenticate():
                return {
                    'success': False,
                    'emails': [],
                    'error': 'Gmail not connected',
                    'spoken_response': "I can't access your email right now. The email service isn't set up yet."
                }

        try:
            # Calculate time query
            after_date = datetime.now() - timedelta(hours=hours_back)
            after_timestamp = int(after_date.timestamp())

            query = f'after:{after_timestamp} in:inbox'
            if priority_only:
                query += ' is:important'

            # Fetch messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                return {
                    'success': True,
                    'emails': [],
                    'count': 0,
                    'spoken_response': "Good news! You don't have any new emails to worry about."
                }

            # Parse each email
            emails = []
            for msg in messages:
                email_data = self._fetch_and_parse_email(msg['id'])
                if email_data:
                    email_data['is_priority'] = self._is_priority_email(email_data)
                    emails.append(email_data)

            # Sort by priority
            emails.sort(key=lambda x: (not x['is_priority'], x['date']), reverse=True)

            return {
                'success': True,
                'emails': emails,
                'count': len(emails),
                'priority_count': sum(1 for e in emails if e['is_priority']),
                'spoken_response': self._format_emails_spoken(emails)
            }

        except HttpError as error:
            return {
                'success': False,
                'emails': [],
                'error': str(error),
                'spoken_response': "I had trouble checking your email. Let's try again in a moment."
            }
        except Exception as e:
            return {
                'success': False,
                'emails': [],
                'error': str(e),
                'spoken_response': "Something went wrong checking your email. Would you like to try again?"
            }

    def _fetch_and_parse_email(self, message_id: str) -> Optional[Dict]:
        """
        Fetch and parse a single email.

        Args:
            message_id: Gmail message ID

        Returns:
            Parsed email dict or None
        """
        try:
            email = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            headers = email['payload']['headers']

            parsed = {
                'id': email['id'],
                'subject': '',
                'from': '',
                'from_email': '',
                'from_name': '',
                'date': '',
                'snippet': email.get('snippet', ''),
                'body_preview': ''
            }

            # Extract headers
            for header in headers:
                name = header['name'].lower()
                if name == 'subject':
                    parsed['subject'] = header['value']
                elif name == 'from':
                    from_value = header['value']
                    parsed['from'] = from_value
                    # Extract name and email
                    if '<' in from_value:
                        parts = from_value.split('<')
                        parsed['from_name'] = parts[0].strip().strip('"')
                        parsed['from_email'] = parts[1].strip('>').lower()
                    else:
                        parsed['from_email'] = from_value.lower()
                        parsed['from_name'] = from_value.split('@')[0]
                elif name == 'date':
                    parsed['date'] = header['value']

            # Get body preview
            parsed['body_preview'] = self._get_body_preview(email['payload'])

            return parsed

        except Exception:
            return None

    def _get_body_preview(self, payload: Dict, max_length: int = 500) -> str:
        """Extract body preview from email payload."""
        try:
            if 'body' in payload and payload['body'].get('data'):
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
                return body[:max_length]

            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            return body[:max_length]
        except Exception:
            pass

        return ""

    def _is_priority_email(self, email: Dict) -> bool:
        """Determine if email is priority."""
        # Check if from known contact
        if email['from_email'] in self.priority_senders:
            return True

        # Check for priority domains
        for domain in self.PRIORITY_DOMAINS:
            if domain in email['from_email']:
                return True

        # Check for priority keywords in subject
        subject_lower = email['subject'].lower()
        for keyword in self.PRIORITY_KEYWORDS:
            if keyword in subject_lower:
                return True

        return False

    def _format_emails_spoken(self, emails: List[Dict]) -> str:
        """Format emails list for voice output."""
        if not emails:
            return "You don't have any new emails."

        priority_emails = [e for e in emails if e['is_priority']]
        other_count = len(emails) - len(priority_emails)

        parts = []

        if priority_emails:
            count = len(priority_emails)
            parts.append(f"You have {count} important email{'s' if count > 1 else ''}.")

            # Read first 2 priority emails
            for i, email in enumerate(priority_emails[:2], 1):
                sender = email['from_name'] or email['from_email'].split('@')[0]
                subject = email['subject'] or 'No subject'
                parts.append(f"Email {i}: From {sender}, about {subject}.")

        if other_count > 0:
            parts.append(f"You also have {other_count} other email{'s' if other_count > 1 else ''}.")

        if not priority_emails and emails:
            parts.append(f"You have {len(emails)} new email{'s' if len(emails) > 1 else ''}.")
            email = emails[0]
            sender = email['from_name'] or email['from_email'].split('@')[0]
            subject = email['subject'] or 'No subject'
            parts.append(f"The most recent is from {sender}, about {subject}.")

        return ' '.join(parts)

    def get_email_detail(self, email_id: str) -> Dict[str, Any]:
        """
        Get detailed email content for reading aloud.

        Args:
            email_id: Gmail message ID

        Returns:
            Dict with email content formatted for reading
        """
        if not self.service:
            return {
                'success': False,
                'error': 'Gmail not connected',
                'spoken_response': "I can't read that email right now."
            }

        email = self._fetch_and_parse_email(email_id)

        if not email:
            return {
                'success': False,
                'error': 'Email not found',
                'spoken_response': "I couldn't find that email. Would you like to try again?"
            }

        sender = email['from_name'] or email['from_email'].split('@')[0]
        subject = email['subject'] or 'No subject'
        body = email['body_preview'] or email['snippet']

        # Clean up body for reading
        body = ' '.join(body.split())[:800]  # Remove excess whitespace, limit length

        spoken = f"This email is from {sender}. The subject is: {subject}. "
        spoken += f"Here's what it says: {body}"

        return {
            'success': True,
            'email': email,
            'spoken_response': spoken
        }


# CLI testing
if __name__ == "__main__":
    client = EmailClient()

    print("\n" + "=" * 60)
    print("ELDER TECH CONCIERGE - Email Client Test")
    print("=" * 60 + "\n")

    if not client.is_available():
        print("Gmail API not available. Check credentials.json")
        sys.exit(1)

    print("Authenticating with Gmail...")
    if not client.authenticate():
        print("Authentication failed.")
        sys.exit(1)

    print("Connected to Gmail!\n")
    print("Fetching recent emails...")

    result = client.get_recent_emails(hours_back=24, max_results=5)

    if result['success']:
        print(f"\nFound {result['count']} emails")
        print(f"\nSpoken response:")
        print(f"  {result['spoken_response']}")
    else:
        print(f"\nError: {result.get('error')}")
