#!/usr/bin/env python3
"""
Bridge v2 — Modular Flask API for n8n and agent operations.

Structured replacement for the monolithic agent_bridge_api.py (13,257 lines).
Same capabilities, organized by tower and function.

Architecture:
  app.py          — Shared infrastructure (Flask app, config, helpers, health)
  core/           — Shared endpoint groups used by multiple towers
  towers/         — Tower-specific endpoint groups
  middleware/     — Shared middleware (cache, rate limiting)

Usage:
    python -m execution.bridge_v2.app --port 5011
"""

import argparse
import os
import subprocess
import sys
import time
import traceback
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from flask import Flask, jsonify, request
from flask_cors import CORS


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_PORT = 5011
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_OUTPUT_SIZE = 100 * 1024  # 100KB
COMMAND_TIMEOUT = 120  # 2 minutes

ALLOWED_BASE_PATHS = [
    "/Users/williammarceaujr./dev-sandbox",
    "/Users/williammarceaujr./production",
    "/tmp",
    "/home/ec2-user/dev-sandbox",
    "/home/ec2-user",
    "/home/clawdbot/dev-sandbox",
]

SERVER_START_TIME = time.time()


# =============================================================================
# Error Handling
# =============================================================================

class ErrorCode(Enum):
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    INVALID_PATH = "INVALID_PATH"
    PATH_NOT_ALLOWED = "PATH_NOT_ALLOWED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_INVALID = "APPROVAL_INVALID"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    DIRECTORY_NOT_FOUND = "DIRECTORY_NOT_FOUND"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    NOT_A_FILE = "NOT_A_FILE"
    NOT_A_DIRECTORY = "NOT_A_DIRECTORY"
    FILE_EXISTS = "FILE_EXISTS"
    NOT_A_GIT_REPO = "NOT_A_GIT_REPO"
    COMMAND_TIMEOUT = "COMMAND_TIMEOUT"
    SEARCH_TIMEOUT = "SEARCH_TIMEOUT"
    REQUEST_TIMEOUT = "REQUEST_TIMEOUT"
    ENCODING_ERROR = "ENCODING_ERROR"
    GIT_ERROR = "GIT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def make_error(
    code: ErrorCode, message: str, status: int = 400,
    context: Optional[Dict] = None, include_tb: bool = False
) -> Tuple[Dict, int]:
    """Structured error response."""
    resp = {
        "success": False,
        "error": {"code": code.value, "message": message},
        "error_message": message,  # backwards compat
    }
    if context:
        resp["error"]["context"] = context
    if include_tb:
        resp["error"]["traceback"] = traceback.format_exc()
    return jsonify(resp), status


def make_success(data: Dict[str, Any], message: Optional[str] = None):
    """Structured success response."""
    resp = {"success": True, **data}
    if message:
        resp["message"] = message
    return jsonify(resp)


# =============================================================================
# Shared Helpers
# =============================================================================

def validate_path(path: str) -> Tuple[bool, str]:
    """Validate that a path is within allowed directories."""
    try:
        resolved = str(Path(path).resolve())
        for base in ALLOWED_BASE_PATHS:
            if resolved.startswith(base):
                return True, resolved
        return False, f"Path not in allowed directories: {resolved}"
    except Exception as e:
        return False, f"Invalid path: {e}"


def truncate_output(output: str, max_size: int = MAX_OUTPUT_SIZE) -> Tuple[str, bool]:
    """Truncate output if too large."""
    if len(output) > max_size:
        return output[:max_size] + f"\n\n... [TRUNCATED - {len(output)} total bytes]", True
    return output, False


# Shared state
PENDING_APPROVALS: Dict[str, Dict] = {}
METRICS: Dict[str, Any] = {"requests": 0, "errors": 0, "by_endpoint": {}}


def track_request(endpoint: str):
    """Track a request in metrics."""
    METRICS["requests"] += 1
    METRICS["by_endpoint"][endpoint] = METRICS["by_endpoint"].get(endpoint, 0) + 1


# =============================================================================
# Flask App + Blueprint Registration
# =============================================================================

def create_app():
    """Create and configure the Flask app with all blueprints."""
    app = Flask(__name__)
    CORS(app)

    # Register core blueprints
    from execution.bridge_v2.core.command import command_bp
    from execution.bridge_v2.core.files import files_bp
    from execution.bridge_v2.core.git import git_bp
    from execution.bridge_v2.core.search import search_bp
    from execution.bridge_v2.core.web import web_bp
    from execution.bridge_v2.core.pipeline import pipeline_bp

    app.register_blueprint(command_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(git_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(pipeline_bp)

    # Health endpoint
    @app.route('/health', methods=['GET'])
    def health():
        uptime = time.time() - SERVER_START_TIME
        return jsonify({
            "status": "healthy",
            "version": "2.0.0",
            "uptime_seconds": int(uptime),
            "pending_approvals": len(PENDING_APPROVALS),
            "metrics": METRICS,
        })

    # Metrics endpoint
    @app.route('/metrics', methods=['GET', 'POST'])
    def metrics():
        return jsonify(METRICS)

    return app


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()

    app = create_app()
    print(f"Bridge v2 starting on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)
