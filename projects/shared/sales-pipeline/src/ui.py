"""
Sales Pipeline — Production UI

Kanban pipeline board, deal management, proposal builder,
pre-call intelligence briefs, outreach tracking.
"""

import html as html_mod
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

def _esc(s):
    return html_mod.escape(str(s)) if s else ""

def _money(v):
    try:
        return f"${float(v):,.0f}"
    except (ValueError, TypeError):
        return "$0"

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
    tabs = [("dashboard", "Pipeline", "/"), ("deals", "Deals", "/deals"), ("outreach", "Outreach", "/outreach")]
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
    return _shell(title, "<p>Not found</p>")


def _dashboard(data):
    s = data["stats"]
    deals_by_stage = data["deals_by_stage"]
    activity = data.get("activity", [])
    followups = data.get("followups", [])

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
            total = (d["setup_fee"] or 0) + (d["monthly_fee"] or 0) * 12
            cards += f'''<a href="/deals/{d["id"]}" style="text-decoration:none;color:inherit"><div class="kanban-card">
                <div class="company">{_esc(d["company"])}</div>
                <div class="contact">{_esc(d["contact_name"] or "")}</div>
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

    return stats + kanban + f'<div class="grid-2">{fu_html}{act_html}</div>'


def _deals_list(data):
    deals = data.get("deals", [])
    if not deals:
        return '<div class="empty"><h3>No deals yet</h3><p>Add your first prospect to start tracking.</p><a href="/deals/add" class="btn btn-primary" style="margin-top:12px">+ Add Deal</a></div>'

    rows = ""
    for d in deals:
        color = STAGE_COLORS.get(d["stage"], MUTED)
        total = (d["setup_fee"] or 0) + (d["monthly_fee"] or 0) * 12
        rows += f'''<tr>
            <td><a href="/deals/{d["id"]}"><strong>{_esc(d["company"])}</strong></a></td>
            <td>{_esc(d["contact_name"] or "")}</td>
            <td>{_esc(d["industry"] or "")}</td>
            <td><span class="badge" style="background:{color}22;color:{color}">{_esc(d["stage"])}</span></td>
            <td style="color:{GOLD};font-weight:600">{_money(total) if total > 0 else "—"}</td>
            <td style="color:{MUTED}">{_esc(d["next_action"] or "")}</td>
            <td style="color:{MUTED};font-size:11px">{_esc((d["updated_at"] or "")[:10])}</td>
        </tr>'''

    return f'''<div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <h2 style="margin:0">All Deals ({len(deals)})</h2>
        <a href="/deals/add" class="btn btn-primary btn-sm">+ Add Deal</a>
    </div>
    <table><tr><th>Company</th><th>Contact</th><th>Industry</th><th>Stage</th><th>Value</th><th>Next Action</th><th>Updated</th></tr>{rows}</table></div>'''


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
    d = data["deal"]
    outreach = data.get("outreach", [])
    proposals = data.get("proposals", [])
    briefs = data.get("briefs", [])
    activities = data.get("activities", [])
    color = STAGE_COLORS.get(d["stage"], MUTED)
    total_value = (d["setup_fee"] or 0) + (d["monthly_fee"] or 0) * 12

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

    # Outreach history
    out_html = ""
    if outreach:
        rows = ""
        for o in outreach:
            rows += f'<tr><td style="color:{MUTED}">{_esc((o["created_at"] or "")[:10])}</td><td>{_esc(o["channel"])}</td><td>{_esc(o["message_summary"] or "")}</td><td>{_esc(o["response"] or "—")}</td></tr>'
        out_html = f'<div class="card"><h2>Outreach History</h2><table><tr><th>Date</th><th>Channel</th><th>Message</th><th>Response</th></tr>{rows}</table></div>'

    # Activity
    act_items = ""
    for a in activities[:15]:
        act_items += f'<div class="activity-item"><span class="time">{_esc((a["created_at"] or "")[:16])}</span> <strong>{_esc(a["activity_type"])}</strong> — {_esc(a["description"] or "")}</div>'
    act_html = f'<div class="card"><h2>Activity</h2>{act_items}</div>' if act_items else ""

    return f'<a href="/deals" class="btn btn-ghost" style="margin-bottom:12px">← All Deals</a>' + info + actions + f'<div class="grid-2">{details}{briefs_html or ""}</div>' + prop_html + out_html + act_html


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
