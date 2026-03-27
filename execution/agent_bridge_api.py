#!/usr/bin/env python3
"""
Agent Bridge API - Flask server providing file/command/git operations for n8n agents.

This API enables n8n workflows to perform operations that n8n cannot do natively,
bridging the gap between Claude Code capabilities and n8n automation.

Usage:
    # Start the server
    python -m execution.agent_bridge_api

    # Or with custom port
    python -m execution.agent_bridge_api --port 5010

    # Test health
    curl http://localhost:5010/health

Endpoints:
    GET  /health           - Health check
    POST /files/read       - Read file contents
    POST /files/write      - Write file contents
    POST /files/edit       - Edit file (line-based)
    POST /files/list       - List directory contents
    POST /files/delete     - Delete file (with approval option)
    POST /command/execute  - Execute bash command
    POST /git/status       - Get git status
    POST /git/commit       - Commit changes
    POST /git/push         - Push to remote

Security:
    - Runs on localhost only (127.0.0.1)
    - Path validation prevents directory traversal
    - Destructive commands require approval flag
    - Configurable allowed directories

Author: William Marceau Jr.
Created: 2026-02-06
"""

import argparse
import atexit
import json
import os
import subprocess
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from flask import Flask, Response, jsonify, request, stream_with_context
from flask_cors import CORS


# =============================================================================
# ERROR HANDLING SYSTEM
# =============================================================================

class ErrorCode(Enum):
    """Error codes for structured error responses."""
    # Validation errors (400)
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    INVALID_PATH = "INVALID_PATH"

    # Permission errors (403)
    PATH_NOT_ALLOWED = "PATH_NOT_ALLOWED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_INVALID = "APPROVAL_INVALID"

    # Not found errors (404)
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    DIRECTORY_NOT_FOUND = "DIRECTORY_NOT_FOUND"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TODO_NOT_FOUND = "TODO_NOT_FOUND"
    CHECKPOINT_NOT_FOUND = "CHECKPOINT_NOT_FOUND"

    # Resource errors (400/500)
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    NOT_A_FILE = "NOT_A_FILE"
    NOT_A_DIRECTORY = "NOT_A_DIRECTORY"
    FILE_EXISTS = "FILE_EXISTS"
    NOT_A_GIT_REPO = "NOT_A_GIT_REPO"

    # Timeout errors (504)
    COMMAND_TIMEOUT = "COMMAND_TIMEOUT"
    SEARCH_TIMEOUT = "SEARCH_TIMEOUT"
    REQUEST_TIMEOUT = "REQUEST_TIMEOUT"

    # Encoding errors (400)
    ENCODING_ERROR = "ENCODING_ERROR"

    # External errors (500/502)
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    GIT_ERROR = "GIT_ERROR"

    # System errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


# Error suggestions for common issues
ERROR_SUGGESTIONS = {
    ErrorCode.MISSING_PARAMETER: "Check the API documentation for required parameters.",
    ErrorCode.INVALID_PARAMETER: "Verify the parameter format and allowed values.",
    ErrorCode.INVALID_PATH: "Ensure the path is absolute and properly formatted.",
    ErrorCode.PATH_NOT_ALLOWED: "The path must be within allowed directories: {allowed_paths}",
    ErrorCode.APPROVAL_REQUIRED: "This action requires approval. Use the approval_id to approve or deny.",
    ErrorCode.APPROVAL_INVALID: "Ensure the approval_id is correct and has been approved.",
    ErrorCode.FILE_NOT_FOUND: "Check the file path for typos. Use /files/list or /files/glob to find files.",
    ErrorCode.DIRECTORY_NOT_FOUND: "Verify the directory exists. Use /files/list to browse directories.",
    ErrorCode.SESSION_NOT_FOUND: "The session may have expired or never existed. Use /session/list to see available sessions.",
    ErrorCode.TASK_NOT_FOUND: "The task may have completed or expired. Use /task/list to see active tasks.",
    ErrorCode.TODO_NOT_FOUND: "The todo item may have been deleted. Use /todo/list to see current items.",
    ErrorCode.CHECKPOINT_NOT_FOUND: "Use /session/list to see available checkpoints for this session.",
    ErrorCode.FILE_TOO_LARGE: "Consider reading the file in chunks using limit_lines and offset parameters.",
    ErrorCode.NOT_A_FILE: "The path points to a directory. Use /files/list for directories.",
    ErrorCode.NOT_A_DIRECTORY: "The path points to a file. Use /files/read for files.",
    ErrorCode.FILE_EXISTS: "Use mode='overwrite' to replace the existing file.",
    ErrorCode.NOT_A_GIT_REPO: "Initialize a git repository with 'git init' or check the path.",
    ErrorCode.COMMAND_TIMEOUT: "Increase the timeout parameter or simplify the command.",
    ErrorCode.SEARCH_TIMEOUT: "Narrow the search scope or use a more specific pattern.",
    ErrorCode.REQUEST_TIMEOUT: "Check the URL is accessible and increase the timeout if needed.",
    ErrorCode.ENCODING_ERROR: "Try encoding='binary' or 'base64' for non-text files.",
    ErrorCode.DEPENDENCY_MISSING: "Install required packages: pip install {packages}",
    ErrorCode.EXTERNAL_SERVICE_ERROR: "Check the external service is available and credentials are valid.",
    ErrorCode.GIT_ERROR: "Check git status and resolve any conflicts or issues.",
    ErrorCode.INTERNAL_ERROR: "An unexpected error occurred. Check server logs for details.",
    ErrorCode.UNKNOWN_ERROR: "An unknown error occurred. Please report this issue.",
}


def make_error_response(
    error_code: ErrorCode,
    message: str,
    status_code: int = 400,
    context: Optional[Dict[str, Any]] = None,
    suggestion: Optional[str] = None,
    include_traceback: bool = False,
    **format_kwargs
) -> Tuple[Dict[str, Any], int]:
    """
    Create a structured error response with context and recovery suggestions.

    Args:
        error_code: The error code enum value
        message: Human-readable error message
        status_code: HTTP status code
        context: Additional context about what was attempted
        suggestion: Override the default suggestion
        include_traceback: Include stack trace for debugging
        **format_kwargs: Values to format into the suggestion template

    Returns:
        Tuple of (response dict, status code)
    """
    # Get suggestion (custom or default)
    if suggestion is None:
        suggestion = ERROR_SUGGESTIONS.get(error_code, "")
        if format_kwargs:
            try:
                suggestion = suggestion.format(**format_kwargs)
            except KeyError:
                pass  # Keep original if format fails

    error_response = {
        "success": False,
        "error": {
            "code": error_code.value,
            "message": message,
            "suggestion": suggestion,
        }
    }

    if context:
        error_response["error"]["context"] = context

    if include_traceback:
        error_response["error"]["traceback"] = traceback.format_exc()

    # Also include flat error for backwards compatibility
    error_response["error_message"] = message

    return jsonify(error_response), status_code


def make_success_response(data: Dict[str, Any], message: Optional[str] = None) -> Dict[str, Any]:
    """Create a standardized success response."""
    response = {"success": True, **data}
    if message:
        response["message"] = message
    return jsonify(response)

# Configuration
DEFAULT_PORT = 5010
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

# Persistence Configuration
PERSISTENCE_DIR = Path(os.environ.get('AGENT_BRIDGE_DATA_DIR', '/tmp/agent_bridge_data'))
PERSISTENCE_FILE = PERSISTENCE_DIR / 'state.json'
PERSISTENCE_ENABLED = os.environ.get('AGENT_BRIDGE_PERSIST', 'true').lower() == 'true'
AUTO_SAVE_INTERVAL = 30  # seconds


# =============================================================================
# PERSISTENCE LAYER
# =============================================================================

class PersistenceManager:
    """Manages persistence of in-memory state to disk."""

    def __init__(self, file_path: Path, auto_save_interval: int = 30):
        self.file_path = file_path
        self.auto_save_interval = auto_save_interval
        self._lock = threading.Lock()
        self._dirty = False
        self._auto_save_thread: Optional[threading.Thread] = None
        self._stop_auto_save = threading.Event()

        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """Load state from disk."""
        with self._lock:
            if self.file_path.exists():
                try:
                    with open(self.file_path, 'r') as f:
                        data = json.load(f)
                    print(f"[Persistence] Loaded state from {self.file_path}")
                    print(f"  - Tasks: {len(data.get('tasks', {}))}")
                    print(f"  - Sessions: {len(data.get('sessions', {}))}")
                    print(f"  - Todos: {len(data.get('todos', {}))}")
                    return data
                except (json.JSONDecodeError, IOError) as e:
                    print(f"[Persistence] Error loading state: {e}")
                    return self._default_state()
            return self._default_state()

    def save(self, state: Dict[str, Any], force: bool = False) -> bool:
        """Save state to disk."""
        if not PERSISTENCE_ENABLED and not force:
            return False

        with self._lock:
            try:
                # Write to temp file first, then rename (atomic)
                temp_file = self.file_path.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(state, f, indent=2, default=str)
                temp_file.rename(self.file_path)
                self._dirty = False
                return True
            except IOError as e:
                print(f"[Persistence] Error saving state: {e}")
                return False

    def mark_dirty(self):
        """Mark state as needing save."""
        self._dirty = True

    def start_auto_save(self, get_state_fn: Callable[[], Dict[str, Any]]):
        """Start background auto-save thread."""
        if not PERSISTENCE_ENABLED:
            return

        def auto_save_loop():
            while not self._stop_auto_save.wait(self.auto_save_interval):
                if self._dirty:
                    state = get_state_fn()
                    self.save(state)

        self._auto_save_thread = threading.Thread(target=auto_save_loop, daemon=True)
        self._auto_save_thread.start()
        print(f"[Persistence] Auto-save started (interval: {self.auto_save_interval}s)")

    def stop_auto_save(self, get_state_fn: Callable[[], Dict[str, Any]]):
        """Stop auto-save and perform final save."""
        self._stop_auto_save.set()
        if self._auto_save_thread:
            self._auto_save_thread.join(timeout=5)
        # Final save
        state = get_state_fn()
        self.save(state, force=True)
        print("[Persistence] Final state saved")

    def _default_state(self) -> Dict[str, Any]:
        """Return default empty state."""
        return {
            "tasks": {},
            "sessions": {},
            "todos": {},
            "approvals": {},
            "metrics": {
                "tools": {},
                "global": {
                    "total_calls": 0,
                    "total_success": 0,
                    "total_errors": 0,
                    "total_latency_ms": 0,
                    "started_at": datetime.now().isoformat()
                }
            },
            "saved_at": datetime.now().isoformat()
        }


# =============================================================================
# RETRY LOGIC
# =============================================================================

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Tuple[type, ...] = (Exception,)
):
    """
    Decorator for retrying operations with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        retryable_exceptions: Tuple of exception types to retry on
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        # Add jitter (±25%)
                        import random
                        delay = delay * (0.75 + random.random() * 0.5)
                        print(f"[Retry] Attempt {attempt + 1}/{max_retries} failed: {e}")
                        print(f"[Retry] Waiting {delay:.2f}s before retry...")
                        time.sleep(delay)
            # All retries exhausted
            raise last_exception
        return wrapper
    return decorator


# =============================================================================
# CONTEXT MANAGEMENT
# =============================================================================

# Token estimation constants (approximate for Claude)
CHARS_PER_TOKEN = 4  # Conservative estimate
MAX_CONTEXT_TOKENS = 150000  # Claude Sonnet context window
CONTEXT_BUFFER_TOKENS = 30000  # Reserve for response
EFFECTIVE_CONTEXT_TOKENS = MAX_CONTEXT_TOKENS - CONTEXT_BUFFER_TOKENS


def estimate_tokens(text: str) -> int:
    """Estimate token count for text."""
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN


def estimate_message_tokens(message: Dict[str, Any]) -> int:
    """Estimate tokens in a message."""
    content = message.get('content', '')
    if isinstance(content, str):
        return estimate_tokens(content) + 4  # Add overhead for role/structure
    elif isinstance(content, list):
        # Handle list of content blocks
        total = 4
        for block in content:
            if isinstance(block, dict):
                total += estimate_tokens(str(block.get('text', '')))
            else:
                total += estimate_tokens(str(block))
        return total
    return 10  # Default overhead


def truncate_conversation_history(
    messages: List[Dict[str, Any]],
    max_tokens: int = EFFECTIVE_CONTEXT_TOKENS,
    preserve_first_n: int = 1,
    preserve_last_n: int = 3
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Truncate conversation history to fit within token limit.

    Preserves:
    - First N messages (usually system prompt + initial task)
    - Last N messages (recent context)

    Returns:
        Tuple of (truncated_messages, truncation_info)
    """
    if not messages:
        return messages, {"truncated": False, "original_count": 0, "new_count": 0}

    # Calculate current tokens
    total_tokens = sum(estimate_message_tokens(m) for m in messages)

    if total_tokens <= max_tokens:
        return messages, {
            "truncated": False,
            "original_count": len(messages),
            "new_count": len(messages),
            "estimated_tokens": total_tokens
        }

    # Need to truncate
    original_count = len(messages)

    # Calculate tokens for preserved messages
    first_messages = messages[:preserve_first_n]
    last_messages = messages[-preserve_last_n:] if preserve_last_n > 0 else []

    first_tokens = sum(estimate_message_tokens(m) for m in first_messages)
    last_tokens = sum(estimate_message_tokens(m) for m in last_messages)

    # Available for middle messages
    available_tokens = max_tokens - first_tokens - last_tokens - 100  # Buffer for summary message

    # Build result
    result = list(first_messages)

    # Add truncation marker
    middle_count = original_count - preserve_first_n - preserve_last_n
    if middle_count > 0:
        result.append({
            "role": "assistant",
            "content": f"[Context truncated: {middle_count} messages removed to fit context window. Token estimate: {total_tokens} → {max_tokens}]"
        })

    # Add preserved last messages
    result.extend(last_messages)

    new_tokens = sum(estimate_message_tokens(m) for m in result)

    return result, {
        "truncated": True,
        "original_count": original_count,
        "new_count": len(result),
        "messages_removed": middle_count,
        "original_tokens": total_tokens,
        "new_tokens": new_tokens
    }


# =============================================================================
# v3.6: TOOL RESULT CACHING (LRU with TTL)
# =============================================================================

class LRUCache:
    """Thread-safe LRU cache with TTL support."""

    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl  # seconds
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]
            if time.time() > entry["expires_at"]:
                # Expired - remove and return None
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._stats["hits"] += 1
            return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self.max_size:
                # Remove oldest
                self._cache.popitem(last=False)
                self._stats["evictions"] += 1

            self._cache[key] = {
                "value": value,
                "expires_at": time.time() + (ttl or self.default_ttl),
                "created_at": time.time()
            }

    def invalidate(self, key: str) -> bool:
        """Remove specific key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Remove all keys matching pattern (simple prefix match)."""
        with self._lock:
            to_remove = [k for k in self._cache if k.startswith(pattern)]
            for k in to_remove:
                del self._cache[k]
            return len(to_remove)

    def clear(self) -> int:
        """Clear entire cache."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "hit_rate": round(self._stats["hits"] / total * 100, 1) if total > 0 else 0
            }


# Global cache instance
TOOL_CACHE = LRUCache(max_size=200, default_ttl=300)  # 5 min default TTL


def cache_key(tool: str, **params) -> str:
    """Generate cache key from tool name and parameters."""
    param_str = json.dumps(params, sort_keys=True, default=str)
    return f"{tool}:{param_str}"


# =============================================================================
# v3.6: SMART RATE LIMITING (Token Bucket)
# =============================================================================

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_second: float = 10.0
    burst_size: int = 20
    enabled: bool = True


class TokenBucket:
    """Token bucket rate limiter with burst support."""

    def __init__(self, rate: float = 10.0, burst: int = 20):
        self.rate = rate  # tokens per second
        self.burst = burst  # max tokens
        self.tokens = float(burst)
        self.last_update = time.time()
        self._lock = threading.Lock()
        self._stats = {"allowed": 0, "throttled": 0, "wait_time_total": 0.0}

    def _refill(self) -> None:
        """Refill tokens based on time elapsed."""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_update = now

    def acquire(self, tokens: int = 1, wait: bool = True, timeout: float = 30.0) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire
            wait: If True, wait for tokens; if False, return immediately
            timeout: Maximum time to wait

        Returns:
            True if tokens acquired, False if timed out or would block
        """
        start_time = time.time()

        with self._lock:
            while True:
                self._refill()

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    self._stats["allowed"] += 1
                    return True

                if not wait:
                    self._stats["throttled"] += 1
                    return False

                # Calculate wait time
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.rate

                if time.time() - start_time + wait_time > timeout:
                    self._stats["throttled"] += 1
                    return False

                self._stats["wait_time_total"] += min(wait_time, 0.1)
                self._lock.release()
                time.sleep(min(wait_time, 0.1))
                self._lock.acquire()

    def stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        with self._lock:
            self._refill()
            total = self._stats["allowed"] + self._stats["throttled"]
            return {
                "current_tokens": round(self.tokens, 2),
                "rate": self.rate,
                "burst": self.burst,
                "allowed": self._stats["allowed"],
                "throttled": self._stats["throttled"],
                "throttle_rate": round(self._stats["throttled"] / total * 100, 1) if total > 0 else 0,
                "avg_wait_ms": round(self._stats["wait_time_total"] / self._stats["allowed"] * 1000, 2) if self._stats["allowed"] > 0 else 0
            }


# Rate limiters for different operations
RATE_LIMITERS = {
    "default": TokenBucket(rate=10.0, burst=20),
    "api_call": TokenBucket(rate=5.0, burst=10),  # External API calls
    "file_ops": TokenBucket(rate=20.0, burst=50),  # File operations
    "command": TokenBucket(rate=2.0, burst=5),  # Shell commands (more restrictive)
}


def get_rate_limiter(category: str = "default") -> TokenBucket:
    """Get rate limiter for a category."""
    return RATE_LIMITERS.get(category, RATE_LIMITERS["default"])


# [EXTRACTED to ai-systems tower] Lines 671-2815 (2145 lines)
# AI data models + classes now live in projects/ai-systems/src/models.py
# Stub globals below prevent NameError in /health, get_current_state(), and main()

SESSION_COSTS = {}
CONVERSATION_MEMORIES = {}
TOOL_PIPELINES = {}
WEBHOOKS = {}
AGENT_TEMPLATES = {}
SUB_AGENTS = {}
ORCHESTRATIONS = {}
KNOWLEDGE_BASES = {}
SCHEDULED_TASKS = {}
TOOL_PLUGINS = {}
TASK_OUTCOMES = {}
LEARNING_ENTRIES = {}
RECORDED_WORKFLOWS = {}
CONTEXT_INJECTION_RULES = {}
AGENT_MESSAGES = {}
SHARED_STATES = {}
AGENT_PERSONAS = {}
GOALS = {}
TOOL_MACROS = {}
AUDIT_TRAIL = []
BEHAVIOR_PROFILES = {}
BUILTIN_MACROS = {}
BUILTIN_PIPELINES = {}


class ToolPipeline:
    """Minimal stub for tool pipeline support (full class in ai-systems tower)."""
    def __init__(self, name="", steps=None):
        self.name = name
        self.steps = steps or []
        self.created_at = datetime.now().isoformat()
    def to_dict(self):
        return {"name": self.name, "steps": self.steps, "created_at": self.created_at}


class WebhookConfig:
    """Minimal stub for webhook support (full class in ai-systems tower)."""
    def __init__(self, webhook_id="", url="", events=None, headers=None, active=True):
        self.webhook_id = webhook_id or str(uuid.uuid4())[:8]
        self.url = url
        self.events = events or []
        self.headers = headers or {}
        self.active = active
        self.created_at = datetime.now().isoformat()
        self.last_triggered = None
        self.trigger_count = 0
    def to_dict(self):
        return {"webhook_id": self.webhook_id, "url": self.url, "events": self.events,
                "headers": self.headers, "active": self.active, "created_at": self.created_at}


# =============================================================================
# v3.6: PARALLEL TOOL EXECUTION
# =============================================================================

# Thread pool for parallel execution
PARALLEL_EXECUTOR = ThreadPoolExecutor(max_workers=10, thread_name_prefix="tool_parallel_")


def execute_tool_call(tool_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single tool call (used for parallel execution).

    Args:
        tool_config: Dict with 'tool' (name) and 'input' (parameters)

    Returns:
        Dict with 'tool', 'success', 'result' or 'error', and 'latency_ms'
    """
    import requests as req_lib

    tool_name = tool_config.get('tool')
    tool_input = tool_config.get('input', {})

    # Map tool names to endpoints
    endpoint_map = {
        'file_read': '/files/read',
        'file_write': '/files/write',
        'file_edit': '/files/edit',
        'command': '/command/execute',
        'git_status': '/git/status',
        'web_fetch': '/web/fetch',
        'grep': '/search/grep',
        'glob': '/files/glob',
        'web_search': '/search/web',
    }

    endpoint = endpoint_map.get(tool_name)
    if not endpoint:
        return {
            "tool": tool_name,
            "success": False,
            "error": f"Unknown tool: {tool_name}",
            "latency_ms": 0
        }

    # Execute tool via internal HTTP call
    start_time = time.time()
    try:
        base_url = f"http://127.0.0.1:{DEFAULT_PORT}"
        resp = req_lib.post(f"{base_url}{endpoint}", json=tool_input, timeout=60)
        latency_ms = (time.time() - start_time) * 1000

        result = resp.json()
        return {
            "tool": tool_name,
            "success": result.get("success", resp.ok),
            "result": result if result.get("success") else None,
            "error": result.get("error") if not result.get("success") else None,
            "latency_ms": round(latency_ms, 2)
        }
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return {
            "tool": tool_name,
            "success": False,
            "error": str(e),
            "latency_ms": round(latency_ms, 2)
        }


def execute_tools_parallel(
    tool_calls: List[Dict[str, Any]],
    max_parallel: int = 5,
    timeout: float = 60.0
) -> Dict[str, Any]:
    """
    Execute multiple tool calls in parallel.

    Args:
        tool_calls: List of {'tool': 'name', 'input': {...}}
        max_parallel: Maximum concurrent executions
        timeout: Overall timeout in seconds

    Returns:
        Dict with 'results', 'completed', 'failed', 'total_latency_ms'
    """
    start_time = time.time()
    results = []
    completed = 0
    failed = 0

    # Limit parallelism
    effective_workers = min(max_parallel, len(tool_calls), 10)

    futures = {}
    with ThreadPoolExecutor(max_workers=effective_workers) as executor:
        for i, tool_config in enumerate(tool_calls):
            future = executor.submit(execute_tool_call, tool_config)
            futures[future] = i

        for future in as_completed(futures, timeout=timeout):
            try:
                result = future.result()
                results.append(result)
                if result["success"]:
                    completed += 1
                else:
                    failed += 1
            except Exception as e:
                idx = futures[future]
                results.append({
                    "tool": tool_calls[idx].get("tool", "unknown"),
                    "success": False,
                    "error": f"Execution error: {str(e)}",
                    "latency_ms": 0
                })
                failed += 1

    total_latency = (time.time() - start_time) * 1000

    return {
        "results": results,
        "completed": completed,
        "failed": failed,
        "total_count": len(tool_calls),
        "total_latency_ms": round(total_latency, 2),
        "parallelism": effective_workers
    }


# Flask app
app = Flask(__name__)
CORS(app)

# Track server start time for uptime
SERVER_START_TIME = time.time()

# Initialize persistence manager
persistence_manager = PersistenceManager(PERSISTENCE_FILE, AUTO_SAVE_INTERVAL)

# Load persisted state
_persisted_state = persistence_manager.load()

# Pending approvals storage
PENDING_APPROVALS: Dict[str, Dict[str, Any]] = _persisted_state.get('approvals', {})

# =============================================================================
# EXECUTION METRICS
# =============================================================================

# Load metrics from persisted state or use defaults
_default_metrics = {
    "tools": {},  # Per-tool metrics
    "global": {
        "total_calls": 0,
        "total_success": 0,
        "total_errors": 0,
        "total_latency_ms": 0,
        "started_at": datetime.now().isoformat()
    }
}
EXECUTION_METRICS: Dict[str, Dict[str, Any]] = _persisted_state.get('metrics', _default_metrics)


def record_metric(tool_name: str, success: bool, latency_ms: float, error_info: Any = None):
    """Record execution metrics for a tool call.

    Args:
        tool_name: Name of the tool being tracked
        success: Whether the call succeeded
        latency_ms: Latency in milliseconds
        error_info: Error info - can be string, dict (new structured format), or None
    """
    # Initialize tool metrics if needed
    if tool_name not in EXECUTION_METRICS["tools"]:
        EXECUTION_METRICS["tools"][tool_name] = {
            "calls": 0,
            "success": 0,
            "errors": 0,
            "total_latency_ms": 0,
            "min_latency_ms": float('inf'),
            "max_latency_ms": 0,
            "last_called": None,
            "last_error": None,
            "error_types": {}
        }

    tool = EXECUTION_METRICS["tools"][tool_name]
    tool["calls"] += 1
    tool["total_latency_ms"] += latency_ms
    tool["min_latency_ms"] = min(tool["min_latency_ms"], latency_ms)
    tool["max_latency_ms"] = max(tool["max_latency_ms"], latency_ms)
    tool["last_called"] = datetime.now().isoformat()

    if success:
        tool["success"] += 1
    else:
        tool["errors"] += 1

        # Handle different error formats
        if isinstance(error_info, dict):
            # New structured error format
            error_msg = error_info.get('message', str(error_info))
            error_type = error_info.get('code', 'UNKNOWN_ERROR')
        elif isinstance(error_info, str):
            # Old string format
            error_msg = error_info
            error_type = error_info.split(":")[0] if ":" in error_info else "Unknown"
        else:
            error_msg = str(error_info) if error_info else "Unknown error"
            error_type = "Unknown"

        tool["last_error"] = {"message": error_msg, "code": error_type, "at": datetime.now().isoformat()}
        tool["error_types"][error_type] = tool["error_types"].get(error_type, 0) + 1

    # Update global metrics
    EXECUTION_METRICS["global"]["total_calls"] += 1
    EXECUTION_METRICS["global"]["total_latency_ms"] += latency_ms
    if success:
        EXECUTION_METRICS["global"]["total_success"] += 1
    else:
        EXECUTION_METRICS["global"]["total_errors"] += 1

    # Mark state as dirty for persistence
    persistence_manager.mark_dirty()


def track_metrics(tool_name: str):
    """Decorator to automatically track execution metrics for a tool."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                latency_ms = (time.time() - start_time) * 1000

                # Check if it's a tuple (response, status_code)
                if isinstance(result, tuple):
                    response, status_code = result
                    success = 200 <= status_code < 400
                else:
                    response = result
                    status_code = 200
                    json_data = response.get_json() if hasattr(response, 'get_json') else {}
                    success = json_data.get('success', True)

                # Extract error info for metrics
                error_info = None
                if not success:
                    try:
                        json_data = response.get_json() if hasattr(response, 'get_json') else {}
                        # Handle both new structured format and old format
                        error_data = json_data.get('error', {})
                        if isinstance(error_data, dict):
                            error_info = error_data  # New structured format
                        else:
                            error_info = str(error_data)  # Old string format
                    except Exception:
                        error_info = "Error extracting error info"

                record_metric(tool_name, success, latency_ms, error_info)
                return result
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                record_metric(tool_name, False, latency_ms, str(e))
                raise
        return wrapper
    return decorator


def get_metrics_summary() -> Dict[str, Any]:
    """Get a summary of execution metrics."""
    global_m = EXECUTION_METRICS["global"]
    tools = EXECUTION_METRICS["tools"]

    tool_summaries = {}
    for name, m in tools.items():
        avg_latency = m["total_latency_ms"] / m["calls"] if m["calls"] > 0 else 0
        tool_summaries[name] = {
            "calls": m["calls"],
            "success_rate": round(m["success"] / m["calls"] * 100, 1) if m["calls"] > 0 else 0,
            "avg_latency_ms": round(avg_latency, 2),
            "min_latency_ms": round(m["min_latency_ms"], 2) if m["min_latency_ms"] != float('inf') else 0,
            "max_latency_ms": round(m["max_latency_ms"], 2),
            "errors": m["errors"],
            "last_called": m["last_called"],
            "last_error": m["last_error"]
        }

    avg_global_latency = global_m["total_latency_ms"] / global_m["total_calls"] if global_m["total_calls"] > 0 else 0

    return {
        "summary": {
            "total_calls": global_m["total_calls"],
            "success_rate": round(global_m["total_success"] / global_m["total_calls"] * 100, 1) if global_m["total_calls"] > 0 else 0,
            "avg_latency_ms": round(avg_global_latency, 2),
            "uptime_seconds": round(time.time() - SERVER_START_TIME, 1),
            "started_at": global_m["started_at"]
        },
        "tools": tool_summaries
    }


def validate_path(path: str) -> tuple[bool, str]:
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


def truncate_output(output: str, max_size: int = MAX_OUTPUT_SIZE) -> tuple[str, bool]:
    """Truncate output if too large."""
    if len(output) > max_size:
        return output[:max_size] + f"\n\n... [TRUNCATED - {len(output)} total bytes]", True
    return output, False


# =============================================================================
# HEALTH ENDPOINT
# =============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    uptime = time.time() - SERVER_START_TIME
    return jsonify({
        "status": "healthy",
        "version": "4.1.1",
        "uptime_seconds": int(uptime),
        "pending_approvals": len(PENDING_APPROVALS),
        "active_tasks": len([t for t in BACKGROUND_TASKS.values() if t['status'] == 'running']),
        "total_tasks": len(BACKGROUND_TASKS),
        "saved_sessions": len(SESSION_CHECKPOINTS),
        "streaming_sessions": len(STREAMING_SESSIONS),
        "tracked_costs": len(SESSION_COSTS),
        "conversation_memories": len(CONVERSATION_MEMORIES),
        "custom_pipelines": len(TOOL_PIPELINES),
        "registered_webhooks": len(WEBHOOKS),
        "agent_templates": len(AGENT_TEMPLATES),
        "sub_agents": len(SUB_AGENTS),
        "orchestrations": len(ORCHESTRATIONS),
        "knowledge_bases": len(KNOWLEDGE_BASES),
        "scheduled_tasks": len(SCHEDULED_TASKS),
        "tool_plugins": len(TOOL_PLUGINS),
        "task_outcomes": len(TASK_OUTCOMES),
        "learning_entries": len(LEARNING_ENTRIES),
        "recorded_workflows": len(RECORDED_WORKFLOWS),
        "active_recordings": len(ACTIVE_RECORDINGS),
        "context_injection_rules": len(CONTEXT_INJECTION_RULES),
        "shared_states": len(SHARED_STATES),
        "agent_personas": len(AGENT_PERSONAS),
        "goals": len(GOALS),
        "tool_macros": len(TOOL_MACROS),
        "audit_entries": len(AUDIT_TRAIL),
        "behavior_profiles": len(BEHAVIOR_PROFILES),
        "discovered_tools": len(DISCOVERED_TOOLS),
        "error_solutions": len(ERROR_SOLUTIONS),
        "tool_usage_stats": len(TOOL_USAGE_STATS),
        "meta_knowledge_questions": len(META_KNOWLEDGE['pending_questions']),
        "meta_knowledge_patterns": len(META_KNOWLEDGE['learned_patterns']),
        "cache_stats": TOOL_CACHE.stats(),
        "persistence_enabled": PERSISTENCE_ENABLED,
        "persistence_file": str(PERSISTENCE_FILE),
        "features": [
            "task_persistence", "retry_logic", "context_management", "streaming_responses",
            "structured_errors", "execution_metrics", "parallel_tool_execution", "tool_result_caching",
            "smart_rate_limiting", "cost_token_tracking", "conversation_memory", "tool_pipelines",
            "webhook_notifications", "agent_templates", "multi_agent_orchestration", "knowledge_base_rag",
            "scheduled_tasks", "tool_plugins", "agent_learning_feedback", "workflow_recording_playback",
            "smart_context_injection", "inter_agent_communication", "agent_personas", "goal_decomposition",
            "tool_macros", "audit_trail", "adaptive_behavior"
        ],
        "integrations": ["n8n", "git_enhanced", "terminal_multi"],
        "extracted_towers": ["personal-assistant (gmail, sheets, sms) → port 5011", "lead-generation (clickup, pipeline) → port 5012"],
        "meta_agent": ["self_discovery", "tool_creation", "error_learning", "introspection", "suggestions"],
        "allowed_paths": ALLOWED_BASE_PATHS,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/metrics', methods=['GET', 'POST'])
def metrics():
    """Get execution metrics."""
    return jsonify({
        "success": True,
        **get_metrics_summary()
    })


@app.route('/metrics/reset', methods=['POST'])
def metrics_reset():
    """Reset execution metrics."""
    global EXECUTION_METRICS
    EXECUTION_METRICS = {
        "tools": {},
        "global": {
            "total_calls": 0,
            "total_success": 0,
            "total_errors": 0,
            "total_latency_ms": 0,
            "started_at": datetime.now().isoformat()
        }
    }
    return jsonify({"success": True, "message": "Metrics reset"})


# =============================================================================
# FILE OPERATIONS
# =============================================================================

@app.route('/files/read', methods=['POST'])
@track_metrics('file_read')
def files_read():
    """Read file contents."""
    data = request.get_json() or {}
    path = data.get('path')
    encoding = data.get('encoding', 'utf-8')
    limit_lines = data.get('limit_lines')
    offset = data.get('offset', 0)

    if not path:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "Missing required 'path' parameter",
            status_code=400,
            context={"endpoint": "/files/read", "required_params": ["path"]}
        )

    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return make_error_response(
            ErrorCode.PATH_NOT_ALLOWED,
            resolved_path,
            status_code=403,
            context={"requested_path": path},
            allowed_paths=", ".join(ALLOWED_BASE_PATHS)
        )

    try:
        file_path = Path(resolved_path)

        if not file_path.exists():
            return make_error_response(
                ErrorCode.FILE_NOT_FOUND,
                f"File not found: {path}",
                status_code=404,
                context={"requested_path": path, "resolved_path": resolved_path}
            )

        if not file_path.is_file():
            return make_error_response(
                ErrorCode.NOT_A_FILE,
                f"Path is a directory, not a file: {path}",
                status_code=400,
                context={"requested_path": path, "type": "directory"}
            )

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return make_error_response(
                ErrorCode.FILE_TOO_LARGE,
                f"File too large: {file_size:,} bytes (max {MAX_FILE_SIZE:,} bytes)",
                status_code=400,
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

        return make_success_response({
            "path": resolved_path,
            "content": content,
            "file_size": file_size,
            "encoding": encoding,
            "truncated": False
        })

    except UnicodeDecodeError as e:
        return make_error_response(
            ErrorCode.ENCODING_ERROR,
            f"Cannot decode file with encoding '{encoding}': {str(e)}",
            status_code=400,
            context={"requested_encoding": encoding, "file_path": path}
        )
    except PermissionError as e:
        return make_error_response(
            ErrorCode.PATH_NOT_ALLOWED,
            f"Permission denied reading file: {path}",
            status_code=403,
            context={"file_path": path, "error_type": "permission"},
            include_traceback=True
        )
    except Exception as e:
        return make_error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Unexpected error reading file: {str(e)}",
            status_code=500,
            context={"file_path": path, "error_type": type(e).__name__},
            include_traceback=True
        )


@app.route('/files/write', methods=['POST'])
@track_metrics('file_write')
def files_write():
    """Write file contents."""
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


@app.route('/files/edit', methods=['POST'])
@track_metrics('file_edit')
def files_edit():
    """Edit file with line-based operations."""
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


@app.route('/files/list', methods=['POST'])
def files_list():
    """List directory contents."""
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


# =============================================================================
# SEARCH OPERATIONS (Grep/Glob)
# =============================================================================

@app.route('/search/grep', methods=['POST'])
@track_metrics('grep')
def search_grep():
    """Search file contents using ripgrep or grep."""
    data = request.get_json() or {}
    pattern = data.get('pattern')
    path = data.get('path', ALLOWED_BASE_PATHS[0])
    file_type = data.get('type')  # e.g., 'py', 'js', 'ts'
    glob_pattern = data.get('glob')  # e.g., '*.py', '**/*.ts'
    context_before = data.get('context_before', 0)  # -B
    context_after = data.get('context_after', 0)  # -A
    context = data.get('context', 0)  # -C (both before and after)
    case_insensitive = data.get('case_insensitive', False)
    max_results = min(data.get('max_results', 100), 500)
    output_mode = data.get('output_mode', 'content')  # 'content', 'files_only', 'count'

    if not pattern:
        return jsonify({"success": False, "error": "Missing 'pattern' parameter"}), 400

    # Validate path
    valid, resolved_path = validate_path(path)
    if not valid:
        return jsonify({"success": False, "error": resolved_path}), 403

    try:
        # Build grep/rg command
        # Prefer ripgrep if available, fallback to grep
        rg_available = subprocess.run(['which', 'rg'], capture_output=True).returncode == 0

        if rg_available:
            cmd = ['rg', '--json' if output_mode == 'content' else '-l']
            if case_insensitive:
                cmd.append('-i')
            if context > 0:
                cmd.extend(['-C', str(context)])
            else:
                if context_before > 0:
                    cmd.extend(['-B', str(context_before)])
                if context_after > 0:
                    cmd.extend(['-A', str(context_after)])
            if file_type:
                cmd.extend(['--type', file_type])
            if glob_pattern:
                cmd.extend(['--glob', glob_pattern])
            cmd.extend(['-m', str(max_results)])  # Max matches
            cmd.append(pattern)
            cmd.append(resolved_path)
        else:
            # Fallback to grep
            cmd = ['grep', '-r', '-n']
            if case_insensitive:
                cmd.append('-i')
            if context > 0:
                cmd.extend(['-C', str(context)])
            else:
                if context_before > 0:
                    cmd.extend(['-B', str(context_before)])
                if context_after > 0:
                    cmd.extend(['-A', str(context_after)])
            if output_mode == 'files_only':
                cmd.append('-l')
            cmd.append(pattern)
            cmd.append(resolved_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse results
        matches = []
        if rg_available and output_mode == 'content':
            # Parse ripgrep JSON output
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if item.get('type') == 'match':
                        data = item.get('data', {})
                        matches.append({
                            "file": data.get('path', {}).get('text', ''),
                            "line_number": data.get('line_number'),
                            "text": data.get('lines', {}).get('text', '').rstrip()
                        })
                except json.JSONDecodeError:
                    continue
        elif output_mode == 'files_only':
            matches = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        else:
            # Parse standard grep output
            for line in result.stdout.strip().split('\n')[:max_results]:
                if not line:
                    continue
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    matches.append({
                        "file": parts[0],
                        "line_number": int(parts[1]) if parts[1].isdigit() else None,
                        "text": parts[2]
                    })

        output, truncated = truncate_output(result.stdout)

        return jsonify({
            "success": True,
            "pattern": pattern,
            "path": resolved_path,
            "matches": matches[:max_results],
            "match_count": len(matches),
            "truncated": truncated or len(matches) > max_results,
            "tool": "ripgrep" if rg_available else "grep"
        })

    except subprocess.TimeoutExpired:
        return make_error_response(
            ErrorCode.SEARCH_TIMEOUT,
            "Search timed out after 60 seconds",
            status_code=504,
            context={
                "pattern": pattern,
                "path": resolved_path,
                "suggestion": "Try a more specific pattern or narrow the search path"
            }
        )
    except Exception as e:
        return make_error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Search error: {str(e)}",
            status_code=500,
            context={"pattern": pattern, "path": resolved_path, "error_type": type(e).__name__},
            include_traceback=True
        )


@app.route('/files/glob', methods=['POST'])
@track_metrics('glob')
def files_glob():
    """Find files matching a glob pattern."""
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


@app.route('/search/web', methods=['POST'])
@track_metrics('web_search')
def search_web():
    """Search the web using DuckDuckGo or configured search API."""
    data = request.get_json() or {}
    query = data.get('query')
    max_results = min(data.get('max_results', 10), 20)
    search_type = data.get('type', 'web')  # 'web', 'news', 'images'

    if not query:
        return jsonify({"success": False, "error": "Missing 'query' parameter"}), 400

    try:
        # Try DuckDuckGo HTML search (no API key needed)
        import requests
        from bs4 import BeautifulSoup
        import urllib.parse

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # DuckDuckGo HTML search
        encoded_query = urllib.parse.quote_plus(query)
        url = f'https://html.duckduckgo.com/html/?q={encoded_query}'

        resp = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')

        results = []
        for result in soup.select('.result')[:max_results]:
            title_elem = result.select_one('.result__title')
            snippet_elem = result.select_one('.result__snippet')
            link_elem = result.select_one('.result__url')

            if title_elem:
                title = title_elem.get_text(strip=True)
                link = ''
                if link_elem:
                    link = link_elem.get_text(strip=True)
                    if not link.startswith('http'):
                        link = 'https://' + link
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                results.append({
                    "title": title,
                    "url": link,
                    "snippet": snippet
                })

        return jsonify({
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "source": "duckduckgo"
        })

    except ImportError:
        return jsonify({
            "success": False,
            "error": "Required packages not installed: pip install requests beautifulsoup4"
        }), 500
    except requests.Timeout:
        return jsonify({
            "success": False,
            "error": "Search timed out after 30 seconds"
        }), 504
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/files/delete', methods=['POST'])
def files_delete():
    """Delete a file (with optional approval)."""
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


# =============================================================================
# COMMAND EXECUTION
# =============================================================================

@app.route('/command/execute', methods=['POST'])
@track_metrics('command')
def command_execute():
    """Execute a bash command."""
    data = request.get_json() or {}
    command = data.get('command')
    cwd = data.get('cwd', ALLOWED_BASE_PATHS[0])
    timeout = min(data.get('timeout', COMMAND_TIMEOUT), 300)  # Max 5 minutes
    env = data.get('env', {})
    require_approval = data.get('require_approval', False)
    approval_id = data.get('approval_id')

    if not command:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "Missing required 'command' parameter",
            status_code=400,
            context={"endpoint": "/command/execute", "required_params": ["command"]}
        )

    # Validate working directory
    valid, resolved_cwd = validate_path(cwd)
    if not valid:
        return make_error_response(
            ErrorCode.PATH_NOT_ALLOWED,
            f"Working directory not allowed: {cwd}",
            status_code=403,
            context={"requested_cwd": cwd},
            allowed_paths=", ".join(ALLOWED_BASE_PATHS)
        )

    # Check for dangerous patterns
    dangerous_patterns = [
        'rm -rf /',
        'rm -rf ~',
        'rm -rf *',
        'mkfs',
        'dd if=',
        ':(){',
        'chmod -R 777 /',
        '> /dev/sda',
    ]

    matched_patterns = [p for p in dangerous_patterns if p in command.lower()]
    is_dangerous = len(matched_patterns) > 0

    # If dangerous or approval required, check for approval
    if (is_dangerous or require_approval) and not approval_id:
        approval_id = str(uuid.uuid4())
        PENDING_APPROVALS[approval_id] = {
            "id": approval_id,
            "type": "command",
            "command": command,
            "cwd": resolved_cwd,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "dangerous": is_dangerous,
            "matched_patterns": matched_patterns
        }
        return jsonify({
            "success": False,
            "approval_required": True,
            "approval_id": approval_id,
            "dangerous": is_dangerous,
            "matched_patterns": matched_patterns,
            "message": f"Approval required for command: {command}",
            "instructions": "POST to /approvals/decide with {approval_id, decision: 'approve' or 'deny'}"
        }), 202

    # Verify approval if provided
    if approval_id:
        approval = PENDING_APPROVALS.get(approval_id)
        if not approval:
            return make_error_response(
                ErrorCode.APPROVAL_INVALID,
                f"Approval ID not found: {approval_id}",
                status_code=403,
                context={"approval_id": approval_id, "command": command}
            )
        if approval.get('status') != 'approved':
            return make_error_response(
                ErrorCode.APPROVAL_INVALID,
                f"Approval has status '{approval.get('status')}', expected 'approved'",
                status_code=403,
                context={
                    "approval_id": approval_id,
                    "current_status": approval.get('status'),
                    "command": command
                }
            )

    try:
        # Merge environment
        full_env = os.environ.copy()
        full_env.update(env)

        # Execute command
        start_time = time.time()
        result = subprocess.run(
            command,
            shell=True,
            cwd=resolved_cwd,
            env=full_env,
            capture_output=True,
            timeout=timeout,
            text=True
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # Truncate output if needed
        stdout, stdout_truncated = truncate_output(result.stdout)
        stderr, stderr_truncated = truncate_output(result.stderr)

        # Clean up approval
        if approval_id and approval_id in PENDING_APPROVALS:
            del PENDING_APPROVALS[approval_id]

        # Return response (note: exit_code != 0 is not necessarily an error from the API's perspective)
        response_data = {
            "success": True,  # API call succeeded
            "command_success": result.returncode == 0,  # Command itself succeeded
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": result.returncode,
            "duration_ms": duration_ms,
            "cwd": resolved_cwd,
            "truncated": stdout_truncated or stderr_truncated
        }

        # Add helpful context if command failed
        if result.returncode != 0:
            response_data["command_error"] = {
                "exit_code": result.returncode,
                "stderr_preview": stderr[:500] if stderr else None,
                "suggestion": "Check stderr for error details. Common issues: missing dependencies, permission denied, syntax errors."
            }

        return jsonify(response_data)

    except subprocess.TimeoutExpired as e:
        return make_error_response(
            ErrorCode.COMMAND_TIMEOUT,
            f"Command timed out after {timeout} seconds",
            status_code=504,
            context={
                "command": command,
                "timeout_seconds": timeout,
                "cwd": resolved_cwd,
                "partial_stdout": e.stdout[:500] if e.stdout else None,
                "partial_stderr": e.stderr[:500] if e.stderr else None
            }
        )
    except FileNotFoundError:
        return make_error_response(
            ErrorCode.DIRECTORY_NOT_FOUND,
            f"Working directory not found: {resolved_cwd}",
            status_code=404,
            context={"cwd": resolved_cwd, "command": command}
        )
    except PermissionError:
        return make_error_response(
            ErrorCode.PATH_NOT_ALLOWED,
            f"Permission denied executing command in: {resolved_cwd}",
            status_code=403,
            context={"cwd": resolved_cwd, "command": command}
        )
    except Exception as e:
        return make_error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Unexpected error executing command: {str(e)}",
            status_code=500,
            context={
                "command": command,
                "cwd": resolved_cwd,
                "error_type": type(e).__name__
            },
            include_traceback=True
        )


# =============================================================================
# GIT OPERATIONS
# =============================================================================

@app.route('/git/status', methods=['POST'])
@track_metrics('git_status')
def git_status():
    """Get git status for a repository."""
    data = request.get_json() or {}
    repo_path = data.get('repo_path', ALLOWED_BASE_PATHS[0])

    # Validate path
    valid, resolved_path = validate_path(repo_path)
    if not valid:
        return make_error_response(
            ErrorCode.PATH_NOT_ALLOWED,
            f"Repository path not allowed: {repo_path}",
            status_code=403,
            context={"requested_path": repo_path},
            allowed_paths=", ".join(ALLOWED_BASE_PATHS)
        )

    try:
        # Check if it's a git repo
        git_dir = Path(resolved_path) / '.git'
        if not git_dir.exists():
            return make_error_response(
                ErrorCode.NOT_A_GIT_REPO,
                f"Not a git repository: {repo_path}",
                status_code=400,
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
        return make_error_response(
            ErrorCode.GIT_ERROR,
            f"Git command failed: {str(e)}",
            status_code=500,
            context={
                "repo_path": resolved_path,
                "stderr": e.stderr if hasattr(e, 'stderr') else None,
                "returncode": e.returncode
            }
        )
    except Exception as e:
        return make_error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Unexpected error getting git status: {str(e)}",
            status_code=500,
            context={"repo_path": resolved_path, "error_type": type(e).__name__},
            include_traceback=True
        )


@app.route('/git/commit', methods=['POST'])
def git_commit():
    """Commit changes to git."""
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


@app.route('/git/push', methods=['POST'])
def git_push():
    """Push to remote repository."""
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


@app.route('/git/diff', methods=['POST'])
def git_diff():
    """Get git diff."""
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


# =============================================================================
# WEB FETCH
# =============================================================================

@app.route('/web/fetch', methods=['POST'])
@track_metrics('web_fetch')
def web_fetch():
    """Fetch content from a URL."""
    data = request.get_json() or {}
    url = data.get('url')
    method = data.get('method', 'GET').upper()
    headers = data.get('headers', {})
    body = data.get('body')
    timeout = min(data.get('timeout', 30), 60)  # Max 60 seconds
    extract_text = data.get('extract_text', True)

    if not url:
        return jsonify({"success": False, "error": "Missing 'url' parameter"}), 400

    # Validate URL
    if not url.startswith(('http://', 'https://')):
        return jsonify({"success": False, "error": "URL must start with http:// or https://"}), 400

    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return jsonify({
            "success": False,
            "error": "Required packages not installed: pip install requests beautifulsoup4"
        }), 500

    try:
        # Make request
        start_time = time.time()

        if method == 'GET':
            resp = requests.get(url, headers=headers, timeout=timeout)
        elif method == 'POST':
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        else:
            return jsonify({"success": False, "error": f"Unsupported method: {method}"}), 400

        duration_ms = int((time.time() - start_time) * 1000)

        # Get content
        content_type = resp.headers.get('Content-Type', '')

        if extract_text and 'text/html' in content_type:
            # Parse HTML and extract text
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()

            # Get text
            text = soup.get_text(separator='\n', strip=True)

            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = '\n'.join(lines)

            # Truncate if too long
            text, truncated = truncate_output(text, 50000)

            return jsonify({
                "success": True,
                "url": url,
                "status_code": resp.status_code,
                "content_type": content_type,
                "text": text,
                "duration_ms": duration_ms,
                "truncated": truncated
            })
        else:
            # Return raw content (truncated)
            content, truncated = truncate_output(resp.text, 50000)

            return jsonify({
                "success": True,
                "url": url,
                "status_code": resp.status_code,
                "content_type": content_type,
                "content": content,
                "duration_ms": duration_ms,
                "truncated": truncated
            })

    except requests.Timeout:
        return make_error_response(
            ErrorCode.REQUEST_TIMEOUT,
            f"Request to {url} timed out after {timeout} seconds",
            status_code=504,
            context={"url": url, "method": method, "timeout_seconds": timeout}
        )
    except requests.ConnectionError as e:
        return make_error_response(
            ErrorCode.EXTERNAL_SERVICE_ERROR,
            f"Failed to connect to {url}: {str(e)}",
            status_code=502,
            context={"url": url, "method": method, "error_type": "connection_error"}
        )
    except requests.RequestException as e:
        return make_error_response(
            ErrorCode.EXTERNAL_SERVICE_ERROR,
            f"Request failed: {str(e)}",
            status_code=500,
            context={"url": url, "method": method, "error_type": type(e).__name__}
        )
    except Exception as e:
        return make_error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Unexpected error fetching URL: {str(e)}",
            status_code=500,
            context={"url": url, "method": method, "error_type": type(e).__name__},
            include_traceback=True
        )


# =============================================================================
# APPROVALS
# =============================================================================

@app.route('/approvals/pending', methods=['GET'])
def approvals_pending():
    """Get pending approvals."""
    pending = [
        a for a in PENDING_APPROVALS.values()
        if a.get('status') == 'pending'
    ]
    return jsonify({
        "pending": pending,
        "count": len(pending)
    })


@app.route('/approvals/decide', methods=['POST'])
def approvals_decide():
    """Approve or deny a pending action."""
    data = request.get_json() or {}
    approval_id = data.get('approval_id')
    decision = data.get('decision')  # "approve" or "deny"
    reason = data.get('reason', '')

    if not approval_id:
        return jsonify({"success": False, "error": "Missing 'approval_id'"}), 400

    if decision not in ['approve', 'deny']:
        return jsonify({"success": False, "error": "Decision must be 'approve' or 'deny'"}), 400

    approval = PENDING_APPROVALS.get(approval_id)
    if not approval:
        return jsonify({"success": False, "error": "Approval not found"}), 404

    # Update approval
    approval['status'] = 'approved' if decision == 'approve' else 'denied'
    approval['decided_at'] = datetime.now().isoformat()
    approval['reason'] = reason

    return jsonify({
        "success": True,
        "approval_id": approval_id,
        "status": approval['status']
    })


# =============================================================================
# TODO TRACKING
# =============================================================================

# In-memory todo storage (keyed by session_id) - loaded from persistence
TODO_LISTS: Dict[str, List[Dict[str, Any]]] = _persisted_state.get('todos', {})


@app.route('/todo/list', methods=['POST'])
def todo_list():
    """List all todos for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')

    todos = TODO_LISTS.get(session_id, [])

    # Calculate stats
    completed = len([t for t in todos if t['status'] == 'completed'])
    in_progress = len([t for t in todos if t['status'] == 'in_progress'])
    pending = len([t for t in todos if t['status'] == 'pending'])

    return jsonify({
        "success": True,
        "session_id": session_id,
        "todos": todos,
        "count": len(todos),
        "stats": {
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending
        }
    })


@app.route('/todo/add', methods=['POST'])
def todo_add():
    """Add a new todo item."""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    content = data.get('content')

    if not content:
        return jsonify({"success": False, "error": "Missing 'content' parameter"}), 400

    # Initialize session list if needed
    if session_id not in TODO_LISTS:
        TODO_LISTS[session_id] = []

    # Create todo
    todo_id = str(uuid.uuid4())[:8]
    todo = {
        "id": todo_id,
        "content": content,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    TODO_LISTS[session_id].append(todo)
    persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        "todo": todo,
        "message": f"Todo added: {content}"
    })


@app.route('/todo/update', methods=['POST'])
def todo_update():
    """Update a todo item's status."""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    todo_id = data.get('id')
    status = data.get('status')  # pending, in_progress, completed
    content = data.get('content')  # Optional: update content

    if not todo_id:
        return jsonify({"success": False, "error": "Missing 'id' parameter"}), 400

    if status and status not in ['pending', 'in_progress', 'completed']:
        return jsonify({"success": False, "error": "Invalid status. Use: pending, in_progress, completed"}), 400

    todos = TODO_LISTS.get(session_id, [])

    for todo in todos:
        if todo['id'] == todo_id:
            if status:
                todo['status'] = status
            if content:
                todo['content'] = content
            todo['updated_at'] = datetime.now().isoformat()
            persistence_manager.mark_dirty()

            return jsonify({
                "success": True,
                "todo": todo,
                "message": f"Todo updated: {todo['content']}"
            })

    return make_error_response(
        ErrorCode.TODO_NOT_FOUND,
        f"Todo not found: {todo_id}",
        status_code=404,
        context={"session_id": session_id, "requested_id": todo_id}
    )


@app.route('/todo/delete', methods=['POST'])
def todo_delete():
    """Delete a todo item."""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    todo_id = data.get('id')

    if not todo_id:
        return jsonify({"success": False, "error": "Missing 'id' parameter"}), 400

    todos = TODO_LISTS.get(session_id, [])

    for i, todo in enumerate(todos):
        if todo['id'] == todo_id:
            deleted = todos.pop(i)
            persistence_manager.mark_dirty()
            return jsonify({
                "success": True,
                "deleted": deleted,
                "message": f"Todo deleted: {deleted['content']}"
            })

    return make_error_response(
        ErrorCode.TODO_NOT_FOUND,
        f"Todo not found: {todo_id}",
        status_code=404,
        context={"session_id": session_id, "requested_id": todo_id}
    )


@app.route('/todo/clear', methods=['POST'])
def todo_clear():
    """Clear all todos for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')

    if session_id in TODO_LISTS:
        count = len(TODO_LISTS[session_id])
        TODO_LISTS[session_id] = []
        persistence_manager.mark_dirty()
        return jsonify({
            "success": True,
            "cleared": count,
            "message": f"Cleared {count} todos"
        })

    return jsonify({
        "success": True,
        "cleared": 0,
        "message": "No todos to clear"
    })


# =============================================================================
# SESSION CHECKPOINTS
# =============================================================================

# In-memory session storage (keyed by session_id) - loaded from persistence
SESSION_CHECKPOINTS: Dict[str, Dict[str, Any]] = _persisted_state.get('sessions', {})


@app.route('/session/save', methods=['POST'])
def session_save():
    """Save a session checkpoint."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    session_state = data.get('session_state')
    checkpoint_name = data.get('checkpoint_name', 'default')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id' parameter"}), 400
    if not session_state:
        return jsonify({"success": False, "error": "Missing 'session_state' parameter"}), 400

    # Initialize session if needed
    if session_id not in SESSION_CHECKPOINTS:
        SESSION_CHECKPOINTS[session_id] = {}

    # Save checkpoint with timestamp
    checkpoint = {
        "name": checkpoint_name,
        "state": session_state,
        "saved_at": datetime.now().isoformat(),
        "iteration": session_state.get('state', {}).get('iteration', 0)
    }

    SESSION_CHECKPOINTS[session_id][checkpoint_name] = checkpoint
    persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        "session_id": session_id,
        "checkpoint": checkpoint_name,
        "saved_at": checkpoint['saved_at'],
        "message": f"Session checkpoint saved: {checkpoint_name}"
    })


@app.route('/session/load', methods=['POST'])
def session_load():
    """Load a session checkpoint."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    checkpoint_name = data.get('checkpoint_name', 'default')

    if not session_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "Missing required 'session_id' parameter",
            status_code=400,
            context={"endpoint": "/session/load", "required_params": ["session_id"]}
        )

    if session_id not in SESSION_CHECKPOINTS:
        # List all available sessions in the error
        available_sessions = list(SESSION_CHECKPOINTS.keys())
        return make_error_response(
            ErrorCode.SESSION_NOT_FOUND,
            f"Session not found: {session_id}",
            status_code=404,
            context={
                "requested_session_id": session_id,
                "available_sessions": available_sessions[:10],  # Limit to 10
                "total_sessions": len(available_sessions)
            }
        )

    checkpoints = SESSION_CHECKPOINTS[session_id]
    if checkpoint_name not in checkpoints:
        return make_error_response(
            ErrorCode.CHECKPOINT_NOT_FOUND,
            f"Checkpoint not found: {checkpoint_name}",
            status_code=404,
            context={
                "session_id": session_id,
                "requested_checkpoint": checkpoint_name,
                "available_checkpoints": list(checkpoints.keys())
            }
        )

    checkpoint = checkpoints[checkpoint_name]

    return make_success_response({
        "session_id": session_id,
        "checkpoint": checkpoint_name,
        "session_state": checkpoint['state'],
        "saved_at": checkpoint['saved_at'],
        "iteration": checkpoint['iteration']
    }, message=f"Checkpoint '{checkpoint_name}' loaded successfully")


@app.route('/session/list', methods=['POST'])
def session_list():
    """List all saved sessions and their checkpoints."""
    data = request.get_json() or {}
    session_id = data.get('session_id')  # Optional: filter by session

    if session_id:
        if session_id not in SESSION_CHECKPOINTS:
            return jsonify({
                "success": True,
                "sessions": [],
                "message": f"No checkpoints found for session: {session_id}"
            })

        checkpoints = SESSION_CHECKPOINTS[session_id]
        return jsonify({
            "success": True,
            "session_id": session_id,
            "checkpoints": [
                {
                    "name": name,
                    "saved_at": cp['saved_at'],
                    "iteration": cp['iteration']
                }
                for name, cp in checkpoints.items()
            ]
        })

    # List all sessions
    sessions = []
    for sid, checkpoints in SESSION_CHECKPOINTS.items():
        sessions.append({
            "session_id": sid,
            "checkpoint_count": len(checkpoints),
            "checkpoints": list(checkpoints.keys()),
            "latest_save": max(cp['saved_at'] for cp in checkpoints.values()) if checkpoints else None
        })

    return jsonify({
        "success": True,
        "session_count": len(sessions),
        "sessions": sessions
    })


@app.route('/session/delete', methods=['POST'])
def session_delete():
    """Delete a session or checkpoint."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    checkpoint_name = data.get('checkpoint_name')  # Optional: delete specific checkpoint

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id' parameter"}), 400

    if session_id not in SESSION_CHECKPOINTS:
        return jsonify({"success": False, "error": f"Session not found: {session_id}"}), 404

    if checkpoint_name:
        # Delete specific checkpoint
        if checkpoint_name in SESSION_CHECKPOINTS[session_id]:
            del SESSION_CHECKPOINTS[session_id][checkpoint_name]
            persistence_manager.mark_dirty()
            return jsonify({
                "success": True,
                "deleted": checkpoint_name,
                "message": f"Checkpoint deleted: {checkpoint_name}"
            })
        return make_error_response(
            ErrorCode.CHECKPOINT_NOT_FOUND,
            f"Checkpoint not found: {checkpoint_name}",
            status_code=404,
            context={"session_id": session_id, "checkpoint_name": checkpoint_name}
        )

    # Delete entire session
    checkpoint_count = len(SESSION_CHECKPOINTS[session_id])
    del SESSION_CHECKPOINTS[session_id]
    persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        "deleted_session": session_id,
        "checkpoints_deleted": checkpoint_count,
        "message": f"Session deleted with {checkpoint_count} checkpoints"
    })


# =============================================================================
# BACKGROUND TASKS
# =============================================================================

# In-memory storage for background task results (keyed by task_id) - loaded from persistence
BACKGROUND_TASKS: Dict[str, Dict[str, Any]] = _persisted_state.get('tasks', {})


@app.route('/task/create', methods=['POST'])
def task_create():
    """Create a background task entry (called when workflow starts)."""
    data = request.get_json() or {}
    task_id = data.get('task_id') or f"task_{uuid.uuid4().hex[:12]}"
    session_id = data.get('session_id')
    task_objective = data.get('objective', 'Unknown task')

    BACKGROUND_TASKS[task_id] = {
        "task_id": task_id,
        "session_id": session_id,
        "objective": task_objective,
        "status": "running",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "result": None,
        "error": None,
        "iterations": 0
    }
    persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        "task_id": task_id,
        "status": "running",
        "message": "Background task created"
    })


@app.route('/task/update', methods=['POST'])
def task_update():
    """Update a background task (progress, result, or error)."""
    data = request.get_json() or {}
    task_id = data.get('task_id')

    if not task_id:
        return jsonify({"success": False, "error": "Missing 'task_id' parameter"}), 400

    if task_id not in BACKGROUND_TASKS:
        return jsonify({"success": False, "error": f"Task not found: {task_id}"}), 404

    task = BACKGROUND_TASKS[task_id]

    # Update fields if provided
    if 'status' in data:
        task['status'] = data['status']
    if 'result' in data:
        task['result'] = data['result']
    if 'error' in data:
        task['error'] = data['error']
    if 'iterations' in data:
        task['iterations'] = data['iterations']

    task['updated_at'] = datetime.now().isoformat()
    persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        "task_id": task_id,
        "status": task['status'],
        "message": "Task updated"
    })


@app.route('/task/status', methods=['POST'])
def task_status():
    """Get status of a background task."""
    data = request.get_json() or {}
    task_id = data.get('task_id')

    if not task_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "Missing required 'task_id' parameter",
            status_code=400,
            context={"endpoint": "/task/status", "required_params": ["task_id"]}
        )

    if task_id not in BACKGROUND_TASKS:
        # List recent tasks for context
        recent_tasks = sorted(
            BACKGROUND_TASKS.items(),
            key=lambda x: x[1]['created_at'],
            reverse=True
        )[:5]
        return make_error_response(
            ErrorCode.TASK_NOT_FOUND,
            f"Task not found: {task_id}",
            status_code=404,
            context={
                "requested_task_id": task_id,
                "recent_task_ids": [t[0] for t in recent_tasks],
                "total_tasks": len(BACKGROUND_TASKS)
            }
        )

    task = BACKGROUND_TASKS[task_id]

    return make_success_response({
        "task_id": task_id,
        "session_id": task['session_id'],
        "objective": task['objective'],
        "status": task['status'],
        "created_at": task['created_at'],
        "updated_at": task['updated_at'],
        "iterations": task['iterations'],
        "has_result": task['result'] is not None,
        "has_error": task['error'] is not None
    })


@app.route('/task/result', methods=['POST'])
def task_result():
    """Get full result of a completed background task."""
    data = request.get_json() or {}
    task_id = data.get('task_id')

    if not task_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "Missing required 'task_id' parameter",
            status_code=400,
            context={"endpoint": "/task/result", "required_params": ["task_id"]}
        )

    if task_id not in BACKGROUND_TASKS:
        return make_error_response(
            ErrorCode.TASK_NOT_FOUND,
            f"Task not found: {task_id}",
            status_code=404,
            context={"requested_task_id": task_id}
        )

    task = BACKGROUND_TASKS[task_id]

    if task['status'] == 'running':
        # Calculate runtime
        created = datetime.fromisoformat(task['created_at'])
        runtime_seconds = (datetime.now() - created).total_seconds()

        return make_success_response({
            "task_id": task_id,
            "status": "running",
            "iterations": task['iterations'],
            "runtime_seconds": round(runtime_seconds, 1),
            "estimated_progress": f"{task['iterations']} iterations completed"
        }, message="Task is still running. Poll again for updates.")

    return make_success_response({
        "task_id": task_id,
        "session_id": task['session_id'],
        "objective": task['objective'],
        "status": task['status'],
        "result": task['result'],
        "error": task['error'],
        "iterations": task['iterations'],
        "created_at": task['created_at'],
        "completed_at": task['updated_at']
    })


@app.route('/task/list', methods=['POST'])
def task_list():
    """List all background tasks."""
    data = request.get_json() or {}
    status_filter = data.get('status')  # Optional: filter by status

    tasks = []
    for task_id, task in BACKGROUND_TASKS.items():
        if status_filter and task['status'] != status_filter:
            continue
        tasks.append({
            "task_id": task_id,
            "objective": task['objective'],
            "status": task['status'],
            "created_at": task['created_at'],
            "iterations": task['iterations']
        })

    return jsonify({
        "success": True,
        "task_count": len(tasks),
        "tasks": sorted(tasks, key=lambda x: x['created_at'], reverse=True)
    })


# =============================================================================
# CONTEXT MANAGEMENT ENDPOINTS
# =============================================================================

@app.route('/context/truncate', methods=['POST'])
def context_truncate():
    """Truncate conversation history to fit within token limits."""
    data = request.get_json() or {}
    messages = data.get('messages', [])
    max_tokens = data.get('max_tokens', EFFECTIVE_CONTEXT_TOKENS)
    preserve_first = data.get('preserve_first', 1)
    preserve_last = data.get('preserve_last', 3)

    if not messages:
        return jsonify({
            "success": True,
            "messages": [],
            "truncation_info": {"truncated": False, "original_count": 0, "new_count": 0}
        })

    truncated_messages, info = truncate_conversation_history(
        messages,
        max_tokens=max_tokens,
        preserve_first_n=preserve_first,
        preserve_last_n=preserve_last
    )

    return jsonify({
        "success": True,
        "messages": truncated_messages,
        "truncation_info": info
    })


@app.route('/context/estimate', methods=['POST'])
def context_estimate():
    """Estimate token count for messages."""
    data = request.get_json() or {}
    messages = data.get('messages', [])
    text = data.get('text', '')

    if text:
        tokens = estimate_tokens(text)
        return jsonify({
            "success": True,
            "text_length": len(text),
            "estimated_tokens": tokens,
            "percent_of_limit": round(tokens / EFFECTIVE_CONTEXT_TOKENS * 100, 1)
        })

    if messages:
        total_tokens = sum(estimate_message_tokens(m) for m in messages)
        return jsonify({
            "success": True,
            "message_count": len(messages),
            "estimated_tokens": total_tokens,
            "percent_of_limit": round(total_tokens / EFFECTIVE_CONTEXT_TOKENS * 100, 1),
            "tokens_remaining": max(0, EFFECTIVE_CONTEXT_TOKENS - total_tokens),
            "should_truncate": total_tokens > EFFECTIVE_CONTEXT_TOKENS * 0.8
        })

    return jsonify({
        "success": True,
        "max_tokens": EFFECTIVE_CONTEXT_TOKENS,
        "chars_per_token": CHARS_PER_TOKEN
    })


# =============================================================================
# STREAMING RESPONSES
# =============================================================================

# Active streaming sessions
STREAMING_SESSIONS: Dict[str, Dict[str, Any]] = {}


@app.route('/stream/start', methods=['POST'])
def stream_start():
    """Start a streaming session for real-time updates."""
    data = request.get_json() or {}
    session_id = data.get('session_id') or f"stream_{uuid.uuid4().hex[:8]}"
    task_id = data.get('task_id')

    STREAMING_SESSIONS[session_id] = {
        "session_id": session_id,
        "task_id": task_id,
        "created_at": datetime.now().isoformat(),
        "events": [],
        "closed": False
    }

    return jsonify({
        "success": True,
        "session_id": session_id,
        "stream_url": f"/stream/events/{session_id}",
        "message": "Streaming session created. Connect to stream_url for events."
    })


@app.route('/stream/push', methods=['POST'])
def stream_push():
    """Push an event to a streaming session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    event_type = data.get('type', 'message')
    event_data = data.get('data', {})

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id' parameter"}), 400

    if session_id not in STREAMING_SESSIONS:
        return jsonify({"success": False, "error": f"Streaming session not found: {session_id}"}), 404

    session = STREAMING_SESSIONS[session_id]
    if session['closed']:
        return jsonify({"success": False, "error": "Streaming session is closed"}), 400

    event = {
        "id": str(uuid.uuid4())[:8],
        "type": event_type,
        "data": event_data,
        "timestamp": datetime.now().isoformat()
    }
    session['events'].append(event)

    return jsonify({
        "success": True,
        "event_id": event['id'],
        "session_id": session_id
    })


@app.route('/stream/events/<session_id>', methods=['GET'])
def stream_events(session_id: str):
    """SSE endpoint for streaming events."""
    if session_id not in STREAMING_SESSIONS:
        return jsonify({"error": f"Streaming session not found: {session_id}"}), 404

    def generate() -> Generator[str, None, None]:
        """Generate SSE events."""
        session = STREAMING_SESSIONS[session_id]
        last_event_index = 0

        # Send initial connection event
        yield f"event: connected\ndata: {json.dumps({'session_id': session_id})}\n\n"

        while not session['closed']:
            # Check for new events
            if len(session['events']) > last_event_index:
                for event in session['events'][last_event_index:]:
                    yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"
                last_event_index = len(session['events'])

            # Small sleep to prevent busy waiting
            time.sleep(0.1)

        # Send close event
        yield f"event: close\ndata: {json.dumps({'reason': 'session_closed'})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route('/stream/close', methods=['POST'])
def stream_close():
    """Close a streaming session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id' parameter"}), 400

    if session_id not in STREAMING_SESSIONS:
        return jsonify({"success": False, "error": f"Streaming session not found: {session_id}"}), 404

    STREAMING_SESSIONS[session_id]['closed'] = True

    # Clean up old sessions (keep for 5 minutes for late subscribers)
    # In production, would use a background task
    return jsonify({
        "success": True,
        "session_id": session_id,
        "message": "Streaming session closed"
    })


@app.route('/stream/list', methods=['GET', 'POST'])
def stream_list():
    """List active streaming sessions."""
    sessions = [
        {
            "session_id": s['session_id'],
            "task_id": s['task_id'],
            "created_at": s['created_at'],
            "event_count": len(s['events']),
            "closed": s['closed']
        }
        for s in STREAMING_SESSIONS.values()
    ]

    return jsonify({
        "success": True,
        "session_count": len(sessions),
        "sessions": sessions
    })


# =============================================================================
# RETRY ENDPOINT
# =============================================================================

@app.route('/retry/execute', methods=['POST'])
def retry_execute():
    """Execute an operation with automatic retry and exponential backoff."""
    data = request.get_json() or {}
    endpoint = data.get('endpoint')
    method = data.get('method', 'POST')
    payload = data.get('payload', {})
    max_retries = min(data.get('max_retries', 3), 5)
    base_delay = data.get('base_delay', 1.0)

    if not endpoint:
        return jsonify({"success": False, "error": "Missing 'endpoint' parameter"}), 400

    # Execute with retry
    import requests as req_lib
    from urllib.parse import urljoin

    base_url = f"http://127.0.0.1:{DEFAULT_PORT}"
    full_url = urljoin(base_url, endpoint)

    last_error = None
    attempts = []

    for attempt in range(max_retries + 1):
        try:
            start_time = time.time()
            if method.upper() == 'GET':
                resp = req_lib.get(full_url, timeout=60)
            else:
                resp = req_lib.post(full_url, json=payload, timeout=60)

            latency_ms = (time.time() - start_time) * 1000

            attempts.append({
                "attempt": attempt + 1,
                "status_code": resp.status_code,
                "latency_ms": round(latency_ms, 2),
                "success": resp.ok
            })

            if resp.ok:
                return jsonify({
                    "success": True,
                    "result": resp.json(),
                    "attempts": attempts,
                    "total_attempts": attempt + 1
                })

            # Non-success status code
            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            attempts.append({
                "attempt": attempt + 1,
                "error": str(e),
                "latency_ms": round(latency_ms, 2),
                "success": False
            })
            last_error = str(e)

        # Calculate backoff delay
        if attempt < max_retries:
            import random
            delay = min(base_delay * (2 ** attempt), 30.0)
            delay = delay * (0.75 + random.random() * 0.5)  # Add jitter
            time.sleep(delay)

    return jsonify({
        "success": False,
        "error": f"All {max_retries + 1} attempts failed. Last error: {last_error}",
        "attempts": attempts,
        "total_attempts": len(attempts)
    }), 500


# =============================================================================
# v3.6: PARALLEL TOOL EXECUTION ENDPOINTS
# =============================================================================

@app.route('/tools/parallel', methods=['POST'])
def tools_parallel():
    """Execute multiple tools in parallel."""
    data = request.get_json() or {}
    tool_calls = data.get('tools', [])
    max_parallel = min(data.get('max_parallel', 5), 10)
    timeout = min(data.get('timeout', 60), 120)

    if not tool_calls:
        return jsonify({"success": False, "error": "No tools specified"}), 400

    if len(tool_calls) > 20:
        return jsonify({"success": False, "error": "Maximum 20 parallel tools allowed"}), 400

    result = execute_tools_parallel(tool_calls, max_parallel=max_parallel, timeout=timeout)

    return jsonify({
        "success": True,
        **result
    })


# =============================================================================
# v3.6: CACHE ENDPOINTS
# =============================================================================

@app.route('/cache/stats', methods=['GET', 'POST'])
def cache_stats():
    """Get cache statistics."""
    return jsonify({
        "success": True,
        **TOOL_CACHE.stats()
    })


@app.route('/cache/clear', methods=['POST'])
def cache_clear():
    """Clear entire cache or by pattern."""
    data = request.get_json() or {}
    pattern = data.get('pattern')

    if pattern:
        count = TOOL_CACHE.invalidate_pattern(pattern)
        return jsonify({
            "success": True,
            "cleared": count,
            "pattern": pattern
        })

    count = TOOL_CACHE.clear()
    return jsonify({
        "success": True,
        "cleared": count,
        "message": "Cache cleared"
    })


@app.route('/cache/get', methods=['POST'])
def cache_get():
    """Get value from cache."""
    data = request.get_json() or {}
    key = data.get('key')

    if not key:
        return jsonify({"success": False, "error": "Missing 'key' parameter"}), 400

    value = TOOL_CACHE.get(key)
    if value is None:
        return jsonify({"success": True, "found": False, "value": None})

    return jsonify({"success": True, "found": True, "value": value})


@app.route('/cache/set', methods=['POST'])
def cache_set():
    """Set value in cache."""
    data = request.get_json() or {}
    key = data.get('key')
    value = data.get('value')
    ttl = data.get('ttl')

    if not key:
        return jsonify({"success": False, "error": "Missing 'key' parameter"}), 400

    TOOL_CACHE.set(key, value, ttl)
    return jsonify({"success": True, "key": key, "ttl": ttl or TOOL_CACHE.default_ttl})


# =============================================================================
# v3.6: RATE LIMITING ENDPOINTS
# =============================================================================

@app.route('/ratelimit/stats', methods=['GET', 'POST'])
def ratelimit_stats():
    """Get rate limiter statistics."""
    stats = {}
    for name, limiter in RATE_LIMITERS.items():
        stats[name] = limiter.stats()

    return jsonify({
        "success": True,
        "limiters": stats
    })


@app.route('/ratelimit/acquire', methods=['POST'])
def ratelimit_acquire():
    """Acquire tokens from a rate limiter."""
    data = request.get_json() or {}
    category = data.get('category', 'default')
    tokens = data.get('tokens', 1)
    wait = data.get('wait', True)
    timeout = min(data.get('timeout', 30), 60)

    limiter = get_rate_limiter(category)
    acquired = limiter.acquire(tokens=tokens, wait=wait, timeout=timeout)

    return jsonify({
        "success": True,
        "acquired": acquired,
        "category": category,
        "tokens_requested": tokens
    })


# [EXTRACTED to ai-systems tower] Lines 5536-5741 (206 lines)

# =============================================================================
# v3.7: TOOL PIPELINE ENDPOINTS
# =============================================================================

@app.route('/pipeline/list', methods=['GET', 'POST'])
def pipeline_list():
    """List all available pipelines (built-in and custom)."""
    pipelines = []

    # Add built-in pipelines
    for name, pipeline in BUILTIN_PIPELINES.items():
        pipelines.append({
            "name": name,
            "type": "builtin",
            "description": pipeline.get("description", ""),
            "step_count": len(pipeline.get("steps", []))
        })

    # Add custom pipelines
    for name, pipeline in TOOL_PIPELINES.items():
        pipelines.append({
            "name": name,
            "type": "custom",
            "step_count": len(pipeline.steps),
            "created_at": pipeline.created_at
        })

    return jsonify({
        "success": True,
        "pipelines": pipelines,
        "total": len(pipelines)
    })


@app.route('/pipeline/create', methods=['POST'])
def pipeline_create():
    """Create a custom pipeline."""
    data = request.get_json() or {}
    name = data.get('name')
    steps = data.get('steps', [])

    if not name:
        return jsonify({"success": False, "error": "Missing 'name' parameter"}), 400
    if not steps:
        return jsonify({"success": False, "error": "Missing 'steps' parameter"}), 400
    if name in BUILTIN_PIPELINES:
        return jsonify({"success": False, "error": "Cannot overwrite built-in pipeline"}), 400

    pipeline = ToolPipeline(name=name, steps=steps)
    TOOL_PIPELINES[name] = pipeline

    return jsonify({
        "success": True,
        **pipeline.to_dict()
    })


@app.route('/pipeline/execute', methods=['POST'])
def pipeline_execute():
    """Execute a pipeline with given inputs."""
    import requests as req_lib

    data = request.get_json() or {}
    name = data.get('name')
    inputs = data.get('inputs', {})

    if not name:
        return jsonify({"success": False, "error": "Missing 'name' parameter"}), 400

    # Get pipeline (check custom first, then built-in)
    if name in TOOL_PIPELINES:
        pipeline = TOOL_PIPELINES[name]
        steps = pipeline.steps
    elif name in BUILTIN_PIPELINES:
        steps = BUILTIN_PIPELINES[name].get("steps", [])
    else:
        return jsonify({"success": False, "error": f"Pipeline '{name}' not found"}), 404

    # Execute steps in sequence
    context = dict(inputs)  # Start with provided inputs
    results = []
    start_time = time.time()

    for i, step in enumerate(steps):
        tool_name = step.get("tool")
        input_template = step.get("input_template", step.get("input", {}))
        output_key = step.get("output_key", f"step_{i}_result")

        # Substitute context variables in input
        tool_input = {}
        for key, value in input_template.items():
            if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                # Variable substitution
                var_name = value[1:-1]
                if "[" in var_name:
                    # Handle array indexing like {files[0]}
                    base, idx = var_name.split("[")
                    idx = int(idx.rstrip("]"))
                    tool_input[key] = context.get(base, [])[idx] if base in context else value
                else:
                    tool_input[key] = context.get(var_name, value)
            else:
                tool_input[key] = value

        # Execute tool
        endpoint_map = {
            'file_read': '/files/read',
            'file_write': '/files/write',
            'grep': '/search/grep',
            'glob': '/files/glob',
            'command': '/command/execute',
            'web_search': '/search/web',
            'web_fetch': '/web/fetch',
        }

        endpoint = endpoint_map.get(tool_name)
        if not endpoint:
            results.append({"step": i, "tool": tool_name, "error": "Unknown tool"})
            break

        try:
            base_url = f"http://127.0.0.1:{DEFAULT_PORT}"
            resp = req_lib.post(f"{base_url}{endpoint}", json=tool_input, timeout=60)
            result = resp.json()

            if result.get("success"):
                # Store result in context for next step
                if "content" in result:
                    context[output_key] = result["content"]
                elif "files" in result:
                    context[output_key] = result["files"]
                elif "matches" in result:
                    context[output_key] = result["matches"]
                else:
                    context[output_key] = result

                results.append({"step": i, "tool": tool_name, "success": True, "output_key": output_key})
            else:
                results.append({"step": i, "tool": tool_name, "success": False, "error": result.get("error")})
                break
        except Exception as e:
            results.append({"step": i, "tool": tool_name, "success": False, "error": str(e)})
            break

    total_time = (time.time() - start_time) * 1000

    return jsonify({
        "success": all(r.get("success", False) for r in results),
        "pipeline": name,
        "results": results,
        "context": context,
        "total_time_ms": round(total_time, 2)
    })


# =============================================================================
# v3.7: WEBHOOK NOTIFICATION ENDPOINTS
# =============================================================================

@app.route('/webhook/register', methods=['POST'])
def webhook_register():
    """Register a webhook for notifications."""
    data = request.get_json() or {}
    url = data.get('url')
    events = data.get('events', ['task_complete', 'task_error'])
    headers = data.get('headers', {})

    if not url:
        return jsonify({"success": False, "error": "Missing 'url' parameter"}), 400

    webhook_id = f"wh_{uuid.uuid4().hex[:8]}"
    webhook = WebhookConfig(
        url=url,
        events=events,
        headers=headers,
        retry_count=data.get('retry_count', 3)
    )
    WEBHOOKS[webhook_id] = webhook

    return jsonify({
        "success": True,
        "webhook_id": webhook_id,
        **webhook.to_dict()
    })


@app.route('/webhook/list', methods=['GET', 'POST'])
def webhook_list():
    """List all registered webhooks."""
    webhooks = []
    for webhook_id, webhook in WEBHOOKS.items():
        webhooks.append({
            "webhook_id": webhook_id,
            **webhook.to_dict()
        })

    return jsonify({
        "success": True,
        "webhooks": webhooks,
        "total": len(webhooks)
    })


@app.route('/webhook/delete', methods=['POST'])
def webhook_delete():
    """Delete a registered webhook."""
    data = request.get_json() or {}
    webhook_id = data.get('webhook_id')

    if not webhook_id:
        return jsonify({"success": False, "error": "Missing 'webhook_id' parameter"}), 400

    if webhook_id in WEBHOOKS:
        del WEBHOOKS[webhook_id]
        return jsonify({"success": True, "deleted": True})

    return jsonify({"success": True, "deleted": False, "message": "Webhook not found"})


@app.route('/webhook/test', methods=['POST'])
def webhook_test():
    """Send a test notification to a webhook."""
    data = request.get_json() or {}
    webhook_id = data.get('webhook_id')

    if not webhook_id:
        return jsonify({"success": False, "error": "Missing 'webhook_id' parameter"}), 400

    if webhook_id not in WEBHOOKS:
        return jsonify({"success": False, "error": "Webhook not found"}), 404

    # Send test notification
    results = send_webhook_notification("test", {
        "message": "This is a test notification",
        "webhook_id": webhook_id,
        "timestamp": datetime.now().isoformat()
    })

    return jsonify({
        "success": True,
        "results": results
    })


@app.route('/webhook/notify', methods=['POST'])
def webhook_notify():
    """Manually send a notification to webhooks."""
    data = request.get_json() or {}
    event = data.get('event', 'custom')
    payload = data.get('payload', {})

    results = send_webhook_notification(event, payload)

    return jsonify({
        "success": True,
        "event": event,
        "notifications_sent": len(results),
        "results": results
    })


# [EXTRACTED to ai-systems tower] Lines 6003-7871 (1869 lines)

# =============================================================================
# STATE MANAGEMENT
# =============================================================================

def get_current_state() -> Dict[str, Any]:
    """Get current state for persistence."""
    # Serialize conversation memories
    memories = {k: v.to_dict() for k, v in CONVERSATION_MEMORIES.items()}
    # Serialize pipelines
    pipelines = {k: v.to_dict() for k, v in TOOL_PIPELINES.items()}
    # Serialize webhooks
    webhooks = {k: v.to_dict() for k, v in WEBHOOKS.items()}

    return {
        "tasks": BACKGROUND_TASKS,
        "sessions": SESSION_CHECKPOINTS,
        "todos": TODO_LISTS,
        "approvals": PENDING_APPROVALS,
        "metrics": EXECUTION_METRICS,
        "memories": memories,
        "pipelines": pipelines,
        "webhooks": webhooks,
        "saved_at": datetime.now().isoformat()
    }


@app.route('/state/export', methods=['GET', 'POST'])
def state_export():
    """Export current state for backup."""
    state = get_current_state()
    return jsonify({
        "success": True,
        "state": state,
        "exported_at": datetime.now().isoformat()
    })


@app.route('/state/import', methods=['POST'])
def state_import():
    """Import state from backup (dangerous - requires confirmation)."""
    global BACKGROUND_TASKS, SESSION_CHECKPOINTS, TODO_LISTS, PENDING_APPROVALS, EXECUTION_METRICS

    data = request.get_json() or {}
    state = data.get('state')
    confirm = data.get('confirm', False)

    if not state:
        return jsonify({"success": False, "error": "Missing 'state' parameter"}), 400

    if not confirm:
        return jsonify({
            "success": False,
            "error": "State import requires confirmation",
            "message": "Set 'confirm': true to proceed. This will overwrite all current state.",
            "current_counts": {
                "tasks": len(BACKGROUND_TASKS),
                "sessions": len(SESSION_CHECKPOINTS),
                "todos": len(TODO_LISTS)
            }
        }), 400

    BACKGROUND_TASKS = state.get('tasks', {})
    SESSION_CHECKPOINTS = state.get('sessions', {})
    TODO_LISTS = state.get('todos', {})
    PENDING_APPROVALS = state.get('approvals', {})
    if 'metrics' in state:
        EXECUTION_METRICS = state['metrics']

    persistence_manager.save(get_current_state(), force=True)

    return jsonify({
        "success": True,
        "imported_at": datetime.now().isoformat(),
        "counts": {
            "tasks": len(BACKGROUND_TASKS),
            "sessions": len(SESSION_CHECKPOINTS),
            "todos": len(TODO_LISTS)
        }
    })


@app.route('/state/persist', methods=['POST'])
def state_persist():
    """Force save current state to disk."""
    state = get_current_state()
    success = persistence_manager.save(state, force=True)

    return jsonify({
        "success": success,
        "file": str(PERSISTENCE_FILE),
        "saved_at": datetime.now().isoformat() if success else None
    })


# [EXTRACTED to ai-systems tower] Lines 7966-8242 (277 lines)

# =============================================================================
# SELF-ANNEALING META-AGENT CAPABILITIES
# =============================================================================

@app.route('/meta/capabilities', methods=['GET', 'POST'])
def meta_capabilities():
    """List all available capabilities and tools."""
    capabilities = {
        'core_tools': ['file_read', 'file_write', 'file_edit', 'command', 'git_status', 'grep', 'glob', 'web_search', 'web_fetch', 'todo', 'checkpoint'],
        'integrations': {
            'personal-assistant (port 5011)': ['gmail/*', 'sheets/*', 'sms/*'],
            'lead-generation (port 5012)': ['clickup/*', 'pipeline/*'],
            'n8n': ['n8n/list-workflows', 'n8n/get-workflow', 'n8n/create-workflow', 'n8n/update-workflow', 'n8n/activate-workflow', 'n8n/execute-workflow'],
            'git': ['git/clone', 'git/pull', 'git/branch', 'git/log', 'git/status', 'git/commit', 'git/push', 'git/diff'],
            'terminal': ['command/execute', 'terminal/multi-command', 'terminal/script']
        },
        'meta_capabilities': {
            'self_discovery': '/meta/discover - Find new integrations and tools',
            'tool_creation': '/meta/create-tool - Generate new tool code',
            'error_learning': '/meta/learn-error - Store solutions to errors',
            'introspection': '/meta/introspect - Analyze agent behavior',
            'suggestion': '/meta/suggest - Get improvement suggestions'
        },
        'discovered_tools': list(DISCOVERED_TOOLS.keys()),
        'error_solutions': len(ERROR_SOLUTIONS),
        'usage_stats': len(TOOL_USAGE_STATS)
    }
    return jsonify({"success": True, "capabilities": capabilities})


@app.route('/meta/discover', methods=['POST'])
def meta_discover():
    """Discover new integrations and tools based on available credentials and files."""
    discoveries = []
    cred_checks = [
        ('OPENAI_API_KEY', 'OpenAI API', 'GPT models, embeddings, DALL-E'),
        ('ANTHROPIC_API_KEY', 'Anthropic API', 'Claude models'),
        ('STRIPE_API_KEY', 'Stripe API', 'Payments, subscriptions'),
        ('SLACK_BOT_TOKEN', 'Slack API', 'Messaging, channels'),
        ('NOTION_API_KEY', 'Notion API', 'Databases, pages'),
        ('SENDGRID_API_KEY', 'SendGrid API', 'Email delivery'),
        ('SHOPIFY_API_KEY', 'Shopify API', 'E-commerce'),
    ]
    for env_var, name, capabilities in cred_checks:
        if os.getenv(env_var):
            discoveries.append({'type': 'credential', 'name': name, 'capabilities': capabilities, 'env_var': env_var})
    project_dirs = Path('/Users/williammarceaujr./dev-sandbox/projects').glob('*/*')
    for project_dir in project_dirs:
        if project_dir.is_dir() and (project_dir / 'src').exists():
            for py_file in (project_dir / 'src').glob('*.py'):
                if not py_file.name.startswith('_'):
                    discoveries.append({'type': 'project_tool', 'project': project_dir.parent.name + '/' + project_dir.name, 'file': py_file.name})
    return jsonify({"success": True, "discoveries": discoveries, "count": len(discoveries)})


@app.route('/meta/create-tool', methods=['POST'])
def meta_create_tool():
    """Generate code for a new tool based on a description."""
    data = request.get_json() or {}
    name = data.get('name')
    description = data.get('description')
    input_schema = data.get('input_schema', {})
    if not name or not description:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "name and description are required")
    tool_code = f'''@app.route('/{name.replace("_", "-")}', methods=['POST'])
def {name}():
    """{description}"""
    data = request.get_json() or {{}}
'''
    for param in input_schema:
        tool_code += f"    {param} = data.get('{param}')\n"
    tool_code += '''    try:
        result = {}
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
'''
    DISCOVERED_TOOLS[name] = {'name': name, 'description': description, 'code': tool_code, 'created_at': datetime.now().isoformat()}
    return jsonify({"success": True, "tool_name": name, "code": tool_code})


@app.route('/meta/learn-error', methods=['POST'])
def meta_learn_error():
    """Store a solution to an error for future reference."""
    data = request.get_json() or {}
    error_pattern = data.get('error_pattern')
    solution = data.get('solution')
    context = data.get('context', '')
    if not error_pattern or not solution:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "error_pattern and solution are required")
    error_id = f"err_{len(ERROR_SOLUTIONS) + 1}"
    ERROR_SOLUTIONS[error_id] = {'pattern': error_pattern, 'solution': solution, 'context': context, 'learned_at': datetime.now().isoformat(), 'times_applied': 0}
    return jsonify({"success": True, "error_id": error_id})


@app.route('/meta/find-solution', methods=['POST'])
def meta_find_solution():
    """Find a stored solution for an error."""
    data = request.get_json() or {}
    error_message = data.get('error_message', '')
    matches = []
    for error_id, error_data in ERROR_SOLUTIONS.items():
        if error_data['pattern'].lower() in error_message.lower():
            matches.append({'error_id': error_id, **error_data})
    return jsonify({"success": True, "matches": matches, "count": len(matches)})


@app.route('/meta/introspect', methods=['POST'])
def meta_introspect():
    """Analyze agent behavior and performance."""
    introspection = {
        'active_sessions': len(SESSION_CHECKPOINTS),
        'background_tasks': len(BACKGROUND_TASKS),
        'pending_approvals': len(PENDING_APPROVALS),
        'conversation_memories': len(CONVERSATION_MEMORIES),
        'knowledge_bases': len(KNOWLEDGE_BASES),
        'orchestrations': len(ORCHESTRATIONS),
        'learning_entries': len(TASK_OUTCOMES),
        'audit_entries': len(AUDIT_TRAIL),
        'behavior_profiles': len(BEHAVIOR_PROFILES),
        'discovered_tools': len(DISCOVERED_TOOLS),
        'error_solutions': len(ERROR_SOLUTIONS),
        'tool_usage': TOOL_USAGE_STATS
    }
    return jsonify({"success": True, "introspection": introspection})


@app.route('/meta/suggest', methods=['POST'])
def meta_suggest():
    """Get improvement suggestions based on usage patterns."""
    suggestions = []
    if len(KNOWLEDGE_BASES) == 0:
        suggestions.append("Consider using the Knowledge Base (RAG) for semantic search over your codebase")
    if len(ORCHESTRATIONS) == 0:
        suggestions.append("Consider using Multi-Agent Orchestration for complex tasks")
    if len(BEHAVIOR_PROFILES) == 0:
        suggestions.append("Consider using Adaptive Behavior to learn from your patterns")
    if os.getenv('OPENAI_API_KEY') and 'openai' not in str(DISCOVERED_TOOLS):
        suggestions.append("OpenAI API key detected - consider adding OpenAI tools")
    suggestions.append("Run /meta/discover to find new integrations")
    suggestions.append("Use /meta/learn-error to store solutions to recurring errors")
    return jsonify({"success": True, "suggestions": suggestions})


@app.route('/meta/questions', methods=['GET', 'POST'])
def meta_questions():
    """Get or add pending questions for future consideration."""
    if request.method == 'GET':
        return jsonify({"success": True, "questions": META_KNOWLEDGE['pending_questions']})
    data = request.get_json() or {}
    question = data.get('question')
    context = data.get('context', '')
    if question:
        META_KNOWLEDGE['pending_questions'].append({'question': question, 'context': context, 'added_at': datetime.now().isoformat()})
    return jsonify({"success": True, "questions": META_KNOWLEDGE['pending_questions']})


@app.route('/meta/patterns', methods=['GET', 'POST'])
def meta_patterns():
    """Store or retrieve learned patterns."""
    if request.method == 'GET':
        return jsonify({"success": True, "patterns": META_KNOWLEDGE['learned_patterns']})
    data = request.get_json() or {}
    pattern = data.get('pattern')
    description = data.get('description')
    if pattern:
        META_KNOWLEDGE['learned_patterns'].append({'pattern': pattern, 'description': description, 'learned_at': datetime.now().isoformat()})
    return jsonify({"success": True, "patterns": META_KNOWLEDGE['learned_patterns']})


@app.before_request
def track_tool_usage():
    """Track tool usage for self-improvement."""
    endpoint = request.endpoint
    if endpoint and endpoint not in ['health', 'metrics', 'meta_introspect', 'static']:
        if endpoint not in TOOL_USAGE_STATS:
            TOOL_USAGE_STATS[endpoint] = {'count': 0, 'errors': 0, 'last_used': None}
        TOOL_USAGE_STATS[endpoint]['count'] += 1
        TOOL_USAGE_STATS[endpoint]['last_used'] = datetime.now().isoformat()


# [EXTRACTED to ai-systems tower] Lines 8424-8442 (19 lines)


# [EXTRACTED to ai-systems tower] Lines 8444-9000 (557 lines)

# =============================================================================
# MAIN
# =============================================================================


# Sales Pipeline → Extracted to projects/lead-generation/src/ (port 5012)
# Endpoints: /pipeline/stats, /pipeline/deals, /pipeline/deal/*, /pipeline/outreach/*, /pipeline/trial/*, /pipeline/followups




# n8n, Terminal, Git (extended) — Core infrastructure endpoints
# n8n Workflow Management
N8N_BASE_URL = os.getenv('N8N_BASE_URL', 'http://34.193.98.97:5678')

@app.route('/n8n/list-workflows', methods=['POST'])
def n8n_list_workflows():
    """List all workflows from n8n."""
    try:
        import requests
        url = f'{N8N_BASE_URL}/api/v1/workflows'
        response = requests.get(url, timeout=30)
        result = response.json()
        if 'data' in result:
            workflows = [{'id': w['id'], 'name': w['name'], 'active': w.get('active', False)} for w in result['data']]
            return jsonify({"success": True, "workflows": workflows, "count": len(workflows)})
        return jsonify({"success": True, "workflows": result if isinstance(result, list) else []})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/n8n/get-workflow', methods=['POST'])
def n8n_get_workflow():
    """Get a specific workflow from n8n."""
    data = request.get_json() or {}
    workflow_id = data.get('workflow_id')
    if not workflow_id:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "workflow_id is required")
    try:
        import requests
        url = f'{N8N_BASE_URL}/api/v1/workflows/{workflow_id}'
        response = requests.get(url, timeout=30)
        return jsonify({"success": True, "workflow": response.json()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/n8n/create-workflow', methods=['POST'])
def n8n_create_workflow():
    """Create a new workflow in n8n."""
    data = request.get_json() or {}
    name = data.get('name')
    nodes = data.get('nodes', [])
    connections = data.get('connections', {})
    settings = data.get('settings', {})
    if not name:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "name is required")
    try:
        import requests
        headers = {'Content-Type': 'application/json'}
        url = f'{N8N_BASE_URL}/api/v1/workflows'
        payload = {'name': name, 'nodes': nodes, 'connections': connections, 'settings': settings}
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        result = response.json()
        if 'id' in result:
            return jsonify({"success": True, "workflow_id": result['id'], "name": result['name']})
        else:
            return jsonify({"success": False, "error": result.get('message', 'Unknown error')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/n8n/update-workflow', methods=['POST'])
def n8n_update_workflow():
    """Update an existing workflow in n8n."""
    data = request.get_json() or {}
    workflow_id = data.get('workflow_id')
    if not workflow_id:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "workflow_id is required")
    try:
        import requests
        headers = {'Content-Type': 'application/json'}
        url = f'{N8N_BASE_URL}/api/v1/workflows/{workflow_id}'
        get_response = requests.get(url, timeout=30)
        current = get_response.json()
        for key in ['name', 'nodes', 'connections', 'settings']:
            if key in data:
                current[key] = data[key]
        response = requests.put(url, headers=headers, json=current, timeout=30)
        return jsonify({"success": True, "workflow_id": workflow_id, "updated": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/n8n/activate-workflow', methods=['POST'])
def n8n_activate_workflow():
    """Activate or deactivate a workflow."""
    data = request.get_json() or {}
    workflow_id = data.get('workflow_id')
    active = data.get('active', True)
    if not workflow_id:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "workflow_id is required")
    try:
        import requests
        action = 'activate' if active else 'deactivate'
        url = f'{N8N_BASE_URL}/api/v1/workflows/{workflow_id}/{action}'
        response = requests.post(url, timeout=30)
        return jsonify({"success": True, "workflow_id": workflow_id, "active": active})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/n8n/execute-workflow', methods=['POST'])
def n8n_execute_workflow():
    """Execute a workflow in n8n."""
    data = request.get_json() or {}
    workflow_id = data.get('workflow_id')
    input_data = data.get('data', {})
    if not workflow_id:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "workflow_id is required")
    try:
        import requests
        headers = {'Content-Type': 'application/json'}
        url = f'{N8N_BASE_URL}/api/v1/workflows/{workflow_id}/run'
        response = requests.post(url, headers=headers, json=input_data, timeout=60)
        return jsonify({"success": True, "execution": response.json()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# Enhanced Terminal Operations
@app.route('/terminal/multi-command', methods=['POST'])
def terminal_multi_command():
    """Execute multiple commands."""
    data = request.get_json() or {}
    commands = data.get('commands', [])
    mode = data.get('mode', 'sequential')
    stop_on_error = data.get('stop_on_error', True)
    timeout = data.get('timeout', 60)
    if not commands:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "commands is required")
    results = []
    for cmd in commands:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd='/Users/williammarceaujr./dev-sandbox')
            results.append({'command': cmd, 'success': result.returncode == 0, 'stdout': result.stdout[:5000], 'stderr': result.stderr[:2000]})
            if result.returncode != 0 and stop_on_error:
                break
        except Exception as e:
            results.append({'command': cmd, 'success': False, 'error': str(e)})
            if stop_on_error:
                break
    return jsonify({"success": all(r.get('success') for r in results), "results": results})


@app.route('/terminal/script', methods=['POST'])
def terminal_script():
    """Execute a multi-line script."""
    data = request.get_json() or {}
    script = data.get('script', '')
    interpreter = data.get('interpreter', '/bin/bash')
    timeout = data.get('timeout', 120)
    if not script:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "script is required")
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script)
            script_path = f.name
        os.chmod(script_path, 0o755)
        result = subprocess.run([interpreter, script_path], capture_output=True, text=True, timeout=timeout, cwd='/Users/williammarceaujr./dev-sandbox')
        os.unlink(script_path)
        return jsonify({'success': result.returncode == 0, 'stdout': result.stdout[:20000], 'stderr': result.stderr[:5000], 'return_code': result.returncode})
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Script timed out'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/git/clone', methods=['POST'])
def git_clone():
    """Clone a git repository."""
    data = request.get_json() or {}
    url = data.get('url')
    path = data.get('path')
    branch = data.get('branch')
    if not url or not path:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "url and path are required")
    if not validate_path(path):
        return make_error_response(ErrorCode.PATH_NOT_ALLOWED, f"Path not allowed: {path}")
    cmd = ['git', 'clone']
    if branch:
        cmd.extend(['-b', branch])
    cmd.extend([url, path])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return jsonify({'success': result.returncode == 0, 'path': path, 'stderr': result.stderr})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/git/pull', methods=['POST'])
def git_pull():
    """Pull from remote."""
    data = request.get_json() or {}
    repo_path = data.get('repo_path', '/Users/williammarceaujr./dev-sandbox')
    if not validate_path(repo_path):
        return make_error_response(ErrorCode.PATH_NOT_ALLOWED, f"Path not allowed: {repo_path}")
    try:
        result = subprocess.run(['git', 'pull'], cwd=repo_path, capture_output=True, text=True, timeout=60)
        return jsonify({'success': result.returncode == 0, 'stdout': result.stdout, 'stderr': result.stderr})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/git/branch', methods=['POST'])
def git_branch():
    """Manage git branches."""
    data = request.get_json() or {}
    repo_path = data.get('repo_path', '/Users/williammarceaujr./dev-sandbox')
    action = data.get('action', 'list')
    branch_name = data.get('branch')
    if not validate_path(repo_path):
        return make_error_response(ErrorCode.PATH_NOT_ALLOWED, f"Path not allowed: {repo_path}")
    try:
        if action == 'list':
            result = subprocess.run(['git', 'branch', '-a'], cwd=repo_path, capture_output=True, text=True)
            branches = [b.strip().lstrip('* ') for b in result.stdout.strip().split('\n') if b.strip()]
            current = next((b.lstrip('* ') for b in result.stdout.split('\n') if b.startswith('*')), None)
            return jsonify({'success': True, 'branches': branches, 'current': current})
        elif action == 'create' and branch_name:
            result = subprocess.run(['git', 'checkout', '-b', branch_name], cwd=repo_path, capture_output=True, text=True)
            return jsonify({'success': result.returncode == 0, 'branch': branch_name})
        elif action == 'switch' and branch_name:
            result = subprocess.run(['git', 'checkout', branch_name], cwd=repo_path, capture_output=True, text=True)
            return jsonify({'success': result.returncode == 0, 'branch': branch_name})
        elif action == 'delete' and branch_name:
            result = subprocess.run(['git', 'branch', '-d', branch_name], cwd=repo_path, capture_output=True, text=True)
            return jsonify({'success': result.returncode == 0, 'deleted': branch_name})
        else:
            return make_error_response(ErrorCode.INVALID_PARAMETER, f"Invalid action: {action}")
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/git/log', methods=['POST'])
def git_log():
    """Get git commit log."""
    data = request.get_json() or {}
    repo_path = data.get('repo_path', '/Users/williammarceaujr./dev-sandbox')
    limit = data.get('limit', 10)
    if not validate_path(repo_path):
        return make_error_response(ErrorCode.PATH_NOT_ALLOWED, f"Path not allowed: {repo_path}")
    try:
        result = subprocess.run(['git', 'log', f'-{limit}', '--pretty=format:%H|%an|%ad|%s', '--date=iso'], cwd=repo_path, capture_output=True, text=True)
        commits = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|', 3)
                commits.append({'hash': parts[0], 'author': parts[1], 'date': parts[2], 'message': parts[3] if len(parts) > 3 else ''})
        return jsonify({'success': True, 'commits': commits})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



def main():
    """Run the Flask server."""
    parser = argparse.ArgumentParser(description="Agent Bridge API Server")
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})")
    parser.add_argument('--host', type=str, default='127.0.0.1', help="Host (default: 127.0.0.1)")
    parser.add_argument('--debug', action='store_true', help="Debug mode")
    parser.add_argument('--no-persist', action='store_true', help="Disable persistence")

    args = parser.parse_args()

    # Handle persistence
    global PERSISTENCE_ENABLED
    if args.no_persist:
        PERSISTENCE_ENABLED = False
        print("[Persistence] Disabled via --no-persist flag")
    else:
        # Start auto-save
        persistence_manager.start_auto_save(get_current_state)
        # Register shutdown handler
        atexit.register(lambda: persistence_manager.stop_auto_save(get_current_state))

    print(f"\n{'='*60}")
    print(f"Agent Bridge API v5.1-Ultra - Maximum Capability & Efficiency")
    print(f"{'='*60}")
    print(f"Server: http://{args.host}:{args.port}")
    print(f"Health: http://{args.host}:{args.port}/health")
    print(f"Metrics: http://{args.host}:{args.port}/metrics")
    print(f"{'='*60}")
    print(f"v3.5-3.6 Features:")
    print(f"  ✓ Task Persistence | Retry Logic | Context Management")
    print(f"  ✓ Parallel Tools | Caching | Rate Limiting | Cost Tracking")
    print(f"{'='*60}")
    print(f"v3.7 Features:")
    print(f"  ✓ Conversation Memory ({len(CONVERSATION_MEMORIES)} sessions)")
    print(f"  ✓ Tool Pipelines ({len(BUILTIN_PIPELINES)} built-in)")
    print(f"  ✓ Webhook Notifications ({len(WEBHOOKS)} registered)")
    print(f"  ✓ Agent Templates ({len(AGENT_TEMPLATES)} available)")
    print(f"{'='*60}")
    print(f"v3.8 Features:")
    print(f"  ✓ Multi-Agent Orchestration (spawn sub-agents)")
    print(f"  ✓ Knowledge Base / RAG ({len(KNOWLEDGE_BASES)} KBs)")
    print(f"  ✓ Scheduled Tasks ({len(SCHEDULED_TASKS)} scheduled)")
    print(f"  ✓ Tool Plugins ({len(TOOL_PLUGINS)} registered)")
    print(f"{'='*60}")
    print(f"v3.9 Features:")
    print(f"  ✓ Agent Learning & Feedback ({len(TASK_OUTCOMES)} outcomes)")
    print(f"  ✓ Workflow Recording & Playback ({len(RECORDED_WORKFLOWS)} workflows)")
    print(f"  ✓ Smart Context Injection ({len(CONTEXT_INJECTION_RULES)} rules)")
    print(f"  ✓ Inter-Agent Communication ({len(SHARED_STATES)} shared states)")
    print(f"{'='*60}")
    print(f"v4.0 Features:")
    print(f"  ✓ Agent Personas ({len(AGENT_PERSONAS)} personas)")
    print(f"  ✓ Goal Decomposition ({len(GOALS)} goals)")
    print(f"  ✓ Tool Macros ({len(TOOL_MACROS)} macros, {len(BUILTIN_MACROS)} built-in)")
    print(f"  ✓ Audit Trail ({len(AUDIT_TRAIL)} entries)")
    print(f"  ✓ Adaptive Behavior ({len(BEHAVIOR_PROFILES)} profiles)")
    print(f"{'='*60}")
    print(f"v4.1 Features (META-AGENT):")
    print(f"  ✓ Gmail Integration (list/read/send/search)")
    print(f"  ✓ Google Sheets (read/write/append)")
    print(f"  ✓ Twilio SMS (send/list)")
    print(f"  ✓ ClickUp CRM (tasks/create/update)")
    print(f"  ✓ n8n Workflow Mgmt (list/create/update/execute)")
    print(f"  ✓ Enhanced Terminal (multi-command/script)")
    print(f"  ✓ Enhanced Git (clone/pull/branch/log)")
    print(f"  ✓ Self-Discovery ({len(DISCOVERED_TOOLS)} discovered tools)")
    print(f"  ✓ Error Learning ({len(ERROR_SOLUTIONS)} solutions)")
    print(f"  ✓ Meta-Introspection & Suggestions")
    print(f"{'='*60}")
    print(f"v4.16 Features (ENTERPRISE PLATFORM):")
    print(f"  ✓ Request Prioritization Engine")
    print(f"  ✓ Auto-Scaling Controller")
    print(f"  ✓ API Gateway Pro")
    print(f"  ✓ Service Mesh Integration")
    print(f"  ✓ Event Bus (Pub/Sub)")
    print(f"  ✓ Data Pipeline Manager")
    print(f"  ✓ ML Model Registry")
    print(f"  ✓ Feature Store")
    print(f"  ✓ Chaos Engineering Pro")
    print(f"{'='*60}")
    print(f"v5.1-Ultra Features (MAXIMUM CAPABILITY):")
    print(f"  ✓ Multi-Level Cache (L1/L2/L3)")
    print(f"  ✓ Predictive Preloading Engine")
    print(f"  ✓ Load Shedding & Backpressure")
    print(f"  ✓ Deadline Propagation")
    print(f"  ✓ Resource Quotas & Cost Attribution")
    print(f"  ✓ Smart GC Scheduler")
    print(f"  + All previous features retained")
    print(f"{'='*60}")
    print(f"Allowed paths: {ALLOWED_BASE_PATHS}")
    print(f"Persistence: {'ENABLED' if PERSISTENCE_ENABLED else 'DISABLED'}")
    print(f"Cache: {TOOL_CACHE.max_size} items, {TOOL_CACHE.default_ttl}s TTL")
    print(f"Rate Limit: {RATE_LIMITERS['default'].rate}/s, burst {RATE_LIMITERS['default'].burst}")
    print(f"{'='*60}\n")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
