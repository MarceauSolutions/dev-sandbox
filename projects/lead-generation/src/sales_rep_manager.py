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
    """Generate interactive leads page HTML for a rep.

    Features:
    - Tap Call → opens dialer + marks lead as contacted via API + disables button
    - Tap Text → opens SMS with pre-filled message + marks as contacted
    - When all leads contacted → auto-requests new batch from API
    - All actions logged to pipeline.db outreach_log via API
    """
    owner = config["owner"]
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    rep_id = rep["id"]

    # Build leads JSON for the JavaScript
    leads_json = json.dumps([{
        "deal_id": lead["deal_id"],
        "company": lead["company"],
        "contact_name": lead["contact_name"] or "",
        "contact_phone": lead["contact_phone"],
        "industry": lead["industry"] or "",
        "stage": lead["stage"],
        "status": lead["status"],
    } for lead in leads])

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
        .lead-card {{ background:#1e1e1e; border:1px solid #333; border-radius:12px; padding:1.25rem; margin-bottom:0.75rem; transition:all 0.3s; }}
        .lead-card.contacted {{ opacity:0.4; border-color:#222; }}
        .lead-card.contacted .call-btn {{ background:rgba(100,100,100,0.15); border-color:#555; color:#555; pointer-events:none; }}
        .lead-card.contacted .text-btn {{ background:rgba(100,100,100,0.15); border-color:#555; color:#555; pointer-events:none; }}
        .lead-card.contacted .contacted-badge {{ display:inline-block; }}
        .lead-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem; }}
        .lead-name {{ color:#fff; font-size:1rem; font-weight:700; }}
        .industry-badge {{ background:rgba(59,130,246,0.15); color:#60a5fa; padding:2px 8px; border-radius:10px; font-size:0.75rem; }}
        .lead-contact {{ color:#aaa; font-size:0.9rem; margin-bottom:0.75rem; }}
        .lead-actions {{ display:flex; gap:0.75rem; flex-wrap:wrap; align-items:center; }}
        .call-btn {{ display:inline-flex; align-items:center; gap:0.4rem; background:rgba(201,150,60,0.15); border:1px solid #C9963C; color:#C9963C; padding:0.5rem 1rem; border-radius:25px; text-decoration:none; font-size:0.85rem; font-weight:600; cursor:pointer; }}
        .text-btn {{ display:inline-flex; align-items:center; gap:0.4rem; background:rgba(59,130,246,0.15); border:1px solid #3b82f6; color:#60a5fa; padding:0.5rem 1rem; border-radius:25px; text-decoration:none; font-size:0.85rem; font-weight:600; cursor:pointer; }}
        .contacted-badge {{ display:none; background:rgba(34,197,94,0.15); color:#22c55e; padding:3px 10px; border-radius:10px; font-size:0.75rem; font-weight:600; }}
        .report {{ background:#1e1e1e; border:1px solid #C9963C; border-radius:12px; padding:1.25rem; margin-top:2rem; text-align:center; }}
        .report p {{ color:#aaa; font-size:0.9rem; margin-bottom:0.75rem; }}
        .report a {{ display:inline-block; background:#C9963C; color:#111; font-weight:700; padding:0.6rem 1.5rem; border-radius:25px; text-decoration:none; font-size:0.9rem; }}
        .loading {{ text-align:center; padding:3rem; }}
        .loading-spinner {{ display:inline-block; width:40px; height:40px; border:3px solid #333; border-top-color:#C9963C; border-radius:50%; animation:spin 0.8s linear infinite; }}
        @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
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
            <div class="stat-number" id="stat-total">0</div>
            <div class="stat-label">Total</div>
        </div>
        <div class="stat">
            <div class="stat-number" id="stat-remaining">0</div>
            <div class="stat-label">To Call</div>
        </div>
        <div class="stat">
            <div class="stat-number" id="stat-contacted">0</div>
            <div class="stat-label">Called</div>
        </div>
    </div>

    <div class="refresh">Last updated: {now}</div>

    <div id="leads-container">
        <div class="section-title">Tap to Call or Text</div>
    </div>

    <div id="loading-new" style="display:none;">
        <div class="loading">
            <div class="loading-spinner"></div>
            <p style="color:#C9963C;margin-top:1rem;font-weight:600;">Loading fresh leads...</p>
            <p style="color:#666;font-size:0.85rem;margin-top:0.5rem;">You crushed that batch! Assigning new ones now.</p>
        </div>
    </div>

    <div class="report">
        <p>After each call, text William the outcome:</p>
        <a href="sms:+12393985676?body=Lead%20update%3A%20">📱 Text William the Result</a>
        <p style="margin-top:0.75rem;font-size:0.8rem;">Example: "Dean at Naples Comfort — interested, wants a demo"</p>
    </div>

    <div class="footer">
        <p>Marceau Solutions — AI Automation for Small Businesses</p>
        <p>Questions? Call William: <a href="tel:+12393985676" style="color:#C9963C;text-decoration:none;">(239) 398-5676</a></p>
    </div>
</div>

<script>
const API = 'https://api.marceausolutions.com';
const REP_ID = '{rep_id}';
let leads = {leads_json};

function init() {{
    // Merge server state with localStorage (localStorage tracks contacted on this device)
    const local = JSON.parse(localStorage.getItem('rep_' + REP_ID) || '{{}}');
    leads.forEach(l => {{
        if (local[l.deal_id] === 'contacted') l.status = 'contacted';
    }});
    render();
}}

function render() {{
    const container = document.getElementById('leads-container');
    const assigned = leads.filter(l => l.status === 'assigned');
    const contacted = leads.filter(l => l.status === 'contacted');

    document.getElementById('stat-total').textContent = leads.length;
    document.getElementById('stat-remaining').textContent = assigned.length;
    document.getElementById('stat-contacted').textContent = contacted.length;

    let html = '';
    if (assigned.length > 0) {{
        html += '<div class="section-title">Tap to Call or Text</div>';
        assigned.forEach((l, i) => html += leadCard(l, i + 1, false));
    }}
    if (contacted.length > 0) {{
        html += '<div class="section-title" style="color:#555;">Already Contacted</div>';
        contacted.forEach((l, i) => html += leadCard(l, i + 1, true));
    }}
    container.innerHTML = html;
}}

function leadCard(lead, num, isContacted) {{
    const phone = lead.contact_phone.replace(/[^0-9+]/g, '');
    const phoneLink = phone.startsWith('+') ? phone : '+1' + phone;
    const firstName = lead.contact_name ? lead.contact_name.split(' ')[0] : 'there';
    const cls = isContacted ? 'lead-card contacted' : 'lead-card';
    const badge = lead.industry ? '<span class="industry-badge">' + lead.industry + '</span>' : '';
    const contactedBadge = isContacted ? '<span class="contacted-badge" style="display:inline-block;">CALLED</span>' : '<span class="contacted-badge">CALLED</span>';

    return '<div class="' + cls + '" id="lead-' + lead.deal_id + '">' +
        '<div class="lead-header">' +
            '<span class="lead-name">' + lead.company + '</span>' +
            badge +
        '</div>' +
        '<div class="lead-contact">' + (lead.contact_name || 'Ask for owner') + '</div>' +
        '<div class="lead-actions">' +
            '<a href="tel:' + phoneLink + '" class="call-btn" onclick="markContacted(\'' + lead.deal_id + '\', \'' + lead.company + '\')">' +
                '📞 ' + lead.contact_phone +
            '</a>' +
            '<a href="sms:' + phoneLink + '?body=Hey%20' + firstName + '%2C%20I%20work%20with%20a%20company%20that%20builds%20AI%20phone%20systems%20for%20businesses.%20Would%20you%20be%20open%20to%20a%20quick%20chat%3F" class="text-btn" onclick="markContacted(\'' + lead.deal_id + '\', \'' + lead.company + '\')">' +
                '💬 Text' +
            '</a>' +
            contactedBadge +
        '</div>' +
    '</div>';
}}

function markContacted(dealId, company) {{
    // Update local state immediately
    const lead = leads.find(l => l.deal_id === dealId);
    if (!lead || lead.status === 'contacted') return;
    lead.status = 'contacted';

    // Save to localStorage (persists across page loads on this device)
    const local = JSON.parse(localStorage.getItem('rep_' + REP_ID) || '{{}}');
    local[dealId] = 'contacted';
    localStorage.setItem('rep_' + REP_ID, JSON.stringify(local));

    // Re-render the page
    render();

    // Notify the API (fire and forget — page already updated)
    fetch(API + '/rep/contacted', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ rep_id: REP_ID, deal_id: dealId }})
    }}).then(r => r.json()).then(data => {{
        if (data.all_contacted) {{
            requestNewLeads();
        }}
    }}).catch(() => {{}});  // Offline? No problem — localStorage has it
}}

function requestNewLeads() {{
    document.getElementById('leads-container').style.display = 'none';
    document.getElementById('loading-new').style.display = 'block';

    // Clear localStorage for this rep (new batch incoming)
    localStorage.removeItem('rep_' + REP_ID);

    fetch(API + '/rep/refresh', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ rep_id: REP_ID, count: 15 }})
    }}).then(r => r.json()).then(data => {{
        if (data.ok) {{
            // Reload the page to get fresh leads
            setTimeout(() => window.location.reload(), 3000);
        }} else {{
            document.getElementById('loading-new').innerHTML =
                '<div class="loading"><p style="color:#C9963C;">New leads are being prepared.</p>' +
                '<p style="color:#666;font-size:0.85rem;margin-top:0.5rem;">Refresh this page in a few minutes.</p></div>';
        }}
    }}).catch(() => {{
        document.getElementById('loading-new').innerHTML =
            '<div class="loading"><p style="color:#C9963C;">New leads are being prepared.</p>' +
            '<p style="color:#666;font-size:0.85rem;margin-top:0.5rem;">Refresh this page in a few minutes.</p></div>';
    }});
}}

init();
</script>
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
