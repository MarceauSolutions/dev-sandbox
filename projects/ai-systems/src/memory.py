"""
AI Systems Tower - Conversation Memory Management

Conversation memory management.
Extracted from monolithic agent_bridge_api.py, refactored into Flask blueprint.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify

from .models import (
    CONVERSATION_MEMORIES,
    ConversationMemory,
    get_or_create_memory,
)

memory_bp = Blueprint('memory', __name__)


@memory_bp.route('/memory/add', methods=['POST'])
def memory_add():
    """Add a message to conversation memory."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    role = data.get('role', 'user')
    content = data.get('content')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id' parameter"}), 400
    if not content:
        return jsonify({"success": False, "error": "Missing 'content' parameter"}), 400

    memory = get_or_create_memory(session_id)
    memory.add_message(role, content)

    return jsonify({
        "success": True,
        "session_id": session_id,
        "message_count": len(memory.messages)
    })


@memory_bp.route('/memory/get', methods=['POST'])
def memory_get():
    """Get conversation memory for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    last_n = data.get('last_n', 10)

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id' parameter"}), 400

    if session_id not in CONVERSATION_MEMORIES:
        return jsonify({
            "success": True,
            "session_id": session_id,
            "messages": [],
            "message_count": 0
        })

    memory = CONVERSATION_MEMORIES[session_id]
    return jsonify({
        "success": True,
        **memory.to_dict(),
        "context": memory.get_context(last_n)
    })


@memory_bp.route('/memory/summarize', methods=['POST'])
def memory_summarize():
    """Set a summary for conversation memory."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    summary = data.get('summary')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id' parameter"}), 400

    memory = get_or_create_memory(session_id)
    memory.summary = summary
    memory.updated_at = datetime.now().isoformat()

    return jsonify({
        "success": True,
        "session_id": session_id,
        "summary": summary
    })


@memory_bp.route('/memory/list', methods=['GET', 'POST'])
def memory_list():
    """List all conversation memories."""
    memories = []
    for session_id, memory in CONVERSATION_MEMORIES.items():
        memories.append({
            "session_id": session_id,
            "message_count": len(memory.messages),
            "created_at": memory.created_at,
            "updated_at": memory.updated_at,
            "has_summary": memory.summary is not None
        })

    return jsonify({
        "success": True,
        "memories": memories,
        "total": len(memories)
    })


@memory_bp.route('/memory/clear', methods=['POST'])
def memory_clear():
    """Clear conversation memory for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id' parameter"}), 400

    if session_id in CONVERSATION_MEMORIES:
        del CONVERSATION_MEMORIES[session_id]
        return jsonify({"success": True, "cleared": True})

    return jsonify({"success": True, "cleared": False, "message": "Memory not found"})
