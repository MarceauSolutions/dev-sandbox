#!/usr/bin/env python3
"""
MCP Security Utilities
======================

Shared security functions for all MCP servers in dev-sandbox.
Provides input sanitization, path validation, rate limiting, and audit logging.

Based on real-world MCP vulnerabilities documented at:
- https://authzed.com/blog/timeline-mcp-breaches
- https://unit42.paloaltonetworks.com/model-context-protocol-attack-vectors/

Usage in any MCP server:
    from execution.mcp_security import (
        sanitize_input,
        sanitize_dict,
        validate_path,
        rate_limit,
        audit_log,
        secure_tool,
        RateLimitExceeded,
        ToolRequiresConfirmation
    )

Example:
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        # Rate limit
        rate_limit(f"my-mcp:{name}")

        # Sanitize inputs
        arguments = sanitize_dict(arguments)

        # Audit log
        audit_log("my-mcp", name, arguments)

        # Handle tool...

Version: 1.0.0
Created: 2026-01-29
"""

import re
import json
import logging
from pathlib import Path
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

__version__ = "1.0.0"
__all__ = [
    # Sanitization
    "sanitize_string",
    "sanitize_dict",
    # Path validation
    "validate_path",
    # Rate limiting
    "RateLimiter",
    "rate_limit",
    "RateLimitExceeded",
    # Audit logging
    "AuditLogger",
    "audit_log",
    "log_security_event",
    # Tool protection
    "ToolRequiresConfirmation",
    "check_dangerous_tool",
    "DANGEROUS_TOOLS",
    # Decorator
    "secure_tool",
]


# ─────────────────────────────────────────────────────────────
# INPUT SANITIZATION
# ─────────────────────────────────────────────────────────────

# Patterns commonly used in prompt injection attacks
INJECTION_PATTERNS = [
    r'\[INST\].*?\[/INST\]',           # Llama instruction markers
    r'\[SYSTEM\].*?\[/SYSTEM\]',       # System prompt markers
    r'<\|im_start\|>.*?<\|im_end\|>',  # ChatML markers
    r'<<SYS>>.*?<</SYS>>',             # Llama 2 system markers
    r'System:\s*.*?(?=\n|$)',          # System prefix
    r'Assistant:\s*.*?(?=\n|$)',       # Assistant prefix
    r'Human:\s*.*?(?=\n|$)',           # Human prefix
    r'You are now\s+.*?(?=\n|$)',      # Role-play triggers
    r'Ignore previous instructions',    # Direct override attempts
    r'Disregard all prior',            # Direct override attempts
    r'Forget everything',              # Direct override attempts
    r'New instructions:',              # Direct override attempts
]

# Characters that should never appear in shell arguments
SHELL_DANGEROUS_CHARS = set(';|&$`\n\r\\\'\"<>(){}[]!')

# Characters that should never appear in file paths
PATH_DANGEROUS_CHARS = set(';|&$`\n\r')

# Dangerous command patterns to block in command_arg context
DANGEROUS_COMMAND_PATTERNS = [
    r'\brm\s+(-[rf]+\s+)?/',          # rm -rf /
    r'\bdd\s+if=',                     # dd if=
    r'\bmkfs\.',                       # mkfs.*
    r'\b(wget|curl)\s+.+\s*\|\s*sh',  # wget ... | sh
    r'\bchmod\s+777',                  # chmod 777
    r'\b>\s*/dev/',                    # > /dev/
    r'/etc/(passwd|shadow)',           # sensitive files
    r'\bsudo\b',                        # sudo
    r'\bsu\s+-',                        # su -
]


def sanitize_string(value: str, context: str = "general") -> str:
    """
    Sanitize string input by removing injection patterns.

    Args:
        value: Input string to sanitize
        context: Context for sanitization rules
            - "general": Remove prompt injection patterns
            - "filename": Only allow safe filename characters
            - "command_arg": Remove shell-dangerous characters
            - "email": Basic email format validation
            - "phone": Only allow digits and common phone chars

    Returns:
        Sanitized string

    Example:
        >>> sanitize_string("[INST]evil[/INST]hello", "general")
        'hello'
        >>> sanitize_string("file.txt; rm -rf /", "filename")
        'file.txt rm -rf '
    """
    if not isinstance(value, str):
        return str(value) if value is not None else ""

    result = value

    # Remove prompt injection patterns (always, regardless of context)
    for pattern in INJECTION_PATTERNS:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE | re.DOTALL)

    # Context-specific sanitization
    if context == "filename":
        # Only allow alphanumeric, dash, underscore, dot, space
        result = re.sub(r'[^a-zA-Z0-9_\-\. ]', '', result)
        # Prevent path traversal
        result = result.replace('..', '')

    elif context == "command_arg":
        # Block dangerous command patterns BEFORE removing chars
        for pattern in DANGEROUS_COMMAND_PATTERNS:
            if re.search(pattern, result, re.IGNORECASE):
                raise ValueError(f"Dangerous command pattern detected in input")
        # Remove shell-dangerous characters
        result = ''.join(c for c in result if c not in SHELL_DANGEROUS_CHARS)

    elif context == "email":
        # Basic email format - remove obviously invalid chars
        result = re.sub(r'[^a-zA-Z0-9@._\-+]', '', result)

    elif context == "phone":
        # Only digits and common phone formatting chars
        result = re.sub(r'[^0-9+\-() ]', '', result)

    return result.strip()


def sanitize_dict(
    data: Dict[str, Any],
    rules: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Sanitize all string values in a dictionary.

    Args:
        data: Dictionary to sanitize
        rules: Optional mapping of field names to sanitization contexts
               Fields not in rules use "general" context

    Returns:
        Sanitized dictionary (new dict, original unchanged)

    Example:
        >>> data = {"name": "John[INST]evil[/INST]", "email": "test@example.com"}
        >>> sanitize_dict(data, {"email": "email"})
        {'name': 'John', 'email': 'test@example.com'}
    """
    rules = rules or {}
    result = {}

    for key, value in data.items():
        if isinstance(value, str):
            context = rules.get(key, "general")
            result[key] = sanitize_string(value, context)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value, rules)
        elif isinstance(value, list):
            result[key] = [
                sanitize_string(v, rules.get(key, "general")) if isinstance(v, str) else v
                for v in value
            ]
        else:
            result[key] = value

    return result


# ─────────────────────────────────────────────────────────────
# PATH VALIDATION
# ─────────────────────────────────────────────────────────────

# Default allowed directories for file operations
DEFAULT_ALLOWED_DIRS = [
    Path.home() / "Downloads",
    Path.home() / "Documents",
    Path.home() / "Videos",
    Path("/tmp"),
]


def validate_path(
    path_str: str,
    allowed_dirs: Optional[List[Path]] = None,
    allowed_extensions: Optional[Set[str]] = None,
    must_exist: bool = True,
    allow_symlinks: bool = False
) -> Path:
    """
    Validate a file path against security constraints.

    Prevents:
    - Path traversal attacks (../)
    - Access outside allowed directories
    - Symlink attacks (optionally)
    - Command injection via path

    Args:
        path_str: Path string to validate
        allowed_dirs: List of allowed parent directories (default: Downloads, Documents, Videos, /tmp)
        allowed_extensions: Set of allowed file extensions (e.g., {'.pdf', '.txt'})
        must_exist: Whether the file must already exist
        allow_symlinks: Whether to allow symlinks (default: False for security)

    Returns:
        Validated Path object

    Raises:
        ValueError: If path fails validation

    Example:
        >>> validate_path("/tmp/test.pdf", allowed_extensions={'.pdf'})
        PosixPath('/tmp/test.pdf')
        >>> validate_path("../../../etc/passwd")
        ValueError: Path outside allowed directories
    """
    if allowed_dirs is None:
        allowed_dirs = DEFAULT_ALLOWED_DIRS

    # Check for dangerous characters
    if any(char in path_str for char in PATH_DANGEROUS_CHARS):
        raise ValueError("Invalid characters in path")

    # Resolve to absolute path (handles ../ traversal)
    try:
        path = Path(path_str).resolve()
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid path: {e}")

    # Check existence if required
    if must_exist:
        if not path.exists():
            raise ValueError("Path does not exist")
        if not path.is_file():
            raise ValueError("Path is not a file")

    # Check extension if specified
    if allowed_extensions:
        if path.suffix.lower() not in allowed_extensions:
            raise ValueError(f"File extension not allowed: {path.suffix}")

    # Check against allowed directories
    if not any(_is_subpath(path, allowed) for allowed in allowed_dirs):
        raise ValueError("Path outside allowed directories")

    # Check for symlink attacks
    if not allow_symlinks and path.is_symlink():
        real_path = path.resolve()
        if not any(_is_subpath(real_path, allowed) for allowed in allowed_dirs):
            raise ValueError("Symlink target outside allowed directories")

    return path


def _is_subpath(path: Path, parent: Path) -> bool:
    """Check if path is a subpath of parent."""
    try:
        path.relative_to(parent.resolve())
        return True
    except ValueError:
        return False


# ─────────────────────────────────────────────────────────────
# RATE LIMITING
# ─────────────────────────────────────────────────────────────

class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message)


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window.

    Thread-safe for basic async use (single-threaded event loop).
    For production multi-process deployment, use Redis-backed limiter.
    """

    def __init__(self):
        self._calls: Dict[str, List[datetime]] = defaultdict(list)

    def check(
        self,
        key: str,
        max_calls: int = 60,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if a call is allowed under rate limits.

        Args:
            key: Unique identifier (e.g., "mcp:tool_name", "user:123")
            max_calls: Maximum calls allowed in window
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)

        # Remove old entries
        self._calls[key] = [t for t in self._calls[key] if t > cutoff]

        # Check limit
        if len(self._calls[key]) >= max_calls:
            return False

        # Record this call
        self._calls[key].append(now)
        return True

    def get_remaining(
        self,
        key: str,
        max_calls: int = 60,
        window_seconds: int = 60
    ) -> int:
        """Get remaining calls allowed in current window."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        recent_calls = [t for t in self._calls[key] if t > cutoff]
        return max(0, max_calls - len(recent_calls))

    def reset(self, key: str) -> None:
        """Reset rate limit for a key (useful for testing)."""
        self._calls[key] = []


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(
    key: str,
    max_calls: int = 60,
    window_seconds: int = 60
) -> None:
    """
    Check rate limit and raise exception if exceeded.

    Args:
        key: Unique identifier for rate limiting
        max_calls: Maximum calls allowed
        window_seconds: Time window

    Raises:
        RateLimitExceeded: If rate limit is exceeded

    Example:
        >>> rate_limit("trainerize:list_clients", max_calls=30, window_seconds=60)
    """
    if not _rate_limiter.check(key, max_calls, window_seconds):
        raise RateLimitExceeded(
            f"Rate limit exceeded for {key}. "
            f"Max {max_calls} calls per {window_seconds}s.",
            retry_after=window_seconds
        )


# ─────────────────────────────────────────────────────────────
# AUDIT LOGGING
# ─────────────────────────────────────────────────────────────

class AuditLogger:
    """
    Security audit logger for MCP operations.

    Logs all tool calls and security events to a JSON-lines file
    for later analysis and incident response.
    """

    # Fields that should be redacted from logs
    SENSITIVE_PATTERNS = [
        'password', 'token', 'secret', 'key', 'auth',
        'credential', 'api_key', 'access_token', 'refresh_token',
        'private_key', 'bearer', 'session'
    ]

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or Path.home() / ".mcp-audit.log"
        self._logger = logging.getLogger("mcp.security.audit")

        # Set up file handler if not already configured
        if not self._logger.handlers:
            try:
                handler = logging.FileHandler(self.log_file)
                handler.setFormatter(logging.Formatter('%(message)s'))
                self._logger.addHandler(handler)
                self._logger.setLevel(logging.INFO)
            except (OSError, PermissionError) as e:
                # Fall back to stderr if can't write to file
                logging.warning(f"Could not create audit log file: {e}")

    def log_tool_call(
        self,
        mcp_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        result_status: str = "success",
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a tool call for audit purposes.

        Args:
            mcp_name: Name of the MCP server
            tool_name: Name of the tool called
            arguments: Tool arguments (sensitive fields will be redacted)
            result_status: "success", "error", "rate_limited", etc.
            error: Error message if status is not success
            metadata: Additional metadata to log
        """
        entry = {
            "event": "tool_call",
            "timestamp": datetime.now().isoformat(),
            "mcp": mcp_name,
            "tool": tool_name,
            "arguments": self._redact_sensitive(arguments),
            "status": result_status,
        }

        if error:
            entry["error"] = error[:500]  # Truncate long errors

        if metadata:
            entry["metadata"] = self._redact_sensitive(metadata)

        self._logger.info(json.dumps(entry))

    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        severity: str = "warning"
    ) -> None:
        """
        Log a security-relevant event.

        Args:
            event_type: Type of event (e.g., "rate_limit_exceeded", "path_traversal_attempt")
            details: Event details
            severity: "info", "warning", "error", "critical"
        """
        entry = {
            "event": "security",
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "severity": severity,
            "details": self._redact_sensitive(details),
        }

        level = getattr(logging, severity.upper(), logging.WARNING)
        self._logger.log(level, json.dumps(entry))

    def _redact_sensitive(self, data: Any) -> Any:
        """Redact sensitive fields from log data."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(pattern in key_lower for pattern in self.SENSITIVE_PATTERNS):
                    result[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    result[key] = self._redact_sensitive(value)
                elif isinstance(value, str) and len(value) > 1000:
                    result[key] = value[:100] + "...[TRUNCATED]"
                else:
                    result[key] = value
            return result
        elif isinstance(data, list):
            return [self._redact_sensitive(item) for item in data[:50]]  # Limit list size
        else:
            return data


# Global audit logger instance
_audit_logger = AuditLogger()


def audit_log(
    mcp_name: str,
    tool_name: str,
    arguments: Dict[str, Any],
    result_status: str = "success",
    error: Optional[str] = None
) -> None:
    """
    Log a tool call for audit purposes.

    Example:
        >>> audit_log("trainerize", "list_clients", {"status": "active"})
    """
    _audit_logger.log_tool_call(mcp_name, tool_name, arguments, result_status, error)


def log_security_event(
    event_type: str,
    details: Dict[str, Any],
    severity: str = "warning"
) -> None:
    """
    Log a security-relevant event.

    Example:
        >>> log_security_event("rate_limit_exceeded", {"tool": "send_sms", "count": 100})
    """
    _audit_logger.log_security_event(event_type, details, severity)


# ─────────────────────────────────────────────────────────────
# DANGEROUS TOOL PROTECTION
# ─────────────────────────────────────────────────────────────

class ToolRequiresConfirmation(Exception):
    """
    Raised when a dangerous tool requires user confirmation.

    The MCP server should catch this and return a message
    asking the user to confirm the action.
    """

    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Tool '{tool_name}' requires confirmation: {reason}")


# Tools that should require confirmation before execution
# Add to this dict to protect additional tools
DANGEROUS_TOOLS: Dict[str, str] = {
    # Communication (can't be undone, external impact)
    "send_message": "Sends communication to external parties",
    "send_sms": "Sends SMS messages (costs money, can't be undone)",
    "send_email": "Sends email to external parties",
    "send_group_message": "Broadcasts message to multiple recipients",

    # Data deletion (can't be undone)
    "delete_client": "Permanently deletes client data",
    "delete_file": "Permanently deletes files",
    "delete_program": "Permanently deletes training program",
    "delete_account": "Permanently deletes account",

    # Financial (real money impact)
    "create_order": "Creates financial transactions",
    "execute_trade": "Executes financial trades",
    "process_payment": "Processes payment",
    "refund": "Issues refund",

    # Publishing (public visibility)
    "publish_post": "Publishes content publicly",
    "upload_video": "Uploads video publicly",
    "create_listing": "Creates public listing",

    # Account actions (security sensitive)
    "change_password": "Changes account password",
    "revoke_access": "Revokes access permissions",
    "grant_admin": "Grants administrative privileges",
}


def check_dangerous_tool(tool_name: str) -> None:
    """
    Check if a tool is dangerous and should require confirmation.

    Args:
        tool_name: Name of the tool being called

    Raises:
        ToolRequiresConfirmation: If tool requires user confirmation

    Example:
        >>> check_dangerous_tool("send_sms")
        ToolRequiresConfirmation: Tool 'send_sms' requires confirmation: ...
    """
    if tool_name in DANGEROUS_TOOLS:
        log_security_event(
            "dangerous_tool_invoked",
            {"tool": tool_name, "reason": DANGEROUS_TOOLS[tool_name]},
            severity="warning"
        )
        raise ToolRequiresConfirmation(tool_name, DANGEROUS_TOOLS[tool_name])


def register_dangerous_tool(tool_name: str, reason: str) -> None:
    """
    Register a tool as dangerous (requires confirmation).

    Use this in your MCP server to protect additional tools.

    Example:
        >>> register_dangerous_tool("custom_action", "Performs irreversible action")
    """
    DANGEROUS_TOOLS[tool_name] = reason


# ─────────────────────────────────────────────────────────────
# DECORATOR FOR SECURE TOOL HANDLERS
# ─────────────────────────────────────────────────────────────

def secure_tool(
    mcp_name: str,
    rate_limit_calls: int = 60,
    rate_limit_window: int = 60,
    sanitize_rules: Optional[Dict[str, str]] = None,
    require_confirmation: bool = False,
    confirmation_reason: str = ""
):
    """
    Decorator to add security controls to MCP tool handlers.

    Applies:
    - Rate limiting
    - Input sanitization
    - Audit logging
    - Dangerous tool protection (optional)

    Args:
        mcp_name: Name of the MCP server (for logging)
        rate_limit_calls: Max calls per window
        rate_limit_window: Window in seconds
        sanitize_rules: Dict mapping field names to sanitization contexts
        require_confirmation: If True, requires user confirmation
        confirmation_reason: Reason shown when confirmation required

    Example:
        @secure_tool(
            "trainerize",
            rate_limit_calls=30,
            sanitize_rules={"name": "general", "email": "email"},
            require_confirmation=True,
            confirmation_reason="Sends message to client"
        )
        async def handle_send_message(arguments: dict):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(arguments: dict, *args, **kwargs):
            tool_name = func.__name__

            # Check if requires confirmation
            if require_confirmation:
                log_security_event(
                    "confirmation_required",
                    {"mcp": mcp_name, "tool": tool_name, "reason": confirmation_reason}
                )
                raise ToolRequiresConfirmation(tool_name, confirmation_reason)

            # Rate limiting
            try:
                rate_limit(
                    f"{mcp_name}:{tool_name}",
                    rate_limit_calls,
                    rate_limit_window
                )
            except RateLimitExceeded as e:
                audit_log(mcp_name, tool_name, arguments, "rate_limited", str(e))
                raise

            # Input sanitization
            sanitized_args = arguments
            if sanitize_rules:
                sanitized_args = sanitize_dict(arguments, sanitize_rules)

            # Execute and log
            try:
                result = await func(sanitized_args, *args, **kwargs)
                audit_log(mcp_name, tool_name, sanitized_args, "success")
                return result
            except Exception as e:
                audit_log(mcp_name, tool_name, sanitized_args, "error", str(e))
                raise

        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_audit_log_path() -> Path:
    """Get the path to the audit log file."""
    return _audit_logger.log_file


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance (useful for testing)."""
    return _rate_limiter


def reset_rate_limits() -> None:
    """Reset all rate limits (useful for testing)."""
    global _rate_limiter
    _rate_limiter = RateLimiter()
