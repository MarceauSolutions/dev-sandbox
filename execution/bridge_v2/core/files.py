"""File operations blueprint — /files/read, /files/write, /files/edit, /files/list, /files/glob, /files/delete"""

import uuid
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request
from execution.bridge_v2.app import (
    ErrorCode, make_error, make_success, validate_path, truncate_output,
    ALLOWED_BASE_PATHS, MAX_FILE_SIZE, PENDING_APPROVALS,
    track_request,
)

files_bp = Blueprint('files', __name__)


@files_bp.route('/files/read', methods=['POST'])
def files_read():
    """Read file contents."""
    track_request('files/read')
    data = request.get_json() or {}
    path = data.get('path')
    encoding = data.get('encoding', 'utf-8')
    limit_lines = data.get('limit_lines')
    offset = data.get('offset', 0)

    if not path:
        return make_error(
            ErrorCode.MISSING_PARAMETER,
            "Missing required 'path' parameter",
            status=400,
            context={"endpoint": "/files/read", "required_params": ["path"]}
        )

    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return make_error(
            ErrorCode.PATH_NOT_ALLOWED,
            resolved_path,
            status=403,
            context={"requested_path": path}
        )

    try:
        file_path = Path(resolved_path)

        if not file_path.exists():
            return make_error(
                ErrorCode.FILE_NOT_FOUND,
                f"File not found: {path}",
                status=404,
                context={"requested_path": path, "resolved_path": resolved_path}
            )

        if not file_path.is_file():
            return make_error(
                ErrorCode.NOT_A_FILE,
                f"Path is a directory, not a file: {path}",
                status=400,
                context={"requested_path": path, "type": "directory"}
            )

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return make_error(
                ErrorCode.FILE_TOO_LARGE,
                f"File too large: {file_size:,} bytes (max {MAX_FILE_SIZE:,} bytes)",
                status=400,
                context={
                    "file_size_bytes": file_size,
                    "max_size_bytes": MAX_FILE_SIZE,
                    "file_size_mb": round(file_size / 1024 / 1024, 2)
                }
            )

        # Read file
        if encoding == 'binary' or encoding == 'base64':
            import base64
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('ascii')
        else:
            with open(file_path, 'r', encoding=encoding) as f:
                if limit_lines:
                    lines = f.readlines()
                    content = ''.join(lines[offset:offset + limit_lines])
                else:
                    content = f.read()

        return make_success({
            "path": resolved_path,
            "content": content,
            "file_size": file_size,
            "encoding": encoding,
            "truncated": False
        })

    except UnicodeDecodeError as e:
        return make_error(
            ErrorCode.ENCODING_ERROR,
            f"Cannot decode file with encoding '{encoding}': {str(e)}",
            status=400,
            context={"requested_encoding": encoding, "file_path": path}
        )
    except PermissionError:
        return make_error(
            ErrorCode.PATH_NOT_ALLOWED,
            f"Permission denied reading file: {path}",
            status=403,
            context={"file_path": path, "error_type": "permission"},
            include_tb=True
        )
    except Exception as e:
        return make_error(
            ErrorCode.INTERNAL_ERROR,
            f"Unexpected error reading file: {str(e)}",
            status=500,
            context={"file_path": path, "error_type": type(e).__name__},
            include_tb=True
        )


@files_bp.route('/files/write', methods=['POST'])
def files_write():
    """Write file contents."""
    track_request('files/write')
    data = request.get_json() or {}
    path = data.get('path')
    content = data.get('content', '')
    encoding = data.get('encoding', 'utf-8')
    mode = data.get('mode', 'overwrite')  # create, overwrite, append
    create_dirs = data.get('create_dirs', True)

    if not path:
        return jsonify({"success": False, "error": "Missing 'path' parameter"}), 400

    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return jsonify({"success": False, "error": resolved_path}), 403

    try:
        file_path = Path(resolved_path)

        # Check mode
        if mode == 'create' and file_path.exists():
            return jsonify({
                "success": False,
                "error": f"File already exists: {path}. Use mode='overwrite'"
            }), 400

        # Create parent directories if needed
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine write mode
        if mode == 'append':
            write_mode = 'a'
        else:
            write_mode = 'w'

        # Write file
        if encoding == 'binary' or encoding == 'base64':
            import base64
            with open(file_path, write_mode + 'b') as f:
                f.write(base64.b64decode(content))
        else:
            with open(file_path, write_mode, encoding=encoding) as f:
                f.write(content)

        return jsonify({
            "success": True,
            "path": resolved_path,
            "bytes_written": len(content),
            "mode": mode
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@files_bp.route('/files/edit', methods=['POST'])
def files_edit():
    """Edit file with line-based operations."""
    track_request('files/edit')
    data = request.get_json() or {}
    path = data.get('path')
    edits = data.get('edits', [])
    backup = data.get('backup', False)

    if not path:
        return jsonify({"success": False, "error": "Missing 'path' parameter"}), 400

    if not edits:
        return jsonify({"success": False, "error": "No edits provided"}), 400

    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return jsonify({"success": False, "error": resolved_path}), 403

    try:
        file_path = Path(resolved_path)

        if not file_path.exists():
            return jsonify({"success": False, "error": f"File not found: {path}"}), 404

        # Read existing content
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Create backup if requested
        backup_path = None
        if backup:
            backup_path = str(file_path) + '.bak'
            with open(backup_path, 'w') as f:
                f.writelines(lines)

        # Apply edits (in reverse order to preserve line numbers)
        lines_modified = 0
        for edit in sorted(edits, key=lambda x: x.get('line_start', 0), reverse=True):
            line_start = edit.get('line_start', 1) - 1  # Convert to 0-indexed
            line_end = edit.get('line_end', line_start + 1)
            new_content = edit.get('new_content', '')

            # Validate line numbers
            if line_start < 0 or line_start > len(lines):
                continue

            # Replace lines
            new_lines = new_content.split('\n') if new_content else []
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines[-1] += '\n'

            lines[line_start:line_end] = [l if l.endswith('\n') else l + '\n' for l in new_lines]
            lines_modified += 1

        # Write modified content
        with open(file_path, 'w') as f:
            f.writelines(lines)

        return jsonify({
            "success": True,
            "path": resolved_path,
            "lines_modified": lines_modified,
            "backup_path": backup_path
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@files_bp.route('/files/list', methods=['POST'])
def files_list():
    """List directory contents."""
    track_request('files/list')
    data = request.get_json() or {}
    path = data.get('path', '.')
    pattern = data.get('pattern', '*')
    recursive = data.get('recursive', False)

    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return jsonify({"success": False, "error": resolved_path}), 403

    try:
        dir_path = Path(resolved_path)

        if not dir_path.exists():
            return jsonify({"success": False, "error": f"Directory not found: {path}"}), 404

        if not dir_path.is_dir():
            return jsonify({"success": False, "error": f"Not a directory: {path}"}), 400

        # List files
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))

        # Build file info
        file_list = []
        for f in files[:1000]:  # Limit to 1000 files
            try:
                stat = f.stat()
                file_list.append({
                    "name": f.name,
                    "path": str(f),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "is_dir": f.is_dir()
                })
            except (OSError, PermissionError):
                continue

        return jsonify({
            "success": True,
            "path": resolved_path,
            "files": file_list,
            "count": len(file_list),
            "truncated": len(files) > 1000
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@files_bp.route('/files/glob', methods=['POST'])
def files_glob():
    """Find files matching a glob pattern."""
    track_request('files/glob')
    data = request.get_json() or {}
    pattern = data.get('pattern')
    path = data.get('path', ALLOWED_BASE_PATHS[0])
    sort_by = data.get('sort_by', 'modified')  # 'modified', 'name', 'size'
    max_results = min(data.get('max_results', 100), 1000)
    include_hidden = data.get('include_hidden', False)

    if not pattern:
        return jsonify({"success": False, "error": "Missing 'pattern' parameter"}), 400

    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return jsonify({"success": False, "error": resolved_path}), 403

    try:
        search_path = Path(resolved_path)

        if not search_path.exists():
            return jsonify({"success": False, "error": f"Path not found: {path}"}), 404

        # Find files matching pattern
        if '**' in pattern:
            files = list(search_path.rglob(pattern.replace('**/', '')))
        else:
            files = list(search_path.glob(pattern))

        # Filter hidden files if not requested
        if not include_hidden:
            files = [f for f in files if not any(p.startswith('.') for p in f.parts)]

        # Build file info list
        file_list = []
        for f in files[:max_results * 2]:  # Get extra for sorting
            try:
                stat = f.stat()
                file_list.append({
                    "name": f.name,
                    "path": str(f),
                    "relative_path": str(f.relative_to(search_path)) if str(f).startswith(str(search_path)) else str(f),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "modified_iso": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "is_dir": f.is_dir()
                })
            except (OSError, PermissionError):
                continue

        # Sort results
        if sort_by == 'modified':
            file_list.sort(key=lambda x: x['modified'], reverse=True)
        elif sort_by == 'name':
            file_list.sort(key=lambda x: x['name'].lower())
        elif sort_by == 'size':
            file_list.sort(key=lambda x: x['size'], reverse=True)

        # Limit results
        file_list = file_list[:max_results]

        return jsonify({
            "success": True,
            "pattern": pattern,
            "path": resolved_path,
            "files": file_list,
            "count": len(file_list),
            "total_found": len(files),
            "truncated": len(files) > max_results
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@files_bp.route('/files/delete', methods=['POST'])
def files_delete():
    """Delete a file (with optional approval)."""
    track_request('files/delete')
    data = request.get_json() or {}
    path = data.get('path')
    require_approval = data.get('require_approval', True)
    approval_id = data.get('approval_id')

    if not path:
        return jsonify({"success": False, "error": "Missing 'path' parameter"}), 400

    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return jsonify({"success": False, "error": resolved_path}), 403

    try:
        file_path = Path(resolved_path)

        if not file_path.exists():
            return jsonify({"success": False, "error": f"File not found: {path}"}), 404

        # If approval required and not provided, create approval request
        if require_approval and not approval_id:
            approval_id = str(uuid.uuid4())
            PENDING_APPROVALS[approval_id] = {
                "id": approval_id,
                "type": "file_delete",
                "path": resolved_path,
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
            return jsonify({
                "success": False,
                "approval_required": True,
                "approval_id": approval_id,
                "message": f"Approval required to delete: {resolved_path}"
            }), 202

        # Check approval if provided
        if approval_id:
            approval = PENDING_APPROVALS.get(approval_id)
            if not approval or approval.get('status') != 'approved':
                return jsonify({
                    "success": False,
                    "error": "Invalid or unapproved approval_id"
                }), 403

        # Delete file
        if file_path.is_dir():
            import shutil
            shutil.rmtree(file_path)
        else:
            file_path.unlink()

        # Clean up approval
        if approval_id and approval_id in PENDING_APPROVALS:
            del PENDING_APPROVALS[approval_id]

        return jsonify({
            "success": True,
            "deleted": resolved_path
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
