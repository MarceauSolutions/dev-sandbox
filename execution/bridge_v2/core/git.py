"""Git operations blueprint — /git/status, /git/commit, /git/push, /git/diff"""

import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request
from execution.bridge_v2.app import (
    ErrorCode, make_error, make_success, validate_path, truncate_output,
    ALLOWED_BASE_PATHS, PENDING_APPROVALS,
    track_request,
)

git_bp = Blueprint('git', __name__)


@git_bp.route('/git/status', methods=['POST'])
def git_status():
    """Get git status for a repository."""
    track_request('git/status')
    data = request.get_json() or {}
    repo_path = data.get('repo_path', ALLOWED_BASE_PATHS[0])

    # Validate path
    valid, resolved_path = validate_path(repo_path)
    if not valid:
        return make_error(
            ErrorCode.PATH_NOT_ALLOWED,
            f"Repository path not allowed: {repo_path}",
            status=403,
            context={"requested_path": repo_path}
        )

    try:
        # Check if it's a git repo
        git_dir = Path(resolved_path) / '.git'
        if not git_dir.exists():
            return make_error(
                ErrorCode.NOT_A_GIT_REPO,
                f"Not a git repository: {repo_path}",
                status=400,
                context={
                    "requested_path": repo_path,
                    "resolved_path": resolved_path,
                    "checked_for": str(git_dir)
                }
            )

        # Get branch
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )
        branch = result.stdout.strip()

        # Get status
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )

        # Parse status
        staged = []
        unstaged = []
        untracked = []

        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            status = line[:2]
            filename = line[3:]

            if status[0] == '?':
                untracked.append(filename)
            elif status[0] != ' ':
                staged.append({"file": filename, "status": status[0]})
            if status[1] != ' ' and status[1] != '?':
                unstaged.append({"file": filename, "status": status[1]})

        # Get ahead/behind
        result = subprocess.run(
            ['git', 'rev-list', '--count', '--left-right', '@{upstream}...HEAD'],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )
        ahead = 0
        behind = 0
        if result.returncode == 0:
            parts = result.stdout.strip().split()
            if len(parts) == 2:
                behind, ahead = int(parts[0]), int(parts[1])

        return jsonify({
            "success": True,
            "branch": branch,
            "clean": len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0,
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked,
            "ahead": ahead,
            "behind": behind
        })

    except subprocess.CalledProcessError as e:
        return make_error(
            ErrorCode.GIT_ERROR,
            f"Git command failed: {str(e)}",
            status=500,
            context={
                "repo_path": resolved_path,
                "stderr": e.stderr if hasattr(e, 'stderr') else None,
                "returncode": e.returncode
            }
        )
    except Exception as e:
        return make_error(
            ErrorCode.INTERNAL_ERROR,
            f"Unexpected error getting git status: {str(e)}",
            status=500,
            context={"repo_path": resolved_path, "error_type": type(e).__name__},
            include_tb=True
        )


@git_bp.route('/git/commit', methods=['POST'])
def git_commit():
    """Commit changes to git."""
    track_request('git/commit')
    data = request.get_json() or {}
    repo_path = data.get('repo_path', ALLOWED_BASE_PATHS[0])
    message = data.get('message')
    files = data.get('files', [])  # List of files or "all"
    author = data.get('author')

    if not message:
        return jsonify({"success": False, "error": "Missing 'message' parameter"}), 400

    # Validate path
    valid, resolved_path = validate_path(repo_path)
    if not valid:
        return jsonify({"success": False, "error": resolved_path}), 403

    try:
        # Add files
        if files == "all" or not files:
            result = subprocess.run(
                ['git', 'add', '-A'],
                cwd=resolved_path,
                capture_output=True,
                text=True
            )
        else:
            result = subprocess.run(
                ['git', 'add'] + files,
                cwd=resolved_path,
                capture_output=True,
                text=True
            )

        if result.returncode != 0:
            return jsonify({
                "success": False,
                "error": f"Failed to stage files: {result.stderr}"
            }), 400

        # Commit
        commit_cmd = ['git', 'commit', '-m', message]
        if author:
            commit_cmd.extend(['--author', author])

        result = subprocess.run(
            commit_cmd,
            cwd=resolved_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({
                "success": False,
                "error": f"Commit failed: {result.stderr}"
            }), 400

        # Get commit hash
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )
        commit_hash = result.stdout.strip()

        return jsonify({
            "success": True,
            "commit_hash": commit_hash,
            "message": message
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@git_bp.route('/git/push', methods=['POST'])
def git_push():
    """Push to remote repository."""
    track_request('git/push')
    data = request.get_json() or {}
    repo_path = data.get('repo_path', ALLOWED_BASE_PATHS[0])
    remote = data.get('remote', 'origin')
    branch = data.get('branch')
    force = data.get('force', False)
    approval_id = data.get('approval_id')

    # Validate path
    valid, resolved_path = validate_path(repo_path)
    if not valid:
        return jsonify({"success": False, "error": resolved_path}), 403

    # Force push requires approval
    if force and not approval_id:
        approval_id = str(uuid.uuid4())
        PENDING_APPROVALS[approval_id] = {
            "id": approval_id,
            "type": "git_push_force",
            "repo_path": resolved_path,
            "remote": remote,
            "branch": branch,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        return jsonify({
            "success": False,
            "approval_required": True,
            "approval_id": approval_id,
            "message": "Approval required for force push"
        }), 202

    # Verify approval if provided
    if approval_id:
        approval = PENDING_APPROVALS.get(approval_id)
        if not approval or approval.get('status') != 'approved':
            return jsonify({
                "success": False,
                "error": "Invalid or unapproved approval_id"
            }), 403

    try:
        # Get current branch if not specified
        if not branch:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=resolved_path,
                capture_output=True,
                text=True
            )
            branch = result.stdout.strip()

        # Push
        push_cmd = ['git', 'push', remote, branch]
        if force:
            push_cmd.insert(2, '--force')

        result = subprocess.run(
            push_cmd,
            cwd=resolved_path,
            capture_output=True,
            text=True
        )

        # Clean up approval
        if approval_id and approval_id in PENDING_APPROVALS:
            del PENDING_APPROVALS[approval_id]

        if result.returncode != 0:
            return jsonify({
                "success": False,
                "error": f"Push failed: {result.stderr}"
            }), 400

        return jsonify({
            "success": True,
            "pushed_to": f"{remote}/{branch}",
            "output": result.stdout + result.stderr
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@git_bp.route('/git/diff', methods=['POST'])
def git_diff():
    """Get git diff."""
    track_request('git/diff')
    data = request.get_json() or {}
    repo_path = data.get('repo_path', ALLOWED_BASE_PATHS[0])
    base = data.get('base', 'HEAD')
    head = data.get('head', '')

    # Validate path
    valid, resolved_path = validate_path(repo_path)
    if not valid:
        return jsonify({"success": False, "error": resolved_path}), 403

    try:
        # Get diff
        if head:
            diff_cmd = ['git', 'diff', base, head]
        else:
            diff_cmd = ['git', 'diff', base]

        result = subprocess.run(
            diff_cmd,
            cwd=resolved_path,
            capture_output=True,
            text=True
        )

        # Count files changed
        result_stat = subprocess.run(
            diff_cmd + ['--stat'],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )

        # Parse file count from stat
        stat_lines = result_stat.stdout.strip().split('\n')
        files_changed = len([l for l in stat_lines if '|' in l])

        diff_output, truncated = truncate_output(result.stdout)

        return jsonify({
            "success": True,
            "diff": diff_output,
            "files_changed": files_changed,
            "truncated": truncated
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
