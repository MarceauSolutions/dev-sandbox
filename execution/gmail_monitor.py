#!/usr/bin/env python3
"""
gmail_monitor.py - Gmail Monitor and Email Summarization

WHAT: Monitors Gmail inbox and provides intelligent email summaries
WHY: Never miss important sponsorships, collaborations, or customer inquiries
INPUT: Time period (hours back, default 24)
OUTPUT: Categorized email digest with priority flagging and suggested actions
COST: FREE (uses Gmail API)
TIME: <30 seconds

QUICK USAGE:
  python gmail_monitor.py --hours 24

CAPABILITIES:
  - Email categorization (sponsorships, business, customer, other)
  - Priority flagging (urgent items highlighted)
  - Daily digest generation with summaries
  - Draft response suggestions
  - Batch processing of inbox

DEPENDENCIES: google-auth, google-auth-oauthlib, google-api-python-client
API_KEYS: Google OAuth (credentials.json, token.json)

---
Original Features:
- Email categorization (sponsorships, business, other)
- Priority flagging
- Daily digest generation
- Draft response suggestions

Usage:
    python gmail_monitor.py --hours 24
    python gmail_monitor.py --hours 24 --categories sponsorship,business
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("ERROR: Google API libraries not installed")
    print("Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

import base64
from email.mime.text import MIMEText


class GmailMonitor:
    """
    Monitor Gmail and categorize/summarize emails.
    """

    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    # Email categories and keywords
    CATEGORIES = {
        'sponsorship': ['sponsorship', 'sponsor', 'brand deal', 'collaboration', 'partnership', 'paid promotion'],
        'business': ['invoice', 'payment', 'revenue', 'affiliate', 'commission', 'earnings', 'payout'],
        'customer': ['refund', 'support', 'help', 'question', 'issue', 'problem', 'course', 'purchased'],
        'collaboration': ['collab', 'feature', 'guest', 'interview', 'podcast', 'video together'],
        'administrative': ['confirm', 'verification', 'security', 'password', 'account', 'settings'],
    }

    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        """
        Initialize Gmail monitor.

        Args:
            credentials_path: Path to OAuth credentials file
            token_path: Path to store/load token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    def authenticate(self):
        """
        Authenticate with Gmail API using OAuth 2.0.

        Returns:
            Gmail service object
        """
        creds = None

        # Check if token file exists
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print(f"ERROR: Credentials file not found: {self.credentials_path}")
                    print("\\nTo set up Gmail API:")
                    print("1. Go to https://console.cloud.google.com")
                    print("2. Create a project and enable Gmail API")
                    print("3. Create OAuth credentials (Desktop app)")
                    print("4. Download credentials.json")
                    return None

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        return self.service

    def get_emails(self, hours_back=24, max_results=100):
        """
        Fetch emails from the last N hours.

        Args:
            hours_back: Number of hours to look back
            max_results: Maximum emails to fetch

        Returns:
            List of email objects
        """
        if not self.service:
            print("ERROR: Not authenticated. Call authenticate() first.")
            return []

        try:
            # Calculate date for query
            after_date = datetime.now() - timedelta(hours=hours_back)
            after_timestamp = int(after_date.timestamp())

            # Search query
            query = f'after:{after_timestamp} in:inbox'

            print(f"→ Fetching emails from last {hours_back} hours...")

            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                print("  No emails found")
                return []

            print(f"  ✓ Found {len(messages)} emails")

            # Fetch full message details
            emails = []
            for msg in messages:
                email = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                emails.append(email)

            return emails

        except HttpError as error:
            print(f"ERROR: Gmail API error: {error}")
            return []

    def parse_email(self, email):
        """
        Parse email to extract key information.

        Args:
            email: Gmail API email object

        Returns:
            Dict with parsed email data
        """
        headers = email['payload']['headers']

        # Extract headers
        parsed = {
            'id': email['id'],
            'subject': '',
            'from': '',
            'date': '',
            'snippet': email.get('snippet', ''),
        }

        for header in headers:
            name = header['name'].lower()
            if name == 'subject':
                parsed['subject'] = header['value']
            elif name == 'from':
                parsed['from'] = header['value']
            elif name == 'date':
                parsed['date'] = header['value']

        return parsed

    def categorize_email(self, email):
        """
        Categorize email based on content.

        Args:
            email: Parsed email dict

        Returns:
            Category string and priority level (1-3, 1=highest)
        """
        subject = email['subject'].lower()
        snippet = email['snippet'].lower()
        content = f"{subject} {snippet}"

        # Check each category
        for category, keywords in self.CATEGORIES.items():
            for keyword in keywords:
                if keyword in content:
                    # Determine priority
                    if category in ['sponsorship', 'business']:
                        priority = 1  # High priority
                    elif category in ['customer', 'collaboration']:
                        priority = 2  # Medium priority
                    else:
                        priority = 3  # Low priority

                    return category, priority

        # Default category
        return 'other', 3

    def generate_digest(self, hours_back=24):
        """
        Generate email digest with categorization.

        Args:
            hours_back: Hours to look back

        Returns:
            Dict with digest data
        """
        print(f"\\n{'='*70}")
        print(f"EMAIL DIGEST - Last {hours_back} Hours")
        print(f"{'='*70}\\n")

        # Fetch emails
        emails = self.get_emails(hours_back)

        if not emails:
            print("No emails to process\\n")
            return {'total': 0, 'categories': {}}

        # Parse and categorize
        print(f"→ Analyzing and categorizing emails...\\n")

        categorized = {
            'urgent': [],
            'sponsorship': [],
            'business': [],
            'customer': [],
            'collaboration': [],
            'administrative': [],
            'other': []
        }

        for email in emails:
            parsed = self.parse_email(email)
            category, priority = self.categorize_email(parsed)

            # Add to appropriate category
            if priority == 1:
                categorized['urgent'].append(parsed)

            categorized[category].append(parsed)

        # Generate summary report
        total = len(emails)

        print(f"📧 TOTAL EMAILS: {total}\\n")

        # Urgent items
        if categorized['urgent']:
            print(f"🔴 URGENT ({len(categorized['urgent'])}):")
            for email in categorized['urgent'][:5]:  # Show top 5
                print(f"  • {email['subject']}")
                print(f"    From: {email['from']}")
                print(f"    {email['snippet'][:80]}...")
                print()

        # Business items
        if categorized['sponsorship']:
            print(f"💼 SPONSORSHIPS/COLLABORATIONS ({len(categorized['sponsorship'])}):")
            for email in categorized['sponsorship'][:3]:
                print(f"  • {email['subject']}")
                print(f"    From: {email['from']}")
                print()

        if categorized['business']:
            print(f"💰 BUSINESS/FINANCIAL ({len(categorized['business'])}):")
            for email in categorized['business'][:3]:
                print(f"  • {email['subject']}")
                print(f"    From: {email['from']}")
                print()

        # Customer inquiries
        if categorized['customer']:
            print(f"👤 CUSTOMER INQUIRIES ({len(categorized['customer'])}):")
            for email in categorized['customer'][:3]:
                print(f"  • {email['subject']}")
                print(f"    From: {email['from']}")
                print()

        # Other
        other_count = (
            len(categorized['collaboration']) +
            len(categorized['administrative']) +
            len(categorized['other'])
        )

        if other_count > 0:
            print(f"📬 OTHER ({other_count}):")
            print(f"  Collaboration: {len(categorized['collaboration'])}")
            print(f"  Administrative: {len(categorized['administrative'])}")
            print(f"  Uncategorized: {len(categorized['other'])}")
            print()

        # Suggested actions
        print(f"{'='*70}")
        print(f"SUGGESTED ACTIONS:\\n")

        action_count = 0
        if categorized['urgent']:
            for email in categorized['urgent'][:3]:
                action_count += 1
                print(f"  {action_count}. Respond to: {email['subject'][:60]}")

        if not categorized['urgent']:
            print("  ✓ No urgent actions required")

        print(f"\\n{'='*70}\\n")

        return {
            'total': total,
            'categories': categorized
        }


def main():
    """CLI for Gmail monitor."""
    parser = argparse.ArgumentParser(
        description='Gmail Monitor - Email summarization and categorization'
    )
    parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')
    parser.add_argument('--credentials', default='credentials.json', help='Path to credentials file')
    parser.add_argument('--token', default='token.json', help='Path to token file')
    parser.add_argument('--max-results', type=int, default=100, help='Max emails to fetch')

    args = parser.parse_args()

    # Create monitor
    monitor = GmailMonitor(
        credentials_path=args.credentials,
        token_path=args.token
    )

    # Authenticate
    print("→ Authenticating with Gmail...")
    service = monitor.authenticate()

    if not service:
        print("\\n✗ Authentication failed")
        print("\\nMake sure you have:")
        print("  1. Created a Google Cloud project")
        print("  2. Enabled Gmail API")
        print("  3. Downloaded credentials.json")
        return 1

    print("  ✓ Authentication successful\\n")

    # Generate digest
    try:
        digest = monitor.generate_digest(hours_back=args.hours)

        print(f"📊 Digest complete!")
        print(f"   Total emails processed: {digest['total']}")

        return 0

    except Exception as e:
        print(f"\\n✗ Error generating digest: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())