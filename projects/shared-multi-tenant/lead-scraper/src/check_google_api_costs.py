"""
Google Cloud API Cost Checker
Tracks API usage and alerts when approaching billing thresholds.

Usage:
    python -m src.check_google_api_costs
    python -m src.check_google_api_costs --detailed
    python -m src.check_google_api_costs --alert-threshold 10
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Cost constants (per 1,000 requests)
PLACES_NEARBY_SEARCH_COST = 32.00  # $32 per 1K
PLACES_TEXT_SEARCH_COST = 32.00    # $32 per 1K
PLACES_DETAILS_BASIC_COST = 17.00  # $17 per 1K (basic fields)
PLACES_DETAILS_CONTACT_COST = 3.00 # Additional $3 for contact fields
PLACES_DETAILS_ATMOSPHERE_COST = 5.00  # Additional $5 for atmosphere fields

# Estimate: Using basic + contact + atmosphere = $25 total
PLACES_DETAILS_FULL_COST = 17.00 + 3.00 + 5.00  # $25 per 1K

# Free tier (until March 1, 2025)
FREE_TIER_CREDIT = 200.00  # $200/month


class GoogleAPIUsageTracker:
    """Tracks Google Places API usage and costs."""

    def __init__(self, leads_file: str = "output/leads.json"):
        self.leads_file = Path(__file__).parent.parent / leads_file
        self.usage_log_file = Path(__file__).parent.parent / "output/google_api_usage.json"

    def count_api_calls_from_leads(self) -> Dict[str, int]:
        """
        Estimate API calls based on leads scraped.
        Each lead requires ~2.5 API calls on average:
        - 1 Nearby/Text Search call (returns 20 leads, so 1/20 = 0.05 per lead)
        - 1 Place Details call (1 per lead)
        - ~1.5 calls for pagination and retries
        """
        if not self.leads_file.exists():
            return {"google_places_leads": 0, "estimated_api_calls": 0}

        with open(self.leads_file, 'r') as f:
            data = json.load(f)

        leads = data.get('leads', [])

        # Count leads from Google Places
        google_leads = [
            lead for lead in leads
            if lead.get('source', '').startswith('google_places')
        ]

        # Estimate API calls
        # Nearby/Text Search: Assume 20 results per call, so total_leads / 20
        # Place Details: 1 call per lead
        # Total: (total_leads / 20) + total_leads = total_leads * 1.05
        # Add 50% for pagination, retries, etc. = total_leads * 1.05 * 1.5 = 2.5

        estimated_calls = {
            'google_places_leads': len(google_leads),
            'nearby_search_calls': len(google_leads) // 20 + 1,  # ~5% of leads
            'place_details_calls': len(google_leads),  # 1 per lead
            'total_estimated_calls': int(len(google_leads) * 2.5),  # Conservative estimate
        }

        return estimated_calls

    def calculate_costs(self, api_calls: Dict[str, int]) -> Dict[str, float]:
        """Calculate estimated costs based on API call counts."""

        nearby_cost = (api_calls.get('nearby_search_calls', 0) / 1000) * PLACES_NEARBY_SEARCH_COST
        details_cost = (api_calls.get('place_details_calls', 0) / 1000) * PLACES_DETAILS_FULL_COST
        total_cost = nearby_cost + details_cost

        return {
            'nearby_search_cost': round(nearby_cost, 2),
            'place_details_cost': round(details_cost, 2),
            'total_estimated_cost': round(total_cost, 2),
            'free_tier_remaining': round(FREE_TIER_CREDIT - total_cost, 2),
            'percentage_of_free_tier': round((total_cost / FREE_TIER_CREDIT) * 100, 1)
        }

    def log_usage(self, api_calls: Dict[str, int], costs: Dict[str, float]):
        """Log usage to file for historical tracking."""
        usage_entry = {
            'timestamp': datetime.now().isoformat(),
            'api_calls': api_calls,
            'costs': costs
        }

        # Load existing log
        usage_log = []
        if self.usage_log_file.exists():
            with open(self.usage_log_file, 'r') as f:
                usage_log = json.load(f)

        # Append new entry
        usage_log.append(usage_entry)

        # Keep only last 90 days
        cutoff_date = datetime.now() - timedelta(days=90)
        usage_log = [
            entry for entry in usage_log
            if datetime.fromisoformat(entry['timestamp']) > cutoff_date
        ]

        # Save updated log
        with open(self.usage_log_file, 'w') as f:
            json.dump(usage_log, f, indent=2)

    def get_usage_trend(self, days: int = 7) -> List[Dict]:
        """Get usage trend for last N days."""
        if not self.usage_log_file.exists():
            return []

        with open(self.usage_log_file, 'r') as f:
            usage_log = json.load(f)

        cutoff_date = datetime.now() - timedelta(days=days)
        recent = [
            entry for entry in usage_log
            if datetime.fromisoformat(entry['timestamp']) > cutoff_date
        ]

        return recent

    def send_alert(self, message: str):
        """Send SMS alert via Twilio if costs exceed threshold."""
        try:
            from twilio.rest import Client

            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            from_number = os.getenv('TWILIO_PHONE_NUMBER')
            to_number = os.getenv('NOTIFICATION_PHONE')

            if not all([account_sid, auth_token, from_number, to_number]):
                print("⚠️  Twilio credentials not configured, skipping SMS alert")
                return

            client = Client(account_sid, auth_token)
            client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            print(f"✅ SMS alert sent to {to_number}")

        except Exception as e:
            print(f"⚠️  Failed to send SMS alert: {e}")

    def generate_report(self, detailed: bool = False, alert_threshold: float = 50.0):
        """Generate usage and cost report."""

        # Get API call counts
        api_calls = self.count_api_calls_from_leads()

        # Calculate costs
        costs = self.calculate_costs(api_calls)

        # Log usage
        self.log_usage(api_calls, costs)

        # Print report
        print("\n" + "=" * 60)
        print("📊 GOOGLE PLACES API USAGE & COST REPORT")
        print("=" * 60)
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Free tier: ${FREE_TIER_CREDIT}/month (until March 1, 2025)")
        print("=" * 60)

        print("\n📍 API USAGE:")
        print(f"  Google Places leads scraped: {api_calls['google_places_leads']:,}")
        print(f"  Estimated Nearby Search calls: {api_calls['nearby_search_calls']:,}")
        print(f"  Estimated Place Details calls: {api_calls['place_details_calls']:,}")
        print(f"  TOTAL estimated API calls: {api_calls['total_estimated_calls']:,}")

        print("\n💰 ESTIMATED COSTS:")
        print(f"  Nearby Search: ${costs['nearby_search_cost']:.2f}")
        print(f"  Place Details: ${costs['place_details_cost']:.2f}")
        print(f"  TOTAL: ${costs['total_estimated_cost']:.2f}")

        print("\n🎁 FREE TIER STATUS:")
        print(f"  Used: ${costs['total_estimated_cost']:.2f} / ${FREE_TIER_CREDIT}")
        print(f"  Remaining: ${costs['free_tier_remaining']:.2f}")
        print(f"  Percentage used: {costs['percentage_of_free_tier']:.1f}%")

        # Alert if threshold exceeded
        if costs['total_estimated_cost'] > alert_threshold:
            status = "🚨 ALERT"
            alert_msg = f"🚨 Google API costs: ${costs['total_estimated_cost']:.2f} (threshold: ${alert_threshold})"
            self.send_alert(alert_msg)
        elif costs['percentage_of_free_tier'] > 50:
            status = "⚠️  WARNING"
        else:
            status = "✅ OK"

        print(f"\n  STATUS: {status}")

        # Detailed report
        if detailed:
            print("\n" + "=" * 60)
            print("📈 USAGE TREND (Last 7 Days)")
            print("=" * 60)

            trend = self.get_usage_trend(days=7)
            if trend:
                print(f"\n  Total entries: {len(trend)}")
                for entry in trend[-5:]:  # Show last 5 entries
                    timestamp = entry['timestamp']
                    cost = entry['costs']['total_estimated_cost']
                    calls = entry['api_calls']['total_estimated_calls']
                    print(f"  {timestamp}: {calls:,} calls, ${cost:.2f}")
            else:
                print("  No historical data available")

            print("\n" + "=" * 60)
            print("💡 COST-SAVING TIPS")
            print("=" * 60)
            print("  1. Implement caching (80% cost reduction)")
            print("  2. Use Yelp API as primary source (free)")
            print("  3. Reduce search radius (30-50% savings)")
            print("  4. Remove atmosphere fields (33% savings)")
            print("  5. Set API quotas to prevent runaway costs")
            print("\n  See: /docs/GOOGLE-CLOUD-COST-ANALYSIS.md for details")

        print("\n" + "=" * 60)
        print("✅ Report complete")
        print("=" * 60 + "\n")

        return {
            'api_calls': api_calls,
            'costs': costs,
            'status': status
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Check Google Places API usage and costs')
    parser.add_argument('--detailed', action='store_true', help='Show detailed report with trends')
    parser.add_argument('--alert-threshold', type=float, default=50.0,
                       help='Send SMS alert if costs exceed this amount (default: $50)')
    args = parser.parse_args()

    tracker = GoogleAPIUsageTracker()
    tracker.generate_report(detailed=args.detailed, alert_threshold=args.alert_threshold)


if __name__ == '__main__':
    main()
