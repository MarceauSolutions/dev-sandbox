"""
Import and process Apollo.io exports with credit-efficient workflow.

Implements the 80-90% credit savings strategy:
1. Export Apollo search results (FREE)
2. Score leads manually based on website visits (FREE)
3. Filter for top 20% (scores 8-10)
4. Reveal contacts in Apollo ONLY for top leads (PAID)
5. Import enriched data into our system
"""

import csv
import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

def import_apollo_export(
    csv_file: str,
    output_file: str = None,
    campaign_name: str = None
) -> List[Dict]:
    """
    Import Apollo CSV export and convert to our Lead format.

    Args:
        csv_file: Path to Apollo CSV export
        output_file: Where to save processed leads (default: output/apollo_leads_TIMESTAMP.json)
        campaign_name: Optional campaign name for tracking

    Returns:
        List of lead dicts ready for manual scoring
    """
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/apollo_leads_{timestamp}.json"

    leads = []

    print(f"📥 Importing Apollo export: {csv_file}")

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lead = {
                # Basic info (from free export)
                "business_name": row.get("Company", row.get("Organization Name", "")),
                "website": row.get("Website", row.get("Website URL", "")),
                "city": row.get("City", ""),
                "state": row.get("State", ""),
                "country": row.get("Country", "US"),
                "industry": row.get("Industry", ""),
                "employees": row.get("# Employees", row.get("Employee Count", "")),
                "revenue": row.get("Revenue", ""),

                # Contact info (empty until enriched in Apollo)
                "phone": row.get("Phone", row.get("Direct Phone", "")),
                "email": row.get("Email", ""),
                "contact_name": row.get("Name", row.get("First Name", "") + " " + row.get("Last Name", "")).strip(),
                "title": row.get("Title", ""),

                # Social profiles
                "linkedin": row.get("LinkedIn URL", ""),
                "facebook": row.get("Facebook", ""),
                "twitter": row.get("Twitter", ""),

                # Metadata
                "source": "apollo",
                "campaign": campaign_name or "default",
                "imported_at": datetime.now().isoformat(),

                # Scoring fields (to be filled manually)
                "score": 0,
                "pain_points": [],
                "budget_indicators": [],
                "notes": "",
                "qualified": False
            }
            leads.append(lead)

    # Save to JSON
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(leads, f, indent=2)

    print(f"✅ Imported {len(leads)} leads from Apollo")
    print(f"   Saved to: {output_file}")
    print(f"\n📋 Next steps:")
    print(f"   1. Visit each website and score 1-10")
    print(f"   2. Add scores + pain points to JSON file")
    print(f"   3. Run: python -m src.apollo_import filter {output_file}")
    print(f"   4. Reveal contacts in Apollo for top leads only")
    print(f"\n💡 Scoring guide:")
    print(f"   10 = No website (critical need)")
    print(f"   9 = Poor reviews mentioning calls (Voice AI opportunity)")
    print(f"   8 = No online booking (automation opportunity)")
    print(f"   7 = No social media (content opportunity)")
    print(f"   6 = Outdated website")
    print(f"   1-5 = Lower priority")

    return leads


def filter_by_score(
    input_file: str,
    output_file: str = None,
    min_score: int = 8
) -> List[Dict]:
    """
    Filter leads by score threshold to get top 20%.

    Args:
        input_file: JSON file with scored leads
        output_file: Where to save filtered leads (default: input_file with _top suffix)
        min_score: Minimum score to include (default: 8)

    Returns:
        Filtered list of high-scoring leads
    """
    if output_file is None:
        input_path = Path(input_file)
        output_file = str(input_path.with_name(f"{input_path.stem}_top{input_path.suffix}"))

    print(f"🔍 Filtering leads from: {input_file}")

    with open(input_file, 'r') as f:
        all_leads = json.load(f)

    # Filter by score
    top_leads = [
        lead for lead in all_leads
        if lead.get("score", 0) >= min_score
    ]

    # Mark as qualified
    for lead in top_leads:
        lead["qualified"] = True

    # Save filtered leads
    with open(output_file, 'w') as f:
        json.dump(top_leads, f, indent=2)

    print(f"✅ Filtered to {len(top_leads)} leads (score >= {min_score})")
    print(f"   Original: {len(all_leads)} leads")
    print(f"   Saved to: {output_file}")
    print(f"\n💰 Credit cost estimate:")
    print(f"   {len(top_leads)} leads × 2 credits = {len(top_leads) * 2} credits")
    print(f"\n📋 Next steps:")
    print(f"   1. Go to Apollo.io search")
    print(f"   2. Find these {len(top_leads)} businesses:")
    for i, lead in enumerate(top_leads[:5], 1):
        print(f"      {i}. {lead['business_name']} ({lead['city']}, {lead['state']})")
    if len(top_leads) > 5:
        print(f"      ... and {len(top_leads) - 5} more")
    print(f"   3. Click 'Reveal' for each contact")
    print(f"   4. Export enriched CSV")
    print(f"   5. Run: python -m src.apollo_import merge ENRICHED.csv {output_file}")

    return top_leads


def merge_enriched_data(
    enriched_csv: str,
    scored_json: str,
    output_file: str = None
) -> List[Dict]:
    """
    Merge enriched contact data from Apollo with scored leads.

    Args:
        enriched_csv: CSV export from Apollo with revealed contacts
        scored_json: JSON file with scored leads (from filter_by_score)
        output_file: Where to save final ready-for-outreach leads

    Returns:
        List of leads ready for SMS campaigns
    """
    if output_file is None:
        output_file = "output/apollo_ready_for_outreach.json"

    print(f"🔗 Merging enriched data...")

    # Load scored leads
    with open(scored_json, 'r') as f:
        scored_leads = {lead['business_name']: lead for lead in json.load(f)}

    # Load enriched CSV
    enriched_contacts = []
    with open(enriched_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            enriched_contacts.append(row)

    # Merge data
    ready_leads = []
    for row in enriched_contacts:
        business_name = row.get("Company", row.get("Organization Name", ""))

        if business_name in scored_leads:
            # Get scored lead data
            lead = scored_leads[business_name].copy()

            # Update with enriched contact info
            lead["phone"] = row.get("Phone", row.get("Direct Phone", lead.get("phone", "")))
            lead["email"] = row.get("Email", lead.get("email", ""))
            lead["contact_name"] = row.get("Name", row.get("First Name", "") + " " + row.get("Last Name", "")).strip()
            lead["title"] = row.get("Title", lead.get("title", ""))
            lead["enriched_at"] = datetime.now().isoformat()

            ready_leads.append(lead)

    # Save ready leads
    with open(output_file, 'w') as f:
        json.dump(ready_leads, f, indent=2)

    print(f"✅ Merged {len(ready_leads)} leads with enriched contact data")
    print(f"   Saved to: {output_file}")
    print(f"\n📞 Ready for outreach:")
    print(f"   Leads with phone: {sum(1 for l in ready_leads if l.get('phone'))}")
    print(f"   Leads with email: {sum(1 for l in ready_leads if l.get('email'))}")
    print(f"\n📋 Next step:")
    print(f"   python -m src.scraper sms --for-real --source apollo --file {output_file}")

    return ready_leads


def show_stats(input_file: str):
    """Show statistics for Apollo leads."""
    with open(input_file, 'r') as f:
        leads = json.load(f)

    total = len(leads)
    scored = sum(1 for l in leads if l.get("score", 0) > 0)
    qualified = sum(1 for l in leads if l.get("qualified", False))
    with_phone = sum(1 for l in leads if l.get("phone"))
    with_email = sum(1 for l in leads if l.get("email"))

    # Score distribution
    scores = [l.get("score", 0) for l in leads]
    score_dist = {
        "10": sum(1 for s in scores if s == 10),
        "9": sum(1 for s in scores if s == 9),
        "8": sum(1 for s in scores if s == 8),
        "7": sum(1 for s in scores if s == 7),
        "6": sum(1 for s in scores if s == 6),
        "1-5": sum(1 for s in scores if 1 <= s <= 5),
        "0 (unscored)": sum(1 for s in scores if s == 0)
    }

    print(f"\n📊 Apollo Lead Statistics: {input_file}")
    print(f"\n   Total leads: {total}")
    print(f"   Scored: {scored} ({scored/total*100:.1f}%)")
    print(f"   Qualified (8-10): {qualified} ({qualified/total*100:.1f}%)")
    print(f"   With phone: {with_phone} ({with_phone/total*100:.1f}%)")
    print(f"   With email: {with_email} ({with_email/total*100:.1f}%)")
    print(f"\n   Score distribution:")
    for score, count in score_dist.items():
        if count > 0:
            print(f"      {score}: {count} leads")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Apollo.io Import Tool")
        print("\nUsage:")
        print("  python -m src.apollo_import import <csv_file> [campaign_name]")
        print("  python -m src.apollo_import filter <scored_json_file> [min_score]")
        print("  python -m src.apollo_import merge <enriched_csv> <scored_json>")
        print("  python -m src.apollo_import stats <json_file>")
        print("\nExample workflow:")
        print("  1. Export from Apollo (free) → naples_gyms.csv")
        print("  2. python -m src.apollo_import import naples_gyms.csv 'Naples Gyms'")
        print("  3. Manually score leads in JSON file")
        print("  4. python -m src.apollo_import filter output/apollo_leads_*.json")
        print("  5. Reveal contacts in Apollo for top leads")
        print("  6. Export enriched CSV → naples_gyms_enriched.csv")
        print("  7. python -m src.apollo_import merge naples_gyms_enriched.csv output/apollo_leads_*_top.json")
        print("  8. python -m src.scraper sms --source apollo")
        sys.exit(0)

    command = sys.argv[1]

    if command == "import":
        csv_file = sys.argv[2]
        campaign_name = sys.argv[3] if len(sys.argv) > 3 else None
        import_apollo_export(csv_file, campaign_name=campaign_name)

    elif command == "filter":
        input_file = sys.argv[2]
        min_score = int(sys.argv[3]) if len(sys.argv) > 3 else 8
        filter_by_score(input_file, min_score=min_score)

    elif command == "merge":
        if len(sys.argv) < 4:
            print("❌ Error: merge requires 2 arguments")
            print("Usage: python -m src.apollo_import merge <enriched_csv> <scored_json>")
            sys.exit(1)
        enriched_csv = sys.argv[2]
        scored_json = sys.argv[3]
        merge_enriched_data(enriched_csv, scored_json)

    elif command == "stats":
        input_file = sys.argv[2]
        show_stats(input_file)

    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: import, filter, merge, stats")
        sys.exit(1)
