"""Batch AI consulting outreach calls with parallel execution."""

import os
import sys
import json
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twilio.rest import Client
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
AI_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
BASE_URL = "https://cuddly-bryn-fiduciarily.ngrok-free.dev"


def make_single_call(lead: dict) -> dict:
    """
    Make a single outreach call to a lead.

    Args:
        lead: Dictionary with phone, business_name, business_type, person_name, custom_context

    Returns:
        Result dictionary with status and call details
    """
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    to_number = lead.get("phone", "")
    if not to_number.startswith("+"):
        to_number = "+1" + to_number.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")

    # Build webhook URL with query parameters
    webhook_url = f"{BASE_URL}/twilio/outreach"
    params = {}
    if lead.get("business_name"):
        params["business_name"] = lead["business_name"]
    if lead.get("business_type"):
        params["business_type"] = lead["business_type"]
    if lead.get("person_name"):
        params["person_name"] = lead["person_name"]
    if lead.get("custom_context"):
        params["custom_context"] = lead["custom_context"]

    if params:
        webhook_url = f"{webhook_url}?{urllib.parse.urlencode(params)}"

    try:
        call = client.calls.create(
            url=webhook_url,
            to=to_number,
            from_=AI_PHONE_NUMBER,
            status_callback=f"{BASE_URL}/twilio/status",
            status_callback_event=["initiated", "ringing", "answered", "completed"]
        )

        return {
            "status": "success",
            "phone": to_number,
            "person_name": lead.get("person_name", "Unknown"),
            "business_name": lead.get("business_name", "Unknown"),
            "call_sid": call.sid
        }
    except Exception as e:
        return {
            "status": "error",
            "phone": to_number,
            "person_name": lead.get("person_name", "Unknown"),
            "business_name": lead.get("business_name", "Unknown"),
            "error": str(e)
        }


def batch_outreach(
    leads: list[dict],
    max_parallel: int = 5,
    delay_between_batches: float = 2.0,
    dry_run: bool = False
) -> list[dict]:
    """
    Execute batch outreach calls with parallel execution.

    Args:
        leads: List of lead dictionaries
        max_parallel: Maximum concurrent calls (default 5 to avoid rate limits)
        delay_between_batches: Seconds between batch waves
        dry_run: If True, just print what would be called

    Returns:
        List of result dictionaries
    """
    results = []

    if dry_run:
        print("\n🔍 DRY RUN - No calls will be made\n")
        for i, lead in enumerate(leads, 1):
            print(f"{i}. {lead.get('person_name', 'Unknown')} at {lead.get('business_name', 'Unknown')}")
            print(f"   Phone: {lead.get('phone')}")
            print(f"   Type: {lead.get('business_type', 'N/A')}")
            print(f"   Context: {lead.get('custom_context', 'N/A')[:50]}..." if lead.get('custom_context') else "")
            print()
        return []

    print(f"\n📞 Initiating batch outreach to {len(leads)} leads...")
    print(f"   Max parallel calls: {max_parallel}")
    print(f"   Delay between batches: {delay_between_batches}s\n")

    # Process in batches
    for batch_start in range(0, len(leads), max_parallel):
        batch = leads[batch_start:batch_start + max_parallel]
        batch_num = (batch_start // max_parallel) + 1
        total_batches = (len(leads) + max_parallel - 1) // max_parallel

        print(f"--- Batch {batch_num}/{total_batches} ({len(batch)} calls) ---")

        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            futures = {executor.submit(make_single_call, lead): lead for lead in batch}

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                if result["status"] == "success":
                    print(f"   ✅ {result['person_name']} ({result['business_name']}): {result['call_sid']}")
                else:
                    print(f"   ❌ {result['person_name']} ({result['business_name']}): {result['error']}")

        # Delay between batches (except for last batch)
        if batch_start + max_parallel < len(leads):
            print(f"   Waiting {delay_between_batches}s before next batch...")
            time.sleep(delay_between_batches)

    # Summary
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")

    print(f"\n📊 Batch Complete")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   Total: {len(results)}")

    return results


def load_leads_from_json(filepath: str) -> list[dict]:
    """Load leads from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def load_leads_from_csv(filepath: str) -> list[dict]:
    """Load leads from a CSV file."""
    import csv
    leads = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append({
                "phone": row.get("phone", row.get("Phone", "")),
                "person_name": row.get("person_name", row.get("Name", row.get("name", ""))),
                "business_name": row.get("business_name", row.get("Company", row.get("company", ""))),
                "business_type": row.get("business_type", row.get("Type", row.get("type", ""))),
                "custom_context": row.get("custom_context", row.get("Context", row.get("context", "")))
            })
    return leads


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch AI consulting outreach calls")
    parser.add_argument("--file", "-f", help="JSON or CSV file with leads")
    parser.add_argument("--leads", "-l", type=str, help="JSON string of leads array")
    parser.add_argument("--parallel", "-p", type=int, default=5, help="Max parallel calls (default: 5)")
    parser.add_argument("--delay", "-d", type=float, default=2.0, help="Delay between batches in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Preview calls without making them")

    args = parser.parse_args()

    leads = []

    if args.file:
        if args.file.endswith('.json'):
            leads = load_leads_from_json(args.file)
        elif args.file.endswith('.csv'):
            leads = load_leads_from_csv(args.file)
        else:
            print("Error: File must be .json or .csv")
            sys.exit(1)
    elif args.leads:
        leads = json.loads(args.leads)
    else:
        # Example usage with inline leads
        print("Usage:")
        print("  python batch_outreach.py --file leads.json")
        print("  python batch_outreach.py --file leads.csv")
        print("  python batch_outreach.py --leads '[{\"phone\": \"1234567890\", \"person_name\": \"John\", ...}]'")
        print("\nExample JSON format:")
        example = [
            {
                "phone": "2393984852",
                "person_name": "Angela",
                "business_name": "Insulet Corporation",
                "business_type": "medical device",
                "custom_context": "diabetes care and clinical data insights"
            }
        ]
        print(json.dumps(example, indent=2))
        sys.exit(0)

    if not leads:
        print("No leads provided")
        sys.exit(1)

    results = batch_outreach(
        leads=leads,
        max_parallel=args.parallel,
        delay_between_batches=args.delay,
        dry_run=args.dry_run
    )

    # Save results if not dry run
    if not args.dry_run and results:
        output_file = f"output/batch_results_{int(time.time())}.json"
        os.makedirs("output", exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Results saved to {output_file}")
