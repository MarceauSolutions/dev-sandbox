#!/usr/bin/env python3
"""
Revenue and Spend Analytics
Tracks revenue/expenses from Google Sheets and generates reports.

Features:
- Revenue by source (sponsorships, courses, affiliate)
- Expense by category
- Month-over-month growth
- Profit margin analysis

Usage:
    python revenue_analytics.py --sheet-id YOUR_SHEET_ID
    python revenue_analytics.py --sheet-id YOUR_SHEET_ID --month 2026-01
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
from calendar import month_name

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


class RevenueAnalytics:
    """
    Analyze revenue and expenses from Google Sheets.
    """

    # Google Sheets API scopes
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    def __init__(self, sheet_id, credentials_path='credentials.json', token_path='token.json'):
        """
        Initialize revenue analytics.

        Args:
            sheet_id: Google Sheets ID
            credentials_path: Path to OAuth credentials
            token_path: Path to token file
        """
        self.sheet_id = sheet_id
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    def authenticate(self):
        """
        Authenticate with Google Sheets API.

        Returns:
            Sheets service object
        """
        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        # Authenticate if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print(f"ERROR: Credentials file not found: {self.credentials_path}")
                    return None

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('sheets', 'v4', credentials=creds)
        return self.service

    def read_sheet_data(self, range_name):
        """
        Read data from Google Sheet.

        Args:
            range_name: Range to read (e.g., 'Revenue!A1:D100')

        Returns:
            List of rows
        """
        if not self.service:
            return []

        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])
            return values

        except HttpError as error:
            print(f"ERROR: Sheets API error: {error}")
            return []

    def parse_revenue_data(self, data):
        """
        Parse revenue data from sheet rows.

        Expected format:
        Date | Source | Amount | Notes

        Args:
            data: List of rows from sheet

        Returns:
            List of revenue records
        """
        if not data or len(data) < 2:
            return []

        # Skip header row
        header = data[0]
        rows = data[1:]

        records = []
        for row in rows:
            if len(row) < 3:
                continue

            try:
                record = {
                    'date': row[0],
                    'source': row[1],
                    'amount': float(row[2].replace('$', '').replace(',', '')),
                    'notes': row[3] if len(row) > 3 else ''
                }
                records.append(record)
            except (ValueError, IndexError):
                continue

        return records

    def filter_by_month(self, records, month_str):
        """
        Filter records by month.

        Args:
            records: List of revenue/expense records
            month_str: Month string (e.g., '2026-01')

        Returns:
            Filtered records
        """
        filtered = []

        for record in records:
            # Try to parse date
            try:
                date_str = record['date']

                # Handle various date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y']:
                    try:
                        date = datetime.strptime(date_str, fmt)
                        record_month = date.strftime('%Y-%m')

                        if record_month == month_str:
                            filtered.append(record)
                        break
                    except ValueError:
                        continue

            except Exception:
                continue

        return filtered

    def aggregate_by_source(self, records):
        """
        Aggregate revenue by source.

        Args:
            records: List of revenue records

        Returns:
            Dict of {source: total_amount}
        """
        totals = {}

        for record in records:
            source = record['source']
            amount = record['amount']

            if source in totals:
                totals[source] += amount
            else:
                totals[source] = amount

        return totals

    def calculate_growth(self, current_total, previous_total):
        """
        Calculate month-over-month growth percentage.

        Args:
            current_total: Current month total
            previous_total: Previous month total

        Returns:
            Growth percentage
        """
        if previous_total == 0:
            return 0

        growth = ((current_total - previous_total) / previous_total) * 100
        return growth

    def generate_report(self, month_str=None):
        """
        Generate comprehensive revenue/expense report.

        Args:
            month_str: Month to analyze (e.g., '2026-01'), defaults to current month

        Returns:
            Dict with report data
        """
        print(f"\\n{'='*70}")
        print(f"REVENUE & EXPENSE ANALYTICS")
        print(f"{'='*70}\\n")

        # Default to current month
        if not month_str:
            month_str = datetime.now().strftime('%Y-%m')

        # Parse month
        year, month_num = map(int, month_str.split('-'))
        month_name_str = month_name[month_num]

        print(f"→ Analyzing data for {month_name_str} {year}...\\n")

        # Read revenue and expense data
        print(f"→ Fetching data from Google Sheets...")

        revenue_data = self.read_sheet_data('Revenue!A:D')
        expense_data = self.read_sheet_data('Expenses!A:D')

        if not revenue_data and not expense_data:
            print(f"  ⚠️  No data found in sheet")
            return None

        # Parse data
        revenue_records = self.parse_revenue_data(revenue_data)
        expense_records = self.parse_revenue_data(expense_data)  # Same format

        print(f"  ✓ Loaded {len(revenue_records)} revenue transactions")
        print(f"  ✓ Loaded {len(expense_records)} expense transactions\\n")

        # Filter for current month
        current_revenue = self.filter_by_month(revenue_records, month_str)
        current_expenses = self.filter_by_month(expense_records, month_str)

        # Calculate previous month
        prev_date = datetime(year, month_num, 1) - timedelta(days=1)
        prev_month_str = prev_date.strftime('%Y-%m')

        previous_revenue = self.filter_by_month(revenue_records, prev_month_str)
        previous_expenses = self.filter_by_month(expense_records, prev_month_str)

        # Aggregate by source
        revenue_by_source = self.aggregate_by_source(current_revenue)
        expenses_by_category = self.aggregate_by_source(current_expenses)

        # Calculate totals
        total_revenue = sum(revenue_by_source.values())
        total_expenses = sum(expenses_by_category.values())
        net_profit = total_revenue - total_expenses

        prev_total_revenue = sum(r['amount'] for r in previous_revenue)
        prev_total_expenses = sum(e['amount'] for e in previous_expenses)

        # Calculate growth
        revenue_growth = self.calculate_growth(total_revenue, prev_total_revenue)
        expense_growth = self.calculate_growth(total_expenses, prev_total_expenses)

        # Print report
        print(f"💰 REVENUE REPORT - {month_name_str} {year}")
        print(f"{'='*70}\\n")

        print(f"INCOME:")
        for source, amount in sorted(revenue_by_source.items(), key=lambda x: x[1], reverse=True):
            # Calculate growth for this source
            prev_source = sum(r['amount'] for r in previous_revenue if r['source'] == source)
            source_growth = self.calculate_growth(amount, prev_source)

            growth_indicator = "📈" if source_growth > 0 else "📉" if source_growth < 0 else "➡️"
            growth_str = f"({source_growth:+.1f}%)" if prev_source > 0 else "(new)"

            print(f"  {source:20} ${amount:>8,.2f}  {growth_indicator} {growth_str}")

        print(f"  {'-'*45}")
        print(f"  {'TOTAL REVENUE':20} ${total_revenue:>8,.2f}  ({revenue_growth:+.1f}% vs prev month)\\n")

        print(f"EXPENSES:")
        for category, amount in sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category:20} ${amount:>8,.2f}")

        print(f"  {'-'*45}")
        print(f"  {'TOTAL EXPENSES':20} ${total_expenses:>8,.2f}  ({expense_growth:+.1f}% vs prev month)\\n")

        # Profit margin
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        print(f"{'='*70}")
        print(f"NET PROFIT: ${net_profit:,.2f} ({profit_margin:.1f}% margin)")
        print(f"{'='*70}\\n")

        # Insights
        print(f"📊 INSIGHTS:\\n")

        if revenue_growth > 10:
            print(f"  ✅ Strong revenue growth ({revenue_growth:.1f}%)")
        elif revenue_growth > 0:
            print(f"  ➡️  Modest revenue growth ({revenue_growth:.1f}%)")
        else:
            print(f"  ⚠️  Revenue declined ({revenue_growth:.1f}%)")

        if profit_margin > 70:
            print(f"  ✅ Excellent profit margin ({profit_margin:.1f}%)")
        elif profit_margin > 50:
            print(f"  ✅ Healthy profit margin ({profit_margin:.1f}%)")
        else:
            print(f"  ⚠️  Consider cost optimization (margin: {profit_margin:.1f}%)")

        # Top revenue source
        if revenue_by_source:
            top_source = max(revenue_by_source.items(), key=lambda x: x[1])
            top_pct = (top_source[1] / total_revenue * 100) if total_revenue > 0 else 0
            print(f"  💡 Top revenue source: {top_source[0]} ({top_pct:.1f}%)")

        print(f"\\n{'='*70}\\n")

        return {
            'month': month_str,
            'revenue': revenue_by_source,
            'expenses': expenses_by_category,
            'totals': {
                'revenue': total_revenue,
                'expenses': total_expenses,
                'profit': net_profit,
                'margin': profit_margin
            },
            'growth': {
                'revenue': revenue_growth,
                'expenses': expense_growth
            }
        }


def main():
    """CLI for revenue analytics."""
    parser = argparse.ArgumentParser(
        description='Revenue & Expense Analytics - Generate financial reports from Google Sheets'
    )
    parser.add_argument('--sheet-id', required=True, help='Google Sheets ID')
    parser.add_argument('--month', help='Month to analyze (YYYY-MM format, default: current month)')
    parser.add_argument('--credentials', default='credentials.json', help='Path to credentials file')
    parser.add_argument('--token', default='token.json', help='Path to token file')

    args = parser.parse_args()

    # Create analytics instance
    analytics = RevenueAnalytics(
        sheet_id=args.sheet_id,
        credentials_path=args.credentials,
        token_path=args.token
    )

    # Authenticate
    print("→ Authenticating with Google Sheets...")
    service = analytics.authenticate()

    if not service:
        print("\\n✗ Authentication failed")
        return 1

    print("  ✓ Authentication successful")

    # Generate report
    try:
        report = analytics.generate_report(month_str=args.month)

        if not report:
            print("\\n⚠️  Could not generate report")
            return 1

        print(f"📈 Report generated successfully!")

        return 0

    except Exception as e:
        print(f"\\n✗ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
