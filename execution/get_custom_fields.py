#!/usr/bin/env python3
"""Get custom field IDs from ClickUp"""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"
CLICKUP_API_TOKEN = os.getenv('CLICKUP_API_TOKEN')
INTAKE_LIST_ID = "901709133703"


def get_headers():
    return {
        "Authorization": CLICKUP_API_TOKEN,
        "Content-Type": "application/json"
    }


def get_custom_fields(list_id):
    """Get all custom fields for a list"""
    url = f"{CLICKUP_API_BASE}/list/{list_id}/field"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    fields = get_custom_fields(INTAKE_LIST_ID)

    print("Custom Field IDs:")
    field_map = {}
    for field in fields['fields']:
        print(f"  {field['name']}: {field['id']}")
        field_map[field['name']] = field['id']

    # Save to file for use in add_lead.py
    with open('execution/custom_field_ids.json', 'w') as f:
        json.dump(field_map, f, indent=2)

    print("\n✅ Saved to execution/custom_field_ids.json")
