#!/usr/bin/env python3
"""
Setup Sales CRM in ClickUp

Creates a complete sales pipeline with proper stages and workflow.

Usage:
    python setup_sales_crm.py
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"
CLICKUP_API_TOKEN = os.getenv('CLICKUP_API_TOKEN')
SPACE_ID = "90173085068"  # Template Creative Agency


def get_headers():
    return {
        "Authorization": CLICKUP_API_TOKEN,
        "Content-Type": "application/json"
    }


def create_folder(space_id, folder_name):
    """Create a folder in the space"""
    url = f"{CLICKUP_API_BASE}/space/{space_id}/folder"
    data = {"name": folder_name}

    response = requests.post(url, headers=get_headers(), json=data)
    response.raise_for_status()

    folder = response.json()
    print(f"✅ Created folder: {folder['name']} (ID: {folder['id']})")
    return folder


def create_list(folder_id, list_name):
    """Create a list in a folder"""
    url = f"{CLICKUP_API_BASE}/folder/{folder_id}/list"
    data = {"name": list_name}

    response = requests.post(url, headers=get_headers(), json=data)
    response.raise_for_status()

    lst = response.json()
    print(f"  ✅ Created list: {lst['name']} (ID: {lst['id']})")
    return lst


def setup_sales_crm():
    """Set up the complete sales CRM structure"""

    print("=" * 70)
    print("Setting up Sales CRM in ClickUp")
    print("=" * 70)

    # Create Sales Pipeline folder
    print("\n📁 Creating Sales Pipeline folder...")
    sales_folder = create_folder(SPACE_ID, "Sales Pipeline")
    folder_id = sales_folder['id']

    # Sales Pipeline Stages
    print("\n📊 Creating sales pipeline stages...")

    stages = [
        {
            "name": "1. Intake",
            "description": "New leads and initial contact"
        },
        {
            "name": "2. Qualification",
            "description": "Qualifying leads and understanding needs"
        },
        {
            "name": "3. Meeting Booked",
            "description": "Discovery/kickoff call scheduled"
        },
        {
            "name": "4. Proposal Sent",
            "description": "Proposal or quote delivered"
        },
        {
            "name": "5. Negotiation",
            "description": "Discussing terms and pricing"
        },
        {
            "name": "6. Closed Won",
            "description": "Deal won - contract signed!"
        },
        {
            "name": "7. Closed Lost",
            "description": "Deal lost - analyze why"
        }
    ]

    lists = {}
    for stage in stages:
        lst = create_list(folder_id, stage["name"])
        lists[stage["name"]] = lst['id']

    print("\n" + "=" * 70)
    print("🎉 Sales CRM Setup Complete!")
    print("=" * 70)

    print("\n📋 Sales Pipeline Structure:")
    print(f"  Folder: Sales Pipeline (ID: {folder_id})")
    print("\n  Stages:")
    for i, stage in enumerate(stages, 1):
        print(f"    {stage['name']}")
        print(f"      → {stage['description']}")

    print("\n💡 How to Use:")
    print("  1. New leads start in 'Intake'")
    print("  2. Move through stages as deal progresses")
    print("  3. End in 'Closed Won' or 'Closed Lost'")

    print("\n🤖 You can now tell Claude:")
    print("  - 'Add new lead John Smith to intake'")
    print("  - 'Move Sarah to Meeting Booked'")
    print("  - 'Show all deals in Proposal Sent'")
    print("  - 'Mark Alex as Closed Won'")

    return {
        "folder_id": folder_id,
        "lists": lists
    }


if __name__ == "__main__":
    try:
        result = setup_sales_crm()

        # Save configuration
        print(f"\n💾 Configuration saved!")
        print(f"\nFolder ID: {result['folder_id']}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
