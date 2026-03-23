"""
Outreach Analytics Dashboard — AI Client Sprint (March–April 2026)
Port 8794 | Dark + Gold theme | Auto-refresh 30s
"""

import json
import os
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict

from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE = Path(__file__).parent
LEAD_SCRAPER_OUTPUT = BASE.parent / "lead-scraper" / "output"
PIPELINE_DB = BASE.parent / "sales-pipeline" / "data" / "pipeline.db"


# ─── Data Loaders ─────────────────────────────────────────────────────────────

def load_tracking_files():
    """Load all outreach_tracking_*.json files and return merged email list."""
    emails = []
    pattern = "outreach_tracking_*.json"
    for f in sorted(LEAD_SCRAPER_OUTPUT.glob(pattern)):
        try:
            data = json.loads(f.read_text())
            for em in data.get("emails", []):
                em["_source_file"] = f.name
                em["_campaign"] = data.get("campaign", "unknown")
                em["_date"] = data.get("date", f.stem.replace("outreach_tracking_", ""))
                emails.append(em)
        except Exception:
            pass
    return emails


def load_outreach_queue():
    """Load outreach_queue.json for follow-up sequence data."""
    path = LEAD_SCRAPER_OUTPUT / "outreach_queue.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data.get("queue", [])
    except Exception:
        return []


def load_campaigns():
    """Load all campaign JSON files from campaigns/ subdirectory."""
    campaigns = []
    cdir = LEAD_SCRAPER_OUTPUT / "campaigns"
    if cdir.exists():
        for f in cdir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                campaigns.append(data)
            except Exception:
                pass
    return campaigns


def load_template_stats():
    """Load template_stats.json if it exists."""
    path = LEAD_SCRAPER_OUTPUT / "template_stats.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {}


def load_pipeline_db():
    """Load deals from sales-pipeline SQLite if it exists."""
    if not PIPELINE_DB.exists():
        return {}
    try:
        conn = sqlite3.connect(str(PIPELINE_DB))
        conn.row_factory = sqlite3.Row
        stages = ["Intake", "Qualified", "Meeting Booked", "Proposal Sent", "Negotiation", "Closed Won", "Closed Lost"]
        stage_counts = {s: 0 for s in stages}
        for row in conn.execute("SELECT stage, COUNT(*) as c FROM deals GROUP BY stage"):
            stage_counts[row["stage"]] = row["c"]
        won_revenue = conn.execute(
            "SELECT COALESCE(SUM(setup_fee + monthly_fee*12),0) FROM deals WHERE stage='Closed Won'"
        ).fetchone()[0]
        conn.close()
        return {"stage_counts": stage_counts, "won_revenue": won_revenue}
    except Exception:
        return {}


# ─── Analytics Engine ─────────────────────────────────────────────────────────

def compute_stats():
    emails = load_tracking_files()
    queue = load_outreach_queue()
    campaigns = load_campaigns()
    template_stats = load_template_stats()
    pipeline = load_pipeline_db()

    today_str = date.today().isoformat()

    # ── Email totals
    total_sent = len(emails)
    today_sent = sum(1 for e in emails if e.get("_date") == today_str)

    # ── Reply tracking (from pipeline DB outreach_log or template_stats)
    # Build template performance from campaign data
    template_perf = {}
    for camp in campaigns:
        templates = camp.get("templates", {})
        for tid, tdata in templates.items():
            if not isinstance(tdata, dict):
                continue
            if tid not in template_perf:
                template_perf[tid] = {
                    "name": tdata.get("template_id", tid),
                    "sent": 0, "replies": 0,
                    "pain_point": tdata.get("pain_point", ""),
                    "strategy": tdata.get("strategy", tdata.get("compliance", "")),
                }

    # Merge any external template_stats
    for tid, ts in template_stats.items():
        if tid not in template_perf:
            template_perf[tid] = {"name": tid, "sent": 0, "replies": 0, "pain_point": "", "strategy": ""}
        template_perf[tid]["sent"] += ts.get("sent", 0)
        template_perf[tid]["replies"] += ts.get("replies", 0)

    # ── Follow-up sequence buckets from queue
    # Queue items have scheduled_time; derive "day" by comparing to campaign first send
    # Approximate: group by scheduled day offset relative to first queue item per business
    day_buckets = {"Day 0": 0, "Day 3": 0, "Day 7": 0, "Day 10": 0, "Pending": 0}
    campaign_first = {}  # business_id → earliest sent_at
    for item in queue:
        if item.get("status") == "sent":
            bid = item.get("business_id", "")
            sent = item.get("sent_at", item.get("scheduled_time", ""))
            if bid not in campaign_first or sent < campaign_first[bid]:
                campaign_first[bid] = sent

    for item in queue:
        if item.get("status") != "sent":
            day_buckets["Pending"] += 1
            continue
        bid = item.get("business_id", "")
        sent_str = item.get("sent_at", item.get("scheduled_time", ""))
        first_str = campaign_first.get(bid, sent_str)
        try:
            sent_dt = datetime.fromisoformat(sent_str.replace("Z", "+00:00"))
            first_dt = datetime.fromisoformat(first_str.replace("Z", "+00:00"))
            delta = (sent_dt - first_dt).days
        except Exception:
            delta = 0
        if delta <= 1:
            day_buckets["Day 0"] += item.get("count", 1)
        elif delta <= 4:
            day_buckets["Day 3"] += item.get("count", 1)
        elif delta <= 8:
            day_buckets["Day 7"] += item.get("count", 1)
        else:
            day_buckets["Day 10"] += item.get("count", 1)

    # ── Pipeline funnel from DB
    db_stages = pipeline.get("stage_counts", {})
    funnel = {
        "Sent": total_sent,
        "Replied": db_stages.get("Intake", 0) + db_stages.get("Qualified", 0),
        "Call Booked": db_stages.get("Meeting Booked", 0),
        "Proposal": db_stages.get("Proposal Sent", 0) + db_stages.get("Negotiation", 0),
        "Closed": db_stages.get("Closed Won", 0),
    }

    # ── Response rate
    total_replies = funnel["Replied"] + funnel["Call Booked"] + funnel["Proposal"] + funnel["Closed"]
    response_rate = round(total_replies / max(total_sent, 1) * 100, 1)

    # ── Cost per acquisition (Apollo credits)
    # No direct Apollo credit file found; estimate from campaign budgets
    total_budget_spent = 0
    for camp in campaigns:
        budget = camp.get("budget", {})
        stats = camp.get("stats", {})
        sent_count = stats.get("sent", 0)
        cpm = budget.get("sms_cost_per_message", 0.0079)
        total_budget_spent += sent_count * cpm
    clients_signed = funnel["Closed"]
    cpa = round(total_budget_spent / max(clients_signed, 1), 2)

    # ── Daily trend: emails sent per day (last 14 days)
    daily_counts = defaultdict(int)
    for e in emails:
        d = e.get("_date", "")
        if d:
            daily_counts[d] += 1

    today_date = date.today()
    trend_days = []
    for i in range(13, -1, -1):
        d = (today_date - timedelta(days=i)).isoformat()
        trend_days.append({"date": d, "label": d[5:], "count": daily_counts.get(d, 0)})

    # ── Template performance table (compute rate)
    for tid in template_perf:
        s = template_perf[tid]["sent"]
        r = template_perf[tid]["replies"]
        template_perf[tid]["rate"] = round(r / max(s, 1) * 100, 1) if s > 0 else 0

    return {
        "total_sent": total_sent,
        "today_sent": today_sent,
        "response_rate": response_rate,
        "total_replies": total_replies,
        "day_buckets": day_buckets,
        "template_perf": list(template_perf.values()),
        "funnel": funnel,
        "cpa": cpa,
        "budget_spent": round(total_budget_spent, 2),
        "clients_signed": clients_signed,
        "won_revenue": pipeline.get("won_revenue", 0),
        "trend_days": trend_days,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ─── Template ─────────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Outreach Analytics — Marceau Solutions</title>
<style>
  :root {
    --gold: #C9963C;
    --gold-light: #e8b86d;
    --charcoal: #333333;
    --bg: #1a1a1a;
    --card: #242424;
    --card2: #2c2c2c;
    --border: #3a3a3a;
    --text: #e8e8e8;
    --muted: #888;
    --green: #3fb950;
    --red: #f85149;
    --blue: #58a6ff;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; min-height: 100vh; }

  /* Header */
  .header {
    background: var(--card);
    border-bottom: 2px solid var(--gold);
    padding: 16px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .header-brand { display: flex; align-items: center; gap: 12px; }
  .header-logo { width: 36px; height: 36px; background: var(--gold); border-radius: 6px;
    display: flex; align-items: center; justify-content: center; font-weight: 900; color: #000; font-size: 18px; }
  .header h1 { font-size: 20px; font-weight: 700; color: var(--gold); }
  .header-sub { font-size: 12px; color: var(--muted); margin-top: 2px; }
  .header-meta { text-align: right; font-size: 12px; color: var(--muted); }
  .sprint-badge {
    display: inline-block; background: var(--gold); color: #000;
    font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px; margin-top: 4px;
  }

  /* Layout */
  .main { padding: 24px 32px; max-width: 1400px; }

  /* Stat cards */
  .stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .stat-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    position: relative;
    overflow: hidden;
  }
  .stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--gold);
  }
  .stat-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
  .stat-value { font-size: 36px; font-weight: 800; color: var(--gold); line-height: 1; }
  .stat-sub { font-size: 12px; color: var(--muted); margin-top: 6px; }
  .stat-card.green::before { background: var(--green); }
  .stat-card.green .stat-value { color: var(--green); }
  .stat-card.blue::before { background: var(--blue); }
  .stat-card.blue .stat-value { color: var(--blue); }

  /* Grid panels */
  .panels { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
  .panel-wide { grid-column: 1 / -1; }
  @media (max-width: 900px) { .panels { grid-template-columns: 1fr; } .panel-wide { grid-column: 1; } }

  .panel {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
  }
  .panel-title {
    font-size: 13px; font-weight: 700; color: var(--gold);
    text-transform: uppercase; letter-spacing: 0.8px;
    margin-bottom: 16px; padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
  }

  /* Funnel */
  .funnel { display: flex; flex-direction: column; gap: 8px; }
  .funnel-row { display: flex; align-items: center; gap: 12px; }
  .funnel-label { width: 110px; font-size: 13px; color: var(--muted); flex-shrink: 0; }
  .funnel-bar-wrap { flex: 1; background: var(--card2); border-radius: 4px; height: 28px; overflow: hidden; }
  .funnel-bar { height: 100%; background: var(--gold); border-radius: 4px; transition: width 0.5s ease; display: flex; align-items: center; padding-left: 8px; min-width: 28px; }
  .funnel-count { font-size: 13px; font-weight: 700; color: #000; }
  .funnel-pct { width: 44px; text-align: right; font-size: 12px; color: var(--muted); flex-shrink: 0; }

  /* Day buckets */
  .bucket-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 10px; }
  .bucket-card {
    background: var(--card2); border: 1px solid var(--border); border-radius: 8px;
    padding: 14px; text-align: center;
  }
  .bucket-day { font-size: 11px; color: var(--muted); text-transform: uppercase; margin-bottom: 6px; }
  .bucket-count { font-size: 28px; font-weight: 800; color: var(--gold); }

  /* Template table */
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th { text-align: left; padding: 8px 10px; font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.6px; border-bottom: 1px solid var(--border); }
  tbody tr { border-bottom: 1px solid var(--border); }
  tbody tr:last-child { border-bottom: none; }
  tbody td { padding: 10px; color: var(--text); vertical-align: top; }
  .rate-badge {
    display: inline-block; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 12px;
    background: var(--card2); color: var(--muted);
  }
  .rate-badge.good { background: rgba(63,185,80,0.15); color: var(--green); }
  .rate-badge.great { background: rgba(201,150,60,0.2); color: var(--gold); }

  /* Trend chart */
  .trend { display: flex; align-items: flex-end; gap: 4px; height: 100px; }
  .trend-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
  .trend-bar-wrap { flex: 1; width: 100%; display: flex; align-items: flex-end; }
  .trend-bar { width: 100%; background: var(--gold); border-radius: 3px 3px 0 0; min-height: 2px; transition: height 0.4s ease; }
  .trend-bar.today { background: var(--gold-light); box-shadow: 0 0 8px rgba(201,150,60,0.5); }
  .trend-label { font-size: 9px; color: var(--muted); white-space: nowrap; }
  .trend-num { font-size: 10px; color: var(--text); font-weight: 700; }

  /* Budget row */
  .budget-row { display: flex; gap: 20px; flex-wrap: wrap; margin-top: 10px; }
  .budget-item { background: var(--card2); border-radius: 8px; padding: 12px 16px; flex: 1; min-width: 120px; }
  .budget-item-label { font-size: 11px; color: var(--muted); margin-bottom: 4px; }
  .budget-item-val { font-size: 20px; font-weight: 700; color: var(--gold); }

  /* Footer */
  .footer { padding: 16px 32px; font-size: 11px; color: var(--muted); border-top: 1px solid var(--border); margin-top: 24px; display: flex; justify-content: space-between; }
  .dot { display: inline-block; width: 8px; height: 8px; background: var(--green); border-radius: 50%; margin-right: 6px; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
</style>
</head>
<body>

<div class="header">
  <div class="header-brand">
    <div class="header-logo">M</div>
    <div>
      <div class="header h1" style="font-size:20px;font-weight:700;color:#C9963C;">Outreach Analytics</div>
      <div class="header-sub">Marceau Solutions — AI Client Sprint</div>
    </div>
  </div>
  <div class="header-meta">
    <div>Last updated: {{ stats.last_updated }}</div>
    <span class="sprint-badge">Sprint: Mar 23 → Apr 5, 2026</span>
  </div>
</div>

<div class="main">

  <!-- KPI Cards -->
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-label">Total Emails Sent</div>
      <div class="stat-value">{{ stats.total_sent }}</div>
      <div class="stat-sub">{{ stats.today_sent }} sent today</div>
    </div>
    <div class="stat-card blue">
      <div class="stat-label">Replies / Response Rate</div>
      <div class="stat-value">{{ stats.response_rate }}%</div>
      <div class="stat-sub">{{ stats.total_replies }} total replies</div>
    </div>
    <div class="stat-card green">
      <div class="stat-label">Clients Signed</div>
      <div class="stat-value">{{ stats.clients_signed }}</div>
      <div class="stat-sub">${{ "%.0f"|format(stats.won_revenue) }} won revenue</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Cost Per Acquisition</div>
      <div class="stat-value">${{ stats.cpa }}</div>
      <div class="stat-sub">${{ stats.budget_spent }} total spent</div>
    </div>
  </div>

  <!-- Trend + Funnel -->
  <div class="panels">

    <!-- 14-day trend -->
    <div class="panel">
      <div class="panel-title">14-Day Send Trend</div>
      {% set max_count = stats.trend_days | map(attribute='count') | max %}
      {% set max_h = [max_count, 1] | max %}
      <div class="trend">
        {% for day in stats.trend_days %}
        <div class="trend-col">
          <div class="trend-num">{% if day.count > 0 %}{{ day.count }}{% endif %}</div>
          <div class="trend-bar-wrap">
            <div class="trend-bar {% if loop.last %}today{% endif %}"
              style="height: {{ (day.count / max_h * 90) | round | int }}px;"></div>
          </div>
          <div class="trend-label">{{ day.label }}</div>
        </div>
        {% endfor %}
      </div>
    </div>

    <!-- Pipeline Funnel -->
    <div class="panel">
      <div class="panel-title">Pipeline Funnel</div>
      <div class="funnel">
        {% set top = [stats.funnel.Sent, 1] | max %}
        {% for stage, count in stats.funnel.items() %}
        <div class="funnel-row">
          <div class="funnel-label">{{ stage }}</div>
          <div class="funnel-bar-wrap">
            <div class="funnel-bar" style="width: {{ (count / top * 100) | round | int }}%;">
              <span class="funnel-count">{{ count }}</span>
            </div>
          </div>
          <div class="funnel-pct">{% if loop.index > 1 %}{{ (count / top * 100) | round | int }}%{% endif %}</div>
        </div>
        {% endfor %}
      </div>
    </div>

    <!-- Follow-up sequence buckets -->
    <div class="panel">
      <div class="panel-title">Follow-Up Sequence Status</div>
      <div class="bucket-grid">
        {% for day, count in stats.day_buckets.items() %}
        <div class="bucket-card">
          <div class="bucket-day">{{ day }}</div>
          <div class="bucket-count">{{ count }}</div>
        </div>
        {% endfor %}
      </div>
    </div>

    <!-- Cost / Budget -->
    <div class="panel">
      <div class="panel-title">Cost Efficiency</div>
      <div class="budget-row">
        <div class="budget-item">
          <div class="budget-item-label">Budget Spent</div>
          <div class="budget-item-val">${{ stats.budget_spent }}</div>
        </div>
        <div class="budget-item">
          <div class="budget-item-label">Clients Signed</div>
          <div class="budget-item-val">{{ stats.clients_signed }}</div>
        </div>
        <div class="budget-item">
          <div class="budget-item-label">Cost / Client</div>
          <div class="budget-item-val">${{ stats.cpa }}</div>
        </div>
        <div class="budget-item">
          <div class="budget-item-label">Won Revenue</div>
          <div class="budget-item-val">${{ "%.0f"|format(stats.won_revenue) }}</div>
        </div>
      </div>
    </div>

  </div>

  <!-- Template Performance -->
  <div class="panels">
    <div class="panel panel-wide">
      <div class="panel-title">Template Performance</div>
      {% if stats.template_perf %}
      <table>
        <thead>
          <tr>
            <th>Template</th>
            <th>Pain Point</th>
            <th>Sent</th>
            <th>Replies</th>
            <th>Response Rate</th>
            <th>Strategy</th>
          </tr>
        </thead>
        <tbody>
          {% for t in stats.template_perf | sort(attribute='rate', reverse=True) %}
          <tr>
            <td style="font-weight:600;color:#e8e8e8;">{{ t.name }}</td>
            <td style="color:var(--muted);">{{ t.pain_point or '—' }}</td>
            <td>{{ t.sent }}</td>
            <td>{{ t.replies }}</td>
            <td>
              <span class="rate-badge {% if t.rate >= 10 %}great{% elif t.rate >= 5 %}good{% endif %}">
                {{ t.rate }}%
              </span>
            </td>
            <td style="color:var(--muted);font-size:12px;">{{ t.strategy[:60] if t.strategy else '—' }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
      {% else %}
      <div style="color:var(--muted);font-size:13px;padding:16px 0;">No template data yet — will populate as campaigns run.</div>
      {% endif %}
    </div>
  </div>

</div>

<div class="footer">
  <span><span class="dot"></span>Live — auto-refreshes every 30s</span>
  <span>Marceau Solutions · Outreach Analytics v1.0 · Sprint ends Apr 5, 2026</span>
</div>

<script>
  setTimeout(() => location.reload(), 30000);
</script>
</body>
</html>
"""


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    stats = compute_stats()
    return render_template_string(HTML, stats=stats)


@app.route("/api/stats")
def api_stats():
    return jsonify(compute_stats())


if __name__ == "__main__":
    print("Outreach Analytics → http://127.0.0.1:8794")
    app.run(host="127.0.0.1", port=8794, debug=False)
