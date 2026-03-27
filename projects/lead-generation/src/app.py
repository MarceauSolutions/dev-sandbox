#!/usr/bin/env python3
"""
Lead Generation Tower - Flask API Server

Independent Flask app exposing ClickUp CRM and Sales Pipeline endpoints.
Extracted from monolithic agent_bridge_api.py for tower independence.

Run: python -m projects.lead_generation.src.app
Port: 5012 (avoids conflict with monolith on 5010, PA on 5011)
"""

import os
import logging
from flask import Flask, Blueprint, request, jsonify

from . import clickup_api
from . import pipeline_api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # --- ClickUp CRM Blueprint ---
    clickup_bp = Blueprint('clickup', __name__, url_prefix='/clickup')

    @clickup_bp.route('/list-tasks', methods=['POST'])
    def clickup_list_tasks():
        data = request.get_json() or {}
        return jsonify(clickup_api.list_tasks(list_id=data.get('list_id')))

    @clickup_bp.route('/create-task', methods=['POST'])
    def clickup_create_task():
        data = request.get_json() or {}
        name = data.get('name')
        if not name:
            return jsonify({"success": False, "error": "name is required"}), 400
        return jsonify(clickup_api.create_task(
            name=name, description=data.get('description', ''),
            list_id=data.get('list_id')
        ))

    @clickup_bp.route('/update-task', methods=['POST'])
    def clickup_update_task():
        data = request.get_json() or {}
        task_id = data.get('task_id')
        if not task_id:
            return jsonify({"success": False, "error": "task_id is required"}), 400
        fields = {k: v for k, v in data.items() if k != 'task_id'}
        return jsonify(clickup_api.update_task(task_id=task_id, **fields))

    # --- Sales Pipeline Blueprint ---
    pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/pipeline')

    @pipeline_bp.route('/stats', methods=['GET'])
    def pipeline_stats():
        tower = request.args.get('tower')
        return jsonify(pipeline_api.get_stats(tower=tower))

    @pipeline_bp.route('/deals', methods=['GET'])
    def pipeline_deals():
        return jsonify(pipeline_api.list_deals(
            tower=request.args.get('tower'), stage=request.args.get('stage')
        ))

    @pipeline_bp.route('/deal/add', methods=['POST'])
    def pipeline_add_deal():
        body = request.json or {}
        company = body.pop("company", "").strip()
        if not company:
            return jsonify({"ok": False, "error": "company required"}), 400
        tower = body.pop("tower", "digital-ai-services")
        return jsonify(pipeline_api.add_deal(company=company, tower=tower, **body))

    @pipeline_bp.route('/deal/update', methods=['POST'])
    def pipeline_update_deal():
        body = request.json or {}
        deal_id = body.pop("deal_id", None)
        if not deal_id:
            return jsonify({"ok": False, "error": "deal_id required"}), 400
        return jsonify(pipeline_api.update_deal(deal_id=int(deal_id), **body))

    @pipeline_bp.route('/outreach/log', methods=['POST'])
    def pipeline_log_outreach():
        body = request.json or {}
        return jsonify(pipeline_api.log_outreach(
            company=body.get("company", ""), channel=body.get("channel", "Email"),
            message=body.get("message", ""), response=body.get("response", ""),
            follow_up_date=body.get("follow_up_date"), deal_id=body.get("deal_id"),
            tower=body.get("tower", "digital-ai-services"),
            lead_source=body.get("lead_source", ""),
        ))

    @pipeline_bp.route('/trial/log', methods=['POST'])
    def pipeline_log_trial():
        body = request.json or {}
        deal_id = body.get("deal_id")
        if not deal_id:
            return jsonify({"ok": False, "error": "deal_id required"}), 400
        return jsonify(pipeline_api.log_trial_day(
            deal_id=int(deal_id),
            missed_calls=body.get("missed_calls", 0),
            texts_sent=body.get("texts_sent", 0),
            replies=body.get("replies", 0),
            calls_recovered=body.get("calls_recovered", 0),
            revenue_recovered=float(body.get("revenue_recovered", 0)),
            notes=body.get("notes", ""),
        ))

    @pipeline_bp.route('/trial/summary', methods=['GET'])
    def pipeline_trial_summary():
        deal_id = request.args.get("deal_id")
        if not deal_id:
            return jsonify({"ok": False, "error": "deal_id required"}), 400
        return jsonify(pipeline_api.get_trial_summary(deal_id=int(deal_id)))

    @pipeline_bp.route('/followups', methods=['GET'])
    def pipeline_followups():
        return jsonify(pipeline_api.get_followups_due(tower=request.args.get("tower")))

    # --- Health ---
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            "tower": "lead-generation",
            "status": "healthy",
            "version": "1.1.0",
            "endpoints": {
                "clickup": ["/clickup/list-tasks", "/clickup/create-task", "/clickup/update-task"],
                "pipeline": [
                    "/pipeline/stats", "/pipeline/deals", "/pipeline/deal/add",
                    "/pipeline/deal/update", "/pipeline/outreach/log",
                    "/pipeline/trial/log", "/pipeline/trial/summary", "/pipeline/followups"
                ]
            }
        })

    app.register_blueprint(clickup_bp)
    app.register_blueprint(pipeline_bp)

    return app


if __name__ == '__main__':
    port = int(os.getenv('LG_TOWER_PORT', 5012))
    logger.info(f"Lead Generation Tower starting on port {port}")
    application = create_app()
    application.run(host='0.0.0.0', port=port, debug=False)
