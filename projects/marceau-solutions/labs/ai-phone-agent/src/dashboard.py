#!/usr/bin/env python3.11
"""
Warm Leads Dashboard — SQLite-backed.

Reads lead data from the same `phone_agent.db` that `app.py` writes to.
ElevenLabs poller transcripts arrive via `app.py:/elevenlabs-poll/sync` and
land here via the shared DB — no separate file store, no JSON race.

Deployment: leads.marceausolutions.com (gunicorn — see gunicorn_conf.py)
Port: 8796
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import db

app = Flask(__name__)
CORS(app)


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'Warm Leads Dashboard'})


@app.route('/')
def dashboard():
    leads = db.list_leads()
    return render_template_string(DASHBOARD_HTML, leads=leads, now=datetime.now())


@app.route('/api/leads', methods=['GET'])
def get_leads():
    status = request.args.get('status')
    source = request.args.get('source')
    leads = db.list_leads(status=status, source=source)
    return jsonify({'leads': leads, 'count': len(leads)})


@app.route('/api/leads', methods=['POST'])
def add_lead():
    """Add a new lead (called by webhook). Backward-compatible JSON shape."""
    data = request.json or {}
    lead = db.insert_lead(data)
    return jsonify({'status': 'created', 'lead': lead})


@app.route('/api/leads/<int:lead_id>', methods=['PATCH'])
def update_lead(lead_id):
    data = request.json or {}
    lead = db.update_lead(lead_id, data)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    return jsonify({'status': 'updated', 'lead': lead})


@app.route('/api/leads/<int:lead_id>/contacted', methods=['POST'])
def mark_contacted(lead_id):
    lead = db.update_lead(lead_id, {'contacted': True, 'status': 'contacted'})
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    return jsonify({'status': 'updated', 'lead': lead})


@app.route('/api/leads/by-conversation/<conv_id>', methods=['GET', 'PATCH'])
def lead_by_conversation(conv_id):
    """Look up or upsert a lead by ElevenLabs conversation_id."""
    if request.method == 'PATCH':
        data = request.json or {}
        lead = db.upsert_lead_by_conversation(conv_id, data)
        return jsonify({'status': 'upserted', 'lead': lead})

    lead = db.find_lead_by_conversation(conv_id)
    if not lead:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'lead': lead})


DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Warm Leads | Marceau Solutions</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a; color: #fff; padding: 20px; min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { font-size: 1.8rem; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }
        .subtitle { color: #888; margin-bottom: 30px; }

        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .stat-card { background: #1a1a1a; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #333; }
        .stat-value { font-size: 2.5rem; font-weight: bold; }
        .stat-label { color: #888; font-size: 0.85rem; margin-top: 5px; }
        .stat-card.warm .stat-value { color: #f59e0b; }
        .stat-card.hot .stat-value { color: #ef4444; }
        .stat-card.contacted .stat-value { color: #22c55e; }

        .leads-table { width: 100%; border-collapse: collapse; background: #1a1a1a; border-radius: 12px; overflow: hidden; }
        .leads-table th, .leads-table td { padding: 15px; text-align: left; border-bottom: 1px solid #333; }
        .leads-table th { background: #222; color: #888; font-weight: 500; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 1px; }
        .leads-table tr:hover { background: #222; }

        .status { padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 500; }
        .status-warm_lead { background: #f59e0b22; color: #f59e0b; }
        .status-hot_lead { background: #ef444422; color: #ef4444; }
        .status-contacted { background: #22c55e22; color: #22c55e; }
        .status-voicemail_lead { background: #8b5cf622; color: #8b5cf6; }
        .status-short_call { background: #6b728022; color: #6b7280; }
        .status-new { background: #3b82f622; color: #3b82f6; }

        .source { color: #888; font-size: 0.85rem; }
        .phone { font-family: monospace; }
        .pain-points { max-width: 300px; font-size: 0.9rem; color: #ccc; }
        .conv { font-family: monospace; color: #666; font-size: 0.75rem; }

        .btn { padding: 8px 16px; border-radius: 8px; border: none; cursor: pointer; font-size: 0.85rem; }
        .btn-primary { background: #3b82f6; color: white; }
        .btn-success { background: #22c55e; color: white; }
        .btn:hover { opacity: 0.9; }

        .empty { text-align: center; padding: 60px; color: #666; }
        .timestamp { color: #666; font-size: 0.8rem; }

        @media (max-width: 768px) {
            .leads-table { display: block; overflow-x: auto; }
            .stats { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Warm Leads</h1>
        <p class="subtitle">Inbound leads from AI phone agent | Last updated: {{ now.strftime('%Y-%m-%d %H:%M') }}</p>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ leads|length }}</div>
                <div class="stat-label">Total Leads</div>
            </div>
            <div class="stat-card warm">
                <div class="stat-value">{{ leads|selectattr('status', 'eq', 'warm_lead')|list|length }}</div>
                <div class="stat-label">Warm</div>
            </div>
            <div class="stat-card hot">
                <div class="stat-value">{{ leads|selectattr('status', 'eq', 'hot_lead')|list|length }}</div>
                <div class="stat-label">Hot</div>
            </div>
            <div class="stat-card contacted">
                <div class="stat-value">{{ leads|selectattr('contacted', 'eq', true)|list|length }}</div>
                <div class="stat-label">Contacted</div>
            </div>
        </div>

        {% if leads %}
        <table class="leads-table">
            <thead>
                <tr>
                    <th>Phone</th>
                    <th>Business</th>
                    <th>Pain Points</th>
                    <th>Source</th>
                    <th>Status</th>
                    <th>Conv. ID</th>
                    <th>Time</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for lead in leads %}
                <tr>
                    <td class="phone">{{ lead.phone }}</td>
                    <td>{{ lead.business_type or '-' }}</td>
                    <td class="pain-points">{{ (lead.pain_points or '')[:100] }}{% if lead.pain_points and lead.pain_points|length > 100 %}...{% endif %}</td>
                    <td class="source">{{ lead.source }}</td>
                    <td><span class="status status-{{ lead.status }}">{{ lead.status.replace('_', ' ').title() }}</span></td>
                    <td class="conv">{{ (lead.conversation_id or '')[:8] }}</td>
                    <td class="timestamp">{{ lead.created_at[:16].replace('T', ' ') }}</td>
                    <td>
                        {% if not lead.contacted %}
                        <button class="btn btn-success" onclick="markContacted({{ lead.id }})">Called</button>
                        {% else %}
                        <span style="color: #22c55e;">Done</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty">
            <p>No leads yet. When someone calls (855) 239-9364, they'll appear here.</p>
        </div>
        {% endif %}
    </div>

    <script>
        async function markContacted(leadId) {
            const resp = await fetch(`/api/leads/${leadId}/contacted`, { method: 'POST' });
            if (resp.ok) location.reload();
        }
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
'''


if __name__ == '__main__':
    print('[dev] Warm Leads Dashboard starting on port 8796 (Flask dev server)')
    print('  ⚠  In production use: gunicorn -c gunicorn_conf.py dashboard:app')
    app.run(host='0.0.0.0', port=8796, debug=False)
