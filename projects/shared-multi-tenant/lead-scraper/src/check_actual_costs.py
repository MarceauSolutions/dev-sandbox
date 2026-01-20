#!/usr/bin/env python3
"""
Check actual costs to date for all Marceau Solutions infrastructure.

Usage:
  python -m src.check_actual_costs
  python -m src.check_actual_costs --since 2026-01-01
  python -m src.check_actual_costs --detailed
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from twilio.rest import Client
import json

# Load environment variables
load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')


def get_twilio_actual_costs(since_date=None):
    """Get ACTUAL Twilio costs from API (not estimates)."""

    if not since_date:
        # Default to start of year
        since_date = datetime(2026, 1, 1)

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    # Get SMS usage
    try:
        sms_records = client.usage.records.list(
            category='sms',
            start_date=since_date.date(),
            end_date=datetime.now().date()
        )

        sms_count = sum([int(record.count) for record in sms_records])
        sms_cost = sum([float(record.price) for record in sms_records])

    except Exception as e:
        print(f"Warning: Could not fetch SMS usage: {e}")
        sms_count = 0
        sms_cost = 0.0

    # Get Voice usage
    try:
        voice_records = client.usage.records.list(
            category='calls',
            start_date=since_date.date(),
            end_date=datetime.now().date()
        )

        voice_count = sum([int(record.count) for record in voice_records])
        voice_cost = sum([float(record.price) for record in voice_records])

    except Exception as e:
        print(f"Warning: Could not fetch voice usage: {e}")
        voice_count = 0
        voice_cost = 0.0

    # Get phone number rental costs
    try:
        phone_numbers = client.incoming_phone_numbers.list()
        phone_rental_cost = len(phone_numbers) * 1.00  # $1/month per number (approximate)

    except Exception as e:
        print(f"Warning: Could not fetch phone numbers: {e}")
        phone_rental_cost = 0.0

    # Get account balance
    try:
        balance = client.api.v2010.balance.fetch()
        current_balance = float(balance.balance)
        currency = balance.currency
    except Exception as e:
        print(f"Warning: Could not fetch balance: {e}")
        current_balance = 0.0
        currency = "USD"

    return {
        'sms': {
            'count': sms_count,
            'cost': abs(sms_cost)  # Twilio returns negative for charges
        },
        'voice': {
            'count': voice_count,
            'cost': abs(voice_cost)
        },
        'phone_rental': {
            'numbers': len(phone_numbers) if 'phone_numbers' in locals() else 0,
            'cost': phone_rental_cost
        },
        'account': {
            'balance': current_balance,
            'currency': currency
        },
        'total_twilio_cost': abs(sms_cost) + abs(voice_cost) + phone_rental_cost
    }


def get_fixed_infrastructure_costs():
    """Calculate fixed monthly infrastructure costs."""

    # Monthly fixed costs (comprehensive)
    return {
        'hosting': {
            'service': 'GitHub Pages',
            'cost': 0.00,
            'note': 'Free tier'
        },
        'domains': {
            'service': 'Domain registrations (2)',
            'cost': 2.00,
            'note': 'swflorida-comfort-hvac.com + squarefoot-shipping.com'
        },
        'crm': {
            'service': 'ClickUp',
            'cost': 0.00,
            'note': 'Free tier'
        },
        'google_workspace': {
            'service': 'Google Workspace',
            'cost': 6.00,
            'note': 'Email, Sheets, Forms'
        },
        'claude_api': {
            'service': 'Claude API (Anthropic)',
            'cost': 100.00,
            'note': '$100/month subscription'
        },
        'ngrok': {
            'service': 'ngrok (AI webhook tunneling)',
            'cost': 20.00,
            'note': 'Pay-as-you-go plan'
        },
        'apollo_io': {
            'service': 'Apollo.io (Lead enrichment)',
            'cost': 59.00,
            'note': 'Basic plan - underutilized!'
        },
        'google_places': {
            'service': 'Google Places API',
            'cost': 0.00,
            'note': 'Under $200/month free tier'
        },
        'yelp': {
            'service': 'Yelp Fusion API',
            'cost': 0.00,
            'note': 'Free tier (5,000 calls/day)'
        },
        'shotstack': {
            'service': 'Shotstack (Video generation)',
            'cost': 0.00,
            'note': '$10 credits remaining (pay-as-you-go)'
        },
        'xai': {
            'service': 'xAI/Grok (Image generation)',
            'cost': 25.00,
            'note': '$24.99/month ($13.06 used so far)'
        },
        'creatomate': {
            'service': 'Creatomate (Video generation)',
            'cost': 0.00,
            'note': 'Free trial (not charged yet)'
        },
        'x_api': {
            'service': 'X (Twitter) API',
            'cost': 0.00,
            'note': 'Free tier'
        },
        'elevenlabs_voice': {
            'service': 'ElevenLabs Voice AI (phone calls)',
            'cost': 0.00,
            'note': 'Need to check - used for AI customer service'
        },
        'total_fixed': 212.00  # $212/month in API subscriptions
    }


def get_campaign_costs():
    """Check if any campaigns have actually been run."""

    # Check for SMS campaign data
    campaign_file = '/Users/williammarceaujr./dev-sandbox/projects/lead-scraper/output/sms_campaigns.json'

    if os.path.exists(campaign_file):
        try:
            with open(campaign_file, 'r') as f:
                campaigns = json.load(f)

            total_campaign_spend = 0
            campaign_summary = []

            for campaign in campaigns:
                if 'cost' in campaign:
                    total_campaign_spend += campaign['cost']
                    campaign_summary.append({
                        'name': campaign.get('name', 'Unknown'),
                        'contacts': campaign.get('contacts_sent', 0),
                        'cost': campaign.get('cost', 0)
                    })

            return {
                'campaigns_run': len(campaigns),
                'total_spend': total_campaign_spend,
                'campaigns': campaign_summary
            }
        except Exception as e:
            print(f"Warning: Could not read campaign data: {e}")

    return {
        'campaigns_run': 0,
        'total_spend': 0.00,
        'campaigns': []
    }


def generate_cost_report(since_date=None, detailed=False):
    """Generate comprehensive cost report."""

    print("\n" + "="*60)
    print("MARCEAU SOLUTIONS - ACTUAL COSTS TO DATE")
    print("="*60)

    if since_date:
        print(f"Period: {since_date.date()} to {datetime.now().date()}")
    else:
        print(f"Period: 2026-01-01 to {datetime.now().date()}")

    print("\n")

    # 1. Twilio costs (variable)
    print("1. TWILIO USAGE (Variable Costs)")
    print("-" * 60)

    twilio = get_twilio_actual_costs(since_date)

    print(f"   SMS Messages Sent: {twilio['sms']['count']:,}")
    print(f"   SMS Cost: ${twilio['sms']['cost']:.2f}")
    print(f"   Voice Calls: {twilio['voice']['count']:,}")
    print(f"   Voice Cost: ${twilio['voice']['cost']:.2f}")
    print(f"   Phone Numbers: {twilio['phone_rental']['numbers']}")
    print(f"   Phone Rental: ${twilio['phone_rental']['cost']:.2f}/month")
    print(f"   ")
    print(f"   TOTAL TWILIO: ${twilio['total_twilio_cost']:.2f}")
    print(f"   Current Balance: ${twilio['account']['balance']:.2f} {twilio['account']['currency']}")

    print("\n")

    # 2. Fixed infrastructure costs
    print("2. FIXED INFRASTRUCTURE (Monthly)")
    print("-" * 60)

    fixed = get_fixed_infrastructure_costs()

    for service, details in fixed.items():
        if service != 'total_fixed':
            print(f"   {details['service']}: ${details['cost']:.2f} - {details['note']}")

    print(f"   ")
    print(f"   TOTAL FIXED: ${fixed['total_fixed']:.2f}/month")

    print("\n")

    # 3. Campaign costs
    print("3. CAMPAIGN SPENDING")
    print("-" * 60)

    campaigns = get_campaign_costs()

    if campaigns['campaigns_run'] > 0:
        print(f"   Campaigns Run: {campaigns['campaigns_run']}")

        if detailed:
            for camp in campaigns['campaigns']:
                print(f"   - {camp['name']}: {camp['contacts']} contacts @ ${camp['cost']:.2f}")

        print(f"   ")
        print(f"   TOTAL CAMPAIGN SPEND: ${campaigns['total_spend']:.2f}")
    else:
        print("   No campaigns run yet")
        print(f"   TOTAL CAMPAIGN SPEND: $0.00")

    print("\n")

    # 4. TOTAL SUMMARY
    print("="*60)
    print("TOTAL COSTS SUMMARY")
    print("="*60)

    total_variable = twilio['total_twilio_cost'] + campaigns['total_spend']
    total_fixed_monthly = fixed['total_fixed']

    # Calculate days elapsed this month to prorate fixed costs
    today = datetime.now()
    days_in_month = 31  # January
    days_elapsed = today.day
    prorated_fixed = (total_fixed_monthly / days_in_month) * days_elapsed

    grand_total = total_variable + prorated_fixed

    print(f"Variable Costs (Twilio + Campaigns): ${total_variable:.2f}")
    print(f"Fixed Costs (Prorated for {days_elapsed} days): ${prorated_fixed:.2f}")
    print(f"")
    print(f"GRAND TOTAL TO DATE: ${grand_total:.2f}")
    print(f"Monthly Burn Rate: ${total_fixed_monthly + total_variable:.2f}/month")
    print("")

    # Budget check
    budget_limit = 500.00  # From COST-BUDGET-TRACKING-JAN-19-2026.md
    percent_used = (grand_total / budget_limit) * 100

    if grand_total < budget_limit:
        print(f"✅ BUDGET STATUS: UNDER LIMIT")
        print(f"   ${grand_total:.2f} / ${budget_limit:.2f} spent ({percent_used:.1f}%)")
        print(f"   Remaining: ${budget_limit - grand_total:.2f}")
    else:
        print(f"⚠️  BUDGET STATUS: OVER LIMIT")
        print(f"   ${grand_total:.2f} / ${budget_limit:.2f} spent ({percent_used:.1f}%)")
        print(f"   Over by: ${grand_total - budget_limit:.2f}")

    print("\n")

    # 5. Notes and context
    print("NOTES:")
    print("-" * 60)
    print("• Fixed costs are prorated based on days elapsed this month")
    print("• HVAC (SW Florida Comfort) is testimonial client (dad)")
    print("• Shipping (Square Foot) is testimonial client (friend)")
    print("• Revenue from these projects = side income helping on jobs")
    print("• Budget limit: $500/month for practice projects")
    print("• Month 1 plan: $6 (SMS testing only)")
    print("")

    return {
        'twilio': twilio,
        'fixed': fixed,
        'campaigns': campaigns,
        'totals': {
            'variable': total_variable,
            'fixed_prorated': prorated_fixed,
            'grand_total': grand_total,
            'monthly_burn': total_fixed_monthly + total_variable,
            'budget_limit': budget_limit,
            'percent_used': percent_used
        }
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Check actual infrastructure costs')
    parser.add_argument('--since', help='Start date (YYYY-MM-DD)', default=None)
    parser.add_argument('--detailed', action='store_true', help='Show detailed breakdown')

    args = parser.parse_args()

    since_date = None
    if args.since:
        since_date = datetime.strptime(args.since, '%Y-%m-%d')

    report = generate_cost_report(since_date=since_date, detailed=args.detailed)
