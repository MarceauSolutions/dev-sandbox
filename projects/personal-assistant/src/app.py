#!/usr/bin/env python3
"""
Personal Assistant Tower - Flask API Server

Independent Flask app exposing Gmail, Sheets, and SMS endpoints.
Extracted from monolithic agent_bridge_api.py for tower independence.

Run: python -m projects.personal_assistant.src.app
Port: 5011 (avoids conflict with monolith on 5010)
"""

import os
import logging
from flask import Flask, Blueprint, request, jsonify

from . import gmail_api
from . import sheets_api
from . import sms_api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # --- Gmail Blueprint ---
    gmail_bp = Blueprint('gmail', __name__, url_prefix='/gmail')

    @gmail_bp.route('/list', methods=['POST'])
    def gmail_list():
        data = request.get_json() or {}
        return jsonify(gmail_api.list_emails(
            max_results=data.get('max_results', 10),
            query=data.get('query', ''),
            label_ids=data.get('label_ids')
        ))

    @gmail_bp.route('/read', methods=['POST'])
    def gmail_read():
        data = request.get_json() or {}
        message_id = data.get('message_id')
        if not message_id:
            return jsonify({"success": False, "error": "message_id is required"}), 400
        return jsonify(gmail_api.read_email(message_id))

    @gmail_bp.route('/send', methods=['POST'])
    def gmail_send():
        data = request.get_json() or {}
        to = data.get('to')
        if not to:
            return jsonify({"success": False, "error": "to is required"}), 400
        return jsonify(gmail_api.send_email(
            to=to, subject=data.get('subject', ''),
            body=data.get('body', ''), cc=data.get('cc', ''), bcc=data.get('bcc', '')
        ))

    @gmail_bp.route('/draft', methods=['POST'])
    def gmail_draft():
        data = request.get_json() or {}
        to = data.get('to')
        if not to:
            return jsonify({"success": False, "error": "to is required"}), 400
        return jsonify(gmail_api.create_draft(
            to=to, subject=data.get('subject', ''),
            body=data.get('body', ''), cc=data.get('cc', ''), bcc=data.get('bcc', '')
        ))

    @gmail_bp.route('/search', methods=['POST'])
    def gmail_search():
        data = request.get_json() or {}
        return jsonify(gmail_api.search_emails(
            query=data.get('query', ''), max_results=data.get('max_results', 20)
        ))

    @gmail_bp.route('/search-all', methods=['POST'])
    def gmail_search_all():
        data = request.get_json() or {}
        return jsonify(gmail_api.search_all_accounts(
            query=data.get('query', ''), accounts=data.get('accounts', 'all'),
            max_results=data.get('max_results', 10)
        ))

    # --- Sheets Blueprint ---
    sheets_bp = Blueprint('sheets', __name__, url_prefix='/sheets')

    @sheets_bp.route('/read', methods=['POST'])
    def sheets_read():
        data = request.get_json() or {}
        return jsonify(sheets_api.read_sheet(
            spreadsheet_id=data.get('spreadsheet_id'),
            range_name=data.get('range', 'Sheet1!A1:Z100')
        ))

    @sheets_bp.route('/write', methods=['POST'])
    def sheets_write():
        data = request.get_json() or {}
        values = data.get('values', [])
        if not values:
            return jsonify({"success": False, "error": "values is required"}), 400
        return jsonify(sheets_api.write_sheet(
            values=values, spreadsheet_id=data.get('spreadsheet_id'),
            range_name=data.get('range', 'Sheet1!A1')
        ))

    @sheets_bp.route('/append', methods=['POST'])
    def sheets_append():
        data = request.get_json() or {}
        return jsonify(sheets_api.append_sheet(
            values=data.get('values', []), spreadsheet_id=data.get('spreadsheet_id'),
            range_name=data.get('range', 'Sheet1!A1')
        ))

    # --- SMS Blueprint ---
    sms_bp = Blueprint('sms', __name__, url_prefix='/sms')

    @sms_bp.route('/send', methods=['POST'])
    def sms_send():
        data = request.get_json() or {}
        to = data.get('to')
        body = data.get('body', '')
        if not to:
            return jsonify({"success": False, "error": "to is required"}), 400
        if not body:
            return jsonify({"success": False, "error": "body is required"}), 400
        return jsonify(sms_api.send_sms(to=to, body=body, from_number=data.get('from')))

    @sms_bp.route('/list', methods=['POST'])
    def sms_list():
        data = request.get_json() or {}
        return jsonify(sms_api.list_sms(
            limit=data.get('limit', 20), direction=data.get('direction')
        ))

    # --- Scheduler Blueprint (for Clawdbot integration) ---
    scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/scheduler')

    @scheduler_bp.route('/today', methods=['GET'])
    def scheduler_today():
        """Get today's proposed schedule. Clawdbot calls this for 'What's my schedule?'"""
        from .daily_scheduler import generate_proposed_schedule, format_for_digest
        is_post_april6 = __import__('datetime').datetime.now() >= __import__('datetime').datetime(2026, 4, 6)
        schedule = generate_proposed_schedule(post_april_6=is_post_april6)
        return jsonify({
            "success": True,
            "schedule": schedule,
            "formatted": format_for_digest(schedule),
        })

    @scheduler_bp.route('/approve', methods=['POST'])
    def scheduler_approve():
        """Approve pending schedule → create calendar blocks.
        Clawdbot calls this when William says 'yes schedule' in Telegram."""
        from .daily_scheduler import create_approved_blocks
        result = create_approved_blocks()
        return jsonify({"success": True, **result})

    @scheduler_bp.route('/digest', methods=['GET'])
    def scheduler_digest():
        """Get the morning digest. Clawdbot calls this for 'morning briefing'."""
        from .unified_morning_digest import generate_digest
        message = generate_digest(hours_back=12, preview=True)
        return jsonify({"success": True, "digest": message})

    @scheduler_bp.route('/health-check', methods=['GET'])
    def scheduler_health():
        """Get system health. Clawdbot calls this for 'system status'."""
        from .system_health_check import run_all_checks
        return jsonify(run_all_checks())

    # --- Health ---
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            "tower": "personal-assistant",
            "status": "healthy",
            "version": "1.1.0",
            "endpoints": {
                "gmail": ["/gmail/list", "/gmail/read", "/gmail/send", "/gmail/draft", "/gmail/search", "/gmail/search-all"],
                "sheets": ["/sheets/read", "/sheets/write", "/sheets/append"],
                "sms": ["/sms/send", "/sms/list"]
            }
        })

    app.register_blueprint(gmail_bp)
    app.register_blueprint(sheets_bp)
    app.register_blueprint(sms_bp)
    app.register_blueprint(scheduler_bp)

    return app


if __name__ == '__main__':
    port = int(os.getenv('PA_TOWER_PORT', 5011))
    logger.info(f"Personal Assistant Tower starting on port {port}")
    application = create_app()
    application.run(host='0.0.0.0', port=port, debug=False)
