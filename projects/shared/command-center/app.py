#!/usr/bin/env python3
"""
Marceau Command Center — Standalone Business Dashboard

WHAT: Web dashboard at localhost:8780 for all business operations
WHY: William can manage scorecard, pipeline, content, and revenue without terminal/Claude
INPUT: Google Sheets (Scorecard), Stripe API, local scripts
OUTPUT: Interactive web dashboard with full CRUD

QUICK USAGE:
  ./scripts/command-center.sh
  # or: python projects/shared/command-center/app.py

DEPENDENCIES: flask, google-api-python-client, google-auth, stripe
API_KEYS: Google OAuth (credentials.json + token_sheets.json), STRIPE_SECRET_KEY
"""

import os
import sys
import json
import subprocess
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, render_template_string, request, jsonify, send_file
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

# Google Sheets
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# Stripe
try:
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_AVAILABLE = bool(stripe.api_key)
except ImportError:
    STRIPE_AVAILABLE = False

# --- Constants ---
SPREADSHEET_ID = "1Y5PwloUBbHM8AeiL032_zWy9jjo9vwhyRZkl7qaKw5o"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token_sheets.json"
DAY_ZERO = datetime(2026, 3, 17)  # 90-day start
PORT = 8780

app = Flask(__name__)


# ============================================================
# Google Sheets helpers
# ============================================================

def get_sheets_service():
    """Get authenticated Google Sheets service."""
    if not GOOGLE_AVAILABLE:
        return None
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
        else:
            if not CREDENTIALS_FILE.exists():
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds)


def sheets_read(range_str):
    """Read from scorecard sheet."""
    svc = get_sheets_service()
    if not svc:
        return []
    result = svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=range_str
    ).execute()
    return result.get('values', [])


def sheets_append(range_str, values):
    """Append row to scorecard sheet."""
    svc = get_sheets_service()
    if not svc:
        return False
    svc.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=range_str,
        valueInputOption='USER_ENTERED',
        body={'values': values}
    ).execute()
    return True


def sheets_update(range_str, values):
    """Update cells in scorecard sheet."""
    svc = get_sheets_service()
    if not svc:
        return False
    svc.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=range_str,
        valueInputOption='USER_ENTERED',
        body={'values': values}
    ).execute()
    return True


# ============================================================
# Date helpers
# ============================================================

def get_day_info():
    """Calculate day number, week number from DAY_ZERO."""
    today = datetime.now()
    delta = (today - DAY_ZERO).days + 1  # Day 1 = March 17
    day_num = max(1, min(delta, 90))
    week_num = max(1, min((delta - 1) // 7 + 1, 12))
    return {
        'day_number': day_num,
        'week_number': week_num,
        'date': today.strftime('%Y-%m-%d'),
        'day_of_week': today.strftime('%A'),
        'days_remaining': max(0, 90 - delta),
        'pct_complete': round(min(delta / 90 * 100, 100), 1),
    }


# ============================================================
# API Routes
# ============================================================

@app.route('/api/day-info')
def api_day_info():
    return jsonify(get_day_info())


@app.route('/api/log-day', methods=['POST'])
def api_log_day():
    """Write daily scorecard entry to Google Sheets."""
    try:
        data = request.json
        info = get_day_info()
        row = [[
            info['date'],
            str(info['day_number']),
            str(info['week_number']),
            info['day_of_week'],
            str(data.get('energy', '')),
            str(data.get('outreach', '')),
            str(data.get('meetings', '')),
            str(data.get('videos', '')),
            str(data.get('content', '')),
            str(data.get('training', '')),
            str(data.get('notes', '')),
        ]]
        success = sheets_append("'Daily Log'!A:K", row)
        if success:
            return jsonify({'status': 'ok', 'message': f'Day {info["day_number"]} logged'})
        return jsonify({'status': 'error', 'message': 'Sheets API unavailable'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/daily-log')
def api_daily_log():
    """Get all daily log entries."""
    try:
        rows = sheets_read("'Daily Log'!A:K")
        if not rows:
            return jsonify({'headers': [], 'rows': []})
        return jsonify({'headers': rows[0], 'rows': rows[1:]})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/weekly-summary')
def api_weekly_summary():
    """Get weekly summary data."""
    try:
        rows = sheets_read("'Weekly Summary'!A:O")
        if not rows:
            return jsonify({'headers': [], 'rows': []})
        return jsonify({'headers': rows[0], 'rows': rows[1:]})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/goals')
def api_goals():
    """Get 90-day goals."""
    try:
        rows = sheets_read("'90-Day Goals'!A:F")
        if not rows:
            return jsonify({'headers': [], 'rows': []})
        return jsonify({'headers': rows[0], 'rows': rows[1:]})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/content-calendar')
def api_content_calendar():
    """Get content calendar."""
    try:
        rows = sheets_read("'Content Calendar'!A:F")
        if not rows:
            return jsonify({'headers': [], 'rows': []})
        return jsonify({'headers': rows[0], 'rows': rows[1:]})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/content-calendar/toggle', methods=['POST'])
def api_toggle_content():
    """Toggle content item published status."""
    try:
        data = request.json
        row_idx = int(data['row']) + 2  # +1 for header, +1 for 1-based
        current = data.get('current', 'FALSE')
        new_val = 'FALSE' if current == 'TRUE' else 'TRUE'
        sheets_update(f"'Content Calendar'!D{row_idx}", [[new_val]])
        if new_val == 'TRUE':
            sheets_update(f"'Content Calendar'!E{row_idx}", [[datetime.now().strftime('%Y-%m-%d')]])
        return jsonify({'status': 'ok', 'new_value': new_val})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/pipeline')
def api_pipeline():
    """Get pipeline data. Uses a 'Pipeline' tab if it exists, otherwise returns sample structure."""
    try:
        # Try reading Pipeline tab
        rows = sheets_read("'Pipeline'!A:G")
        if rows and len(rows) > 1:
            return jsonify({'headers': rows[0], 'rows': rows[1:]})
        # If no Pipeline tab, return empty with headers
        return jsonify({
            'headers': ['Name', 'Business', 'Source', 'Stage', 'Value', 'Notes', 'Date_Added'],
            'rows': []
        })
    except Exception:
        # Tab doesn't exist — create it
        try:
            svc = get_sheets_service()
            if svc:
                # Add the Pipeline tab
                svc.spreadsheets().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body={'requests': [{'addSheet': {'properties': {'title': 'Pipeline'}}}]}
                ).execute()
                headers = [['Name', 'Business', 'Source', 'Stage', 'Value', 'Notes', 'Date_Added']]
                sheets_update("'Pipeline'!A1:G1", headers)
        except Exception:
            pass
        return jsonify({
            'headers': ['Name', 'Business', 'Source', 'Stage', 'Value', 'Notes', 'Date_Added'],
            'rows': []
        })


@app.route('/api/pipeline/add', methods=['POST'])
def api_pipeline_add():
    """Add a new lead to the pipeline."""
    try:
        data = request.json
        row = [[
            data.get('name', ''),
            data.get('business', ''),
            data.get('source', ''),
            data.get('stage', 'Lead'),
            data.get('value', ''),
            data.get('notes', ''),
            datetime.now().strftime('%Y-%m-%d'),
        ]]
        success = sheets_append("'Pipeline'!A:G", row)
        if success:
            return jsonify({'status': 'ok'})
        return jsonify({'status': 'error', 'message': 'Sheets unavailable'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/pipeline/update-stage', methods=['POST'])
def api_pipeline_update_stage():
    """Move a lead to the next stage."""
    try:
        data = request.json
        row_idx = int(data['row']) + 2  # +1 header, +1 for 1-based
        new_stage = data['stage']
        sheets_update(f"'Pipeline'!D{row_idx}", [[new_stage]])
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/pipeline/add-note', methods=['POST'])
def api_pipeline_add_note():
    """Add note to a pipeline lead."""
    try:
        data = request.json
        row_idx = int(data['row']) + 2
        note = data['note']
        # Get existing notes
        existing = sheets_read(f"'Pipeline'!F{row_idx}")
        old_note = existing[0][0] if existing and existing[0] else ''
        new_note = f"{old_note}\n{datetime.now().strftime('%m/%d')}: {note}" if old_note else f"{datetime.now().strftime('%m/%d')}: {note}"
        sheets_update(f"'Pipeline'!F{row_idx}", [[new_note]])
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/revenue')
def api_revenue():
    """Get Stripe revenue data."""
    if not STRIPE_AVAILABLE:
        return jsonify({'status': 'error', 'message': 'Stripe not configured'}), 500
    try:
        now = datetime.now()
        seven_days_ago = int((now - timedelta(days=7)).timestamp())
        thirty_days_ago = int((now - timedelta(days=30)).timestamp())

        # Get charges for last 30 days
        charges = stripe.Charge.list(created={'gte': thirty_days_ago}, limit=100)

        revenue_7d = 0
        revenue_30d = 0
        recent_charges = []

        for charge in charges.auto_paging_iter():
            if charge.status == 'succeeded':
                amount = charge.amount / 100  # cents to dollars
                revenue_30d += amount
                if charge.created >= seven_days_ago:
                    revenue_7d += amount
                if len(recent_charges) < 10:
                    recent_charges.append({
                        'amount': amount,
                        'date': datetime.fromtimestamp(charge.created).strftime('%Y-%m-%d'),
                        'description': charge.description or 'Charge',
                        'customer': charge.billing_details.get('name', '') if charge.billing_details else '',
                    })

        # Get active subscriptions
        subs = stripe.Subscription.list(status='active', limit=100)
        mrr = sum(
            sub.items.data[0].price.unit_amount / 100
            for sub in subs.auto_paging_iter()
            if sub.items.data
        )

        return jsonify({
            'revenue_7d': round(revenue_7d, 2),
            'revenue_30d': round(revenue_30d, 2),
            'mrr': round(mrr, 2),
            'recent_charges': recent_charges,
            'active_subs': subs.data.__len__() if hasattr(subs.data, '__len__') else 0,
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/health')
def api_health():
    """Run health check."""
    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / 'scripts' / 'health_check.py'), '--fast'],
            capture_output=True, text=True, timeout=30, cwd=str(PROJECT_ROOT)
        )
        output = result.stdout + result.stderr
        return jsonify({'status': 'ok', 'output': output})
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'message': 'Health check timed out'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/generate-proposal', methods=['POST'])
def api_generate_proposal():
    """Generate a branded proposal PDF."""
    try:
        data = request.json
        # Build proposal data JSON
        proposal_data = {
            "title": f"Proposal for {data.get('client_name', 'Client')}",
            "client_name": data.get('client_name', ''),
            "service": data.get('service', 'AI Business Services'),
            "price": data.get('price', ''),
            "sections": [
                {"heading": "Overview", "body": data.get('overview', 'Custom AI-powered business solutions tailored to your needs.')},
                {"heading": "Deliverables", "body": data.get('deliverables', '- Custom solution design\n- Implementation\n- Training & support')},
                {"heading": "Investment", "body": f"${data.get('price', 'TBD')}/month"},
                {"heading": "Next Steps", "body": "Schedule a call: calendly.com/wmarceau/free-fitness-strategy-call"},
            ]
        }

        # Write temp JSON
        tmp_json = PROJECT_ROOT / "tmp_proposal.json"
        tmp_pdf = PROJECT_ROOT / f"proposal_{data.get('client_name', 'client').replace(' ', '_').lower()}.pdf"
        with open(tmp_json, 'w') as f:
            json.dump(proposal_data, f)

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / 'execution' / 'branded_pdf_engine.py'),
             '--template', 'generic', '--input', str(tmp_json), '--output', str(tmp_pdf)],
            capture_output=True, text=True, timeout=30, cwd=str(PROJECT_ROOT)
        )

        tmp_json.unlink(missing_ok=True)

        if tmp_pdf.exists():
            return send_file(str(tmp_pdf), as_attachment=True, download_name=tmp_pdf.name)
        return jsonify({'status': 'error', 'message': result.stdout + result.stderr}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/weekly-totals')
def api_weekly_totals():
    """Calculate running totals for current week from daily log."""
    try:
        rows = sheets_read("'Daily Log'!A:K")
        if not rows or len(rows) < 2:
            return jsonify({'outreach': 0, 'meetings': 0, 'videos': 0, 'content': 0})

        info = get_day_info()
        current_week = info['week_number']

        totals = {'outreach': 0, 'meetings': 0, 'videos': 0, 'content': 0}
        for row in rows[1:]:
            if len(row) >= 3 and row[2] == str(current_week):
                totals['outreach'] += int(row[5]) if len(row) > 5 and row[5] else 0
                totals['meetings'] += int(row[6]) if len(row) > 6 and row[6] else 0
                totals['videos'] += int(row[7]) if len(row) > 7 and row[7] else 0
                totals['content'] += int(row[8]) if len(row) > 8 and row[8] else 0

        # Weekly targets
        targets = {'outreach': 50, 'meetings': 5, 'videos': 2, 'content': 5}
        return jsonify({'totals': totals, 'targets': targets})
    except Exception as e:
        return jsonify({'totals': {'outreach': 0, 'meetings': 0, 'videos': 0, 'content': 0},
                        'targets': {'outreach': 50, 'meetings': 5, 'videos': 2, 'content': 5}})


# ============================================================
# Main page — single HTML file with all frontend
# ============================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Marceau Command Center</title>
<style>
  :root {
    --gold: #C9963C;
    --gold-light: #D4AF37;
    --gold-dim: rgba(201,150,60,0.15);
    --charcoal: #333333;
    --charcoal-deep: #2D2D2D;
    --bg: #1a1a1a;
    --card-bg: #252525;
    --card-border: #3a3a3a;
    --text: #f8fafc;
    --text-dim: #94a3b8;
    --green: #22c55e;
    --yellow: #f59e0b;
    --red: #ef4444;
    --blue: #3b82f6;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }

  /* --- Header --- */
  .header {
    background: var(--charcoal-deep);
    border-bottom: 2px solid var(--gold);
    padding: 12px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  .header h1 {
    color: var(--gold);
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .header-stats {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
  }
  .header-stat {
    text-align: center;
  }
  .header-stat .value {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--gold);
  }
  .header-stat .label {
    font-size: 0.7rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  /* --- Navigation --- */
  .nav {
    display: flex;
    gap: 0;
    background: var(--charcoal);
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .nav button {
    flex: 1;
    min-width: 100px;
    padding: 12px 16px;
    background: none;
    border: none;
    border-bottom: 3px solid transparent;
    color: var(--text-dim);
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s;
  }
  .nav button:hover { color: var(--text); background: rgba(255,255,255,0.05); }
  .nav button.active {
    color: var(--gold);
    border-bottom-color: var(--gold);
    background: rgba(201,150,60,0.08);
  }

  /* --- Content Area --- */
  .content { padding: 16px; max-width: 1200px; margin: 0 auto; }

  .section { display: none; }
  .section.active { display: block; }

  /* --- Cards --- */
  .card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
  }
  .card h2 {
    color: var(--gold);
    font-size: 1rem;
    margin-bottom: 16px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  /* --- Form elements --- */
  .form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
  }
  .form-group { display: flex; flex-direction: column; gap: 4px; }
  .form-group label {
    font-size: 0.75rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .form-group input, .form-group textarea, .form-group select {
    background: var(--bg);
    border: 1px solid var(--card-border);
    border-radius: 6px;
    color: var(--text);
    padding: 10px 12px;
    font-size: 0.95rem;
    transition: border 0.2s;
  }
  .form-group input:focus, .form-group textarea:focus, .form-group select:focus {
    outline: none;
    border-color: var(--gold);
  }
  .form-group textarea { resize: vertical; min-height: 60px; }

  /* --- Buttons --- */
  .btn {
    padding: 10px 20px;
    border-radius: 6px;
    border: none;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-gold { background: var(--gold); color: var(--charcoal); }
  .btn-gold:hover { background: var(--gold-light); }
  .btn-outline {
    background: none;
    border: 1px solid var(--gold);
    color: var(--gold);
  }
  .btn-outline:hover { background: var(--gold-dim); }
  .btn-small {
    padding: 5px 12px;
    font-size: 0.75rem;
    border-radius: 4px;
  }
  .btn-green { background: var(--green); color: #fff; }
  .btn-blue { background: var(--blue); color: #fff; }
  .btn-red { background: var(--red); color: #fff; }

  /* --- Progress bar --- */
  .progress-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }
  .progress-label {
    font-size: 0.8rem;
    color: var(--text-dim);
    min-width: 80px;
  }
  .progress-bar {
    flex: 1;
    height: 8px;
    background: var(--bg);
    border-radius: 4px;
    overflow: hidden;
  }
  .progress-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
  }
  .progress-value {
    font-size: 0.8rem;
    font-weight: 600;
    min-width: 50px;
    text-align: right;
  }

  /* --- Table --- */
  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }
  .data-table th {
    background: var(--charcoal);
    color: var(--gold);
    padding: 10px 12px;
    text-align: left;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    position: sticky;
    top: 0;
  }
  .data-table td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--card-border);
    vertical-align: top;
  }
  .data-table tr:hover td { background: rgba(255,255,255,0.03); }

  /* --- Badges --- */
  .badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .badge-lead { background: var(--text-dim); color: var(--charcoal); }
  .badge-discovery { background: var(--blue); color: #fff; }
  .badge-proposal { background: var(--yellow); color: var(--charcoal); }
  .badge-won { background: var(--green); color: #fff; }
  .badge-lost { background: var(--red); color: #fff; }

  .stage-Lead { background: #6b7280; color: #fff; }
  .stage-Discovery { background: var(--blue); color: #fff; }
  .stage-Proposal { background: var(--yellow); color: var(--charcoal); }
  .stage-Closed\\ Won, .stage-won { background: var(--green); color: #fff; }
  .stage-Closed\\ Lost, .stage-lost { background: var(--red); color: #fff; }

  /* --- Status colors --- */
  .status-achieved { color: var(--gold); font-weight: 700; }
  .status-on-track { color: var(--green); }
  .status-in-progress { color: var(--blue); }
  .status-at-risk { color: var(--yellow); }
  .status-not-started { color: var(--text-dim); }

  /* --- Toast --- */
  .toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    z-index: 1000;
    transform: translateY(100px);
    opacity: 0;
    transition: all 0.3s ease;
  }
  .toast.show { transform: translateY(0); opacity: 1; }
  .toast-success { background: var(--green); color: #fff; }
  .toast-error { background: var(--red); color: #fff; }

  /* --- Quick action cards --- */
  .action-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
  }
  .action-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 20px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .action-card:hover {
    border-color: var(--gold);
    transform: translateY(-2px);
  }
  .action-card h3 { color: var(--gold); margin-bottom: 8px; font-size: 0.95rem; }
  .action-card p { color: var(--text-dim); font-size: 0.8rem; }

  /* --- Health output --- */
  .health-output {
    background: var(--bg);
    border: 1px solid var(--card-border);
    border-radius: 6px;
    padding: 16px;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.8rem;
    white-space: pre-wrap;
    max-height: 400px;
    overflow-y: auto;
    color: var(--green);
  }

  /* --- Revenue cards --- */
  .revenue-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 20px;
  }
  .revenue-card {
    background: var(--bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 16px;
    text-align: center;
  }
  .revenue-card .amount {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--gold);
  }
  .revenue-card .label {
    font-size: 0.75rem;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-top: 4px;
  }

  /* --- Loading spinner --- */
  .spinner {
    display: inline-block;
    width: 20px; height: 20px;
    border: 2px solid var(--card-border);
    border-top-color: var(--gold);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* --- Modal --- */
  .modal-overlay {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.7);
    z-index: 200;
    align-items: center;
    justify-content: center;
  }
  .modal-overlay.show { display: flex; }
  .modal {
    background: var(--card-bg);
    border: 1px solid var(--gold);
    border-radius: 12px;
    padding: 24px;
    width: 90%;
    max-width: 500px;
    max-height: 80vh;
    overflow-y: auto;
  }
  .modal h2 { color: var(--gold); margin-bottom: 16px; }
  .modal-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    margin-top: 16px;
  }

  /* --- Responsive --- */
  @media (max-width: 600px) {
    .header { padding: 10px 12px; }
    .header h1 { font-size: 1rem; }
    .header-stats { gap: 12px; }
    .header-stat .value { font-size: 1.1rem; }
    .content { padding: 10px; }
    .form-grid { grid-template-columns: 1fr 1fr; }
    .nav button { padding: 10px 12px; font-size: 0.75rem; min-width: 70px; }
    .revenue-card .amount { font-size: 1.4rem; }
  }

  /* Checkbox styling */
  .content-check {
    width: 20px; height: 20px;
    accent-color: var(--gold);
    cursor: pointer;
  }

  .table-scroll { overflow-x: auto; }
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <h1>MARCEAU COMMAND CENTER</h1>
  <div class="header-stats">
    <div class="header-stat">
      <div class="value" id="hdr-day">--</div>
      <div class="label">Day / 90</div>
    </div>
    <div class="header-stat">
      <div class="value" id="hdr-week">--</div>
      <div class="label">Week / 12</div>
    </div>
    <div class="header-stat">
      <div class="value" id="hdr-pct">--</div>
      <div class="label">Complete</div>
    </div>
    <div class="header-stat">
      <div class="value" id="hdr-remaining">--</div>
      <div class="label">Days Left</div>
    </div>
  </div>
</div>

<!-- Navigation -->
<div class="nav">
  <button class="active" onclick="showSection('scorecard', this)">Scorecard</button>
  <button onclick="showSection('pipeline', this)">Pipeline</button>
  <button onclick="showSection('actions', this)">Quick Actions</button>
  <button onclick="showSection('weekly', this)">Weekly View</button>
  <button onclick="showSection('content', this)">Content</button>
</div>

<div class="content">

  <!-- ======== SECTION 1: DAILY SCORECARD ======== -->
  <div id="section-scorecard" class="section active">
    <div class="card">
      <h2>Log Today — <span id="today-date"></span> (<span id="today-dow"></span>)</h2>
      <div class="form-grid">
        <div class="form-group">
          <label>Energy (1-10)</label>
          <input type="number" id="inp-energy" min="1" max="10" placeholder="7">
        </div>
        <div class="form-group">
          <label>Outreach Count</label>
          <input type="number" id="inp-outreach" min="0" placeholder="0">
        </div>
        <div class="form-group">
          <label>Meetings Booked</label>
          <input type="number" id="inp-meetings" min="0" placeholder="0">
        </div>
        <div class="form-group">
          <label>Videos Filmed</label>
          <input type="number" id="inp-videos" min="0" placeholder="0">
        </div>
        <div class="form-group">
          <label>Content Posted</label>
          <input type="number" id="inp-content" min="0" placeholder="0">
        </div>
        <div class="form-group">
          <label>Training</label>
          <select id="inp-training">
            <option value="">--</option>
            <option value="Yes">Yes</option>
            <option value="No">No</option>
            <option value="Rest Day">Rest Day</option>
          </select>
        </div>
      </div>
      <div class="form-group" style="margin-top: 12px;">
        <label>Notes</label>
        <textarea id="inp-notes" placeholder="Wins, blockers, observations..."></textarea>
      </div>
      <div style="margin-top: 16px; display: flex; gap: 10px; flex-wrap: wrap;">
        <button class="btn btn-gold" onclick="logDay()">Log Day</button>
      </div>
    </div>

    <!-- Weekly progress bars -->
    <div class="card">
      <h2>This Week's Progress</h2>
      <div id="weekly-progress">
        <div class="spinner"></div> Loading...
      </div>
    </div>

    <!-- Recent log entries -->
    <div class="card">
      <h2>Recent Entries</h2>
      <div class="table-scroll">
        <table class="data-table" id="daily-log-table">
          <thead><tr><th>Date</th><th>Day</th><th>Energy</th><th>Outreach</th><th>Meetings</th><th>Videos</th><th>Content</th><th>Training</th></tr></thead>
          <tbody id="daily-log-body"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- ======== SECTION 2: SALES PIPELINE ======== -->
  <div id="section-pipeline" class="section">
    <div class="card">
      <h2>Sales Pipeline</h2>
      <div style="margin-bottom: 16px;">
        <button class="btn btn-gold" onclick="showAddLeadModal()">+ Add Lead</button>
      </div>
      <div class="table-scroll">
        <table class="data-table" id="pipeline-table">
          <thead><tr><th>Name</th><th>Business</th><th>Source</th><th>Stage</th><th>Value</th><th>Notes</th><th>Actions</th></tr></thead>
          <tbody id="pipeline-body"></tbody>
        </table>
      </div>
      <div id="pipeline-empty" style="display:none; text-align:center; padding:40px; color: var(--text-dim);">
        No leads yet. Click "+ Add Lead" to start building your pipeline.
      </div>
    </div>
  </div>

  <!-- ======== SECTION 3: QUICK ACTIONS ======== -->
  <div id="section-actions" class="section">
    <div class="action-grid">
      <div class="action-card" onclick="showProposalModal()">
        <h3>Generate Proposal</h3>
        <p>Create a branded PDF proposal for a prospect</p>
      </div>
      <div class="action-card" onclick="checkHealth()">
        <h3>System Health Check</h3>
        <p>Check n8n, EC2, Stripe, and all integrations</p>
      </div>
      <div class="action-card" onclick="viewRevenue()">
        <h3>View Revenue</h3>
        <p>7-day, 30-day revenue and MRR from Stripe</p>
      </div>
      <div class="action-card" onclick="window.open('https://n8n.marceausolutions.com', '_blank')">
        <h3>Open n8n</h3>
        <p>Workflow automation dashboard</p>
      </div>
      <div class="action-card" onclick="window.open('https://docs.google.com/spreadsheets/d/{{ sheet_id }}', '_blank')">
        <h3>Open Scorecard Sheet</h3>
        <p>View raw data in Google Sheets</p>
      </div>
      <div class="action-card" onclick="window.open('https://dashboard.stripe.com', '_blank')">
        <h3>Open Stripe</h3>
        <p>Payment dashboard and subscriptions</p>
      </div>
    </div>

    <!-- Health check output -->
    <div class="card" id="health-card" style="display:none; margin-top: 16px;">
      <h2>System Health</h2>
      <div class="health-output" id="health-output"></div>
    </div>

    <!-- Revenue display -->
    <div class="card" id="revenue-card" style="display:none; margin-top: 16px;">
      <h2>Revenue</h2>
      <div class="revenue-grid" id="revenue-grid"></div>
      <h2 style="margin-top:16px;">Recent Charges</h2>
      <div class="table-scroll">
        <table class="data-table">
          <thead><tr><th>Date</th><th>Amount</th><th>Description</th><th>Customer</th></tr></thead>
          <tbody id="revenue-charges"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- ======== SECTION 4: WEEKLY SCORECARD ======== -->
  <div id="section-weekly" class="section">
    <div class="card">
      <h2>12-Week Scorecard</h2>
      <div class="table-scroll">
        <table class="data-table" id="weekly-table">
          <thead><tr>
            <th>Week</th><th>Starting</th><th>Outreach</th><th>Meetings</th>
            <th>Proposals</th><th>Closed</th><th>Videos</th><th>Shorts</th>
            <th>Training</th><th>Avg Energy</th><th>Score</th>
          </tr></thead>
          <tbody id="weekly-body"></tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <h2>90-Day Goals</h2>
      <div id="goals-container"></div>
    </div>
  </div>

  <!-- ======== SECTION 5: CONTENT CALENDAR ======== -->
  <div id="section-content" class="section">
    <div class="card">
      <h2>Content Calendar</h2>
      <div class="table-scroll">
        <table class="data-table" id="content-table">
          <thead><tr><th>Week</th><th>Topic</th><th>Type</th><th>Published</th><th>Date</th><th>Notes</th></tr></thead>
          <tbody id="content-body"></tbody>
        </table>
      </div>
    </div>
  </div>

</div>

<!-- ======== MODALS ======== -->

<!-- Add Lead Modal -->
<div class="modal-overlay" id="modal-add-lead">
  <div class="modal">
    <h2>Add New Lead</h2>
    <div class="form-group" style="margin-bottom:10px;">
      <label>Name</label>
      <input type="text" id="lead-name" placeholder="John Smith">
    </div>
    <div class="form-group" style="margin-bottom:10px;">
      <label>Business</label>
      <input type="text" id="lead-business" placeholder="Smith HVAC">
    </div>
    <div class="form-group" style="margin-bottom:10px;">
      <label>Source</label>
      <select id="lead-source">
        <option value="Cold Outreach">Cold Outreach</option>
        <option value="Referral">Referral</option>
        <option value="Inbound">Inbound</option>
        <option value="Social Media">Social Media</option>
        <option value="Networking">Networking</option>
      </select>
    </div>
    <div class="form-group" style="margin-bottom:10px;">
      <label>Estimated Value ($/mo)</label>
      <input type="text" id="lead-value" placeholder="2000">
    </div>
    <div class="form-group" style="margin-bottom:10px;">
      <label>Notes</label>
      <textarea id="lead-notes" placeholder="Initial contact details..."></textarea>
    </div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal('modal-add-lead')">Cancel</button>
      <button class="btn btn-gold" onclick="addLead()">Add Lead</button>
    </div>
  </div>
</div>

<!-- Add Note Modal -->
<div class="modal-overlay" id="modal-add-note">
  <div class="modal">
    <h2>Add Note</h2>
    <input type="hidden" id="note-row-idx">
    <div class="form-group">
      <label>Note</label>
      <textarea id="note-text" placeholder="Follow-up details..."></textarea>
    </div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal('modal-add-note')">Cancel</button>
      <button class="btn btn-gold" onclick="saveNote()">Save Note</button>
    </div>
  </div>
</div>

<!-- Proposal Modal -->
<div class="modal-overlay" id="modal-proposal">
  <div class="modal">
    <h2>Generate Proposal</h2>
    <div class="form-group" style="margin-bottom:10px;">
      <label>Client Name</label>
      <input type="text" id="prop-client" placeholder="Client Name">
    </div>
    <div class="form-group" style="margin-bottom:10px;">
      <label>Service</label>
      <input type="text" id="prop-service" placeholder="AI Business Services">
    </div>
    <div class="form-group" style="margin-bottom:10px;">
      <label>Monthly Price ($)</label>
      <input type="text" id="prop-price" placeholder="2000">
    </div>
    <div class="form-group" style="margin-bottom:10px;">
      <label>Overview</label>
      <textarea id="prop-overview" placeholder="What you'll deliver..."></textarea>
    </div>
    <div class="form-group" style="margin-bottom:10px;">
      <label>Deliverables</label>
      <textarea id="prop-deliverables" placeholder="- Item 1&#10;- Item 2"></textarea>
    </div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal('modal-proposal')">Cancel</button>
      <button class="btn btn-gold" onclick="generateProposal()">Generate PDF</button>
    </div>
  </div>
</div>

<!-- Toast -->
<div class="toast" id="toast"></div>

<script>
// ============================================================
// STATE & NAVIGATION
// ============================================================

function showSection(name, btn) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('section-' + name).classList.add('active');
  if (btn) btn.classList.add('active');

  // Load data for section
  if (name === 'pipeline') loadPipeline();
  if (name === 'weekly') { loadWeeklySummary(); loadGoals(); }
  if (name === 'content') loadContentCalendar();
}

function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast toast-' + type + ' show';
  setTimeout(() => t.classList.remove('show'), 3000);
}

function showModal(id) { document.getElementById(id).classList.add('show'); }
function closeModal(id) { document.getElementById(id).classList.remove('show'); }

// ============================================================
// HEADER STATS
// ============================================================

async function loadDayInfo() {
  try {
    const r = await fetch('/api/day-info');
    const d = await r.json();
    document.getElementById('hdr-day').textContent = d.day_number;
    document.getElementById('hdr-week').textContent = d.week_number;
    document.getElementById('hdr-pct').textContent = d.pct_complete + '%';
    document.getElementById('hdr-remaining').textContent = d.days_remaining;
    document.getElementById('today-date').textContent = d.date;
    document.getElementById('today-dow').textContent = d.day_of_week;
  } catch(e) { console.error('Day info error:', e); }
}

// ============================================================
// DAILY SCORECARD
// ============================================================

async function logDay() {
  const data = {
    energy: document.getElementById('inp-energy').value,
    outreach: document.getElementById('inp-outreach').value,
    meetings: document.getElementById('inp-meetings').value,
    videos: document.getElementById('inp-videos').value,
    content: document.getElementById('inp-content').value,
    training: document.getElementById('inp-training').value,
    notes: document.getElementById('inp-notes').value,
  };

  try {
    const r = await fetch('/api/log-day', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    });
    const result = await r.json();
    if (result.status === 'ok') {
      showToast(result.message);
      // Clear form
      ['inp-energy','inp-outreach','inp-meetings','inp-videos','inp-content','inp-notes'].forEach(
        id => document.getElementById(id).value = ''
      );
      document.getElementById('inp-training').value = '';
      loadDailyLog();
      loadWeeklyProgress();
    } else {
      showToast(result.message, 'error');
    }
  } catch(e) {
    showToast('Error logging day: ' + e.message, 'error');
  }
}

async function loadDailyLog() {
  try {
    const r = await fetch('/api/daily-log');
    const d = await r.json();
    const tbody = document.getElementById('daily-log-body');
    tbody.innerHTML = '';

    // Show last 10 entries, most recent first
    const rows = (d.rows || []).slice(-10).reverse();
    rows.forEach(row => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${row[0] || ''}</td>
        <td>${row[1] || ''}</td>
        <td>${row[4] || ''}</td>
        <td>${row[5] || ''}</td>
        <td>${row[6] || ''}</td>
        <td>${row[7] || ''}</td>
        <td>${row[8] || ''}</td>
        <td>${row[9] || ''}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch(e) { console.error('Daily log error:', e); }
}

async function loadWeeklyProgress() {
  try {
    const r = await fetch('/api/weekly-totals');
    const d = await r.json();
    const container = document.getElementById('weekly-progress');

    const metrics = [
      {key: 'outreach', label: 'Outreach', color: 'var(--gold)'},
      {key: 'meetings', label: 'Meetings', color: 'var(--blue)'},
      {key: 'videos', label: 'Videos', color: 'var(--green)'},
      {key: 'content', label: 'Content', color: 'var(--yellow)'},
    ];

    let html = '';
    metrics.forEach(m => {
      const val = d.totals[m.key] || 0;
      const target = d.targets[m.key] || 1;
      const pct = Math.min(Math.round(val / target * 100), 100);
      const color = pct >= 100 ? 'var(--green)' : pct >= 60 ? m.color : 'var(--red)';
      html += `
        <div class="progress-wrap">
          <span class="progress-label">${m.label}</span>
          <div class="progress-bar">
            <div class="progress-fill" style="width:${pct}%;background:${color};"></div>
          </div>
          <span class="progress-value">${val}/${target}</span>
        </div>
      `;
    });
    container.innerHTML = html;
  } catch(e) {
    document.getElementById('weekly-progress').innerHTML = '<span style="color:var(--text-dim)">Unable to load weekly progress</span>';
  }
}

// ============================================================
// PIPELINE
// ============================================================

const STAGES = ['Lead', 'Discovery', 'Proposal', 'Closed Won', 'Closed Lost'];

function stageBadge(stage) {
  const cls = {
    'Lead': 'badge-lead',
    'Discovery': 'badge-discovery',
    'Proposal': 'badge-proposal',
    'Closed Won': 'badge-won',
    'Closed Lost': 'badge-lost',
  }[stage] || 'badge-lead';
  return `<span class="badge ${cls}">${stage}</span>`;
}

function nextStage(current) {
  const idx = STAGES.indexOf(current);
  if (idx >= 0 && idx < STAGES.length - 2) return STAGES[idx + 1];
  return null;
}

async function loadPipeline() {
  try {
    const r = await fetch('/api/pipeline');
    const d = await r.json();
    const tbody = document.getElementById('pipeline-body');
    const empty = document.getElementById('pipeline-empty');
    tbody.innerHTML = '';

    if (!d.rows || d.rows.length === 0) {
      empty.style.display = 'block';
      return;
    }
    empty.style.display = 'none';

    d.rows.forEach((row, idx) => {
      const stage = row[3] || 'Lead';
      const next = nextStage(stage);
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${row[0] || ''}</strong></td>
        <td>${row[1] || ''}</td>
        <td>${row[2] || ''}</td>
        <td>${stageBadge(stage)}</td>
        <td>${row[4] ? '$' + row[4] : ''}</td>
        <td style="max-width:200px;white-space:pre-wrap;font-size:0.75rem;">${row[5] || ''}</td>
        <td style="white-space:nowrap;">
          ${next ? `<button class="btn btn-small btn-green" onclick="moveStage(${idx}, '${next}')">&#8594; ${next}</button>` : ''}
          <button class="btn btn-small btn-outline" onclick="showNoteModal(${idx})">+ Note</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch(e) { console.error('Pipeline error:', e); }
}

function showAddLeadModal() { showModal('modal-add-lead'); }

async function addLead() {
  const data = {
    name: document.getElementById('lead-name').value,
    business: document.getElementById('lead-business').value,
    source: document.getElementById('lead-source').value,
    value: document.getElementById('lead-value').value,
    notes: document.getElementById('lead-notes').value,
  };
  if (!data.name) { showToast('Name is required', 'error'); return; }

  try {
    const r = await fetch('/api/pipeline/add', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    });
    const result = await r.json();
    if (result.status === 'ok') {
      showToast('Lead added');
      closeModal('modal-add-lead');
      ['lead-name','lead-business','lead-value','lead-notes'].forEach(
        id => document.getElementById(id).value = ''
      );
      loadPipeline();
    } else {
      showToast(result.message, 'error');
    }
  } catch(e) { showToast('Error adding lead', 'error'); }
}

async function moveStage(rowIdx, newStage) {
  try {
    await fetch('/api/pipeline/update-stage', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({row: rowIdx, stage: newStage}),
    });
    showToast(`Moved to ${newStage}`);
    loadPipeline();
  } catch(e) { showToast('Error updating stage', 'error'); }
}

function showNoteModal(rowIdx) {
  document.getElementById('note-row-idx').value = rowIdx;
  document.getElementById('note-text').value = '';
  showModal('modal-add-note');
}

async function saveNote() {
  const rowIdx = document.getElementById('note-row-idx').value;
  const note = document.getElementById('note-text').value;
  if (!note) { showToast('Note is empty', 'error'); return; }

  try {
    await fetch('/api/pipeline/add-note', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({row: parseInt(rowIdx), note: note}),
    });
    showToast('Note added');
    closeModal('modal-add-note');
    loadPipeline();
  } catch(e) { showToast('Error saving note', 'error'); }
}

// ============================================================
// QUICK ACTIONS
// ============================================================

function showProposalModal() { showModal('modal-proposal'); }

async function generateProposal() {
  const data = {
    client_name: document.getElementById('prop-client').value,
    service: document.getElementById('prop-service').value,
    price: document.getElementById('prop-price').value,
    overview: document.getElementById('prop-overview').value,
    deliverables: document.getElementById('prop-deliverables').value,
  };
  if (!data.client_name) { showToast('Client name required', 'error'); return; }

  showToast('Generating PDF...');
  try {
    const r = await fetch('/api/generate-proposal', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    });
    if (r.ok) {
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `proposal_${data.client_name.replace(/\\s/g, '_').toLowerCase()}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      closeModal('modal-proposal');
      showToast('Proposal downloaded');
    } else {
      const err = await r.json();
      showToast(err.message || 'Error generating proposal', 'error');
    }
  } catch(e) { showToast('Error: ' + e.message, 'error'); }
}

async function checkHealth() {
  const card = document.getElementById('health-card');
  const output = document.getElementById('health-output');
  card.style.display = 'block';
  output.textContent = 'Running health check...';

  try {
    const r = await fetch('/api/health');
    const d = await r.json();
    output.textContent = d.output || d.message || 'No output';
  } catch(e) {
    output.textContent = 'Error: ' + e.message;
    output.style.color = 'var(--red)';
  }
}

async function viewRevenue() {
  const card = document.getElementById('revenue-card');
  const grid = document.getElementById('revenue-grid');
  const charges = document.getElementById('revenue-charges');
  card.style.display = 'block';
  grid.innerHTML = '<div class="spinner"></div> Loading Stripe data...';
  charges.innerHTML = '';

  try {
    const r = await fetch('/api/revenue');
    const d = await r.json();
    if (d.status === 'error') {
      grid.innerHTML = `<div style="color:var(--red);">${d.message}</div>`;
      return;
    }

    grid.innerHTML = `
      <div class="revenue-card">
        <div class="amount">$${d.revenue_7d.toLocaleString()}</div>
        <div class="label">Last 7 Days</div>
      </div>
      <div class="revenue-card">
        <div class="amount">$${d.revenue_30d.toLocaleString()}</div>
        <div class="label">Last 30 Days</div>
      </div>
      <div class="revenue-card">
        <div class="amount">$${d.mrr.toLocaleString()}</div>
        <div class="label">Monthly Recurring</div>
      </div>
      <div class="revenue-card">
        <div class="amount">${d.active_subs}</div>
        <div class="label">Active Subs</div>
      </div>
    `;

    (d.recent_charges || []).forEach(c => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${c.date}</td><td>$${c.amount.toFixed(2)}</td><td>${c.description}</td><td>${c.customer}</td>`;
      charges.appendChild(tr);
    });
  } catch(e) {
    grid.innerHTML = `<div style="color:var(--red);">Error: ${e.message}</div>`;
  }
}

// ============================================================
// WEEKLY SCORECARD
// ============================================================

async function loadWeeklySummary() {
  try {
    const r = await fetch('/api/weekly-summary');
    const d = await r.json();
    const tbody = document.getElementById('weekly-body');
    tbody.innerHTML = '';

    const info = await (await fetch('/api/day-info')).json();
    const currentWeek = info.week_number;

    (d.rows || []).forEach(row => {
      const weekNum = parseInt(row[0]) || 0;
      const isCurrent = weekNum === currentWeek;
      const score = row[12] || '';
      let scoreClass = '';
      if (score) {
        const s = parseInt(score);
        scoreClass = s >= 80 ? 'color:var(--green)' : s >= 60 ? 'color:var(--yellow)' : 'color:var(--red)';
      }

      const tr = document.createElement('tr');
      tr.style.background = isCurrent ? 'rgba(201,150,60,0.1)' : '';
      tr.innerHTML = `
        <td style="font-weight:${isCurrent?'700':'400'};color:${isCurrent?'var(--gold)':'inherit'}">
          ${isCurrent ? '&#9654; ' : ''}Week ${row[0] || ''}
        </td>
        <td>${row[1] || ''}</td>
        <td>${row[2] || ''}</td>
        <td>${row[3] || ''}</td>
        <td>${row[4] || ''}</td>
        <td>${row[5] || ''}</td>
        <td>${row[6] || ''}</td>
        <td>${row[7] || ''}</td>
        <td>${row[8] || ''}</td>
        <td>${row[9] || ''}</td>
        <td style="${scoreClass};font-weight:700;">${score}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch(e) { console.error('Weekly summary error:', e); }
}

async function loadGoals() {
  try {
    const r = await fetch('/api/goals');
    const d = await r.json();
    const container = document.getElementById('goals-container');
    container.innerHTML = '';

    (d.rows || []).forEach(row => {
      const goal = row[0] || '';
      const target = row[1] || '';
      const current = row[2] || '';
      const pct = row[3] || '0';
      const status = row[5] || 'Not Started';
      const statusClass = 'status-' + status.toLowerCase().replace(/\\s+/g, '-');

      // Try to extract a number for progress bar
      let pctNum = parseInt(pct) || 0;
      const color = pctNum >= 80 ? 'var(--green)' : pctNum >= 40 ? 'var(--yellow)' : 'var(--red)';

      container.innerHTML += `
        <div style="margin-bottom:16px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <span style="font-size:0.9rem;font-weight:600;">${goal}</span>
            <span class="${statusClass}" style="font-size:0.8rem;">${status}</span>
          </div>
          <div class="progress-wrap">
            <span class="progress-label">${current}</span>
            <div class="progress-bar">
              <div class="progress-fill" style="width:${pctNum}%;background:${color};"></div>
            </div>
            <span class="progress-value">${target}</span>
          </div>
        </div>
      `;
    });
  } catch(e) { console.error('Goals error:', e); }
}

// ============================================================
// CONTENT CALENDAR
// ============================================================

async function loadContentCalendar() {
  try {
    const r = await fetch('/api/content-calendar');
    const d = await r.json();
    const tbody = document.getElementById('content-body');
    tbody.innerHTML = '';

    const info = await (await fetch('/api/day-info')).json();
    const currentWeek = info.week_number;

    (d.rows || []).forEach((row, idx) => {
      const weekNum = parseInt(row[0]) || 0;
      const isCurrentWeek = weekNum === currentWeek;
      const published = (row[3] || '').toString().toUpperCase() === 'TRUE';

      const tr = document.createElement('tr');
      tr.style.background = isCurrentWeek ? 'rgba(201,150,60,0.08)' : '';
      tr.innerHTML = `
        <td style="font-weight:${isCurrentWeek?'700':'400'};color:${isCurrentWeek?'var(--gold)':'inherit'}">
          ${isCurrentWeek ? '&#9654; ' : ''}${row[0] || ''}
        </td>
        <td style="${published?'text-decoration:line-through;opacity:0.6;':''}">${row[1] || ''}</td>
        <td><span class="badge" style="background:${row[2]==='Short'?'var(--blue)':'var(--gold)'};color:#fff;">${row[2] || ''}</span></td>
        <td>
          <input type="checkbox" class="content-check" ${published?'checked':''}
            onchange="toggleContent(${idx}, '${published?'TRUE':'FALSE'}')">
        </td>
        <td>${row[4] || ''}</td>
        <td>${row[5] || ''}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch(e) { console.error('Content calendar error:', e); }
}

async function toggleContent(rowIdx, current) {
  try {
    await fetch('/api/content-calendar/toggle', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({row: rowIdx, current: current}),
    });
    showToast(current === 'TRUE' ? 'Unmarked' : 'Marked as published');
    loadContentCalendar();
  } catch(e) { showToast('Error updating content', 'error'); }
}

// ============================================================
// INIT
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  loadDayInfo();
  loadDailyLog();
  loadWeeklyProgress();
});

// Close modals on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.classList.remove('show');
  });
});
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML, sheet_id=SPREADSHEET_ID)


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    print(f"\n{'='*60}")
    print("  MARCEAU COMMAND CENTER")
    print(f"  http://127.0.0.1:{PORT}")
    print(f"{'='*60}")
    print(f"  Google Sheets: {'Connected' if GOOGLE_AVAILABLE else 'NOT AVAILABLE'}")
    print(f"  Stripe: {'Connected' if STRIPE_AVAILABLE else 'NOT AVAILABLE'}")
    print(f"  Scorecard: {SPREADSHEET_ID}")
    print(f"{'='*60}\n")

    app.run(host='127.0.0.1', port=PORT, debug=False)
