"""
Marceau Accountability Engine — Production UI

YouTube-demo-ready dashboard with animated progress rings, streak tracking,
weekly burn-down charts, goal visualization, and milestone celebrations.
"""

import html
from datetime import datetime

# Brand
GOLD = "#C9963C"
GOLD_DIM = "rgba(201,150,60,0.15)"
GOLD_GLOW = "rgba(201,150,60,0.4)"
CHARCOAL = "#333333"
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


def _pct_color(pct):
    if pct >= 80: return GREEN
    if pct >= 50: return YELLOW
    return RED


def _progress_ring(pct, size=120, stroke=8, label="", sublabel="", color=None):
    """SVG animated progress ring."""
    if color is None:
        color = _pct_color(pct)
    r = (size - stroke) / 2
    circ = 2 * 3.14159 * r
    offset = circ - (pct / 100) * circ
    return f'''<div style="text-align:center">
        <svg width="{size}" height="{size}" style="transform:rotate(-90deg)">
            <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{SURFACE}" stroke-width="{stroke}"/>
            <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke}"
                stroke-dasharray="{circ}" stroke-dashoffset="{offset}" stroke-linecap="round"
                style="transition:stroke-dashoffset 1.5s ease-out"/>
        </svg>
        <div style="margin-top:-{size//2+10}px;position:relative;z-index:1">
            <div style="font-size:{size//4}px;font-weight:800;color:{color}">{pct}%</div>
        </div>
        <div style="margin-top:{size//4-5}px;font-size:13px;font-weight:600;color:{TEXT}">{html.escape(str(label))}</div>
        <div style="font-size:11px;color:{MUTED}">{html.escape(str(sublabel))}</div>
    </div>'''


def _metric_bar(label, current, target, color=GOLD, icon=""):
    """Horizontal progress bar with label."""
    pct = min(100, round((current / target) * 100)) if target else 0
    bar_color = _pct_color(pct)
    return f'''<div style="margin-bottom:14px">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px">
            <span style="font-size:13px;font-weight:600">{icon} {html.escape(str(label))}</span>
            <span style="font-size:13px;color:{bar_color};font-weight:700">{current}/{target}</span>
        </div>
        <div style="background:{SURFACE};border-radius:6px;height:8px;overflow:hidden">
            <div style="background:linear-gradient(90deg,{color},{bar_color});height:8px;border-radius:6px;width:{pct}%;transition:width 1.2s ease-out"></div>
        </div>
    </div>'''


def _stat_card(value, label, icon="", color=GOLD, subtitle=""):
    sub = f'<div style="font-size:10px;color:{MUTED};margin-top:2px">{html.escape(str(subtitle))}</div>' if subtitle else ""
    return f'''<div class="stat">
        <div style="font-size:11px;margin-bottom:4px">{icon}</div>
        <div class="stat-value" style="color:{color}">{value}</div>
        <div class="stat-label">{html.escape(str(label))}</div>
        {sub}
    </div>'''


def _streak_badge(streak):
    if streak == 0:
        return '<span style="color:#8b949e">No active streak</span>'
    if streak >= 7:
        color = GOLD
        emoji = "🔥"
    elif streak >= 3:
        color = GREEN
        emoji = "⚡"
    else:
        color = YELLOW
        emoji = "📈"
    return f'<span style="background:linear-gradient(135deg,{color}22,{color}11);border:1px solid {color}44;padding:6px 14px;border-radius:20px;font-size:14px;font-weight:700;color:{color}">{emoji} {streak}-day streak</span>'


def _milestone_item(name, achieved, date=""):
    if achieved:
        return f'<div style="padding:8px 12px;display:flex;align-items:center;gap:8px;opacity:1"><span style="color:{GREEN};font-size:18px">✓</span><span style="font-weight:600">{html.escape(str(name))}</span><span style="color:{MUTED};font-size:11px;margin-left:auto">{html.escape(str(date))}</span></div>'
    return f'<div style="padding:8px 12px;display:flex;align-items:center;gap:8px;opacity:0.4"><span style="color:{MUTED};font-size:18px">○</span><span>{html.escape(str(name))}</span></div>'


def _energy_chart(energy_data):
    """Simple bar chart for energy/pain trend."""
    if not energy_data:
        return '<div style="color:#8b949e;text-align:center;padding:20px">No energy data yet</div>'

    bars = ""
    for d in energy_data[-10:]:
        e = d.get("energy", 0)
        p = d.get("pain", 0)
        date_short = d.get("date", "")[-5:]  # MM-DD
        e_height = e * 8
        p_height = p * 8
        e_color = GREEN if e >= 7 else (YELLOW if e >= 4 else RED)
        p_color = f"{RED}88" if p > 0 else "transparent"
        bars += f'''<div style="display:flex;flex-direction:column;align-items:center;gap:2px;flex:1">
            <div style="height:80px;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:1px;width:100%">
                <div style="width:60%;background:{e_color};height:{e_height}px;border-radius:3px 3px 0 0;min-height:2px" title="Energy: {e}"></div>
                {'<div style="width:60%;background:'+p_color+';height:'+str(p_height)+'px;border-radius:0 0 3px 3px;min-height:2px" title="Pain: '+str(p)+'"></div>' if p > 0 else ''}
            </div>
            <div style="font-size:9px;color:{MUTED}">{date_short}</div>
        </div>'''

    return f'''<div style="display:flex;gap:4px;align-items:flex-end;padding:8px 0">
        {bars}
    </div>
    <div style="display:flex;gap:16px;justify-content:center;margin-top:4px">
        <span style="font-size:10px;color:{MUTED}"><span style="color:{GREEN}">■</span> Energy</span>
        <span style="font-size:10px;color:{MUTED}"><span style="color:{RED}88">■</span> Pain</span>
    </div>'''


def _daily_log_table(daily_log):
    if not daily_log:
        return '<div style="color:#8b949e;text-align:center;padding:20px">No daily entries yet</div>'

    rows = ""
    for d in reversed(daily_log):
        energy = d.get("Morning_Energy", "—")
        outreach = d.get("Outreach_Count", "—")
        meetings = d.get("Meetings_Booked", "—")
        videos = d.get("Videos_Filmed", "—")
        content = d.get("Content_Posted", "—")
        trained = "✓" if d.get("Training_Session", "").upper() in ("TRUE", "YES", "1") else "—"
        day = d.get("Day_of_Week", "")[:3]
        date = d.get("Date", "")[-5:]
        rows += f'<tr><td style="color:{MUTED}">{day} {date}</td><td>{energy}</td><td style="font-weight:600">{outreach}</td><td>{meetings}</td><td>{videos}</td><td>{content}</td><td style="color:{GREEN if trained == "✓" else MUTED}">{trained}</td></tr>'

    return f'''<table style="width:100%;font-size:12px">
        <tr><th>Day</th><th>⚡</th><th>📤 Out</th><th>🤝 Meet</th><th>🎥 Vid</th><th>📱 Post</th><th>🏋️</th></tr>
        {rows}
    </table>'''


CSS = f"""
* {{ margin:0;padding:0;box-sizing:border-box; }}
body {{ background:{BG};color:{TEXT};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,sans-serif;line-height:1.5; }}
.container {{ max-width:1280px;margin:0 auto;padding:16px 20px; }}
.header {{ display:flex;align-items:center;justify-content:space-between;padding:16px 0;border-bottom:2px solid {GOLD};margin-bottom:20px; }}
.header h1 {{ font-size:22px;font-weight:800;color:{GOLD}; }}
.header h1 span {{ color:{TEXT};font-weight:400; }}
.header-right {{ display:flex;align-items:center;gap:16px; }}
.header-badge {{ background:{GOLD};color:{CHARCOAL};padding:4px 12px;border-radius:16px;font-size:12px;font-weight:700; }}

.grid {{ display:grid;gap:16px; }}
.grid-2 {{ grid-template-columns:1fr 1fr; }}
.grid-3 {{ grid-template-columns:1fr 1fr 1fr; }}
.grid-4 {{ grid-template-columns:repeat(4,1fr); }}
.grid-5 {{ grid-template-columns:repeat(5,1fr); }}

.card {{ background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:18px;position:relative;overflow:hidden; }}
.card-glow {{ border-color:{GOLD}44;box-shadow:0 0 20px {GOLD}11; }}
.card h2 {{ font-size:14px;font-weight:600;color:{MUTED};text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px; }}
.card h3 {{ font-size:16px;font-weight:700;margin-bottom:8px; }}

.stat-grid {{ display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:16px; }}
.stat {{ background:{SURFACE};border:1px solid {BORDER};border-radius:10px;padding:14px;text-align:center;transition:transform .15s,border-color .15s; }}
.stat:hover {{ transform:translateY(-2px);border-color:{GOLD}44; }}
.stat-value {{ font-size:28px;font-weight:800;line-height:1.1; }}
.stat-label {{ font-size:11px;color:{MUTED};margin-top:2px;text-transform:uppercase;letter-spacing:0.3px; }}

.rings {{ display:flex;justify-content:space-around;flex-wrap:wrap;gap:12px;padding:8px 0; }}

table {{ width:100%;border-collapse:collapse; }}
th {{ text-align:left;padding:8px 10px;color:{MUTED};font-size:10px;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid {BORDER}; }}
td {{ padding:8px 10px;border-bottom:1px solid {BORDER}22; }}

.goal-card {{ display:flex;align-items:center;gap:12px;padding:12px;background:{SURFACE};border-radius:10px;border:1px solid {BORDER};margin-bottom:8px;transition:border-color .15s; }}
.goal-card:hover {{ border-color:{GOLD}44; }}
.goal-icon {{ font-size:24px; }}
.goal-info {{ flex:1; }}
.goal-name {{ font-size:13px;font-weight:600; }}
.goal-progress {{ font-size:11px;color:{MUTED}; }}
.goal-bar {{ height:6px;background:{SURFACE};border-radius:3px;margin-top:4px;overflow:hidden; }}
.goal-fill {{ height:6px;border-radius:3px;transition:width 1.2s ease-out; }}
.goal-pct {{ font-size:18px;font-weight:800;min-width:50px;text-align:right; }}

.refresh-btn {{ background:{SURFACE};border:1px solid {BORDER};color:{MUTED};padding:6px 14px;border-radius:8px;cursor:pointer;font-size:12px;transition:all .15s; }}
.refresh-btn:hover {{ border-color:{GOLD};color:{GOLD}; }}

.pulse {{ animation:pulse 2s ease-in-out infinite; }}
@keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.5; }} }}

@media(max-width:900px) {{
    .grid-2,.grid-3,.grid-4,.grid-5 {{ grid-template-columns:1fr; }}
    .rings {{ justify-content:center; }}
    .header {{ flex-direction:column;gap:8px;text-align:center; }}
    .stat-grid {{ grid-template-columns:repeat(2,1fr); }}
}}
@media(min-width:901px) and (max-width:1100px) {{
    .grid-3 {{ grid-template-columns:1fr 1fr; }}
    .grid-5 {{ grid-template-columns:repeat(3,1fr); }}
}}
"""


def render_dashboard(data, error=None):
    if error or not data:
        err_msg = html.escape(str(error)) if error else "Could not load data. Check Google Sheets credentials."
        content = f'''<div class="container">
            <div class="header"><h1>Accountability <span>Engine</span></h1></div>
            <div class="card" style="text-align:center;padding:60px">
                <h3 style="color:{RED}">Connection Error</h3>
                <p style="color:{MUTED};margin-top:8px">{err_msg}</p>
            </div>
        </div>'''
        return _shell("Dashboard", content)

    ctx = data["context"]
    wt = data["week_totals"]
    wp = data["week_pcts"]
    targets = data["targets"]

    # ── Tab Nav ──
    tab_nav = f'''<div style="display:flex;gap:0;border-bottom:2px solid {GOLD};margin-bottom:20px">
        <a href="/" style="padding:10px 20px;font-size:13px;font-weight:700;color:{GOLD};text-decoration:none;border-bottom:2px solid {GOLD};margin-bottom:-2px">90-Day Tracker</a>
        <a href="/sprint" style="padding:10px 20px;font-size:13px;font-weight:600;color:{MUTED};text-decoration:none;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .15s" onmouseover="this.style.color='{GOLD}'" onmouseout="this.style.color='{MUTED}'">Sprint Hub</a>
    </div>'''

    # ── Header ──
    header = f'''<div class="header">
        <div>
            <h1>Accountability <span>Engine</span></h1>
            <div style="font-size:12px;color:{MUTED};margin-top:2px">90-Day Execution Plan — {ctx["plan_start"]} to {ctx["plan_end"]}</div>
        </div>
        <div class="header-right">
            {_streak_badge(data["streak"])}
            <span class="header-badge">Day {ctx["day_number"]} / 84</span>
            <span class="header-badge" style="background:{SURFACE};color:{GOLD};border:1px solid {GOLD}44">Week {ctx["week_number"]}</span>
            <button class="refresh-btn" onclick="location.reload()">↻ Refresh</button>
        </div>
    </div>'''

    # ── Top Stats ──
    on_track_color = _pct_color(data["on_track"])
    stats = f'''<div class="stat-grid">
        {_stat_card(f'{data["on_track"]}%', "On Track", "📊", on_track_color)}
        {_stat_card(ctx["days_remaining"], "Days Left", "⏳", BLUE)}
        {_stat_card(f'{ctx["pct_complete"]}%', "Plan Progress", "🎯", GOLD)}
        {_stat_card(data["total_outreach"], "Total Outreach", "📤", PURPLE)}
        {_stat_card(f'${data["mrr"]:.0f}', "Monthly Revenue", "💰", GREEN)}
        {_stat_card(data["streak"], "Day Streak", "🔥", GOLD if data["streak"]>=3 else MUTED)}
    </div>'''

    # ── Weekly Progress Rings ──
    rings = f'''<div class="card card-glow">
        <h2>Week {ctx["week_number"]} Progress</h2>
        <div class="rings">
            {_progress_ring(wp["outreach"], 110, 7, "Outreach", f'{wt["outreach"]}/{targets["outreach"]}')}
            {_progress_ring(wp["meetings"], 110, 7, "Meetings", f'{wt["meetings"]}/{targets["meetings"]}')}
            {_progress_ring(wp["videos"], 110, 7, "Videos", f'{wt["videos"]}/{targets["videos"]}')}
            {_progress_ring(wp["content"], 110, 7, "Content", f'{wt["content"]}/{targets["content"]}')}
            {_progress_ring(wp["training"], 110, 7, "Training", f'{wt["training"]}/{targets["training"]}')}
        </div>
    </div>'''

    # ── Weekly Metrics Bars ──
    bars = f'''<div class="card">
        <h2>Weekly Breakdown</h2>
        {_metric_bar("Outreach Messages", wt["outreach"], targets["outreach"], GOLD, "📤")}
        {_metric_bar("Meetings Booked", wt["meetings"], targets["meetings"], BLUE, "🤝")}
        {_metric_bar("Videos Filmed", wt["videos"], targets["videos"], PURPLE, "🎥")}
        {_metric_bar("Content Posted", wt["content"], targets["content"], GREEN, "📱")}
        {_metric_bar("Training Sessions", wt["training"], targets["training"], YELLOW, "🏋️")}
    </div>'''

    # ── 90-Day Goals ──
    goals_html = ""
    for g in data["goals"]:
        color = _pct_color(g["pct"])
        goals_html += f'''<div class="goal-card">
            <div class="goal-icon">{g["icon"]}</div>
            <div class="goal-info">
                <div class="goal-name">{html.escape(str(g["name"]))}</div>
                <div class="goal-progress">{g["current"]:.0f} / {g["target"]}</div>
                <div class="goal-bar"><div class="goal-fill" style="width:{g['pct']}%;background:{color}"></div></div>
            </div>
            <div class="goal-pct" style="color:{color}">{g["pct"]}%</div>
        </div>'''

    goals_section = f'''<div class="card">
        <h2>90-Day Goals</h2>
        {goals_html}
    </div>'''

    # ── Energy & Health ──
    energy_section = f'''<div class="card">
        <h2>Energy & Pain Trend</h2>
        {_energy_chart(data["energy_data"])}
    </div>'''

    # ── Milestones ──
    milestones_html = ""
    achieved_count = sum(1 for m in data["milestones"] if m["achieved"])
    for m in data["milestones"]:
        milestones_html += _milestone_item(m["name"], m["achieved"], m.get("date", ""))
    milestones_section = f'''<div class="card">
        <h2>Milestones ({achieved_count}/{len(data["milestones"])})</h2>
        {milestones_html if milestones_html else '<div style="color:#8b949e;padding:16px;text-align:center">No milestones configured</div>'}
    </div>'''

    # ── Daily Log ──
    log_section = f'''<div class="card">
        <h2>Recent Activity</h2>
        {_daily_log_table(data["daily_log"])}
    </div>'''

    # ── Assemble Layout ──
    content = f'''<div class="container">
        {header}
        {tab_nav}
        {stats}
        {rings}
        <div class="grid grid-2">
            {bars}
            {goals_section}
        </div>
        <div class="grid grid-3">
            {energy_section}
            {milestones_section}
            {log_section}
        </div>
        <footer style="text-align:center;padding:24px;color:{MUTED};font-size:11px;border-top:1px solid {BORDER};margin-top:20px">
            Accountability Engine by <a href="https://marceausolutions.com" style="color:{GOLD};text-decoration:none">Marceau Solutions™</a> — Embrace the Pain &amp; Defy the Odds
            <br>© {datetime.now().year} Marceau Solutions LLC
        </footer>
    </div>'''

    return _shell("Accountability Engine", content)


def render_sprint(tasks_data, outreach_stats, error=None):
    """Sprint Command Center — unified hub for AI client sprint tools."""
    SPRINT_END = "April 5, 2026"
    from datetime import date
    days_left = (date(2026, 4, 5) - date.today()).days

    all_tasks = tasks_data.get("tasks", [])
    today_pending = [t for t in all_tasks if t.get("section") == "today" and t.get("status") == "pending"]
    this_week = [t for t in all_tasks if t.get("section") == "this_week" and t.get("status") == "pending"]
    recently_done = [t for t in all_tasks if t.get("status") == "complete"][-8:]  # last 8
    stats = tasks_data.get("stats", {})

    # ── Tab Nav ──
    nav = f'''<div style="display:flex;gap:0;border-bottom:2px solid {GOLD};margin-bottom:20px">
        <a href="/" style="padding:10px 20px;font-size:13px;font-weight:600;color:{MUTED};text-decoration:none;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .15s" onmouseover="this.style.color='{GOLD}'" onmouseout="this.style.color='{MUTED}'">90-Day Tracker</a>
        <a href="/sprint" style="padding:10px 20px;font-size:13px;font-weight:700;color:{GOLD};text-decoration:none;border-bottom:2px solid {GOLD};margin-bottom:-2px">Sprint Hub</a>
    </div>'''

    # ── Header ──
    header = f'''<div class="header">
        <div>
            <h1>Sprint <span>Command Center</span></h1>
            <div style="font-size:12px;color:{MUTED};margin-top:2px">AI Client Sprint — March 23 to {SPRINT_END}</div>
        </div>
        <div class="header-right">
            <span class="header-badge" style="background:{RED if days_left <= 3 else YELLOW if days_left <= 7 else GOLD};color:{CHARCOAL}">{days_left} days left</span>
            <span class="header-badge" style="background:{SURFACE};color:{GOLD};border:1px solid {GOLD}44">{stats.get("total_completed", 0)}/{stats.get("total_created", 0)} tasks done</span>
            <button class="refresh-btn" onclick="location.reload()">↻ Refresh</button>
        </div>
    </div>'''

    # ── Quick Stats ──
    follow_ups = outreach_stats.get("follow_ups_due", 0)
    top_stats = f'''<div class="stat-grid">
        {_stat_card(outreach_stats.get("total_sent", 0), "Emails Sent", "📤", PURPLE)}
        {_stat_card(follow_ups, "Follow-ups Due", "⚡", RED if follow_ups > 0 else MUTED)}
        {_stat_card(len(today_pending), "Today's Tasks", "📋", GOLD)}
        {_stat_card(stats.get("total_completed", 0), "Completed", "✓", GREEN)}
        {_stat_card(days_left, "Days to April 6", "⏳", BLUE)}
        {_stat_card("(239) 457-0662", "Demo Line", "📞", GOLD)}
    </div>'''

    # ── Today's Tasks ──
    def _task_row(t):
        pri_color = RED if t.get("priority") == "high" else YELLOW if t.get("priority") == "medium" else MUTED
        pri_dot = f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{pri_color};margin-right:6px;flex-shrink:0"></span>'
        tags = " ".join(f'<span style="background:{SURFACE};border:1px solid {BORDER};padding:2px 6px;border-radius:4px;font-size:10px;color:{MUTED}">{html.escape(tag)}</span>' for tag in t.get("tags", [])[:3])
        return f'''<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 12px;background:{SURFACE};border-radius:8px;border:1px solid {BORDER};margin-bottom:6px">
            {pri_dot}
            <div style="flex:1;min-width:0">
                <div style="font-size:13px;font-weight:600">{html.escape(t.get("title",""))}</div>
                <div style="display:flex;gap:4px;margin-top:4px;flex-wrap:wrap">{tags}</div>
            </div>
            <span style="font-size:11px;color:{MUTED};white-space:nowrap">{t.get("project","")}</span>
        </div>'''

    today_html = "".join(_task_row(t) for t in today_pending) or f'<div style="color:{GREEN};text-align:center;padding:16px;font-weight:600">All clear — nothing pending today</div>'
    week_html = "".join(_task_row(t) for t in this_week[:6]) or f'<div style="color:{MUTED};text-align:center;padding:12px">No upcoming tasks</div>'

    tasks_section = f'''<div class="card card-glow">
        <h2>Today — Priority Queue</h2>
        {today_html}
    </div>
    <div class="card">
        <h2>This Week</h2>
        {week_html}
    </div>'''

    # ── Quick Launch ──
    def _launch_btn(label, url, icon, desc=""):
        return f'''<a href="{url}" target="_blank" style="display:block;background:{SURFACE};border:1px solid {BORDER};border-radius:10px;padding:14px;text-decoration:none;color:{TEXT};transition:all .15s" onmouseover="this.style.borderColor='{GOLD}';this.style.boxShadow='0 0 12px {GOLD_GLOW}'" onmouseout="this.style.borderColor='{BORDER}';this.style.boxShadow='none'">
            <div style="font-size:22px;margin-bottom:4px">{icon}</div>
            <div style="font-size:13px;font-weight:700">{html.escape(label)}</div>
            <div style="font-size:10px;color:{MUTED};margin-top:2px">{html.escape(desc)}</div>
        </a>'''

    tools_section = f'''<div class="card">
        <h2>Quick Launch — Sprint Tools</h2>
        <div class="grid grid-5" style="margin-top:4px">
            {_launch_btn("Outreach Analytics", "http://127.0.0.1:8794", "📊", "Volume, response rate, CAC")}
            {_launch_btn("Client Tracker", "http://127.0.0.1:8795", "📈", "Trial client performance")}
            {_launch_btn("Sales Coach", "http://127.0.0.1:8796", "🎯", "Mock call practice")}
            {_launch_btn("Sales Pipeline", "http://127.0.0.1:8788", "💼", "Deals & proposals")}
            {_launch_btn("API Key Manager", "http://127.0.0.1:8793", "🔑", "Key health & rotation")}
        </div>
    </div>'''

    # ── Recently Done ──
    done_html = ""
    for t in reversed(recently_done):
        done_html += f'<div style="display:flex;align-items:center;gap:8px;padding:7px 10px;border-bottom:1px solid {BORDER}22"><span style="color:{GREEN}">✓</span><span style="font-size:12px;flex:1">{html.escape(t.get("title",""))}</span><span style="font-size:10px;color:{MUTED}">{t.get("project","")}</span></div>'

    done_section = f'''<div class="card">
        <h2>Recently Completed</h2>
        {done_html or f'<div style="color:{MUTED};text-align:center;padding:16px">No completed tasks yet</div>'}
    </div>'''

    # ── Session Close ──
    close_section = f'''<div class="card" style="border-color:{GOLD}44">
        <h2>Close Session</h2>
        <p style="font-size:12px;color:{MUTED};margin-bottom:12px">Any prompts raised during the session that weren't addressed? Add them here — they'll be saved to the task list and sent to Clawdbot.</p>
        <textarea id="missed-items" placeholder="- Unaddressed item 1&#10;- Unaddressed item 2" style="width:100%;background:{SURFACE};border:1px solid {BORDER};border-radius:8px;padding:10px;color:{TEXT};font-size:12px;resize:vertical;min-height:80px;font-family:inherit"></textarea>
        <button onclick="closeSession()" style="margin-top:10px;background:{GOLD};color:{CHARCOAL};border:none;padding:10px 24px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer;width:100%">
            Send EOD Summary to Clawdbot
        </button>
        <div id="close-result" style="margin-top:8px;font-size:12px;display:none"></div>
    </div>'''

    close_script = f'''<script>
async function closeSession() {{
    const missed = document.getElementById('missed-items').value;
    const btn = document.querySelector('[onclick="closeSession()"]');
    btn.textContent = 'Sending...';
    btn.disabled = true;
    try {{
        const r = await fetch('/api/sprint-close', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{missed_items: missed}})
        }});
        const d = await r.json();
        const res = document.getElementById('close-result');
        res.style.display = 'block';
        if (d.ok) {{
            res.style.color = '{GREEN}';
            res.textContent = 'EOD summary sent to Clawdbot. Missed items saved to task list.';
            btn.textContent = 'Session Closed ✓';
        }} else {{
            res.style.color = '{RED}';
            res.textContent = 'Error: ' + (d.error || 'Unknown');
            btn.disabled = false;
            btn.textContent = 'Send EOD Summary to Clawdbot';
        }}
    }} catch(e) {{
        document.getElementById('close-result').style.display = 'block';
        document.getElementById('close-result').style.color = '{RED}';
        document.getElementById('close-result').textContent = 'Network error: ' + e.message;
        btn.disabled = false;
        btn.textContent = 'Send EOD Summary to Clawdbot';
    }}
}}
</script>'''

    content = f'''<div class="container">
        {header}
        {nav}
        {top_stats}
        <div class="grid grid-2">
            {tasks_section}
            <div>
                {tools_section}
                {done_section}
                {close_section}
            </div>
        </div>
        {close_script}
        <footer style="text-align:center;padding:24px;color:{MUTED};font-size:11px;border-top:1px solid {BORDER};margin-top:20px">
            Sprint Hub — <a href="/" style="color:{GOLD};text-decoration:none">Back to 90-Day Tracker</a>
            &nbsp;|&nbsp; Demo Line: (239) 457-0662 &nbsp;|&nbsp; Call it → voicemail → text in 10 sec
        </footer>
    </div>'''

    return _shell("Sprint Command Center", content)


def render_landing():
    """Not used for accountability — direct to dashboard."""
    return render_dashboard(None, error="Redirecting...")


def _shell(title, content):
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{html.escape(title)} — Marceau Accountability Engine</title>
<meta name="description" content="90-day execution tracking with real-time metrics, health-aware coaching, and goal visualization.">
<style>{CSS}</style>
</head><body>{content}
<script>
// Auto-refresh every 5 minutes
setTimeout(() => location.reload(), 300000);
</script>
</body></html>"""
