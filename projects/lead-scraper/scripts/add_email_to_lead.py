#!/usr/bin/env python3
"""
Quick script to add emails to leads after manual collection.

Usage:
    python scripts/add_email_to_lead.py "Business Name" "email@domain.com"
    python scripts/add_email_to_lead.py "Soluna Restaurant" "owner@solunanaples.net"
"""

import sys
import json
from pathlib import Path

def add_email(business_name: str, email: str):
    """Add email to a lead by business name."""
    leads_file = Path("output/leads.json")
    
    # Load leads
    with open(leads_file) as f:
        leads = json.load(f)
    
    # Find matching lead
    found = False
    for lead_id, lead in leads.items():
        if lead.get("business_name", "").lower() == business_name.lower():
            lead["email"] = email
            found = True
            print(f"✅ Added email to: {lead['business_name']}")
            print(f"   Email: {email}")
            break
    
    if not found:
        print(f"❌ Lead not found: {business_name}")
        print(f"   Try exact name from CSV")
        return False
    
    # Save
    with open(leads_file, 'w') as f:
        json.dump(leads, f, indent=2)
    
    print(f"✅ Database updated")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/add_email_to_lead.py 'Business Name' 'email@domain.com'")
        sys.exit(1)
    
    business_name = sys.argv[1]
    email = sys.argv[2]
    
    add_email(business_name, email)
