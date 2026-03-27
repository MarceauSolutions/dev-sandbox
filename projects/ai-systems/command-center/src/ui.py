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


def _activity_rings(outreach_count, outreach_target, tasks_today, tasks_done, streak, streak_target=14):
    """Apple Watch-style three concentric activity rings — outreach (gold), tasks (blue), streak (purple)."""
    SIZE = 200
    CX = SIZE / 2
    CY = SIZE / 2

    # Ring specs: (radius, stroke_width, color, pct)
    outreach_pct = min(100, round((outreach_count / outreach_target) * 100)) if outreach_target else 0
    tasks_total = len(tasks_today) if tasks_today else 0
    tasks_pct = min(100, round((tasks_done / tasks_total) * 100)) if tasks_total > 0 else 0
    streak_pct = min(100, round((streak / streak_target) * 100))

    rings = [
        # (radius, stroke, color, pct, label, value_str)
        (88,  10, GOLD,   outreach_pct, "Outreach", f"{outreach_count}/{outreach_target}"),
        (68,  10, BLUE,   tasks_pct,    "Tasks",    f"{tasks_done}/{tasks_total}"),
        (48,  10, PURPLE, streak_pct,   "Streak",   f"{streak}d"),
    ]

    PI = 3.14159
    svg_rings = ""
    for radius, stroke, color, pct, _label, _val in rings:
        circ = 2 * PI * radius
        offset = circ - (pct / 100) * circ
        # Track circle (dim)
        svg_rings += f'<circle cx="{CX}" cy="{CY}" r="{radius}" fill="none" stroke="{color}22" stroke-width="{stroke}"/>'
        # Progress arc
        svg_rings += f'''<circle cx="{CX}" cy="{CY}" r="{radius}" fill="none" stroke="{color}" stroke-width="{stroke}"
            stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}" stroke-linecap="round"
            style="transition:stroke-dashoffset 1.8s cubic-bezier(.4,0,.2,1)"/>'''

    # Labels below rings: three columns
    label_html = ""
    for _radius, _stroke, color, pct, label, val in rings:
        label_html += f'''<div style="text-align:center;flex:1">
            <div style="font-size:18px;font-weight:800;color:{color};line-height:1">{val}</div>
            <div style="font-size:10px;color:{MUTED};margin-top:2px;text-transform:uppercase;letter-spacing:.3px">{label}</div>
            <div style="font-size:9px;color:{color};margin-top:1px">{pct}%</div>
        </div>'''

    return f'''<div style="display:flex;flex-direction:column;align-items:center;gap:12px">
        <div style="position:relative">
            <svg width="{SIZE}" height="{SIZE}" style="transform:rotate(-90deg)">
                {svg_rings}
            </svg>
            <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">
                <div style="text-align:center">
                    <div style="font-size:11px;color:{MUTED};text-transform:uppercase;letter-spacing:.5px">Activity</div>
                    <div style="font-size:28px;font-weight:900;color:{GOLD};line-height:1">{outreach_pct}%</div>
                </div>
            </div>
        </div>
        <div style="display:flex;gap:8px;width:{SIZE}px">
            {label_html}
        </div>
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

.right-now-pulse {{ animation:right-now-border-pulse 2.5s ease-in-out infinite; }}
@keyframes right-now-border-pulse {{
    0%,100% {{ border-color:{GOLD}44;box-shadow:0 0 8px {GOLD}22; }}
    50% {{ border-color:{GOLD}cc;box-shadow:0 0 24px {GOLD}66; }}
}}

.task-done-check {{ animation:check-pop .4s cubic-bezier(.17,.67,.83,.67); }}
@keyframes check-pop {{
    0% {{ transform:scale(0.5);opacity:0; }}
    60% {{ transform:scale(1.3);opacity:1; }}
    100% {{ transform:scale(1);opacity:1; }}
}}

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


def _right_now_card(time_block):
    """RIGHT NOW card — current calendar time block with countdown."""
    if not time_block:
        return ""

    err = time_block.get("error")
    current = time_block.get("current")
    nxt = time_block.get("next")

    if err and not current and not nxt:
        return f'''<div class="card right-now-pulse" style="margin-bottom:16px">
            <h2 style="font-size:16px;font-weight:800;color:{GOLD};letter-spacing:.5px">RIGHT NOW</h2>
            <span style="color:{MUTED};font-size:13px">Calendar unavailable — {html.escape(str(err))}</span>
        </div>'''

    current_html = ""
    next_html = ""

    if current:
        mins = current["mins_left"]
        hrs = mins // 60
        mins_rem = mins % 60
        time_str = f"{hrs}h {mins_rem}m left" if hrs > 0 else f"{mins_rem}m left"
        urgency_color = RED if mins <= 10 else YELLOW if mins <= 20 else GOLD
        current_html = f'''<div style="display:flex;align-items:center;gap:14px;padding:16px 18px;background:linear-gradient(135deg,{GOLD}22,{GOLD}08);border:1px solid {GOLD}55;border-radius:12px">
            <div style="width:12px;height:12px;border-radius:50%;background:{urgency_color};flex-shrink:0;box-shadow:0 0 12px {urgency_color}aa" class="pulse"></div>
            <div style="flex:1">
                <div style="font-size:19px;font-weight:800;color:{GOLD}">{html.escape(current["title"])}</div>
                <div style="font-size:12px;color:{MUTED};margin-top:3px">{current["start"]} – {current["end"]}</div>
            </div>
            <div style="text-align:right;flex-shrink:0">
                <div style="font-size:26px;font-weight:900;color:{urgency_color};line-height:1">{time_str}</div>
                <div style="font-size:10px;color:{MUTED};margin-top:2px;text-transform:uppercase;letter-spacing:.3px">remaining</div>
            </div>
        </div>'''
    else:
        current_html = f'<div style="padding:12px 16px;color:{MUTED};font-size:14px;font-style:italic">No active time block right now</div>'

    if nxt:
        mins_until = nxt.get("mins_until")
        if mins_until is not None:
            eta = f"in {mins_until}m" if mins_until < 60 else f"in {mins_until//60}h {mins_until%60}m"
            next_html = f'<div style="margin-top:10px;padding:10px 14px;background:{SURFACE};border-radius:8px;font-size:13px;color:{MUTED}">Up next: <strong style="color:{TEXT}">{html.escape(nxt["title"])}</strong> at {nxt["start"]} <span style="color:{BLUE}">({eta})</span></div>'
        else:
            next_html = f'<div style="margin-top:10px;padding:10px 14px;background:{SURFACE};border-radius:8px;font-size:13px;color:{MUTED}">Up next: <strong style="color:{TEXT}">{html.escape(nxt["title"])}</strong> at {nxt["start"]}</div>'

    return f'''<div class="card right-now-pulse" style="margin-bottom:16px">
        <h2 style="font-size:16px;font-weight:800;color:{GOLD};letter-spacing:.5px;margin-bottom:10px">RIGHT NOW</h2>
        {current_html}
        {next_html}
    </div>'''


def _tasks_section(tasks):
    """Today + this_week tasks from tasks.json for the main dashboard."""
    today_tasks = tasks.get("today", [])
    week_tasks = tasks.get("this_week", [])

    if not today_tasks and not week_tasks:
        return ""

    def _task_row(t):
        is_done = t.get("status") == "complete"
        pri = t.get("priority", "medium")
        pri_color = RED if pri == "high" else YELLOW if pri == "medium" else MUTED
        title_style = f"text-decoration:line-through;color:{MUTED}" if is_done else "font-weight:600"
        due = ""
        if t.get("due_date"):
            try:
                due_dt = datetime.fromisoformat(t["due_date"].replace("Z", "+00:00"))
                due = f'<span style="font-size:10px;color:{MUTED}">{due_dt.strftime("%-I:%M %p")}</span>'
            except Exception:
                pass
        status_icon = f'<span class="task-done-check" style="color:{GOLD};font-size:16px;font-weight:900;line-height:1">✓</span>' if is_done else f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{pri_color};flex-shrink:0"></span>'
        return f'''<div style="display:flex;align-items:flex-start;gap:8px;padding:7px 10px;border-bottom:1px solid {BORDER}22;{'opacity:0.5' if is_done else ''}">
            <div style="margin-top:2px;flex-shrink:0">{status_icon}</div>
            <div style="flex:1;min-width:0">
                <span style="font-size:13px;{title_style}">{html.escape(t.get("title",""))}</span>
                {due}
            </div>
        </div>'''

    today_html = "".join(_task_row(t) for t in today_tasks) or f'<div style="color:{GREEN};text-align:center;padding:12px;font-size:13px">All clear today</div>'
    week_html = "".join(_task_row(t) for t in week_tasks[:6]) or f'<div style="color:{MUTED};text-align:center;padding:8px;font-size:12px">No upcoming tasks</div>'

    pending_today = sum(1 for t in today_tasks if t.get("status") != "complete")
    pending_week = sum(1 for t in week_tasks if t.get("status") != "complete")

    return f'''<div class="card" style="border-color:{GOLD}44">
        <h2>Today's Tasks <span style="color:{GOLD};font-weight:700">{pending_today} pending</span></h2>
        {today_html}
        <div style="margin-top:12px;padding-top:10px;border-top:1px solid {BORDER}">
            <div style="font-size:11px;font-weight:600;color:{MUTED};text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px">This Week ({pending_week} pending)</div>
            {week_html}
        </div>
        <div style="margin-top:8px;text-align:right">
            <a href="/sprint" style="font-size:11px;color:{GOLD};text-decoration:none">Full Sprint Hub →</a>
        </div>
    </div>'''


def _outreach_log_section(emails):
    """Today's cold outreach log for the main dashboard."""
    if not emails:
        return f'''<div class="card">
            <h2>Today's Outreach Log</h2>
            <div style="color:{MUTED};text-align:center;padding:16px;font-size:13px">No outreach emails sent today yet</div>
        </div>'''

    rows = ""
    for e in emails:
        sent_time = ""
        try:
            dt = datetime.fromisoformat(e["sent_at"].replace("Z", "+00:00"))
            sent_time = dt.strftime("%-I:%M %p")
        except Exception:
            pass
        stage = e.get("pipeline_stage", "")
        stage_html = f'<span style="background:{BLUE}22;color:{BLUE};padding:1px 6px;border-radius:8px;font-size:10px">{html.escape(stage)}</span>' if stage else ""
        rows += f'''<tr>
            <td style="font-weight:600;font-size:12px">{html.escape(e.get("first_name",""))} / {html.escape(e.get("company",""))}</td>
            <td style="font-size:11px;color:{MUTED}">{html.escape(e.get("industry","—"))}</td>
            <td style="font-size:11px;color:{MUTED}">{html.escape(e.get("subject",""))}</td>
            <td style="font-size:11px;color:{MUTED}">{sent_time}</td>
            <td>{stage_html}</td>
        </tr>'''

    return f'''<div class="card">
        <h2>Today's Outreach — {len(emails)} sent</h2>
        <div style="overflow-x:auto">
        <table style="margin-top:4px;font-size:12px">
            <thead><tr>
                <th>Contact / Company</th><th>Industry</th><th>Subject</th><th>Sent</th><th>Stage</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>
        </div>
    </div>'''


def render_dashboard(data, error=None, time_block=None):
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
        <a href="/outreach" style="padding:10px 20px;font-size:13px;font-weight:600;color:{MUTED};text-decoration:none;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .15s" onmouseover="this.style.color='{GOLD}'" onmouseout="this.style.color='{MUTED}'">Cold Outreach</a>
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

    # ── Sprint countdown ──
    from datetime import date as _date
    _sprint_end = _date(2026, 4, 5)
    _sprint_days_left = max(0, (_sprint_end - _date.today()).days)
    _sprint_color = RED if _sprint_days_left <= 3 else YELLOW if _sprint_days_left <= 7 else GOLD
    sprint_countdown = f'''<div style="background:linear-gradient(135deg,{_sprint_color}18,{_sprint_color}08);border:1px solid {_sprint_color}44;border-radius:12px;padding:14px 20px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between">
        <div>
            <div style="font-size:11px;color:{MUTED};text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px">AI Client Sprint</div>
            <div style="font-size:15px;font-weight:700;color:{TEXT}">Ends April 5, 2026</div>
        </div>
        <div style="text-align:right">
            <div style="font-size:42px;font-weight:900;color:{_sprint_color};line-height:1">{_sprint_days_left}</div>
            <div style="font-size:11px;color:{MUTED};text-transform:uppercase;letter-spacing:.3px">days left</div>
        </div>
    </div>'''

    # ── Activity Rings (Apple Watch style — concentric) ──
    tasks_obj = data.get("tasks", {})
    _today_tasks = tasks_obj.get("today", [])
    _tasks_done = sum(1 for t in _today_tasks if t.get("status") == "complete")
    _today_outreach = wt.get("outreach", 0)
    activity_rings_html = _activity_rings(
        outreach_count=_today_outreach,
        outreach_target=100,  # Daily target
        tasks_today=_today_tasks,
        tasks_done=_tasks_done,
        streak=data["streak"],
        streak_target=14,
    )
    rings_top = f'''<div class="card card-glow" style="margin-bottom:16px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
            <div>
                <h2 style="margin-bottom:4px">Today's Activity</h2>
                <div style="font-size:11px;color:{MUTED}">Outreach · Tasks · Streak — close all three rings</div>
            </div>
            <div style="font-size:10px;color:{MUTED};text-align:right">
                <div><span style="color:{GOLD}">■</span> Outreach (100/day)</div>
                <div style="margin-top:2px"><span style="color:{BLUE}">■</span> Tasks done today</div>
                <div style="margin-top:2px"><span style="color:{PURPLE}">■</span> Sprint streak (14-day)</div>
            </div>
        </div>
        <div style="display:flex;align-items:center;justify-content:center;gap:40px;flex-wrap:wrap">
            {activity_rings_html}
            <div style="flex:1;min-width:200px;max-width:320px">
                {_metric_bar("Daily Outreach", _today_outreach, 100, GOLD, "📤")}
                {_metric_bar("Tasks Done Today", _tasks_done, max(len(_today_tasks),1), BLUE, "✓")}
                {_metric_bar("Sprint Streak", data["streak"], 14, PURPLE, "🔥")}
            </div>
        </div>
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

    # ── Sheets status notice ──
    sheets_notice = ""
    if not data.get("sheets_ok"):
        sheets_notice = f'''<div style="background:{YELLOW}18;border:1px solid {YELLOW}44;border-radius:8px;padding:10px 14px;margin-bottom:12px;font-size:12px;color:{YELLOW}">
            ⚠ Sheets disconnected — showing local data. Outreach count pulled from tracking files.
        </div>'''

    # ── Tasks from tasks.json ──
    tasks_card = _tasks_section(data.get("tasks", {}))

    # ── Today's outreach log ──
    outreach_log_card = _outreach_log_section(data.get("outreach_log", []))

    # ── RIGHT NOW time block ──
    right_now = _right_now_card(time_block)

    # ── Assemble Layout ──
    content = f'''<div class="container">
        {header}
        {tab_nav}
        {sheets_notice}
        {sprint_countdown}
        {right_now}
        {rings_top}
        {stats}
        {rings}
        <div class="grid grid-2">
            {bars}
            {goals_section}
        </div>
        <div class="grid grid-2">
            {tasks_card}
            {outreach_log_card}
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
        <a href="/outreach" style="padding:10px 20px;font-size:13px;font-weight:600;color:{MUTED};text-decoration:none;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .15s" onmouseover="this.style.color='{GOLD}'" onmouseout="this.style.color='{MUTED}'">Cold Outreach</a>
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
        {_stat_card("(855) 239-9364", "Demo Line", "📞", GOLD)}
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
    def _launch_btn(label, url, icon, desc="", badge=""):
        badge_html = f'<span style="position:absolute;top:8px;right:8px;background:{RED};color:white;font-size:9px;font-weight:700;padding:1px 5px;border-radius:8px">{badge}</span>' if badge else ""
        return f'''<a href="{url}" target="_blank" style="display:block;position:relative;background:{SURFACE};border:1px solid {BORDER};border-radius:10px;padding:14px;text-decoration:none;color:{TEXT};transition:all .15s" onmouseover="this.style.borderColor='{GOLD}';this.style.boxShadow='0 0 12px {GOLD_GLOW}'" onmouseout="this.style.borderColor='{BORDER}';this.style.boxShadow='none'">
            {badge_html}
            <div style="font-size:22px;margin-bottom:4px">{icon}</div>
            <div style="font-size:13px;font-weight:700">{html.escape(label)}</div>
            <div style="font-size:10px;color:{MUTED};margin-top:2px">{html.escape(desc)}</div>
        </a>'''

    follow_ups_due = outreach_stats.get("follow_ups_due", 0)
    tools_section = f'''<div class="card">
        <h2>Quick Launch — Sprint Tools</h2>
        <div class="grid grid-5" style="margin-top:4px">
            {_launch_btn("Sales Pipeline", "http://127.0.0.1:8785", "💼", "Deals, kanban, proposals")}
            {_launch_btn("Outreach Analytics", "http://127.0.0.1:8794", "📊", "Sent / reply rate / funnel")}
            {_launch_btn("Cold Outreach", "http://localhost:8780/sprint", "📤", "Sprint hub outreach view", str(follow_ups_due) if follow_ups_due > 0 else "")}
            {_launch_btn("ClaimBack", "http://127.0.0.1:8790", "🏥", "Medical billing disputes")}
            {_launch_btn("API Key Manager", "http://127.0.0.1:8793", "🔑", "API key health & rotation")}
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
            &nbsp;|&nbsp; Demo Line: (855) 239-9364 &nbsp;|&nbsp; AI receptionist + missed-call text-back
        </footer>
    </div>'''

    return _shell("Sprint Command Center", content)


def render_outreach(records, error=None):
    """Cold outreach pipeline feed — 91 batch leads + follow-up sequence status."""
    from datetime import datetime, date

    TOUCH_NAMES = {
        0: ("Day 3", "Check-in", YELLOW),
        1: ("Day 7", "Social Proof", BLUE),
        2: ("Day 14", "Direct Question", PURPLE),
        3: ("Day 21", "Breakup", RED),
    }
    TOUCH_DAYS = {0: 3, 1: 7, 2: 14, 3: 21}

    today = date.today()

    # Nav
    nav = f'''<div style="display:flex;gap:0;border-bottom:2px solid {GOLD};margin-bottom:20px">
        <a href="/" style="padding:10px 20px;font-size:13px;font-weight:600;color:{MUTED};text-decoration:none;border-bottom:2px solid transparent;margin-bottom:-2px" onmouseover="this.style.color='{GOLD}'" onmouseout="this.style.color='{MUTED}'">90-Day Tracker</a>
        <a href="/sprint" style="padding:10px 20px;font-size:13px;font-weight:600;color:{MUTED};text-decoration:none;border-bottom:2px solid transparent;margin-bottom:-2px" onmouseover="this.style.color='{GOLD}'" onmouseout="this.style.color='{MUTED}'">Sprint Hub</a>
        <a href="/outreach" style="padding:10px 20px;font-size:13px;font-weight:700;color:{GOLD};text-decoration:none;border-bottom:2px solid {GOLD};margin-bottom:-2px">Cold Outreach</a>
    </div>'''

    # Header
    header = f'''<div class="header">
        <div>
            <h1>Cold Outreach <span>Pipeline</span></h1>
            <div style="font-size:12px;color:{MUTED};margin-top:2px">Batch send March 23 — 4-touch Hormozi sequence (Day 3 / 7 / 14 / 21)</div>
        </div>
        <div class="header-right">
            <button class="refresh-btn" onclick="location.reload()">↻ Refresh</button>
        </div>
    </div>'''

    if error:
        content = f'''<div class="container">{header}{nav}
            <div class="card" style="text-align:center;padding:40px">
                <h3 style="color:{RED}">Error loading outreach data</h3>
                <p style="color:{MUTED};margin-top:8px">{html.escape(str(error))}</p>
            </div></div>'''
        return _shell("Cold Outreach Pipeline", content)

    # Build enriched records
    sent_records = [r for r in records if r.get("status") == "sent"]
    pending_records = [r for r in records if r.get("status") == "pending"]

    due_count = 0
    rows_html = ""
    stage_counts = {"Day 3": 0, "Day 7": 0, "Day 14": 0, "Day 21": 0, "Done": 0, "Replied": 0}

    for r in sent_records:
        sent_str = r.get("sent_at", "")
        fc = r.get("follow_up_count", 0)
        biz = html.escape(r.get("business_name", "—")[:40])
        email = html.escape(r.get("email", "—"))
        template = html.escape(r.get("template_used", "—"))
        status = r.get("status", "sent")

        if status == "replied":
            stage_label = "Replied"
            stage_color = GREEN
            next_due_html = f'<span style="color:{GREEN};font-weight:700">Replied ✓</span>'
            stage_counts["Replied"] += 1
        elif fc >= 4:
            stage_label = "Complete"
            stage_color = MUTED
            next_due_html = f'<span style="color:{MUTED}">Sequence done</span>'
            stage_counts["Done"] += 1
        else:
            touch_name, touch_type, touch_color = TOUCH_NAMES[fc]
            stage_label = touch_name
            stage_color = touch_color

            if sent_str:
                try:
                    sent_dt = datetime.fromisoformat(sent_str).date()
                    days_since = (today - sent_dt).days
                    days_needed = TOUCH_DAYS[fc]
                    days_left = days_needed - days_since
                    if days_left <= 0:
                        due_count += 1
                        next_due_html = f'<span style="color:{RED};font-weight:700">DUE NOW — {touch_type}</span>'
                    elif days_left == 1:
                        next_due_html = f'<span style="color:{YELLOW}">Tomorrow — {touch_type}</span>'
                    else:
                        next_due_html = f'<span style="color:{MUTED}">in {days_left}d — {touch_type}</span>'
                except Exception:
                    next_due_html = f'<span style="color:{MUTED}">—</span>'
            else:
                next_due_html = f'<span style="color:{MUTED}">—</span>'

            if touch_name in stage_counts:
                stage_counts[touch_name] += 1

        rows_html += f'''<tr>
            <td style="font-weight:600">{biz}</td>
            <td style="color:{MUTED};font-size:12px">{email}</td>
            <td><span style="background:{stage_color}22;color:{stage_color};padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600">{stage_label}</span></td>
            <td style="font-size:11px">{fc}/4</td>
            <td>{next_due_html}</td>
            <td style="color:{MUTED};font-size:11px">{html.escape(template)}</td>
        </tr>'''

    # Stats bar
    total_sent = len(sent_records)
    replied = stage_counts["Replied"]
    reply_rate = round(replied / total_sent * 100, 1) if total_sent else 0
    stats = f'''<div class="stat-grid">
        {_stat_card(total_sent, "Emails Sent", "📤", PURPLE)}
        {_stat_card(due_count, "Follow-ups Due", "⚡", RED if due_count > 0 else MUTED)}
        {_stat_card(replied, "Replies", "💬", GREEN)}
        {_stat_card(f'{reply_rate}%', "Reply Rate", "📊", GOLD)}
        {_stat_card(stage_counts["Day 3"], "At Day 3", "1️⃣", YELLOW)}
        {_stat_card(stage_counts["Day 7"], "At Day 7", "2️⃣", BLUE)}
        {_stat_card(stage_counts["Day 14"], "At Day 14", "3️⃣", PURPLE)}
        {_stat_card(stage_counts["Day 21"], "At Day 21", "4️⃣", RED)}
    </div>'''

    # Table
    table = f'''<div class="card" style="overflow-x:auto">
        <h2>All Sent Leads — Follow-up Status</h2>
        <table style="margin-top:8px">
            <thead><tr>
                <th>Business</th><th>Email</th><th>Stage</th><th>Touches</th><th>Next Due</th><th>Template</th>
            </tr></thead>
            <tbody>
                {rows_html if rows_html else f'<tr><td colspan="6" style="text-align:center;color:{MUTED};padding:20px">No sent records found.</td></tr>'}
            </tbody>
        </table>
    </div>'''

    # Pending note
    pending_note = ""
    if pending_records:
        pending_note = f'<div class="card" style="border-color:{YELLOW}44"><p style="font-size:12px;color:{MUTED}"><strong style="color:{YELLOW}">Note:</strong> {len(pending_records)} records in "pending" state (generated but not sent — likely filtered leads). They are excluded from this view.</p></div>'

    # Automation status note
    auto_note = f'''<div class="card" style="border-color:{GOLD}44">
        <h2>Automation Status</h2>
        <p style="font-size:12px;color:{MUTED}">Follow-up emails fire automatically every day at <strong style="color:{GOLD}">9:00am</strong> via Mac launchd (<code style="background:{SURFACE};padding:2px 6px;border-radius:4px">com.marceausolutions.cold-email-followup</code>).
        No action needed — the system checks for due touches and sends them.
        Logs: <code style="background:{SURFACE};padding:2px 6px;border-radius:4px">projects/lead-generation/logs/daily-loop.log</code></p>
        <div style="margin-top:8px;font-size:12px;color:{MUTED}">
            Touch sequence: Day 3 (soft check-in) → Day 7 (social proof / HVAC case study) → Day 14 (wrong inbox?) → Day 21 (breakup / close the file)
        </div>
    </div>'''

    content = f'''<div class="container">
        {header}
        {nav}
        {stats}
        {pending_note}
        {auto_note}
        {table}
        <footer style="text-align:center;padding:24px;color:{MUTED};font-size:11px;border-top:1px solid {BORDER};margin-top:20px">
            Cold Outreach Pipeline — <a href="/sprint" style="color:{GOLD};text-decoration:none">Back to Sprint Hub</a>
        </footer>
    </div>'''

    return _shell("Cold Outreach Pipeline", content)


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
