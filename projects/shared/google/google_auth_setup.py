#!/usr/bin/env python3
"""
Google API Authentication Setup

One-time setup script that authenticates all Google APIs at once:
- Gmail (for email monitoring)
- Google Calendar (for reminders)
- Google Sheets (for revenue tracking)

This creates a token.json file with all necessary permissions.

Usage:
    python google_auth_setup.py
"""

import os
import sys
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: Google API libraries not installed")
    print("Install with: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)


# All scopes needed for fitness influencer operations
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',     # Read emails
    'https://www.googleapis.com/auth/calendar',           # Manage calendar
    'https://www.googleapis.com/auth/spreadsheets',       # Read/write sheets
]


def setup_google_apis(credentials_path='credentials.json', token_path='token.json'):
    """
    Authenticate with Google APIs and save token.
    
    Args:
        credentials_path: Path to OAuth credentials file
        token_path: Path to save token
        
    Returns:
        True if successful
    """
    print("\n" + "="*70)
    print("GOOGLE API AUTHENTICATION SETUP")
    print("="*70 + "\n")
    
    # Check for credentials file
    if not os.path.exists(credentials_path):
        print(f"ERROR: Credentials file not found: {credentials_path}\n")
        print("To set up Google APIs:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create/select your project")
        print("3. Enable Gmail API, Calendar API, and Sheets API")
        print("4. Create OAuth credentials (Desktop app)")
        print("5. Download credentials.json to this directory\n")
        return False
    
    print("→ Starting OAuth authentication flow...\n")
    print("This will open your browser to grant permissions for:")
    print("  • Gmail (read emails)")
    print("  • Google Calendar (manage events)")
    print("  • Google Sheets (read/write data)\n")
    
    try:
        # Start OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_path, SCOPES
        )
        creds = flow.run_local_server(port=0)
        
        # Save token
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        
        print("\n" + "="*70)
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print("="*70 + "\n")
        print(f"Token saved to: {token_path}")
        print("\nYou can now use:")
        print("  • gmail_monitor.py - Monitor your emails")
        print("  • calendar_reminders.py - Manage calendar")
        print("  • revenue_analytics.py - Track revenue\n")
        
        # Test the APIs
        print("→ Testing API connections...\n")
        
        # Test Gmail
        try:
            gmail = build('gmail', 'v1', credentials=creds)
            profile = gmail.users().getProfile(userId='me').execute()
            print(f"  ✓ Gmail: {profile.get('emailAddress')}")
        except Exception as e:
            print(f"  ✗ Gmail: {e}")
        
        # Test Calendar
        try:
            calendar = build('calendar', 'v3', credentials=creds)
            calendar_list = calendar.calendarList().list().execute()
            print(f"  ✓ Calendar: {len(calendar_list.get('items', []))} calendars")
        except Exception as e:
            print(f"  ✗ Calendar: {e}")
        
        # Test Sheets
        try:
            sheets = build('sheets', 'v4', credentials=creds)
            print(f"  ✓ Sheets: Connected")
        except Exception as e:
            print(f"  ✗ Sheets: {e}")
        
        print("\n" + "="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Authentication failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run authentication setup."""
    # Check if already authenticated
    if os.path.exists('token.json'):
        print("\n⚠️  token.json already exists.")
        response = input("Delete and re-authenticate? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 0
        os.remove('token.json')
    
    # Run setup
    success = setup_google_apis()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())