"""
Client Performance Tracker — AI Services Trial Dashboard
Port 8795 | Dark + Gold theme | Manual daily stats entry + PDF reports
"""

import io
import json
import os
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

from flask import Flask, render_template_string, request, redirect, url_for, send_file, jsonify, flash

app = Flask(__name__)
app.secret_key = "marceau-client-tracker-2026"

# ─── DB Setup ─────────────────────────────────────────────────────────────────

BASE = Path(__file__).parent
DB_PATH = BASE / "data" / "clients.db"


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _create_tables(conn)
    return conn


def _create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            phone TEXT,
            industry TEXT,
            trial_start_date TEXT NOT NULL,
            avg_job_value REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            stat_date TEXT NOT NULL,
            calls_missed INTEGER DEFAULT 0,
            texts_sent INTEGER DEFAULT 0,
            replies_received INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(client_id, stat_date)
        );
    """)
    conn.commit()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def days_in_trial(trial_start_date: str) -> int:
    try:
        start = date.fromisoformat(trial_start_date)
        return (date.today() - start).days + 1
    except Exception:
        return 1


def days_remaining(trial_start_date: str, trial_length: int = 14) -> int:
    try:
        start = date.fromisoformat(trial_start_date)
        end = start + timedelta(days=trial_length - 1)
        remaining = (end - date.today()).days
        return max(0, remaining)
    except Exception:
        return 0


def get_client_summary(conn, client_id):
    client = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    if not client:
        return None
    stats = conn.execute(
        "SELECT * FROM daily_stats WHERE client_id = ? ORDER BY stat_date ASC",
        (client_id,)
    ).fetchall()

    total_missed = sum(r["calls_missed"] for r in stats)
    total_texts = sum(r["texts_sent"] for r in stats)
    total_replies = sum(r["replies_received"] for r in stats)
    recovery_rate = round(total_replies / max(total_missed, 1) * 100, 1)
    revenue_recovered = round(total_replies * client["avg_job_value"], 2)
    day_in = days_in_trial(client["trial_start_date"])
    day_remaining = days_remaining(client["trial_start_date"])

    return {
        "client": dict(client),
        "stats": [dict(r) for r in stats],
        "total_missed": total_missed,
        "total_texts": total_texts,
        "total_replies": total_replies,
        "recovery_rate": recovery_rate,
        "revenue_recovered": revenue_recovered,
        "day_in": min(day_in, 14),
        "day_remaining": day_remaining,
    }


def get_all_summaries(conn):
    clients = conn.execute("SELECT * FROM clients ORDER BY trial_start_date DESC").fetchall()
    return [get_client_summary(conn, c["id"]) for c in clients]


# ─── PDF Generator ────────────────────────────────────────────────────────────

def generate_pdf_report(summary: dict) -> bytes:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.colors import HexColor, white, black
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        gold = HexColor("#C9963C")
        charcoal = HexColor("#333333")
        dark_bg = HexColor("#1a1a1a")
        card_bg = HexColor("#242424")
        light_text = HexColor("#e8e8e8")
        muted = HexColor("#888888")
        green = HexColor("#3fb950")

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=letter,
            leftMargin=0.75*inch, rightMargin=0.75*inch,
            topMargin=0.75*inch, bottomMargin=0.75*inch
        )

        styles = getSampleStyleSheet()
        client = summary["client"]

        def style(name, **kw):
            return ParagraphStyle(name, **kw)

        title_style = style("Title", fontSize=26, textColor=gold, fontName="Helvetica-Bold",
                            spaceAfter=4, alignment=TA_CENTER)
        sub_style = style("Sub", fontSize=11, textColor=muted, fontName="Helvetica",
                          spaceAfter=2, alignment=TA_CENTER)
        section_style = style("Section", fontSize=13, textColor=gold, fontName="Helvetica-Bold",
                              spaceBefore=14, spaceAfter=6)
        body_style = style("Body", fontSize=10, textColor=light_text, fontName="Helvetica",
                           spaceAfter=4, leading=16)
        stat_label_style = style("StatLbl", fontSize=9, textColor=muted, fontName="Helvetica",
                                 alignment=TA_CENTER)
        stat_val_style = style("StatVal", fontSize=24, textColor=gold, fontName="Helvetica-Bold",
                               alignment=TA_CENTER)

        story = []

        # Header
        story.append(Paragraph("Client Performance Report", title_style))
        story.append(Paragraph(f"{client['business_name']} — 14-Day AI Trial", sub_style))
        story.append(Paragraph(
            f"Trial Start: {client['trial_start_date']} &nbsp;|&nbsp; "
            f"Industry: {client.get('industry','—')} &nbsp;|&nbsp; "
            f"Day {summary['day_in']} of 14",
            sub_style
        ))
        story.append(Paragraph(
            f"Report generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            sub_style
        ))
        story.append(Spacer(1, 0.2*inch))
        story.append(HRFlowable(width="100%", thickness=2, color=gold))
        story.append(Spacer(1, 0.15*inch))

        # KPI grid as table
        story.append(Paragraph("Performance Summary", section_style))
        kpi_data = [
            [
                Paragraph("Missed Calls", stat_label_style),
                Paragraph("Texts Sent", stat_label_style),
                Paragraph("Replies Received", stat_label_style),
                Paragraph("Recovery Rate", stat_label_style),
                Paragraph("Revenue Recovered", stat_label_style),
            ],
            [
                Paragraph(str(summary["total_missed"]), stat_val_style),
                Paragraph(str(summary["total_texts"]), stat_val_style),
                Paragraph(str(summary["total_replies"]), stat_val_style),
                Paragraph(f"{summary['recovery_rate']}%", stat_val_style),
                Paragraph(f"${summary['revenue_recovered']:,.0f}", stat_val_style),
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[1.3*inch]*5)
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), card_bg),
            ("GRID", (0,0), (-1,-1), 1, HexColor("#3a3a3a")),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [card_bg, card_bg]),
            ("TOPPADDING", (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 0.2*inch))

        # Avg job value note
        story.append(Paragraph(
            f"<b>Average Job Value:</b> ${client['avg_job_value']:,.2f} &nbsp;|&nbsp; "
            f"Each reply represents a potential ${client['avg_job_value']:,.2f} recovered job.",
            body_style
        ))
        story.append(Spacer(1, 0.15*inch))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#3a3a3a")))

        # Daily breakdown table
        if summary["stats"]:
            story.append(Paragraph("Daily Breakdown", section_style))
            header = [
                Paragraph("<b>Date</b>", body_style),
                Paragraph("<b>Missed</b>", body_style),
                Paragraph("<b>Texts</b>", body_style),
                Paragraph("<b>Replies</b>", body_style),
                Paragraph("<b>Recovery</b>", body_style),
                Paragraph("<b>Rev. Recovered</b>", body_style),
            ]
            rows = [header]
            for s in summary["stats"]:
                rec = round(s["replies_received"] / max(s["calls_missed"], 1) * 100, 0)
                rev = s["replies_received"] * client["avg_job_value"]
                rows.append([
                    Paragraph(s["stat_date"], body_style),
                    Paragraph(str(s["calls_missed"]), body_style),
                    Paragraph(str(s["texts_sent"]), body_style),
                    Paragraph(str(s["replies_received"]), body_style),
                    Paragraph(f"{rec:.0f}%", body_style),
                    Paragraph(f"${rev:,.2f}", body_style),
                ])
            daily_table = Table(rows, colWidths=[1.1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.9*inch, 1.2*inch])
            daily_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), gold),
                ("TEXTCOLOR", (0,0), (-1,0), black),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [card_bg, HexColor("#2c2c2c")]),
                ("GRID", (0,0), (-1,-1), 0.5, HexColor("#3a3a3a")),
                ("TOPPADDING", (0,0), (-1,-1), 6),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
                ("LEFTPADDING", (0,0), (-1,-1), 8),
            ]))
            story.append(daily_table)
            story.append(Spacer(1, 0.15*inch))

        # What This Means section
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#3a3a3a")))
        story.append(Paragraph("What This Means For Your Business", section_style))
        story.append(Paragraph(
            f"During your {summary['day_in']}-day trial, our AI text-back system intercepted "
            f"<b>{summary['total_missed']}</b> missed calls, sent <b>{summary['total_texts']}</b> "
            f"automated follow-up texts, and converted <b>{summary['total_replies']}</b> of those "
            f"leads back into active conversations — a <b>{summary['recovery_rate']}%</b> recovery rate.",
            body_style
        ))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(
            f"At your average job value of <b>${client['avg_job_value']:,.2f}</b>, those recovered "
            f"conversations represent an estimated <b>${summary['revenue_recovered']:,.0f}</b> in "
            f"revenue that would otherwise have been lost to a competitor who answered their phone.",
            body_style
        ))
        story.append(Spacer(1, 0.2*inch))
        story.append(HRFlowable(width="100%", thickness=2, color=gold))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(
            "Marceau Solutions · wmarceau@marceausolutions.com · (239) 398-5676 · marceausolutions.com",
            sub_style
        ))

        doc.build(story)
        return buf.getvalue()

    except ImportError:
        # Fallback: simple text-based PDF alternative message
        return None


# ─── HTML Template ────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Client Performance Tracker — Marceau Solutions</title>
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
  body { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

  .header {
    background: var(--card); border-bottom: 2px solid var(--gold);
    padding: 16px 32px; display: flex; align-items: center; justify-content: space-between;
  }
  .header-logo { width: 36px; height: 36px; background: var(--gold); border-radius: 6px;
    display: flex; align-items: center; justify-content: center; font-weight: 900; color: #000; font-size: 18px; margin-right: 12px; }
  .header-brand { display: flex; align-items: center; }
  .header-title { font-size: 20px; font-weight: 700; color: var(--gold); }
  .header-sub { font-size: 12px; color: var(--muted); }
  .sprint-badge { display: inline-block; background: var(--gold); color: #000;
    font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px; }

  .main { padding: 24px 32px; max-width: 1400px; }

  /* Add Client Form */
  .form-card {
    background: var(--card); border: 1px solid var(--gold); border-radius: 10px;
    padding: 20px; margin-bottom: 28px;
  }
  .form-title { font-size: 13px; font-weight: 700; color: var(--gold);
    text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 16px; }
  .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
  .form-group { display: flex; flex-direction: column; gap: 5px; }
  label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
  input, select, textarea {
    background: var(--card2); border: 1px solid var(--border); border-radius: 6px;
    color: var(--text); padding: 9px 12px; font-size: 13px; width: 100%;
    transition: border-color 0.2s;
  }
  input:focus, select:focus, textarea:focus { outline: none; border-color: var(--gold); }
  .btn {
    background: var(--gold); color: #000; border: none; padding: 10px 20px;
    border-radius: 6px; font-size: 13px; font-weight: 700; cursor: pointer;
    transition: background 0.2s; white-space: nowrap;
  }
  .btn:hover { background: var(--gold-light); }
  .btn-sm { padding: 6px 14px; font-size: 12px; }
  .btn-secondary { background: var(--card2); color: var(--text); border: 1px solid var(--border); }
  .btn-secondary:hover { border-color: var(--gold); background: var(--card); }
  .btn-danger { background: rgba(248,81,73,0.15); color: var(--red); border: 1px solid rgba(248,81,73,0.3); }
  .btn-danger:hover { background: rgba(248,81,73,0.25); }

  /* Flash messages */
  .flash { padding: 10px 16px; border-radius: 6px; margin-bottom: 16px; font-size: 13px; }
  .flash-success { background: rgba(63,185,80,0.15); color: var(--green); border: 1px solid rgba(63,185,80,0.3); }
  .flash-error { background: rgba(248,81,73,0.15); color: var(--red); border: 1px solid rgba(248,81,73,0.3); }

  /* Client cards */
  .clients-grid { display: grid; gap: 20px; }
  .client-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 10px;
    overflow: hidden;
  }
  .client-card-header {
    background: var(--card2); padding: 16px 20px;
    display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid var(--border);
  }
  .client-name { font-size: 17px; font-weight: 700; color: var(--text); }
  .client-meta { font-size: 12px; color: var(--muted); margin-top: 3px; }
  .client-actions { display: flex; gap: 8px; align-items: center; }

  .trial-progress {
    padding: 0 20px 12px; margin-top: 14px;
  }
  .progress-label { font-size: 11px; color: var(--muted); text-transform: uppercase;
    letter-spacing: 0.6px; margin-bottom: 6px; display: flex; justify-content: space-between; }
  .progress-bar { background: var(--card2); border-radius: 4px; height: 8px; overflow: hidden; }
  .progress-fill { height: 100%; background: var(--gold); border-radius: 4px; transition: width 0.4s; }

  /* KPI grid inside client card */
  .client-kpis {
    padding: 0 20px 16px;
    display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px;
  }
  @media (max-width: 800px) { .client-kpis { grid-template-columns: repeat(3, 1fr); } }
  .kpi {
    background: var(--card2); border-radius: 8px; padding: 10px;
    text-align: center; border: 1px solid var(--border);
  }
  .kpi-label { font-size: 10px; color: var(--muted); text-transform: uppercase; margin-bottom: 4px; }
  .kpi-value { font-size: 22px; font-weight: 800; color: var(--gold); }
  .kpi-value.green { color: var(--green); }
  .kpi-value.blue { color: var(--blue); }

  /* Stats entry form */
  .stats-form {
    border-top: 1px solid var(--border); padding: 14px 20px;
    display: none;
  }
  .stats-form.open { display: block; }
  .stats-form-title { font-size: 12px; font-weight: 700; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 10px; }
  .stats-form-row { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; }

  /* Daily history table */
  .history-wrap { padding: 0 20px 16px; display: none; }
  .history-wrap.open { display: block; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th { text-align: left; padding: 7px 10px; font-size: 11px; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }
  tbody tr { border-bottom: 1px solid var(--border); }
  tbody tr:last-child { border-bottom: none; }
  tbody td { padding: 9px 10px; }

  /* Empty state */
  .empty { text-align: center; padding: 60px 20px; color: var(--muted); font-size: 15px; }
  .empty-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.4; }

  .footer {
    padding: 16px 32px; font-size: 11px; color: var(--muted);
    border-top: 1px solid var(--border); margin-top: 24px;
    display: flex; justify-content: space-between;
  }
</style>
</head>
<body>

<div class="header">
  <div class="header-brand">
    <div class="header-logo">M</div>
    <div>
      <div class="header-title">Client Performance Tracker</div>
      <div class="header-sub">14-Day AI Trial Results</div>
    </div>
  </div>
  <span class="sprint-badge">Sprint: Mar 23 → Apr 5, 2026</span>
</div>

<div class="main">

  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}
      <div class="flash flash-{{ cat }}">{{ msg }}</div>
    {% endfor %}
  {% endwith %}

  <!-- Add Client -->
  <div class="form-card">
    <div class="form-title">+ Add Trial Client</div>
    <form method="POST" action="/add_client">
      <div class="form-grid">
        <div class="form-group">
          <label>Business Name *</label>
          <input type="text" name="business_name" required placeholder="Naples HVAC Co.">
        </div>
        <div class="form-group">
          <label>Phone</label>
          <input type="text" name="phone" placeholder="(239) 555-1234">
        </div>
        <div class="form-group">
          <label>Industry</label>
          <select name="industry">
            <option>HVAC</option>
            <option>Med Spa</option>
            <option>Dental</option>
            <option>Restaurant</option>
            <option>Salon</option>
            <option>Insurance</option>
            <option>Real Estate</option>
            <option>Legal</option>
            <option>Auto</option>
            <option>Retail</option>
            <option>Other</option>
          </select>
        </div>
        <div class="form-group">
          <label>Avg Job Value ($)</label>
          <input type="number" name="avg_job_value" min="0" step="50" value="500" required>
        </div>
        <div class="form-group">
          <label>Trial Start Date *</label>
          <input type="date" name="trial_start_date" required value="{{ today }}">
        </div>
        <div class="form-group" style="justify-content:flex-end;">
          <button type="submit" class="btn">Add Client</button>
        </div>
      </div>
    </form>
  </div>

  <!-- Client List -->
  {% if summaries %}
  <div class="clients-grid">
    {% for s in summaries %}
    {% set c = s.client %}
    <div class="client-card">

      <div class="client-card-header">
        <div>
          <div class="client-name">{{ c.business_name }}</div>
          <div class="client-meta">
            {{ c.industry }} &nbsp;·&nbsp; Trial started {{ c.trial_start_date }}
            &nbsp;·&nbsp; Avg job: ${{ "%.0f"|format(c.avg_job_value) }}
            {% if c.phone %}&nbsp;·&nbsp; {{ c.phone }}{% endif %}
          </div>
        </div>
        <div class="client-actions">
          <a href="/report/{{ c.id }}" class="btn btn-sm">Generate Report</a>
          <button class="btn btn-sm btn-secondary" onclick="toggleStats({{ c.id }})">Log Stats</button>
          <button class="btn btn-sm btn-secondary" onclick="toggleHistory({{ c.id }})">History</button>
          <form method="POST" action="/delete_client/{{ c.id }}" style="display:inline;"
            onsubmit="return confirm('Delete {{ c.business_name }}?')">
            <button type="submit" class="btn btn-sm btn-danger">Delete</button>
          </form>
        </div>
      </div>

      <!-- Trial Progress Bar -->
      <div class="trial-progress">
        <div class="progress-label">
          <span>Day {{ s.day_in }} of 14</span>
          <span>{{ s.day_remaining }} days remaining</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width: {{ (s.day_in / 14 * 100) | round | int }}%;"></div>
        </div>
      </div>

      <!-- KPIs -->
      <div class="client-kpis">
        <div class="kpi">
          <div class="kpi-label">Missed Calls</div>
          <div class="kpi-value">{{ s.total_missed }}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Texts Sent</div>
          <div class="kpi-value blue">{{ s.total_texts }}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Replies</div>
          <div class="kpi-value green">{{ s.total_replies }}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Recovery Rate</div>
          <div class="kpi-value">{{ s.recovery_rate }}%</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Rev. Recovered</div>
          <div class="kpi-value" style="font-size:18px;">${{ "%.0f"|format(s.revenue_recovered) }}</div>
        </div>
      </div>

      <!-- Daily Stats Entry Form (collapsible) -->
      <div class="stats-form" id="stats-{{ c.id }}">
        <div class="stats-form-title">Log Daily Stats</div>
        <form method="POST" action="/add_stats/{{ c.id }}">
          <div class="stats-form-row">
            <div class="form-group">
              <label>Date</label>
              <input type="date" name="stat_date" value="{{ today }}" required style="width:150px;">
            </div>
            <div class="form-group">
              <label>Missed Calls</label>
              <input type="number" name="calls_missed" min="0" value="0" required style="width:100px;">
            </div>
            <div class="form-group">
              <label>Texts Sent</label>
              <input type="number" name="texts_sent" min="0" value="0" required style="width:100px;">
            </div>
            <div class="form-group">
              <label>Replies Received</label>
              <input type="number" name="replies_received" min="0" value="0" required style="width:120px;">
            </div>
            <div class="form-group">
              <label>Notes (optional)</label>
              <input type="text" name="notes" placeholder="Any context..." style="width:200px;">
            </div>
            <button type="submit" class="btn">Save Stats</button>
          </div>
        </form>
      </div>

      <!-- Daily History (collapsible) -->
      <div class="history-wrap" id="history-{{ c.id }}">
        {% if s.stats %}
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Missed</th>
              <th>Texts</th>
              <th>Replies</th>
              <th>Recovery</th>
              <th>Rev. Recovered</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {% for row in s.stats | reverse %}
            <tr>
              <td>{{ row.stat_date }}</td>
              <td>{{ row.calls_missed }}</td>
              <td style="color:var(--blue);">{{ row.texts_sent }}</td>
              <td style="color:var(--green);">{{ row.replies_received }}</td>
              <td>{% if row.calls_missed > 0 %}{{ (row.replies_received / row.calls_missed * 100) | round | int }}{% else %}0{% endif %}%</td>
              <td style="color:var(--gold);">${{ "%.0f"|format(row.replies_received * c.avg_job_value) }}</td>
              <td style="color:var(--muted);font-size:12px;">{{ row.notes or '—' }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        {% else %}
        <div style="color:var(--muted);font-size:13px;padding:10px 0;">No stats logged yet. Use "Log Stats" to add daily data.</div>
        {% endif %}
      </div>

    </div>
    {% endfor %}
  </div>
  {% else %}
  <div class="empty">
    <div class="empty-icon">📊</div>
    <div>No trial clients yet.</div>
    <div style="margin-top:8px;font-size:13px;">Add your first client above to start tracking results.</div>
  </div>
  {% endif %}

</div>

<div class="footer">
  <span>Marceau Solutions · Client Performance Tracker v1.0</span>
  <span>Sprint ends Apr 5, 2026 · {{ summaries|length }} active client(s)</span>
</div>

<script>
function toggleStats(id) {
  const el = document.getElementById('stats-' + id);
  el.classList.toggle('open');
}
function toggleHistory(id) {
  const el = document.getElementById('history-' + id);
  el.classList.toggle('open');
}
</script>
</body>
</html>
"""

REPORT_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Report — {{ s.client.business_name }}</title>
<style>
  body { background: #1a1a1a; color: #e8e8e8; font-family: -apple-system, sans-serif; padding: 32px; }
  h1 { color: #C9963C; }
  .warn { color: #f85149; padding: 12px; background: rgba(248,81,73,0.1); border-radius: 6px; margin-top: 16px; }
  a { color: #C9963C; }
</style></head>
<body>
<h1>Report: {{ s.client.business_name }}</h1>
<p style="color:#888;">reportlab is not installed — PDF generation unavailable.</p>
<div class="warn">
  To enable PDF reports, run: <code>pip install reportlab</code><br>
  Then click <a href="/report/{{ s.client.id }}">Generate Report</a> again.
</div>
<p style="margin-top:20px;"><a href="/">&larr; Back to Dashboard</a></p>
</body></html>"""


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    conn = get_db()
    summaries = get_all_summaries(conn)
    conn.close()
    today = date.today().isoformat()
    return render_template_string(HTML, summaries=summaries, today=today)


@app.route("/add_client", methods=["POST"])
def add_client():
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO clients (business_name, phone, industry, avg_job_value, trial_start_date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.form["business_name"].strip(),
            request.form.get("phone", "").strip(),
            request.form.get("industry", "Other"),
            float(request.form.get("avg_job_value", 0)),
            request.form["trial_start_date"],
        ))
        conn.commit()
        flash(f"Client '{request.form['business_name']}' added successfully.", "success")
    except Exception as e:
        flash(f"Error adding client: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for("index"))


@app.route("/add_stats/<int:client_id>", methods=["POST"])
def add_stats(client_id):
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO daily_stats (client_id, stat_date, calls_missed, texts_sent, replies_received, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(client_id, stat_date) DO UPDATE SET
              calls_missed = excluded.calls_missed,
              texts_sent = excluded.texts_sent,
              replies_received = excluded.replies_received,
              notes = excluded.notes
        """, (
            client_id,
            request.form["stat_date"],
            int(request.form.get("calls_missed", 0)),
            int(request.form.get("texts_sent", 0)),
            int(request.form.get("replies_received", 0)),
            request.form.get("notes", ""),
        ))
        conn.commit()
        flash("Stats saved.", "success")
    except Exception as e:
        flash(f"Error saving stats: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for("index"))


@app.route("/delete_client/<int:client_id>", methods=["POST"])
def delete_client(client_id):
    conn = get_db()
    try:
        name = conn.execute("SELECT business_name FROM clients WHERE id = ?", (client_id,)).fetchone()
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()
        flash(f"Client '{name['business_name'] if name else client_id}' deleted.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for("index"))


@app.route("/report/<int:client_id>")
def report(client_id):
    conn = get_db()
    summary = get_client_summary(conn, client_id)
    conn.close()
    if not summary:
        flash("Client not found.", "error")
        return redirect(url_for("index"))

    pdf_bytes = generate_pdf_report(summary)
    if pdf_bytes is None:
        return render_template_string(REPORT_HTML, s=summary)

    filename = f"{summary['client']['business_name'].replace(' ', '_')}_14day_report.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=filename
    )


@app.route("/api/clients")
def api_clients():
    conn = get_db()
    summaries = get_all_summaries(conn)
    conn.close()
    return jsonify(summaries)


if __name__ == "__main__":
    print("Client Performance Tracker → http://127.0.0.1:8795")
    app.run(host="127.0.0.1", port=8795, debug=False)
