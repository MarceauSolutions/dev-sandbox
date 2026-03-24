"""
Sales Pipeline — Production UI

Kanban pipeline board, deal management, proposal builder,
pre-call intelligence briefs, outreach tracking.
"""

import html as html_mod
import urllib.parse
from datetime import datetime

GOLD = "#C9963C"
BG = "#0d1117"
CARD = "#161b22"
SURFACE = "#21262d"
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
RED = "#f85149"
GREEN = "#3fb950"
YELLOW = "#d29922"
BLUE = "#58a6ff"
PURPLE = "#bc8cff"
CHARCOAL = "#333333"

STAGE_COLORS = {
    "Intake": MUTED, "Qualified": BLUE, "Meeting Booked": YELLOW,
    "Proposal Sent": PURPLE, "Negotiation": GOLD, "Closed Won": GREEN, "Closed Lost": RED
}

STAGES = ["Intake", "Qualified", "Meeting Booked", "Proposal Sent", "Negotiation", "Closed Won", "Closed Lost"]
STAGE_DOTS_ORDER = ["Intake", "Qualified", "Meeting Booked", "Proposal Sent", "Closed Won"]

def _esc(s):
    return html_mod.escape(str(s)) if s else ""


def _stage_dots(current_stage):
    """5-dot stage progress indicator showing pipeline position."""
    pipeline_stages = ["Intake", "Qualified", "Meeting Booked", "Proposal Sent", "Closed Won"]
    try:
        current_idx = pipeline_stages.index(current_stage)
    except ValueError:
        # Closed Lost or Negotiation — map appropriately
        current_idx = -1 if current_stage == "Closed Lost" else 3  # Negotiation ≈ Proposal Sent level

    dots = ""
    for i, stage in enumerate(pipeline_stages):
        color = STAGE_COLORS.get(stage, MUTED)
        if current_stage == "Closed Lost":
            # All dots red for lost
            filled = f'<span title="{stage}" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{RED};margin:0 2px"></span>'
            dots += filled
        elif i <= current_idx:
            filled = f'<span title="{stage}" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{color};margin:0 2px"></span>'
            dots += filled
        else:
            empty = f'<span title="{stage}" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{SURFACE};border:1px solid {BORDER};margin:0 2px"></span>'
            dots += empty
    return f'<div style="display:flex;align-items:center;margin-top:4px">{dots}</div>'

def _money(v):
    try:
        return f"${float(v):,.0f}"
    except (ValueError, TypeError):
        return "$0"


def _tier_badge(tier):
    """Render a tier badge or empty string."""
    if tier == 1:
        return f'<span style="background:#C9963C22;color:#C9963C;border:1px solid #C9963C44;border-radius:4px;font-size:10px;font-weight:700;padding:2px 6px;margin-left:5px">T1</span>'
    elif tier == 2:
        return f'<span style="background:#58a6ff22;color:#58a6ff;border:1px solid #58a6ff44;border-radius:4px;font-size:10px;font-weight:700;padding:2px 6px;margin-left:5px">T2</span>'
    return ""


def _sprint_header(stats, tier1_queue):
    """Sprint war-room header — first thing William sees every morning."""
    from datetime import date as _date
    sprint_end = _date(2026, 4, 6)
    days_left = max(0, (sprint_end - _date.today()).days)

    outreach_week = stats.get("outreach_week", 0)
    target = 700  # 100/day x 7 days
    pct = min(1.0, outreach_week / target)
    arc_deg = pct * 360

    # SVG arc progress ring (100px)
    r = 38
    circ = 2 * 3.14159 * r
    offset = circ * (1 - pct)
    ring_svg = f'''<svg width="90" height="90" viewBox="0 0 90 90" style="transform:rotate(-90deg)">
        <circle cx="45" cy="45" r="{r}" fill="none" stroke="#30363d" stroke-width="8"/>
        <circle cx="45" cy="45" r="{r}" fill="none" stroke="{GOLD}" stroke-width="8"
                stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"
                stroke-linecap="round"/>
    </svg>
    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;line-height:1.1">
        <div style="font-size:18px;font-weight:800;color:{GOLD}">{outreach_week}</div>
        <div style="font-size:9px;color:{MUTED};text-transform:uppercase">/{target}</div>
    </div>'''

    # Today's call queue (top 5 T1 deals)
    queue_rows = ""
    for d in tier1_queue[:5]:
        next_a = _esc(d.get("next_action") or "")
        queue_rows += f'''<a href="/deals/{d["id"]}" style="display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:8px;background:#0d111722;border:1px solid #30363d44;text-decoration:none;color:inherit;transition:border-color .15s" onmouseover="this.style.borderColor='#C9963C44'" onmouseout="this.style.borderColor='#30363d44'">
            <span style="font-weight:700;font-size:13px;color:{TEXT}">{_esc(d["company"])}</span>
            <span style="background:#C9963C22;color:#C9963C;border:1px solid #C9963C44;border-radius:4px;font-size:9px;font-weight:700;padding:1px 5px;flex-shrink:0">T1</span>
            <span style="font-size:11px;color:{MUTED};flex-shrink:0">{_esc(d.get("stage",""))}</span>
            {f'<span style="font-size:11px;color:{MUTED};margin-left:auto">{_esc(next_a)}</span>' if next_a else ""}
        </a>'''

    if not queue_rows:
        queue_rows = f'<div style="font-size:12px;color:{MUTED};padding:8px 0">No Tier 1 deals yet — sync outreach or add manually.</div>'

    in_pipeline = len(tier1_queue)

    return f'''<div style="background:{CARD};border:1px solid {GOLD}44;border-radius:14px;padding:20px 24px;margin-bottom:18px;position:relative;overflow:hidden">
        <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,{GOLD},{GOLD}66,transparent)"></div>
        <div style="display:flex;align-items:flex-start;gap:20px;flex-wrap:wrap">

            <!-- Left: Sprint label + days left -->
            <div style="flex:1;min-width:160px">
                <div style="font-size:11px;color:{GOLD};font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">SPRINT</div>
                <div style="font-size:20px;font-weight:800;color:{TEXT};line-height:1.2">Sign 1 AI Client<br>by April 6</div>
                <div style="margin-top:12px;display:flex;align-items:baseline;gap:6px">
                    <span style="font-size:36px;font-weight:800;color:{GOLD}">{days_left}</span>
                    <span style="font-size:13px;color:{MUTED}">days left</span>
                </div>
            </div>

            <!-- Center: Outreach ring -->
            <div style="display:flex;flex-direction:column;align-items:center;gap:4px;min-width:100px">
                <div style="position:relative;width:90px;height:90px">{ring_svg}</div>
                <div style="font-size:10px;color:{MUTED};text-transform:uppercase;letter-spacing:.5px;text-align:center">Outreach<br>This Week</div>
            </div>

            <!-- Right: Pipeline count -->
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:80px">
                <div style="font-size:38px;font-weight:800;color:{BLUE}">{in_pipeline}</div>
                <div style="font-size:10px;color:{MUTED};text-transform:uppercase;letter-spacing:.5px;text-align:center">T1 Deals<br>in Pipeline</div>
            </div>

        </div>

        <!-- Call queue -->
        <div style="margin-top:18px;border-top:1px solid #30363d55;padding-top:14px">
            <div style="font-size:11px;font-weight:700;color:{GOLD};text-transform:uppercase;letter-spacing:.8px;margin-bottom:10px">
                TODAY'S CALL QUEUE — Tier 1 First
            </div>
            <div style="display:flex;flex-direction:column;gap:6px">{queue_rows}</div>
        </div>
    </div>'''

CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:{BG};color:{TEXT};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,sans-serif;font-size:14px;line-height:1.5}}
a{{color:{GOLD};text-decoration:none}}a:hover{{text-decoration:underline}}
.container{{max-width:1400px;margin:0 auto;padding:16px 20px}}
.topnav{{background:{CARD};border-bottom:1px solid {BORDER};padding:0 20px;position:sticky;top:0;z-index:100}}
.topnav-inner{{max-width:1400px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:52px}}
.logo{{font-size:18px;font-weight:700;color:{GOLD}}}
.logo span{{color:{TEXT};font-weight:400}}
.nav-links{{display:flex;gap:4px}}
.nav-links a{{padding:6px 14px;border-radius:8px;font-size:13px;color:{MUTED};font-weight:500}}
.nav-links a:hover,.nav-links a.active{{background:{SURFACE};color:{TEXT};text-decoration:none}}
.nav-links a.active{{color:{GOLD}}}

.card{{background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:18px;margin-bottom:14px}}
.card h2{{font-size:14px;font-weight:600;color:{MUTED};text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px}}
.stat-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:16px}}
.stat{{background:{SURFACE};border:1px solid {BORDER};border-radius:10px;padding:14px;text-align:center}}
.stat .val{{font-size:26px;font-weight:800;color:{GOLD}}}
.stat .lbl{{font-size:10px;color:{MUTED};text-transform:uppercase;letter-spacing:.3px;margin-top:2px}}

/* Kanban */
.kanban{{display:flex;gap:12px;overflow-x:auto;padding-bottom:12px;min-height:400px}}
.kanban-col{{min-width:220px;flex:1;background:{SURFACE};border-radius:10px;padding:10px;border:1px solid {BORDER}}}
.kanban-col h3{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:6px 8px;border-radius:6px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center}}
.kanban-card{{background:{CARD};border:1px solid {BORDER};border-radius:8px;padding:10px;margin-bottom:8px;cursor:pointer;transition:border-color .15s,transform .1s}}
.kanban-card:hover{{border-color:{GOLD}44;transform:translateY(-1px)}}
.kanban-card .company{{font-weight:700;font-size:13px}}
.kanban-card .contact{{font-size:11px;color:{MUTED}}}
.kanban-card .amount{{font-size:12px;color:{GOLD};font-weight:600;margin-top:4px}}
.kanban-card .tag{{display:inline-block;background:{BG};padding:1px 6px;border-radius:4px;font-size:10px;color:{MUTED};margin-top:4px}}

.badge{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:8px 10px;color:{MUTED};font-size:10px;text-transform:uppercase;border-bottom:1px solid {BORDER}}}
td{{padding:8px 10px;border-bottom:1px solid {BORDER}22;font-size:13px}}
input,select,textarea{{background:{SURFACE};color:{TEXT};border:1px solid {BORDER};border-radius:8px;padding:10px 14px;font-size:14px;width:100%;font-family:inherit}}
input:focus,select:focus,textarea:focus{{outline:none;border-color:{GOLD};box-shadow:0 0 0 3px rgba(201,150,60,0.1)}}
label{{font-size:12px;color:{MUTED};margin-bottom:4px;display:block;font-weight:500}}
.form-group{{margin-bottom:12px}}
.form-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.btn{{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:8px;font-weight:600;font-size:13px;cursor:pointer;border:none;font-family:inherit;text-decoration:none;transition:opacity .15s}}
.btn:hover{{opacity:.9;text-decoration:none}}
.btn-primary{{background:{GOLD};color:{CHARCOAL}}}
.btn-secondary{{background:{SURFACE};color:{TEXT};border:1px solid {BORDER}}}
.btn-danger{{background:rgba(248,81,73,.15);color:{RED};border:1px solid rgba(248,81,73,.3)}}
.btn-sm{{padding:5px 10px;font-size:12px}}
.btn-ghost{{background:transparent;color:{MUTED};padding:5px 10px;font-size:12px}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}}
.empty{{text-align:center;padding:40px;color:{MUTED}}}
.brief-section{{background:{SURFACE};border-radius:8px;padding:12px;margin-bottom:10px;border-left:3px solid {GOLD}}}
.brief-section h4{{font-size:12px;color:{GOLD};text-transform:uppercase;margin-bottom:6px}}
.brief-section p,.brief-section pre{{font-size:13px;white-space:pre-wrap;color:{TEXT}}}
.activity-item{{padding:6px 0;border-bottom:1px solid {BORDER}22;font-size:12px}}
.activity-item .time{{color:{MUTED};min-width:120px;display:inline-block}}
@media(max-width:900px){{.kanban{{flex-direction:column}}.form-grid,.grid-2,.grid-3{{grid-template-columns:1fr}}.stat-grid{{grid-template-columns:repeat(2,1fr)}}}}
"""


def _nav(active=""):
    tabs = [("dashboard", "Pipeline", "/"), ("deals", "All Prospects", "/deals"), ("outreach", "Outreach", "/outreach"), ("import", "Import CSV", "/import")]
    links = "".join(f'<a href="{h}" class="{"active" if t==active else ""}">{l}</a>' for t, l, h in tabs)
    return f'''<nav class="topnav"><div class="topnav-inner">
        <a href="/" class="logo">Sales<span>Pipeline™</span></a>
        <div class="nav-links">{links}<a href="/deals/add" class="btn btn-primary btn-sm" style="margin-left:8px">+ New Deal</a></div>
    </div></nav>'''


def _shell(title, content, active=""):
    return f'''<!DOCTYPE html><html lang="en"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>{_esc(title)} — Sales Pipeline™</title>
    <style>{CSS}</style></head><body>{_nav(active)}<div class="container">{content}</div>
    </body></html>'''


def render_page(page, title, data, error=""):
    if page == "dashboard":
        return _shell(title, _dashboard(data), "dashboard")
    elif page == "deals":
        return _shell(title, _deals_list(data), "deals")
    elif page == "add_deal":
        return _shell(title, _add_deal(data), "deals")
    elif page == "deal_detail":
        return _shell(title, _deal_detail(data), "deals")
    elif page == "outreach":
        return _shell(title, _outreach(data), "outreach")
    elif page == "new_proposal":
        return _shell(title, _new_proposal(data), "deals")
    elif page == "import":
        return _shell(title, _import_page(data), "import")
    return _shell(title, "<p>Not found</p>")


def _dashboard(data):
    s = data["stats"]
    deals_by_stage = data["deals_by_stage"]
    activity = data.get("activity", [])
    followups = data.get("followups", [])
    tier1_queue = data.get("tier1_queue", [])

    sprint = _sprint_header(s, tier1_queue)

    stats = f'''<div class="stat-grid">
        <div class="stat"><div class="val">{s["total_active"]}</div><div class="lbl">Active Deals</div></div>
        <div class="stat"><div class="val" style="color:{GREEN}">{_money(s["pipeline_value"])}</div><div class="lbl">Pipeline Value</div></div>
        <div class="stat"><div class="val">{s["outreach_today"]}</div><div class="lbl">Outreach Today</div></div>
        <div class="stat"><div class="val">{s["outreach_week"]}</div><div class="lbl">Outreach (7d)</div></div>
        <div class="stat"><div class="val" style="color:{YELLOW}">{s["meetings_this_week"]}</div><div class="lbl">Meetings</div></div>
        <div class="stat"><div class="val" style="color:{PURPLE}">{s["proposals_out"]}</div><div class="lbl">Proposals Out</div></div>
        <div class="stat"><div class="val" style="color:{GREEN}">{s["deals_won"]}</div><div class="lbl">Deals Won</div></div>
        <div class="stat"><div class="val" style="color:{RED if s['followups_due']>0 else MUTED}">{s["followups_due"]}</div><div class="lbl">Follow-ups Due</div></div>
    </div>'''

    # Kanban
    cols = ""
    for stage in STAGES[:-1]:  # Exclude Closed Lost from kanban
        color = STAGE_COLORS.get(stage, MUTED)
        cards = ""
        stage_deals = deals_by_stage.get(stage, [])
        count = len(stage_deals)
        for d in stage_deals:
            d = dict(d)
            total = (d.get("setup_fee") or 0) + (d.get("monthly_fee") or 0) * 12
            tier_val = d.get("tier") or 0
            cards += f'''<a href="/deals/{d["id"]}" style="text-decoration:none;color:inherit"><div class="kanban-card">
                <div class="company" style="display:flex;align-items:center;gap:4px">{_esc(d["company"])}{_tier_badge(tier_val)}</div>
                <div class="contact">{_esc(d.get("contact_name") or "")}</div>
                {_stage_dots(d["stage"])}
                {f'<div class="amount">{_money(total)}/yr</div>' if total > 0 else ""}
                {f'<div class="tag">{_esc(d["industry"])}</div>' if d.get("industry") else ""}
            </div></a>'''
        if not cards:
            cards = f'<div style="color:{MUTED};font-size:11px;text-align:center;padding:20px">No deals</div>'
        cols += f'''<div class="kanban-col">
            <h3 style="color:{color}">{stage} <span class="badge" style="background:{color}22;color:{color}">{count}</span></h3>
            {cards}
        </div>'''

    kanban = f'<div class="card" style="overflow-x:auto"><h2>Pipeline Board</h2><div class="kanban">{cols}</div></div>'

    # Follow-ups due
    fu_html = ""
    if followups:
        rows = ""
        for f in followups[:10]:
            rows += f'<tr><td>{_esc(f.get("deal_company") or f.get("company",""))}</td><td>{_esc(f["contact"])}</td><td>{_esc(f["channel"])}</td><td style="color:{MUTED}">{_esc(f.get("follow_up_date",""))}</td></tr>'
        fu_html = f'<div class="card"><h2 style="color:{RED}">Follow-ups Due ({len(followups)})</h2><table><tr><th>Company</th><th>Contact</th><th>Channel</th><th>Due</th></tr>{rows}</table></div>'

    # Recent activity
    act_html = ""
    if activity:
        items = ""
        for a in activity[:12]:
            items += f'<div class="activity-item"><span class="time">{_esc((a["created_at"] or "")[:16])}</span> <strong>{_esc(a["activity_type"])}</strong> — {_esc(a["description"] or "")}</div>'
        act_html = f'<div class="card"><h2>Recent Activity</h2>{items}</div>'

    # All prospects scrollable table
    all_deals = data.get("all_deals", [])
    prospects_rows = ""
    if all_deals:
        for d in all_deals:
            color = STAGE_COLORS.get(d["stage"], MUTED)
            total = (d["setup_fee"] or 0) + (d["monthly_fee"] or 0) * 12
            prospects_rows += f'''<tr>
                <td><a href="/deals/{d["id"]}" style="font-weight:700">{_esc(d["company"])}</a></td>
                <td style="font-size:12px">{_esc(d["contact_name"] or "")}</td>
                <td style="font-size:11px;color:{MUTED}">{_esc(d["industry"] or "")}</td>
                <td>
                    <span class="badge" style="background:{color}22;color:{color}">{_esc(d["stage"])}</span>
                    {_stage_dots(d["stage"])}
                </td>
                <td style="color:{GOLD};font-weight:600;font-size:12px">{_money(total) if total > 0 else "—"}</td>
            </tr>'''
        prospects_table = f'''<div class="card" style="margin-top:14px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                <h2 style="margin:0">All Prospects <span style="color:{MUTED};font-weight:400;font-size:12px">({len(all_deals)})</span></h2>
                <div style="display:flex;gap:8px">
                    <a href="/import" class="btn btn-secondary btn-sm">⬆ Import CSV</a>
                    <a href="/deals" class="btn btn-secondary btn-sm">View All →</a>
                </div>
            </div>
            <div style="overflow-y:auto;max-height:340px">
                <table><thead><tr><th>Company</th><th>Contact</th><th>Industry</th><th>Stage</th><th>Value</th></tr></thead>
                <tbody>{prospects_rows}</tbody></table>
            </div>
        </div>'''
    else:
        prospects_table = f'''<div class="card" style="margin-top:14px">
            <h2>All Prospects</h2>
            <div class="empty" style="padding:30px">
                <p>No prospects yet.</p>
                <a href="/import" class="btn btn-primary" style="margin-top:10px">⬆ Import CSV</a>
                <a href="/deals/add" class="btn btn-secondary" style="margin-top:10px;margin-left:8px">+ Add Manually</a>
            </div>
        </div>'''

    return sprint + stats + kanban + f'<div class="grid-2">{fu_html}{act_html}</div>' + prospects_table


def _deals_list(data):
    deals = data.get("deals", [])

    action_buttons = f'''<div style="display:flex;gap:8px;flex-wrap:wrap">
        <a href="/deals/add" class="btn btn-primary btn-sm">+ New Deal</a>
        <a href="/import" class="btn btn-secondary btn-sm">⬆ Import CSV</a>
        <button onclick="syncOutreach()" id="sync-btn" class="btn btn-secondary btn-sm">⟳ Sync Today's Outreach</button>
    </div>'''

    sync_script = f'''<script>
async function syncOutreach() {{
    const btn = document.getElementById('sync-btn');
    btn.textContent = 'Syncing...';
    btn.disabled = true;
    try {{
        const r = await fetch('/deals/sync-outreach', {{method:'POST'}});
        const d = await r.json();
        if (d.ok) {{
            btn.textContent = '✓ Synced (' + d.added + ' added)';
            btn.style.color = '{GREEN}';
            setTimeout(() => location.reload(), 1200);
        }} else {{
            btn.textContent = 'Error: ' + (d.error || 'Unknown');
            btn.style.color = '{RED}';
            btn.disabled = false;
        }}
    }} catch(e) {{
        btn.textContent = 'Network error';
        btn.style.color = '{RED}';
        btn.disabled = false;
    }}
}}
</script>'''

    if not deals:
        return f'''<div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <h2 style="margin:0">All Prospects</h2>
            {action_buttons}
        </div>
        <div class="empty"><h3>No prospects yet</h3><p>Import a CSV or add your first prospect manually.</p></div>
        {sync_script}</div>'''

    rows = ""
    for d in deals:
        color = STAGE_COLORS.get(d["stage"], MUTED)
        total = (d["setup_fee"] or 0) + (d["monthly_fee"] or 0) * 12
        dots = _stage_dots(d["stage"])
        rows += f'''<tr>
            <td><a href="/deals/{d["id"]}"><strong>{_esc(d["company"])}</strong></a></td>
            <td style="font-size:12px">{_esc(d["contact_name"] or "")}<br><span style="color:{MUTED};font-size:11px">{_esc(d["contact_email"] or "")}</span></td>
            <td style="font-size:12px">{_esc(d["industry"] or "")}</td>
            <td>
                <span class="badge" style="background:{color}22;color:{color}">{_esc(d["stage"])}</span>
                {dots}
            </td>
            <td style="color:{GOLD};font-weight:600">{_money(total) if total > 0 else "—"}</td>
            <td style="color:{MUTED};font-size:12px">{_esc(d["next_action"] or "")}</td>
            <td style="color:{MUTED};font-size:11px">{_esc((d["updated_at"] or "")[:10])}</td>
        </tr>'''

    return f'''<div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:8px">
            <div>
                <h2 style="margin:0;font-size:16px;color:{TEXT}">All Prospects <span style="color:{MUTED};font-weight:400">({len(deals)})</span></h2>
                <div style="font-size:11px;color:{MUTED};margin-top:2px">Stage dots: Intake → Qualified → Meeting → Proposal → Won</div>
            </div>
            {action_buttons}
        </div>
        <div style="overflow-x:auto">
        <table><tr><th>Company</th><th>Contact</th><th>Industry</th><th>Stage</th><th>Value</th><th>Next Action</th><th>Updated</th></tr>{rows}</table>
        </div>
    </div>{sync_script}'''


def _add_deal(data):
    industry_opts = "".join(f'<option value="{i}">{i}</option>' for i in data.get("industries", []))
    return f'''<div style="max-width:700px;margin:0 auto">
    <div class="card">
        <h2>Add New Deal</h2>
        <form method="POST" action="/deals/add">
            <div class="form-grid">
                <div class="form-group"><label>Company Name *</label><input type="text" name="company" required placeholder="Naples HVAC Co."></div>
                <div class="form-group"><label>Contact Name</label><input type="text" name="contact_name" placeholder="John Smith"></div>
                <div class="form-group"><label>Phone</label><input type="tel" name="contact_phone" placeholder="(239) 555-0100"></div>
                <div class="form-group"><label>Email</label><input type="email" name="contact_email" placeholder="john@company.com"></div>
                <div class="form-group"><label>Industry</label><select name="industry">{industry_opts}</select></div>
                <div class="form-group"><label>Lead Source</label><input type="text" name="lead_source" placeholder="Apollo, Yelp, Referral..."></div>
            </div>
            <div class="form-group"><label>Pain Points</label><textarea name="pain_points" rows="2" placeholder="What problems does this business have that AI can solve?"></textarea></div>
            <div class="form-group"><label>Notes</label><textarea name="notes" rows="2" placeholder="Any additional context..."></textarea></div>
            <button type="submit" class="btn btn-primary">Add Deal</button>
        </form>
    </div></div>'''


def _deal_detail(data):
    _raw_deal = data["deal"]
    d = dict(_raw_deal) if not isinstance(_raw_deal, dict) else _raw_deal
    outreach = data.get("outreach", [])
    proposals = data.get("proposals", [])
    briefs = data.get("briefs", [])
    activities = data.get("activities", [])
    color = STAGE_COLORS.get(d["stage"], MUTED)
    total_value = (d.get("setup_fee") or 0) + (d.get("monthly_fee") or 0) * 12

    # Stage selector
    stage_btns = ""
    for s in STAGES:
        sc = STAGE_COLORS.get(s, MUTED)
        active = "border-width:2px" if s == d["stage"] else "opacity:0.5"
        stage_btns += f'<form method="POST" action="/deals/{d["id"]}/stage" style="display:inline"><input type="hidden" name="stage" value="{s}"><button type="submit" class="btn btn-sm" style="background:{sc}22;color:{sc};border:1px solid {sc}44;{active};margin:2px">{s}</button></form>'

    # Deal info
    info = f'''<div class="card">
        <div style="display:flex;justify-content:space-between;align-items:start;flex-wrap:wrap;gap:12px">
            <div>
                <span class="badge" style="background:{color}22;color:{color};font-size:13px;padding:4px 14px">{_esc(d["stage"])}</span>
                <h3 style="font-size:22px;margin-top:8px">{_esc(d["company"])}</h3>
                <div style="color:{MUTED};font-size:13px">{_esc(d["industry"] or "")} {" · " + _esc(d["lead_source"]) if d.get("lead_source") else ""}</div>
            </div>
            <div style="text-align:right">
                <div style="font-size:28px;font-weight:800;color:{GOLD}">{_money(total_value)}<span style="font-size:12px;color:{MUTED}">/yr</span></div>
                <div style="font-size:12px;color:{MUTED}">{_money(d["setup_fee"] or 0)} setup + {_money(d["monthly_fee"] or 0)}/mo</div>
            </div>
        </div>
        <div style="margin-top:12px">{stage_btns}</div>
    </div>'''

    # Contact + details
    details = f'''<div class="card"><h2>Details</h2>
        <form method="POST" action="/deals/{d["id"]}/update">
        <div class="form-grid">
            <div class="form-group"><label>Contact</label><input name="contact_name" value="{_esc(d["contact_name"] or "")}"></div>
            <div class="form-group"><label>Phone</label><input name="contact_phone" value="{_esc(d["contact_phone"] or "")}"></div>
            <div class="form-group"><label>Email</label><input name="contact_email" value="{_esc(d["contact_email"] or "")}"></div>
            <div class="form-group"><label>Next Action</label><input name="next_action" value="{_esc(d["next_action"] or "")}" placeholder="e.g., Follow up Tuesday"></div>
            <div class="form-group"><label>Next Action Date</label><input type="date" name="next_action_date" value="{_esc(d["next_action_date"] or "")}"></div>
            <div class="form-group"><label>Setup Fee</label><input type="number" name="setup_fee" value="{d["setup_fee"] or 0}"></div>
            <div class="form-group"><label>Monthly Fee</label><input type="number" name="monthly_fee" value="{d["monthly_fee"] or 0}"></div>
        </div>
        <div class="form-group"><label>Pain Points</label><textarea name="pain_points" rows="2">{_esc(d["pain_points"] or "")}</textarea></div>
        <div class="form-group"><label>Notes</label><textarea name="notes" rows="2">{_esc(d["notes"] or "")}</textarea></div>
        <button type="submit" class="btn btn-sm btn-secondary">Save Changes</button>
        </form>
    </div>'''

    # Action buttons
    actions = f'''<div class="card"><h2>Actions</h2>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
            <a href="/deals/{d["id"]}/proposal/new" class="btn btn-primary btn-sm">📄 Generate Proposal</a>
            <form method="POST" action="/deals/{d["id"]}/brief/generate" style="display:inline"><button type="submit" class="btn btn-secondary btn-sm">🧠 Pre-Call Brief</button></form>
            <form method="POST" action="/deals/{d["id"]}/delete" onsubmit="return confirm('Delete this deal?')" style="display:inline"><button type="submit" class="btn btn-danger btn-sm">Delete</button></form>
        </div>
    </div>'''

    # Briefs
    briefs_html = ""
    if briefs:
        for b in briefs[:3]:
            briefs_html += f'''<div class="card"><h2>Pre-Call Brief ({_esc((b["created_at"] or "")[:10])})</h2>
                <div class="brief-section"><h4>Company Research</h4><pre>{_esc(b.get("company_research",""))}</pre></div>
                <div class="brief-section"><h4>Common Pain Points</h4><pre>{_esc(b.get("pain_points",""))}</pre></div>
                <div class="brief-section"><h4>Talking Points</h4><pre>{_esc(b.get("talking_points",""))}</pre></div>
                <div class="brief-section"><h4>Questions to Ask</h4><pre>{_esc(b.get("questions_to_ask",""))}</pre></div>
                <div class="brief-section"><h4>Competitive Landscape</h4><pre>{_esc(b.get("competitive_landscape",""))}</pre></div>
                <div class="brief-section" style="border-left-color:{GREEN}"><h4>Recommended Solution & ROI</h4><pre>{_esc(b.get("recommended_solution",""))}</pre></div>
            </div>'''

    # Proposals
    prop_html = ""
    if proposals:
        rows = ""
        for p in proposals:
            rows += f'<tr><td>{_esc(p["title"])}</td><td>{_money(p["setup_fee"])}</td><td>{_money(p["monthly_fee"])}/mo</td><td>{_esc(p["status"])}</td><td style="color:{MUTED}">{_esc((p["created_at"] or "")[:10])}</td></tr>'
        prop_html = f'<div class="card"><h2>Proposals</h2><table><tr><th>Title</th><th>Setup</th><th>Monthly</th><th>Status</th><th>Date</th></tr>{rows}</table></div>'

    # Interaction Timeline (all channels)
    CHANNEL_ICONS = {
        "Email": "📧", "Call": "📞", "In-Person": "🤝",
        "SMS": "💬", "LinkedIn": "💼", "DM": "💬", "Referral": "🔗",
    }
    out_html = ""
    if outreach:
        timeline_items = ""
        for o in outreach:
            o = dict(o) if not isinstance(o, dict) else o
            ch = o.get("channel") or "Email"
            icon = CHANNEL_ICONS.get(ch, "📋")
            summary = _esc(o.get("message_summary") or "")
            response = _esc(o.get("response") or "")
            date_str = _esc((o.get("created_at") or "")[:10])
            timeline_items += f'''<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid {BORDER}22">
                <div style="font-size:20px;flex-shrink:0;padding-top:2px">{icon}</div>
                <div style="flex:1">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:2px">
                        <span style="font-size:12px;font-weight:600;color:{TEXT}">{_esc(ch)}</span>
                        <span style="font-size:11px;color:{MUTED}">{date_str}</span>
                    </div>
                    <div style="font-size:13px;color:{TEXT}">{summary}</div>
                    {f'<div style="font-size:12px;color:{MUTED};margin-top:3px">{response}</div>' if response else ""}
                </div>
            </div>'''
        out_html = f'<div class="card"><h2>Interaction Timeline</h2><div style="max-height:400px;overflow-y:auto">{timeline_items}</div></div>'

    # Activity
    act_items = ""
    for a in activities[:15]:
        act_items += f'<div class="activity-item"><span class="time">{_esc((a["created_at"] or "")[:16])}</span> <strong>{_esc(a["activity_type"])}</strong> — {_esc(a["description"] or "")}</div>'
    act_html = f'<div class="card"><h2>Activity</h2>{act_items}</div>' if act_items else ""

    send_proposal = _send_proposal_section(d)
    precall = _precall_intel(d)
    call_log = _call_logger(d)
    visit_log = _visit_logger(d)

    return (
        f'<a href="/deals" class="btn btn-ghost" style="margin-bottom:12px">← All Deals</a>'
        + info + actions + precall + call_log + visit_log + send_proposal
        + f'<div class="grid-2">{details}{briefs_html or ""}</div>'
        + prop_html + out_html + act_html
    )


def _precall_intel(d: dict) -> str:
    """One-click research launchers + email context before a call."""
    tier_val = d.get("tier") or 0
    if tier_val == 1:
        tier_label = "Tier 1 — Deep Research"
        tier_style = f"background:#C9963C22;color:#C9963C;border:1px solid #C9963C44"
        tier_text = "T1"
    elif tier_val == 2:
        tier_label = "Tier 2 — Industry Template"
        tier_style = f"background:#58a6ff22;color:#58a6ff;border:1px solid #58a6ff44"
        tier_text = "T2"
    else:
        tier_label = "Tier Unknown"
        tier_style = f"background:#8b949e22;color:#8b949e;border:1px solid #8b949e44"
        tier_text = "—"

    verdict = _esc(d.get("research_verdict") or "No research recorded — add notes below")
    template = _esc(d.get("email_template") or "Not recorded")
    company_q = urllib.parse.quote_plus((d.get("company") or "") + " Naples FL")
    company_raw = urllib.parse.quote_plus(d.get("company") or "")
    website = d.get("website") or ""

    website_btn = (
        f'<a href="{_esc(website)}" target="_blank" rel="noopener" style="display:flex;align-items:center;justify-content:center;gap:6px;padding:12px 14px;border-radius:8px;background:{SURFACE};border:1px solid #C9963C44;color:{TEXT};font-size:13px;font-weight:600;text-decoration:none;min-height:44px">🌐 Website</a>'
        if website else
        f'<span style="display:flex;align-items:center;justify-content:center;gap:6px;padding:12px 14px;border-radius:8px;background:{SURFACE};border:1px solid {BORDER};color:{MUTED};font-size:13px;font-weight:600;min-height:44px;opacity:0.5">🌐 Website</span>'
    )

    launchers = f'''<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-top:12px">
        <a href="https://www.google.com/search?q={company_q}" target="_blank" rel="noopener" style="display:flex;align-items:center;justify-content:center;gap:6px;padding:12px 14px;border-radius:8px;background:{SURFACE};border:1px solid {BORDER};color:{TEXT};font-size:13px;font-weight:600;text-decoration:none;min-height:44px">🔍 Google</a>
        <a href="https://www.facebook.com/search/top?q={company_raw}" target="_blank" rel="noopener" style="display:flex;align-items:center;justify-content:center;gap:6px;padding:12px 14px;border-radius:8px;background:{SURFACE};border:1px solid {BORDER};color:{TEXT};font-size:13px;font-weight:600;text-decoration:none;min-height:44px">📘 Facebook</a>
        <a href="https://www.linkedin.com/search/results/companies/?keywords={company_raw}" target="_blank" rel="noopener" style="display:flex;align-items:center;justify-content:center;gap:6px;padding:12px 14px;border-radius:8px;background:{SURFACE};border:1px solid {BORDER};color:{TEXT};font-size:13px;font-weight:600;text-decoration:none;min-height:44px">💼 LinkedIn</a>
        {website_btn}
        <a href="https://www.google.com/maps/search/{company_q}" target="_blank" rel="noopener" style="display:flex;align-items:center;justify-content:center;gap:6px;padding:12px 14px;border-radius:8px;background:{SURFACE};border:1px solid {BORDER};color:{TEXT};font-size:13px;font-weight:600;text-decoration:none;min-height:44px">🗺️ Maps</a>
    </div>'''

    return f'''<div class="card">
        <h2>Pre-Call Intel</h2>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
            <span style="{tier_style};border-radius:6px;font-size:13px;font-weight:800;padding:4px 12px">{tier_text}</span>
            <span style="font-size:13px;color:{MUTED}">{tier_label}</span>
        </div>
        <div class="brief-section">
            <h4>Research Verdict</h4>
            <p>{verdict}</p>
        </div>
        <div style="font-size:12px;color:{MUTED};margin-bottom:4px">Email template used: <span style="color:{TEXT}">{template}</span></div>
        <div style="font-size:11px;font-weight:700;color:{GOLD};text-transform:uppercase;letter-spacing:.5px;margin-top:12px;margin-bottom:2px">Quick Research</div>
        {launchers}
    </div>'''


def _call_logger(d: dict) -> str:
    """Compact inline call logger — no page reload."""
    deal_id = d["id"]
    outcomes = ["Answered - Interested", "Answered - Not Interested", "Answered - Callback", "Voicemail", "No Answer"]
    opts = "".join(f'<option value="{o}">{o}</option>' for o in outcomes)
    return f'''<div class="card" id="call-logger-{deal_id}">
        <h2>Log a Call</h2>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end">
            <div style="flex:0 0 220px">
                <label style="font-size:11px;color:{MUTED};margin-bottom:4px;display:block">Outcome</label>
                <select id="call-outcome-{deal_id}" style="padding:10px 12px;min-height:44px">{opts}</select>
            </div>
            <div style="flex:1;min-width:160px">
                <label style="font-size:11px;color:{MUTED};margin-bottom:4px;display:block">Notes</label>
                <input type="text" id="call-notes-{deal_id}" placeholder="e.g. Spoke to owner, call back Thursday 2pm" style="padding:10px 12px;min-height:44px">
            </div>
            <button onclick="logCall({deal_id})" style="padding:10px 18px;border-radius:8px;background:{GOLD};color:#333;font-weight:700;font-size:13px;border:none;cursor:pointer;min-height:44px;flex-shrink:0">Log Call</button>
        </div>
        <div id="call-result-{deal_id}" style="margin-top:8px;font-size:12px;display:none"></div>
    </div>
    <script>
    async function logCall(id) {{
        const outcome = document.getElementById('call-outcome-' + id).value;
        const notes = document.getElementById('call-notes-' + id).value;
        const res = document.getElementById('call-result-' + id);
        const fd = new FormData();
        fd.append('outcome', outcome);
        fd.append('notes', notes);
        res.style.display = 'block';
        res.style.color = '{MUTED}';
        res.textContent = 'Logging...';
        try {{
            const r = await fetch('/deals/' + id + '/log-call', {{method:'POST', body:fd}});
            const j = await r.json();
            if (j.ok) {{
                res.style.color = '{GREEN}';
                res.textContent = '✓ Call logged';
                document.getElementById('call-notes-' + id).value = '';
                setTimeout(() => location.reload(), 1200);
            }} else {{
                res.style.color = '{RED}';
                res.textContent = 'Error: ' + (j.error || 'Unknown');
            }}
        }} catch(e) {{
            res.style.color = '{RED}';
            res.textContent = 'Network error: ' + e.message;
        }}
    }}
    </script>'''


def _visit_logger(d: dict) -> str:
    """Compact inline in-person visit logger — no page reload."""
    deal_id = d["id"]
    reactions = ["Positive", "Neutral", "Not Interested", "Requested Follow-up"]
    opts = "".join(f'<option value="{r}">{r}</option>' for r in reactions)
    return f'''<div class="card" id="visit-logger-{deal_id}">
        <h2>Log an In-Person Visit</h2>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end">
            <div style="flex:0 0 160px">
                <label style="font-size:11px;color:{MUTED};margin-bottom:4px;display:block">Spoke To</label>
                <input type="text" id="visit-spoke-{deal_id}" placeholder="Owner, manager..." style="padding:10px 12px;min-height:44px">
            </div>
            <div style="flex:0 0 180px">
                <label style="font-size:11px;color:{MUTED};margin-bottom:4px;display:block">Reaction</label>
                <select id="visit-reaction-{deal_id}" style="padding:10px 12px;min-height:44px">{opts}</select>
            </div>
            <div style="flex:1;min-width:140px">
                <label style="font-size:11px;color:{MUTED};margin-bottom:4px;display:block">Notes</label>
                <input type="text" id="visit-notes-{deal_id}" placeholder="What happened?" style="padding:10px 12px;min-height:44px">
            </div>
            <button onclick="logVisit({deal_id})" style="padding:10px 18px;border-radius:8px;background:{GOLD};color:#333;font-weight:700;font-size:13px;border:none;cursor:pointer;min-height:44px;flex-shrink:0">Log Visit</button>
        </div>
        <div id="visit-result-{deal_id}" style="margin-top:8px;font-size:12px;display:none"></div>
    </div>
    <script>
    async function logVisit(id) {{
        const spoke = document.getElementById('visit-spoke-' + id).value;
        const reaction = document.getElementById('visit-reaction-' + id).value;
        const notes = document.getElementById('visit-notes-' + id).value;
        const res = document.getElementById('visit-result-' + id);
        const fd = new FormData();
        fd.append('spoke_to', spoke);
        fd.append('reaction', reaction);
        fd.append('notes', notes);
        res.style.display = 'block';
        res.style.color = '{MUTED}';
        res.textContent = 'Logging...';
        try {{
            const r = await fetch('/deals/' + id + '/log-visit', {{method:'POST', body:fd}});
            const j = await r.json();
            if (j.ok) {{
                res.style.color = '{GREEN}';
                res.textContent = '✓ Visit logged';
                document.getElementById('visit-spoke-' + id).value = '';
                document.getElementById('visit-notes-' + id).value = '';
                setTimeout(() => location.reload(), 1200);
            }} else {{
                res.style.color = '{RED}';
                res.textContent = 'Error: ' + (j.error || 'Unknown');
            }}
        }} catch(e) {{
            res.style.color = '{RED}';
            res.textContent = 'Network error: ' + e.message;
        }}
    }}
    </script>'''


def _send_proposal_section(d: dict) -> str:
    """Render the 'Send Proposal & Agreement' card for the deal detail page."""
    deal_id = d["id"]
    contact_name  = _esc(d.get("contact_name") or "")
    contact_email = _esc(d.get("contact_email") or "")
    pain_points   = _esc(d.get("pain_points") or "")

    tier_opts = "".join(
        f'<option value="{n}">{label}</option>'
        for n, label in [
            (1, "Tier 1 — Starter  ($497/mo)"),
            (2, "Tier 2 — Growth   ($997/mo)"),
            (3, "Tier 3 — Pro      ($1,497/mo)"),
            (4, "Tier 4 — Elite    ($2,497/mo)"),
        ]
    )

    return f'''
<div class="card" id="send-proposal-card">
  <h2>Send Proposal &amp; Agreement</h2>
  <p style="font-size:12px;color:{MUTED};margin-bottom:14px">
    Generates PDFs, emails the client, creates a branded signing link, and advances stage to Proposal Sent.
  </p>
  <form id="proposal-form" onsubmit="sendProposal(event, {deal_id})">
    <div class="form-grid">
      <div class="form-group">
        <label>Client Name</label>
        <input type="text" name="client_name" value="{contact_name}" required placeholder="Full name">
      </div>
      <div class="form-group">
        <label>Client Email</label>
        <input type="email" name="client_email" value="{contact_email}" required placeholder="email@company.com">
      </div>
      <div class="form-group">
        <label>Tier</label>
        <select name="tier">{tier_opts}</select>
      </div>
      <div class="form-group">
        <label>Pain Point</label>
        <input type="text" name="pain_point" value="{pain_points}" placeholder="Their main problem AI can solve" required>
      </div>
    </div>
    <button type="submit" id="proposal-btn" class="btn btn-primary">
      Generate &amp; Send &rarr;
    </button>
  </form>
  <div id="proposal-result" style="display:none;margin-top:14px"></div>
</div>

<script>
async function sendProposal(e, dealId) {{
  e.preventDefault();
  const btn = document.getElementById('proposal-btn');
  const result = document.getElementById('proposal-result');
  btn.disabled = true;
  btn.textContent = 'Sending…';
  result.style.display = 'none';

  const form = document.getElementById('proposal-form');
  const data = new FormData(form);

  try {{
    const r = await fetch(`/deals/${{dealId}}/send-proposal`, {{
      method: 'POST',
      body: data,
    }});
    const j = await r.json();
    if (j.ok) {{
      result.style.display = 'block';
      result.innerHTML = `
        <div style="background:#0d2a00;border:1px solid #3fb95044;border-radius:8px;padding:14px 18px;font-size:13px">
          <div style="color:#3fb950;font-weight:700;margin-bottom:8px">Proposal sent!</div>
          <div style="margin-bottom:6px">
            <span style="color:{MUTED}">Signing URL: </span>
            <a href="${{j.signing_url}}" target="_blank" style="color:{GOLD};word-break:break-all">${{j.signing_url}}</a>
          </div>
          <div style="margin-bottom:6px">
            <span style="color:{MUTED}">Deal stage: </span>
            <span style="color:#bc8cff;font-weight:600">Proposal Sent</span>
          </div>
          ${{j.email_sent ? '<div style="color:{MUTED}">Email sent to client.</div>' : ''}}
        </div>`;
      btn.textContent = 'Sent!';
      btn.style.opacity = '0.6';
      // Refresh the stage badge after 2s
      setTimeout(() => location.reload(), 3000);
    }} else {{
      result.style.display = 'block';
      result.innerHTML = `<div style="background:#2d0a0a;border:1px solid #f8514944;border-radius:8px;padding:12px 16px;color:#f85149;font-size:13px">Error: ${{j.error || 'Unknown error'}}</div>`;
      btn.disabled = false;
      btn.textContent = 'Generate & Send →';
    }}
  }} catch(err) {{
    result.style.display = 'block';
    result.innerHTML = `<div style="background:#2d0a0a;border:1px solid #f8514944;border-radius:8px;padding:12px 16px;color:#f85149;font-size:13px">Network error: ${{err}}</div>`;
    btn.disabled = false;
    btn.textContent = 'Generate & Send →';
  }}
}}
</script>'''


def _outreach(data):
    log = data.get("log", [])
    followups = data.get("followups", [])
    deals = data.get("deals", [])
    channels = data.get("channels", [])

    deal_opts = '<option value="">— No deal —</option>' + "".join(f'<option value="{d["id"]}">{_esc(d["company"])}</option>' for d in deals)
    ch_opts = "".join(f'<option value="{c}">{c}</option>' for c in channels)

    form = f'''<div class="card"><h2>Log Outreach</h2>
        <form method="POST" action="/outreach/log">
        <div class="form-grid">
            <div class="form-group"><label>Link to Deal</label><select name="deal_id">{deal_opts}</select></div>
            <div class="form-group"><label>Company</label><input name="company" placeholder="If not linked to deal"></div>
            <div class="form-group"><label>Contact</label><input name="contact" placeholder="Name"></div>
            <div class="form-group"><label>Channel</label><select name="channel">{ch_opts}</select></div>
            <div class="form-group"><label>Message</label><input name="message" placeholder="What did you say?"></div>
            <div class="form-group"><label>Follow-up Date</label><input type="date" name="follow_up_date"></div>
        </div>
        <button type="submit" class="btn btn-primary btn-sm">Log</button>
        </form></div>'''

    # Follow-ups
    fu_html = ""
    if followups:
        rows = "".join(f'<tr><td>{_esc(f.get("deal_company") or f.get("company",""))}</td><td>{_esc(f["contact"])}</td><td>{_esc(f["channel"])}</td><td style="color:{RED}">{_esc(f.get("follow_up_date",""))}</td></tr>' for f in followups)
        fu_html = f'<div class="card"><h2 style="color:{RED}">Follow-ups Due ({len(followups)})</h2><table><tr><th>Company</th><th>Contact</th><th>Channel</th><th>Due</th></tr>{rows}</table></div>'

    # Log
    rows = ""
    for o in log:
        rows += f'<tr><td style="color:{MUTED}">{_esc((o["created_at"] or "")[:10])}</td><td>{_esc(o["company"] or "")}</td><td>{_esc(o["contact"] or "")}</td><td>{_esc(o["channel"])}</td><td>{_esc(o["message_summary"] or "")}</td><td>{_esc(o["response"] or "—")}</td></tr>'
    log_html = f'<div class="card"><h2>Outreach Log</h2><table><tr><th>Date</th><th>Company</th><th>Contact</th><th>Ch</th><th>Message</th><th>Response</th></tr>{rows}</table></div>' if rows else ""

    return form + fu_html + log_html


def _import_page(data):
    result = data.get("result", "")
    error = data.get("error", "")
    result_html = ""
    if result:
        result_html = f'<div style="background:{GREEN}18;border:1px solid {GREEN}44;border-radius:8px;padding:12px 16px;margin-bottom:14px;color:{GREEN};font-size:13px">{_esc(result)}</div>'
    if error:
        result_html = f'<div style="background:{RED}18;border:1px solid {RED}44;border-radius:8px;padding:12px 16px;margin-bottom:14px;color:{RED};font-size:13px">{_esc(error)}</div>'

    return f'''<div style="max-width:700px;margin:0 auto">
    <div class="card">
        <h2>Import Prospects from CSV</h2>
        <p style="font-size:13px;color:{MUTED};margin-bottom:16px">
            Upload a CSV file with prospect data. Expected columns: <code style="background:{SURFACE};padding:1px 5px;border-radius:4px">company</code>,
            <code style="background:{SURFACE};padding:1px 5px;border-radius:4px">contact_name</code>,
            <code style="background:{SURFACE};padding:1px 5px;border-radius:4px">contact_email</code>,
            <code style="background:{SURFACE};padding:1px 5px;border-radius:4px">industry</code>.
            Duplicates (same company name) are skipped automatically.
        </p>
        {result_html}
        <form method="POST" action="/import" enctype="multipart/form-data">
            <div class="form-group">
                <label>CSV File</label>
                <input type="file" name="file" accept=".csv" required style="padding:8px">
            </div>
            <div class="form-group">
                <label>Default Stage</label>
                <select name="stage">
                    <option value="Intake" selected>Intake</option>
                    <option value="Qualified">Qualified</option>
                </select>
            </div>
            <div class="form-group">
                <label>Lead Source</label>
                <input type="text" name="lead_source" placeholder="Apollo, Manual, etc." value="CSV Import">
            </div>
            <button type="submit" class="btn btn-primary">Upload & Import</button>
            <a href="/deals" class="btn btn-secondary" style="margin-left:8px">Cancel</a>
        </form>
    </div>
    <div class="card" style="margin-top:14px">
        <h2>Sync from Today's Outreach</h2>
        <p style="font-size:13px;color:{MUTED};margin-bottom:14px">
            Pull all emails sent today from the outreach tracking file and create deals for any that aren't already in the pipeline.
        </p>
        <button onclick="syncOutreach()" id="sync-btn2" class="btn btn-secondary">⟳ Sync Today's Outreach Now</button>
        <div id="sync-result" style="margin-top:10px;font-size:13px;display:none"></div>
    </div>
    <script>
    async function syncOutreach() {{
        const btn = document.getElementById('sync-btn2');
        const res = document.getElementById('sync-result');
        btn.textContent = 'Syncing...'; btn.disabled = true; res.style.display = 'none';
        try {{
            const r = await fetch('/deals/sync-outreach', {{method:'POST'}});
            const d = await r.json();
            res.style.display = 'block';
            if (d.ok) {{
                res.style.color = '{GREEN}';
                res.textContent = '✓ Done — ' + d.added + ' new deal(s) created, ' + d.skipped + ' already existed.';
                btn.textContent = 'Synced ✓';
            }} else {{
                res.style.color = '{RED}';
                res.textContent = 'Error: ' + (d.error || 'Unknown');
                btn.disabled = false; btn.textContent = '⟳ Sync Today\'s Outreach Now';
            }}
        }} catch(e) {{
            res.style.display = 'block'; res.style.color = '{RED}';
            res.textContent = 'Network error: ' + e.message;
            btn.disabled = false; btn.textContent = '⟳ Sync Today\'s Outreach Now';
        }}
    }}
    </script></div>'''


def _new_proposal(data):
    d = data["deal"]
    return f'''<div style="max-width:700px;margin:0 auto">
    <a href="/deals/{d["id"]}" class="btn btn-ghost" style="margin-bottom:12px">← Back to {_esc(d["company"])}</a>
    <div class="card">
        <h2>Generate Proposal for {_esc(d["company"])}</h2>
        <form method="POST" action="/deals/{d["id"]}/proposal/create">
            <div class="form-group"><label>Proposal Title</label><input name="title" required value="AI Automation for {_esc(d['company'])}"></div>
            <div class="form-grid">
                <div class="form-group"><label>Setup Fee ($)</label><input type="number" name="setup_fee" value="2000"></div>
                <div class="form-group"><label>Monthly Fee ($)</label><input type="number" name="monthly_fee" value="500"></div>
            </div>
            <div class="form-group"><label>Scope Summary</label><textarea name="scope" rows="3" placeholder="What AI systems will be built and deployed...">AI phone answering system with 24/7 availability, appointment booking integration, automated follow-up sequences, and monthly performance reporting.</textarea></div>
            <div class="form-group"><label>Deliverables</label><textarea name="deliverables" rows="4" placeholder="Line-by-line deliverables...">• AI phone answering system (24/7 coverage)\n• Calendar integration for appointment booking\n• Automated SMS follow-up sequences\n• Custom greeting and call routing\n• Monthly analytics dashboard\n• Ongoing optimization and support</textarea></div>
            <div class="form-group"><label>Timeline</label><textarea name="timeline" rows="2" placeholder="Implementation timeline...">Week 1: Discovery + setup. Week 2: Build + test. Week 3: Go live + monitoring. Ongoing: monthly optimization.</textarea></div>
            <button type="submit" class="btn btn-primary">Create Proposal & Move to "Proposal Sent"</button>
        </form>
    </div></div>'''
