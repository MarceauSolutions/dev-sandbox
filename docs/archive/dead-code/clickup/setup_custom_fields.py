#!/usr/bin/env python3
"""
Setup Custom Fields for Sales CRM

Creates custom field columns in ClickUp for customer information.
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"
CLICKUP_API_TOKEN = os.getenv('CLICKUP_API_TOKEN')

# List IDs for all pipeline stages
PIPELINE_LISTS = {
    "Intake": "901709133703",
    "Qualification": "901709133704",
    "Meeting Booked": "901709133705",
    "Proposal Sent": "901709133706",
    "Negotiation": "901709133707",
    "Closed Won": "901709133708",
    "Closed Lost": "901709133709"
}


def get_headers():
    return {
        "Authorization": CLICKUP_API_TOKEN,
        "Content-Type": "application/json"
    }


def create_custom_field(list_id, field_name, field_type, type_config=None):
    """Create a custom field in a list"""
    url = f"{CLICKUP_API_BASE}/list/{list_id}/field"

    data = {
        "name": field_name,
        "type": field_type
    }

    if type_config:
        data["type_config"] = type_config

    try:
        response = requests.post(url, headers=get_headers(), json=data)
        response.raise_for_status()
        field = response.json()
        print(f"  ✅ Created field: {field_name}")
        return field
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and "already exists" in e.response.text.lower():
            print(f"  ⚠️  Field already exists: {field_name}")
            return None
        else:
            raise


def setup_custom_fields_for_list(list_id, list_name):
    """Set up all custom fields for a single list"""
    print(f"\n📋 Setting up custom fields for: {list_name}")

    # Email field
    create_custom_field(list_id, "Email", "email")

    # Phone field
    create_custom_field(list_id, "Phone", "phone")

    # Company field
    create_custom_field(list_id, "Company", "short_text")

    # Budget field (currency)
    create_custom_field(list_id, "Budget", "currency", {
        "currency_type": "USD",
        "precision": 0
    })

    # Project Type field
    create_custom_field(list_id, "Project Type", "short_text")

    # Timeline field
    create_custom_field(list_id, "Timeline", "short_text")

    # Referral Source dropdown
    create_custom_field(list_id, "Referral Source", "drop_down", {
        "options": [
            {"name": "Website", "color": "#3498db"},
            {"name": "LinkedIn", "color": "#0077b5"},
            {"name": "Referral", "color": "#2ecc71"},
            {"name": "Cold Outreach", "color": "#95a5a6"},
            {"name": "Social Media", "color": "#e74c3c"},
            {"name": "Event", "color": "#f39c12"},
            {"name": "Other", "color": "#9b59b6"}
        ]
    })

    # Priority/Temperature field
    create_custom_field(list_id, "Lead Temperature", "drop_down", {
        "options": [
            {"name": "Hot 🔥", "color": "#e74c3c"},
            {"name": "Warm 🌡️", "color": "#f39c12"},
            {"name": "Cold ❄️", "color": "#3498db"}
        ]
    })


def main():
    print("=" * 70)
    print("Setting Up Custom Fields for Sales CRM")
    print("=" * 70)

    for list_name, list_id in PIPELINE_LISTS.items():
        setup_custom_fields_for_list(list_id, list_name)

    print("\n" + "=" * 70)
    print("✅ Custom Fields Setup Complete!")
    print("=" * 70)

    print("\n📊 Custom Fields Created:")
    print("  • Email")
    print("  • Phone")
    print("  • Company")
    print("  • Budget (USD)")
    print("  • Project Type")
    print("  • Timeline")
    print("  • Referral Source (dropdown)")
    print("  • Lead Temperature (Hot/Warm/Cold)")

    print("\n💡 These fields will now appear as columns in your ClickUp lists!")
    print("   You can show/hide columns and filter by these fields.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
