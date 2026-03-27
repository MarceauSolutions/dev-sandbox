"""
AI Systems Tower - Data Models

Extracted from monolithic agent_bridge_api.py.
Contains all AI-specific data classes for orchestration, learning, personas, etc.
"""

import json
import os
import time
import uuid
import threading
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path

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


