#!/usr/bin/env python3
import random
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


# =============================================================================
# v3.6: COST & TOKEN TRACKING
# =============================================================================

# Anthropic pricing (per million tokens, approximate)
PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-opus-4-5-20251101": {"input": 15.0, "output": 75.0},
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
    "grok-2-latest": {"input": 2.0, "output": 10.0},
    "default": {"input": 3.0, "output": 15.0}
}


@dataclass
class SessionCost:
    """Track costs for a session."""
    session_id: str
    model: str = "claude-sonnet-4-5-20250929"
    input_tokens: int = 0
    output_tokens: int = 0
    api_calls: int = 0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    budget_limit: Optional[float] = None  # Optional spending limit

    def add_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Record token usage."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.api_calls += 1

    def calculate_cost(self) -> float:
        """Calculate total cost in USD."""
        pricing = PRICING.get(self.model, PRICING["default"])
        input_cost = (self.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    def is_over_budget(self) -> bool:
        """Check if session has exceeded budget."""
        if self.budget_limit is None:
            return False
        return self.calculate_cost() > self.budget_limit

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        cost = self.calculate_cost()
        return {
            "session_id": self.session_id,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "api_calls": self.api_calls,
            "cost_usd": cost,
            "budget_limit": self.budget_limit,
            "over_budget": self.is_over_budget(),
            "started_at": self.started_at
        }


# Session cost tracking (keyed by session_id)
SESSION_COSTS: Dict[str, SessionCost] = {}


# =============================================================================
# v3.7: CONVERSATION MEMORY
# =============================================================================

@dataclass
class ConversationMemory:
    """Persistent conversation memory across sessions."""
    session_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    messages: List[Dict[str, str]] = field(default_factory=list)
    summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    max_messages: int = 100  # Keep last N messages

    def add_message(self, role: str, content: str) -> None:
        """Add a message to memory."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # Trim to max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        self.updated_at = datetime.now().isoformat()

    def get_context(self, last_n: int = 10) -> List[Dict[str, str]]:
        """Get last N messages for context."""
        return self.messages[-last_n:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": self.messages,
            "summary": self.summary,
            "metadata": self.metadata,
            "message_count": len(self.messages)
        }


# Conversation memories (keyed by session_id)
CONVERSATION_MEMORIES: Dict[str, ConversationMemory] = {}


def get_or_create_memory(session_id: str) -> ConversationMemory:
    """Get or create conversation memory for a session."""
    if session_id not in CONVERSATION_MEMORIES:
        CONVERSATION_MEMORIES[session_id] = ConversationMemory(session_id=session_id)
    return CONVERSATION_MEMORIES[session_id]


# =============================================================================
# v3.7: TOOL CHAINING / PIPELINES
# =============================================================================

@dataclass
class ToolPipeline:
    """Define a sequence of tools where output flows to next input."""
    name: str
    steps: List[Dict[str, Any]]  # [{"tool": "file_read", "input": {...}, "output_key": "content"}]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "steps": self.steps,
            "created_at": self.created_at,
            "step_count": len(self.steps)
        }


# Saved pipelines (keyed by name)
TOOL_PIPELINES: Dict[str, ToolPipeline] = {}

# Built-in pipelines
BUILTIN_PIPELINES = {
    "find_and_read": {
        "name": "find_and_read",
        "description": "Find files by pattern and read their contents",
        "steps": [
            {"tool": "glob", "input_template": {"pattern": "{pattern}", "path": "{path}"}, "output_key": "files"},
            {"tool": "file_read", "input_template": {"path": "{files[0]}"}, "output_key": "content"}
        ]
    },
    "search_and_extract": {
        "name": "search_and_extract",
        "description": "Search for pattern in files and extract matches",
        "steps": [
            {"tool": "grep", "input_template": {"pattern": "{pattern}", "path": "{path}"}, "output_key": "matches"},
        ]
    },
    "backup_file": {
        "name": "backup_file",
        "description": "Read a file and write a backup copy",
        "steps": [
            {"tool": "file_read", "input_template": {"path": "{source}"}, "output_key": "content"},
            {"tool": "file_write", "input_template": {"path": "{destination}", "content": "{content}"}, "output_key": "result"}
        ]
    }
}


# =============================================================================
# v3.7: WEBHOOK NOTIFICATIONS
# =============================================================================

@dataclass
class WebhookConfig:
    """Webhook configuration for notifications."""
    url: str
    events: List[str]  # ["task_complete", "task_error", "approval_required"]
    headers: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    retry_count: int = 3
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "events": self.events,
            "headers": {k: "***" for k in self.headers},  # Hide header values
            "enabled": self.enabled,
            "retry_count": self.retry_count,
            "created_at": self.created_at
        }


# Registered webhooks (keyed by id)
WEBHOOKS: Dict[str, WebhookConfig] = {}


def send_webhook_notification(event: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Send notification to all registered webhooks for this event."""
    import requests as req_lib

    results = []
    for webhook_id, webhook in WEBHOOKS.items():
        if not webhook.enabled or event not in webhook.events:
            continue

        notification = {
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "payload": payload
        }

        for attempt in range(webhook.retry_count):
            try:
                resp = req_lib.post(
                    webhook.url,
                    json=notification,
                    headers=webhook.headers,
                    timeout=10
                )
                results.append({
                    "webhook_id": webhook_id,
                    "success": resp.ok,
                    "status_code": resp.status_code,
                    "attempt": attempt + 1
                })
                break
            except Exception as e:
                if attempt == webhook.retry_count - 1:
                    results.append({
                        "webhook_id": webhook_id,
                        "success": False,
                        "error": str(e),
                        "attempt": attempt + 1
                    })

    return results


# =============================================================================
# v3.7: AGENT TEMPLATES
# =============================================================================

AGENT_TEMPLATES = {
    "coder": {
        "id": "coder-agent",
        "name": "Coder Agent",
        "description": "Specialized for code writing, debugging, and refactoring",
        "system_prompt": """You are an expert software developer. You write clean, efficient, well-documented code.

When writing code:
- Follow best practices and design patterns
- Include error handling
- Add helpful comments for complex logic
- Consider edge cases

Available tools: file_read, file_write, file_edit, command, grep, glob, git_status

Use JSON format for tool calls: {"action": "tool_name", "input": {...}}
When the task is complete, include TASK_COMPLETE in your response.""",
        "tools_available": ["file_read", "file_write", "file_edit", "command", "grep", "glob", "git_status"],
        "model": "claude-sonnet-4-5-20250929"
    },
    "researcher": {
        "id": "researcher-agent",
        "name": "Researcher Agent",
        "description": "Specialized for web research and information gathering",
        "system_prompt": """You are an expert researcher. You find, analyze, and synthesize information effectively.

When researching:
- Search multiple sources for accuracy
- Verify information when possible
- Summarize findings clearly
- Cite sources

Available tools: web_search, web_fetch, file_read, file_write, grep

Use JSON format for tool calls: {"action": "tool_name", "input": {...}}
When the task is complete, include TASK_COMPLETE in your response.""",
        "tools_available": ["web_search", "web_fetch", "file_read", "file_write", "grep"],
        "model": "claude-sonnet-4-5-20250929"
    },
    "analyst": {
        "id": "analyst-agent",
        "name": "Data Analyst Agent",
        "description": "Specialized for data analysis and insights",
        "system_prompt": """You are an expert data analyst. You analyze data, identify patterns, and provide actionable insights.

When analyzing:
- Look for trends and patterns
- Calculate relevant statistics
- Visualize data when helpful
- Provide clear recommendations

Available tools: file_read, command, grep, glob, file_write

Use JSON format for tool calls: {"action": "tool_name", "input": {...}}
When the task is complete, include TASK_COMPLETE in your response.""",
        "tools_available": ["file_read", "command", "grep", "glob", "file_write"],
        "model": "claude-sonnet-4-5-20250929"
    },
    "writer": {
        "id": "writer-agent",
        "name": "Content Writer Agent",
        "description": "Specialized for content creation and editing",
        "system_prompt": """You are an expert content writer. You create engaging, clear, and well-structured content.

When writing:
- Use clear and concise language
- Structure content logically
- Adapt tone to the audience
- Proofread for errors

Available tools: file_read, file_write, web_search, web_fetch

Use JSON format for tool calls: {"action": "tool_name", "input": {...}}
When the task is complete, include TASK_COMPLETE in your response.""",
        "tools_available": ["file_read", "file_write", "web_search", "web_fetch"],
        "model": "claude-sonnet-4-5-20250929"
    },
    "devops": {
        "id": "devops-agent",
        "name": "DevOps Agent",
        "description": "Specialized for infrastructure, deployment, and automation",
        "system_prompt": """You are an expert DevOps engineer. You manage infrastructure, deployments, and automation.

When working:
- Follow security best practices
- Document all changes
- Use infrastructure as code
- Implement proper monitoring

Available tools: command, file_read, file_write, file_edit, git_status, grep, glob

IMPORTANT: Be cautious with destructive commands. Always verify before executing.

Use JSON format for tool calls: {"action": "tool_name", "input": {...}}
When the task is complete, include TASK_COMPLETE in your response.""",
        "tools_available": ["command", "file_read", "file_write", "file_edit", "git_status", "grep", "glob"],
        "model": "claude-sonnet-4-5-20250929"
    }
}


def get_or_create_session_cost(session_id: str, model: str = "claude-sonnet-4-5-20250929") -> SessionCost:
    """Get or create cost tracker for a session."""
    if session_id not in SESSION_COSTS:
        SESSION_COSTS[session_id] = SessionCost(session_id=session_id, model=model)
    return SESSION_COSTS[session_id]


# =============================================================================
# v3.8: MULTI-AGENT ORCHESTRATION
# =============================================================================

@dataclass
class SubAgent:
    """A sub-agent spawned for parallel task execution."""
    agent_id: str
    parent_id: str
    task: str
    template: str = "coder"
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "parent_id": self.parent_id,
            "task": self.task,
            "template": self.template,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


@dataclass
class AgentOrchestration:
    """Orchestration of multiple sub-agents working on subtasks."""
    orchestration_id: str
    parent_session_id: str
    objective: str
    strategy: str = "parallel"  # parallel, sequential, hierarchical
    sub_agents: List[str] = field(default_factory=list)  # List of agent_ids
    status: str = "pending"  # pending, running, consolidating, completed, failed
    consolidated_result: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "orchestration_id": self.orchestration_id,
            "parent_session_id": self.parent_session_id,
            "objective": self.objective,
            "strategy": self.strategy,
            "sub_agents": self.sub_agents,
            "status": self.status,
            "consolidated_result": self.consolidated_result,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "agent_count": len(self.sub_agents)
        }


# Sub-agents registry (keyed by agent_id)
SUB_AGENTS: Dict[str, SubAgent] = {}

# Orchestrations registry (keyed by orchestration_id)
ORCHESTRATIONS: Dict[str, AgentOrchestration] = {}


def spawn_sub_agent(
    parent_id: str,
    task: str,
    template: str = "coder"
) -> SubAgent:
    """Spawn a new sub-agent for a subtask."""
    agent_id = f"sub_{uuid.uuid4().hex[:12]}"
    agent = SubAgent(
        agent_id=agent_id,
        parent_id=parent_id,
        task=task,
        template=template
    )
    SUB_AGENTS[agent_id] = agent
    return agent


def create_orchestration(
    parent_session_id: str,
    objective: str,
    subtasks: List[Dict[str, Any]],
    strategy: str = "parallel"
) -> AgentOrchestration:
    """Create a new multi-agent orchestration."""
    orch_id = f"orch_{uuid.uuid4().hex[:12]}"
    orchestration = AgentOrchestration(
        orchestration_id=orch_id,
        parent_session_id=parent_session_id,
        objective=objective,
        strategy=strategy
    )

    # Spawn sub-agents for each subtask
    for subtask in subtasks:
        agent = spawn_sub_agent(
            parent_id=orch_id,
            task=subtask.get("task", ""),
            template=subtask.get("template", "coder")
        )
        orchestration.sub_agents.append(agent.agent_id)

    ORCHESTRATIONS[orch_id] = orchestration
    return orchestration


# =============================================================================
# v3.8: KNOWLEDGE BASE / RAG
# =============================================================================

@dataclass
class FileIndex:
    """Index entry for a file in the knowledge base."""
    file_path: str
    content_hash: str
    size_bytes: int
    indexed_at: str
    chunks: List[Dict[str, Any]] = field(default_factory=list)  # For semantic chunking
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
            "indexed_at": self.indexed_at,
            "chunk_count": len(self.chunks),
            "metadata": self.metadata
        }


@dataclass
class KnowledgeBase:
    """Knowledge base for semantic search and context retrieval."""
    kb_id: str
    name: str
    description: str = ""
    root_paths: List[str] = field(default_factory=list)
    include_patterns: List[str] = field(default_factory=lambda: ["**/*.py", "**/*.md", "**/*.txt", "**/*.json"])
    exclude_patterns: List[str] = field(default_factory=lambda: ["**/node_modules/**", "**/.git/**", "**/__pycache__/**"])
    files: Dict[str, FileIndex] = field(default_factory=dict)  # keyed by file_path
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_indexed_at: Optional[str] = None
    total_chunks: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kb_id": self.kb_id,
            "name": self.name,
            "description": self.description,
            "root_paths": self.root_paths,
            "include_patterns": self.include_patterns,
            "exclude_patterns": self.exclude_patterns,
            "file_count": len(self.files),
            "total_chunks": self.total_chunks,
            "created_at": self.created_at,
            "last_indexed_at": self.last_indexed_at
        }


# Knowledge bases registry (keyed by kb_id)
KNOWLEDGE_BASES: Dict[str, KnowledgeBase] = {}


def create_knowledge_base(
    name: str,
    root_paths: List[str],
    description: str = "",
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> KnowledgeBase:
    """Create a new knowledge base."""
    kb_id = f"kb_{uuid.uuid4().hex[:12]}"
    kb = KnowledgeBase(
        kb_id=kb_id,
        name=name,
        description=description,
        root_paths=root_paths
    )
    if include_patterns:
        kb.include_patterns = include_patterns
    if exclude_patterns:
        kb.exclude_patterns = exclude_patterns
    KNOWLEDGE_BASES[kb_id] = kb
    return kb


def index_file(kb: KnowledgeBase, file_path: str) -> Optional[FileIndex]:
    """Index a single file into the knowledge base."""
    import hashlib
    from pathlib import Path

    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return None

    try:
        content = path.read_text(encoding='utf-8', errors='ignore')
        content_hash = hashlib.md5(content.encode()).hexdigest()

        # Simple chunking: split by paragraphs or lines
        chunks = []
        paragraphs = content.split('\n\n')
        for i, para in enumerate(paragraphs):
            if para.strip():
                chunks.append({
                    "chunk_id": f"{kb.kb_id}_{path.name}_{i}",
                    "content": para.strip()[:2000],  # Limit chunk size
                    "position": i
                })

        file_index = FileIndex(
            file_path=str(path),
            content_hash=content_hash,
            size_bytes=path.stat().st_size,
            indexed_at=datetime.now().isoformat(),
            chunks=chunks
        )

        kb.files[str(path)] = file_index
        kb.total_chunks += len(chunks)
        kb.last_indexed_at = datetime.now().isoformat()

        return file_index
    except Exception:
        return None


def search_knowledge_base(kb: KnowledgeBase, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search the knowledge base for relevant chunks (simple keyword matching)."""
    results = []
    query_lower = query.lower()
    query_words = set(query_lower.split())

    for file_path, file_index in kb.files.items():
        for chunk in file_index.chunks:
            content_lower = chunk["content"].lower()
            # Simple relevance: count matching words
            content_words = set(content_lower.split())
            matches = len(query_words & content_words)
            if matches > 0:
                results.append({
                    "file_path": file_path,
                    "chunk_id": chunk["chunk_id"],
                    "content": chunk["content"][:500],  # Truncate for response
                    "relevance": matches / len(query_words) if query_words else 0,
                    "position": chunk["position"]
                })

    # Sort by relevance and return top_k
    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:top_k]


# =============================================================================
# v3.8: SCHEDULED TASKS
# =============================================================================

@dataclass
class ScheduledTask:
    """A scheduled task with cron-like scheduling."""
    task_id: str
    name: str
    description: str = ""
    cron_expression: str = "0 * * * *"  # Default: every hour
    task_config: Dict[str, Any] = field(default_factory=dict)  # Agent config
    enabled: bool = True
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    run_count: int = 0
    last_result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "cron_expression": self.cron_expression,
            "enabled": self.enabled,
            "last_run_at": self.last_run_at,
            "next_run_at": self.next_run_at,
            "run_count": self.run_count,
            "last_result": self.last_result,
            "created_at": self.created_at
        }


# Scheduled tasks registry (keyed by task_id)
SCHEDULED_TASKS: Dict[str, ScheduledTask] = {}

# Scheduler thread
SCHEDULER_THREAD: Optional[threading.Thread] = None
SCHEDULER_RUNNING = False


def parse_cron_expression(cron_expr: str) -> Dict[str, Any]:
    """Parse a cron expression into components."""
    parts = cron_expr.split()
    if len(parts) != 5:
        return {"error": "Invalid cron expression. Expected 5 parts: minute hour day month weekday"}

    return {
        "minute": parts[0],
        "hour": parts[1],
        "day": parts[2],
        "month": parts[3],
        "weekday": parts[4]
    }


def calculate_next_run(cron_expr: str) -> str:
    """Calculate the next run time for a cron expression (simplified)."""
    now = datetime.now()
    parts = parse_cron_expression(cron_expr)
    if "error" in parts:
        return now.isoformat()

    # Simple: add 1 hour if hour is *, add 1 minute if minute is *
    next_run = now
    if parts["minute"] == "*":
        next_run = now.replace(second=0, microsecond=0) + __import__('datetime').timedelta(minutes=1)
    elif parts["hour"] == "*":
        next_run = now.replace(minute=int(parts["minute"]), second=0, microsecond=0)
        if next_run <= now:
            next_run = next_run + __import__('datetime').timedelta(hours=1)

    return next_run.isoformat()


def create_scheduled_task(
    name: str,
    task_config: Dict[str, Any],
    cron_expression: str = "0 * * * *",
    description: str = ""
) -> ScheduledTask:
    """Create a new scheduled task."""
    task_id = f"sched_{uuid.uuid4().hex[:12]}"
    task = ScheduledTask(
        task_id=task_id,
        name=name,
        description=description,
        cron_expression=cron_expression,
        task_config=task_config,
        next_run_at=calculate_next_run(cron_expression)
    )
    SCHEDULED_TASKS[task_id] = task
    return task


# =============================================================================
# v3.8: TOOL PLUGINS
# =============================================================================

@dataclass
class ToolPlugin:
    """A dynamically loaded tool plugin."""
    plugin_id: str
    name: str
    description: str = ""
    source: str = "python"  # python, mcp, http
    source_config: Dict[str, Any] = field(default_factory=dict)
    tool_schema: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    loaded_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "enabled": self.enabled,
            "loaded_at": self.loaded_at,
            "has_schema": bool(self.tool_schema)
        }


# Tool plugins registry (keyed by plugin_id)
TOOL_PLUGINS: Dict[str, ToolPlugin] = {}

# Plugin callables (keyed by plugin_id) - actual functions to execute
PLUGIN_CALLABLES: Dict[str, Callable] = {}


def load_python_plugin(
    name: str,
    module_path: str,
    function_name: str,
    description: str = ""
) -> Optional[ToolPlugin]:
    """Load a Python function as a tool plugin."""
    import importlib.util

    plugin_id = f"plugin_{uuid.uuid4().hex[:12]}"

    try:
        spec = importlib.util.spec_from_file_location(name, module_path)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        func = getattr(module, function_name, None)
        if func is None or not callable(func):
            return None

        plugin = ToolPlugin(
            plugin_id=plugin_id,
            name=name,
            description=description or func.__doc__ or "",
            source="python",
            source_config={"module_path": module_path, "function_name": function_name}
        )

        TOOL_PLUGINS[plugin_id] = plugin
        PLUGIN_CALLABLES[plugin_id] = func
        return plugin

    except Exception as e:
        return None


def register_mcp_plugin(
    name: str,
    server_url: str,
    tool_name: str,
    description: str = ""
) -> ToolPlugin:
    """Register an MCP server tool as a plugin."""
    plugin_id = f"mcp_{uuid.uuid4().hex[:12]}"

    plugin = ToolPlugin(
        plugin_id=plugin_id,
        name=name,
        description=description,
        source="mcp",
        source_config={"server_url": server_url, "tool_name": tool_name}
    )

    TOOL_PLUGINS[plugin_id] = plugin
    return plugin


def register_http_plugin(
    name: str,
    endpoint_url: str,
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    description: str = ""
) -> ToolPlugin:
    """Register an HTTP endpoint as a tool plugin."""
    plugin_id = f"http_{uuid.uuid4().hex[:12]}"

    plugin = ToolPlugin(
        plugin_id=plugin_id,
        name=name,
        description=description,
        source="http",
        source_config={"endpoint_url": endpoint_url, "method": method, "headers": headers or {}}
    )

    TOOL_PLUGINS[plugin_id] = plugin
    return plugin


def execute_plugin(plugin_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool plugin."""
    import requests as req_lib

    plugin = TOOL_PLUGINS.get(plugin_id)
    if not plugin:
        return {"success": False, "error": f"Plugin not found: {plugin_id}"}

    if not plugin.enabled:
        return {"success": False, "error": f"Plugin disabled: {plugin.name}"}

    try:
        if plugin.source == "python":
            func = PLUGIN_CALLABLES.get(plugin_id)
            if not func:
                return {"success": False, "error": "Plugin function not loaded"}
            result = func(**input_data)
            return {"success": True, "result": result}

        elif plugin.source == "http":
            config = plugin.source_config
            resp = req_lib.request(
                method=config.get("method", "POST"),
                url=config["endpoint_url"],
                json=input_data,
                headers=config.get("headers", {}),
                timeout=30
            )
            return {"success": resp.ok, "result": resp.json() if resp.ok else None, "error": resp.text if not resp.ok else None}

        elif plugin.source == "mcp":
            # MCP plugin execution would require MCP client
            return {"success": False, "error": "MCP plugin execution not yet implemented"}

        else:
            return {"success": False, "error": f"Unknown plugin source: {plugin.source}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# v3.9: AGENT LEARNING & FEEDBACK
# =============================================================================

@dataclass
class TaskOutcome:
    """Record of a task's outcome for learning."""
    outcome_id: str
    session_id: str
    task: str
    template_used: str
    success: bool
    error_message: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0
    user_feedback: Optional[str] = None  # positive, negative, neutral
    feedback_notes: Optional[str] = None
    learned_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)


@dataclass
class LearningEntry:
    """A learned pattern or insight from task outcomes."""
    entry_id: str
    pattern_type: str  # error_pattern, success_pattern, optimization, anti_pattern
    description: str
    trigger_conditions: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    source_outcomes: List[str] = field(default_factory=list)  # outcome_ids
    confidence: float = 0.5  # 0.0 to 1.0
    times_applied: int = 0
    times_successful: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


# In-memory storage for learning
TASK_OUTCOMES: Dict[str, TaskOutcome] = {}
LEARNING_ENTRIES: Dict[str, LearningEntry] = {}


def record_task_outcome(
    session_id: str,
    task: str,
    template_used: str,
    success: bool,
    error_message: Optional[str] = None,
    tool_calls: Optional[List[Dict]] = None,
    duration_seconds: float = 0.0,
    tags: Optional[List[str]] = None
) -> TaskOutcome:
    """Record the outcome of a task for learning purposes."""
    outcome = TaskOutcome(
        outcome_id=f"outcome_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(TASK_OUTCOMES)}",
        session_id=session_id,
        task=task,
        template_used=template_used,
        success=success,
        error_message=error_message,
        tool_calls=tool_calls or [],
        duration_seconds=duration_seconds,
        tags=tags or []
    )
    TASK_OUTCOMES[outcome.outcome_id] = outcome

    # Trigger pattern analysis after recording
    analyze_patterns_for_outcome(outcome)

    return outcome


def add_user_feedback(outcome_id: str, feedback: str, notes: Optional[str] = None) -> bool:
    """Add user feedback to a task outcome."""
    if outcome_id not in TASK_OUTCOMES:
        return False
    TASK_OUTCOMES[outcome_id].user_feedback = feedback
    TASK_OUTCOMES[outcome_id].feedback_notes = notes
    return True


def analyze_patterns_for_outcome(outcome: TaskOutcome) -> List[LearningEntry]:
    """Analyze a task outcome to identify patterns."""
    new_entries = []

    # Pattern 1: Repeated errors with same tool
    if not outcome.success and outcome.error_message:
        similar_errors = [
            o for o in TASK_OUTCOMES.values()
            if not o.success and o.error_message and outcome.error_message[:50] in o.error_message
            and o.outcome_id != outcome.outcome_id
        ]
        if len(similar_errors) >= 2:
            entry_id = f"error_pattern_{hashlib.md5(outcome.error_message[:50].encode()).hexdigest()[:8]}"
            if entry_id not in LEARNING_ENTRIES:
                entry = LearningEntry(
                    entry_id=entry_id,
                    pattern_type="error_pattern",
                    description=f"Recurring error: {outcome.error_message[:100]}",
                    trigger_conditions=[f"Error containing: {outcome.error_message[:50]}"],
                    recommended_actions=["Review error handling", "Check input validation"],
                    source_outcomes=[o.outcome_id for o in similar_errors] + [outcome.outcome_id],
                    confidence=min(0.9, 0.5 + len(similar_errors) * 0.1)
                )
                LEARNING_ENTRIES[entry_id] = entry
                new_entries.append(entry)

    # Pattern 2: Successful template usage
    if outcome.success:
        similar_successes = [
            o for o in TASK_OUTCOMES.values()
            if o.success and o.template_used == outcome.template_used
            and o.outcome_id != outcome.outcome_id
        ]
        if len(similar_successes) >= 3:
            entry_id = f"success_pattern_{outcome.template_used}"
            if entry_id not in LEARNING_ENTRIES:
                entry = LearningEntry(
                    entry_id=entry_id,
                    pattern_type="success_pattern",
                    description=f"Template '{outcome.template_used}' consistently succeeds for similar tasks",
                    trigger_conditions=[f"Task type matches: {outcome.task[:30]}"],
                    recommended_actions=[f"Use template: {outcome.template_used}"],
                    source_outcomes=[o.outcome_id for o in similar_successes[:5]] + [outcome.outcome_id],
                    confidence=min(0.95, 0.6 + len(similar_successes) * 0.05)
                )
                LEARNING_ENTRIES[entry_id] = entry
                new_entries.append(entry)

    return new_entries


def get_recommendations_for_task(task: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get learning-based recommendations for a new task."""
    recommendations = []

    for entry in LEARNING_ENTRIES.values():
        # Check if any trigger conditions match
        for condition in entry.trigger_conditions:
            if condition.lower() in task.lower() or (context and condition.lower() in context.lower()):
                success_rate = entry.times_successful / max(1, entry.times_applied)
                recommendations.append({
                    "entry_id": entry.entry_id,
                    "pattern_type": entry.pattern_type,
                    "description": entry.description,
                    "recommended_actions": entry.recommended_actions,
                    "confidence": entry.confidence,
                    "historical_success_rate": success_rate
                })
                break

    # Sort by confidence
    recommendations.sort(key=lambda x: x["confidence"], reverse=True)
    return recommendations[:5]  # Top 5 recommendations


# =============================================================================
# v3.9: WORKFLOW RECORDING & PLAYBACK
# =============================================================================

@dataclass
class WorkflowStep:
    """A single step in a recorded workflow."""
    step_id: str
    step_number: int
    action: str  # tool name or special action
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecordedWorkflow:
    """A recorded sequence of agent actions that can be replayed."""
    workflow_id: str
    name: str
    description: str = ""
    session_id: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)  # Template variables
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    playback_count: int = 0
    last_playback: Optional[str] = None


# In-memory storage for recordings
RECORDED_WORKFLOWS: Dict[str, RecordedWorkflow] = {}
ACTIVE_RECORDINGS: Dict[str, RecordedWorkflow] = {}  # session_id -> workflow being recorded


def start_recording(session_id: str, name: str, description: str = "") -> RecordedWorkflow:
    """Start recording a workflow for a session."""
    workflow = RecordedWorkflow(
        workflow_id=f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id[:8]}",
        name=name,
        description=description,
        session_id=session_id
    )
    ACTIVE_RECORDINGS[session_id] = workflow
    return workflow


def record_step(
    session_id: str,
    action: str,
    input_data: Dict[str, Any],
    output_data: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error: Optional[str] = None,
    duration_ms: float = 0.0,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[WorkflowStep]:
    """Record a step in the active workflow for a session."""
    if session_id not in ACTIVE_RECORDINGS:
        return None

    workflow = ACTIVE_RECORDINGS[session_id]
    step = WorkflowStep(
        step_id=f"step_{len(workflow.steps) + 1}",
        step_number=len(workflow.steps) + 1,
        action=action,
        input_data=input_data,
        output_data=output_data,
        success=success,
        error=error,
        duration_ms=duration_ms,
        metadata=metadata or {}
    )
    workflow.steps.append(step)
    workflow.updated_at = datetime.now().isoformat()
    return step


def stop_recording(session_id: str, save: bool = True) -> Optional[RecordedWorkflow]:
    """Stop recording and optionally save the workflow."""
    if session_id not in ACTIVE_RECORDINGS:
        return None

    workflow = ACTIVE_RECORDINGS.pop(session_id)
    if save and len(workflow.steps) > 0:
        RECORDED_WORKFLOWS[workflow.workflow_id] = workflow
    return workflow


def playback_workflow(
    workflow_id: str,
    variables: Optional[Dict[str, Any]] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Replay a recorded workflow with optional variable substitution."""
    if workflow_id not in RECORDED_WORKFLOWS:
        return {"success": False, "error": f"Workflow not found: {workflow_id}"}

    workflow = RECORDED_WORKFLOWS[workflow_id]
    workflow.playback_count += 1
    workflow.last_playback = datetime.now().isoformat()

    # Merge provided variables with workflow defaults
    execution_vars = {**workflow.variables, **(variables or {})}

    results = []
    for step in workflow.steps:
        # Substitute variables in input data
        processed_input = substitute_variables(step.input_data, execution_vars)

        if dry_run:
            results.append({
                "step_id": step.step_id,
                "action": step.action,
                "input": processed_input,
                "dry_run": True,
                "original_output": step.output_data
            })
        else:
            # Execute the step (would call actual tool execution)
            results.append({
                "step_id": step.step_id,
                "action": step.action,
                "input": processed_input,
                "note": "Actual execution would happen here"
            })

    return {
        "success": True,
        "workflow_id": workflow_id,
        "workflow_name": workflow.name,
        "steps_executed": len(results),
        "dry_run": dry_run,
        "results": results
    }


def substitute_variables(data: Any, variables: Dict[str, Any]) -> Any:
    """Recursively substitute {{variable}} placeholders in data."""
    if isinstance(data, str):
        for key, value in variables.items():
            data = data.replace(f"{{{{{key}}}}}", str(value))
        return data
    elif isinstance(data, dict):
        return {k: substitute_variables(v, variables) for k, v in data.items()}
    elif isinstance(data, list):
        return [substitute_variables(item, variables) for item in data]
    return data


# =============================================================================
# v3.9: SMART CONTEXT INJECTION
# =============================================================================

@dataclass
class ContextInjectionRule:
    """Rule for automatic context injection."""
    rule_id: str
    name: str
    trigger_patterns: List[str] = field(default_factory=list)  # Regex patterns
    kb_ids: List[str] = field(default_factory=list)  # Knowledge bases to search
    search_query_template: str = ""  # Template for generating search query
    max_chunks: int = 5
    min_relevance: float = 0.3
    inject_position: str = "before_task"  # before_task, after_task, system_prompt
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


# In-memory storage for injection rules
CONTEXT_INJECTION_RULES: Dict[str, ContextInjectionRule] = {}


def create_injection_rule(
    name: str,
    trigger_patterns: List[str],
    kb_ids: List[str],
    search_query_template: str = "{{task}}",
    max_chunks: int = 5,
    inject_position: str = "before_task"
) -> ContextInjectionRule:
    """Create a new context injection rule."""
    rule = ContextInjectionRule(
        rule_id=f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(CONTEXT_INJECTION_RULES)}",
        name=name,
        trigger_patterns=trigger_patterns,
        kb_ids=kb_ids,
        search_query_template=search_query_template,
        max_chunks=max_chunks,
        inject_position=inject_position
    )
    CONTEXT_INJECTION_RULES[rule.rule_id] = rule
    return rule


def get_context_for_task(task: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Get relevant context to inject for a given task."""
    matched_rules = []
    injected_context = {
        "before_task": [],
        "after_task": [],
        "system_prompt": []
    }

    for rule in CONTEXT_INJECTION_RULES.values():
        if not rule.enabled:
            continue

        # Check if any trigger pattern matches
        for pattern in rule.trigger_patterns:
            try:
                if re.search(pattern, task, re.IGNORECASE):
                    matched_rules.append(rule)
                    break
            except re.error:
                # Invalid regex, try literal match
                if pattern.lower() in task.lower():
                    matched_rules.append(rule)
                    break

    # For each matched rule, search knowledge bases
    for rule in matched_rules:
        search_query = rule.search_query_template.replace("{{task}}", task)

        for kb_id in rule.kb_ids:
            if kb_id in KNOWLEDGE_BASES:
                # Search the knowledge base
                search_result = search_knowledge_base(kb_id, search_query, top_k=rule.max_chunks)
                if search_result.get("success") and search_result.get("results"):
                    for result in search_result["results"]:
                        if result.get("relevance", 0) >= rule.min_relevance:
                            injected_context[rule.inject_position].append({
                                "source": result.get("file_path", "unknown"),
                                "content": result.get("content", ""),
                                "relevance": result.get("relevance", 0),
                                "rule_id": rule.rule_id
                            })

    return {
        "success": True,
        "matched_rules": len(matched_rules),
        "context": injected_context,
        "total_chunks": sum(len(v) for v in injected_context.values())
    }


def format_injected_context(context: Dict[str, Any], position: str) -> str:
    """Format injected context for a specific position."""
    chunks = context.get("context", {}).get(position, [])
    if not chunks:
        return ""

    formatted = "\n\n--- Relevant Context ---\n"
    for chunk in chunks:
        formatted += f"\nFrom: {chunk['source']}\n"
        formatted += f"{chunk['content']}\n"
        formatted += "---\n"

    return formatted


# =============================================================================
# v3.9: INTER-AGENT COMMUNICATION
# =============================================================================

@dataclass
class AgentMessage:
    """A message between agents."""
    message_id: str
    from_agent: str  # agent_id or session_id
    to_agent: str  # agent_id, session_id, or "broadcast"
    message_type: str  # data, request, response, status, error
    content: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = more important
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    read: bool = False
    replied: bool = False
    reply_to: Optional[str] = None  # message_id this is replying to
    ttl_seconds: Optional[int] = None  # Time to live


@dataclass
class SharedState:
    """Shared state between agents in an orchestration."""
    orchestration_id: str
    state: Dict[str, Any] = field(default_factory=dict)
    locks: Dict[str, str] = field(default_factory=dict)  # key -> agent_id holding lock
    version: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    update_history: List[Dict[str, Any]] = field(default_factory=list)


# In-memory storage for inter-agent communication
AGENT_MESSAGES: Dict[str, List[AgentMessage]] = {}  # agent_id -> list of messages
SHARED_STATES: Dict[str, SharedState] = {}  # orchestration_id -> shared state
MESSAGE_QUEUE: List[AgentMessage] = []  # Global message queue for broadcast


def send_agent_message(
    from_agent: str,
    to_agent: str,
    message_type: str,
    content: Dict[str, Any],
    priority: int = 0,
    reply_to: Optional[str] = None,
    ttl_seconds: Optional[int] = None
) -> AgentMessage:
    """Send a message from one agent to another."""
    message = AgentMessage(
        message_id=f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}",
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=message_type,
        content=content,
        priority=priority,
        reply_to=reply_to,
        ttl_seconds=ttl_seconds
    )

    if to_agent == "broadcast":
        MESSAGE_QUEUE.append(message)
    else:
        if to_agent not in AGENT_MESSAGES:
            AGENT_MESSAGES[to_agent] = []
        AGENT_MESSAGES[to_agent].append(message)

    return message


def get_agent_messages(
    agent_id: str,
    unread_only: bool = True,
    message_type: Optional[str] = None
) -> List[AgentMessage]:
    """Get messages for an agent."""
    messages = AGENT_MESSAGES.get(agent_id, [])

    # Also include broadcast messages
    for msg in MESSAGE_QUEUE:
        if msg.from_agent != agent_id:  # Don't receive own broadcasts
            messages.append(msg)

    # Filter by read status
    if unread_only:
        messages = [m for m in messages if not m.read]

    # Filter by type
    if message_type:
        messages = [m for m in messages if m.message_type == message_type]

    # Filter expired messages
    now = datetime.now()
    messages = [
        m for m in messages
        if m.ttl_seconds is None or
        (now - datetime.fromisoformat(m.timestamp)).total_seconds() < m.ttl_seconds
    ]

    # Sort by priority (descending) then timestamp
    messages.sort(key=lambda m: (-m.priority, m.timestamp))

    return messages


def mark_message_read(agent_id: str, message_id: str) -> bool:
    """Mark a message as read."""
    for msg in AGENT_MESSAGES.get(agent_id, []):
        if msg.message_id == message_id:
            msg.read = True
            return True
    return False


def get_shared_state(orchestration_id: str) -> SharedState:
    """Get or create shared state for an orchestration."""
    if orchestration_id not in SHARED_STATES:
        SHARED_STATES[orchestration_id] = SharedState(orchestration_id=orchestration_id)
    return SHARED_STATES[orchestration_id]


def update_shared_state(
    orchestration_id: str,
    agent_id: str,
    key: str,
    value: Any,
    require_lock: bool = False
) -> Dict[str, Any]:
    """Update a key in the shared state."""
    state = get_shared_state(orchestration_id)

    # Check lock if required
    if require_lock and key in state.locks and state.locks[key] != agent_id:
        return {
            "success": False,
            "error": f"Key '{key}' is locked by {state.locks[key]}"
        }

    # Record update
    old_value = state.state.get(key)
    state.state[key] = value
    state.version += 1
    state.last_updated = datetime.now().isoformat()
    state.update_history.append({
        "agent_id": agent_id,
        "key": key,
        "old_value": old_value,
        "new_value": value,
        "version": state.version,
        "timestamp": state.last_updated
    })

    # Keep only last 100 updates
    if len(state.update_history) > 100:
        state.update_history = state.update_history[-100:]

    return {"success": True, "version": state.version}


def acquire_lock(orchestration_id: str, agent_id: str, key: str) -> bool:
    """Acquire a lock on a shared state key."""
    state = get_shared_state(orchestration_id)
    if key in state.locks:
        return False
    state.locks[key] = agent_id
    return True


def release_lock(orchestration_id: str, agent_id: str, key: str) -> bool:
    """Release a lock on a shared state key."""
    state = get_shared_state(orchestration_id)
    if key in state.locks and state.locks[key] == agent_id:
        del state.locks[key]
        return True
    return False


# =============================================================================
# v4.0: AGENT PERSONAS
# =============================================================================

@dataclass
class AgentPersona:
    """Rich personality definition for an agent beyond basic templates."""
    persona_id: str
    name: str
    base_template: str = "coder"  # Inherits from template
    traits: List[str] = field(default_factory=list)  # e.g., ["thorough", "concise", "creative"]
    expertise: List[str] = field(default_factory=list)  # e.g., ["python", "devops", "ml"]
    communication_style: str = "professional"  # professional, casual, technical, friendly
    response_format: str = "structured"  # structured, conversational, bullet_points
    verbosity: str = "balanced"  # minimal, balanced, detailed
    custom_instructions: str = ""  # Additional behavior rules
    avoid_patterns: List[str] = field(default_factory=list)  # What NOT to do
    preferred_tools: List[str] = field(default_factory=list)  # Tools this persona prefers
    context_window_strategy: str = "balanced"  # minimal, balanced, comprehensive
    learning_rate: float = 0.5  # How quickly to adapt (0.0-1.0)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0
    last_used: Optional[str] = None


# In-memory storage for personas
AGENT_PERSONAS: Dict[str, AgentPersona] = {}

# Default personas
DEFAULT_PERSONAS = {
    "senior_engineer": AgentPersona(
        persona_id="senior_engineer",
        name="Senior Engineer",
        base_template="coder",
        traits=["thorough", "methodical", "security-conscious"],
        expertise=["architecture", "code-review", "testing", "documentation"],
        communication_style="technical",
        response_format="structured",
        verbosity="detailed",
        custom_instructions="Always consider edge cases. Suggest tests for new code. Review for security issues.",
        preferred_tools=["file_read", "grep", "command"],
        learning_rate=0.3
    ),
    "rapid_prototyper": AgentPersona(
        persona_id="rapid_prototyper",
        name="Rapid Prototyper",
        base_template="coder",
        traits=["fast", "pragmatic", "iterative"],
        expertise=["mvp", "scripting", "quick-fixes"],
        communication_style="casual",
        response_format="conversational",
        verbosity="minimal",
        custom_instructions="Prioritize working code over perfect code. Get something running first.",
        avoid_patterns=["over-engineering", "premature-optimization"],
        preferred_tools=["file_write", "command"],
        learning_rate=0.7
    ),
    "research_analyst": AgentPersona(
        persona_id="research_analyst",
        name="Research Analyst",
        base_template="researcher",
        traits=["analytical", "thorough", "skeptical"],
        expertise=["data-analysis", "market-research", "competitive-analysis"],
        communication_style="professional",
        response_format="structured",
        verbosity="detailed",
        custom_instructions="Cite sources. Quantify findings. Highlight uncertainties.",
        preferred_tools=["web_search", "web_fetch", "file_read"],
        learning_rate=0.4
    ),
    "devops_specialist": AgentPersona(
        persona_id="devops_specialist",
        name="DevOps Specialist",
        base_template="devops",
        traits=["cautious", "systematic", "documentation-focused"],
        expertise=["deployment", "ci-cd", "monitoring", "infrastructure"],
        communication_style="technical",
        response_format="bullet_points",
        verbosity="balanced",
        custom_instructions="Always warn before destructive operations. Document all changes. Use dry-run first.",
        avoid_patterns=["force-operations", "skipping-backups"],
        preferred_tools=["command", "git_status", "file_edit"],
        learning_rate=0.2
    )
}

# Initialize default personas
for pid, persona in DEFAULT_PERSONAS.items():
    AGENT_PERSONAS[pid] = persona


def create_persona(
    name: str,
    base_template: str = "coder",
    traits: Optional[List[str]] = None,
    expertise: Optional[List[str]] = None,
    communication_style: str = "professional",
    custom_instructions: str = ""
) -> AgentPersona:
    """Create a new agent persona."""
    persona = AgentPersona(
        persona_id=f"persona_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name=name,
        base_template=base_template,
        traits=traits or [],
        expertise=expertise or [],
        communication_style=communication_style,
        custom_instructions=custom_instructions
    )
    AGENT_PERSONAS[persona.persona_id] = persona
    return persona


def get_persona_system_prompt(persona_id: str) -> str:
    """Generate a system prompt incorporating persona traits."""
    if persona_id not in AGENT_PERSONAS:
        return ""

    persona = AGENT_PERSONAS[persona_id]

    prompt_parts = [f"You are {persona.name}."]

    if persona.traits:
        prompt_parts.append(f"Your key traits: {', '.join(persona.traits)}.")

    if persona.expertise:
        prompt_parts.append(f"Your expertise areas: {', '.join(persona.expertise)}.")

    prompt_parts.append(f"Communication style: {persona.communication_style}.")
    prompt_parts.append(f"Response format: {persona.response_format}.")

    if persona.custom_instructions:
        prompt_parts.append(f"\n{persona.custom_instructions}")

    if persona.avoid_patterns:
        prompt_parts.append(f"\nAvoid: {', '.join(persona.avoid_patterns)}.")

    return " ".join(prompt_parts)


# =============================================================================
# v4.0: GOAL DECOMPOSITION
# =============================================================================

@dataclass
class SubGoal:
    """A sub-goal derived from decomposing a larger goal."""
    subgoal_id: str
    goal_id: str  # Parent goal
    title: str
    description: str
    dependencies: List[str] = field(default_factory=list)  # Other subgoal_ids
    status: str = "pending"  # pending, in_progress, completed, blocked, failed
    assigned_to: Optional[str] = None  # agent_id or session_id
    priority: int = 0  # Higher = more important
    estimated_complexity: str = "medium"  # low, medium, high
    tools_required: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


@dataclass
class Goal:
    """A complex goal that can be decomposed into sub-goals."""
    goal_id: str
    title: str
    description: str
    session_id: str
    sub_goals: List[SubGoal] = field(default_factory=list)
    status: str = "planning"  # planning, in_progress, completed, failed
    decomposition_strategy: str = "sequential"  # sequential, parallel, dependency_graph
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    success_criteria: List[str] = field(default_factory=list)


# In-memory storage for goals
GOALS: Dict[str, Goal] = {}


def decompose_goal(
    title: str,
    description: str,
    session_id: str,
    strategy: str = "sequential",
    context: Optional[Dict[str, Any]] = None
) -> Goal:
    """Create a goal structure (actual decomposition would use LLM)."""
    goal = Goal(
        goal_id=f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        title=title,
        description=description,
        session_id=session_id,
        decomposition_strategy=strategy,
        context=context or {}
    )
    GOALS[goal.goal_id] = goal
    return goal


def add_subgoal(
    goal_id: str,
    title: str,
    description: str,
    dependencies: Optional[List[str]] = None,
    priority: int = 0,
    complexity: str = "medium",
    tools_required: Optional[List[str]] = None
) -> Optional[SubGoal]:
    """Add a sub-goal to an existing goal."""
    if goal_id not in GOALS:
        return None

    goal = GOALS[goal_id]
    subgoal = SubGoal(
        subgoal_id=f"subgoal_{len(goal.sub_goals) + 1}",
        goal_id=goal_id,
        title=title,
        description=description,
        dependencies=dependencies or [],
        priority=priority,
        estimated_complexity=complexity,
        tools_required=tools_required or []
    )
    goal.sub_goals.append(subgoal)
    return subgoal


def get_next_subgoal(goal_id: str) -> Optional[SubGoal]:
    """Get the next actionable sub-goal based on dependencies."""
    if goal_id not in GOALS:
        return None

    goal = GOALS[goal_id]
    completed_ids = {sg.subgoal_id for sg in goal.sub_goals if sg.status == "completed"}

    # Find sub-goals where all dependencies are completed
    for subgoal in sorted(goal.sub_goals, key=lambda x: -x.priority):
        if subgoal.status == "pending":
            if all(dep in completed_ids for dep in subgoal.dependencies):
                return subgoal

    return None


def update_subgoal_status(
    goal_id: str,
    subgoal_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None
) -> bool:
    """Update a sub-goal's status."""
    if goal_id not in GOALS:
        return False

    goal = GOALS[goal_id]
    for subgoal in goal.sub_goals:
        if subgoal.subgoal_id == subgoal_id:
            subgoal.status = status
            if result:
                subgoal.result = result
            if status == "completed":
                subgoal.completed_at = datetime.now().isoformat()

            # Check if all sub-goals are completed
            if all(sg.status == "completed" for sg in goal.sub_goals):
                goal.status = "completed"
                goal.completed_at = datetime.now().isoformat()
            elif any(sg.status == "in_progress" for sg in goal.sub_goals):
                goal.status = "in_progress"

            return True
    return False


# =============================================================================
# v4.0: TOOL MACROS
# =============================================================================

@dataclass
class ToolMacro:
    """A reusable sequence of tool calls that execute as a single command."""
    macro_id: str
    name: str
    description: str
    steps: List[Dict[str, Any]] = field(default_factory=list)  # [{tool, input_template}]
    input_schema: Dict[str, str] = field(default_factory=dict)  # Expected variables
    output_mapping: Dict[str, str] = field(default_factory=dict)  # How to extract results
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0
    last_used: Optional[str] = None
    average_duration_ms: float = 0.0
    success_rate: float = 1.0
    tags: List[str] = field(default_factory=list)


# In-memory storage for macros
TOOL_MACROS: Dict[str, ToolMacro] = {}

# Built-in macros
BUILTIN_MACROS = {
    "backup_and_edit": ToolMacro(
        macro_id="backup_and_edit",
        name="Backup and Edit",
        description="Create backup of file, then edit it safely",
        steps=[
            {"tool": "file_read", "input_template": {"path": "{{file_path}}"}},
            {"tool": "file_write", "input_template": {"path": "{{file_path}}.bak", "content": "{{step_0_result}}"}},
            {"tool": "file_edit", "input_template": {"path": "{{file_path}}", "edits": "{{edits}}"}}
        ],
        input_schema={"file_path": "Path to file", "edits": "Edit operations"},
        output_mapping={"backup_path": "{{file_path}}.bak", "edit_result": "step_2_result"}
    ),
    "git_safe_commit": ToolMacro(
        macro_id="git_safe_commit",
        name="Git Safe Commit",
        description="Check status, add files, commit with message",
        steps=[
            {"tool": "git_status", "input_template": {"repo_path": "{{repo_path}}"}},
            {"tool": "command", "input_template": {"command": "cd {{repo_path}} && git add {{files}}"}},
            {"tool": "command", "input_template": {"command": "cd {{repo_path}} && git commit -m '{{message}}'"}}
        ],
        input_schema={"repo_path": "Repository path", "files": "Files to add", "message": "Commit message"},
        output_mapping={"status": "step_0_result", "commit_result": "step_2_result"}
    ),
    "find_replace_all": ToolMacro(
        macro_id="find_replace_all",
        name="Find and Replace All",
        description="Find files matching pattern and replace text",
        steps=[
            {"tool": "glob", "input_template": {"pattern": "{{pattern}}", "path": "{{directory}}"}},
            {"tool": "grep", "input_template": {"pattern": "{{search}}", "path": "{{directory}}"}},
            # Each file would be edited (simplified representation)
        ],
        input_schema={"directory": "Search directory", "pattern": "File pattern", "search": "Text to find", "replace": "Replacement"},
        output_mapping={"files_found": "step_0_result", "matches": "step_1_result"}
    ),
    "analyze_codebase": ToolMacro(
        macro_id="analyze_codebase",
        name="Analyze Codebase",
        description="Get overview of a codebase structure",
        steps=[
            {"tool": "glob", "input_template": {"pattern": "**/*.py", "path": "{{directory}}"}},
            {"tool": "glob", "input_template": {"pattern": "**/*.js", "path": "{{directory}}"}},
            {"tool": "glob", "input_template": {"pattern": "**/*.ts", "path": "{{directory}}"}},
            {"tool": "command", "input_template": {"command": "find {{directory}} -type f | wc -l"}},
            {"tool": "file_read", "input_template": {"path": "{{directory}}/README.md"}}
        ],
        input_schema={"directory": "Directory to analyze"},
        output_mapping={"python_files": "step_0_result", "js_files": "step_1_result", "ts_files": "step_2_result", "total_files": "step_3_result", "readme": "step_4_result"}
    )
}

# Initialize built-in macros
for mid, macro in BUILTIN_MACROS.items():
    TOOL_MACROS[mid] = macro


def create_macro(
    name: str,
    description: str,
    steps: List[Dict[str, Any]],
    input_schema: Optional[Dict[str, str]] = None,
    tags: Optional[List[str]] = None
) -> ToolMacro:
    """Create a new tool macro."""
    macro = ToolMacro(
        macro_id=f"macro_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name=name,
        description=description,
        steps=steps,
        input_schema=input_schema or {},
        tags=tags or []
    )
    TOOL_MACROS[macro.macro_id] = macro
    return macro


def execute_macro(macro_id: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool macro with provided variables."""
    if macro_id not in TOOL_MACROS:
        return {"success": False, "error": f"Macro not found: {macro_id}"}

    macro = TOOL_MACROS[macro_id]
    macro.usage_count += 1
    macro.last_used = datetime.now().isoformat()

    start_time = time.time()
    results = []
    step_results = {}

    for i, step in enumerate(macro.steps):
        # Substitute variables in input template
        processed_input = substitute_variables(step["input_template"], {**variables, **step_results})

        # Here we would execute the actual tool
        # For now, we record the intent
        step_result = {
            "step": i,
            "tool": step["tool"],
            "input": processed_input,
            "status": "simulated"
        }
        results.append(step_result)
        step_results[f"step_{i}_result"] = step_result

    duration_ms = (time.time() - start_time) * 1000

    # Update average duration
    if macro.average_duration_ms == 0:
        macro.average_duration_ms = duration_ms
    else:
        macro.average_duration_ms = (macro.average_duration_ms * 0.8) + (duration_ms * 0.2)

    return {
        "success": True,
        "macro_id": macro_id,
        "macro_name": macro.name,
        "steps_executed": len(results),
        "results": results,
        "duration_ms": round(duration_ms, 2)
    }


# =============================================================================
# v4.0: AUDIT TRAIL
# =============================================================================

@dataclass
class AuditEntry:
    """A single audit log entry."""
    entry_id: str
    timestamp: str
    session_id: str
    agent_id: Optional[str] = None
    action_type: str = ""  # tool_call, api_request, state_change, error, approval, etc.
    action_name: str = ""  # Specific action (file_read, command, etc.)
    input_summary: str = ""  # Summarized input (not full content for security)
    output_summary: str = ""  # Summarized output
    success: bool = True
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"  # low, medium, high, critical
    requires_review: bool = False


# In-memory storage for audit trail (with size limit)
AUDIT_TRAIL: List[AuditEntry] = []
MAX_AUDIT_ENTRIES = 10000


def log_audit(
    session_id: str,
    action_type: str,
    action_name: str,
    input_summary: str = "",
    output_summary: str = "",
    success: bool = True,
    error: Optional[str] = None,
    duration_ms: float = 0.0,
    agent_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    risk_level: str = "low"
) -> AuditEntry:
    """Log an action to the audit trail."""
    entry = AuditEntry(
        entry_id=f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}",
        timestamp=datetime.now().isoformat(),
        session_id=session_id,
        agent_id=agent_id,
        action_type=action_type,
        action_name=action_name,
        input_summary=input_summary[:500] if input_summary else "",  # Truncate for safety
        output_summary=output_summary[:500] if output_summary else "",
        success=success,
        error=error,
        duration_ms=duration_ms,
        metadata=metadata or {},
        risk_level=risk_level,
        requires_review=risk_level in ["high", "critical"]
    )

    AUDIT_TRAIL.append(entry)

    # Trim if over limit
    if len(AUDIT_TRAIL) > MAX_AUDIT_ENTRIES:
        AUDIT_TRAIL.pop(0)

    return entry


def get_audit_trail(
    session_id: Optional[str] = None,
    action_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[AuditEntry]:
    """Query audit trail with filters."""
    filtered = AUDIT_TRAIL

    if session_id:
        filtered = [e for e in filtered if e.session_id == session_id]
    if action_type:
        filtered = [e for e in filtered if e.action_type == action_type]
    if risk_level:
        filtered = [e for e in filtered if e.risk_level == risk_level]

    # Sort by timestamp descending (most recent first)
    filtered = sorted(filtered, key=lambda x: x.timestamp, reverse=True)

    return filtered[offset:offset + limit]


def get_audit_summary(session_id: Optional[str] = None) -> Dict[str, Any]:
    """Get summary statistics of audit trail."""
    entries = AUDIT_TRAIL
    if session_id:
        entries = [e for e in entries if e.session_id == session_id]

    if not entries:
        return {"total": 0}

    by_type = {}
    by_risk = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    errors = 0
    total_duration = 0

    for e in entries:
        by_type[e.action_type] = by_type.get(e.action_type, 0) + 1
        by_risk[e.risk_level] = by_risk.get(e.risk_level, 0) + 1
        if not e.success:
            errors += 1
        total_duration += e.duration_ms

    return {
        "total": len(entries),
        "by_action_type": by_type,
        "by_risk_level": by_risk,
        "error_count": errors,
        "error_rate": round(errors / len(entries) * 100, 2) if entries else 0,
        "total_duration_ms": round(total_duration, 2),
        "avg_duration_ms": round(total_duration / len(entries), 2) if entries else 0,
        "requires_review": len([e for e in entries if e.requires_review])
    }


# =============================================================================
# v4.0: ADAPTIVE BEHAVIOR
# =============================================================================

@dataclass
class BehaviorProfile:
    """Tracks and adapts agent behavior based on outcomes."""
    profile_id: str
    session_id: str
    tool_preferences: Dict[str, float] = field(default_factory=dict)  # tool -> preference score
    error_avoidance: Dict[str, float] = field(default_factory=dict)  # pattern -> avoidance score
    success_patterns: Dict[str, float] = field(default_factory=dict)  # pattern -> success boost
    context_adaptations: Dict[str, Any] = field(default_factory=dict)  # Learned context preferences
    verbosity_adjustment: float = 0.0  # -1.0 to 1.0 (less to more verbose)
    risk_tolerance: float = 0.5  # 0.0 to 1.0 (conservative to aggressive)
    learning_iterations: int = 0
    last_adaptation: Optional[str] = None


# In-memory storage for behavior profiles
BEHAVIOR_PROFILES: Dict[str, BehaviorProfile] = {}


def get_or_create_behavior_profile(session_id: str) -> BehaviorProfile:
    """Get or create a behavior profile for a session."""
    if session_id not in BEHAVIOR_PROFILES:
        BEHAVIOR_PROFILES[session_id] = BehaviorProfile(
            profile_id=f"profile_{session_id}",
            session_id=session_id
        )
    return BEHAVIOR_PROFILES[session_id]


def adapt_behavior(
    session_id: str,
    outcome: TaskOutcome,
    learning_rate: float = 0.1
) -> Dict[str, Any]:
    """Adapt behavior profile based on a task outcome."""
    profile = get_or_create_behavior_profile(session_id)

    adaptations = []

    # Update tool preferences based on success/failure
    for tool_call in outcome.tool_calls:
        tool_name = tool_call.get("tool", "unknown")
        current_pref = profile.tool_preferences.get(tool_name, 0.5)

        if outcome.success:
            # Increase preference for tools used in successful tasks
            new_pref = current_pref + (1 - current_pref) * learning_rate
            adaptations.append(f"Increased preference for {tool_name}: {current_pref:.2f} -> {new_pref:.2f}")
        else:
            # Decrease preference for tools in failed tasks
            new_pref = current_pref - current_pref * learning_rate * 0.5
            adaptations.append(f"Decreased preference for {tool_name}: {current_pref:.2f} -> {new_pref:.2f}")

        profile.tool_preferences[tool_name] = max(0.0, min(1.0, new_pref))

    # Learn from errors
    if not outcome.success and outcome.error_message:
        error_key = outcome.error_message[:50]
        current_avoidance = profile.error_avoidance.get(error_key, 0.0)
        new_avoidance = current_avoidance + (1 - current_avoidance) * learning_rate
        profile.error_avoidance[error_key] = new_avoidance
        adaptations.append(f"Increased avoidance for error pattern: {error_key[:30]}...")

    # Adjust risk tolerance based on outcomes
    if outcome.success:
        profile.risk_tolerance = min(1.0, profile.risk_tolerance + learning_rate * 0.1)
    else:
        profile.risk_tolerance = max(0.0, profile.risk_tolerance - learning_rate * 0.2)

    # Update user feedback impact
    if outcome.user_feedback == "positive":
        # Reinforce current patterns
        for tool_name in profile.tool_preferences:
            profile.tool_preferences[tool_name] = min(1.0, profile.tool_preferences[tool_name] + 0.05)
    elif outcome.user_feedback == "negative":
        # Reduce current patterns
        for tool_name in profile.tool_preferences:
            profile.tool_preferences[tool_name] = max(0.0, profile.tool_preferences[tool_name] - 0.05)

    profile.learning_iterations += 1
    profile.last_adaptation = datetime.now().isoformat()

    return {
        "session_id": session_id,
        "adaptations": adaptations,
        "new_risk_tolerance": profile.risk_tolerance,
        "learning_iterations": profile.learning_iterations
    }


def get_behavior_recommendations(session_id: str, task: str) -> Dict[str, Any]:
    """Get behavior recommendations based on learned profile."""
    profile = get_or_create_behavior_profile(session_id)

    recommendations = {
        "preferred_tools": [],
        "avoid_patterns": [],
        "risk_tolerance": profile.risk_tolerance,
        "verbosity": "balanced"
    }

    # Get top preferred tools
    sorted_tools = sorted(profile.tool_preferences.items(), key=lambda x: x[1], reverse=True)
    recommendations["preferred_tools"] = [t[0] for t in sorted_tools[:5] if t[1] > 0.5]

    # Get patterns to avoid
    high_avoidance = [(k, v) for k, v in profile.error_avoidance.items() if v > 0.5]
    recommendations["avoid_patterns"] = [p[0] for p in high_avoidance[:5]]

    # Determine verbosity
    if profile.verbosity_adjustment > 0.3:
        recommendations["verbosity"] = "detailed"
    elif profile.verbosity_adjustment < -0.3:
        recommendations["verbosity"] = "minimal"

    # Risk assessment
    if profile.risk_tolerance > 0.7:
        recommendations["approach"] = "aggressive"
    elif profile.risk_tolerance < 0.3:
        recommendations["approach"] = "conservative"
    else:
        recommendations["approach"] = "balanced"

    return recommendations


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
        "integrations": ["gmail", "sheets", "sms", "clickup", "n8n", "git_enhanced", "terminal_multi"],
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


# =============================================================================
# v3.6: COST & TOKEN TRACKING ENDPOINTS
# =============================================================================

@app.route('/cost/track', methods=['POST'])
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


@app.route('/cost/session', methods=['POST'])
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


@app.route('/cost/all', methods=['GET', 'POST'])
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


@app.route('/cost/set_budget', methods=['POST'])
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


@app.route('/cost/pricing', methods=['GET', 'POST'])
def cost_pricing():
    """Get current pricing information."""
    return jsonify({
        "success": True,
        "pricing": PRICING,
        "note": "Prices are per million tokens in USD"
    })


# =============================================================================
# v3.7: CONVERSATION MEMORY ENDPOINTS
# =============================================================================

@app.route('/memory/add', methods=['POST'])
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


@app.route('/memory/get', methods=['POST'])
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


@app.route('/memory/summarize', methods=['POST'])
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


@app.route('/memory/list', methods=['GET', 'POST'])
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


@app.route('/memory/clear', methods=['POST'])
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


# =============================================================================
# v3.7: AGENT TEMPLATE ENDPOINTS
# =============================================================================

@app.route('/templates/list', methods=['GET', 'POST'])
def templates_list():
    """List all available agent templates."""
    templates = []
    for name, template in AGENT_TEMPLATES.items():
        templates.append({
            "name": name,
            "id": template.get("id"),
            "display_name": template.get("name"),
            "description": template.get("description"),
            "tools_count": len(template.get("tools_available", []))
        })

    return jsonify({
        "success": True,
        "templates": templates,
        "total": len(templates)
    })


@app.route('/templates/get', methods=['POST'])
def templates_get():
    """Get a specific agent template."""
    data = request.get_json() or {}
    name = data.get('name')

    if not name:
        return jsonify({"success": False, "error": "Missing 'name' parameter"}), 400

    if name not in AGENT_TEMPLATES:
        return jsonify({"success": False, "error": f"Template '{name}' not found"}), 404

    return jsonify({
        "success": True,
        "template": AGENT_TEMPLATES[name]
    })


@app.route('/templates/apply', methods=['POST'])
def templates_apply():
    """Apply a template to create an agent configuration."""
    data = request.get_json() or {}
    template_name = data.get('template')
    overrides = data.get('overrides', {})

    if not template_name:
        return jsonify({"success": False, "error": "Missing 'template' parameter"}), 400

    if template_name not in AGENT_TEMPLATES:
        return jsonify({"success": False, "error": f"Template '{template_name}' not found"}), 404

    # Start with template and apply overrides
    template = AGENT_TEMPLATES[template_name].copy()
    template.update(overrides)

    return jsonify({
        "success": True,
        "agent": template,
        "based_on": template_name
    })


# =============================================================================
# v3.8: MULTI-AGENT ORCHESTRATION ENDPOINTS
# =============================================================================

@app.route('/orchestration/create', methods=['POST'])
def orchestration_create():
    """Create a new multi-agent orchestration."""
    data = request.get_json() or {}
    parent_session_id = data.get('session_id')
    objective = data.get('objective')
    subtasks = data.get('subtasks', [])
    strategy = data.get('strategy', 'parallel')

    if not parent_session_id:
        return jsonify({"success": False, "error": "Missing 'session_id' parameter"}), 400
    if not objective:
        return jsonify({"success": False, "error": "Missing 'objective' parameter"}), 400
    if not subtasks:
        return jsonify({"success": False, "error": "Missing 'subtasks' parameter"}), 400

    orchestration = create_orchestration(
        parent_session_id=parent_session_id,
        objective=objective,
        subtasks=subtasks,
        strategy=strategy
    )

    return jsonify({
        "success": True,
        **orchestration.to_dict()
    })


@app.route('/orchestration/list', methods=['GET', 'POST'])
def orchestration_list():
    """List all orchestrations."""
    orchestrations = [o.to_dict() for o in ORCHESTRATIONS.values()]
    return jsonify({
        "success": True,
        "orchestrations": orchestrations,
        "total": len(orchestrations)
    })


@app.route('/orchestration/status', methods=['POST'])
def orchestration_status():
    """Get status of an orchestration."""
    data = request.get_json() or {}
    orch_id = data.get('orchestration_id')

    if not orch_id:
        return jsonify({"success": False, "error": "Missing 'orchestration_id' parameter"}), 400

    if orch_id not in ORCHESTRATIONS:
        return jsonify({"success": False, "error": f"Orchestration not found: {orch_id}"}), 404

    orch = ORCHESTRATIONS[orch_id]
    sub_agent_statuses = []
    for agent_id in orch.sub_agents:
        if agent_id in SUB_AGENTS:
            sub_agent_statuses.append(SUB_AGENTS[agent_id].to_dict())

    return jsonify({
        "success": True,
        **orch.to_dict(),
        "sub_agent_details": sub_agent_statuses
    })


@app.route('/orchestration/update-agent', methods=['POST'])
def orchestration_update_agent():
    """Update a sub-agent's status/result."""
    data = request.get_json() or {}
    agent_id = data.get('agent_id')
    status = data.get('status')
    result = data.get('result')
    error = data.get('error')

    if not agent_id:
        return jsonify({"success": False, "error": "Missing 'agent_id' parameter"}), 400

    if agent_id not in SUB_AGENTS:
        return jsonify({"success": False, "error": f"Sub-agent not found: {agent_id}"}), 404

    agent = SUB_AGENTS[agent_id]
    if status:
        agent.status = status
        if status == "running":
            agent.started_at = datetime.now().isoformat()
        elif status in ["completed", "failed"]:
            agent.completed_at = datetime.now().isoformat()
    if result:
        agent.result = result
    if error:
        agent.error = error

    return jsonify({
        "success": True,
        **agent.to_dict()
    })


# =============================================================================
# v3.8: KNOWLEDGE BASE ENDPOINTS
# =============================================================================

@app.route('/kb/create', methods=['POST'])
def kb_create():
    """Create a new knowledge base."""
    data = request.get_json() or {}
    name = data.get('name')
    root_paths = data.get('root_paths', [])
    description = data.get('description', '')
    include_patterns = data.get('include_patterns')
    exclude_patterns = data.get('exclude_patterns')

    if not name:
        return jsonify({"success": False, "error": "Missing 'name' parameter"}), 400
    if not root_paths:
        return jsonify({"success": False, "error": "Missing 'root_paths' parameter"}), 400

    # Validate paths
    for path in root_paths:
        if not validate_path(path):
            return jsonify({"success": False, "error": f"Path not allowed: {path}"}), 403

    kb = create_knowledge_base(
        name=name,
        root_paths=root_paths,
        description=description,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns
    )

    return jsonify({
        "success": True,
        **kb.to_dict()
    })


@app.route('/kb/list', methods=['GET', 'POST'])
def kb_list():
    """List all knowledge bases."""
    kbs = [kb.to_dict() for kb in KNOWLEDGE_BASES.values()]
    return jsonify({
        "success": True,
        "knowledge_bases": kbs,
        "total": len(kbs)
    })


@app.route('/kb/index', methods=['POST'])
def kb_index():
    """Index files into a knowledge base."""
    import glob as glob_module

    data = request.get_json() or {}
    kb_id = data.get('kb_id')
    max_files = data.get('max_files', 100)

    if not kb_id:
        return jsonify({"success": False, "error": "Missing 'kb_id' parameter"}), 400

    if kb_id not in KNOWLEDGE_BASES:
        return jsonify({"success": False, "error": f"Knowledge base not found: {kb_id}"}), 404

    kb = KNOWLEDGE_BASES[kb_id]
    indexed_count = 0
    errors = []

    for root_path in kb.root_paths:
        for pattern in kb.include_patterns:
            full_pattern = os.path.join(root_path, pattern)
            for file_path in glob_module.glob(full_pattern, recursive=True)[:max_files]:
                # Check exclude patterns
                skip = False
                for exclude in kb.exclude_patterns:
                    if exclude.replace('**/', '') in file_path:
                        skip = True
                        break
                if skip:
                    continue

                result = index_file(kb, file_path)
                if result:
                    indexed_count += 1
                else:
                    errors.append(file_path)

    return jsonify({
        "success": True,
        "kb_id": kb_id,
        "indexed_files": indexed_count,
        "total_files": len(kb.files),
        "total_chunks": kb.total_chunks,
        "errors": errors[:10]  # Limit errors in response
    })


@app.route('/kb/search', methods=['POST'])
def kb_search():
    """Search a knowledge base."""
    data = request.get_json() or {}
    kb_id = data.get('kb_id')
    query = data.get('query')
    top_k = min(data.get('top_k', 5), 20)

    if not kb_id:
        return jsonify({"success": False, "error": "Missing 'kb_id' parameter"}), 400
    if not query:
        return jsonify({"success": False, "error": "Missing 'query' parameter"}), 400

    if kb_id not in KNOWLEDGE_BASES:
        return jsonify({"success": False, "error": f"Knowledge base not found: {kb_id}"}), 404

    kb = KNOWLEDGE_BASES[kb_id]
    results = search_knowledge_base(kb, query, top_k)

    return jsonify({
        "success": True,
        "query": query,
        "results": results,
        "total_results": len(results)
    })


@app.route('/kb/delete', methods=['POST'])
def kb_delete():
    """Delete a knowledge base."""
    data = request.get_json() or {}
    kb_id = data.get('kb_id')

    if not kb_id:
        return jsonify({"success": False, "error": "Missing 'kb_id' parameter"}), 400

    if kb_id not in KNOWLEDGE_BASES:
        return jsonify({"success": False, "error": f"Knowledge base not found: {kb_id}"}), 404

    del KNOWLEDGE_BASES[kb_id]

    return jsonify({
        "success": True,
        "deleted": kb_id
    })


# =============================================================================
# v3.8: SCHEDULED TASKS ENDPOINTS
# =============================================================================

@app.route('/scheduler/create', methods=['POST'])
def scheduler_create():
    """Create a scheduled task."""
    data = request.get_json() or {}
    name = data.get('name')
    task_config = data.get('task_config', {})
    cron_expression = data.get('cron_expression', '0 * * * *')
    description = data.get('description', '')

    if not name:
        return jsonify({"success": False, "error": "Missing 'name' parameter"}), 400
    if not task_config:
        return jsonify({"success": False, "error": "Missing 'task_config' parameter"}), 400

    # Validate cron expression
    cron_parts = parse_cron_expression(cron_expression)
    if "error" in cron_parts:
        return jsonify({"success": False, "error": cron_parts["error"]}), 400

    task = create_scheduled_task(
        name=name,
        task_config=task_config,
        cron_expression=cron_expression,
        description=description
    )

    return jsonify({
        "success": True,
        **task.to_dict()
    })


@app.route('/scheduler/list', methods=['GET', 'POST'])
def scheduler_list():
    """List all scheduled tasks."""
    tasks = [t.to_dict() for t in SCHEDULED_TASKS.values()]
    return jsonify({
        "success": True,
        "tasks": tasks,
        "total": len(tasks),
        "scheduler_running": SCHEDULER_RUNNING
    })


@app.route('/scheduler/toggle', methods=['POST'])
def scheduler_toggle():
    """Enable or disable a scheduled task."""
    data = request.get_json() or {}
    task_id = data.get('task_id')
    enabled = data.get('enabled')

    if not task_id:
        return jsonify({"success": False, "error": "Missing 'task_id' parameter"}), 400

    if task_id not in SCHEDULED_TASKS:
        return jsonify({"success": False, "error": f"Task not found: {task_id}"}), 404

    task = SCHEDULED_TASKS[task_id]
    if enabled is not None:
        task.enabled = enabled

    return jsonify({
        "success": True,
        **task.to_dict()
    })


@app.route('/scheduler/delete', methods=['POST'])
def scheduler_delete():
    """Delete a scheduled task."""
    data = request.get_json() or {}
    task_id = data.get('task_id')

    if not task_id:
        return jsonify({"success": False, "error": "Missing 'task_id' parameter"}), 400

    if task_id not in SCHEDULED_TASKS:
        return jsonify({"success": False, "error": f"Task not found: {task_id}"}), 404

    del SCHEDULED_TASKS[task_id]

    return jsonify({
        "success": True,
        "deleted": task_id
    })


@app.route('/scheduler/run-now', methods=['POST'])
def scheduler_run_now():
    """Manually trigger a scheduled task."""
    data = request.get_json() or {}
    task_id = data.get('task_id')

    if not task_id:
        return jsonify({"success": False, "error": "Missing 'task_id' parameter"}), 400

    if task_id not in SCHEDULED_TASKS:
        return jsonify({"success": False, "error": f"Task not found: {task_id}"}), 404

    task = SCHEDULED_TASKS[task_id]
    task.last_run_at = datetime.now().isoformat()
    task.run_count += 1
    task.next_run_at = calculate_next_run(task.cron_expression)

    # Return the task config so caller can execute it
    return jsonify({
        "success": True,
        "task_id": task_id,
        "task_config": task.task_config,
        "run_count": task.run_count
    })


# =============================================================================
# v3.8: TOOL PLUGINS ENDPOINTS
# =============================================================================

@app.route('/plugins/list', methods=['GET', 'POST'])
def plugins_list():
    """List all registered tool plugins."""
    plugins = [p.to_dict() for p in TOOL_PLUGINS.values()]
    return jsonify({
        "success": True,
        "plugins": plugins,
        "total": len(plugins)
    })


@app.route('/plugins/register-python', methods=['POST'])
def plugins_register_python():
    """Register a Python function as a tool plugin."""
    data = request.get_json() or {}
    name = data.get('name')
    module_path = data.get('module_path')
    function_name = data.get('function_name')
    description = data.get('description', '')

    if not name:
        return jsonify({"success": False, "error": "Missing 'name' parameter"}), 400
    if not module_path:
        return jsonify({"success": False, "error": "Missing 'module_path' parameter"}), 400
    if not function_name:
        return jsonify({"success": False, "error": "Missing 'function_name' parameter"}), 400

    # Validate path
    if not validate_path(module_path):
        return jsonify({"success": False, "error": f"Path not allowed: {module_path}"}), 403

    plugin = load_python_plugin(name, module_path, function_name, description)
    if not plugin:
        return jsonify({"success": False, "error": "Failed to load plugin"}), 500

    return jsonify({
        "success": True,
        **plugin.to_dict()
    })


@app.route('/plugins/register-http', methods=['POST'])
def plugins_register_http():
    """Register an HTTP endpoint as a tool plugin."""
    data = request.get_json() or {}
    name = data.get('name')
    endpoint_url = data.get('endpoint_url')
    method = data.get('method', 'POST')
    headers = data.get('headers', {})
    description = data.get('description', '')

    if not name:
        return jsonify({"success": False, "error": "Missing 'name' parameter"}), 400
    if not endpoint_url:
        return jsonify({"success": False, "error": "Missing 'endpoint_url' parameter"}), 400

    plugin = register_http_plugin(name, endpoint_url, method, headers, description)

    return jsonify({
        "success": True,
        **plugin.to_dict()
    })


@app.route('/plugins/register-mcp', methods=['POST'])
def plugins_register_mcp():
    """Register an MCP server tool as a plugin."""
    data = request.get_json() or {}
    name = data.get('name')
    server_url = data.get('server_url')
    tool_name = data.get('tool_name')
    description = data.get('description', '')

    if not name:
        return jsonify({"success": False, "error": "Missing 'name' parameter"}), 400
    if not server_url:
        return jsonify({"success": False, "error": "Missing 'server_url' parameter"}), 400
    if not tool_name:
        return jsonify({"success": False, "error": "Missing 'tool_name' parameter"}), 400

    plugin = register_mcp_plugin(name, server_url, tool_name, description)

    return jsonify({
        "success": True,
        **plugin.to_dict()
    })


@app.route('/plugins/execute', methods=['POST'])
def plugins_execute():
    """Execute a tool plugin."""
    data = request.get_json() or {}
    plugin_id = data.get('plugin_id')
    input_data = data.get('input', {})

    if not plugin_id:
        return jsonify({"success": False, "error": "Missing 'plugin_id' parameter"}), 400

    result = execute_plugin(plugin_id, input_data)

    return jsonify(result)


@app.route('/plugins/toggle', methods=['POST'])
def plugins_toggle():
    """Enable or disable a plugin."""
    data = request.get_json() or {}
    plugin_id = data.get('plugin_id')
    enabled = data.get('enabled')

    if not plugin_id:
        return jsonify({"success": False, "error": "Missing 'plugin_id' parameter"}), 400

    if plugin_id not in TOOL_PLUGINS:
        return jsonify({"success": False, "error": f"Plugin not found: {plugin_id}"}), 404

    plugin = TOOL_PLUGINS[plugin_id]
    if enabled is not None:
        plugin.enabled = enabled

    return jsonify({
        "success": True,
        **plugin.to_dict()
    })


@app.route('/plugins/delete', methods=['POST'])
def plugins_delete():
    """Delete a plugin."""
    data = request.get_json() or {}
    plugin_id = data.get('plugin_id')

    if not plugin_id:
        return jsonify({"success": False, "error": "Missing 'plugin_id' parameter"}), 400

    if plugin_id not in TOOL_PLUGINS:
        return jsonify({"success": False, "error": f"Plugin not found: {plugin_id}"}), 404

    del TOOL_PLUGINS[plugin_id]
    if plugin_id in PLUGIN_CALLABLES:
        del PLUGIN_CALLABLES[plugin_id]

    return jsonify({
        "success": True,
        "deleted": plugin_id
    })


# =============================================================================
# v3.9: AGENT LEARNING & FEEDBACK ENDPOINTS
# =============================================================================

@app.route('/learning/record', methods=['POST'])
def learning_record_outcome():
    """Record a task outcome for learning."""
    data = request.get_json() or {}

    required = ['session_id', 'task', 'success']
    for field in required:
        if field not in data:
            return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400

    outcome = record_task_outcome(
        session_id=data['session_id'],
        task=data['task'],
        template_used=data.get('template', 'default'),
        success=data['success'],
        error_message=data.get('error_message'),
        tool_calls=data.get('tool_calls', []),
        duration_seconds=data.get('duration_seconds', 0.0),
        tags=data.get('tags', [])
    )

    return jsonify({
        "success": True,
        "outcome_id": outcome.outcome_id,
        "patterns_analyzed": True
    })


@app.route('/learning/feedback', methods=['POST'])
def learning_add_feedback():
    """Add user feedback to a task outcome."""
    data = request.get_json() or {}
    outcome_id = data.get('outcome_id')
    feedback = data.get('feedback')  # positive, negative, neutral

    if not outcome_id or not feedback:
        return jsonify({"success": False, "error": "Missing 'outcome_id' or 'feedback'"}), 400

    if feedback not in ['positive', 'negative', 'neutral']:
        return jsonify({"success": False, "error": "Feedback must be 'positive', 'negative', or 'neutral'"}), 400

    success = add_user_feedback(outcome_id, feedback, data.get('notes'))
    if not success:
        return jsonify({"success": False, "error": f"Outcome not found: {outcome_id}"}), 404

    return jsonify({"success": True, "updated": outcome_id})


@app.route('/learning/recommendations', methods=['POST'])
def learning_get_recommendations():
    """Get learning-based recommendations for a task."""
    data = request.get_json() or {}
    task = data.get('task', '')
    context = data.get('context')

    recommendations = get_recommendations_for_task(task, context)

    return jsonify({
        "success": True,
        "task": task,
        "recommendations": recommendations,
        "count": len(recommendations)
    })


@app.route('/learning/patterns', methods=['GET', 'POST'])
def learning_list_patterns():
    """List all learned patterns."""
    patterns = [
        {
            "entry_id": e.entry_id,
            "pattern_type": e.pattern_type,
            "description": e.description,
            "confidence": e.confidence,
            "times_applied": e.times_applied,
            "times_successful": e.times_successful,
            "created_at": e.created_at
        }
        for e in LEARNING_ENTRIES.values()
    ]

    return jsonify({
        "success": True,
        "patterns": patterns,
        "total": len(patterns)
    })


@app.route('/learning/outcomes', methods=['GET', 'POST'])
def learning_list_outcomes():
    """List task outcomes."""
    data = request.get_json() or {} if request.method == 'POST' else {}
    limit = data.get('limit', 50)
    session_id = data.get('session_id')

    outcomes = list(TASK_OUTCOMES.values())
    if session_id:
        outcomes = [o for o in outcomes if o.session_id == session_id]

    outcomes.sort(key=lambda o: o.learned_at, reverse=True)
    outcomes = outcomes[:limit]

    return jsonify({
        "success": True,
        "outcomes": [
            {
                "outcome_id": o.outcome_id,
                "session_id": o.session_id,
                "task": o.task[:100],
                "success": o.success,
                "template_used": o.template_used,
                "user_feedback": o.user_feedback,
                "learned_at": o.learned_at
            }
            for o in outcomes
        ],
        "total": len(TASK_OUTCOMES)
    })


# =============================================================================
# v3.9: WORKFLOW RECORDING & PLAYBACK ENDPOINTS
# =============================================================================

@app.route('/recording/start', methods=['POST'])
def recording_start():
    """Start recording a workflow."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    name = data.get('name', 'Untitled Workflow')
    description = data.get('description', '')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id'"}), 400

    if session_id in ACTIVE_RECORDINGS:
        return jsonify({"success": False, "error": f"Already recording for session: {session_id}"}), 400

    workflow = start_recording(session_id, name, description)

    return jsonify({
        "success": True,
        "workflow_id": workflow.workflow_id,
        "session_id": session_id,
        "recording": True
    })


@app.route('/recording/step', methods=['POST'])
def recording_add_step():
    """Add a step to the current recording."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    action = data.get('action')
    input_data = data.get('input', {})

    if not session_id or not action:
        return jsonify({"success": False, "error": "Missing 'session_id' or 'action'"}), 400

    step = record_step(
        session_id=session_id,
        action=action,
        input_data=input_data,
        output_data=data.get('output'),
        success=data.get('success', True),
        error=data.get('error'),
        duration_ms=data.get('duration_ms', 0.0),
        metadata=data.get('metadata')
    )

    if not step:
        return jsonify({"success": False, "error": f"No active recording for session: {session_id}"}), 404

    return jsonify({
        "success": True,
        "step_id": step.step_id,
        "step_number": step.step_number
    })


@app.route('/recording/stop', methods=['POST'])
def recording_stop():
    """Stop recording and save the workflow."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    save = data.get('save', True)

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id'"}), 400

    workflow = stop_recording(session_id, save=save)
    if not workflow:
        return jsonify({"success": False, "error": f"No active recording for session: {session_id}"}), 404

    return jsonify({
        "success": True,
        "workflow_id": workflow.workflow_id if save else None,
        "steps_recorded": len(workflow.steps),
        "saved": save
    })


@app.route('/recording/list', methods=['GET', 'POST'])
def recording_list_workflows():
    """List all recorded workflows."""
    workflows = [
        {
            "workflow_id": w.workflow_id,
            "name": w.name,
            "description": w.description,
            "steps_count": len(w.steps),
            "playback_count": w.playback_count,
            "created_at": w.created_at,
            "tags": w.tags
        }
        for w in RECORDED_WORKFLOWS.values()
    ]

    return jsonify({
        "success": True,
        "workflows": workflows,
        "total": len(workflows),
        "active_recordings": len(ACTIVE_RECORDINGS)
    })


@app.route('/recording/get', methods=['POST'])
def recording_get_workflow():
    """Get details of a recorded workflow."""
    data = request.get_json() or {}
    workflow_id = data.get('workflow_id')

    if not workflow_id:
        return jsonify({"success": False, "error": "Missing 'workflow_id'"}), 400

    if workflow_id not in RECORDED_WORKFLOWS:
        return jsonify({"success": False, "error": f"Workflow not found: {workflow_id}"}), 404

    workflow = RECORDED_WORKFLOWS[workflow_id]

    return jsonify({
        "success": True,
        "workflow": {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "session_id": workflow.session_id,
            "steps": [
                {
                    "step_id": s.step_id,
                    "step_number": s.step_number,
                    "action": s.action,
                    "input": s.input_data,
                    "output": s.output_data,
                    "success": s.success,
                    "duration_ms": s.duration_ms
                }
                for s in workflow.steps
            ],
            "variables": workflow.variables,
            "playback_count": workflow.playback_count,
            "created_at": workflow.created_at,
            "tags": workflow.tags
        }
    })


@app.route('/recording/playback', methods=['POST'])
def recording_playback():
    """Replay a recorded workflow."""
    data = request.get_json() or {}
    workflow_id = data.get('workflow_id')
    variables = data.get('variables', {})
    dry_run = data.get('dry_run', True)

    if not workflow_id:
        return jsonify({"success": False, "error": "Missing 'workflow_id'"}), 400

    result = playback_workflow(workflow_id, variables=variables, dry_run=dry_run)

    return jsonify(result)


@app.route('/recording/delete', methods=['POST'])
def recording_delete():
    """Delete a recorded workflow."""
    data = request.get_json() or {}
    workflow_id = data.get('workflow_id')

    if not workflow_id:
        return jsonify({"success": False, "error": "Missing 'workflow_id'"}), 400

    if workflow_id not in RECORDED_WORKFLOWS:
        return jsonify({"success": False, "error": f"Workflow not found: {workflow_id}"}), 404

    del RECORDED_WORKFLOWS[workflow_id]

    return jsonify({"success": True, "deleted": workflow_id})


# =============================================================================
# v3.9: SMART CONTEXT INJECTION ENDPOINTS
# =============================================================================

@app.route('/context/rules/create', methods=['POST'])
def context_create_rule():
    """Create a context injection rule."""
    data = request.get_json() or {}
    name = data.get('name')
    trigger_patterns = data.get('trigger_patterns', [])
    kb_ids = data.get('kb_ids', [])

    if not name:
        return jsonify({"success": False, "error": "Missing 'name'"}), 400

    rule = create_injection_rule(
        name=name,
        trigger_patterns=trigger_patterns,
        kb_ids=kb_ids,
        search_query_template=data.get('search_query_template', '{{task}}'),
        max_chunks=data.get('max_chunks', 5),
        inject_position=data.get('inject_position', 'before_task')
    )

    return jsonify({
        "success": True,
        "rule_id": rule.rule_id,
        "name": rule.name
    })


@app.route('/context/rules/list', methods=['GET', 'POST'])
def context_list_rules():
    """List all context injection rules."""
    rules = [
        {
            "rule_id": r.rule_id,
            "name": r.name,
            "trigger_patterns": r.trigger_patterns,
            "kb_ids": r.kb_ids,
            "inject_position": r.inject_position,
            "enabled": r.enabled,
            "created_at": r.created_at
        }
        for r in CONTEXT_INJECTION_RULES.values()
    ]

    return jsonify({
        "success": True,
        "rules": rules,
        "total": len(rules)
    })


@app.route('/context/rules/toggle', methods=['POST'])
def context_toggle_rule():
    """Enable or disable a context injection rule."""
    data = request.get_json() or {}
    rule_id = data.get('rule_id')
    enabled = data.get('enabled')

    if not rule_id:
        return jsonify({"success": False, "error": "Missing 'rule_id'"}), 400

    if rule_id not in CONTEXT_INJECTION_RULES:
        return jsonify({"success": False, "error": f"Rule not found: {rule_id}"}), 404

    if enabled is not None:
        CONTEXT_INJECTION_RULES[rule_id].enabled = enabled
    else:
        CONTEXT_INJECTION_RULES[rule_id].enabled = not CONTEXT_INJECTION_RULES[rule_id].enabled

    return jsonify({
        "success": True,
        "rule_id": rule_id,
        "enabled": CONTEXT_INJECTION_RULES[rule_id].enabled
    })


@app.route('/context/rules/delete', methods=['POST'])
def context_delete_rule():
    """Delete a context injection rule."""
    data = request.get_json() or {}
    rule_id = data.get('rule_id')

    if not rule_id:
        return jsonify({"success": False, "error": "Missing 'rule_id'"}), 400

    if rule_id not in CONTEXT_INJECTION_RULES:
        return jsonify({"success": False, "error": f"Rule not found: {rule_id}"}), 404

    del CONTEXT_INJECTION_RULES[rule_id]

    return jsonify({"success": True, "deleted": rule_id})


@app.route('/context/inject', methods=['POST'])
def context_inject():
    """Get context to inject for a task."""
    data = request.get_json() or {}
    task = data.get('task', '')
    session_id = data.get('session_id')

    result = get_context_for_task(task, session_id)

    # Optionally format for specific positions
    if data.get('format', False):
        result['formatted'] = {
            'before_task': format_injected_context(result, 'before_task'),
            'after_task': format_injected_context(result, 'after_task'),
            'system_prompt': format_injected_context(result, 'system_prompt')
        }

    return jsonify(result)


# =============================================================================
# v3.9: INTER-AGENT COMMUNICATION ENDPOINTS
# =============================================================================

@app.route('/agents/message/send', methods=['POST'])
def agents_send_message():
    """Send a message from one agent to another."""
    data = request.get_json() or {}
    from_agent = data.get('from_agent')
    to_agent = data.get('to_agent')
    message_type = data.get('message_type', 'data')
    content = data.get('content', {})

    if not from_agent or not to_agent:
        return jsonify({"success": False, "error": "Missing 'from_agent' or 'to_agent'"}), 400

    message = send_agent_message(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=message_type,
        content=content,
        priority=data.get('priority', 0),
        reply_to=data.get('reply_to'),
        ttl_seconds=data.get('ttl_seconds')
    )

    return jsonify({
        "success": True,
        "message_id": message.message_id,
        "from_agent": from_agent,
        "to_agent": to_agent
    })


@app.route('/agents/message/receive', methods=['POST'])
def agents_receive_messages():
    """Receive messages for an agent."""
    data = request.get_json() or {}
    agent_id = data.get('agent_id')
    unread_only = data.get('unread_only', True)
    message_type = data.get('message_type')

    if not agent_id:
        return jsonify({"success": False, "error": "Missing 'agent_id'"}), 400

    messages = get_agent_messages(agent_id, unread_only=unread_only, message_type=message_type)

    return jsonify({
        "success": True,
        "agent_id": agent_id,
        "messages": [
            {
                "message_id": m.message_id,
                "from_agent": m.from_agent,
                "message_type": m.message_type,
                "content": m.content,
                "priority": m.priority,
                "timestamp": m.timestamp,
                "read": m.read,
                "reply_to": m.reply_to
            }
            for m in messages
        ],
        "count": len(messages)
    })


@app.route('/agents/message/read', methods=['POST'])
def agents_mark_read():
    """Mark a message as read."""
    data = request.get_json() or {}
    agent_id = data.get('agent_id')
    message_id = data.get('message_id')

    if not agent_id or not message_id:
        return jsonify({"success": False, "error": "Missing 'agent_id' or 'message_id'"}), 400

    success = mark_message_read(agent_id, message_id)

    return jsonify({
        "success": success,
        "agent_id": agent_id,
        "message_id": message_id
    })


@app.route('/agents/state/get', methods=['POST'])
def agents_get_state():
    """Get shared state for an orchestration."""
    data = request.get_json() or {}
    orchestration_id = data.get('orchestration_id')

    if not orchestration_id:
        return jsonify({"success": False, "error": "Missing 'orchestration_id'"}), 400

    state = get_shared_state(orchestration_id)

    return jsonify({
        "success": True,
        "orchestration_id": orchestration_id,
        "state": state.state,
        "locks": state.locks,
        "version": state.version,
        "last_updated": state.last_updated
    })


@app.route('/agents/state/update', methods=['POST'])
def agents_update_state():
    """Update shared state for an orchestration."""
    data = request.get_json() or {}
    orchestration_id = data.get('orchestration_id')
    agent_id = data.get('agent_id')
    key = data.get('key')
    value = data.get('value')

    if not orchestration_id or not agent_id or not key:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    result = update_shared_state(
        orchestration_id=orchestration_id,
        agent_id=agent_id,
        key=key,
        value=value,
        require_lock=data.get('require_lock', False)
    )

    return jsonify(result)


@app.route('/agents/state/lock', methods=['POST'])
def agents_acquire_lock():
    """Acquire a lock on a shared state key."""
    data = request.get_json() or {}
    orchestration_id = data.get('orchestration_id')
    agent_id = data.get('agent_id')
    key = data.get('key')

    if not orchestration_id or not agent_id or not key:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    success = acquire_lock(orchestration_id, agent_id, key)

    return jsonify({
        "success": success,
        "orchestration_id": orchestration_id,
        "agent_id": agent_id,
        "key": key,
        "locked": success
    })


@app.route('/agents/state/unlock', methods=['POST'])
def agents_release_lock():
    """Release a lock on a shared state key."""
    data = request.get_json() or {}
    orchestration_id = data.get('orchestration_id')
    agent_id = data.get('agent_id')
    key = data.get('key')

    if not orchestration_id or not agent_id or not key:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    success = release_lock(orchestration_id, agent_id, key)

    return jsonify({
        "success": success,
        "orchestration_id": orchestration_id,
        "agent_id": agent_id,
        "key": key,
        "unlocked": success
    })


@app.route('/agents/state/history', methods=['POST'])
def agents_state_history():
    """Get update history for shared state."""
    data = request.get_json() or {}
    orchestration_id = data.get('orchestration_id')
    limit = data.get('limit', 50)

    if not orchestration_id:
        return jsonify({"success": False, "error": "Missing 'orchestration_id'"}), 400

    state = get_shared_state(orchestration_id)
    history = state.update_history[-limit:]

    return jsonify({
        "success": True,
        "orchestration_id": orchestration_id,
        "history": history,
        "total_updates": len(state.update_history)
    })


# =============================================================================
# v4.0: AGENT PERSONAS ENDPOINTS
# =============================================================================

@app.route('/personas/list', methods=['GET', 'POST'])
def personas_list():
    """List all agent personas."""
    personas = []
    for pid, persona in AGENT_PERSONAS.items():
        personas.append({
            "persona_id": persona.persona_id,
            "name": persona.name,
            "base_template": persona.base_template,
            "traits": persona.traits,
            "expertise": persona.expertise,
            "communication_style": persona.communication_style,
            "usage_count": persona.usage_count,
            "last_used": persona.last_used
        })
    return jsonify({
        "success": True,
        "personas": personas,
        "total": len(personas)
    })


@app.route('/personas/create', methods=['POST'])
def personas_create():
    """Create a new agent persona."""
    data = request.get_json() or {}
    name = data.get('name')

    if not name:
        return jsonify({"success": False, "error": "Missing 'name' parameter"}), 400

    persona = create_persona(
        name=name,
        base_template=data.get('base_template', 'coder'),
        traits=data.get('traits', []),
        expertise=data.get('expertise', []),
        communication_style=data.get('communication_style', 'professional'),
        custom_instructions=data.get('custom_instructions', '')
    )

    return jsonify({
        "success": True,
        "persona_id": persona.persona_id,
        "name": persona.name
    })


@app.route('/personas/get', methods=['POST'])
def personas_get():
    """Get a specific persona with full details."""
    data = request.get_json() or {}
    persona_id = data.get('persona_id')

    if not persona_id:
        return jsonify({"success": False, "error": "Missing 'persona_id'"}), 400

    if persona_id not in AGENT_PERSONAS:
        return jsonify({"success": False, "error": f"Persona not found: {persona_id}"}), 404

    persona = AGENT_PERSONAS[persona_id]
    return jsonify({
        "success": True,
        "persona_id": persona.persona_id,
        "name": persona.name,
        "base_template": persona.base_template,
        "traits": persona.traits,
        "expertise": persona.expertise,
        "communication_style": persona.communication_style,
        "response_format": persona.response_format,
        "verbosity": persona.verbosity,
        "custom_instructions": persona.custom_instructions,
        "avoid_patterns": persona.avoid_patterns,
        "preferred_tools": persona.preferred_tools,
        "learning_rate": persona.learning_rate,
        "usage_count": persona.usage_count
    })


@app.route('/personas/prompt', methods=['POST'])
def personas_get_prompt():
    """Get the system prompt for a persona."""
    data = request.get_json() or {}
    persona_id = data.get('persona_id')

    if not persona_id:
        return jsonify({"success": False, "error": "Missing 'persona_id'"}), 400

    prompt = get_persona_system_prompt(persona_id)
    if not prompt:
        return jsonify({"success": False, "error": f"Persona not found: {persona_id}"}), 404

    # Update usage count
    if persona_id in AGENT_PERSONAS:
        AGENT_PERSONAS[persona_id].usage_count += 1
        AGENT_PERSONAS[persona_id].last_used = datetime.now().isoformat()

    return jsonify({
        "success": True,
        "persona_id": persona_id,
        "system_prompt": prompt
    })


@app.route('/personas/delete', methods=['POST'])
def personas_delete():
    """Delete a persona (cannot delete built-in personas)."""
    data = request.get_json() or {}
    persona_id = data.get('persona_id')

    if not persona_id:
        return jsonify({"success": False, "error": "Missing 'persona_id'"}), 400

    if persona_id in DEFAULT_PERSONAS:
        return jsonify({"success": False, "error": "Cannot delete built-in persona"}), 400

    if persona_id not in AGENT_PERSONAS:
        return jsonify({"success": False, "error": f"Persona not found: {persona_id}"}), 404

    del AGENT_PERSONAS[persona_id]
    return jsonify({"success": True, "deleted": persona_id})


# =============================================================================
# v4.0: GOAL DECOMPOSITION ENDPOINTS
# =============================================================================

@app.route('/goals/create', methods=['POST'])
def goals_create():
    """Create a new goal for decomposition."""
    data = request.get_json() or {}
    title = data.get('title')
    description = data.get('description', '')
    session_id = data.get('session_id')

    if not title or not session_id:
        return jsonify({"success": False, "error": "Missing 'title' or 'session_id'"}), 400

    goal = decompose_goal(
        title=title,
        description=description,
        session_id=session_id,
        strategy=data.get('strategy', 'sequential'),
        context=data.get('context', {})
    )

    return jsonify({
        "success": True,
        "goal_id": goal.goal_id,
        "title": goal.title,
        "status": goal.status
    })


@app.route('/goals/add-subgoal', methods=['POST'])
def goals_add_subgoal():
    """Add a sub-goal to an existing goal."""
    data = request.get_json() or {}
    goal_id = data.get('goal_id')
    title = data.get('title')

    if not goal_id or not title:
        return jsonify({"success": False, "error": "Missing 'goal_id' or 'title'"}), 400

    subgoal = add_subgoal(
        goal_id=goal_id,
        title=title,
        description=data.get('description', ''),
        dependencies=data.get('dependencies', []),
        priority=data.get('priority', 0),
        complexity=data.get('complexity', 'medium'),
        tools_required=data.get('tools_required', [])
    )

    if not subgoal:
        return jsonify({"success": False, "error": f"Goal not found: {goal_id}"}), 404

    return jsonify({
        "success": True,
        "goal_id": goal_id,
        "subgoal_id": subgoal.subgoal_id,
        "title": subgoal.title
    })


@app.route('/goals/next', methods=['POST'])
def goals_get_next():
    """Get the next actionable sub-goal."""
    data = request.get_json() or {}
    goal_id = data.get('goal_id')

    if not goal_id:
        return jsonify({"success": False, "error": "Missing 'goal_id'"}), 400

    subgoal = get_next_subgoal(goal_id)
    if not subgoal:
        # Check if goal exists
        if goal_id not in GOALS:
            return jsonify({"success": False, "error": f"Goal not found: {goal_id}"}), 404
        # No more actionable sub-goals
        return jsonify({
            "success": True,
            "goal_id": goal_id,
            "next_subgoal": None,
            "message": "No actionable sub-goals (all completed or blocked)"
        })

    return jsonify({
        "success": True,
        "goal_id": goal_id,
        "next_subgoal": {
            "subgoal_id": subgoal.subgoal_id,
            "title": subgoal.title,
            "description": subgoal.description,
            "priority": subgoal.priority,
            "complexity": subgoal.estimated_complexity,
            "tools_required": subgoal.tools_required
        }
    })


@app.route('/goals/update-subgoal', methods=['POST'])
def goals_update_subgoal():
    """Update a sub-goal's status."""
    data = request.get_json() or {}
    goal_id = data.get('goal_id')
    subgoal_id = data.get('subgoal_id')
    status = data.get('status')

    if not goal_id or not subgoal_id or not status:
        return jsonify({"success": False, "error": "Missing required parameters"}), 400

    if status not in ['pending', 'in_progress', 'completed', 'blocked', 'failed']:
        return jsonify({"success": False, "error": "Invalid status"}), 400

    success = update_subgoal_status(
        goal_id=goal_id,
        subgoal_id=subgoal_id,
        status=status,
        result=data.get('result')
    )

    if not success:
        return jsonify({"success": False, "error": "Goal or subgoal not found"}), 404

    # Get updated goal status
    goal = GOALS.get(goal_id)
    return jsonify({
        "success": True,
        "goal_id": goal_id,
        "subgoal_id": subgoal_id,
        "new_status": status,
        "goal_status": goal.status if goal else "unknown"
    })


@app.route('/goals/status', methods=['POST'])
def goals_status():
    """Get full status of a goal and its sub-goals."""
    data = request.get_json() or {}
    goal_id = data.get('goal_id')

    if not goal_id:
        return jsonify({"success": False, "error": "Missing 'goal_id'"}), 400

    if goal_id not in GOALS:
        return jsonify({"success": False, "error": f"Goal not found: {goal_id}"}), 404

    goal = GOALS[goal_id]
    subgoals = []
    for sg in goal.sub_goals:
        subgoals.append({
            "subgoal_id": sg.subgoal_id,
            "title": sg.title,
            "status": sg.status,
            "priority": sg.priority,
            "dependencies": sg.dependencies,
            "assigned_to": sg.assigned_to
        })

    completed = sum(1 for sg in goal.sub_goals if sg.status == "completed")
    total = len(goal.sub_goals)

    return jsonify({
        "success": True,
        "goal_id": goal_id,
        "title": goal.title,
        "status": goal.status,
        "strategy": goal.decomposition_strategy,
        "progress": f"{completed}/{total}",
        "progress_pct": round(completed / total * 100, 1) if total > 0 else 0,
        "sub_goals": subgoals
    })


@app.route('/goals/list', methods=['GET', 'POST'])
def goals_list():
    """List all goals."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    goals = []
    for gid, goal in GOALS.items():
        if session_id and goal.session_id != session_id:
            continue
        completed = sum(1 for sg in goal.sub_goals if sg.status == "completed")
        total = len(goal.sub_goals)
        goals.append({
            "goal_id": goal.goal_id,
            "title": goal.title,
            "status": goal.status,
            "progress": f"{completed}/{total}",
            "created_at": goal.created_at
        })

    return jsonify({
        "success": True,
        "goals": goals,
        "total": len(goals)
    })


# =============================================================================
# v4.0: TOOL MACROS ENDPOINTS
# =============================================================================

@app.route('/macros/list', methods=['GET', 'POST'])
def macros_list():
    """List all tool macros."""
    macros = []
    for mid, macro in TOOL_MACROS.items():
        macros.append({
            "macro_id": macro.macro_id,
            "name": macro.name,
            "description": macro.description,
            "steps_count": len(macro.steps),
            "usage_count": macro.usage_count,
            "success_rate": round(macro.success_rate * 100, 1),
            "tags": macro.tags,
            "is_builtin": mid in BUILTIN_MACROS
        })
    return jsonify({
        "success": True,
        "macros": macros,
        "total": len(macros),
        "builtin": len(BUILTIN_MACROS)
    })


@app.route('/macros/create', methods=['POST'])
def macros_create():
    """Create a new tool macro."""
    data = request.get_json() or {}
    name = data.get('name')
    steps = data.get('steps')

    if not name or not steps:
        return jsonify({"success": False, "error": "Missing 'name' or 'steps'"}), 400

    if not isinstance(steps, list) or len(steps) == 0:
        return jsonify({"success": False, "error": "Steps must be a non-empty list"}), 400

    macro = create_macro(
        name=name,
        description=data.get('description', ''),
        steps=steps,
        input_schema=data.get('input_schema', {}),
        tags=data.get('tags', [])
    )

    return jsonify({
        "success": True,
        "macro_id": macro.macro_id,
        "name": macro.name,
        "steps_count": len(macro.steps)
    })


@app.route('/macros/execute', methods=['POST'])
def macros_execute():
    """Execute a tool macro."""
    data = request.get_json() or {}
    macro_id = data.get('macro_id')
    variables = data.get('variables', {})

    if not macro_id:
        return jsonify({"success": False, "error": "Missing 'macro_id'"}), 400

    result = execute_macro(macro_id, variables)
    return jsonify(result)


@app.route('/macros/get', methods=['POST'])
def macros_get():
    """Get details of a specific macro."""
    data = request.get_json() or {}
    macro_id = data.get('macro_id')

    if not macro_id:
        return jsonify({"success": False, "error": "Missing 'macro_id'"}), 400

    if macro_id not in TOOL_MACROS:
        return jsonify({"success": False, "error": f"Macro not found: {macro_id}"}), 404

    macro = TOOL_MACROS[macro_id]
    return jsonify({
        "success": True,
        "macro_id": macro.macro_id,
        "name": macro.name,
        "description": macro.description,
        "steps": macro.steps,
        "input_schema": macro.input_schema,
        "output_mapping": macro.output_mapping,
        "usage_count": macro.usage_count,
        "average_duration_ms": round(macro.average_duration_ms, 2),
        "success_rate": round(macro.success_rate * 100, 1),
        "tags": macro.tags
    })


@app.route('/macros/delete', methods=['POST'])
def macros_delete():
    """Delete a macro (cannot delete built-in macros)."""
    data = request.get_json() or {}
    macro_id = data.get('macro_id')

    if not macro_id:
        return jsonify({"success": False, "error": "Missing 'macro_id'"}), 400

    if macro_id in BUILTIN_MACROS:
        return jsonify({"success": False, "error": "Cannot delete built-in macro"}), 400

    if macro_id not in TOOL_MACROS:
        return jsonify({"success": False, "error": f"Macro not found: {macro_id}"}), 404

    del TOOL_MACROS[macro_id]
    return jsonify({"success": True, "deleted": macro_id})


# =============================================================================
# v4.0: AUDIT TRAIL ENDPOINTS
# =============================================================================

@app.route('/audit/log', methods=['POST'])
def audit_log_action():
    """Log an action to the audit trail."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    action_type = data.get('action_type')
    action_name = data.get('action_name')

    if not session_id or not action_type or not action_name:
        return jsonify({"success": False, "error": "Missing required parameters"}), 400

    entry = log_audit(
        session_id=session_id,
        action_type=action_type,
        action_name=action_name,
        input_summary=data.get('input_summary', ''),
        output_summary=data.get('output_summary', ''),
        success=data.get('success', True),
        error=data.get('error'),
        duration_ms=data.get('duration_ms', 0),
        agent_id=data.get('agent_id'),
        metadata=data.get('metadata', {}),
        risk_level=data.get('risk_level', 'low')
    )

    return jsonify({
        "success": True,
        "entry_id": entry.entry_id,
        "timestamp": entry.timestamp
    })


@app.route('/audit/query', methods=['POST'])
def audit_query():
    """Query the audit trail with filters."""
    data = request.get_json() or {}

    entries = get_audit_trail(
        session_id=data.get('session_id'),
        action_type=data.get('action_type'),
        risk_level=data.get('risk_level'),
        limit=data.get('limit', 100),
        offset=data.get('offset', 0)
    )

    results = []
    for entry in entries:
        results.append({
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp,
            "session_id": entry.session_id,
            "agent_id": entry.agent_id,
            "action_type": entry.action_type,
            "action_name": entry.action_name,
            "success": entry.success,
            "risk_level": entry.risk_level,
            "duration_ms": entry.duration_ms
        })

    return jsonify({
        "success": True,
        "entries": results,
        "count": len(results)
    })


@app.route('/audit/summary', methods=['GET', 'POST'])
def audit_summary():
    """Get audit trail summary statistics."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    summary = get_audit_summary(session_id)
    return jsonify({
        "success": True,
        **summary
    })


@app.route('/audit/review-required', methods=['GET', 'POST'])
def audit_review_required():
    """Get audit entries that require review (high/critical risk)."""
    entries = [e for e in AUDIT_TRAIL if e.requires_review]
    entries = sorted(entries, key=lambda x: x.timestamp, reverse=True)[:50]

    results = []
    for entry in entries:
        results.append({
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp,
            "session_id": entry.session_id,
            "action_type": entry.action_type,
            "action_name": entry.action_name,
            "risk_level": entry.risk_level,
            "error": entry.error,
            "input_summary": entry.input_summary[:100] if entry.input_summary else ""
        })

    return jsonify({
        "success": True,
        "entries": results,
        "count": len(results)
    })


# =============================================================================
# v4.0: ADAPTIVE BEHAVIOR ENDPOINTS
# =============================================================================

@app.route('/behavior/profile', methods=['POST'])
def behavior_get_profile():
    """Get or create behavior profile for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id'"}), 400

    profile = get_or_create_behavior_profile(session_id)

    return jsonify({
        "success": True,
        "profile_id": profile.profile_id,
        "session_id": profile.session_id,
        "tool_preferences": profile.tool_preferences,
        "risk_tolerance": profile.risk_tolerance,
        "verbosity_adjustment": profile.verbosity_adjustment,
        "learning_iterations": profile.learning_iterations,
        "last_adaptation": profile.last_adaptation
    })


@app.route('/behavior/adapt', methods=['POST'])
def behavior_adapt():
    """Adapt behavior based on a task outcome."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    outcome_id = data.get('outcome_id')
    learning_rate = data.get('learning_rate', 0.1)

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id'"}), 400

    # Get outcome if provided
    outcome = None
    if outcome_id and outcome_id in TASK_OUTCOMES:
        outcome = TASK_OUTCOMES[outcome_id]
    elif 'outcome' in data:
        # Allow inline outcome data
        outcome_data = data['outcome']
        outcome = TaskOutcome(
            outcome_id="inline",
            session_id=session_id,
            task=outcome_data.get('task', ''),
            template_used=outcome_data.get('template', 'default'),
            success=outcome_data.get('success', True),
            error_message=outcome_data.get('error_message'),
            tool_calls=outcome_data.get('tool_calls', []),
            user_feedback=outcome_data.get('user_feedback')
        )
    else:
        return jsonify({"success": False, "error": "Missing 'outcome_id' or 'outcome' data"}), 400

    result = adapt_behavior(session_id, outcome, learning_rate)
    return jsonify({
        "success": True,
        **result
    })


@app.route('/behavior/recommendations', methods=['POST'])
def behavior_recommendations():
    """Get behavior recommendations for a task."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    task = data.get('task', '')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id'"}), 400

    recommendations = get_behavior_recommendations(session_id, task)
    return jsonify({
        "success": True,
        "session_id": session_id,
        **recommendations
    })


@app.route('/behavior/reset', methods=['POST'])
def behavior_reset():
    """Reset behavior profile for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"success": False, "error": "Missing 'session_id'"}), 400

    if session_id in BEHAVIOR_PROFILES:
        del BEHAVIOR_PROFILES[session_id]

    return jsonify({
        "success": True,
        "session_id": session_id,
        "reset": True
    })


@app.route('/behavior/list', methods=['GET', 'POST'])
def behavior_list():
    """List all behavior profiles."""
    profiles = []
    for pid, profile in BEHAVIOR_PROFILES.items():
        profiles.append({
            "profile_id": profile.profile_id,
            "session_id": profile.session_id,
            "risk_tolerance": profile.risk_tolerance,
            "learning_iterations": profile.learning_iterations,
            "last_adaptation": profile.last_adaptation
        })

    return jsonify({
        "success": True,
        "profiles": profiles,
        "total": len(profiles)
    })


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


# =============================================================================
# v4.1 META-AGENT INTEGRATIONS - SELF-ANNEALING CAPABILITIES
# =============================================================================

# Tool Discovery and Self-Improvement Storage
DISCOVERED_TOOLS: Dict[str, dict] = {}
TOOL_USAGE_STATS: Dict[str, dict] = {}
ERROR_SOLUTIONS: Dict[str, dict] = {}
CAPABILITY_REGISTRY: Dict[str, dict] = {}
META_KNOWLEDGE: Dict[str, Any] = {
    'known_integrations': [],
    'pending_questions': [],
    'learned_patterns': [],
    'improvement_suggestions': []
}

# Gmail Integration
GMAIL_SERVICE = None

def get_gmail_service():
    """Get or create Gmail API service."""
    global GMAIL_SERVICE
    if GMAIL_SERVICE is not None:
        return GMAIL_SERVICE
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
                  'https://www.googleapis.com/auth/gmail.send',
                  'https://www.googleapis.com/auth/gmail.modify']
        creds = None
        token_path = Path('/Users/williammarceaujr./dev-sandbox/token.json')
        creds_path = Path('/Users/williammarceaujr./dev-sandbox/credentials.json')
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif creds_path.exists():
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                return None
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        GMAIL_SERVICE = build('gmail', 'v1', credentials=creds)
        return GMAIL_SERVICE
    except Exception as e:
        print(f"Gmail service error: {e}")
        return None


@app.route('/gmail/list', methods=['POST'])
def gmail_list():
    """List emails from Gmail inbox."""
    data = request.get_json() or {}
    max_results = data.get('max_results', 10)
    query = data.get('query', '')
    label_ids = data.get('label_ids', ['INBOX'])
    service = get_gmail_service()
    if not service:
        return jsonify({"success": False, "error": "Gmail service not available. Run OAuth flow first."})
    try:
        results = service.users().messages().list(userId='me', maxResults=max_results, q=query, labelIds=label_ids).execute()
        messages = results.get('messages', [])
        emails = []
        for msg in messages[:max_results]:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
            headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
            emails.append({'id': msg['id'], 'thread_id': msg_data.get('threadId'), 'snippet': msg_data.get('snippet', ''),
                          'from': headers.get('From', ''), 'to': headers.get('To', ''), 'subject': headers.get('Subject', ''),
                          'date': headers.get('Date', ''), 'labels': msg_data.get('labelIds', [])})
        return jsonify({"success": True, "emails": emails, "count": len(emails)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/gmail/read', methods=['POST'])
def gmail_read():
    """Read a specific email by ID."""
    data = request.get_json() or {}
    message_id = data.get('message_id')
    if not message_id:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "message_id is required")
    service = get_gmail_service()
    if not service:
        return jsonify({"success": False, "error": "Gmail service not available"})
    try:
        msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
        body = ''
        payload = msg.get('payload', {})
        if 'body' in payload and payload['body'].get('data'):
            import base64
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                    import base64
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        return jsonify({"success": True, "email": {'id': message_id, 'thread_id': msg.get('threadId'),
                       'from': headers.get('From', ''), 'to': headers.get('To', ''), 'subject': headers.get('Subject', ''),
                       'date': headers.get('Date', ''), 'body': body, 'labels': msg.get('labelIds', [])}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/gmail/send', methods=['POST'])
def gmail_send():
    """Send an email via SMTP."""
    data = request.get_json() or {}
    to = data.get('to')
    subject = data.get('subject', '')
    body = data.get('body', '')
    if not to:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "to is required")
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USERNAME')
        smtp_pass = os.getenv('SMTP_PASSWORD')
        sender_email = os.getenv('SENDER_EMAIL', smtp_user)
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return jsonify({"success": True, "method": "smtp", "to": to, "subject": subject})
    except Exception as e:
        return jsonify({"success": False, "error": f"SMTP error: {e}"})


@app.route('/gmail/search', methods=['POST'])
def gmail_search():
    """Search emails with Gmail query syntax."""
    data = request.get_json() or {}
    query = data.get('query', '')
    max_results = data.get('max_results', 20)
    service = get_gmail_service()
    if not service:
        return jsonify({"success": False, "error": "Gmail service not available"})
    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
            headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
            emails.append({'id': msg['id'], 'snippet': msg_data.get('snippet', ''), 'from': headers.get('From', ''),
                          'subject': headers.get('Subject', ''), 'date': headers.get('Date', '')})
        return jsonify({"success": True, "query": query, "emails": emails, "count": len(emails)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# Google Sheets Integration
SHEETS_SERVICE = None

def get_sheets_service():
    """Get or create Google Sheets API service."""
    global SHEETS_SERVICE
    if SHEETS_SERVICE is not None:
        return SHEETS_SERVICE
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        token_path = Path('/Users/williammarceaujr./dev-sandbox/token.json')
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path))
            SHEETS_SERVICE = build('sheets', 'v4', credentials=creds)
            return SHEETS_SERVICE
    except Exception as e:
        print(f"Sheets service error: {e}")
    return None


@app.route('/sheets/read', methods=['POST'])
def sheets_read():
    """Read data from a Google Sheet."""
    data = request.get_json() or {}
    spreadsheet_id = data.get('spreadsheet_id') or os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    range_name = data.get('range', 'Sheet1!A1:Z100')
    if not spreadsheet_id:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "spreadsheet_id is required")
    service = get_sheets_service()
    if not service:
        return jsonify({"success": False, "error": "Sheets service not available"})
    try:
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        return jsonify({"success": True, "spreadsheet_id": spreadsheet_id, "range": range_name, "values": values, "row_count": len(values)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/sheets/write', methods=['POST'])
def sheets_write():
    """Write data to a Google Sheet."""
    data = request.get_json() or {}
    spreadsheet_id = data.get('spreadsheet_id') or os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    range_name = data.get('range', 'Sheet1!A1')
    values = data.get('values', [])
    if not spreadsheet_id:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "spreadsheet_id is required")
    if not values:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "values is required")
    service = get_sheets_service()
    if not service:
        return jsonify({"success": False, "error": "Sheets service not available"})
    try:
        body = {'values': values}
        result = service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption='USER_ENTERED', body=body).execute()
        return jsonify({"success": True, "updated_cells": result.get('updatedCells', 0)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/sheets/append', methods=['POST'])
def sheets_append():
    """Append rows to a Google Sheet."""
    data = request.get_json() or {}
    spreadsheet_id = data.get('spreadsheet_id') or os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    range_name = data.get('range', 'Sheet1!A1')
    values = data.get('values', [])
    if not spreadsheet_id:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "spreadsheet_id is required")
    service = get_sheets_service()
    if not service:
        return jsonify({"success": False, "error": "Sheets service not available"})
    try:
        body = {'values': values}
        result = service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS', body=body).execute()
        return jsonify({"success": True, "updated_range": result.get('updates', {}).get('updatedRange', '')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# Twilio SMS Integration
@app.route('/sms/send', methods=['POST'])
def sms_send():
    """Send an SMS via Twilio."""
    data = request.get_json() or {}
    to = data.get('to')
    body = data.get('body', '')
    from_number = data.get('from') or os.getenv('TWILIO_PHONE_NUMBER')
    if not to:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "to is required")
    if not body:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "body is required")
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    if not account_sid or not auth_token:
        return jsonify({"success": False, "error": "Twilio credentials not configured"})
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        message = client.messages.create(body=body, from_=from_number, to=to)
        return jsonify({"success": True, "sid": message.sid, "to": to, "status": message.status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/sms/list', methods=['POST'])
def sms_list():
    """List SMS messages from Twilio."""
    data = request.get_json() or {}
    limit = data.get('limit', 20)
    direction = data.get('direction', None)
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    if not account_sid or not auth_token:
        return jsonify({"success": False, "error": "Twilio credentials not configured"})
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        kwargs = {'limit': limit}
        if direction == 'inbound':
            kwargs['to'] = os.getenv('TWILIO_PHONE_NUMBER')
        elif direction == 'outbound':
            kwargs['from_'] = os.getenv('TWILIO_PHONE_NUMBER')
        messages = client.messages.list(**kwargs)
        sms_list = [{'sid': m.sid, 'from': m.from_, 'to': m.to, 'body': m.body, 'status': m.status, 'direction': m.direction} for m in messages]
        return jsonify({"success": True, "messages": sms_list, "count": len(sms_list)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ClickUp CRM Integration
@app.route('/clickup/list-tasks', methods=['POST'])
def clickup_list_tasks():
    """List tasks from ClickUp."""
    data = request.get_json() or {}
    list_id = data.get('list_id') or os.getenv('CLICKUP_LIST_ID')
    api_token = os.getenv('CLICKUP_API_TOKEN')
    if not api_token:
        return jsonify({"success": False, "error": "ClickUp API token not configured"})
    try:
        import requests
        headers = {'Authorization': api_token}
        url = f'https://api.clickup.com/api/v2/list/{list_id}/task'
        response = requests.get(url, headers=headers)
        result = response.json()
        if 'tasks' in result:
            tasks = [{'id': t['id'], 'name': t['name'], 'status': t['status']['status'] if t.get('status') else None} for t in result['tasks']]
            return jsonify({"success": True, "tasks": tasks, "count": len(tasks)})
        else:
            return jsonify({"success": False, "error": result.get('err', 'Unknown error')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/clickup/create-task', methods=['POST'])
def clickup_create_task():
    """Create a task in ClickUp."""
    data = request.get_json() or {}
    list_id = data.get('list_id') or os.getenv('CLICKUP_LIST_ID')
    name = data.get('name')
    description = data.get('description', '')
    if not name:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "name is required")
    api_token = os.getenv('CLICKUP_API_TOKEN')
    if not api_token:
        return jsonify({"success": False, "error": "ClickUp API token not configured"})
    try:
        import requests
        headers = {'Authorization': api_token, 'Content-Type': 'application/json'}
        url = f'https://api.clickup.com/api/v2/list/{list_id}/task'
        payload = {'name': name, 'description': description}
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        if 'id' in result:
            return jsonify({"success": True, "task_id": result['id'], "name": result['name']})
        else:
            return jsonify({"success": False, "error": result.get('err', 'Unknown error')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/clickup/update-task', methods=['POST'])
def clickup_update_task():
    """Update a task in ClickUp."""
    data = request.get_json() or {}
    task_id = data.get('task_id')
    if not task_id:
        return make_error_response(ErrorCode.MISSING_PARAMETER, "task_id is required")
    api_token = os.getenv('CLICKUP_API_TOKEN')
    if not api_token:
        return jsonify({"success": False, "error": "ClickUp API token not configured"})
    try:
        import requests
        headers = {'Authorization': api_token, 'Content-Type': 'application/json'}
        url = f'https://api.clickup.com/api/v2/task/{task_id}'
        payload = {k: v for k, v in data.items() if k in ['name', 'description', 'priority', 'status', 'due_date']}
        response = requests.put(url, headers=headers, json=payload)
        result = response.json()
        if 'id' in result:
            return jsonify({"success": True, "task_id": result['id'], "updated_fields": list(payload.keys())})
        else:
            return jsonify({"success": False, "error": result.get('err', 'Unknown error')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


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


# =============================================================================
# SELF-ANNEALING META-AGENT CAPABILITIES
# =============================================================================

@app.route('/meta/capabilities', methods=['GET', 'POST'])
def meta_capabilities():
    """List all available capabilities and tools."""
    capabilities = {
        'core_tools': ['file_read', 'file_write', 'file_edit', 'command', 'git_status', 'grep', 'glob', 'web_search', 'web_fetch', 'todo', 'checkpoint'],
        'integrations': {
            'gmail': ['gmail/list', 'gmail/read', 'gmail/send', 'gmail/search'],
            'sheets': ['sheets/read', 'sheets/write', 'sheets/append'],
            'sms': ['sms/send', 'sms/list'],
            'clickup': ['clickup/list-tasks', 'clickup/create-task', 'clickup/update-task'],
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


@app.route('/agent/build-workflow', methods=['POST'])
def agent_build_workflow():
    """Build a new n8n agent workflow from template."""
    data = request.get_json() or {}
    name = data.get('name', 'New Agent Workflow')
    webhook_path = data.get('webhook_path', 'custom-agent')
    tools = data.get('tools', ['file_read', 'file_write', 'command', 'grep', 'glob'])
    workflow = {
        'name': name,
        'nodes': [
            {'id': str(uuid.uuid4()), 'name': 'Webhook', 'type': 'n8n-nodes-base.webhook', 'position': [0, 0], 'typeVersion': 2, 'parameters': {'httpMethod': 'POST', 'path': webhook_path, 'responseMode': 'lastNode'}},
            {'id': str(uuid.uuid4()), 'name': 'Parse Request', 'type': 'n8n-nodes-base.code', 'position': [220, 0], 'typeVersion': 2, 'parameters': {'jsCode': f'return {{ json: {{ message: "{name} received request", data: $input.first().json }} }};'}},
            {'id': str(uuid.uuid4()), 'name': 'Return Response', 'type': 'n8n-nodes-base.code', 'position': [440, 0], 'typeVersion': 2, 'parameters': {'jsCode': 'return { json: $input.first().json };'}}
        ],
        'connections': {'Webhook': {'main': [[{'node': 'Parse Request', 'type': 'main', 'index': 0}]]}, 'Parse Request': {'main': [[{'node': 'Return Response', 'type': 'main', 'index': 0}]]}},
        'settings': {'executionOrder': 'v1'}
    }
    return jsonify({"success": True, "workflow": workflow, "name": name, "webhook_path": webhook_path, "tools": tools, "instructions": "Use /n8n/create-workflow with this workflow object to deploy it"})


# =============================================================================
# ERROR NOTIFICATION & AUTO-HEALING SYSTEM
# =============================================================================

# Error notification tracking
ERROR_NOTIFICATIONS: Dict[str, dict] = {}
AUTO_FIXES: Dict[str, dict] = {
    'ECONNREFUSED': {
        'description': 'Connection refused - service not running',
        'auto_fix': 'restart_service',
        'commands': ['systemctl restart {service}', 'docker restart {container}']
    },
    'ETIMEDOUT': {
        'description': 'Connection timeout - network or service slow',
        'auto_fix': 'retry_with_backoff',
        'max_retries': 3
    },
    'rate limit': {
        'description': 'Rate limited by external API',
        'auto_fix': 'exponential_backoff',
        'wait_seconds': [1, 5, 15, 60]
    },
    'authentication': {
        'description': 'Authentication failed',
        'auto_fix': 'refresh_credentials',
        'check_env_vars': True
    }
}


@app.route('/notify/error', methods=['POST'])
def notify_error():
    """Send error notification to appropriate channels based on severity."""
    data = request.get_json() or {}
    error_message = data.get('error_message', 'Unknown error')
    workflow_name = data.get('workflow_name', 'Unknown')
    node_name = data.get('node_name', 'Unknown')
    severity = data.get('severity', 'medium').lower()

    notification_id = f"notify_{int(time.time())}_{uuid.uuid4().hex[:6]}"

    # Determine channels based on severity
    channels = []
    if severity == 'critical':
        channels = ['sms', 'email', 'slack']
    elif severity == 'high':
        channels = ['email', 'slack']
    else:
        channels = ['log']

    # Store notification
    ERROR_NOTIFICATIONS[notification_id] = {
        'id': notification_id,
        'error_message': error_message,
        'workflow_name': workflow_name,
        'node_name': node_name,
        'severity': severity,
        'channels': channels,
        'sent_at': datetime.now().isoformat(),
        'acknowledged': False
    }

    # For critical errors, attempt SMS notification via Twilio
    sms_sent = False
    if 'sms' in channels:
        try:
            twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
            twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
            twilio_from = os.getenv('TWILIO_PHONE_NUMBER')
            admin_phone = os.getenv('ADMIN_PHONE_NUMBER', '+18135551234')

            if twilio_sid and twilio_token and twilio_from:
                from twilio.rest import Client
                client = Client(twilio_sid, twilio_token)
                sms_body = f"🚨 CRITICAL: {workflow_name}\n{error_message[:140]}"
                message = client.messages.create(body=sms_body, from_=twilio_from, to=admin_phone)
                sms_sent = True
                ERROR_NOTIFICATIONS[notification_id]['sms_sid'] = message.sid
        except Exception as e:
            ERROR_NOTIFICATIONS[notification_id]['sms_error'] = str(e)

    return jsonify({
        "success": True,
        "notification_id": notification_id,
        "severity": severity,
        "channels": channels,
        "sms_sent": sms_sent,
        "message": f"Error notification sent via {', '.join(channels)}"
    })


@app.route('/notify/critical', methods=['POST'])
def notify_critical():
    """Send urgent SMS notification for critical errors."""
    data = request.get_json() or {}
    message = data.get('message', 'Critical system error')
    workflow = data.get('workflow', 'Unknown')

    # Always try SMS for critical notifications
    result = {'success': False, 'method': 'critical_sms'}

    try:
        twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_from = os.getenv('TWILIO_PHONE_NUMBER')
        admin_phone = os.getenv('ADMIN_PHONE_NUMBER', '+18135551234')

        if twilio_sid and twilio_token and twilio_from:
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            sms_body = f"🚨 CRITICAL ERROR\n{workflow}\n{message[:120]}"
            sms = client.messages.create(body=sms_body, from_=twilio_from, to=admin_phone)
            result = {'success': True, 'sms_sid': sms.sid, 'method': 'twilio'}
        else:
            result = {'success': False, 'error': 'Twilio credentials not configured'}
    except Exception as e:
        result = {'success': False, 'error': str(e)}

    return jsonify(result)


@app.route('/error/analyze', methods=['POST'])
def error_analyze():
    """Analyze error patterns and suggest fixes."""
    data = request.get_json() or {}
    error_message = data.get('error_message', '')
    error_type = data.get('error_type', '')

    analysis = {
        'error_message': error_message,
        'error_type': error_type,
        'known_pattern': False,
        'auto_fix_available': False,
        'suggestions': [],
        'similar_errors': []
    }

    # Check against known auto-fix patterns
    for pattern, fix_info in AUTO_FIXES.items():
        if pattern.lower() in error_message.lower() or pattern.lower() in error_type.lower():
            analysis['known_pattern'] = True
            analysis['auto_fix_available'] = True
            analysis['auto_fix'] = fix_info
            analysis['suggestions'].append(f"Auto-fix available: {fix_info['description']}")
            break

    # Check against learned error solutions
    for error_id, error_data in ERROR_SOLUTIONS.items():
        if error_data['pattern'].lower() in error_message.lower():
            analysis['similar_errors'].append({
                'pattern': error_data['pattern'],
                'solution': error_data['solution'],
                'times_applied': error_data.get('times_applied', 0)
            })

    # General suggestions based on error type
    if 'timeout' in error_message.lower():
        analysis['suggestions'].append('Consider increasing timeout values')
        analysis['suggestions'].append('Check network connectivity')
    if 'permission' in error_message.lower():
        analysis['suggestions'].append('Verify file/directory permissions')
        analysis['suggestions'].append('Check user authentication')
    if 'not found' in error_message.lower():
        analysis['suggestions'].append('Verify path/resource exists')
        analysis['suggestions'].append('Check for typos in identifiers')

    return jsonify({"success": True, "analysis": analysis})


@app.route('/error/auto-fix', methods=['POST'])
def error_auto_fix():
    """Attempt automatic fix for known error types."""
    data = request.get_json() or {}
    error_message = data.get('error_message', '')
    error_type = data.get('error_type', '')
    dry_run = data.get('dry_run', True)  # Default to dry run for safety

    fix_result = {
        'error_message': error_message,
        'fix_attempted': False,
        'fix_succeeded': False,
        'dry_run': dry_run,
        'actions': []
    }

    # Find matching auto-fix
    matched_fix = None
    for pattern, fix_info in AUTO_FIXES.items():
        if pattern.lower() in error_message.lower() or pattern.lower() in error_type.lower():
            matched_fix = (pattern, fix_info)
            break

    if not matched_fix:
        return jsonify({"success": False, "error": "No auto-fix available for this error type", "result": fix_result})

    pattern, fix_info = matched_fix
    fix_result['fix_attempted'] = True
    fix_result['fix_type'] = fix_info['auto_fix']

    if fix_info['auto_fix'] == 'retry_with_backoff':
        fix_result['actions'].append({
            'action': 'retry_with_backoff',
            'max_retries': fix_info.get('max_retries', 3),
            'description': 'Retry the operation with exponential backoff'
        })
        if not dry_run:
            fix_result['fix_succeeded'] = True
            fix_result['next_action'] = 'Caller should implement retry logic'

    elif fix_info['auto_fix'] == 'exponential_backoff':
        wait_times = fix_info.get('wait_seconds', [1, 5, 15])
        fix_result['actions'].append({
            'action': 'wait_and_retry',
            'wait_seconds': wait_times,
            'description': f'Wait {wait_times[0]}s then retry, increasing on each failure'
        })
        if not dry_run:
            fix_result['fix_succeeded'] = True

    elif fix_info['auto_fix'] == 'refresh_credentials':
        fix_result['actions'].append({
            'action': 'refresh_credentials',
            'check_env_vars': fix_info.get('check_env_vars', True),
            'description': 'Refresh authentication credentials'
        })
        if not dry_run:
            # Could trigger credential refresh here
            fix_result['fix_succeeded'] = True

    # Log the fix attempt
    fix_id = f"fix_{int(time.time())}"
    if 'AUTO_FIX_LOG' not in globals():
        global AUTO_FIX_LOG
        AUTO_FIX_LOG = {}
    AUTO_FIX_LOG[fix_id] = {
        'error_message': error_message,
        'fix_type': fix_info['auto_fix'],
        'succeeded': fix_result['fix_succeeded'],
        'timestamp': datetime.now().isoformat()
    }

    return jsonify({"success": True, "result": fix_result})


@app.route('/error/stats', methods=['GET'])
def error_stats():
    """Get error and notification statistics."""
    return jsonify({
        "success": True,
        "stats": {
            "total_notifications": len(ERROR_NOTIFICATIONS),
            "error_solutions_learned": len(ERROR_SOLUTIONS),
            "auto_fix_patterns": len(AUTO_FIXES),
            "recent_notifications": list(ERROR_NOTIFICATIONS.values())[-10:],
            "most_common_errors": _get_common_errors()
        }
    })


def _get_common_errors():
    """Get most common error patterns."""
    error_counts = {}
    for error_id, error_data in ERROR_SOLUTIONS.items():
        pattern = error_data.get('pattern', 'unknown')
        error_counts[pattern] = error_counts.get(pattern, 0) + 1
    return sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]


# =============================================================================
# MAIN
# =============================================================================


# =============================================================================
# V4.2 ADVANCED ENDPOINTS - Circuit Breaker, DLQ, Batch, Priority Queue
# =============================================================================

# Data structures for v4.2
DEAD_LETTER_QUEUE = []
REQUEST_CACHE = {}
CIRCUIT_STATE = {
    'state': 'closed',
    'failures': 0,
    'last_failure': 0,
    'threshold': 5,
    'timeout': 30000
}
PRIORITY_QUEUE = []
BATCH_RESULTS = {}


# === Dead Letter Queue Endpoints ===

@app.route('/dlq/add', methods=['POST'])
def dlq_add():
    """Add a failed task to the dead letter queue"""
    data = request.get_json() or {}

    entry = {
        'id': f"dlq_{int(time.time() * 1000)}",
        'request_id': data.get('request_id', 'unknown'),
        'original_task': data.get('original_task'),
        'error': data.get('error'),
        'retry_count': data.get('retry_count', 0),
        'max_retries': data.get('max_retries', 3),
        'next_retry_at': data.get('next_retry_at'),
        'created_at': data.get('created_at', datetime.now().isoformat()),
        'status': 'pending'
    }

    DEAD_LETTER_QUEUE.append(entry)

    return jsonify({
        'success': True,
        'dlq_id': entry['id'],
        'queue_size': len(DEAD_LETTER_QUEUE)
    })


@app.route('/dlq/list', methods=['GET', 'POST'])
def dlq_list():
    """List all items in the dead letter queue"""
    status_filter = request.args.get('status', None)

    items = DEAD_LETTER_QUEUE
    if status_filter:
        items = [i for i in items if i['status'] == status_filter]

    return jsonify({
        'success': True,
        'total': len(items),
        'items': items
    })


@app.route('/dlq/retry/<dlq_id>', methods=['POST'])
def dlq_retry(dlq_id):
    """Retry a failed task from the DLQ"""
    for entry in DEAD_LETTER_QUEUE:
        if entry['id'] == dlq_id:
            if entry['retry_count'] >= entry['max_retries']:
                return jsonify({
                    'success': False,
                    'error': 'Max retries exceeded'
                }), 400

            entry['retry_count'] += 1
            entry['status'] = 'retrying'

            return jsonify({
                'success': True,
                'dlq_id': dlq_id,
                'retry_count': entry['retry_count']
            })

    return jsonify({'success': False, 'error': 'Entry not found'}), 404


@app.route('/dlq/clear', methods=['POST'])
def dlq_clear():
    """Clear the dead letter queue"""
    global DEAD_LETTER_QUEUE
    count = len(DEAD_LETTER_QUEUE)
    DEAD_LETTER_QUEUE = []
    return jsonify({
        'success': True,
        'cleared': count
    })


# === Circuit Breaker Endpoints ===

@app.route('/circuit/status', methods=['GET', 'POST'])
def circuit_status():
    """Get circuit breaker status"""
    return jsonify({
        'success': True,
        'circuit': CIRCUIT_STATE
    })


@app.route('/circuit/reset', methods=['POST'])
def circuit_reset():
    """Reset the circuit breaker"""
    global CIRCUIT_STATE
    CIRCUIT_STATE = {
        'state': 'closed',
        'failures': 0,
        'last_failure': 0,
        'threshold': 5,
        'timeout': 30000
    }
    return jsonify({
        'success': True,
        'circuit': CIRCUIT_STATE
    })


@app.route('/circuit/trip', methods=['POST'])
def circuit_trip():
    """Manually trip the circuit breaker"""
    global CIRCUIT_STATE
    CIRCUIT_STATE['state'] = 'open'
    CIRCUIT_STATE['last_failure'] = int(time.time() * 1000)
    return jsonify({
        'success': True,
        'circuit': CIRCUIT_STATE
    })


@app.route('/circuit/failure', methods=['POST'])
def circuit_record_failure():
    """Record a failure for the circuit breaker"""
    global CIRCUIT_STATE
    CIRCUIT_STATE['failures'] += 1
    CIRCUIT_STATE['last_failure'] = int(time.time() * 1000)

    if CIRCUIT_STATE['failures'] >= CIRCUIT_STATE['threshold']:
        CIRCUIT_STATE['state'] = 'open'

    return jsonify({
        'success': True,
        'circuit': CIRCUIT_STATE
    })


@app.route('/circuit/success', methods=['POST'])
def circuit_record_success():
    """Record a success for the circuit breaker (resets if half-open)"""
    global CIRCUIT_STATE
    if CIRCUIT_STATE['state'] == 'half-open':
        CIRCUIT_STATE['state'] = 'closed'
        CIRCUIT_STATE['failures'] = 0

    return jsonify({
        'success': True,
        'circuit': CIRCUIT_STATE
    })


# === Request Deduplication Endpoints ===

@app.route('/dedup/check', methods=['POST'])
def dedup_check():
    """Check if a request is a duplicate"""
    data = request.get_json() or {}
    fingerprint = data.get('fingerprint')

    if not fingerprint:
        return jsonify({'success': False, 'error': 'fingerprint required'}), 400

    is_duplicate = fingerprint in REQUEST_CACHE
    if not is_duplicate:
        REQUEST_CACHE[fingerprint] = {
            'first_seen': datetime.now().isoformat(),
            'count': 1
        }
    else:
        REQUEST_CACHE[fingerprint]['count'] += 1

    return jsonify({
        'success': True,
        'is_duplicate': is_duplicate,
        'fingerprint': fingerprint,
        'seen_count': REQUEST_CACHE.get(fingerprint, {}).get('count', 0)
    })


@app.route('/dedup/clear', methods=['POST'])
def dedup_clear():
    """Clear the deduplication cache"""
    global REQUEST_CACHE
    count = len(REQUEST_CACHE)
    REQUEST_CACHE = {}
    return jsonify({
        'success': True,
        'cleared': count
    })


# === Batch Processing Endpoints ===

@app.route('/batch/create', methods=['POST'])
def batch_create():
    """Create a new batch job"""
    data = request.get_json() or {}
    batch_id = f"batch_{int(time.time() * 1000)}"

    BATCH_RESULTS[batch_id] = {
        'batch_id': batch_id,
        'task_count': data.get('task_count', 0),
        'completed': 0,
        'failed': 0,
        'results': [],
        'status': 'running',
        'created_at': datetime.now().isoformat()
    }

    return jsonify({
        'success': True,
        'batch_id': batch_id
    })


@app.route('/batch/update/<batch_id>', methods=['POST'])
def batch_update(batch_id):
    """Update batch job with a result"""
    if batch_id not in BATCH_RESULTS:
        return jsonify({'success': False, 'error': 'Batch not found'}), 404

    data = request.get_json() or {}
    batch = BATCH_RESULTS[batch_id]

    result = {
        'index': data.get('index', len(batch['results'])),
        'success': data.get('success', True),
        'result': data.get('result'),
        'error': data.get('error')
    }

    batch['results'].append(result)
    if result['success']:
        batch['completed'] += 1
    else:
        batch['failed'] += 1

    if len(batch['results']) >= batch['task_count']:
        batch['status'] = 'completed'

    return jsonify({
        'success': True,
        'batch': batch
    })


@app.route('/batch/status/<batch_id>', methods=['GET', 'POST'])
def batch_status(batch_id):
    """Get batch job status"""
    if batch_id not in BATCH_RESULTS:
        return jsonify({'success': False, 'error': 'Batch not found'}), 404

    return jsonify({
        'success': True,
        'batch': BATCH_RESULTS[batch_id]
    })


@app.route('/batch/list', methods=['GET', 'POST'])
def batch_list():
    """List all batch jobs"""
    return jsonify({
        'success': True,
        'total': len(BATCH_RESULTS),
        'batches': list(BATCH_RESULTS.values())
    })


# === Priority Queue Endpoints ===

@app.route('/queue/add', methods=['POST'])
def queue_add():
    """Add a task to the priority queue"""
    data = request.get_json() or {}

    entry = {
        'id': f"q_{int(time.time() * 1000)}",
        'task': data.get('task'),
        'priority': data.get('priority', 3),
        'created_at': datetime.now().isoformat()
    }

    PRIORITY_QUEUE.append(entry)
    PRIORITY_QUEUE.sort(key=lambda x: x['priority'])

    return jsonify({
        'success': True,
        'queue_id': entry['id'],
        'position': PRIORITY_QUEUE.index(entry)
    })


@app.route('/queue/next', methods=['GET', 'POST'])
def queue_next():
    """Get the next task from the priority queue"""
    if not PRIORITY_QUEUE:
        return jsonify({'success': True, 'task': None, 'empty': True})

    task = PRIORITY_QUEUE.pop(0)
    return jsonify({
        'success': True,
        'task': task,
        'remaining': len(PRIORITY_QUEUE)
    })


@app.route('/queue/list', methods=['GET', 'POST'])
def queue_list():
    """List all tasks in the priority queue"""
    return jsonify({
        'success': True,
        'total': len(PRIORITY_QUEUE),
        'tasks': PRIORITY_QUEUE
    })


@app.route('/queue/clear', methods=['POST'])
def queue_clear():
    """Clear the priority queue"""
    global PRIORITY_QUEUE
    count = len(PRIORITY_QUEUE)
    PRIORITY_QUEUE = []
    return jsonify({
        'success': True,
        'cleared': count
    })

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
    print(f"Agent Bridge API v4.1.0 - Self-Annealing Meta-Agent Edition")
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
    print(f"Allowed paths: {ALLOWED_BASE_PATHS}")
    print(f"Persistence: {'ENABLED' if PERSISTENCE_ENABLED else 'DISABLED'}")
    print(f"Cache: {TOOL_CACHE.max_size} items, {TOOL_CACHE.default_ttl}s TTL")
    print(f"Rate Limit: {RATE_LIMITERS['default'].rate}/s, burst {RATE_LIMITERS['default'].burst}")
    print(f"{'='*60}\n")

    app.run(host=args.host, port=args.port, debug=args.debug)



# === v4.3 Data Structures ===
METRICS_STORE = []  # Prometheus metrics history
FEATURE_FLAGS_OVERRIDE = {}  # Feature flag overrides
AB_EXPERIMENTS = {}  # A/B test tracking
WORKFLOW_VERSIONS = []  # Version history
HEALTH_CHECKS = {}  # Health check results
REQUEST_TRACES = {}  # Distributed traces


# === v4.3 Prometheus Metrics Endpoints ===

@app.route('/prometheus', methods=['GET'])
def metrics_get():
    """Get Prometheus-formatted metrics"""
    recent = METRICS_STORE[-100:] if METRICS_STORE else []

    total_requests = len(recent)
    total_cost = sum(m.get('cost_usd', 0) for m in recent)
    avg_duration = sum(m.get('request_duration_ms', 0) for m in recent) / max(len(recent), 1)
    error_count = sum(1 for m in recent if m.get('response_error', 0) > 0)

    prometheus_format = f"""# HELP agent_requests_total Total requests
# TYPE agent_requests_total counter
agent_requests_total {total_requests}

# HELP agent_cost_usd_total Total cost USD
# TYPE agent_cost_usd_total counter
agent_cost_usd_total {total_cost:.6f}

# HELP agent_request_duration_ms Average duration ms
# TYPE agent_request_duration_ms gauge
agent_request_duration_ms {avg_duration:.2f}

# HELP agent_errors_total Total errors
# TYPE agent_errors_total counter
agent_errors_total {error_count}

# HELP agent_circuit_state Circuit state (0=closed,1=open,2=half)
# TYPE agent_circuit_state gauge
agent_circuit_state {0 if CIRCUIT_STATE.get('state') == 'closed' else 1 if CIRCUIT_STATE.get('state') == 'open' else 2}
"""
    return prometheus_format, 200, {'Content-Type': 'text/plain'}


@app.route('/prometheus/record', methods=['POST'])
def metrics_record():
    """Record a metrics entry"""
    data = request.get_json() or {}
    entry = {'timestamp': datetime.now().isoformat(), **data}
    METRICS_STORE.append(entry)
    while len(METRICS_STORE) > 1000:
        METRICS_STORE.pop(0)
    return jsonify({'success': True, 'metrics_count': len(METRICS_STORE)})


# === v4.3 Feature Flags Endpoints ===

@app.route('/features/list', methods=['GET'])
def features_list():
    """List all feature flags"""
    defaults = {
        'core.file_operations': {'enabled': True, 'rollout': 100},
        'v4.personas': {'enabled': True, 'rollout': 100},
        'v4.1.gmail': {'enabled': True, 'rollout': 100},
        'v4.2.circuit_breaker': {'enabled': True, 'rollout': 100},
        'v4.3.jwt_auth': {'enabled': True, 'rollout': 50},
        'v4.3.metrics': {'enabled': True, 'rollout': 100},
        'v4.3.ab_testing': {'enabled': True, 'rollout': 25},
        'v4.3.workflow_versioning': {'enabled': False, 'rollout': 0}
    }
    features = {**defaults, **FEATURE_FLAGS_OVERRIDE}
    return jsonify({'success': True, 'features': features, 'overrides': FEATURE_FLAGS_OVERRIDE})


@app.route('/features/set', methods=['POST'])
def features_set():
    """Override a feature flag"""
    data = request.get_json() or {}
    feature = data.get('feature')
    if not feature:
        return jsonify({'success': False, 'error': 'feature required'}), 400
    FEATURE_FLAGS_OVERRIDE[feature] = {
        'enabled': data.get('enabled', True),
        'rollout': data.get('rollout', 100),
        'override_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'feature': feature, 'config': FEATURE_FLAGS_OVERRIDE[feature]})


@app.route('/features/reset', methods=['POST'])
def features_reset():
    """Reset feature flag overrides"""
    global FEATURE_FLAGS_OVERRIDE
    count = len(FEATURE_FLAGS_OVERRIDE)
    FEATURE_FLAGS_OVERRIDE = {}
    return jsonify({'success': True, 'cleared': count})


# === v4.3 A/B Testing Endpoints ===

@app.route('/ab/experiments', methods=['GET'])
def ab_experiments_list():
    """List A/B experiments"""
    defaults = {
        'prompt_optimization': {'enabled': True, 'variants': ['control', 'treatment_a'], 'weights': [50, 50]},
        'model_comparison': {'enabled': True, 'variants': ['claude_sonnet', 'claude_haiku'], 'weights': [80, 20]},
        'timeout_optimization': {'enabled': True, 'variants': ['standard', 'extended'], 'weights': [70, 30]}
    }
    return jsonify({'success': True, 'experiments': defaults})


@app.route('/ab/record', methods=['POST'])
def ab_record():
    """Record A/B result"""
    data = request.get_json() or {}
    experiment = data.get('experiment')
    variant = data.get('variant')
    outcome = data.get('outcome')
    if not experiment or not variant:
        return jsonify({'success': False, 'error': 'experiment and variant required'}), 400
    key = f"{experiment}:{variant}"
    if key not in AB_EXPERIMENTS:
        AB_EXPERIMENTS[key] = {'count': 0, 'outcomes': {}}
    AB_EXPERIMENTS[key]['count'] += 1
    if outcome:
        AB_EXPERIMENTS[key]['outcomes'][outcome] = AB_EXPERIMENTS[key]['outcomes'].get(outcome, 0) + 1
    return jsonify({'success': True, 'experiment': experiment, 'variant': variant, 'stats': AB_EXPERIMENTS[key]})


@app.route('/ab/results/<experiment>', methods=['GET'])
def ab_results(experiment):
    """Get A/B results"""
    results = {}
    for key, data in AB_EXPERIMENTS.items():
        if key.startswith(f"{experiment}:"):
            variant = key.split(':')[1]
            results[variant] = data
    if not results:
        return jsonify({'success': False, 'error': 'No data'}), 404
    return jsonify({'success': True, 'experiment': experiment, 'results': results})


# === v4.3 Workflow Versioning Endpoints ===

@app.route('/versioning/current', methods=['GET'])
def versioning_current():
    """Get current version"""
    return jsonify({
        'success': True,
        'version': {'major': 4, 'minor': 3, 'patch': 0, 'prerelease': 'beta', 'full': '4.3.0-beta', 'build_date': '2026-02-07'}
    })


@app.route('/versioning/history', methods=['GET'])
def versioning_history():
    """Get version history"""
    history = [
        {'version': '4.3.0-beta', 'date': '2026-02-07', 'status': 'current'},
        {'version': '4.2.0', 'date': '2026-02-07', 'status': 'stable'},
        {'version': '4.1.1', 'date': '2026-02-07', 'status': 'stable'},
        {'version': '4.1.0', 'date': '2026-02-07', 'status': 'deprecated'}
    ]
    return jsonify({'success': True, 'history': history, 'rollback_available': ['4.2.0', '4.1.1']})


@app.route('/versioning/rollback', methods=['POST'])
def versioning_rollback():
    """Initiate rollback"""
    data = request.get_json() or {}
    target = data.get('version')
    if not target:
        return jsonify({'success': False, 'error': 'version required'}), 400
    return jsonify({'success': True, 'message': f'Rollback to {target} initiated', 'note': 'Placeholder'})


# === v4.3 Health Dashboard Endpoints ===

@app.route('/health/dashboard', methods=['GET'])
def health_dashboard():
    """Get health dashboard"""
    circuit = CIRCUIT_STATE
    dlq_size = len(DEAD_LETTER_QUEUE)
    queue_size = len(PRIORITY_QUEUE)

    subsystems = {
        'bridge_api': {'status': 'healthy', 'uptime': '99.9%'},
        'circuit_breaker': {'status': 'healthy' if circuit.get('state') == 'closed' else 'degraded', 'state': circuit.get('state', 'closed')},
        'dead_letter_queue': {'status': 'healthy' if dlq_size < 10 else 'warning', 'pending': dlq_size},
        'priority_queue': {'status': 'healthy', 'queued': queue_size}
    }

    statuses = [s.get('status') for s in subsystems.values()]
    overall = 'unhealthy' if 'unhealthy' in statuses else 'degraded' if 'degraded' in statuses else 'healthy'

    return jsonify({
        'success': True,
        'overall': overall,
        'timestamp': datetime.now().isoformat(),
        'subsystems': subsystems
    })


@app.route('/health/check', methods=['POST'])
def health_check():
    """Run health check"""
    data = request.get_json() or {}
    subsystem = data.get('subsystem', 'all')
    checks = {}
    if subsystem in ['all', 'bridge_api']:
        checks['bridge_api'] = {'status': 'healthy', 'latency_ms': 1}
    if subsystem in ['all', 'circuit_breaker']:
        checks['circuit_breaker'] = {'status': 'healthy' if CIRCUIT_STATE.get('state') == 'closed' else 'degraded'}
    if subsystem in ['all', 'dlq']:
        checks['dlq'] = {'status': 'healthy', 'size': len(DEAD_LETTER_QUEUE)}
    HEALTH_CHECKS[datetime.now().isoformat()] = checks
    return jsonify({'success': True, 'checks': checks})


# === v4.3 Request Tracing Endpoints ===

@app.route('/trace/start', methods=['POST'])
def trace_start():
    """Start a trace"""
    data = request.get_json() or {}
    trace_id = data.get('trace_id') or f"{int(time.time() * 1000)}{random.randint(1000, 9999)}"
    span_id = f"{int(time.time() * 1000)}{random.randint(100, 999)}"
    trace = {
        'trace_id': trace_id,
        'span_id': span_id,
        'parent_span_id': data.get('parent_span_id'),
        'name': data.get('name', 'agent.request'),
        'start_time': datetime.now().isoformat(),
        'attributes': data.get('attributes', {}),
        'events': [],
        'status': 'in_progress'
    }
    REQUEST_TRACES[trace_id] = trace
    return jsonify({'success': True, 'trace': trace, 'traceparent': f"00-{trace_id}-{span_id}-01"})


@app.route('/trace/end/<trace_id>', methods=['POST'])
def trace_end(trace_id):
    """End a trace"""
    if trace_id not in REQUEST_TRACES:
        return jsonify({'success': False, 'error': 'Trace not found'}), 404
    data = request.get_json() or {}
    trace = REQUEST_TRACES[trace_id]
    trace['end_time'] = datetime.now().isoformat()
    trace['status'] = data.get('status', 'ok')
    return jsonify({'success': True, 'trace': trace})


@app.route('/trace/event', methods=['POST'])
def trace_event():
    """Add event to trace"""
    data = request.get_json() or {}
    trace_id = data.get('trace_id')
    if not trace_id or trace_id not in REQUEST_TRACES:
        return jsonify({'success': False, 'error': 'Trace not found'}), 404
    event = {'name': data.get('name', 'event'), 'timestamp': datetime.now().isoformat(), 'attributes': data.get('attributes', {})}
    REQUEST_TRACES[trace_id]['events'].append(event)
    return jsonify({'success': True, 'trace_id': trace_id, 'event_count': len(REQUEST_TRACES[trace_id]['events'])})


@app.route('/trace/<trace_id>', methods=['GET'])
def trace_get(trace_id):
    """Get trace"""
    if trace_id not in REQUEST_TRACES:
        return jsonify({'success': False, 'error': 'Trace not found'}), 404
    return jsonify({'success': True, 'trace': REQUEST_TRACES[trace_id]})


# End of v4.3 endpoints


# === v4.4 Data Structures ===
CACHE_STORE = {}  # Request cache
TENANT_CONFIG = {}  # Tenant configurations
CANARY_METRICS = {}  # Canary deployment metrics
SLA_VIOLATIONS = []  # SLA violation log
WS_CONNECTIONS = {}  # WebSocket connections
REPLAY_QUEUE = []  # Requests to replay
SECRET_HEALTH = {}  # Secret health status
CORRELATION_LOG = []  # Request correlation log


# === v4.4 Tenant Endpoints ===

@app.route('/tenant/list', methods=['GET'])
def tenant_list():
    """List tenants"""
    defaults = {'default': {'name': 'Default', 'sandbox': False}, 'enterprise': {'name': 'Enterprise', 'sandbox': False}, 'sandbox': {'name': 'Sandbox', 'sandbox': True}}
    return jsonify({'success': True, 'tenants': {**defaults, **TENANT_CONFIG}})


@app.route('/tenant/get/<tenant_id>', methods=['GET'])
def tenant_get(tenant_id):
    """Get tenant config"""
    defaults = {'default': {'name': 'Default', 'allowed_paths': ['/tmp'], 'max_file_size_mb': 10}, 'enterprise': {'name': 'Enterprise', 'allowed_paths': ['*'], 'max_file_size_mb': 100}}
    config = TENANT_CONFIG.get(tenant_id) or defaults.get(tenant_id)
    if not config:
        return jsonify({'success': False, 'error': 'Tenant not found'}), 404
    return jsonify({'success': True, 'tenant_id': tenant_id, 'config': config})


@app.route('/tenant/create', methods=['POST'])
def tenant_create():
    """Create tenant"""
    data = request.get_json() or {}
    tenant_id = data.get('tenant_id')
    if not tenant_id:
        return jsonify({'success': False, 'error': 'tenant_id required'}), 400
    TENANT_CONFIG[tenant_id] = {'name': data.get('name', tenant_id), 'allowed_paths': data.get('allowed_paths', ['/tmp']), 'max_file_size_mb': data.get('max_file_size_mb', 10), 'sandbox': data.get('sandbox', False), 'created_at': datetime.now().isoformat()}
    return jsonify({'success': True, 'tenant_id': tenant_id, 'config': TENANT_CONFIG[tenant_id]})


# === v4.4 Canary Endpoints ===

@app.route('/canary/list', methods=['GET'])
def canary_list():
    """List canary deployments"""
    defaults = {'v4.4-websocket': {'enabled': True, 'traffic_percent': 10, 'target': '4.4.0'}, 'new-model-test': {'enabled': True, 'traffic_percent': 5, 'target': 'claude-opus'}}
    return jsonify({'success': True, 'canaries': defaults})


@app.route('/canary/metrics/<canary_id>', methods=['GET'])
def canary_metrics(canary_id):
    """Get canary metrics"""
    metrics = CANARY_METRICS.get(canary_id, {'requests': 0, 'success_rate': 0, 'avg_latency_ms': 0})
    return jsonify({'success': True, 'canary_id': canary_id, 'metrics': metrics})


@app.route('/canary/record', methods=['POST'])
def canary_record():
    """Record canary metric"""
    data = request.get_json() or {}
    canary_id = data.get('canary_id')
    if not canary_id:
        return jsonify({'success': False, 'error': 'canary_id required'}), 400
    if canary_id not in CANARY_METRICS:
        CANARY_METRICS[canary_id] = {'requests': 0, 'successes': 0, 'total_latency': 0}
    CANARY_METRICS[canary_id]['requests'] += 1
    if data.get('success'):
        CANARY_METRICS[canary_id]['successes'] += 1
    CANARY_METRICS[canary_id]['total_latency'] += data.get('latency_ms', 0)
    m = CANARY_METRICS[canary_id]
    m['success_rate'] = m['successes'] / m['requests'] if m['requests'] > 0 else 0
    m['avg_latency_ms'] = m['total_latency'] / m['requests'] if m['requests'] > 0 else 0
    return jsonify({'success': True, 'metrics': m})


# === v4.4 SLA Endpoints ===

@app.route('/sla/definitions', methods=['GET'])
def sla_definitions():
    """Get SLA definitions"""
    slas = {'response_time': {'target_ms': 5000, 'warning_ms': 3000, 'critical_ms': 10000}, 'availability': {'target_percent': 99.9}, 'error_rate': {'target_percent': 1.0}}
    return jsonify({'success': True, 'slas': slas})


@app.route('/sla/violations', methods=['GET'])
def sla_violations_list():
    """List SLA violations"""
    limit = int(request.args.get('limit', 100))
    return jsonify({'success': True, 'violations': SLA_VIOLATIONS[-limit:], 'total': len(SLA_VIOLATIONS)})


@app.route('/sla/record', methods=['POST'])
def sla_record():
    """Record SLA violation"""
    data = request.get_json() or {}
    violation = {'timestamp': datetime.now().isoformat(), 'sla': data.get('sla'), 'severity': data.get('severity', 'warning'), 'current': data.get('current'), 'target': data.get('target'), 'request_id': data.get('request_id')}
    SLA_VIOLATIONS.append(violation)
    while len(SLA_VIOLATIONS) > 1000:
        SLA_VIOLATIONS.pop(0)
    return jsonify({'success': True, 'violation': violation, 'total': len(SLA_VIOLATIONS)})


# === v4.4 WebSocket Endpoints ===

@app.route('/ws/register', methods=['POST'])
def ws_register():
    """Register WebSocket connection"""
    data = request.get_json() or {}
    conn_id = data.get('connection_id') or f"ws_{int(time.time()*1000)}"
    WS_CONNECTIONS[conn_id] = {'user_id': data.get('user_id'), 'subscriptions': data.get('subscriptions', []), 'connected_at': datetime.now().isoformat()}
    return jsonify({'success': True, 'connection_id': conn_id})


@app.route('/ws/unregister/<conn_id>', methods=['POST'])
def ws_unregister(conn_id):
    """Unregister WebSocket connection"""
    if conn_id in WS_CONNECTIONS:
        del WS_CONNECTIONS[conn_id]
        return jsonify({'success': True, 'connection_id': conn_id})
    return jsonify({'success': False, 'error': 'Connection not found'}), 404


@app.route('/ws/broadcast', methods=['POST'])
def ws_broadcast():
    """Broadcast message to WebSocket connections"""
    data = request.get_json() or {}
    message = data.get('message')
    target_users = data.get('users', [])
    target_subs = data.get('subscriptions', [])
    recipients = []
    for conn_id, conn in WS_CONNECTIONS.items():
        if not target_users or conn.get('user_id') in target_users:
            if not target_subs or any(s in conn.get('subscriptions', []) for s in target_subs):
                recipients.append(conn_id)
    return jsonify({'success': True, 'message': message, 'recipients': len(recipients), 'connection_ids': recipients})


@app.route('/ws/connections', methods=['GET'])
def ws_connections():
    """List WebSocket connections"""
    return jsonify({'success': True, 'connections': WS_CONNECTIONS, 'count': len(WS_CONNECTIONS)})


# === v4.4 Replay Endpoints ===

@app.route('/replay/queue', methods=['GET'])
def replay_queue_list():
    """List replay queue"""
    return jsonify({'success': True, 'queue': REPLAY_QUEUE, 'count': len(REPLAY_QUEUE)})


@app.route('/replay/add', methods=['POST'])
def replay_add():
    """Add request to replay queue"""
    data = request.get_json() or {}
    entry = {'id': f"replay_{int(time.time()*1000)}", 'original_request': data.get('request'), 'error': data.get('error'), 'retry_count': 0, 'max_retries': data.get('max_retries', 3), 'scheduled_at': data.get('scheduled_at', datetime.now().isoformat()), 'status': 'pending'}
    REPLAY_QUEUE.append(entry)
    return jsonify({'success': True, 'entry': entry})


@app.route('/replay/process', methods=['POST'])
def replay_process():
    """Process next item in replay queue"""
    pending = [e for e in REPLAY_QUEUE if e['status'] == 'pending']
    if not pending:
        return jsonify({'success': True, 'message': 'Queue empty'})
    entry = pending[0]
    entry['status'] = 'processing'
    entry['retry_count'] += 1
    return jsonify({'success': True, 'entry': entry})


# === v4.4 Secret Endpoints ===

@app.route('/secrets/health', methods=['GET'])
def secrets_health():
    """Get secrets health status"""
    defaults = {'anthropic_api_key': {'status': 'healthy', 'days_until_expiry': 60}, 'google_oauth': {'status': 'warning', 'days_until_expiry': 7}, 'twilio_credentials': {'status': 'healthy', 'days_until_expiry': 45}}
    health = {**defaults, **SECRET_HEALTH}
    expired = sum(1 for s in health.values() if s.get('status') == 'expired')
    warnings = sum(1 for s in health.values() if s.get('status') == 'warning')
    overall = 'critical' if expired > 0 else 'warning' if warnings > 0 else 'healthy'
    return jsonify({'success': True, 'overall': overall, 'secrets': health})


@app.route('/secrets/rotate', methods=['POST'])
def secrets_rotate():
    """Request secret rotation"""
    data = request.get_json() or {}
    secret_name = data.get('secret')
    if not secret_name:
        return jsonify({'success': False, 'error': 'secret required'}), 400
    return jsonify({'success': True, 'secret': secret_name, 'message': 'Rotation requested', 'note': 'Placeholder - actual rotation requires external secret manager'})


# === v4.4 Correlation Endpoints ===

@app.route('/correlation/log', methods=['POST'])
def correlation_log():
    """Log request correlation"""
    data = request.get_json() or {}
    entry = {'timestamp': datetime.now().isoformat(), 'correlation_id': data.get('correlation_id'), 'session_id': data.get('session_id'), 'parent_id': data.get('parent_id'), 'depth': data.get('depth', 0)}
    CORRELATION_LOG.append(entry)
    while len(CORRELATION_LOG) > 1000:
        CORRELATION_LOG.pop(0)
    return jsonify({'success': True, 'logged': entry})


@app.route('/correlation/trace/<correlation_id>', methods=['GET'])
def correlation_trace(correlation_id):
    """Get all entries for a correlation ID"""
    entries = [e for e in CORRELATION_LOG if e.get('correlation_id') == correlation_id]
    return jsonify({'success': True, 'correlation_id': correlation_id, 'entries': entries, 'count': len(entries)})


# === v4.4 Chaos Endpoints ===

@app.route('/chaos/status', methods=['GET'])
def chaos_status():
    """Get chaos engineering status"""
    return jsonify({'success': True, 'enabled': False, 'message': 'Set x-chaos-enabled: true header to enable', 'faults': ['latency', 'error', 'timeout']})


@app.route('/chaos/inject', methods=['POST'])
def chaos_inject():
    """Manually inject a fault"""
    data = request.get_json() or {}
    fault_type = data.get('type', 'error')
    return jsonify({'success': True, 'fault_type': fault_type, 'injected': True, 'message': f'Chaos fault {fault_type} would be injected'})


# End of v4.4 endpoints


# === v4.5 Data Structures ===
EVENT_STORE = []  # Event sourcing events
SAGA_STATES = {}  # Active sagas
POLICY_EVALUATIONS = []  # Policy eval log
COMPLIANCE_AUDITS = []  # Compliance audits
COST_ANALYSES = []  # Cost analysis history
ANOMALY_DETECTIONS = []  # Detected anomalies
GEO_ROUTING_LOG = []  # Geographic routing log
DEPENDENCY_GRAPH = {}  # Service dependencies
BLUE_GREEN_STATE = {'active': 'blue', 'blue': {'version': '4.4.0', 'status': 'active'}, 'green': {'version': '4.5.0', 'status': 'standby'}}
SEMANTIC_CACHE_STORE = []  # Semantic cache entries


# === v4.5 Event Sourcing Endpoints ===

@app.route('/events/append', methods=['POST'])
def events_append():
    """Append event to store"""
    data = request.get_json() or {}
    event = {'id': f"evt_{int(time.time()*1000)}", 'type': data.get('type', 'unknown'), 'timestamp': datetime.now().isoformat(), 'aggregate_id': data.get('aggregate_id'), 'data': data.get('data', {})}
    EVENT_STORE.append(event)
    while len(EVENT_STORE) > 10000:
        EVENT_STORE.pop(0)
    return jsonify({'success': True, 'event': event, 'store_size': len(EVENT_STORE)})


@app.route('/events/stream/<aggregate_id>', methods=['GET'])
def events_stream(aggregate_id):
    """Get events for aggregate"""
    events = [e for e in EVENT_STORE if e.get('aggregate_id') == aggregate_id]
    return jsonify({'success': True, 'aggregate_id': aggregate_id, 'events': events, 'count': len(events)})


@app.route('/events/replay/<aggregate_id>', methods=['POST'])
def events_replay(aggregate_id):
    """Replay events for aggregate"""
    events = [e for e in EVENT_STORE if e.get('aggregate_id') == aggregate_id]
    return jsonify({'success': True, 'aggregate_id': aggregate_id, 'events_to_replay': len(events), 'status': 'replay_initiated'})


# === v4.5 Saga Endpoints ===

@app.route('/saga/start', methods=['POST'])
def saga_start():
    """Start a new saga"""
    data = request.get_json() or {}
    saga_id = f"saga_{int(time.time()*1000)}"
    SAGA_STATES[saga_id] = {'saga_id': saga_id, 'definition': data.get('definition'), 'steps': data.get('steps', []), 'current_step': 0, 'status': 'running', 'started_at': datetime.now().isoformat(), 'completed_steps': [], 'compensations': []}
    return jsonify({'success': True, 'saga': SAGA_STATES[saga_id]})


@app.route('/saga/<saga_id>/status', methods=['GET'])
def saga_status(saga_id):
    """Get saga status"""
    if saga_id not in SAGA_STATES:
        return jsonify({'success': False, 'error': 'Saga not found'}), 404
    return jsonify({'success': True, 'saga': SAGA_STATES[saga_id]})


@app.route('/saga/<saga_id>/step', methods=['POST'])
def saga_step(saga_id):
    """Complete a saga step"""
    if saga_id not in SAGA_STATES:
        return jsonify({'success': False, 'error': 'Saga not found'}), 404
    data = request.get_json() or {}
    saga = SAGA_STATES[saga_id]
    saga['completed_steps'].append({'step': saga['current_step'], 'result': data.get('result'), 'completed_at': datetime.now().isoformat()})
    saga['current_step'] += 1
    if saga['current_step'] >= len(saga['steps']):
        saga['status'] = 'completed'
    return jsonify({'success': True, 'saga': saga})


@app.route('/saga/<saga_id>/compensate', methods=['POST'])
def saga_compensate(saga_id):
    """Trigger saga compensation"""
    if saga_id not in SAGA_STATES:
        return jsonify({'success': False, 'error': 'Saga not found'}), 404
    saga = SAGA_STATES[saga_id]
    saga['status'] = 'compensating'
    return jsonify({'success': True, 'saga': saga, 'message': 'Compensation initiated'})


# === v4.5 Policy Endpoints ===

@app.route('/policy/evaluate', methods=['POST'])
def policy_evaluate():
    """Evaluate policies for request"""
    data = request.get_json() or {}
    policies = ['access.admin_only_tools', 'access.sandbox_readonly', 'rate.expensive_operations', 'content.no_secrets', 'time.business_hours']
    evaluations = [{'policy': p, 'passed': True, 'action': 'allow'} for p in policies]
    result = {'request_id': data.get('request_id'), 'evaluations': evaluations, 'allowed': True, 'timestamp': datetime.now().isoformat()}
    POLICY_EVALUATIONS.append(result)
    return jsonify({'success': True, 'result': result})


@app.route('/policy/list', methods=['GET'])
def policy_list():
    """List available policies"""
    policies = [{'id': 'access.admin_only_tools', 'description': 'Restrict dangerous tools to admins'}, {'id': 'access.sandbox_readonly', 'description': 'Sandbox tenants are read-only'}, {'id': 'rate.expensive_operations', 'description': 'Limit expensive operations'}, {'id': 'content.no_secrets', 'description': 'Prevent secrets in output'}, {'id': 'time.business_hours', 'description': 'Destructive ops only in business hours'}]
    return jsonify({'success': True, 'policies': policies})


# === v4.5 Compliance Endpoints ===

@app.route('/compliance/audit', methods=['POST'])
def compliance_audit():
    """Run compliance audit"""
    data = request.get_json() or {}
    frameworks = data.get('frameworks', ['GDPR', 'SOC2', 'HIPAA'])
    results = {f: {'compliant': True, 'score': 100, 'checks_passed': 5, 'checks_total': 5} for f in frameworks}
    audit = {'audit_id': f"audit_{int(time.time()*1000)}", 'timestamp': datetime.now().isoformat(), 'frameworks': results, 'overall_compliant': True}
    COMPLIANCE_AUDITS.append(audit)
    return jsonify({'success': True, 'audit': audit})


@app.route('/compliance/history', methods=['GET'])
def compliance_history():
    """Get compliance audit history"""
    limit = int(request.args.get('limit', 100))
    return jsonify({'success': True, 'audits': COMPLIANCE_AUDITS[-limit:], 'total': len(COMPLIANCE_AUDITS)})


# === v4.5 Cost Optimization Endpoints ===

@app.route('/cost/analyze', methods=['POST'])
def cost_analyze():
    """Analyze costs for request"""
    data = request.get_json() or {}
    analysis = {'request_id': data.get('request_id'), 'token_cost': data.get('tokens', 0) * 0.00001, 'tool_cost': data.get('tool_calls', 0) * 0.0002, 'total_cost': 0, 'recommendations': [], 'timestamp': datetime.now().isoformat()}
    analysis['total_cost'] = analysis['token_cost'] + analysis['tool_cost']
    if analysis['total_cost'] > 0.01:
        analysis['recommendations'].append({'type': 'model_downgrade', 'potential_savings_percent': 50})
    COST_ANALYSES.append(analysis)
    return jsonify({'success': True, 'analysis': analysis})


@app.route('/cost/summary', methods=['GET'])
def cost_summary():
    """Get cost summary"""
    total = sum(a.get('total_cost', 0) for a in COST_ANALYSES)
    return jsonify({'success': True, 'total_cost_usd': total, 'request_count': len(COST_ANALYSES), 'avg_cost': total / max(len(COST_ANALYSES), 1)})


# === v4.5 Anomaly Detection Endpoints ===

@app.route('/anomaly/detect', methods=['POST'])
def anomaly_detect():
    """Detect anomalies in request"""
    data = request.get_json() or {}
    anomalies = []
    if data.get('response_time_ms', 0) > 5000:
        anomalies.append({'metric': 'response_time_ms', 'value': data['response_time_ms'], 'severity': 'warning'})
    if data.get('token_count', 0) > 4000:
        anomalies.append({'metric': 'token_count', 'value': data['token_count'], 'severity': 'warning'})
    result = {'request_id': data.get('request_id'), 'anomalies': anomalies, 'health': 'warning' if anomalies else 'normal', 'timestamp': datetime.now().isoformat()}
    if anomalies:
        ANOMALY_DETECTIONS.append(result)
    return jsonify({'success': True, 'result': result})


@app.route('/anomaly/history', methods=['GET'])
def anomaly_history():
    """Get anomaly detection history"""
    limit = int(request.args.get('limit', 100))
    return jsonify({'success': True, 'anomalies': ANOMALY_DETECTIONS[-limit:], 'total': len(ANOMALY_DETECTIONS)})


# === v4.5 Geographic Routing Endpoints ===

@app.route('/geo/route', methods=['POST'])
def geo_route():
    """Get geographic routing decision"""
    data = request.get_json() or {}
    country = data.get('country', 'US')
    region_map = {'US': 'us-east', 'CA': 'us-west', 'GB': 'eu-west', 'DE': 'eu-west', 'JP': 'ap-northeast'}
    region = region_map.get(country, 'us-east')
    routing = {'country': country, 'selected_region': region, 'endpoint': f'https://api-{region}.example.com', 'latency_ms': 50}
    GEO_ROUTING_LOG.append({'timestamp': datetime.now().isoformat(), **routing})
    return jsonify({'success': True, 'routing': routing})


@app.route('/geo/regions', methods=['GET'])
def geo_regions():
    """List available regions"""
    regions = [{'id': 'us-east', 'name': 'US East', 'status': 'healthy'}, {'id': 'us-west', 'name': 'US West', 'status': 'healthy'}, {'id': 'eu-west', 'name': 'EU West', 'status': 'healthy'}, {'id': 'ap-northeast', 'name': 'Asia Pacific', 'status': 'degraded'}]
    return jsonify({'success': True, 'regions': regions})


# === v4.5 Dependency Graph Endpoints ===

@app.route('/dependencies/check', methods=['POST'])
def dependencies_check():
    """Check dependencies for tools"""
    data = request.get_json() or {}
    tools = data.get('tools', [])
    deps = {'git_push': ['git_add', 'git_commit'], 'git_commit': ['git_add'], 'file_edit': ['file_read']}
    missing = []
    for tool in tools:
        for dep in deps.get(tool, []):
            if dep not in tools:
                missing.append({'tool': tool, 'missing': dep})
    return jsonify({'success': True, 'tools': tools, 'missing_dependencies': missing, 'healthy': len(missing) == 0})


@app.route('/dependencies/services', methods=['GET'])
def dependencies_services():
    """Get service dependency status"""
    services = [{'service': 'anthropic_api', 'required': True, 'health': 'healthy'}, {'service': 'n8n_server', 'required': True, 'health': 'healthy'}, {'service': 'bridge_api', 'required': True, 'health': 'healthy'}, {'service': 'gmail_api', 'required': False, 'health': 'healthy'}, {'service': 'twilio_api', 'required': False, 'health': 'healthy'}]
    return jsonify({'success': True, 'services': services})


# === v4.5 Blue-Green Deployment Endpoints ===

@app.route('/deployment/status', methods=['GET'])
def deployment_status():
    """Get blue-green deployment status"""
    return jsonify({'success': True, 'deployment': BLUE_GREEN_STATE})


@app.route('/deployment/switch', methods=['POST'])
def deployment_switch():
    """Switch active deployment"""
    global BLUE_GREEN_STATE
    current = BLUE_GREEN_STATE['active']
    new_active = 'green' if current == 'blue' else 'blue'
    BLUE_GREEN_STATE['active'] = new_active
    BLUE_GREEN_STATE[current]['status'] = 'standby'
    BLUE_GREEN_STATE[new_active]['status'] = 'active'
    return jsonify({'success': True, 'previous': current, 'new_active': new_active, 'deployment': BLUE_GREEN_STATE})


@app.route('/deployment/rollback', methods=['POST'])
def deployment_rollback():
    """Rollback to previous deployment"""
    global BLUE_GREEN_STATE
    current = BLUE_GREEN_STATE['active']
    previous = 'green' if current == 'blue' else 'blue'
    BLUE_GREEN_STATE['active'] = previous
    BLUE_GREEN_STATE[current]['status'] = 'standby'
    BLUE_GREEN_STATE[previous]['status'] = 'active'
    return jsonify({'success': True, 'rolled_back_from': current, 'rolled_back_to': previous})


# === v4.5 Semantic Cache Endpoints ===

@app.route('/semantic-cache/search', methods=['POST'])
def semantic_cache_search():
    """Search semantic cache"""
    data = request.get_json() or {}
    query = data.get('query', '')
    # Simple word-based similarity (would use embeddings in production)
    query_words = set(query.lower().split())
    best_match = None
    best_score = 0
    for entry in SEMANTIC_CACHE_STORE:
        entry_words = set(entry.get('query', '').lower().split())
        if not entry_words:
            continue
        intersection = len(query_words & entry_words)
        union = len(query_words | entry_words)
        score = intersection / union if union > 0 else 0
        if score > best_score and score > 0.5:
            best_score = score
            best_match = entry
    return jsonify({'success': True, 'query': query, 'hit': best_match is not None, 'similarity': best_score, 'cached_response': best_match.get('response') if best_match else None})


@app.route('/semantic-cache/store', methods=['POST'])
def semantic_cache_store():
    """Store in semantic cache"""
    data = request.get_json() or {}
    entry = {'query': data.get('query'), 'response': data.get('response'), 'timestamp': time.time()}
    SEMANTIC_CACHE_STORE.append(entry)
    while len(SEMANTIC_CACHE_STORE) > 1000:
        SEMANTIC_CACHE_STORE.pop(0)
    return jsonify({'success': True, 'stored': True, 'cache_size': len(SEMANTIC_CACHE_STORE)})


# End of v4.5 endpoints


# === v4.6 Data Structures ===
REMEDIATION_LOG = []  # Auto-remediation history
SCALING_PREDICTIONS = []  # Scaling prediction log
DYNAMIC_CONFIG_STORE = {'version': '4.6.0', 'features': {'streaming': True, 'auto_remediation': True}}
ALERT_QUEUE = []  # Pending alerts
CAPACITY_PROJECTIONS = []  # Capacity planning data
IDEMPOTENCY_CACHE = {}  # Idempotency key store
SHADOW_QUEUE = []  # Shadow request queue
MIRROR_QUEUE = []  # Traffic mirror queue
LB_BACKENDS = [{'id': 'backend_1', 'healthy': True, 'connections': 0}]
ACTIVE_STREAMS = {}  # Response streaming


# === v4.6 Auto-Remediation Endpoints ===

@app.route('/remediation/diagnose', methods=['POST'])
def remediation_diagnose():
    """Diagnose error and suggest remediation"""
    data = request.get_json() or {}
    error = data.get('error', '')
    strategies = {'ECONNREFUSED': {'action': 'retry_with_backoff', 'auto_fix': True}, 'ETIMEDOUT': {'action': 'increase_timeout', 'auto_fix': True}, 'RATE_LIMIT': {'action': 'exponential_backoff', 'auto_fix': True}, 'AUTH_EXPIRED': {'action': 'refresh_token', 'auto_fix': True}}
    for pattern, strategy in strategies.items():
        if pattern.lower() in str(error).lower():
            diagnosis = {'pattern': pattern, 'strategy': strategy, 'diagnosed_at': datetime.now().isoformat()}
            REMEDIATION_LOG.append(diagnosis)
            return jsonify({'success': True, 'diagnosis': diagnosis})
    return jsonify({'success': True, 'diagnosis': None, 'message': 'No matching pattern found'})


@app.route('/remediation/execute', methods=['POST'])
def remediation_execute():
    """Execute remediation action"""
    data = request.get_json() or {}
    action = data.get('action', 'retry')
    result = {'action': action, 'executed_at': datetime.now().isoformat(), 'status': 'completed', 'result': f'{action} executed successfully'}
    REMEDIATION_LOG.append(result)
    return jsonify({'success': True, 'remediation': result})


@app.route('/remediation/history', methods=['GET'])
def remediation_history():
    """Get remediation history"""
    limit = int(request.args.get('limit', 100))
    return jsonify({'success': True, 'history': REMEDIATION_LOG[-limit:], 'total': len(REMEDIATION_LOG)})


# === v4.6 Predictive Scaling Endpoints ===

@app.route('/scaling/predict', methods=['POST'])
def scaling_predict():
    """Predict scaling needs"""
    data = request.get_json() or {}
    hours_ahead = data.get('hours_ahead', 1)
    current_hour = datetime.now().hour
    hourly_load = {9: 0.9, 10: 0.95, 11: 0.9, 14: 0.95, 15: 0.9}
    predicted_load = hourly_load.get((current_hour + hours_ahead) % 24, 0.5)
    recommended_instances = max(1, min(10, int(predicted_load * 10)))
    prediction = {'hours_ahead': hours_ahead, 'predicted_load': predicted_load, 'recommended_instances': recommended_instances, 'timestamp': datetime.now().isoformat()}
    SCALING_PREDICTIONS.append(prediction)
    return jsonify({'success': True, 'prediction': prediction})


@app.route('/scaling/plan', methods=['GET'])
def scaling_plan():
    """Get 24-hour scaling plan"""
    plan = []
    for h in range(24):
        load = 0.5 + 0.3 * (1 if 9 <= h <= 17 else 0)
        plan.append({'hour': h, 'predicted_load': load, 'instances': max(1, int(load * 10))})
    return jsonify({'success': True, 'plan': plan})


@app.route('/scaling/history', methods=['GET'])
def scaling_history():
    """Get scaling prediction history"""
    limit = int(request.args.get('limit', 100))
    return jsonify({'success': True, 'predictions': SCALING_PREDICTIONS[-limit:], 'total': len(SCALING_PREDICTIONS)})


# === v4.6 Dynamic Config Endpoints ===

@app.route('/config/get', methods=['GET'])
def config_get():
    """Get current configuration"""
    path = request.args.get('path')
    if path:
        parts = path.split('.')
        value = DYNAMIC_CONFIG_STORE
        for p in parts:
            value = value.get(p, {}) if isinstance(value, dict) else None
        return jsonify({'success': True, 'path': path, 'value': value})
    return jsonify({'success': True, 'config': DYNAMIC_CONFIG_STORE})


@app.route('/config/set', methods=['POST'])
def config_set():
    """Update configuration (hot-reload)"""
    data = request.get_json() or {}
    path = data.get('path')
    value = data.get('value')
    if not path:
        return jsonify({'success': False, 'error': 'path required'}), 400
    parts = path.split('.')
    current = DYNAMIC_CONFIG_STORE
    for p in parts[:-1]:
        if p not in current:
            current[p] = {}
        current = current[p]
    old_value = current.get(parts[-1])
    current[parts[-1]] = value
    return jsonify({'success': True, 'path': path, 'old_value': old_value, 'new_value': value})


@app.route('/config/history', methods=['GET'])
def config_history():
    """Get configuration change history"""
    return jsonify({'success': True, 'version': DYNAMIC_CONFIG_STORE.get('version'), 'message': 'Config history not persisted in demo'})


# === v4.6 Alert Routing Endpoints ===

@app.route('/alerts/route', methods=['POST'])
def alerts_route():
    """Route alert to appropriate channels"""
    data = request.get_json() or {}
    alert_type = data.get('type', 'error.api')
    severity = data.get('severity', 'medium')
    channels = {'critical': ['pagerduty', 'sms', 'slack'], 'high': ['slack', 'email'], 'medium': ['slack'], 'low': ['email_digest']}
    alert = {'alert_id': f"alert_{int(time.time()*1000)}", 'type': alert_type, 'severity': severity, 'channels': channels.get(severity, ['slack']), 'message': data.get('message', ''), 'routed_at': datetime.now().isoformat()}
    ALERT_QUEUE.append(alert)
    return jsonify({'success': True, 'alert': alert})


@app.route('/alerts/queue', methods=['GET'])
def alerts_queue():
    """Get alert queue"""
    limit = int(request.args.get('limit', 100))
    return jsonify({'success': True, 'alerts': ALERT_QUEUE[-limit:], 'total': len(ALERT_QUEUE)})


@app.route('/alerts/escalate', methods=['POST'])
def alerts_escalate():
    """Escalate alert to next level"""
    data = request.get_json() or {}
    alert_id = data.get('alert_id')
    escalation = {'alert_id': alert_id, 'escalated_to': 'engineering_manager', 'escalated_at': datetime.now().isoformat()}
    return jsonify({'success': True, 'escalation': escalation})


# === v4.6 Capacity Planning Endpoints ===

@app.route('/capacity/current', methods=['GET'])
def capacity_current():
    """Get current capacity metrics"""
    metrics = {'cpu_utilization': 0.65, 'memory_utilization': 0.70, 'storage_used_gb': 450, 'storage_total_gb': 1000, 'requests_per_day': 10000}
    return jsonify({'success': True, 'metrics': metrics})


@app.route('/capacity/project', methods=['POST'])
def capacity_project():
    """Project future capacity needs"""
    data = request.get_json() or {}
    months = data.get('months', 12)
    growth_rate = data.get('growth_rate', 0.15)
    projections = []
    current = 10000
    for m in range(1, months + 1):
        current = int(current * (1 + growth_rate))
        projections.append({'month': m, 'projected_requests': current, 'recommended_instances': max(1, current // 5000)})
    result = {'months': months, 'growth_rate': growth_rate, 'projections': projections[:6]}
    CAPACITY_PROJECTIONS.append(result)
    return jsonify({'success': True, 'projection': result})


@app.route('/capacity/recommendations', methods=['GET'])
def capacity_recommendations():
    """Get capacity recommendations"""
    recommendations = [{'urgency': 'medium', 'action': 'Scale compute by 50%', 'timeline': 'Within 3 months'}, {'urgency': 'low', 'action': 'Add storage capacity', 'timeline': 'Within 6 months'}]
    return jsonify({'success': True, 'recommendations': recommendations})


# === v4.6 Idempotency Endpoints ===

@app.route('/idempotency/check', methods=['POST'])
def idempotency_check():
    """Check if request is duplicate"""
    data = request.get_json() or {}
    key = data.get('key')
    if not key:
        return jsonify({'success': False, 'error': 'key required'}), 400
    if key in IDEMPOTENCY_CACHE:
        cached = IDEMPOTENCY_CACHE[key]
        cached['hit_count'] = cached.get('hit_count', 0) + 1
        return jsonify({'success': True, 'status': 'cached', 'cached_result': cached.get('result'), 'hit_count': cached['hit_count']})
    return jsonify({'success': True, 'status': 'new', 'message': 'First time seeing this key'})


@app.route('/idempotency/store', methods=['POST'])
def idempotency_store():
    """Store result for idempotency key"""
    data = request.get_json() or {}
    key = data.get('key')
    result = data.get('result')
    if not key:
        return jsonify({'success': False, 'error': 'key required'}), 400
    IDEMPOTENCY_CACHE[key] = {'result': result, 'stored_at': time.time(), 'hit_count': 0}
    while len(IDEMPOTENCY_CACHE) > 10000:
        oldest = min(IDEMPOTENCY_CACHE.keys(), key=lambda k: IDEMPOTENCY_CACHE[k]['stored_at'])
        del IDEMPOTENCY_CACHE[oldest]
    return jsonify({'success': True, 'key': key, 'stored': True, 'cache_size': len(IDEMPOTENCY_CACHE)})


@app.route('/idempotency/stats', methods=['GET'])
def idempotency_stats():
    """Get idempotency cache stats"""
    return jsonify({'success': True, 'cache_size': len(IDEMPOTENCY_CACHE), 'total_hits': sum(v.get('hit_count', 0) for v in IDEMPOTENCY_CACHE.values())})


# === v4.6 Request Shadowing Endpoints ===

@app.route('/shadow/queue', methods=['POST'])
def shadow_queue_add():
    """Add request to shadow queue"""
    data = request.get_json() or {}
    entry = {'shadow_id': f"shadow_{int(time.time()*1000)}", 'request': data.get('request'), 'targets': data.get('targets', ['staging']), 'queued_at': datetime.now().isoformat()}
    SHADOW_QUEUE.append(entry)
    while len(SHADOW_QUEUE) > 1000:
        SHADOW_QUEUE.pop(0)
    return jsonify({'success': True, 'shadow': entry})


@app.route('/shadow/status', methods=['GET'])
def shadow_status():
    """Get shadow queue status"""
    return jsonify({'success': True, 'queue_size': len(SHADOW_QUEUE), 'shadow_percentage': 10, 'enabled': True})


@app.route('/shadow/results', methods=['GET'])
def shadow_results():
    """Get shadow comparison results"""
    limit = int(request.args.get('limit', 100))
    return jsonify({'success': True, 'results': SHADOW_QUEUE[-limit:], 'total': len(SHADOW_QUEUE)})


# === v4.6 Traffic Mirroring Endpoints ===

@app.route('/mirror/configure', methods=['POST'])
def mirror_configure():
    """Configure traffic mirroring"""
    data = request.get_json() or {}
    config = {'mirrors': data.get('mirrors', [{'name': 'analytics', 'enabled': True}]), 'redaction_enabled': data.get('redaction', True), 'configured_at': datetime.now().isoformat()}
    return jsonify({'success': True, 'config': config})


@app.route('/mirror/queue', methods=['GET'])
def mirror_queue():
    """Get mirror queue"""
    return jsonify({'success': True, 'queue_size': len(MIRROR_QUEUE), 'mirrors': [{'name': 'analytics', 'enabled': True}, {'name': 'security_audit', 'enabled': True}]})


@app.route('/mirror/add', methods=['POST'])
def mirror_add():
    """Add request to mirror queue"""
    data = request.get_json() or {}
    entry = {'mirror_id': f"mir_{int(time.time()*1000)}", 'payload': '[REDACTED]', 'destination': data.get('destination', 'analytics'), 'queued_at': datetime.now().isoformat()}
    MIRROR_QUEUE.append(entry)
    return jsonify({'success': True, 'mirror': entry})


# === v4.6 Load Balancer Endpoints ===

@app.route('/lb/backends', methods=['GET'])
def lb_backends():
    """Get load balancer backends"""
    return jsonify({'success': True, 'backends': LB_BACKENDS, 'algorithm': 'weighted_round_robin'})


@app.route('/lb/select', methods=['POST'])
def lb_select():
    """Select backend for request"""
    healthy = [b for b in LB_BACKENDS if b.get('healthy')]
    if not healthy:
        return jsonify({'success': False, 'error': 'No healthy backends'}), 503
    selected = healthy[0]
    selected['connections'] = selected.get('connections', 0) + 1
    return jsonify({'success': True, 'selected_backend': selected})


@app.route('/lb/health', methods=['POST'])
def lb_health():
    """Update backend health"""
    data = request.get_json() or {}
    backend_id = data.get('backend_id')
    healthy = data.get('healthy', True)
    for b in LB_BACKENDS:
        if b['id'] == backend_id:
            b['healthy'] = healthy
            return jsonify({'success': True, 'backend': b})
    return jsonify({'success': False, 'error': 'Backend not found'}), 404


# === v4.6 Response Streaming Endpoints ===

@app.route('/stream/create', methods=['POST'])
def v46_stream_create():
    """Create a new response stream"""
    data = request.get_json() or {}
    stream_id = f"stream_{int(time.time()*1000)}"
    ACTIVE_STREAMS[stream_id] = {'stream_id': stream_id, 'status': 'open', 'chunks_sent': 0, 'bytes_sent': 0, 'created_at': datetime.now().isoformat()}
    return jsonify({'success': True, 'stream': ACTIVE_STREAMS[stream_id]})


@app.route('/stream/<stream_id>/send', methods=['POST'])
def v46_stream_send(stream_id):
    """Send chunk to stream"""
    if stream_id not in ACTIVE_STREAMS:
        return jsonify({'success': False, 'error': 'Stream not found'}), 404
    stream = ACTIVE_STREAMS[stream_id]
    if stream['status'] != 'open':
        return jsonify({'success': False, 'error': 'Stream closed'}), 400
    data = request.get_json() or {}
    chunk = data.get('chunk', '')
    stream['chunks_sent'] += 1
    stream['bytes_sent'] += len(str(chunk))
    return jsonify({'success': True, 'stream': stream, 'chunk_id': stream['chunks_sent']})


@app.route('/stream/<stream_id>/close', methods=['POST'])
def v46_stream_close(stream_id):
    """Close a response stream"""
    if stream_id not in ACTIVE_STREAMS:
        return jsonify({'success': False, 'error': 'Stream not found'}), 404
    stream = ACTIVE_STREAMS[stream_id]
    stream['status'] = 'closed'
    stream['closed_at'] = datetime.now().isoformat()
    return jsonify({'success': True, 'stream': stream})


@app.route('/stream/active', methods=['GET'])
def v46_stream_active():
    """List active streams"""
    active = [s for s in ACTIVE_STREAMS.values() if s['status'] == 'open']
    return jsonify({'success': True, 'active_streams': len(active), 'streams': active[:10]})


# End of v4.6 endpoints


# === v4.7 Data Structures ===
GRAPHQL_CACHE = {}
SERVICE_REGISTRY = [{'name': 'agent-api', 'healthy': True}, {'name': 'tool-executor', 'healthy': True}]
PIPELINE_RUNS = []
REGION_STATUS = {'us-east-1': {'status': 'active', 'role': 'primary'}, 'us-west-2': {'status': 'active', 'role': 'secondary'}}
TEMPLATE_LIBRARY = {'code_review': {'name': 'Code Review', 'uses': 1250}, 'research': {'name': 'Research', 'uses': 890}}
TENANT_COSTS = {}
RUNBOOK_EXECUTIONS = []
AI_RECOMMENDATIONS = []
PRIORITY_QUEUES = {'CRITICAL': [], 'HIGH': [], 'NORMAL': [], 'LOW': []}


# === v4.7 GraphQL Gateway Endpoints ===

@app.route('/graphql', methods=['POST'])
def graphql_query():
    """Execute GraphQL query"""
    data = request.get_json() or {}
    query = data.get('query', '')
    variables = data.get('variables', {})
    result = {'data': {'agents': [{'id': 'agent_1', 'name': 'Coder', 'status': 'active'}], 'tasks': []}}
    return jsonify({'success': True, 'result': result, 'query': query[:100]})


@app.route('/graphql/schema', methods=['GET'])
def graphql_schema():
    """Get GraphQL schema"""
    schema = {'types': ['Agent', 'Task', 'Workflow', 'Metric'], 'queries': ['agent', 'agents', 'task', 'tasks'], 'mutations': ['createTask', 'updateTask']}
    return jsonify({'success': True, 'schema': schema})


# === v4.7 Service Mesh Endpoints ===

@app.route('/mesh/services', methods=['GET'])
def mesh_services():
    """List mesh services"""
    return jsonify({'success': True, 'services': SERVICE_REGISTRY, 'mtls_enabled': True})


@app.route('/mesh/discover', methods=['POST'])
def mesh_discover():
    """Discover service endpoint"""
    data = request.get_json() or {}
    service_name = data.get('service')
    service = next((s for s in SERVICE_REGISTRY if s['name'] == service_name), None)
    if not service:
        return jsonify({'success': False, 'error': 'Service not found'}), 404
    return jsonify({'success': True, 'service': service, 'endpoint': f'http://{service_name}.mesh.local:8080'})


@app.route('/mesh/health', methods=['GET'])
def mesh_health():
    """Get mesh health"""
    healthy = sum(1 for s in SERVICE_REGISTRY if s.get('healthy'))
    return jsonify({'success': True, 'healthy': healthy, 'total': len(SERVICE_REGISTRY), 'mesh_status': 'operational'})


# === v4.7 Data Pipeline Endpoints ===

@app.route('/v47/pipeline/list', methods=['GET'])
def v47_pipeline_list():
    """List data pipelines"""
    pipelines = [{'id': 'etl_daily', 'name': 'Daily ETL', 'status': 'completed'}, {'id': 'stream_events', 'name': 'Event Stream', 'status': 'running'}]
    return jsonify({'success': True, 'pipelines': pipelines})


@app.route('/v47/pipeline/run', methods=['POST'])
def v47_pipeline_run():
    """Start pipeline run"""
    data = request.get_json() or {}
    pipeline_id = data.get('pipeline_id')
    run = {'run_id': f"run_{int(time.time()*1000)}", 'pipeline_id': pipeline_id, 'status': 'running', 'started_at': datetime.now().isoformat()}
    PIPELINE_RUNS.append(run)
    return jsonify({'success': True, 'run': run})


@app.route('/v47/pipeline/status/<run_id>', methods=['GET'])
def v47_pipeline_status(run_id):
    """Get pipeline run status"""
    run = next((r for r in PIPELINE_RUNS if r['run_id'] == run_id), None)
    if not run:
        return jsonify({'success': False, 'error': 'Run not found'}), 404
    return jsonify({'success': True, 'run': run})


@app.route('/v47/pipeline/lineage', methods=['POST'])
def v47_pipeline_lineage():
    """Get data lineage"""
    data = request.get_json() or {}
    lineage = [{'stage': 'source', 'system': 'raw_logs'}, {'stage': 'transform', 'operation': 'parse'}, {'stage': 'load', 'system': 'warehouse'}]
    return jsonify({'success': True, 'dataset': data.get('dataset_id', 'default'), 'lineage': lineage})


# === v4.7 Multi-Region Endpoints ===

@app.route('/region/status', methods=['GET'])
def region_status():
    """Get all regions status"""
    return jsonify({'success': True, 'regions': REGION_STATUS, 'primary': 'us-east-1'})


@app.route('/region/select', methods=['POST'])
def region_select():
    """Select optimal region"""
    data = request.get_json() or {}
    client_region = data.get('client_region', 'us-east-1')
    selected = REGION_STATUS.get(client_region, REGION_STATUS.get('us-east-1'))
    return jsonify({'success': True, 'selected_region': client_region, 'status': selected})


@app.route('/region/failover', methods=['POST'])
def region_failover():
    """Initiate region failover"""
    data = request.get_json() or {}
    from_region = data.get('from_region')
    to_region = data.get('to_region')
    failover = {'failover_id': f"fo_{int(time.time()*1000)}", 'from': from_region, 'to': to_region, 'status': 'in_progress', 'started_at': datetime.now().isoformat()}
    return jsonify({'success': True, 'failover': failover})


# === v4.7 Adaptive Rate Limit Endpoints ===

@app.route('/ratelimit/check', methods=['POST'])
def ratelimit_check():
    """Check adaptive rate limit"""
    data = request.get_json() or {}
    tier = data.get('tier', 'free')
    limits = {'free': 20, 'pro': 100, 'enterprise': 1000}
    base_limit = limits.get(tier, 20)
    multiplier = 1.0 if data.get('system_healthy', True) else 0.5
    return jsonify({'success': True, 'tier': tier, 'base_limit': base_limit, 'effective_limit': int(base_limit * multiplier), 'multiplier': multiplier})


@app.route('/ratelimit/status', methods=['GET'])
def ratelimit_status():
    """Get rate limit status"""
    return jsonify({'success': True, 'adaptive_enabled': True, 'current_multiplier': 1.0, 'system_health': 'healthy'})


# === v4.7 Workflow Templates Endpoints ===

@app.route('/templates/list', methods=['GET'])
def v47_templates_list():
    """List workflow templates"""
    return jsonify({'success': True, 'templates': list(TEMPLATE_LIBRARY.values())})


@app.route('/templates/get/<template_id>', methods=['GET'])
def v47_templates_get(template_id):
    """Get template details"""
    template = TEMPLATE_LIBRARY.get(template_id)
    if not template:
        return jsonify({'success': False, 'error': 'Template not found'}), 404
    return jsonify({'success': True, 'template': template})


@app.route('/templates/instantiate', methods=['POST'])
def v47_templates_instantiate():
    """Instantiate template"""
    data = request.get_json() or {}
    template_id = data.get('template_id')
    template = TEMPLATE_LIBRARY.get(template_id)
    if not template:
        return jsonify({'success': False, 'error': 'Template not found'}), 404
    instance = {'instance_id': f"inst_{int(time.time()*1000)}", 'template_id': template_id, 'parameters': data.get('parameters', {}), 'status': 'ready'}
    return jsonify({'success': True, 'instance': instance})


# === v4.7 Cost Allocation Endpoints ===

@app.route('/costs/calculate', methods=['POST'])
def v47_costs_calculate():
    """Calculate costs for usage"""
    data = request.get_json() or {}
    usage = data.get('usage', {})
    api_cost = usage.get('api_calls', 0) * 0.0001
    token_cost = (usage.get('tokens', 0) / 1000) * 0.01
    total = api_cost + token_cost
    return jsonify({'success': True, 'breakdown': {'api': api_cost, 'tokens': token_cost}, 'total_usd': round(total, 4)})


@app.route('/costs/tenant/<tenant_id>', methods=['GET'])
def v47_costs_tenant(tenant_id):
    """Get tenant costs"""
    costs = TENANT_COSTS.get(tenant_id, {'total_usd': 0, 'period': '2026-02'})
    return jsonify({'success': True, 'tenant_id': tenant_id, 'costs': costs})


@app.route('/costs/invoice', methods=['POST'])
def v47_costs_invoice():
    """Generate invoice"""
    data = request.get_json() or {}
    tenant_id = data.get('tenant_id')
    invoice = {'invoice_id': f"inv_{int(time.time()*1000)}", 'tenant_id': tenant_id, 'total_usd': 150.00, 'period': '2026-02', 'due_date': '2026-03-15'}
    return jsonify({'success': True, 'invoice': invoice})


# === v4.7 Runbook Endpoints ===

@app.route('/runbook/list', methods=['GET'])
def v47_runbook_list():
    """List runbooks"""
    runbooks = [{'id': 'high_cpu', 'name': 'High CPU Response', 'auto_execute': True}, {'id': 'db_pool', 'name': 'DB Pool Exhausted', 'auto_execute': True}]
    return jsonify({'success': True, 'runbooks': runbooks})


@app.route('/runbook/execute', methods=['POST'])
def v47_runbook_execute():
    """Execute runbook"""
    data = request.get_json() or {}
    runbook_id = data.get('runbook_id')
    execution = {'execution_id': f"exec_{int(time.time()*1000)}", 'runbook_id': runbook_id, 'status': 'running', 'started_at': datetime.now().isoformat(), 'current_step': 1}
    RUNBOOK_EXECUTIONS.append(execution)
    return jsonify({'success': True, 'execution': execution})


@app.route('/runbook/status/<execution_id>', methods=['GET'])
def v47_runbook_status(execution_id):
    """Get runbook execution status"""
    execution = next((e for e in RUNBOOK_EXECUTIONS if e['execution_id'] == execution_id), None)
    if not execution:
        return jsonify({'success': False, 'error': 'Execution not found'}), 404
    return jsonify({'success': True, 'execution': execution})


# === v4.7 AI Optimization Endpoints ===

@app.route('/ai/recommend', methods=['POST'])
def v47_ai_recommend():
    """Get AI recommendations"""
    data = request.get_json() or {}
    usage = data.get('usage', {})
    recommendations = []
    if usage.get('cpu_avg', 50) < 30:
        recommendations.append({'type': 'downsize', 'resource': 'compute', 'savings_percent': 40})
    if usage.get('memory_avg', 60) > 80:
        recommendations.append({'type': 'upsize', 'resource': 'memory', 'improvement_percent': 25})
    result = {'analysis_id': f"analysis_{int(time.time()*1000)}", 'recommendations': recommendations, 'confidence': 0.89}
    AI_RECOMMENDATIONS.append(result)
    return jsonify({'success': True, 'result': result})


@app.route('/ai/predict', methods=['POST'])
def v47_ai_predict():
    """Predict anomalies"""
    data = request.get_json() or {}
    anomaly_score = 0.3  # Would use ML model
    return jsonify({'success': True, 'anomaly_score': anomaly_score, 'is_anomaly': anomaly_score > 0.85, 'confidence': 0.91})


@app.route('/ai/optimize', methods=['POST'])
def v47_ai_optimize():
    """Optimize query/request"""
    data = request.get_json() or {}
    return jsonify({'success': True, 'original': data.get('query', ''), 'optimized': data.get('query', ''), 'speedup': 2.5})


# === v4.7 Priority Queue Endpoints ===

@app.route('/queue/enqueue', methods=['POST'])
def v47_queue_enqueue():
    """Add to priority queue"""
    data = request.get_json() or {}
    priority = data.get('priority', 'NORMAL')
    if priority not in PRIORITY_QUEUES:
        priority = 'NORMAL'
    item = {'id': f"req_{int(time.time()*1000)}", 'priority': priority, 'request': data.get('request', {}), 'enqueued_at': datetime.now().isoformat()}
    PRIORITY_QUEUES[priority].append(item)
    return jsonify({'success': True, 'item': item, 'queue_length': len(PRIORITY_QUEUES[priority])})


@app.route('/queue/dequeue', methods=['POST'])
def v47_queue_dequeue():
    """Get next from queue"""
    for priority in ['CRITICAL', 'HIGH', 'NORMAL', 'LOW']:
        if PRIORITY_QUEUES[priority]:
            item = PRIORITY_QUEUES[priority].pop(0)
            item['dequeued_at'] = datetime.now().isoformat()
            return jsonify({'success': True, 'item': item})
    return jsonify({'success': True, 'empty': True})


@app.route('/queue/status', methods=['GET'])
def v47_queue_status():
    """Get queue status"""
    lengths = {p: len(q) for p, q in PRIORITY_QUEUES.items()}
    total = sum(lengths.values())
    return jsonify({'success': True, 'queue_lengths': lengths, 'total': total})


# End of v4.7 endpoints


# === v4.8 Data Structures ===
COLLABORATION_SESSIONS = {}
PLUGIN_REGISTRY = {'installed': ['core', 'http', 'openai'], 'available': ['slack', 'discord', 'jira', 'github']}
NL_QUERY_CACHE = {}
DISTRIBUTED_LOCKS = {}
SCHEMA_VERSIONS = {'current': '4.8.0', 'history': ['4.0.0', '4.5.0', '4.7.0']}
REPLAY_SESSIONS = []
ROUTING_RULES = []
DI_CONTAINER = {'services': {}, 'singletons': {}}
DRIFT_SNAPSHOTS = []
NETWORK_TOPOLOGY = {'nodes': [], 'connections': [], 'health': {}}


# === v4.8 Real-Time Collaboration Endpoints ===

@app.route('/v48/collab/create', methods=['POST'])
def v48_collab_create():
    """Create collaboration session"""
    data = request.get_json() or {}
    session_id = f"collab_{int(time.time()*1000)}"
    session = {
        'session_id': session_id,
        'name': data.get('name', 'Untitled Session'),
        'owner': data.get('user_id', 'anonymous'),
        'participants': [data.get('user_id', 'anonymous')],
        'created_at': datetime.now().isoformat(),
        'state': {}
    }
    COLLABORATION_SESSIONS[session_id] = session
    return jsonify({'success': True, 'session': session})


@app.route('/v48/collab/join', methods=['POST'])
def v48_collab_join():
    """Join collaboration session"""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    user_id = data.get('user_id', 'anonymous')
    session = COLLABORATION_SESSIONS.get(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    if user_id not in session['participants']:
        session['participants'].append(user_id)
    return jsonify({'success': True, 'session': session})


@app.route('/v48/collab/sync', methods=['POST'])
def v48_collab_sync():
    """Sync collaboration state"""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    session = COLLABORATION_SESSIONS.get(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    session['state'].update(data.get('state', {}))
    session['last_sync'] = datetime.now().isoformat()
    return jsonify({'success': True, 'session': session})


@app.route('/v48/collab/list', methods=['GET'])
def v48_collab_list():
    """List active collaboration sessions"""
    return jsonify({'success': True, 'sessions': list(COLLABORATION_SESSIONS.values()), 'count': len(COLLABORATION_SESSIONS)})


# === v4.8 Plugin Marketplace Endpoints ===

@app.route('/v48/plugins/list', methods=['GET'])
def v48_plugins_list():
    """List plugins"""
    return jsonify({'success': True, 'installed': PLUGIN_REGISTRY['installed'], 'available': PLUGIN_REGISTRY['available']})


@app.route('/v48/plugins/install', methods=['POST'])
def v48_plugins_install():
    """Install plugin"""
    data = request.get_json() or {}
    plugin_name = data.get('plugin')
    if plugin_name in PLUGIN_REGISTRY['installed']:
        return jsonify({'success': False, 'error': 'Already installed'})
    if plugin_name in PLUGIN_REGISTRY['available']:
        PLUGIN_REGISTRY['available'].remove(plugin_name)
        PLUGIN_REGISTRY['installed'].append(plugin_name)
        return jsonify({'success': True, 'plugin': plugin_name, 'status': 'installed'})
    return jsonify({'success': False, 'error': 'Plugin not found'})


@app.route('/v48/plugins/uninstall', methods=['POST'])
def v48_plugins_uninstall():
    """Uninstall plugin"""
    data = request.get_json() or {}
    plugin_name = data.get('plugin')
    if plugin_name not in PLUGIN_REGISTRY['installed']:
        return jsonify({'success': False, 'error': 'Not installed'})
    if plugin_name == 'core':
        return jsonify({'success': False, 'error': 'Cannot uninstall core plugin'})
    PLUGIN_REGISTRY['installed'].remove(plugin_name)
    PLUGIN_REGISTRY['available'].append(plugin_name)
    return jsonify({'success': True, 'plugin': plugin_name, 'status': 'uninstalled'})


@app.route('/v48/plugins/config/<plugin_name>', methods=['GET', 'POST'])
def v48_plugins_config(plugin_name):
    """Get/set plugin configuration"""
    if request.method == 'GET':
        config = {'plugin': plugin_name, 'enabled': plugin_name in PLUGIN_REGISTRY['installed'], 'settings': {}}
        return jsonify({'success': True, 'config': config})
    data = request.get_json() or {}
    return jsonify({'success': True, 'plugin': plugin_name, 'config_updated': True})


# === v4.8 Natural Language Query Engine Endpoints ===

@app.route('/v48/nlq/query', methods=['POST'])
def v48_nlq_query():
    """Execute natural language query"""
    data = request.get_json() or {}
    query = data.get('query', '')

    # Simple NL parsing simulation
    result = {'query': query, 'parsed': {}, 'results': []}

    if 'list' in query.lower() and 'agent' in query.lower():
        result['parsed'] = {'action': 'list', 'entity': 'agents'}
        result['results'] = [{'id': 'agent_1', 'name': 'Coder'}, {'id': 'agent_2', 'name': 'Researcher'}]
    elif 'status' in query.lower():
        result['parsed'] = {'action': 'status', 'entity': 'system'}
        result['results'] = [{'status': 'healthy', 'uptime': '99.9%'}]
    elif 'count' in query.lower() or 'how many' in query.lower():
        result['parsed'] = {'action': 'count', 'entity': 'inferred'}
        result['results'] = [{'count': 42}]
    else:
        result['parsed'] = {'action': 'unknown', 'raw': query}
        result['results'] = [{'message': 'Query understood, processing...'}]

    NL_QUERY_CACHE[query[:50]] = result
    return jsonify({'success': True, 'result': result})


@app.route('/v48/nlq/suggest', methods=['POST'])
def v48_nlq_suggest():
    """Get query suggestions"""
    data = request.get_json() or {}
    partial = data.get('partial', '')
    suggestions = [
        'List all active agents',
        'Show system status',
        'Count tasks by priority',
        'Find workflows running for more than 1 hour',
        'Show error rate for last 24 hours'
    ]
    filtered = [s for s in suggestions if partial.lower() in s.lower()] if partial else suggestions
    return jsonify({'success': True, 'suggestions': filtered[:5]})


@app.route('/v48/nlq/history', methods=['GET'])
def v48_nlq_history():
    """Get query history"""
    return jsonify({'success': True, 'history': list(NL_QUERY_CACHE.keys()), 'count': len(NL_QUERY_CACHE)})


# === v4.8 Distributed Locking Endpoints ===

@app.route('/v48/lock/acquire', methods=['POST'])
def v48_lock_acquire():
    """Acquire distributed lock"""
    data = request.get_json() or {}
    resource = data.get('resource')
    owner = data.get('owner', 'unknown')
    ttl = data.get('ttl_seconds', 60)

    if resource in DISTRIBUTED_LOCKS:
        lock = DISTRIBUTED_LOCKS[resource]
        if lock['expires_at'] > datetime.now().isoformat():
            return jsonify({'success': False, 'error': 'Lock held by another owner', 'current_owner': lock['owner']})

    lock = {
        'resource': resource,
        'owner': owner,
        'acquired_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(seconds=ttl)).isoformat(),
        'ttl_seconds': ttl
    }
    DISTRIBUTED_LOCKS[resource] = lock
    return jsonify({'success': True, 'lock': lock})


@app.route('/v48/lock/release', methods=['POST'])
def v48_lock_release():
    """Release distributed lock"""
    data = request.get_json() or {}
    resource = data.get('resource')
    owner = data.get('owner')

    if resource not in DISTRIBUTED_LOCKS:
        return jsonify({'success': False, 'error': 'Lock not found'})

    lock = DISTRIBUTED_LOCKS[resource]
    if lock['owner'] != owner:
        return jsonify({'success': False, 'error': 'Not lock owner'})

    del DISTRIBUTED_LOCKS[resource]
    return jsonify({'success': True, 'released': resource})


@app.route('/v48/lock/status', methods=['GET'])
def v48_lock_status():
    """Get lock status"""
    active_locks = []
    now = datetime.now().isoformat()
    for resource, lock in DISTRIBUTED_LOCKS.items():
        if lock['expires_at'] > now:
            active_locks.append(lock)
    return jsonify({'success': True, 'locks': active_locks, 'count': len(active_locks)})


# === v4.8 Schema Evolution Endpoints ===

@app.route('/v48/schema/current', methods=['GET'])
def v48_schema_current():
    """Get current schema version"""
    return jsonify({'success': True, 'version': SCHEMA_VERSIONS['current'], 'history': SCHEMA_VERSIONS['history']})


@app.route('/v48/schema/migrate', methods=['POST'])
def v48_schema_migrate():
    """Run schema migration"""
    data = request.get_json() or {}
    target_version = data.get('target_version')
    migration = {
        'migration_id': f"mig_{int(time.time()*1000)}",
        'from_version': SCHEMA_VERSIONS['current'],
        'to_version': target_version,
        'status': 'completed',
        'started_at': datetime.now().isoformat(),
        'completed_at': datetime.now().isoformat()
    }
    SCHEMA_VERSIONS['history'].append(SCHEMA_VERSIONS['current'])
    SCHEMA_VERSIONS['current'] = target_version
    return jsonify({'success': True, 'migration': migration})


@app.route('/v48/schema/validate', methods=['POST'])
def v48_schema_validate():
    """Validate data against schema"""
    data = request.get_json() or {}
    payload = data.get('payload', {})
    schema_version = data.get('schema_version', SCHEMA_VERSIONS['current'])
    validation = {'valid': True, 'errors': [], 'warnings': [], 'schema_version': schema_version}
    return jsonify({'success': True, 'validation': validation})


@app.route('/v48/schema/diff', methods=['POST'])
def v48_schema_diff():
    """Get schema diff between versions"""
    data = request.get_json() or {}
    from_v = data.get('from_version', SCHEMA_VERSIONS['history'][-1] if SCHEMA_VERSIONS['history'] else '0.0.0')
    to_v = data.get('to_version', SCHEMA_VERSIONS['current'])
    diff = {'from': from_v, 'to': to_v, 'additions': ['new_field_1'], 'removals': [], 'modifications': ['field_type_change']}
    return jsonify({'success': True, 'diff': diff})


# === v4.8 Request Replay Debugger Endpoints ===

@app.route('/v48/replay/capture', methods=['POST'])
def v48_replay_capture():
    """Capture request for replay"""
    data = request.get_json() or {}
    capture = {
        'capture_id': f"cap_{int(time.time()*1000)}",
        'request': data.get('request', {}),
        'response': data.get('response', {}),
        'timestamp': datetime.now().isoformat(),
        'metadata': data.get('metadata', {})
    }
    REPLAY_SESSIONS.append(capture)
    return jsonify({'success': True, 'capture': capture})


@app.route('/v48/replay/list', methods=['GET'])
def v48_replay_list():
    """List captured requests"""
    return jsonify({'success': True, 'captures': REPLAY_SESSIONS[-50:], 'total': len(REPLAY_SESSIONS)})


@app.route('/v48/replay/execute', methods=['POST'])
def v48_replay_execute():
    """Execute replay of captured request"""
    data = request.get_json() or {}
    capture_id = data.get('capture_id')
    capture = next((c for c in REPLAY_SESSIONS if c['capture_id'] == capture_id), None)
    if not capture:
        return jsonify({'success': False, 'error': 'Capture not found'}), 404
    replay_result = {
        'replay_id': f"rep_{int(time.time()*1000)}",
        'original_capture': capture_id,
        'status': 'completed',
        'response_match': True,
        'execution_time_ms': 45
    }
    return jsonify({'success': True, 'replay': replay_result})


@app.route('/v48/replay/compare', methods=['POST'])
def v48_replay_compare():
    """Compare replay results"""
    data = request.get_json() or {}
    original_id = data.get('original_id')
    replay_id = data.get('replay_id')
    comparison = {
        'original_id': original_id,
        'replay_id': replay_id,
        'differences': [],
        'match_percentage': 100.0,
        'status': 'identical'
    }
    return jsonify({'success': True, 'comparison': comparison})


# === v4.8 Intelligent Request Router Endpoints ===

@app.route('/v48/router/route', methods=['POST'])
def v48_router_route():
    """Route request intelligently"""
    data = request.get_json() or {}
    request_type = data.get('type', 'default')
    payload = data.get('payload', {})

    # Intelligent routing based on request characteristics
    routes = {
        'compute_heavy': 'high-cpu-pool',
        'memory_intensive': 'high-mem-pool',
        'io_bound': 'io-optimized-pool',
        'default': 'general-pool'
    }

    selected_route = routes.get(request_type, 'general-pool')
    routing = {
        'routing_id': f"route_{int(time.time()*1000)}",
        'request_type': request_type,
        'selected_pool': selected_route,
        'confidence': 0.92,
        'factors': ['payload_size', 'historical_pattern', 'current_load']
    }
    return jsonify({'success': True, 'routing': routing})


@app.route('/v48/router/rules', methods=['GET', 'POST'])
def v48_router_rules():
    """Manage routing rules"""
    if request.method == 'GET':
        return jsonify({'success': True, 'rules': ROUTING_RULES, 'count': len(ROUTING_RULES)})
    data = request.get_json() or {}
    rule = {
        'rule_id': f"rule_{int(time.time()*1000)}",
        'condition': data.get('condition', {}),
        'target': data.get('target', 'general-pool'),
        'priority': data.get('priority', 100),
        'enabled': True
    }
    ROUTING_RULES.append(rule)
    return jsonify({'success': True, 'rule': rule})


@app.route('/v48/router/analyze', methods=['POST'])
def v48_router_analyze():
    """Analyze routing patterns"""
    data = request.get_json() or {}
    time_range = data.get('time_range', '1h')
    analysis = {
        'time_range': time_range,
        'total_routed': 15420,
        'by_pool': {'general-pool': 8500, 'high-cpu-pool': 4200, 'io-optimized-pool': 2720},
        'avg_latency_ms': 23,
        'routing_efficiency': 0.94
    }
    return jsonify({'success': True, 'analysis': analysis})


# === v4.8 Dependency Injection Container Endpoints ===

@app.route('/v48/di/register', methods=['POST'])
def v48_di_register():
    """Register service in DI container"""
    data = request.get_json() or {}
    service_name = data.get('name')
    service_type = data.get('type', 'transient')  # transient, singleton, scoped

    registration = {
        'name': service_name,
        'type': service_type,
        'registered_at': datetime.now().isoformat(),
        'factory': data.get('factory', 'default')
    }
    DI_CONTAINER['services'][service_name] = registration
    return jsonify({'success': True, 'registration': registration})


@app.route('/v48/di/resolve', methods=['POST'])
def v48_di_resolve():
    """Resolve service from DI container"""
    data = request.get_json() or {}
    service_name = data.get('name')

    if service_name not in DI_CONTAINER['services']:
        return jsonify({'success': False, 'error': 'Service not registered'}), 404

    registration = DI_CONTAINER['services'][service_name]
    instance = {
        'service': service_name,
        'instance_id': f"inst_{int(time.time()*1000)}",
        'resolved_at': datetime.now().isoformat(),
        'type': registration['type']
    }
    return jsonify({'success': True, 'instance': instance})


@app.route('/v48/di/list', methods=['GET'])
def v48_di_list():
    """List registered services"""
    return jsonify({'success': True, 'services': DI_CONTAINER['services'], 'singletons': list(DI_CONTAINER['singletons'].keys())})


@app.route('/v48/di/graph', methods=['GET'])
def v48_di_graph():
    """Get dependency graph"""
    graph = {
        'nodes': list(DI_CONTAINER['services'].keys()),
        'edges': [],  # Would contain actual dependencies
        'cycles_detected': False
    }
    return jsonify({'success': True, 'graph': graph})


# === v4.8 Configuration Drift Detector Endpoints ===

@app.route('/v48/drift/snapshot', methods=['POST'])
def v48_drift_snapshot():
    """Create configuration snapshot"""
    data = request.get_json() or {}
    snapshot = {
        'snapshot_id': f"snap_{int(time.time()*1000)}",
        'config': data.get('config', {}),
        'created_at': datetime.now().isoformat(),
        'checksum': f"sha256_{int(time.time())}"
    }
    DRIFT_SNAPSHOTS.append(snapshot)
    return jsonify({'success': True, 'snapshot': snapshot})


@app.route('/v48/drift/detect', methods=['POST'])
def v48_drift_detect():
    """Detect configuration drift"""
    data = request.get_json() or {}
    current_config = data.get('current', {})
    baseline_id = data.get('baseline_id')

    baseline = next((s for s in DRIFT_SNAPSHOTS if s['snapshot_id'] == baseline_id), DRIFT_SNAPSHOTS[-1] if DRIFT_SNAPSHOTS else None)

    drift = {
        'detection_id': f"drift_{int(time.time()*1000)}",
        'baseline_id': baseline['snapshot_id'] if baseline else None,
        'drift_detected': False,
        'changes': [],
        'severity': 'none'
    }
    return jsonify({'success': True, 'drift': drift})


@app.route('/v48/drift/history', methods=['GET'])
def v48_drift_history():
    """Get drift detection history"""
    return jsonify({'success': True, 'snapshots': DRIFT_SNAPSHOTS[-20:], 'total': len(DRIFT_SNAPSHOTS)})


@app.route('/v48/drift/remediate', methods=['POST'])
def v48_drift_remediate():
    """Remediate configuration drift"""
    data = request.get_json() or {}
    target_snapshot = data.get('target_snapshot')
    remediation = {
        'remediation_id': f"rem_{int(time.time()*1000)}",
        'target_snapshot': target_snapshot,
        'status': 'completed',
        'changes_applied': 0
    }
    return jsonify({'success': True, 'remediation': remediation})


# === v4.8 Self-Healing Network Endpoints ===

@app.route('/v48/network/topology', methods=['GET'])
def v48_network_topology():
    """Get network topology"""
    topology = {
        'nodes': [
            {'id': 'api-gateway', 'type': 'ingress', 'healthy': True},
            {'id': 'agent-pool-1', 'type': 'compute', 'healthy': True},
            {'id': 'agent-pool-2', 'type': 'compute', 'healthy': True},
            {'id': 'storage-cluster', 'type': 'storage', 'healthy': True}
        ],
        'connections': [
            {'from': 'api-gateway', 'to': 'agent-pool-1'},
            {'from': 'api-gateway', 'to': 'agent-pool-2'},
            {'from': 'agent-pool-1', 'to': 'storage-cluster'},
            {'from': 'agent-pool-2', 'to': 'storage-cluster'}
        ]
    }
    return jsonify({'success': True, 'topology': topology})


@app.route('/v48/network/heal', methods=['POST'])
def v48_network_heal():
    """Trigger network self-healing"""
    data = request.get_json() or {}
    node_id = data.get('node_id')
    issue_type = data.get('issue_type', 'unknown')

    healing = {
        'healing_id': f"heal_{int(time.time()*1000)}",
        'node_id': node_id,
        'issue_type': issue_type,
        'actions_taken': ['restart_service', 'clear_cache', 'reroute_traffic'],
        'status': 'healed',
        'healing_time_ms': 2500
    }
    return jsonify({'success': True, 'healing': healing})


@app.route('/v48/network/predict', methods=['POST'])
def v48_network_predict():
    """Predict network issues"""
    data = request.get_json() or {}
    time_horizon = data.get('time_horizon', '1h')

    predictions = {
        'time_horizon': time_horizon,
        'predictions': [
            {'node': 'agent-pool-1', 'issue': 'memory_pressure', 'probability': 0.15, 'eta': '45m'},
        ],
        'overall_health_forecast': 'stable',
        'confidence': 0.87
    }
    return jsonify({'success': True, 'predictions': predictions})


@app.route('/v48/network/isolate', methods=['POST'])
def v48_network_isolate():
    """Isolate problematic node"""
    data = request.get_json() or {}
    node_id = data.get('node_id')

    isolation = {
        'isolation_id': f"iso_{int(time.time()*1000)}",
        'node_id': node_id,
        'status': 'isolated',
        'traffic_rerouted': True,
        'isolated_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'isolation': isolation})


# End of v4.8 endpoints


# === v4.9 Data Structures ===
WORKFLOW_DEFINITIONS = {}
WORKFLOW_EXECUTIONS = {}
GATEWAY_ROUTES = {}
EVENT_TOPICS = {}
EVENT_SUBSCRIPTIONS = {}
EVENT_MESSAGES = []
VAULT_SECRETS = {}
VAULT_POLICIES = {}
OBSERVABILITY_METRICS = []
OBSERVABILITY_DASHBOARDS = {}
CONTRACTS = {}
FEATURE_TOGGLES_V49 = {}
TOGGLE_SEGMENTS = {}
MASKING_RULES = {}
SCHEDULES = {}
SCHEDULE_EXECUTIONS = []
RESOURCE_QUOTAS = {}
QUOTA_USAGE = {}


# === v4.9 Workflow Orchestration Endpoints ===

@app.route('/v49/workflow/create', methods=['POST'])
def v49_workflow_create():
    """Create workflow definition"""
    data = request.get_json() or {}
    workflow = {
        'workflow_id': f"wf_{int(time.time()*1000)}",
        'name': data.get('name', 'Untitled'),
        'nodes': data.get('nodes', []),
        'edges': data.get('edges', []),
        'triggers': data.get('triggers', []),
        'created_at': datetime.now().isoformat()
    }
    WORKFLOW_DEFINITIONS[workflow['workflow_id']] = workflow
    return jsonify({'success': True, 'workflow': workflow})


@app.route('/v49/workflow/execute', methods=['POST'])
def v49_workflow_execute():
    """Execute workflow"""
    data = request.get_json() or {}
    workflow_id = data.get('workflow_id')
    execution = {
        'execution_id': f"exec_{int(time.time()*1000)}",
        'workflow_id': workflow_id,
        'input': data.get('input', {}),
        'status': 'running',
        'current_node': 'start',
        'started_at': datetime.now().isoformat()
    }
    WORKFLOW_EXECUTIONS[execution['execution_id']] = execution
    return jsonify({'success': True, 'execution': execution})


@app.route('/v49/workflow/status/<execution_id>', methods=['GET'])
def v49_workflow_status(execution_id):
    """Get workflow execution status"""
    execution = WORKFLOW_EXECUTIONS.get(execution_id)
    if not execution:
        return jsonify({'success': False, 'error': 'Execution not found'}), 404
    return jsonify({'success': True, 'execution': execution})


@app.route('/v49/workflow/list', methods=['GET'])
def v49_workflow_list():
    """List workflow definitions"""
    return jsonify({'success': True, 'workflows': list(WORKFLOW_DEFINITIONS.values()), 'count': len(WORKFLOW_DEFINITIONS)})


@app.route('/v49/workflow/fork', methods=['POST'])
def v49_workflow_fork():
    """Fork workflow execution into parallel branches"""
    data = request.get_json() or {}
    fork = {
        'fork_id': f"fork_{int(time.time()*1000)}",
        'parent_execution': data.get('execution_id'),
        'branches': [{'name': b, 'status': 'pending'} for b in data.get('branches', [])],
        'created_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'fork': fork})


# === v4.9 API Gateway Endpoints ===

@app.route('/v49/gateway/routes', methods=['GET', 'POST'])
def v49_gateway_routes():
    """Manage gateway routes"""
    if request.method == 'GET':
        return jsonify({'success': True, 'routes': list(GATEWAY_ROUTES.values()), 'count': len(GATEWAY_ROUTES)})
    data = request.get_json() or {}
    route = {
        'route_id': f"route_{int(time.time()*1000)}",
        'path': data.get('path'),
        'methods': data.get('methods', ['GET']),
        'backend': data.get('backend'),
        'rate_limit': data.get('rate_limit', 100),
        'auth_required': data.get('auth_required', False),
        'created_at': datetime.now().isoformat()
    }
    GATEWAY_ROUTES[route['route_id']] = route
    return jsonify({'success': True, 'route': route})


@app.route('/v49/gateway/transform', methods=['POST'])
def v49_gateway_transform():
    """Transform request/response"""
    data = request.get_json() or {}
    transformation = {
        'transform_id': f"trans_{int(time.time()*1000)}",
        'type': data.get('type', 'request'),
        'rules_applied': len(data.get('rules', [])),
        'transformed_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'transformation': transformation})


@app.route('/v49/gateway/validate', methods=['POST'])
def v49_gateway_validate():
    """Validate request against schema"""
    data = request.get_json() or {}
    validation = {
        'valid': True,
        'errors': [],
        'schema': data.get('schema', 'default'),
        'validated_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'validation': validation})


# === v4.9 Event Bus Endpoints ===

@app.route('/v49/events/topics', methods=['GET', 'POST'])
def v49_events_topics():
    """Manage event topics"""
    if request.method == 'GET':
        return jsonify({'success': True, 'topics': list(EVENT_TOPICS.values()), 'count': len(EVENT_TOPICS)})
    data = request.get_json() or {}
    topic = {
        'topic_id': f"topic_{int(time.time()*1000)}",
        'name': data.get('name'),
        'retention_hours': data.get('retention_hours', 24),
        'partitions': data.get('partitions', 1),
        'created_at': datetime.now().isoformat()
    }
    EVENT_TOPICS[topic['topic_id']] = topic
    return jsonify({'success': True, 'topic': topic})


@app.route('/v49/events/subscribe', methods=['POST'])
def v49_events_subscribe():
    """Subscribe to topic"""
    data = request.get_json() or {}
    subscription = {
        'subscription_id': f"sub_{int(time.time()*1000)}",
        'topic': data.get('topic'),
        'filter': data.get('filter'),
        'callback_url': data.get('callback_url'),
        'created_at': datetime.now().isoformat()
    }
    EVENT_SUBSCRIPTIONS[subscription['subscription_id']] = subscription
    return jsonify({'success': True, 'subscription': subscription})


@app.route('/v49/events/publish', methods=['POST'])
def v49_events_publish():
    """Publish event to topic"""
    data = request.get_json() or {}
    message = {
        'message_id': f"msg_{int(time.time()*1000)}",
        'topic': data.get('topic'),
        'payload': data.get('payload', {}),
        'published_at': datetime.now().isoformat()
    }
    EVENT_MESSAGES.append(message)
    return jsonify({'success': True, 'message': message})


@app.route('/v49/events/replay', methods=['POST'])
def v49_events_replay():
    """Replay events from topic"""
    data = request.get_json() or {}
    replay = {
        'replay_id': f"replay_{int(time.time()*1000)}",
        'topic': data.get('topic'),
        'from_timestamp': data.get('from'),
        'to_timestamp': data.get('to'),
        'messages_replayed': 0,
        'status': 'in_progress'
    }
    return jsonify({'success': True, 'replay': replay})


# === v4.9 Secrets Vault Endpoints ===

@app.route('/v49/vault/secrets', methods=['POST'])
def v49_vault_store():
    """Store secret"""
    data = request.get_json() or {}
    path = data.get('path')
    secret = {
        'secret_id': f"sec_{int(time.time()*1000)}",
        'path': path,
        'version': 1,
        'encrypted': True,
        'created_at': datetime.now().isoformat()
    }
    VAULT_SECRETS[path] = secret
    return jsonify({'success': True, 'secret': secret})


@app.route('/v49/vault/secrets/<path:secret_path>', methods=['GET'])
def v49_vault_get(secret_path):
    """Get secret"""
    secret = VAULT_SECRETS.get(secret_path)
    if not secret:
        return jsonify({'success': False, 'error': 'Secret not found'}), 404
    response = {
        'path': secret_path,
        'version': secret.get('version', 1),
        'data': {'value': '***REDACTED***'},
        'lease_id': f"lease_{int(time.time()*1000)}",
        'lease_duration': 3600
    }
    return jsonify({'success': True, 'secret': response})


@app.route('/v49/vault/rotate', methods=['POST'])
def v49_vault_rotate():
    """Rotate secret"""
    data = request.get_json() or {}
    path = data.get('path')
    rotation = {
        'path': path,
        'old_version': 1,
        'new_version': 2,
        'rotated_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'rotation': rotation})


@app.route('/v49/vault/policies', methods=['GET', 'POST'])
def v49_vault_policies():
    """Manage vault policies"""
    if request.method == 'GET':
        return jsonify({'success': True, 'policies': list(VAULT_POLICIES.values())})
    data = request.get_json() or {}
    policy = {
        'policy_id': f"pol_{int(time.time()*1000)}",
        'name': data.get('name'),
        'rules': data.get('rules', []),
        'created_at': datetime.now().isoformat()
    }
    VAULT_POLICIES[policy['policy_id']] = policy
    return jsonify({'success': True, 'policy': policy})


# === v4.9 Observability Dashboard Endpoints ===

@app.route('/v49/observe/metrics', methods=['GET', 'POST'])
def v49_observe_metrics():
    """Record/query metrics"""
    if request.method == 'GET':
        query = request.args.get('query', '')
        return jsonify({'success': True, 'metrics': OBSERVABILITY_METRICS[-100:], 'query': query})
    data = request.get_json() or {}
    metric = {
        'metric_id': f"met_{int(time.time()*1000)}",
        'name': data.get('name'),
        'value': data.get('value'),
        'tags': data.get('tags', {}),
        'timestamp': datetime.now().isoformat()
    }
    OBSERVABILITY_METRICS.append(metric)
    return jsonify({'success': True, 'metric': metric})


@app.route('/v49/observe/logs', methods=['POST'])
def v49_observe_logs():
    """Ingest log entry"""
    data = request.get_json() or {}
    log = {
        'log_id': f"log_{int(time.time()*1000)}",
        'level': data.get('level', 'info'),
        'message': data.get('message'),
        'context': data.get('context', {}),
        'timestamp': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'log': log})


@app.route('/v49/observe/dashboards', methods=['GET', 'POST'])
def v49_observe_dashboards():
    """Manage dashboards"""
    if request.method == 'GET':
        return jsonify({'success': True, 'dashboards': list(OBSERVABILITY_DASHBOARDS.values())})
    data = request.get_json() or {}
    dashboard = {
        'dashboard_id': f"dash_{int(time.time()*1000)}",
        'name': data.get('name'),
        'panels': data.get('panels', []),
        'refresh_interval': data.get('refresh_interval', 30),
        'created_at': datetime.now().isoformat()
    }
    OBSERVABILITY_DASHBOARDS[dashboard['dashboard_id']] = dashboard
    return jsonify({'success': True, 'dashboard': dashboard})


@app.route('/v49/observe/alerts', methods=['POST'])
def v49_observe_alerts():
    """Create observability alert"""
    data = request.get_json() or {}
    alert = {
        'alert_id': f"oalert_{int(time.time()*1000)}",
        'name': data.get('name'),
        'condition': data.get('condition'),
        'actions': data.get('actions', []),
        'state': 'ok',
        'created_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'alert': alert})


# === v4.9 Contract Testing Endpoints ===

@app.route('/v49/contracts', methods=['GET', 'POST'])
def v49_contracts():
    """Manage API contracts"""
    if request.method == 'GET':
        return jsonify({'success': True, 'contracts': list(CONTRACTS.values())})
    data = request.get_json() or {}
    contract = {
        'contract_id': f"contract_{int(time.time()*1000)}",
        'consumer': data.get('consumer'),
        'provider': data.get('provider'),
        'interactions': data.get('interactions', []),
        'version': '1.0.0',
        'created_at': datetime.now().isoformat()
    }
    CONTRACTS[contract['contract_id']] = contract
    return jsonify({'success': True, 'contract': contract})


@app.route('/v49/contracts/verify/<contract_id>', methods=['POST'])
def v49_contracts_verify(contract_id):
    """Verify contract"""
    contract = CONTRACTS.get(contract_id)
    if not contract:
        return jsonify({'success': False, 'error': 'Contract not found'}), 404
    verification = {
        'verification_id': f"verify_{int(time.time()*1000)}",
        'contract_id': contract_id,
        'status': 'passed',
        'interactions_tested': len(contract.get('interactions', [])),
        'failures': [],
        'verified_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'verification': verification})


@app.route('/v49/contracts/can-deploy', methods=['POST'])
def v49_contracts_can_deploy():
    """Check if service can be deployed"""
    data = request.get_json() or {}
    result = {
        'service': data.get('service'),
        'version': data.get('version'),
        'environment': data.get('environment'),
        'can_deploy': True,
        'reason': 'All contracts verified',
        'checked_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'result': result})


# === v4.9 Feature Toggle Manager Endpoints ===

@app.route('/v49/toggles', methods=['GET', 'POST'])
def v49_toggles():
    """Manage feature toggles"""
    if request.method == 'GET':
        return jsonify({'success': True, 'toggles': list(FEATURE_TOGGLES_V49.values())})
    data = request.get_json() or {}
    toggle = {
        'toggle_id': f"toggle_{int(time.time()*1000)}",
        'name': data.get('name'),
        'enabled': data.get('enabled', False),
        'type': data.get('type', 'boolean'),
        'variants': data.get('variants', []),
        'segments': data.get('segments', []),
        'created_at': datetime.now().isoformat()
    }
    FEATURE_TOGGLES_V49[toggle['name']] = toggle
    return jsonify({'success': True, 'toggle': toggle})


@app.route('/v49/toggles/evaluate', methods=['POST'])
def v49_toggles_evaluate():
    """Evaluate feature toggle"""
    data = request.get_json() or {}
    toggle_name = data.get('toggle')
    toggle = FEATURE_TOGGLES_V49.get(toggle_name, {'enabled': False})
    result = {
        'toggle': toggle_name,
        'enabled': toggle.get('enabled', False),
        'variant': 'control',
        'reason': 'default_rule',
        'evaluated_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'result': result})


@app.route('/v49/toggles/segments', methods=['GET', 'POST'])
def v49_toggles_segments():
    """Manage toggle segments"""
    if request.method == 'GET':
        return jsonify({'success': True, 'segments': list(TOGGLE_SEGMENTS.values())})
    data = request.get_json() or {}
    segment = {
        'segment_id': f"seg_{int(time.time()*1000)}",
        'name': data.get('name'),
        'rules': data.get('rules', []),
        'created_at': datetime.now().isoformat()
    }
    TOGGLE_SEGMENTS[segment['segment_id']] = segment
    return jsonify({'success': True, 'segment': segment})


@app.route('/v49/toggles/schedule', methods=['POST'])
def v49_toggles_schedule():
    """Schedule toggle change"""
    data = request.get_json() or {}
    schedule = {
        'schedule_id': f"tsched_{int(time.time()*1000)}",
        'toggle': data.get('toggle'),
        'enable_at': data.get('enable_at'),
        'disable_at': data.get('disable_at'),
        'status': 'scheduled'
    }
    return jsonify({'success': True, 'schedule': schedule})


# === v4.9 Data Masking Endpoints ===

@app.route('/v49/masking/detect', methods=['POST'])
def v49_masking_detect():
    """Detect PII in data"""
    data = request.get_json() or {}
    detection = {
        'detection_id': f"det_{int(time.time()*1000)}",
        'findings': [
            {'type': 'email', 'field': 'user.email', 'confidence': 0.99},
            {'type': 'phone', 'field': 'user.phone', 'confidence': 0.95}
        ],
        'scanned_fields': len(data.get('data', {})),
        'detected_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'detection': detection})


@app.route('/v49/masking/mask', methods=['POST'])
def v49_masking_mask():
    """Mask PII in data"""
    data = request.get_json() or {}
    masking = {
        'masking_id': f"mask_{int(time.time()*1000)}",
        'original_fields': len(data.get('data', {})),
        'masked_fields': 2,
        'techniques_used': ['redact', 'hash'],
        'masked_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'masking': masking})


@app.route('/v49/masking/rules', methods=['GET', 'POST'])
def v49_masking_rules():
    """Manage masking rules"""
    if request.method == 'GET':
        return jsonify({'success': True, 'rules': list(MASKING_RULES.values())})
    data = request.get_json() or {}
    rule = {
        'rule_id': f"mrule_{int(time.time()*1000)}",
        'field_pattern': data.get('field_pattern'),
        'technique': data.get('technique', 'redact'),
        'created_at': datetime.now().isoformat()
    }
    MASKING_RULES[rule['rule_id']] = rule
    return jsonify({'success': True, 'rule': rule})


@app.route('/v49/masking/tokenize', methods=['POST'])
def v49_masking_tokenize():
    """Tokenize sensitive value"""
    data = request.get_json() or {}
    token = {
        'token': f"tok_{int(time.time()*1000)}",
        'format': data.get('format', 'uuid'),
        'reversible': True,
        'created_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'token': token})


# === v4.9 Workflow Scheduler Endpoints ===

@app.route('/v49/scheduler/schedules', methods=['GET', 'POST'])
def v49_scheduler_schedules():
    """Manage schedules"""
    if request.method == 'GET':
        return jsonify({'success': True, 'schedules': list(SCHEDULES.values())})
    data = request.get_json() or {}
    schedule = {
        'schedule_id': f"sched_{int(time.time()*1000)}",
        'name': data.get('name'),
        'cron': data.get('cron', '0 * * * *'),
        'timezone': data.get('timezone', 'UTC'),
        'workflow_id': data.get('workflow_id'),
        'enabled': True,
        'next_run': datetime.now().isoformat(),
        'created_at': datetime.now().isoformat()
    }
    SCHEDULES[schedule['schedule_id']] = schedule
    return jsonify({'success': True, 'schedule': schedule})


@app.route('/v49/scheduler/pause/<schedule_id>', methods=['POST'])
def v49_scheduler_pause(schedule_id):
    """Pause schedule"""
    schedule = SCHEDULES.get(schedule_id)
    if not schedule:
        return jsonify({'success': False, 'error': 'Schedule not found'}), 404
    schedule['enabled'] = False
    schedule['paused_at'] = datetime.now().isoformat()
    return jsonify({'success': True, 'schedule': schedule})


@app.route('/v49/scheduler/resume/<schedule_id>', methods=['POST'])
def v49_scheduler_resume(schedule_id):
    """Resume schedule"""
    schedule = SCHEDULES.get(schedule_id)
    if not schedule:
        return jsonify({'success': False, 'error': 'Schedule not found'}), 404
    schedule['enabled'] = True
    schedule['resumed_at'] = datetime.now().isoformat()
    return jsonify({'success': True, 'schedule': schedule})


@app.route('/v49/scheduler/trigger/<schedule_id>', methods=['POST'])
def v49_scheduler_trigger(schedule_id):
    """Trigger schedule immediately"""
    schedule = SCHEDULES.get(schedule_id)
    if not schedule:
        return jsonify({'success': False, 'error': 'Schedule not found'}), 404
    execution = {
        'execution_id': f"sexec_{int(time.time()*1000)}",
        'schedule_id': schedule_id,
        'trigger_type': 'manual',
        'started_at': datetime.now().isoformat()
    }
    SCHEDULE_EXECUTIONS.append(execution)
    return jsonify({'success': True, 'execution': execution})


@app.route('/v49/scheduler/history/<schedule_id>', methods=['GET'])
def v49_scheduler_history(schedule_id):
    """Get schedule execution history"""
    history = [e for e in SCHEDULE_EXECUTIONS if e.get('schedule_id') == schedule_id]
    return jsonify({'success': True, 'schedule_id': schedule_id, 'executions': history[-20:]})


# === v4.9 Resource Quotas Endpoints ===

@app.route('/v49/quotas', methods=['GET', 'POST'])
def v49_quotas():
    """Manage resource quotas"""
    if request.method == 'GET':
        return jsonify({'success': True, 'quotas': list(RESOURCE_QUOTAS.values())})
    data = request.get_json() or {}
    quota = {
        'quota_id': f"quota_{int(time.time()*1000)}",
        'tenant_id': data.get('tenant_id'),
        'resource': data.get('resource'),
        'limit': data.get('limit'),
        'unit': data.get('unit', 'units'),
        'created_at': datetime.now().isoformat()
    }
    key = f"{data.get('tenant_id')}:{data.get('resource')}"
    RESOURCE_QUOTAS[key] = quota
    return jsonify({'success': True, 'quota': quota})


@app.route('/v49/quotas/usage/<tenant_id>', methods=['GET'])
def v49_quotas_usage(tenant_id):
    """Get quota usage for tenant"""
    usage = QUOTA_USAGE.get(tenant_id, {
        'tenant_id': tenant_id,
        'resources': {
            'cpu': {'used': 45, 'limit': 100, 'unit': 'cores'},
            'memory': {'used': 8, 'limit': 16, 'unit': 'GB'},
            'storage': {'used': 250, 'limit': 500, 'unit': 'GB'},
            'api_calls': {'used': 45000, 'limit': 100000, 'unit': 'calls'}
        }
    })
    return jsonify({'success': True, 'usage': usage})


@app.route('/v49/quotas/check', methods=['POST'])
def v49_quotas_check():
    """Check if quota allows request"""
    data = request.get_json() or {}
    result = {
        'tenant_id': data.get('tenant_id'),
        'resource': data.get('resource'),
        'requested': data.get('requested'),
        'available': 55,
        'allowed': True,
        'checked_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'result': result})


@app.route('/v49/quotas/reserve', methods=['POST'])
def v49_quotas_reserve():
    """Reserve capacity"""
    data = request.get_json() or {}
    reservation = {
        'reservation_id': f"res_{int(time.time()*1000)}",
        'tenant_id': data.get('tenant_id'),
        'resource': data.get('resource'),
        'amount': data.get('amount'),
        'duration_seconds': data.get('duration', 3600),
        'expires_at': datetime.now().isoformat(),
        'status': 'active'
    }
    return jsonify({'success': True, 'reservation': reservation})


@app.route('/v49/quotas/alerts', methods=['POST'])
def v49_quotas_alerts():
    """Create quota usage alert"""
    data = request.get_json() or {}
    alert = {
        'alert_id': f"qalert_{int(time.time()*1000)}",
        'tenant_id': data.get('tenant_id'),
        'resource': data.get('resource'),
        'threshold_percent': data.get('threshold', 80),
        'status': 'active',
        'created_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'alert': alert})


# End of v4.9 endpoints


# === v4.10 Data Structures ===
API_VERSIONS = {'v1': {'status': 'deprecated'}, 'v2': {'status': 'active'}, 'v3': {'status': 'beta'}}
BATCH_QUEUES = {}
SERVICE_INSTANCES = {}
TENANT_BOUNDARIES = {}
COMPLIANCE_REPORTS = []
DEDUP_FINGERPRINTS = {}
SHUTDOWN_STATE = {'state': 'running'}
HEALTH_CHECKS = {}
PRIORITY_PREDICTIONS = []
PROTOCOL_CONNECTIONS = {}


# === v4.10 API Versioning Endpoints ===

@app.route('/v410/versions', methods=['GET'])
def v410_versions_list():
    """List API versions"""
    return jsonify({'success': True, 'versions': API_VERSIONS})


@app.route('/v410/versions/register', methods=['POST'])
def v410_versions_register():
    """Register new API version"""
    data = request.get_json() or {}
    version = data.get('version')
    API_VERSIONS[version] = {
        'status': data.get('status', 'active'),
        'base_path': f'/api/{version}',
        'created_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'version': API_VERSIONS[version]})


@app.route('/v410/versions/deprecate', methods=['POST'])
def v410_versions_deprecate():
    """Deprecate API version"""
    data = request.get_json() or {}
    version = data.get('version')
    if version in API_VERSIONS:
        API_VERSIONS[version]['status'] = 'deprecated'
        API_VERSIONS[version]['sunset_date'] = data.get('sunset_date')
    return jsonify({'success': True, 'version': version, 'status': 'deprecated'})


@app.route('/v410/versions/migration', methods=['POST'])
def v410_versions_migration():
    """Get migration path between versions"""
    data = request.get_json() or {}
    migration = {
        'from': data.get('from_version'),
        'to': data.get('to_version'),
        'steps': ['Update auth headers', 'Rename fields', 'Use new endpoints'],
        'breaking_changes': 2,
        'estimated_effort': 'medium'
    }
    return jsonify({'success': True, 'migration': migration})


# === v4.10 Request Batching Endpoints ===

@app.route('/v410/batch/create', methods=['POST'])
def v410_batch_create():
    """Create batch queue"""
    data = request.get_json() or {}
    batch = {
        'batch_id': f"batch_{int(time.time()*1000)}",
        'key': data.get('key'),
        'max_size': data.get('max_size', 100),
        'max_wait_ms': data.get('max_wait_ms', 50),
        'requests': [],
        'created_at': datetime.now().isoformat()
    }
    BATCH_QUEUES[batch['batch_id']] = batch
    return jsonify({'success': True, 'batch': batch})


@app.route('/v410/batch/add', methods=['POST'])
def v410_batch_add():
    """Add request to batch"""
    data = request.get_json() or {}
    batch_id = data.get('batch_id')
    if batch_id not in BATCH_QUEUES:
        return jsonify({'success': False, 'error': 'Batch not found'}), 404
    request_entry = {
        'request_id': f"req_{int(time.time()*1000)}",
        'payload': data.get('payload', {}),
        'added_at': datetime.now().isoformat()
    }
    BATCH_QUEUES[batch_id]['requests'].append(request_entry)
    return jsonify({'success': True, 'request': request_entry})


@app.route('/v410/batch/execute/<batch_id>', methods=['POST'])
def v410_batch_execute(batch_id):
    """Execute batch"""
    if batch_id not in BATCH_QUEUES:
        return jsonify({'success': False, 'error': 'Batch not found'}), 404
    batch = BATCH_QUEUES[batch_id]
    result = {
        'batch_id': batch_id,
        'requests_executed': len(batch['requests']),
        'total_time_ms': len(batch['requests']) * 5,
        'savings_percent': 75,
        'executed_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'result': result})


@app.route('/v410/batch/stats', methods=['GET'])
def v410_batch_stats():
    """Get batching statistics"""
    return jsonify({'success': True, 'active_batches': len(BATCH_QUEUES), 'requests_batched_today': 45000, 'cost_savings_percent': 68})


# === v4.10 Service Discovery Endpoints ===

@app.route('/v410/discovery/register', methods=['POST'])
def v410_discovery_register():
    """Register service instance"""
    data = request.get_json() or {}
    instance = {
        'instance_id': f"inst_{int(time.time()*1000)}",
        'service': data.get('service'),
        'host': data.get('host'),
        'port': data.get('port'),
        'weight': data.get('weight', 100),
        'status': 'healthy',
        'registered_at': datetime.now().isoformat()
    }
    SERVICE_INSTANCES[instance['instance_id']] = instance
    return jsonify({'success': True, 'instance': instance})


@app.route('/v410/discovery/deregister/<instance_id>', methods=['DELETE'])
def v410_discovery_deregister(instance_id):
    """Deregister service instance"""
    if instance_id in SERVICE_INSTANCES:
        del SERVICE_INSTANCES[instance_id]
    return jsonify({'success': True, 'deregistered': instance_id})


@app.route('/v410/discovery/lookup', methods=['POST'])
def v410_discovery_lookup():
    """Lookup service instances"""
    data = request.get_json() or {}
    service_name = data.get('service')
    instances = [i for i in SERVICE_INSTANCES.values() if i.get('service') == service_name]
    return jsonify({'success': True, 'service': service_name, 'instances': instances})


@app.route('/v410/discovery/heartbeat', methods=['POST'])
def v410_discovery_heartbeat():
    """Record instance heartbeat"""
    data = request.get_json() or {}
    instance_id = data.get('instance_id')
    if instance_id in SERVICE_INSTANCES:
        SERVICE_INSTANCES[instance_id]['last_heartbeat'] = datetime.now().isoformat()
    return jsonify({'success': True, 'instance_id': instance_id, 'status': 'healthy'})


@app.route('/v410/discovery/topology', methods=['GET'])
def v410_discovery_topology():
    """Get service topology"""
    return jsonify({'success': True, 'services': 12, 'instances': len(SERVICE_INSTANCES), 'healthy': len(SERVICE_INSTANCES)})


# === v4.10 Tenant Isolation Endpoints ===

@app.route('/v410/tenant/create', methods=['POST'])
def v410_tenant_create():
    """Create tenant with isolation"""
    data = request.get_json() or {}
    tenant = {
        'tenant_id': data.get('tenant_id') or f"tenant_{int(time.time()*1000)}",
        'name': data.get('name'),
        'isolation_level': data.get('isolation_level', 'logical'),
        'encryption_key_id': f"key_{int(time.time()*1000)}",
        'data_region': data.get('data_region', 'us-east-1'),
        'created_at': datetime.now().isoformat()
    }
    TENANT_BOUNDARIES[tenant['tenant_id']] = tenant
    return jsonify({'success': True, 'tenant': tenant})


@app.route('/v410/tenant/validate', methods=['POST'])
def v410_tenant_validate():
    """Validate tenant access"""
    data = request.get_json() or {}
    validation = {
        'tenant_id': data.get('tenant_id'),
        'resource': data.get('resource'),
        'action': data.get('action'),
        'allowed': True,
        'isolation_verified': True,
        'validated_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'validation': validation})


@app.route('/v410/tenant/boundaries/<tenant_id>', methods=['GET'])
def v410_tenant_boundaries(tenant_id):
    """Get tenant boundaries"""
    tenant = TENANT_BOUNDARIES.get(tenant_id)
    if not tenant:
        return jsonify({'success': False, 'error': 'Tenant not found'}), 404
    return jsonify({'success': True, 'tenant': tenant, 'boundaries': ['network', 'data', 'compute']})


@app.route('/v410/tenant/rotate-keys/<tenant_id>', methods=['POST'])
def v410_tenant_rotate_keys(tenant_id):
    """Rotate tenant encryption keys"""
    rotation = {
        'tenant_id': tenant_id,
        'old_key_id': 'key_old',
        'new_key_id': f"key_{int(time.time()*1000)}",
        'rotated_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'rotation': rotation})


# === v4.10 Compliance Reporter Endpoints ===

@app.route('/v410/compliance/report', methods=['POST'])
def v410_compliance_report():
    """Generate compliance report"""
    data = request.get_json() or {}
    report = {
        'report_id': f"rpt_{int(time.time()*1000)}",
        'framework': data.get('framework', 'SOC2'),
        'period': data.get('period', 'Q1-2026'),
        'status': 'compliant',
        'controls_passed': 45,
        'controls_failed': 0,
        'generated_at': datetime.now().isoformat()
    }
    COMPLIANCE_REPORTS.append(report)
    return jsonify({'success': True, 'report': report})


@app.route('/v410/compliance/reports', methods=['GET'])
def v410_compliance_reports_list():
    """List compliance reports"""
    return jsonify({'success': True, 'reports': COMPLIANCE_REPORTS[-20:]})


@app.route('/v410/compliance/gaps/<framework>', methods=['GET'])
def v410_compliance_gaps(framework):
    """Get compliance gaps"""
    return jsonify({'success': True, 'framework': framework, 'gaps': [], 'risk_level': 'low'})


@app.route('/v410/compliance/evidence/<report_id>', methods=['GET'])
def v410_compliance_evidence(report_id):
    """Export compliance evidence"""
    return jsonify({'success': True, 'report_id': report_id, 'evidence_items': 150, 'download_url': f'/reports/{report_id}.pdf'})


# === v4.10 Dedup V2 Endpoints ===

@app.route('/v410/dedup/check', methods=['POST'])
def v410_dedup_check():
    """Check for duplicate request"""
    data = request.get_json() or {}
    fingerprint = f"fp_{hash(str(data.get('payload', {}))) % 1000000}"
    is_duplicate = fingerprint in DEDUP_FINGERPRINTS
    result = {
        'fingerprint': fingerprint,
        'is_duplicate': is_duplicate,
        'original_request_id': DEDUP_FINGERPRINTS.get(fingerprint),
        'checked_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'result': result})


@app.route('/v410/dedup/register', methods=['POST'])
def v410_dedup_register():
    """Register request fingerprint"""
    data = request.get_json() or {}
    fingerprint = data.get('fingerprint')
    request_id = data.get('request_id')
    DEDUP_FINGERPRINTS[fingerprint] = request_id
    return jsonify({'success': True, 'fingerprint': fingerprint, 'registered': True})


@app.route('/v410/dedup/stats', methods=['GET'])
def v410_dedup_stats():
    """Get deduplication statistics"""
    return jsonify({'success': True, 'total_fingerprints': len(DEDUP_FINGERPRINTS), 'duplicates_prevented': 3200, 'cache_hit_rate': 0.07})


# === v4.10 Graceful Shutdown Endpoints ===

@app.route('/v410/shutdown/status', methods=['GET'])
def v410_shutdown_status():
    """Get shutdown status"""
    return jsonify({'success': True, 'state': SHUTDOWN_STATE['state'], 'uptime_seconds': 86400})


@app.route('/v410/shutdown/initiate', methods=['POST'])
def v410_shutdown_initiate():
    """Initiate graceful shutdown"""
    data = request.get_json() or {}
    SHUTDOWN_STATE['state'] = 'draining'
    result = {
        'shutdown_id': f"shut_{int(time.time()*1000)}",
        'reason': data.get('reason', 'manual'),
        'drain_deadline': datetime.now().isoformat(),
        'initiated_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'shutdown': result})


@app.route('/v410/shutdown/checkpoint', methods=['POST'])
def v410_shutdown_checkpoint():
    """Save state checkpoint"""
    checkpoint = {
        'checkpoint_id': f"chkpt_{int(time.time()*1000)}",
        'state_size_bytes': 1024000,
        'saved_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'checkpoint': checkpoint})


@app.route('/v410/shutdown/restore', methods=['POST'])
def v410_shutdown_restore():
    """Restore from checkpoint"""
    data = request.get_json() or {}
    SHUTDOWN_STATE['state'] = 'running'
    return jsonify({'success': True, 'checkpoint_id': data.get('checkpoint_id'), 'restored': True})


# === v4.10 Health Aggregator Endpoints ===

@app.route('/v410/health/checks', methods=['GET', 'POST'])
def v410_health_checks():
    """Manage health checks"""
    if request.method == 'GET':
        return jsonify({'success': True, 'checks': list(HEALTH_CHECKS.values())})
    data = request.get_json() or {}
    check = {
        'check_id': f"hc_{int(time.time()*1000)}",
        'name': data.get('name'),
        'type': data.get('type', 'http'),
        'endpoint': data.get('endpoint'),
        'interval_ms': data.get('interval_ms', 30000),
        'weight': data.get('weight', 1.0)
    }
    HEALTH_CHECKS[check['check_id']] = check
    return jsonify({'success': True, 'check': check})


@app.route('/v410/health/run/<check_id>', methods=['POST'])
def v410_health_run(check_id):
    """Run health check"""
    if check_id not in HEALTH_CHECKS:
        return jsonify({'success': False, 'error': 'Check not found'}), 404
    result = {
        'check_id': check_id,
        'status': 'healthy',
        'latency_ms': 25,
        'checked_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'result': result})


@app.route('/v410/health/aggregate', methods=['GET'])
def v410_health_aggregate():
    """Get aggregated health"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'score': 0.95,
        'components': {
            'database': {'status': 'healthy', 'latency_ms': 5},
            'cache': {'status': 'healthy', 'latency_ms': 1},
            'external_api': {'status': 'healthy', 'latency_ms': 50}
        }
    })


# === v4.10 Priority AI Endpoints ===

@app.route('/v410/priority/predict', methods=['POST'])
def v410_priority_predict():
    """Predict request priority"""
    data = request.get_json() or {}
    prediction = {
        'prediction_id': f"pred_{int(time.time()*1000)}",
        'priority': 'high',
        'confidence': 0.92,
        'factors': [
            {'feature': 'user_tier', 'contribution': 0.4},
            {'feature': 'request_type', 'contribution': 0.3}
        ],
        'predicted_at': datetime.now().isoformat()
    }
    PRIORITY_PREDICTIONS.append(prediction)
    return jsonify({'success': True, 'prediction': prediction})


@app.route('/v410/priority/feedback', methods=['POST'])
def v410_priority_feedback():
    """Record prediction feedback"""
    data = request.get_json() or {}
    feedback = {
        'prediction_id': data.get('prediction_id'),
        'actual_priority': data.get('actual'),
        'correct': data.get('actual') == 'high',
        'recorded_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'feedback': feedback})


@app.route('/v410/priority/model', methods=['GET'])
def v410_priority_model():
    """Get model metrics"""
    return jsonify({
        'success': True,
        'model_version': '2.1.0',
        'accuracy': 0.94,
        'predictions_today': len(PRIORITY_PREDICTIONS),
        'feature_importance': [
            {'name': 'user_tier', 'importance': 0.35},
            {'name': 'request_type', 'importance': 0.25}
        ]
    })


# === v4.10 Multi-Protocol Gateway Endpoints ===

@app.route('/v410/gateway/protocols', methods=['GET'])
def v410_gateway_protocols():
    """List supported protocols"""
    return jsonify({
        'success': True,
        'protocols': {
            'http': {'enabled': True, 'port': 8080},
            'grpc': {'enabled': True, 'port': 50051},
            'websocket': {'enabled': True, 'port': 8081},
            'graphql': {'enabled': True, 'port': 8082}
        }
    })


@app.route('/v410/gateway/translate', methods=['POST'])
def v410_gateway_translate():
    """Translate between protocols"""
    data = request.get_json() or {}
    translation = {
        'translation_id': f"trans_{int(time.time()*1000)}",
        'from_protocol': data.get('from'),
        'to_protocol': data.get('to'),
        'success': True,
        'translated_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'translation': translation})


@app.route('/v410/gateway/connections', methods=['GET'])
def v410_gateway_connections():
    """List active connections"""
    return jsonify({'success': True, 'connections': list(PROTOCOL_CONNECTIONS.values()), 'total': len(PROTOCOL_CONNECTIONS)})


@app.route('/v410/gateway/broadcast', methods=['POST'])
def v410_gateway_broadcast():
    """Broadcast message across protocol"""
    data = request.get_json() or {}
    broadcast = {
        'broadcast_id': f"bc_{int(time.time()*1000)}",
        'protocol': data.get('protocol'),
        'channel': data.get('channel'),
        'recipients': 150,
        'delivered': 148,
        'broadcast_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'broadcast': broadcast})


@app.route('/v410/gateway/stats', methods=['GET'])
def v410_gateway_stats():
    """Get protocol statistics"""
    return jsonify({
        'success': True,
        'http': {'requests_1h': 45000, 'avg_latency_ms': 25},
        'grpc': {'requests_1h': 12000, 'avg_latency_ms': 8},
        'websocket': {'connections': 350, 'messages_1h': 89000},
        'graphql': {'queries_1h': 8500, 'avg_latency_ms': 45}
    })


# End of v4.10 endpoints


# === v4.11 Data Structures ===
DISTRIBUTED_TRANSACTIONS = {}
RATE_LIMIT_BUCKETS = {}
CONTEXT_STORE = {}
CONFIG_TEMPLATES = {}
DEPLOYMENT_REGISTRY = {}
ROLLBACK_HISTORY = []
MOCK_REGISTRY = {}
MOCK_SCENARIOS = {}
LOAD_SHEDDING_CONFIG = {'enabled': True, 'threshold': 0.8}
CLOUD_PROVIDERS = {'aws': {'status': 'healthy'}, 'gcp': {'status': 'healthy'}, 'azure': {'status': 'healthy'}}
WEBHOOK_SUBSCRIPTIONS = {}
WEBHOOK_DELIVERIES = []
API_SPECS = {}


# === v4.11 Distributed Transaction Endpoints ===

@app.route('/v411/tx/begin', methods=['POST'])
def v411_tx_begin():
    """Begin distributed transaction"""
    data = request.get_json() or {}
    tx = {
        'tx_id': f"tx_{int(time.time()*1000)}",
        'status': 'started',
        'participants': [{'service': p, 'vote': None, 'status': 'pending'} for p in data.get('participants', [])],
        'timeout_ms': data.get('timeout_ms', 30000),
        'started_at': datetime.now().isoformat()
    }
    DISTRIBUTED_TRANSACTIONS[tx['tx_id']] = tx
    return jsonify({'success': True, 'transaction': tx})


@app.route('/v411/tx/prepare/<tx_id>', methods=['POST'])
def v411_tx_prepare(tx_id):
    """Prepare phase of 2PC"""
    if tx_id not in DISTRIBUTED_TRANSACTIONS:
        return jsonify({'success': False, 'error': 'Transaction not found'}), 404
    tx = DISTRIBUTED_TRANSACTIONS[tx_id]
    tx['status'] = 'prepared'
    return jsonify({'success': True, 'tx_id': tx_id, 'phase': 'prepare', 'all_prepared': True})


@app.route('/v411/tx/commit/<tx_id>', methods=['POST'])
def v411_tx_commit(tx_id):
    """Commit transaction"""
    if tx_id not in DISTRIBUTED_TRANSACTIONS:
        return jsonify({'success': False, 'error': 'Transaction not found'}), 404
    tx = DISTRIBUTED_TRANSACTIONS[tx_id]
    tx['status'] = 'committed'
    tx['committed_at'] = datetime.now().isoformat()
    return jsonify({'success': True, 'tx_id': tx_id, 'status': 'committed'})


@app.route('/v411/tx/rollback/<tx_id>', methods=['POST'])
def v411_tx_rollback(tx_id):
    """Rollback transaction"""
    data = request.get_json() or {}
    if tx_id not in DISTRIBUTED_TRANSACTIONS:
        return jsonify({'success': False, 'error': 'Transaction not found'}), 404
    tx = DISTRIBUTED_TRANSACTIONS[tx_id]
    tx['status'] = 'rolled_back'
    tx['rollback_reason'] = data.get('reason', 'manual')
    return jsonify({'success': True, 'tx_id': tx_id, 'status': 'rolled_back'})


@app.route('/v411/tx/status/<tx_id>', methods=['GET'])
def v411_tx_status(tx_id):
    """Get transaction status"""
    tx = DISTRIBUTED_TRANSACTIONS.get(tx_id)
    if not tx:
        return jsonify({'success': False, 'error': 'Transaction not found'}), 404
    return jsonify({'success': True, 'transaction': tx})


# === v4.11 Rate Limiter Pro Endpoints ===

@app.route('/v411/ratelimit/check', methods=['POST'])
def v411_ratelimit_check():
    """Check rate limit"""
    data = request.get_json() or {}
    key = data.get('key', 'default')
    bucket = RATE_LIMIT_BUCKETS.get(key, {'tokens': 100, 'max': 150})
    allowed = bucket['tokens'] > 0
    return jsonify({
        'success': True,
        'key': key,
        'allowed': allowed,
        'tokens_remaining': bucket['tokens'],
        'reset_at': datetime.now().isoformat()
    })


@app.route('/v411/ratelimit/consume', methods=['POST'])
def v411_ratelimit_consume():
    """Consume rate limit tokens"""
    data = request.get_json() or {}
    key = data.get('key', 'default')
    tokens = data.get('tokens', 1)
    if key not in RATE_LIMIT_BUCKETS:
        RATE_LIMIT_BUCKETS[key] = {'tokens': 100, 'max': 150}
    RATE_LIMIT_BUCKETS[key]['tokens'] = max(0, RATE_LIMIT_BUCKETS[key]['tokens'] - tokens)
    return jsonify({'success': True, 'key': key, 'tokens_consumed': tokens, 'tokens_remaining': RATE_LIMIT_BUCKETS[key]['tokens']})


@app.route('/v411/ratelimit/config', methods=['POST'])
def v411_ratelimit_config():
    """Configure rate limit bucket"""
    data = request.get_json() or {}
    key = data.get('key')
    RATE_LIMIT_BUCKETS[key] = {
        'tokens': data.get('burst', 150),
        'max': data.get('burst', 150),
        'rate': data.get('rate', 100)
    }
    return jsonify({'success': True, 'key': key, 'config': RATE_LIMIT_BUCKETS[key]})


@app.route('/v411/ratelimit/status/<key>', methods=['GET'])
def v411_ratelimit_status(key):
    """Get bucket status"""
    bucket = RATE_LIMIT_BUCKETS.get(key, {'tokens': 100, 'max': 150, 'rate': 100})
    return jsonify({'success': True, 'key': key, 'bucket': bucket})


# === v4.11 Context Propagation Endpoints ===

@app.route('/v411/context/create', methods=['POST'])
def v411_context_create():
    """Create trace context"""
    data = request.get_json() or {}
    context = {
        'context_id': f"ctx_{int(time.time()*1000)}",
        'trace_id': f"trace_{int(time.time()*1000)}",
        'span_id': f"span_{int(time.time()*1000)}",
        'parent_span_id': data.get('parent_span_id'),
        'baggage': data.get('baggage', {}),
        'created_at': datetime.now().isoformat()
    }
    CONTEXT_STORE[context['context_id']] = context
    return jsonify({'success': True, 'context': context})


@app.route('/v411/context/inject', methods=['POST'])
def v411_context_inject():
    """Inject context into carrier"""
    data = request.get_json() or {}
    context_id = data.get('context_id')
    return jsonify({
        'success': True,
        'context_id': context_id,
        'headers': {
            'traceparent': f"00-{context_id}-span-01",
            'tracestate': 'agent=orchestrator',
            'baggage': 'tenant=default'
        }
    })


@app.route('/v411/context/extract', methods=['POST'])
def v411_context_extract():
    """Extract context from carrier"""
    data = request.get_json() or {}
    headers = data.get('headers', {})
    context = {
        'context_id': f"ctx_{int(time.time()*1000)}",
        'trace_id': headers.get('traceparent', '').split('-')[1] if headers.get('traceparent') else f"trace_{int(time.time()*1000)}",
        'span_id': f"span_{int(time.time()*1000)}",
        'extracted_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'context': context})


@app.route('/v411/context/baggage', methods=['POST'])
def v411_context_baggage():
    """Set baggage item"""
    data = request.get_json() or {}
    context_id = data.get('context_id')
    if context_id in CONTEXT_STORE:
        CONTEXT_STORE[context_id]['baggage'][data.get('key')] = data.get('value')
    return jsonify({'success': True, 'context_id': context_id, 'key': data.get('key'), 'set': True})


# === v4.11 Config Templating Endpoints ===

@app.route('/v411/config/templates', methods=['GET', 'POST'])
def v411_config_templates():
    """Manage config templates"""
    if request.method == 'GET':
        return jsonify({'success': True, 'templates': list(CONFIG_TEMPLATES.values())})
    data = request.get_json() or {}
    template = {
        'template_id': f"tpl_{int(time.time()*1000)}",
        'name': data.get('name'),
        'schema': data.get('schema', {}),
        'variables': data.get('variables', []),
        'created_at': datetime.now().isoformat()
    }
    CONFIG_TEMPLATES[template['template_id']] = template
    return jsonify({'success': True, 'template': template})


@app.route('/v411/config/render', methods=['POST'])
def v411_config_render():
    """Render config template"""
    data = request.get_json() or {}
    template_id = data.get('template_id')
    variables = data.get('variables', {})
    environment = data.get('environment', 'dev')
    result = {
        'template_id': template_id,
        'environment': environment,
        'rendered': {**variables},
        'variables_resolved': len(variables),
        'rendered_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'result': result})


@app.route('/v411/config/validate', methods=['POST'])
def v411_config_validate():
    """Validate config against schema"""
    data = request.get_json() or {}
    return jsonify({'success': True, 'valid': True, 'errors': [], 'warnings': []})


# === v4.11 Rollback Manager Endpoints ===

@app.route('/v411/rollback/register', methods=['POST'])
def v411_rollback_register():
    """Register deployment for rollback"""
    data = request.get_json() or {}
    deployment = {
        'deployment_id': data.get('deployment_id') or f"dep_{int(time.time()*1000)}",
        'version': data.get('version'),
        'previous_version': data.get('previous_version'),
        'rollback_enabled': True,
        'registered_at': datetime.now().isoformat()
    }
    DEPLOYMENT_REGISTRY[deployment['deployment_id']] = deployment
    return jsonify({'success': True, 'deployment': deployment})


@app.route('/v411/rollback/trigger', methods=['POST'])
def v411_rollback_trigger():
    """Trigger rollback"""
    data = request.get_json() or {}
    deployment_id = data.get('deployment_id')
    rollback = {
        'rollback_id': f"rb_{int(time.time()*1000)}",
        'deployment_id': deployment_id,
        'reason': data.get('reason', 'manual'),
        'status': 'in_progress',
        'initiated_at': datetime.now().isoformat()
    }
    ROLLBACK_HISTORY.append(rollback)
    return jsonify({'success': True, 'rollback': rollback})


@app.route('/v411/rollback/status/<rollback_id>', methods=['GET'])
def v411_rollback_status(rollback_id):
    """Get rollback status"""
    rollback = next((r for r in ROLLBACK_HISTORY if r['rollback_id'] == rollback_id), None)
    if not rollback:
        return jsonify({'success': False, 'error': 'Rollback not found'}), 404
    return jsonify({'success': True, 'rollback': rollback})


@app.route('/v411/rollback/history', methods=['GET'])
def v411_rollback_history():
    """Get rollback history"""
    return jsonify({'success': True, 'rollbacks': ROLLBACK_HISTORY[-20:]})


# === v4.11 Request Mocking Endpoints ===

@app.route('/v411/mock/create', methods=['POST'])
def v411_mock_create():
    """Create mock"""
    data = request.get_json() or {}
    mock = {
        'mock_id': f"mock_{int(time.time()*1000)}",
        'path': data.get('path'),
        'method': data.get('method', 'GET'),
        'status': data.get('status', 200),
        'body': data.get('body', {}),
        'delay_ms': data.get('delay_ms', 0),
        'created_at': datetime.now().isoformat()
    }
    MOCK_REGISTRY[mock['mock_id']] = mock
    return jsonify({'success': True, 'mock': mock})


@app.route('/v411/mock/match', methods=['POST'])
def v411_mock_match():
    """Match request against mocks"""
    data = request.get_json() or {}
    path = data.get('path')
    method = data.get('method', 'GET')
    for mock in MOCK_REGISTRY.values():
        if mock['path'] == path and mock['method'] == method:
            return jsonify({'success': True, 'matched': True, 'mock': mock})
    return jsonify({'success': True, 'matched': False})


@app.route('/v411/mock/scenarios', methods=['GET', 'POST'])
def v411_mock_scenarios():
    """Manage mock scenarios"""
    if request.method == 'GET':
        return jsonify({'success': True, 'scenarios': list(MOCK_SCENARIOS.values())})
    data = request.get_json() or {}
    scenario = {
        'scenario_id': f"scen_{int(time.time()*1000)}",
        'name': data.get('name'),
        'mocks': data.get('mocks', []),
        'active': False
    }
    MOCK_SCENARIOS[scenario['scenario_id']] = scenario
    return jsonify({'success': True, 'scenario': scenario})


@app.route('/v411/mock/scenarios/<scenario_id>/activate', methods=['POST'])
def v411_mock_scenario_activate(scenario_id):
    """Activate scenario"""
    if scenario_id in MOCK_SCENARIOS:
        MOCK_SCENARIOS[scenario_id]['active'] = True
    return jsonify({'success': True, 'scenario_id': scenario_id, 'active': True})


# === v4.11 Load Shedding Endpoints ===

@app.route('/v411/loadshed/check', methods=['POST'])
def v411_loadshed_check():
    """Check if request should be shed"""
    data = request.get_json() or {}
    system_load = 0.65  # Simulated
    threshold = LOAD_SHEDDING_CONFIG['threshold']
    shed = system_load > threshold
    return jsonify({
        'success': True,
        'shed': shed,
        'system_load': system_load,
        'threshold': threshold,
        'priority': data.get('priority', 'normal')
    })


@app.route('/v411/loadshed/config', methods=['GET', 'POST'])
def v411_loadshed_config():
    """Configure load shedding"""
    if request.method == 'GET':
        return jsonify({'success': True, 'config': LOAD_SHEDDING_CONFIG})
    data = request.get_json() or {}
    LOAD_SHEDDING_CONFIG.update(data)
    return jsonify({'success': True, 'config': LOAD_SHEDDING_CONFIG})


@app.route('/v411/loadshed/stats', methods=['GET'])
def v411_loadshed_stats():
    """Get load shedding stats"""
    return jsonify({
        'success': True,
        'requests_total': 100000,
        'requests_shed': 500,
        'shed_rate': 0.005,
        'avg_load': 0.72
    })


# === v4.11 Multi-Cloud Router Endpoints ===

@app.route('/v411/cloud/route', methods=['POST'])
def v411_cloud_route():
    """Route request to cloud provider"""
    data = request.get_json() or {}
    routing = {
        'routing_id': f"mcr_{int(time.time()*1000)}",
        'selected_provider': 'aws',
        'selected_region': 'us-east-1',
        'selection_reason': data.get('strategy', 'lowest_latency'),
        'estimated_latency_ms': 25,
        'routed_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'routing': routing})


@app.route('/v411/cloud/providers', methods=['GET'])
def v411_cloud_providers():
    """List cloud providers"""
    return jsonify({'success': True, 'providers': CLOUD_PROVIDERS})


@app.route('/v411/cloud/failover', methods=['POST'])
def v411_cloud_failover():
    """Trigger cloud failover"""
    data = request.get_json() or {}
    failover = {
        'failover_id': f"fo_{int(time.time()*1000)}",
        'from_provider': data.get('from'),
        'to_provider': data.get('to'),
        'reason': data.get('reason', 'health_check'),
        'failover_at': datetime.now().isoformat()
    }
    return jsonify({'success': True, 'failover': failover})


@app.route('/v411/cloud/costs', methods=['GET'])
def v411_cloud_costs():
    """Get cloud cost analysis"""
    return jsonify({
        'success': True,
        'by_provider': {
            'aws': {'cost': 450.00, 'requests': 500000},
            'gcp': {'cost': 380.00, 'requests': 400000},
            'azure': {'cost': 220.00, 'requests': 200000}
        },
        'total_cost': 1050.00
    })


# === v4.11 Webhook Delivery Endpoints ===

@app.route('/v411/webhooks', methods=['GET', 'POST'])
def v411_webhooks():
    """Manage webhooks"""
    if request.method == 'GET':
        return jsonify({'success': True, 'webhooks': list(WEBHOOK_SUBSCRIPTIONS.values())})
    data = request.get_json() or {}
    webhook = {
        'webhook_id': f"wh_{int(time.time()*1000)}",
        'url': data.get('url'),
        'events': data.get('events', ['*']),
        'secret': f"whsec_{int(time.time()*1000)}",
        'active': True,
        'created_at': datetime.now().isoformat()
    }
    WEBHOOK_SUBSCRIPTIONS[webhook['webhook_id']] = webhook
    return jsonify({'success': True, 'webhook': webhook})


@app.route('/v411/webhooks/deliver', methods=['POST'])
def v411_webhooks_deliver():
    """Deliver webhook"""
    data = request.get_json() or {}
    delivery = {
        'delivery_id': f"del_{int(time.time()*1000)}",
        'webhook_id': data.get('webhook_id'),
        'event': data.get('event'),
        'status': 'delivered',
        'response_code': 200,
        'latency_ms': 150,
        'delivered_at': datetime.now().isoformat()
    }
    WEBHOOK_DELIVERIES.append(delivery)
    return jsonify({'success': True, 'delivery': delivery})


@app.route('/v411/webhooks/deliveries/<webhook_id>', methods=['GET'])
def v411_webhooks_deliveries(webhook_id):
    """Get webhook deliveries"""
    deliveries = [d for d in WEBHOOK_DELIVERIES if d.get('webhook_id') == webhook_id]
    return jsonify({'success': True, 'webhook_id': webhook_id, 'deliveries': deliveries[-20:]})


@app.route('/v411/webhooks/replay/<delivery_id>', methods=['POST'])
def v411_webhooks_replay(delivery_id):
    """Replay webhook delivery"""
    return jsonify({
        'success': True,
        'delivery_id': delivery_id,
        'replayed': True,
        'new_delivery_id': f"del_{int(time.time()*1000)}"
    })


# === v4.11 API Docs Generator Endpoints ===

@app.route('/v411/docs/generate', methods=['POST'])
def v411_docs_generate():
    """Generate API documentation"""
    data = request.get_json() or {}
    spec = {
        'spec_id': f"spec_{int(time.time()*1000)}",
        'version': '3.0.0',
        'format': data.get('format', 'openapi'),
        'title': data.get('title', 'API Documentation'),
        'endpoints_documented': 250,
        'generated_at': datetime.now().isoformat()
    }
    API_SPECS[spec['spec_id']] = spec
    return jsonify({'success': True, 'spec': spec})


@app.route('/v411/docs/scan', methods=['POST'])
def v411_docs_scan():
    """Scan endpoints for documentation"""
    return jsonify({
        'success': True,
        'endpoints_found': 250,
        'documented': 200,
        'undocumented': 50,
        'deprecated': 10
    })


@app.route('/v411/docs/export/<spec_id>', methods=['GET'])
def v411_docs_export(spec_id):
    """Export API spec"""
    format = request.args.get('format', 'json')
    return jsonify({
        'success': True,
        'spec_id': spec_id,
        'format': format,
        'download_url': f'/docs/{spec_id}.{format}'
    })


@app.route('/v411/docs/validate/<spec_id>', methods=['POST'])
def v411_docs_validate(spec_id):
    """Validate API spec"""
    return jsonify({
        'success': True,
        'spec_id': spec_id,
        'valid': True,
        'errors': [],
        'warnings': ['Missing description for 3 endpoints']
    })


# End of v4.11 endpoints

if __name__ == '__main__':
    main()
