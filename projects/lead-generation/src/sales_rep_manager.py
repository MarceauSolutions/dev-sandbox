#!/usr/bin/env python3
"""
Sales Rep Manager — Assign leads to sales reps and generate their lead pages.

This system lets you:
  1. Add/remove sales reps (edit config/sales_reps.json)
  2. Assign leads from pipeline.db to reps
  3. Generate a live leads page for each rep at marceausolutions.com/partner/{slug}/leads/
  4. Reps see their leads on their phone, you record outcomes via Telegram

To swap a rep: set active=false in sales_reps.json, add a new rep,
run `reassign` to move their leads to the new person.

Usage:
    python3 -m projects.lead_generation.src.sales_rep_manager assign --rep will-george --count 15
    python3 -m projects.lead_generation.src.sales_rep_manager generate
    python3 -m projects.lead_generation.src.sales_rep_manager list
    python3 -m projects.lead_generation.src.sales_rep_manager reassign --from will-george --to new-rep
    python3 -m projects.lead_generation.src.sales_rep_manager remove --rep will-george
"""

import argparse
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

# Path resolution
if os.environ.get("REPO_ROOT"):
    _REPO_ROOT = Path(os.environ["REPO_ROOT"])
else:
    _REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_CONFIG_PATH = _REPO_ROOT / "projects" / "lead-generation" / "config" / "sales_reps.json"
_ASSIGNMENTS_PATH = _REPO_ROOT / "projects" / "lead-generation" / "data" / "rep_assignments.json"
_DB_PATH = _REPO_ROOT / "projects" / "lead-generation" / "sales-pipeline" / "data" / "pipeline.db"
_OUTPUT_DIR = _REPO_ROOT / "client-sites" / "sales-toolkit" / "partner-pages"

# Industries with best conversion rates (from learned_preferences)
PRIORITY_INDUSTRIES = ["HVAC", "Plumbing", "Med Spa", "Dental", "Auto", "Gym", "Restaurant"]


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return json.load(f)


def _load_assignments() -> dict:
    if _ASSIGNMENTS_PATH.exists():
        with open(_ASSIGNMENTS_PATH) as f:
            return json.load(f)
    return {"assignments": {}}


def _save_assignments(data: dict):
    _ASSIGNMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_ASSIGNMENTS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _get_db():
    return sqlite3.connect(str(_DB_PATH))


def _get_rep(config: dict, rep_id: str) -> dict:
    for rep in config["active_reps"]:
        if rep["id"] == rep_id:
            return rep
    return None


def list_reps():
    """List all sales reps and their assigned lead counts."""
    config = _load_config()
    assignments = _load_assignments()

    print("\nSALES REPS:")
    print("-" * 60)

    # Owner
    owner = config["owner"]
    owner_count = sum(1 for a in assignments.get("assignments", {}).values() if a["rep_id"] == owner["id"])
    print(f"  [OWNER] {owner['name']} ({owner['email']})")
    print(f"          {owner_count} leads assigned")

    # Reps
    for rep in config["active_reps"]:
        status = "ACTIVE" if rep["active"] else "INACTIVE"
        rep_count = sum(1 for a in assignments.get("assignments", {}).values() if a["rep_id"] == rep["id"])
        print(f"\n  [{status}] {rep['name']} ({rep['email']})")
        print(f"          ID: {rep['id']} | Page: /partner/{rep['page_slug']}/")
        print(f"          {rep_count} leads assigned")

    print()


def assign_leads(rep_id: str, count: int = 15, industries: list = None):
    """Assign unassigned leads from pipeline.db to a sales rep."""
    config = _load_config()
    rep = _get_rep(config, rep_id)
    if not rep:
        print(f"ERROR: Rep '{rep_id}' not found in config")
        return

    if not rep["active"]:
        print(f"ERROR: Rep '{rep_id}' is inactive. Set active=true in config first.")
        return

    assignments = _load_assignments()
    assigned_deal_ids = set(assignments.get("assignments", {}).keys())

    # Current rep's count
    max_leads = config["assignment_rules"]["max_leads_per_rep"]
    current_count = sum(1 for a in assignments.get("assignments", {}).values() if a["rep_id"] == rep_id)
    available_slots = max_leads - current_count
    count = min(count, available_slots)

    if count <= 0:
        print(f"Rep '{rep_id}' already at max ({max_leads} leads)")
        return

    # Query pipeline for unassigned, contactable leads
    conn = _get_db()
    cursor = conn.cursor()

    # Get leads that are Contacted or Qualified, have a phone number, and aren't already assigned
    query = """
        SELECT id, company, contact_name, contact_phone, contact_email, industry, stage
        FROM deals
        WHERE stage IN ('Contacted', 'Qualified', 'Intake')
        AND contact_phone IS NOT NULL
        AND contact_phone != ''
        AND id NOT IN ({})
        ORDER BY
            CASE
                WHEN industry IN ('HVAC', 'Plumbing') THEN 1
                WHEN industry IN ('Med Spa', 'Dental') THEN 2
                WHEN industry IN ('Auto', 'Gym', 'Restaurant') THEN 3
                ELSE 4
            END,
            id DESC
        LIMIT ?
    """.format(",".join(str(i) for i in assigned_deal_ids) if assigned_deal_ids else "0")

    cursor.execute(query, (count,))
    leads = cursor.fetchall()
    conn.close()

    if not leads:
        print("No unassigned leads with phone numbers available")
        return

    # Assign
    if "assignments" not in assignments:
        assignments["assignments"] = {}

    new_count = 0
    for lead in leads:
        deal_id, company, contact, phone, email, industry, stage = lead
        assignments["assignments"][str(deal_id)] = {
            "rep_id": rep_id,
            "company": company,
            "contact_name": contact or "",
            "contact_phone": phone,
            "contact_email": email or "",
            "industry": industry or "",
            "stage": stage,
            "assigned_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "assigned",
            "notes": ""
        }
        new_count += 1

    _save_assignments(assignments)
    print(f"\nAssigned {new_count} leads to {rep['name']}:")
    for lead in leads:
        print(f"  #{lead[0]} {lead[1]} — {lead[2] or 'No name'} ({lead[3]})")
    print(f"\nTotal for {rep['name']}: {current_count + new_count}/{max_leads}")


def reassign_leads(from_rep: str, to_rep: str):
    """Move all leads from one rep to another."""
    config = _load_config()
    to_rep_obj = _get_rep(config, to_rep)
    if not to_rep_obj:
        print(f"ERROR: Target rep '{to_rep}' not found")
        return

    assignments = _load_assignments()
    moved = 0
    for deal_id, assignment in assignments.get("assignments", {}).items():
        if assignment["rep_id"] == from_rep:
            assignment["rep_id"] = to_rep
            assignment["reassigned_date"] = datetime.now().strftime("%Y-%m-%d")
            moved += 1

    _save_assignments(assignments)
    print(f"Reassigned {moved} leads from '{from_rep}' to '{to_rep}'")


def remove_rep(rep_id: str, reassign_to: str = None):
    """Deactivate a rep and optionally reassign their leads."""
    config = _load_config()
    for rep in config["active_reps"]:
        if rep["id"] == rep_id:
            rep["active"] = False
            break

    with open(_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    if reassign_to:
        reassign_leads(rep_id, reassign_to)
        print(f"Deactivated '{rep_id}' and reassigned leads to '{reassign_to}'")
    else:
        print(f"Deactivated '{rep_id}'. Leads still assigned — use --reassign-to to move them.")


def generate_pages():
    """Generate a live leads page for each active rep."""
    config = _load_config()
    assignments = _load_assignments()

    for rep in config["active_reps"]:
        if not rep["active"]:
            continue

        # Get this rep's leads
        rep_leads = []
        for deal_id, assignment in assignments.get("assignments", {}).items():
            if assignment["rep_id"] == rep["id"]:
                rep_leads.append({**assignment, "deal_id": deal_id})

        # Sort: assigned first, then by industry priority
        rep_leads.sort(key=lambda x: (
            0 if x["status"] == "assigned" else 1,
            PRIORITY_INDUSTRIES.index(x["industry"]) if x["industry"] in PRIORITY_INDUSTRIES else 99
        ))

        # Generate HTML
        html = _generate_leads_html(rep, rep_leads, config)

        # Write to partner pages directory
        output_dir = _OUTPUT_DIR / rep["page_slug"]
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "leads.html"
        with open(output_path, "w") as f:
            f.write(html)

        print(f"Generated leads page for {rep['name']}: {output_path}")
        print(f"  {len(rep_leads)} leads ({sum(1 for l in rep_leads if l['status'] == 'assigned')} active)")

    # Also deploy to marceausolutions.com repo if it exists
    website_repo = Path("/tmp/marceausolutions-check")
    if website_repo.exists():
        for rep in config["active_reps"]:
            if not rep["active"]:
                continue
            src = _OUTPUT_DIR / rep["page_slug"] / "leads.html"
            dest_dir = website_repo / "partner" / rep["page_slug"]
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / "leads.html"
            if src.exists():
                import shutil
                shutil.copy2(str(src), str(dest))
                print(f"  Deployed to website repo: partner/{rep['page_slug']}/leads.html")


def _generate_leads_html(rep: dict, leads: list, config: dict) -> str:
    """Generate the leads page HTML for a rep."""
    owner = config["owner"]
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    leads_html = ""
    for i, lead in enumerate(leads, 1):
        status_color = "#C9963C" if lead["status"] == "assigned" else "#666"
        status_label = lead["status"].upper()
        industry_badge = f'<span style="background:rgba(59,130,246,0.15);color:#60a5fa;padding:2px 8px;border-radius:10px;font-size:0.75rem;">{lead["industry"]}</span>' if lead["industry"] else ""

        phone_link = lead["contact_phone"].replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
        if not phone_link.startswith("+"):
            phone_link = "+1" + phone_link

        leads_html += f"""
        <div style="background:#1e1e1e;border:1px solid #333;border-radius:12px;padding:1.25rem;margin-bottom:0.75rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
                <strong style="color:#fff;font-size:1rem;">{i}. {lead['company']}</strong>
                {industry_badge}
            </div>
            <div style="color:#aaa;font-size:0.9rem;margin-bottom:0.75rem;">
                {lead['contact_name'] or 'Ask for owner'} | {lead['stage']}
            </div>
            <div style="display:flex;gap:0.75rem;flex-wrap:wrap;">
                <a href="tel:{phone_link}" style="display:inline-flex;align-items:center;gap:0.4rem;background:rgba(201,150,60,0.15);border:1px solid #C9963C;color:#C9963C;padding:0.5rem 1rem;border-radius:25px;text-decoration:none;font-size:0.85rem;font-weight:600;">
                    📞 {lead['contact_phone']}
                </a>
                <a href="sms:{phone_link}?body=Hey%20{lead['contact_name'].split()[0] if lead['contact_name'] else 'there'}%2C%20I%20work%20with%20a%20company%20that%20builds%20AI%20phone%20systems%20for%20businesses.%20Would%20you%20be%20open%20to%20a%20quick%20chat%3F" style="display:inline-flex;align-items:center;gap:0.4rem;background:rgba(59,130,246,0.15);border:1px solid #3b82f6;color:#60a5fa;padding:0.5rem 1rem;border-radius:25px;text-decoration:none;font-size:0.85rem;font-weight:600;">
                    💬 Text
                </a>
            </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Leads — Marceau Solutions</title>
    <meta name="robots" content="noindex, nofollow">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Inter',sans-serif; background:#111; color:#fff; min-height:100vh; padding:1rem; }}
        .container {{ max-width:600px; margin:0 auto; }}
        h1 {{ font-size:1.3rem; font-weight:800; color:#C9963C; margin-bottom:0.25rem; }}
        .subtitle {{ color:#999; font-size:0.85rem; margin-bottom:1.5rem; }}
        .stats {{ display:flex; gap:1rem; margin-bottom:1.5rem; }}
        .stat {{ background:#1e1e1e; border:1px solid #333; border-radius:10px; padding:0.75rem 1rem; flex:1; text-align:center; }}
        .stat-number {{ font-size:1.5rem; font-weight:800; color:#C9963C; }}
        .stat-label {{ font-size:0.7rem; color:#999; text-transform:uppercase; letter-spacing:0.05em; }}
        .section-title {{ font-size:0.85rem; font-weight:700; color:#C9963C; text-transform:uppercase; letter-spacing:0.1em; margin:1.5rem 0 0.75rem; }}
        .report {{ background:#1e1e1e; border:1px solid #C9963C; border-radius:12px; padding:1.25rem; margin-top:2rem; text-align:center; }}
        .report p {{ color:#aaa; font-size:0.9rem; margin-bottom:0.75rem; }}
        .report a {{ display:inline-block; background:#C9963C; color:#111; font-weight:700; padding:0.6rem 1.5rem; border-radius:25px; text-decoration:none; font-size:0.9rem; }}
        .footer {{ text-align:center; margin-top:2rem; padding:1rem; color:#666; font-size:0.75rem; }}
        .refresh {{ color:#666; font-size:0.75rem; text-align:center; margin-bottom:1rem; }}
    </style>
</head>
<body>
<div class="container">
    <h1>Your Leads</h1>
    <div class="subtitle">{rep['name']} — Marceau Solutions Partner</div>

    <div class="stats">
        <div class="stat">
            <div class="stat-number">{len(leads)}</div>
            <div class="stat-label">Total Leads</div>
        </div>
        <div class="stat">
            <div class="stat-number">{sum(1 for l in leads if l['status'] == 'assigned')}</div>
            <div class="stat-label">To Call</div>
        </div>
        <div class="stat">
            <div class="stat-number">{sum(1 for l in leads if l['status'] == 'contacted')}</div>
            <div class="stat-label">Contacted</div>
        </div>
    </div>

    <div class="refresh">Last updated: {now}</div>

    <div class="section-title">Tap to Call or Text</div>
    {leads_html}

    <div class="report">
        <p>After you talk to someone, text William the result:</p>
        <a href="sms:+12393985676?body=Lead%20update%3A%20">📱 Text William</a>
        <p style="margin-top:0.75rem;font-size:0.8rem;">Example: "Spoke to John at ABC HVAC — interested, wants a demo"</p>
    </div>

    <div class="footer">
        <p>Marceau Solutions — AI Automation for Small Businesses</p>
        <p>Questions? Call William: <a href="tel:+12393985676" style="color:#C9963C;text-decoration:none;">(239) 398-5676</a></p>
    </div>
</div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Sales Rep Manager")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all reps and lead counts")

    assign_p = sub.add_parser("assign", help="Assign leads to a rep")
    assign_p.add_argument("--rep", required=True, help="Rep ID")
    assign_p.add_argument("--count", type=int, default=15, help="Number of leads")

    sub.add_parser("generate", help="Generate leads pages for all active reps")

    reassign_p = sub.add_parser("reassign", help="Move leads between reps")
    reassign_p.add_argument("--from", dest="from_rep", required=True)
    reassign_p.add_argument("--to", dest="to_rep", required=True)

    remove_p = sub.add_parser("remove", help="Deactivate a rep")
    remove_p.add_argument("--rep", required=True)
    remove_p.add_argument("--reassign-to", default=None)

    args = parser.parse_args()

    if args.command == "list":
        list_reps()
    elif args.command == "assign":
        assign_leads(args.rep, args.count)
    elif args.command == "generate":
        generate_pages()
    elif args.command == "reassign":
        reassign_leads(args.from_rep, args.to_rep)
    elif args.command == "remove":
        remove_rep(args.rep, args.reassign_to)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
