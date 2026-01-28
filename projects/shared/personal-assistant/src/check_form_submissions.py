#!/usr/bin/env python3
"""
Check form submissions across all Marceau Solutions websites.

Websites monitored:
1. marceausolutions.com (main automation business)
2. swflorida-comfort-hvac.com (HVAC practice client)
3. squarefoot-shipping.com (Shipping practice client)

Usage:
  python -m src.check_form_submissions
  python -m src.check_form_submissions --since 2026-01-01
  python -m src.check_form_submissions --website hvac
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json

# Load environment variables
load_dotenv()

SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def get_credentials():
    """Get Google Sheets API credentials."""
    creds = None

    # Token file stores user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Need credentials.json from .env
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


def get_form_submissions(since_date=None, website_filter=None):
    """
    Fetch form submissions from Google Sheets.

    Args:
        since_date: datetime object (default: last 7 days)
        website_filter: 'marceau', 'hvac', or 'shipping' (default: all)

    Returns:
        List of submissions with categorization
    """

    if not since_date:
        since_date = datetime.now() - timedelta(days=7)

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    # Fetch all submissions from Sheet
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A2:K'  # Default sheet name
    ).execute()

    values = result.get('values', [])

    if not values:
        return []

    submissions = []

    for row in values:
        # Parse row based on actual sheet structure:
        # Timestamp, First Name, Last Name, Business Name, Email, Phone,
        # Project Description, SMS Opt-in, Email Opt-in, Source, Status
        timestamp_str = row[0] if len(row) > 0 else ''
        first_name = row[1] if len(row) > 1 else ''
        last_name = row[2] if len(row) > 2 else ''
        name = f"{first_name} {last_name}".strip()
        company = row[3] if len(row) > 3 else ''
        email = row[4] if len(row) > 4 else ''
        phone = row[5] if len(row) > 5 else ''
        message = row[6] if len(row) > 6 else ''
        source = row[9] if len(row) > 9 else ''  # Column 10 (0-indexed = 9)

        # Parse timestamp - try multiple formats
        timestamp = None
        timestamp_formats = [
            '%Y-%m-%dT%H:%M:%S',      # ISO format: 2026-01-15T12:07:00
            '%Y-%m-%d %H:%M:%S',      # Standard: 2026-01-15 12:07:00
            '%m/%d/%Y %H:%M:%S',      # US format: 01/15/2026 12:07:00
            '%Y-%m-%dT%H:%M:%S.%f',   # ISO with microseconds
        ]
        for fmt in timestamp_formats:
            try:
                timestamp = datetime.strptime(timestamp_str, fmt)
                break
            except ValueError:
                continue

        if not timestamp:
            continue  # Skip rows with invalid timestamps

        # Filter by date
        if timestamp < since_date:
            continue

        # Filter by website
        if website_filter:
            if website_filter.lower() == 'marceau' and 'marceausolutions.com' not in source.lower():
                continue
            elif website_filter.lower() == 'hvac' and 'hvac' not in source.lower():
                continue
            elif website_filter.lower() == 'shipping' and 'shipping' not in source.lower():
                continue

        submissions.append({
            'timestamp': timestamp,
            'name': name,
            'email': email,
            'phone': phone,
            'company': company,
            'message': message,
            'source': source,
            'age_days': (datetime.now() - timestamp).days,
            'age_hours': (datetime.now() - timestamp).seconds // 3600
        })

    return submissions


def categorize_submissions(submissions):
    """Categorize submissions by urgency and source."""

    categories = {
        'hot': [],      # <24 hours old, not responded
        'warm': [],     # 24-72 hours old, not responded
        'cold': [],     # >72 hours old, not responded
        'by_source': {
            'marceau': [],
            'hvac': [],
            'shipping': []
        }
    }

    for sub in submissions:
        # Categorize by age
        if sub['age_days'] == 0 and sub['age_hours'] < 24:
            categories['hot'].append(sub)
        elif sub['age_days'] <= 3:
            categories['warm'].append(sub)
        else:
            categories['cold'].append(sub)

        # Categorize by source
        if 'marceausolutions.com' in sub['source'].lower():
            categories['by_source']['marceau'].append(sub)
        elif 'hvac' in sub['source'].lower():
            categories['by_source']['hvac'].append(sub)
        elif 'shipping' in sub['source'].lower():
            categories['by_source']['shipping'].append(sub)

    return categories


def generate_report(submissions, since_date=None):
    """Generate human-readable report."""

    print("\n" + "="*60)
    print("FORM SUBMISSION REPORT")
    print("="*60)

    if since_date:
        print(f"Period: {since_date.date()} to {datetime.now().date()}")
    else:
        print(f"Period: Last 7 days")

    print(f"Total Submissions: {len(submissions)}")
    print("\n")

    if len(submissions) == 0:
        print("✅ No form submissions in this period")
        print("\n")
        return

    # Categorize
    categories = categorize_submissions(submissions)

    # Hot leads (urgent)
    print("🔥 HOT LEADS (< 24 hours old) - RESPOND IMMEDIATELY")
    print("-" * 60)
    if len(categories['hot']) > 0:
        for sub in categories['hot']:
            print(f"   [{sub['timestamp'].strftime('%Y-%m-%d %H:%M')}] {sub['name']} ({sub['email']})")
            print(f"      Company: {sub['company']}")
            print(f"      Source: {sub['source']}")
            print(f"      Message: {sub['message'][:100]}...")
            print(f"      Age: {sub['age_hours']} hours ago")
            print("")
    else:
        print("   None")
    print("\n")

    # Warm leads
    print("⚠️  WARM LEADS (24-72 hours old) - RESPOND TODAY")
    print("-" * 60)
    if len(categories['warm']) > 0:
        for sub in categories['warm']:
            print(f"   [{sub['timestamp'].strftime('%Y-%m-%d %H:%M')}] {sub['name']} ({sub['email']})")
            print(f"      Company: {sub['company']}")
            print(f"      Source: {sub['source']}")
            print(f"      Age: {sub['age_days']} days ago")
            print("")
    else:
        print("   None")
    print("\n")

    # Cold leads (overdue)
    print("❄️  COLD LEADS (> 72 hours old) - OVERDUE")
    print("-" * 60)
    if len(categories['cold']) > 0:
        for sub in categories['cold']:
            print(f"   [{sub['timestamp'].strftime('%Y-%m-%d %H:%M')}] {sub['name']} ({sub['email']})")
            print(f"      Company: {sub['company']}")
            print(f"      Source: {sub['source']}")
            print(f"      Age: {sub['age_days']} days ago")
            print("")
    else:
        print("   None")
    print("\n")

    # By website
    print("📊 BREAKDOWN BY WEBSITE")
    print("-" * 60)
    print(f"   Marceau Solutions: {len(categories['by_source']['marceau'])} submissions")
    print(f"   SW Florida Comfort HVAC: {len(categories['by_source']['hvac'])} submissions")
    print(f"   Square Foot Shipping: {len(categories['by_source']['shipping'])} submissions")
    print("\n")

    # Action items
    print("✅ ACTION ITEMS")
    print("-" * 60)
    if len(categories['hot']) > 0:
        print(f"   1. Respond to {len(categories['hot'])} HOT leads within 4 hours")
    if len(categories['warm']) > 0:
        print(f"   2. Respond to {len(categories['warm'])} WARM leads today")
    if len(categories['cold']) > 0:
        print(f"   3. Follow up on {len(categories['cold'])} COLD leads (apologize for delay)")

    if len(categories['hot']) == 0 and len(categories['warm']) == 0 and len(categories['cold']) == 0:
        print("   All caught up! No pending responses.")

    print("\n")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Check form submissions across all websites')
    parser.add_argument('--since', help='Start date (YYYY-MM-DD)', default=None)
    parser.add_argument('--website', choices=['marceau', 'hvac', 'shipping'], help='Filter by website')

    args = parser.parse_args()

    since_date = None
    if args.since:
        since_date = datetime.strptime(args.since, '%Y-%m-%d')
    else:
        since_date = datetime.now() - timedelta(days=7)  # Default: last 7 days

    submissions = get_form_submissions(since_date=since_date, website_filter=args.website)
    generate_report(submissions, since_date=since_date)
