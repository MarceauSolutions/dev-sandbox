"""Command execution blueprint — /command/execute"""

import os
import subprocess
import time
import uuid

from flask import Blueprint, jsonify, request
from execution.bridge_v2.app import (
    ErrorCode, make_error, make_success, validate_path, truncate_output,
    ALLOWED_BASE_PATHS, COMMAND_TIMEOUT, MAX_OUTPUT_SIZE, PENDING_APPROVALS,
    track_request,
)

command_bp = Blueprint('command', __name__)


@command_bp.route('/command/execute', methods=['POST'])
def execute():
    """Execute a bash command."""
    track_request('command/execute')
    data = request.get_json() or {}
    command = data.get('command')
    cwd = data.get('cwd', ALLOWED_BASE_PATHS[0])
    timeout = min(data.get('timeout', COMMAND_TIMEOUT), 300)
    env = data.get('env', {})
    require_approval = data.get('require_approval', False)
    approval_id = data.get('approval_id')

    if not command:
        return make_error(ErrorCode.MISSING_PARAMETER, "Missing 'command' parameter")

    valid, resolved_cwd = validate_path(cwd)
    if not valid:
        return make_error(ErrorCode.PATH_NOT_ALLOWED, f"Working directory not allowed: {cwd}", 403)

    # Dangerous command check
    dangerous_patterns = [
        'rm -rf /', 'rm -rf ~', 'rm -rf *', 'mkfs', 'dd if=',
        ':(){', 'chmod -R 777 /', '> /dev/sda',
    ]
    matched = [p for p in dangerous_patterns if p in command.lower()]

    if (matched or require_approval) and not approval_id:
        aid = str(uuid.uuid4())
        PENDING_APPROVALS[aid] = {
            "id": aid, "type": "command", "command": command,
            "cwd": resolved_cwd, "created_at": time.time(),
            "status": "pending", "matched_patterns": matched,
        }
        return jsonify({
            "success": False, "approval_required": True, "approval_id": aid,
            "dangerous": bool(matched), "matched_patterns": matched,
            "message": f"Approval required for: {command}",
        }), 202

    if approval_id:
        approval = PENDING_APPROVALS.get(approval_id)
        if not approval or approval.get('status') != 'approved':
            return make_error(ErrorCode.APPROVAL_INVALID, "Invalid or unapproved approval", 403)

    try:
        full_env = os.environ.copy()
        full_env.update(env)

        start = time.time()
        result = subprocess.run(
            command, shell=True, cwd=resolved_cwd, env=full_env,
            capture_output=True, timeout=timeout, text=True,
        )
        duration_ms = int((time.time() - start) * 1000)

        stdout, stdout_trunc = truncate_output(result.stdout)
        stderr, stderr_trunc = truncate_output(result.stderr)

        if approval_id and approval_id in PENDING_APPROVALS:
            del PENDING_APPROVALS[approval_id]

        resp = {
            "success": True,
            "command_success": result.returncode == 0,
            "stdout": stdout, "stderr": stderr,
            "exit_code": result.returncode,
            "duration_ms": duration_ms,
            "cwd": resolved_cwd,
            "truncated": stdout_trunc or stderr_trunc,
        }
        if result.returncode != 0:
            resp["command_error"] = {
                "exit_code": result.returncode,
                "stderr_preview": stderr[:500] if stderr else None,
            }
        return jsonify(resp)

    except subprocess.TimeoutExpired:
        return make_error(ErrorCode.COMMAND_TIMEOUT, f"Timed out after {timeout}s", 504)
    except FileNotFoundError:
        return make_error(ErrorCode.DIRECTORY_NOT_FOUND, f"Directory not found: {resolved_cwd}", 404)
    except PermissionError:
        return make_error(ErrorCode.PATH_NOT_ALLOWED, f"Permission denied: {resolved_cwd}", 403)
    except Exception as e:
        return make_error(ErrorCode.INTERNAL_ERROR, str(e), 500, include_tb=True)


@command_bp.route('/approvals/pending', methods=['GET'])
def approvals_pending():
    """List pending approvals."""
    return jsonify({"approvals": list(PENDING_APPROVALS.values())})


@command_bp.route('/approvals/decide', methods=['POST'])
def approvals_decide():
    """Approve or deny a pending action."""
    data = request.get_json() or {}
    aid = data.get('approval_id')
    decision = data.get('decision')

    if not aid or not decision:
        return make_error(ErrorCode.MISSING_PARAMETER, "Need approval_id and decision")

    approval = PENDING_APPROVALS.get(aid)
    if not approval:
        return make_error(ErrorCode.APPROVAL_INVALID, f"Approval not found: {aid}", 404)

    approval['status'] = decision
    return make_success({"approval_id": aid, "status": decision})
