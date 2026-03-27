"""
AI Agent Monitoring - Langfuse + Helicone integration.

Provides monitored Anthropic clients for tracking costs, performance,
and quality across all three agents (Claude Code, Clawdbot, Ralph).

Setup:
  1. Sign up at cloud.langfuse.com (free, 50K events/month)
  2. Sign up at helicone.ai (free, 10K requests/month)
  3. Add keys to .env:
     LANGFUSE_PUBLIC_KEY=pk-lf-xxx
     LANGFUSE_SECRET_KEY=sk-lf-xxx
     LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
     HELICONE_API_KEY=sk-helicone-xxx

Usage:
  from execution.ai_monitoring import get_monitored_client

  # Langfuse (detailed tracing, 90-day retention)
  client, trace = get_monitored_client("langfuse", agent="claude-code")

  # Helicone (proxy-based, caching, simple)
  client, _ = get_monitored_client("helicone", agent="clawdbot")

  # No monitoring
  client, _ = get_monitored_client("none")
"""

import os
from typing import Optional, Tuple, Any


def get_monitored_client(
    backend: str = "helicone",
    agent: str = "unknown",
    trace_name: Optional[str] = None,
) -> Tuple[Any, Optional[Any]]:
    """
    Returns an Anthropic client with optional monitoring.

    Args:
        backend: "langfuse", "helicone", or "none"
        agent: Agent identifier (claude-code, clawdbot, ralph)
        trace_name: Optional trace name for Langfuse

    Returns:
        (client, trace_or_none)
    """
    from anthropic import Anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if backend == "langfuse":
        try:
            from langfuse import get_client
            langfuse = get_client()
            if not langfuse.auth_check():
                print("[ai_monitoring] Langfuse auth failed, falling back to unmonitored")
                return Anthropic(api_key=api_key), None

            trace = langfuse.trace(
                name=trace_name or f"{agent}-call",
                metadata={"agent": agent},
            )
            return Anthropic(api_key=api_key), trace
        except ImportError:
            print("[ai_monitoring] langfuse not installed. pip install langfuse")
            return Anthropic(api_key=api_key), None

    elif backend == "helicone":
        helicone_key = os.environ.get("HELICONE_API_KEY")
        if not helicone_key:
            print("[ai_monitoring] HELICONE_API_KEY not set, falling back to unmonitored")
            return Anthropic(api_key=api_key), None

        client = Anthropic(
            api_key=api_key,
            base_url="https://anthropic.helicone.ai",
            default_headers={
                "Helicone-Auth": f"Bearer {helicone_key}",
                "Helicone-Property-Agent": agent,
                "Helicone-Cache-Enabled": "true",
            },
        )
        return client, None

    else:
        return Anthropic(api_key=api_key), None


def log_generation(trace, model: str, input_data, output_data, usage: dict, metadata: dict = None):
    """Log a generation to Langfuse trace (no-op if trace is None)."""
    if trace is None:
        return
    try:
        from langfuse import get_client
        langfuse = get_client()
        langfuse.generation(
            trace_id=trace.id,
            model=model,
            input=input_data,
            output=output_data,
            usage=usage,
            metadata=metadata or {},
        )
    except Exception as e:
        print(f"[ai_monitoring] Failed to log generation: {e}")
