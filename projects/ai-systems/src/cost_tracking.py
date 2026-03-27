"""
AI Systems Tower - Token Cost Tracking And Budget Management

Token cost tracking and budget management.
Extracted from monolithic agent_bridge_api.py, refactored into Flask blueprint.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify

from .models import (
    SESSION_COSTS,
    SessionCost,
    PRICING,
    get_or_create_session_cost,
)

cost_tracking_bp = Blueprint('cost_tracking', __name__)


@cost_tracking_bp.route('/cost/track', methods=['POST'])
def cost_track():
    """Track token usage for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    input_tokens = data.get('input_tokens', 0)
    output_tokens = data.get('output_tokens', 0)
    model = data.get('model', 'claude-sonnet-4-5-20250929')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id' parameter"}), 400

    session_cost = get_or_create_session_cost(session_id, model)
    session_cost.add_usage(input_tokens, output_tokens)

    return jsonify({
        "success": True,
        **session_cost.to_dict()
    })


@cost_tracking_bp.route('/cost/session', methods=['POST'])
def cost_session():
    """Get cost information for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id' parameter"}), 400

    if session_id not in SESSION_COSTS:
        return jsonify({
            "success": True,
            "found": False,
            "session_id": session_id
        })

    return jsonify({
        "success": True,
        "found": True,
        **SESSION_COSTS[session_id].to_dict()
    })


@cost_tracking_bp.route('/cost/all', methods=['GET', 'POST'])
def cost_all():
    """Get cost information for all sessions."""
    sessions = [s.to_dict() for s in SESSION_COSTS.values()]
    total_cost = sum(s.calculate_cost() for s in SESSION_COSTS.values())
    total_tokens = sum(s.input_tokens + s.output_tokens for s in SESSION_COSTS.values())

    return jsonify({
        "success": True,
        "session_count": len(sessions),
        "total_cost_usd": round(total_cost, 4),
        "total_tokens": total_tokens,
        "sessions": sessions
    })


@cost_tracking_bp.route('/cost/set_budget', methods=['POST'])
def cost_set_budget():
    """Set a budget limit for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    budget = data.get('budget')  # In USD

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id' parameter"}), 400

    if budget is not None and budget <= 0:
        return jsonify({"success": False, "error": "Budget must be positive"}), 400

    session_cost = get_or_create_session_cost(session_id)
    session_cost.budget_limit = budget

    return jsonify({
        "success": True,
        **session_cost.to_dict()
    })


@cost_tracking_bp.route('/cost/pricing', methods=['GET', 'POST'])
def cost_pricing():
    """Get current pricing information."""
    return jsonify({
        "success": True,
        "pricing": PRICING,
        "note": "Prices are per million tokens in USD"
    })
