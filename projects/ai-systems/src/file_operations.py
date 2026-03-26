"""
AI Systems File Operations API - Tower-specific file and git operations.

Extracted from monolithic agent_bridge_api.py to restore tower independence.
Provides file/git functionality for ai-systems tower only.
"""

import os
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_OUTPUT_SIZE = 100 * 1024  # 100KB for command output
COMMAND_TIMEOUT = 120  # 2 minutes default
ALLOWED_BASE_PATHS = [
    "/Users/williammarceaujr./dev-sandbox",
    "/Users/williammarceaujr./production",
    "/tmp",
    "/home/ec2-user/dev-sandbox",
    "/home/ec2-user",
]


def validate_path(path: str) -> Tuple[bool, str]:
    """Validate that a path is safe to access."""
    try:
        # Resolve to absolute path
        resolved = Path(path).resolve()
        resolved_str = str(resolved)

        # Check against allowed base paths
        for base in ALLOWED_BASE_PATHS:
            if resolved_str.startswith(base):
                return True, resolved_str

        return False, f"Path not in allowed directories: {resolved_str}"
    except Exception as e:
        return False, f"Invalid path: {str(e)}"


def truncate_output(output: str, max_size: int = MAX_OUTPUT_SIZE) -> Tuple[str, bool]:
    """Truncate output if too large."""
    if len(output) > max_size:
        return output[:max_size] + f"\n\n... [TRUNCATED - {len(output)} total bytes]", True
    return output, False


def read_file(path: str, encoding: str = 'utf-8', limit_lines: Optional[int] = None,
              offset: int = 0) -> Dict[str, Any]:
    """
    Read file contents.

    Args:
        path: File path to read
        encoding: File encoding
        limit_lines: Maximum lines to read
        offset: Line offset to start reading

    Returns:
        Dict with file content and metadata
    """
    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return {"success": False, "error": resolved_path}

    try:
        file_path = Path(resolved_path)

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}

        if not file_path.is_file():
            return {"success": False, "error": f"Path is a directory, not a file: {path}"}

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return {
                "success": False,
                "error": f"File too large: {file_size:,} bytes (max {MAX_FILE_SIZE:,} bytes)"
            }

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

        return {
            "success": True,
            "path": resolved_path,
            "content": content,
            "file_size": file_size,
            "encoding": encoding,
            "truncated": False
        }

    except UnicodeDecodeError as e:
        return {
            "success": False,
            "error": f"Cannot decode file with encoding '{encoding}': {str(e)}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_file(path: str, content: str, encoding: str = 'utf-8', mode: str = 'overwrite',
               create_dirs: bool = True) -> Dict[str, Any]:
    """
    Write content to file.

    Args:
        path: File path to write
        content: Content to write
        encoding: File encoding
        mode: Write mode ('create', 'overwrite', 'append')
        create_dirs: Whether to create parent directories

    Returns:
        Dict with write status
    """
    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return {"success": False, "error": resolved_path}

    try:
        file_path = Path(resolved_path)

        # Check mode
        if mode == 'create' and file_path.exists():
            return {
                "success": False,
                "error": f"File already exists: {path}. Use mode='overwrite'"
            }

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

        return {
            "success": True,
            "path": resolved_path,
            "bytes_written": len(content),
            "mode": mode
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def edit_file(path: str, edits: List[Dict], backup: bool = False) -> Dict[str, Any]:
    """
    Edit file with line-based operations.

    Args:
        path: File path to edit
        edits: List of edit operations
        backup: Whether to create backup

    Returns:
        Dict with edit status
    """
    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return {"success": False, "error": resolved_path}

    try:
        file_path = Path(resolved_path)

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}

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

        return {
            "success": True,
            "path": resolved_path,
            "lines_modified": lines_modified,
            "backup_path": backup_path
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def list_directory(path: str, pattern: str = '*', recursive: bool = False,
                   max_results: int = 1000) -> Dict[str, Any]:
    """
    List directory contents.

    Args:
        path: Directory path to list
        pattern: File pattern to match
        recursive: Whether to list recursively
        max_results: Maximum results to return

    Returns:
        Dict with directory listing
    """
    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return {"success": False, "error": resolved_path}

    try:
        dir_path = Path(resolved_path)

        if not dir_path.exists():
            return {"success": False, "error": f"Directory not found: {path}"}

        if not dir_path.is_dir():
            return {"success": False, "error": f"Not a directory: {path}"}

        # List files
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))

        # Build file info
        file_list = []
        for f in files[:max_results]:
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

        return {
            "success": True,
            "path": resolved_path,
            "files": file_list,
            "count": len(file_list),
            "truncated": len(files) > max_results
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def execute_command(command: str, cwd: str = ALLOWED_BASE_PATHS[0], timeout: int = COMMAND_TIMEOUT,
                    env: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Execute a shell command.

    Args:
        command: Command to execute
        cwd: Working directory
        timeout: Command timeout in seconds
        env: Environment variables

    Returns:
        Dict with command execution results
    """
    # Validate working directory
    valid, resolved_cwd = validate_path(cwd)
    if not valid:
        return {"success": False, "error": f"Working directory not allowed: {cwd}"}

    try:
        # Merge environment
        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        # Execute command
        start_time = datetime.now()
        result = subprocess.run(
            command,
            shell=True,
            cwd=resolved_cwd,
            env=full_env,
            capture_output=True,
            timeout=timeout,
            text=True
        )
        end_time = datetime.now()

        # Truncate output if needed
        stdout, stdout_truncated = truncate_output(result.stdout)
        stderr, stderr_truncated = truncate_output(result.stderr)

        return {
            "success": True,
            "command_success": result.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": result.returncode,
            "duration_ms": int((end_time - start_time).total_seconds() * 1000),
            "cwd": resolved_cwd,
            "truncated": stdout_truncated or stderr_truncated
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Command timed out after {timeout} seconds"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def git_status(repo_path: str = ALLOWED_BASE_PATHS[0]) -> Dict[str, Any]:
    """
    Get git status for a repository.

    Args:
        repo_path: Repository path

    Returns:
        Dict with git status information
    """
    # Validate path
    valid, resolved_path = validate_path(repo_path)
    if not valid:
        return {"success": False, "error": resolved_path}

    try:
        # Check if it's a git repo
        git_dir = Path(resolved_path) / '.git'
        if not git_dir.exists():
            return {"success": False, "error": f"Not a git repository: {repo_path}"}

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

        return {
            "success": True,
            "branch": branch,
            "clean": len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0,
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked,
            "ahead": ahead,
            "behind": behind
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def git_commit(repo_path: str, message: str, files: Optional[List[str]] = None,
               author: Optional[str] = None) -> Dict[str, Any]:
    """
    Commit changes to git.

    Args:
        repo_path: Repository path
        message: Commit message
        files: Files to commit (optional)
        author: Author for commit (optional)

    Returns:
        Dict with commit status
    """
    # Validate path
    valid, resolved_path = validate_path(repo_path)
    if not valid:
        return {"success": False, "error": resolved_path}

    if not message:
        return {"success": False, "error": "Commit message required"}

    try:
        # Add files
        if files:
            result = subprocess.run(
                ['git', 'add'] + files,
                cwd=resolved_path,
                capture_output=True,
                text=True
            )
        else:
            result = subprocess.run(
                ['git', 'add', '-A'],
                cwd=resolved_path,
                capture_output=True,
                text=True
            )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Failed to stage files: {result.stderr}"
            }

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
            return {
                "success": False,
                "error": f"Commit failed: {result.stderr}"
            }

        # Get commit hash
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )
        commit_hash = result.stdout.strip()

        return {
            "success": True,
            "commit_hash": commit_hash,
            "message": message
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# Tower interface functions for CLAUDE.md compliance
def get_tower_capabilities() -> Dict[str, Any]:
    """Return tower capabilities for file/git operations."""
    return {
        "name": "ai-systems-file-ops",
        "description": "File and git operations for AI systems infrastructure",
        "functions": [
            "read_file",
            "write_file",
            "edit_file",
            "list_directory",
            "execute_command",
            "git_status",
            "git_commit"
        ],
        "protocols": ["direct_import", "mcp_server"]
    }


def get_mcp_server_config() -> Dict[str, Any]:
    """Return MCP server configuration for tower integration."""
    return {
        "name": "ai-systems-file-ops",
        "version": "1.0.0",
        "capabilities": get_tower_capabilities(),
        "endpoints": {
            "read": "/files/read",
            "write": "/files/write",
            "edit": "/files/edit",
            "list": "/files/list",
            "command": "/command/execute",
            "git_status": "/git/status",
            "git_commit": "/git/commit"
        }
    }


if __name__ == "__main__":
    # Test the file operations API extraction
    print("Testing ai-systems file operations API extraction...")

    # Test path validation
    valid, resolved = validate_path("/tmp/test")
    if valid:
        print("✓ Path validation working")
    else:
        print("✗ Path validation failed")

    # Test capabilities
    caps = get_tower_capabilities()
    print(f"✓ Tower capabilities: {caps['name']}")

    print("File operations API extraction test completed")