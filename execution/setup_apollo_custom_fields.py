#!/usr/bin/env python3
"""
Setup Apollo-Specific Custom Fields for ClickUp CRM

Adds fields required for Apollo lead tracking:
- Apollo ID (for deduplication/linking)
- Apollo Score (0-10 lead score)
- Email Verified (checkbox)
- Phone Available (checkbox)
- Search Profile (which Apollo profile was used)
- Data Source (apollo, form, sms_reply, etc.)
- Campaign Name (which campaign generated this lead)

Run this ONCE after setting up basic CRM fields.
"""

import requests
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"
CLICKUP_API_TOKEN = os.getenv('CLICKUP_API_TOKEN')

# List IDs for all pipeline stages (from setup_custom_fields.py)
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
        print(f"  ✅ Created field: {field_name} (ID: {field.get('id', 'N/A')})")
        return field
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and "already exists" in e.response.text.lower():
            print(f"  ⚠️  Field already exists: {field_name}")
            return None
        else:
            print(f"  ❌ Failed to create {field_name}: {e.response.text}")
            raise


def get_custom_fields(list_id):
    """Get all custom fields for a list"""
    url = f"{CLICKUP_API_BASE}/list/{list_id}/field"

    response = requests.get(url, headers=get_headers())
    response.raise_for_status()

    return response.json().get('fields', [])


def setup_apollo_fields_for_list(list_id, list_name):
    """Set up Apollo-specific custom fields for a single list"""
    print(f"\n📋 Setting up Apollo fields for: {list_name}")

    # Apollo ID - for tracking/deduplication
    create_custom_field(list_id, "Apollo ID", "short_text")

    # Apollo Score - 0-10 lead quality score
    create_custom_field(list_id, "Apollo Score", "number", {
        "decimal_places": 1
    })

    # Email Verified - checkbox for verified email status
    create_custom_field(list_id, "Email Verified", "checkbox")

    # Phone Available - checkbox for phone availability
    create_custom_field(list_id, "Phone Available", "checkbox")

    # Search Profile - which Apollo search profile was used
    create_custom_field(list_id, "Search Profile", "drop_down", {
        "options": [
            {"name": "naples_gyms", "color": "#e74c3c"},
            {"name": "naples_hvac", "color": "#3498db"},
            {"name": "naples_restaurants", "color": "#f39c12"},
            {"name": "small_business_owners", "color": "#2ecc71"},
            {"name": "verified_contacts_only", "color": "#9b59b6"},
            {"name": "decision_makers_all_sizes", "color": "#1abc9c"},
            {"name": "local_service_businesses", "color": "#e67e22"},
            {"name": "custom", "color": "#95a5a6"}
        ]
    })

    # Data Source - where the lead came from
    create_custom_field(list_id, "Data Source", "drop_down", {
        "options": [
            {"name": "apollo", "color": "#3498db"},
            {"name": "form_submission", "color": "#2ecc71"},
            {"name": "sms_reply", "color": "#f39c12"},
            {"name": "voice_ai", "color": "#9b59b6"},
            {"name": "social_media", "color": "#e74c3c"},
            {"name": "referral", "color": "#1abc9c"},
            {"name": "direct_inquiry", "color": "#e67e22"},
            {"name": "other", "color": "#95a5a6"}
        ]
    })

    # Campaign Name - which campaign generated this lead
    create_custom_field(list_id, "Campaign Name", "short_text")

    # Seniority - decision-maker level
    create_custom_field(list_id, "Seniority", "drop_down", {
        "options": [
            {"name": "Owner", "color": "#e74c3c"},
            {"name": "Founder", "color": "#e74c3c"},
            {"name": "C-Suite", "color": "#f39c12"},
            {"name": "VP", "color": "#f39c12"},
            {"name": "Director", "color": "#3498db"},
            {"name": "Manager", "color": "#3498db"},
            {"name": "Senior", "color": "#95a5a6"},
            {"name": "Entry", "color": "#95a5a6"}
        ]
    })

    # Industry - business category
    create_custom_field(list_id, "Industry", "short_text")

    # Company Size - employee count
    create_custom_field(list_id, "Company Size", "number")

    # LinkedIn URL - for research
    create_custom_field(list_id, "LinkedIn", "url")

    # Website - company website
    create_custom_field(list_id, "Website", "url")


def save_field_ids(list_id):
    """Get all custom field IDs and save to config file"""
    fields = get_custom_fields(list_id)

    field_map = {}
    for field in fields:
        field_map[field['name']] = field['id']

    # Save to config file
    config_file = Path(__file__).parent / "custom_field_ids.json"

    # Merge with existing if present
    if config_file.exists():
        with open(config_file, 'r') as f:
            existing = json.load(f)
        existing.update(field_map)
        field_map = existing

    with open(config_file, 'w') as f:
        json.dump(field_map, f, indent=2)

    print(f"\n💾 Saved {len(field_map)} field IDs to: {config_file}")

    return field_map


def main():
    print("=" * 70)
    print("Setting Up Apollo-Specific Custom Fields for CRM")
    print("=" * 70)

    if not CLICKUP_API_TOKEN:
        print("❌ Error: CLICKUP_API_TOKEN not set in .env")
        print("\nSet this environment variable:")
        print("  export CLICKUP_API_TOKEN='your_token'")
        return

    # Only set up for Intake list first (fields propagate or can be added to others)
    # If you want all lists to have these fields, uncomment the loop
    primary_list_id = PIPELINE_LISTS["Intake"]
    primary_list_name = "Intake"

    setup_apollo_fields_for_list(primary_list_id, primary_list_name)

    # Uncomment to add to all pipeline lists:
    # for list_name, list_id in PIPELINE_LISTS.items():
    #     setup_apollo_fields_for_list(list_id, list_name)

    # Save field IDs for programmatic access
    field_ids = save_field_ids(primary_list_id)

    print("\n" + "=" * 70)
    print("✅ Apollo Custom Fields Setup Complete!")
    print("=" * 70)

    print("\n📊 New Apollo-Specific Fields Created:")
    print("  • Apollo ID (text) - unique identifier for deduplication")
    print("  • Apollo Score (number) - 0-10 lead quality score")
    print("  • Email Verified (checkbox) - verified email status")
    print("  • Phone Available (checkbox) - phone number availability")
    print("  • Search Profile (dropdown) - which search profile was used")
    print("  • Data Source (dropdown) - lead origin (apollo, form, sms, etc.)")
    print("  • Campaign Name (text) - campaign identifier")
    print("  • Seniority (dropdown) - decision-maker level")
    print("  • Industry (text) - business category")
    print("  • Company Size (number) - employee count")
    print("  • LinkedIn (url) - LinkedIn profile")
    print("  • Website (url) - company website")

    print("\n💡 These fields enable:")
    print("   • Full Apollo data tracking in ClickUp")
    print("   • Lead scoring visibility (Apollo Score)")
    print("   • Deduplication via Apollo ID")
    print("   • Campaign attribution and ROI tracking")
    print("   • Filter/sort by Search Profile or Data Source")

    print("\n📁 Field IDs saved to: execution/custom_field_ids.json")
    print("   Used by apollo_to_clickup.py for programmatic access")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
