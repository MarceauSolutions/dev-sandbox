#!/usr/bin/env python3
"""
Add Lead to Sales CRM with Full Customer Information

Usage:
    python add_lead.py --name "John Smith" --email "john@example.com" --phone "555-1234" --budget "10000" --project "Website redesign"
    python add_lead.py --interactive  # Interactive mode with prompts
"""

import requests
import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"
CLICKUP_API_TOKEN = os.getenv('CLICKUP_API_TOKEN')
INTAKE_LIST_ID = "901709133703"  # 1. Intake stage


def get_headers():
    return {
        "Authorization": CLICKUP_API_TOKEN,
        "Content-Type": "application/json"
    }


def create_lead(name, email=None, phone=None, budget=None, project_description=None,
                company=None, timeline=None, referral_source=None, notes=None, temperature="Warm 🌡️"):
    """Create a comprehensive lead in ClickUp"""

    url = f"{CLICKUP_API_BASE}/list/{INTAKE_LIST_ID}/task"

    # Load custom field IDs
    field_ids_path = os.path.join(os.path.dirname(__file__), 'custom_field_ids.json')
    with open(field_ids_path, 'r') as f:
        field_ids = json.load(f)

    # Build task description with phone and notes (phone field is too strict for custom field)
    description_parts = []
    if phone:
        description_parts.append(f"## Contact\n📱 Phone: {phone}")
    if notes:
        description_parts.append(f"## Notes\n{notes}")
    description = "\n\n".join(description_parts) if description_parts else ""

    # Create task with custom fields
    task_data = {
        "name": f"Client: {name}",
        "description": description,
        "markdown_description": description,
        "custom_fields": []
    }

    # Add custom fields (these will show as columns in ClickUp)
    if email:
        task_data["custom_fields"].append({
            "id": field_ids["Email"],
            "value": email
        })

    # Note: Phone is in description because ClickUp phone field is too strict

    if company:
        task_data["custom_fields"].append({
            "id": field_ids["Company"],
            "value": company
        })

    if budget:
        # Convert budget to cents for currency field
        budget_value = budget
        if isinstance(budget, str):
            try:
                budget_clean = budget.replace('$', '').replace(',', '').replace('k', '000').replace('K', '000')
                if '-' not in budget_clean:
                    budget_value = float(budget_clean)
            except:
                budget_value = None

        if budget_value is not None and isinstance(budget_value, (int, float)):
            task_data["custom_fields"].append({
                "id": field_ids["Budget"],
                "value": int(budget_value * 100)  # ClickUp currency is in cents
            })

    if project_description:
        task_data["custom_fields"].append({
            "id": field_ids["Project Type"],
            "value": project_description
        })

    if timeline:
        task_data["custom_fields"].append({
            "id": field_ids["Timeline"],
            "value": timeline
        })

    # Referral Source - dropdown field (needs index)
    if referral_source:
        # Map to dropdown option indexes
        source_mapping = {
            "website": 0,
            "linkedin": 1,
            "referral": 2,
            "cold outreach": 3,
            "social media": 4,
            "event": 5
        }
        source_value = source_mapping.get(referral_source.lower(), 6)  # Default to "Other"
        task_data["custom_fields"].append({
            "id": field_ids["Referral Source"],
            "value": source_value
        })

    # Lead temperature - dropdown field (needs index)
    temp_mapping = {
        "hot 🔥": 0,
        "hot": 0,
        "warm 🌡️": 1,
        "warm": 1,
        "cold ❄️": 2,
        "cold": 2
    }
    temp_value = temp_mapping.get(temperature.lower(), 1)  # Default to Warm
    task_data["custom_fields"].append({
        "id": field_ids["Lead Temperature"],
        "value": temp_value
    })

    response = requests.post(url, headers=get_headers(), json=task_data)
    response.raise_for_status()

    task = response.json()

    print("\n" + "=" * 70)
    print("✅ Lead Added to Sales Pipeline!")
    print("=" * 70)

    print(f"\n📋 Client: {name}")
    if email:
        print(f"📧 Email: {email}")
    if phone:
        print(f"📱 Phone: {phone}")
    if company:
        print(f"🏢 Company: {company}")
    if budget:
        print(f"💰 Budget: ${budget:,}" if isinstance(budget, (int, float)) else f"💰 Budget: {budget}")
    if project_description:
        print(f"🎯 Project: {project_description}")
    if timeline:
        print(f"📅 Timeline: {timeline}")

    print(f"\n🔗 ClickUp Task: {task['url']}")
    print(f"📍 Stage: 1. Intake")
    print(f"🌡️  Temperature: {temperature}")

    return task


def interactive_mode():
    """Interactive prompt for lead information"""

    print("\n" + "=" * 70)
    print("Add New Lead - Interactive Mode")
    print("=" * 70)
    print("(Press Enter to skip optional fields)\n")

    # Required
    name = input("Client Name (required): ").strip()
    while not name:
        print("❌ Name is required")
        name = input("Client Name (required): ").strip()

    # Contact info
    email = input("Email: ").strip() or None
    phone = input("Phone: ").strip() or None
    company = input("Company: ").strip() or None

    # Project details
    project_description = input("Project Description: ").strip() or None
    budget = input("Budget (e.g., 10000 or 10k-15k): ").strip() or None
    timeline = input("Timeline (e.g., 2 months, Q2 2026): ").strip() or None
    referral_source = input("Referral Source (e.g., LinkedIn, Referral, Website): ").strip() or None
    notes = input("Additional Notes: ").strip() or None

    # Temperature
    print("\nLead Temperature:")
    print("  1. Hot 🔥")
    print("  2. Warm 🌡️ (default)")
    print("  3. Cold ❄️")
    temp_choice = input("Choose (1-3): ").strip()
    temperature = {"1": "Hot 🔥", "2": "Warm 🌡️", "3": "Cold ❄️"}.get(temp_choice, "Warm 🌡️")

    # Confirmation
    print("\n" + "-" * 70)
    print("Review Lead Information:")
    print("-" * 70)
    print(f"Name: {name}")
    if email: print(f"Email: {email}")
    if phone: print(f"Phone: {phone}")
    if company: print(f"Company: {company}")
    if project_description: print(f"Project: {project_description}")
    if budget: print(f"Budget: {budget}")
    if timeline: print(f"Timeline: {timeline}")
    if referral_source: print(f"Source: {referral_source}")
    if notes: print(f"Notes: {notes}")
    print(f"Temperature: {temperature}")
    print("-" * 70)

    confirm = input("\nAdd this lead? (y/n): ").strip().lower()

    if confirm == 'y':
        return create_lead(
            name=name,
            email=email,
            phone=phone,
            company=company,
            budget=budget,
            project_description=project_description,
            timeline=timeline,
            referral_source=referral_source,
            notes=notes,
            temperature=temperature
        )
    else:
        print("❌ Lead not added")
        return None


def main():
    """Main CLI handler"""

    # Check for interactive mode
    if "--interactive" in sys.argv or "-i" in sys.argv:
        interactive_mode()
        return

    # Parse command line arguments
    args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith("--"):
            key = sys.argv[i][2:]
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
                args[key] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        else:
            i += 1

    # Check for required name
    if "name" not in args:
        print("Usage:")
        print("  python add_lead.py --name \"John Smith\" --email \"john@example.com\" --phone \"555-1234\" --budget \"10000\" --project \"Website redesign\"")
        print("\nOr use interactive mode:")
        print("  python add_lead.py --interactive")
        print("\nAvailable fields:")
        print("  --name (required)")
        print("  --email")
        print("  --phone")
        print("  --company")
        print("  --budget")
        print("  --project")
        print("  --timeline")
        print("  --source (referral source)")
        print("  --notes")
        print("  --temp (Hot 🔥 / Warm 🌡️ / Cold ❄️)")
        sys.exit(1)

    try:
        task = create_lead(
            name=args.get('name'),
            email=args.get('email'),
            phone=args.get('phone'),
            company=args.get('company'),
            budget=args.get('budget'),
            project_description=args.get('project'),
            timeline=args.get('timeline'),
            referral_source=args.get('source'),
            notes=args.get('notes'),
            temperature=args.get('temp', 'Warm 🌡️')
        )

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
