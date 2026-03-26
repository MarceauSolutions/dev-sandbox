#!/usr/bin/env python3
"""
AI Systems Tower - Flask server for AI orchestration and intelligence.

This tower handles all AI-related functionality including:
- AI monitoring and cost tracking
- Conversation memory management
- Agent templates and personas
- Goal decomposition and orchestration
- Learning and feedback systems
- Workflow recording and playback
- Smart context injection
- Inter-agent communication
- Tool macros and audit trails
- Adaptive behavior

Usage:
    # Start the AI Systems tower
    python -m projects.ai-systems.src.ai_bridge

    # Or with custom port
    python -m projects.ai-systems.src.ai_bridge --port 5011

Author: William Marceau Jr.
Created: 2026-03-26
"""

import argparse
import json
import os
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, Response, jsonify, request, stream_with_context
from flask_cors import CORS

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import shared utilities from execution
from execution.agent_bridge_api import (
    make_error_response, make_success_response, ErrorCode,
    PersistenceManager, retry_with_backoff, truncate_conversation_history,
    LRUCache, TokenBucket, SessionCost, ConversationMemory,
    ToolPipeline, WebhookConfig, AgentTemplate, SubAgent, AgentOrchestration,
    FileIndex, KnowledgeBase, ScheduledTask, ToolPlugin, TaskOutcome,
    LearningEntry, WorkflowStep, RecordedWorkflow, ContextInjectionRule,
    AgentMessage, AgentPersona, SubGoal, Goal, ToolMacro, AuditEntry,
    BehaviorProfile, execute_tools_parallel
)

# =============================================================================
# AI SYSTEMS TOWER CONFIGURATION
# =============================================================================

DEFAULT_PORT = 5011
AI_PERSISTENCE_DIR = Path(os.environ.get('AI_SYSTEMS_DATA_DIR', '/tmp/ai_systems_data'))
AI_PERSISTENCE_FILE = AI_PERSISTENCE_DIR / 'state.json'

# Initialize persistence
ai_persistence_manager = PersistenceManager(AI_PERSISTENCE_FILE, 30)

# Load persisted state
_ai_persisted_state = ai_persistence_manager.load()

# Global state storage
SESSION_COSTS: Dict[str, SessionCost] = _ai_persisted_state.get('session_costs', {})
CONVERSATION_MEMORIES: Dict[str, ConversationMemory] = _ai_persisted_state.get('conversation_memories', {})
TOOL_PIPELINES: Dict[str, ToolPipeline] = _ai_persisted_state.get('tool_pipelines', {})
WEBHOOKS: Dict[str, WebhookConfig] = _ai_persisted_state.get('webhooks', {})
AGENT_TEMPLATES: Dict[str, AgentTemplate] = _ai_persisted_state.get('agent_templates', {})
SUB_AGENTS: Dict[str, SubAgent] = _ai_persisted_state.get('sub_agents', {})
ORCHESTRATIONS: Dict[str, AgentOrchestration] = _ai_persisted_state.get('orchestrations', {})
KNOWLEDGE_BASES: Dict[str, KnowledgeBase] = _ai_persisted_state.get('knowledge_bases', {})
SCHEDULED_TASKS: Dict[str, ScheduledTask] = _ai_persisted_state.get('scheduled_tasks', {})
TOOL_PLUGINS: Dict[str, ToolPlugin] = _ai_persisted_state.get('tool_plugins', {})
TASK_OUTCOMES: Dict[str, TaskOutcome] = _ai_persisted_state.get('task_outcomes', {})
LEARNING_ENTRIES: Dict[str, LearningEntry] = _ai_persisted_state.get('learning_entries', {})
RECORDED_WORKFLOWS: Dict[str, RecordedWorkflow] = _ai_persisted_state.get('recorded_workflows', {})
CONTEXT_INJECTION_RULES: Dict[str, ContextInjectionRule] = _ai_persisted_state.get('context_injection_rules', {})
AGENT_MESSAGES: Dict[str, List[AgentMessage]] = _ai_persisted_state.get('agent_messages', {})
SHARED_STATES: Dict[str, Any] = _ai_persisted_state.get('shared_states', {})
AGENT_PERSONAS: Dict[str, AgentPersona] = _ai_persisted_state.get('agent_personas', {})
GOALS: Dict[str, Goal] = _ai_persisted_state.get('goals', {})
TOOL_MACROS: Dict[str, ToolMacro] = _ai_persisted_state.get('tool_macros', {})
AUDIT_TRAIL: List[AuditEntry] = _ai_persisted_state.get('audit_trail', [])
BEHAVIOR_PROFILES: Dict[str, BehaviorProfile] = _ai_persisted_state.get('behavior_profiles', {})

# Initialize default personas
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

# Flask app
app = Flask(__name__)
CORS(app)

# Track server start time
AI_SERVER_START_TIME = time.time()

# AI Systems specific metrics
AI_EXECUTION_METRICS = {
    "ai_calls": 0,
    "learning_sessions": 0,
    "orchestrations": 0,
    "knowledge_queries": 0,
    "workflows_recorded": 0
}

# =============================================================================
# AI SYSTEMS ENDPOINTS
# =============================================================================

@app.route('/ai/health', methods=['GET'])
def ai_health():
    """AI Systems tower health check."""
    uptime = time.time() - AI_SERVER_START_TIME
    return jsonify({
        "status": "healthy",
        "tower": "ai-systems",
        "version": "1.0.0",
        "uptime_seconds": int(uptime),
        "ai_metrics": AI_EXECUTION_METRICS,
        "active_components": {
            "conversation_memories": len(CONVERSATION_MEMORIES),
            "agent_personas": len(AGENT_PERSONAS),
            "goals": len(GOALS),
            "tool_macros": len(TOOL_MACROS),
            "behavior_profiles": len(BEHAVIOR_PROFILES),
            "knowledge_bases": len(KNOWLEDGE_BASES),
            "orchestrations": len(ORCHESTRATIONS),
            "learning_entries": len(LEARNING_ENTRIES)
        },
        "timestamp": datetime.now().isoformat()
    })

# Cost tracking endpoints
@app.route('/ai/cost/track', methods=['POST'])
def ai_cost_track():
    """Track token usage for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    input_tokens = data.get('input_tokens', 0)
    output_tokens = data.get('output_tokens', 0)
    model = data.get('model', 'claude-sonnet-4-5-20250929')

    if not session_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "session_id is required",
            status_code=400
        ), 400

    session_cost = SESSION_COSTS.get(session_id)
    if not session_cost:
        session_cost = SessionCost(session_id=session_id, model=model)
        SESSION_COSTS[session_id] = session_cost

    session_cost.add_usage(input_tokens, output_tokens)
    AI_EXECUTION_METRICS["ai_calls"] += 1

    ai_persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        **session_cost.to_dict()
    })

@app.route('/ai/cost/session', methods=['POST'])
def ai_cost_session():
    """Get cost information for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if not session_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "session_id is required",
            status_code=400
        ), 400

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

# Conversation memory endpoints
@app.route('/ai/memory/add', methods=['POST'])
def ai_memory_add():
    """Add a message to conversation memory."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    role = data.get('role', 'user')
    content = data.get('content')

    if not session_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "session_id is required",
            status_code=400
        ), 400
    if not content:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "content is required",
            status_code=400
        ), 400

    memory = CONVERSATION_MEMORIES.get(session_id)
    if not memory:
        memory = ConversationMemory(session_id=session_id)
        CONVERSATION_MEMORIES[session_id] = memory

    memory.add_message(role, content)
    ai_persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        "session_id": session_id,
        "message_count": len(memory.messages)
    })

@app.route('/ai/memory/get', methods=['POST'])
def ai_memory_get():
    """Get conversation memory for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    last_n = data.get('last_n', 10)

    if not session_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "session_id is required",
            status_code=400
        ), 400

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

# Agent personas endpoints
@app.route('/ai/personas/list', methods=['GET', 'POST'])
def ai_personas_list():
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

@app.route('/ai/personas/get', methods=['POST'])
def ai_personas_get():
    """Get a specific persona with full details."""
    data = request.get_json() or {}
    persona_id = data.get('persona_id')

    if not persona_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "persona_id is required",
            status_code=400
        ), 400

    if persona_id not in AGENT_PERSONAS:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            f"Persona not found: {persona_id}",
            status_code=404
        ), 404

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

@app.route('/ai/personas/prompt', methods=['POST'])
def ai_personas_get_prompt():
    """Get the system prompt for a persona."""
    data = request.get_json() or {}
    persona_id = data.get('persona_id')

    if not persona_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "persona_id is required",
            status_code=400
        ), 400

    if persona_id not in AGENT_PERSONAS:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            f"Persona not found: {persona_id}",
            status_code=404
        ), 404

    # Import the prompt generation function
    from execution.agent_bridge_api import get_persona_system_prompt

    prompt = get_persona_system_prompt(persona_id)
    if not prompt:
        return make_error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to generate prompt for persona: {persona_id}",
            status_code=500
        ), 500

    # Update usage count
    AGENT_PERSONAS[persona_id].usage_count += 1
    AGENT_PERSONAS[persona_id].last_used = datetime.now().isoformat()

    return jsonify({
        "success": True,
        "persona_id": persona_id,
        "system_prompt": prompt
    })

# Goal decomposition endpoints
@app.route('/ai/goals/create', methods=['POST'])
def ai_goals_create():
    """Create a new goal for decomposition."""
    data = request.get_json() or {}
    title = data.get('title')
    description = data.get('description', '')
    session_id = data.get('session_id')

    if not title or not session_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "title and session_id are required",
            status_code=400
        ), 400

    # Import goal decomposition function
    from execution.agent_bridge_api import decompose_goal

    goal = decompose_goal(
        title=title,
        description=description,
        session_id=session_id,
        strategy=data.get('strategy', 'sequential'),
        context=data.get('context', {})
    )

    GOALS[goal.goal_id] = goal
    ai_persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        "goal_id": goal.goal_id,
        "title": goal.title,
        "status": goal.status
    })

@app.route('/ai/goals/next', methods=['POST'])
def ai_goals_get_next():
    """Get the next actionable sub-goal."""
    data = request.get_json() or {}
    goal_id = data.get('goal_id')

    if not goal_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "goal_id is required",
            status_code=400
        ), 400

    # Import next goal function
    from execution.agent_bridge_api import get_next_subgoal

    subgoal = get_next_subgoal(goal_id)
    if not subgoal:
        if goal_id not in GOALS:
            return make_error_response(
                ErrorCode.MISSING_PARAMETER,
                f"Goal not found: {goal_id}",
                status_code=404
            ), 404
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

# Learning and feedback endpoints
@app.route('/ai/learning/record', methods=['POST'])
def ai_learning_record_outcome():
    """Record a task outcome for learning."""
    data = request.get_json() or {}

    required = ['session_id', 'task', 'success']
    for field in required:
        if field not in data:
            return make_error_response(
                ErrorCode.MISSING_PARAMETER,
                f"{field} is required",
                status_code=400
            ), 400

    # Import learning function
    from execution.agent_bridge_api import record_task_outcome

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

    TASK_OUTCOMES[outcome.outcome_id] = outcome
    AI_EXECUTION_METRICS["learning_sessions"] += 1
    ai_persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        "outcome_id": outcome.outcome_id,
        "patterns_analyzed": True
    })

@app.route('/ai/learning/recommendations', methods=['POST'])
def ai_learning_get_recommendations():
    """Get learning-based recommendations for a task."""
    data = request.get_json() or {}
    task = data.get('task', '')
    context = data.get('context')

    # Import recommendations function
    from execution.agent_bridge_api import get_recommendations_for_task

    recommendations = get_recommendations_for_task(task, context)

    return jsonify({
        "success": True,
        "task": task,
        **recommendations
    })

# Tool macros endpoints
@app.route('/ai/macros/list', methods=['GET', 'POST'])
def ai_macros_list():
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
            "is_builtin": mid in ['backup_and_edit', 'git_safe_commit', 'find_replace_all', 'analyze_codebase']
        })
    return jsonify({
        "success": True,
        "macros": macros,
        "total": len(macros)
    })

@app.route('/ai/macros/execute', methods=['POST'])
def ai_macros_execute():
    """Execute a tool macro."""
    data = request.get_json() or {}
    macro_id = data.get('macro_id')
    variables = data.get('variables', {})

    if not macro_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "macro_id is required",
            status_code=400
        ), 400

    # Import macro execution function
    from execution.agent_bridge_api import execute_macro

    result = execute_macro(macro_id, variables)
    return jsonify(result)

# Adaptive behavior endpoints
@app.route('/ai/behavior/profile', methods=['POST'])
def ai_behavior_get_profile():
    """Get or create behavior profile for a session."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if not session_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "session_id is required",
            status_code=400
        ), 400

    # Import behavior profile function
    from execution.agent_bridge_api import get_or_create_behavior_profile

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

@app.route('/ai/behavior/recommendations', methods=['POST'])
def ai_behavior_recommendations():
    """Get behavior recommendations for a task."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    task = data.get('task', '')

    if not session_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "session_id is required",
            status_code=400
        ), 400

    # Import recommendations function
    from execution.agent_bridge_api import get_behavior_recommendations

    recommendations = get_behavior_recommendations(session_id, task)
    return jsonify({
        "success": True,
        "session_id": session_id,
        **recommendations
    })

# Multi-agent orchestration endpoints
@app.route('/ai/orchestration/create', methods=['POST'])
def ai_orchestration_create():
    """Create a new multi-agent orchestration."""
    data = request.get_json() or {}
    parent_session_id = data.get('session_id')
    objective = data.get('objective')
    subtasks = data.get('subtasks', [])
    strategy = data.get('strategy', 'parallel')

    if not parent_session_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "session_id is required",
            status_code=400
        ), 400
    if not objective:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "objective is required",
            status_code=400
        ), 400
    if not subtasks:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "subtasks is required",
            status_code=400
        ), 400

    # Import orchestration function
    from execution.agent_bridge_api import create_orchestration

    orchestration = create_orchestration(
        parent_session_id=parent_session_id,
        objective=objective,
        subtasks=subtasks,
        strategy=strategy
    )

    ORCHESTRATIONS[orchestration.orchestration_id] = orchestration
    AI_EXECUTION_METRICS["orchestrations"] += 1
    ai_persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        **orchestration.to_dict()
    })

@app.route('/ai/orchestration/status', methods=['POST'])
def ai_orchestration_status():
    """Get status of an orchestration."""
    data = request.get_json() or {}
    orch_id = data.get('orchestration_id')

    if not orch_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "orchestration_id is required",
            status_code=400
        ), 400

    if orch_id not in ORCHESTRATIONS:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            f"Orchestration not found: {orch_id}",
            status_code=404
        ), 404

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

# Knowledge base endpoints
@app.route('/ai/kb/create', methods=['POST'])
def ai_kb_create():
    """Create a new knowledge base."""
    data = request.get_json() or {}
    name = data.get('name')
    root_paths = data.get('root_paths', [])
    description = data.get('description', '')
    include_patterns = data.get('include_patterns')
    exclude_patterns = data.get('exclude_patterns')

    if not name:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "name is required",
            status_code=400
        ), 400
    if not root_paths:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "root_paths is required",
            status_code=400
        ), 400

    # Import KB creation function
    from execution.agent_bridge_api import create_knowledge_base

    kb = create_knowledge_base(
        name=name,
        root_paths=root_paths,
        description=description,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns
    )

    KNOWLEDGE_BASES[kb.kb_id] = kb
    ai_persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        **kb.to_dict()
    })

@app.route('/ai/kb/search', methods=['POST'])
def ai_kb_search():
    """Search a knowledge base."""
    data = request.get_json() or {}
    kb_id = data.get('kb_id')
    query = data.get('query')
    top_k = min(data.get('top_k', 5), 20)

    if not kb_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "kb_id is required",
            status_code=400
        ), 400
    if not query:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "query is required",
            status_code=400
        ), 400

    if kb_id not in KNOWLEDGE_BASES:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            f"Knowledge base not found: {kb_id}",
            status_code=404
        ), 404

    # Import search function
    from execution.agent_bridge_api import search_knowledge_base

    kb = KNOWLEDGE_BASES[kb_id]
    results = search_knowledge_base(kb, query, top_k)
    AI_EXECUTION_METRICS["knowledge_queries"] += 1

    return jsonify({
        "success": True,
        "query": query,
        "results": results,
        "total_results": len(results)
    })

# Workflow recording endpoints
@app.route('/ai/recording/start', methods=['POST'])
def ai_recording_start():
    """Start recording a workflow."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    name = data.get('name', 'Untitled Workflow')
    description = data.get('description', '')

    if not session_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "session_id is required",
            status_code=400
        ), 400

    # Import recording function
    from execution.agent_bridge_api import start_recording

    workflow = start_recording(session_id, name, description)
    RECORDED_WORKFLOWS[workflow.workflow_id] = workflow
    AI_EXECUTION_METRICS["workflows_recorded"] += 1
    ai_persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        "workflow_id": workflow.workflow_id,
        "session_id": session_id,
        "recording": True
    })

@app.route('/ai/recording/playback', methods=['POST'])
def ai_recording_playback():
    """Replay a recorded workflow."""
    data = request.get_json() or {}
    workflow_id = data.get('workflow_id')
    variables = data.get('variables', {})
    dry_run = data.get('dry_run', True)

    if not workflow_id:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "workflow_id is required",
            status_code=400
        ), 400

    # Import playback function
    from execution.agent_bridge_api import playback_workflow

    result = playback_workflow(workflow_id, variables=variables, dry_run=dry_run)

    return jsonify(result)

# Context injection endpoints
@app.route('/ai/context/inject', methods=['POST'])
def ai_context_inject():
    """Get context to inject for a task."""
    data = request.get_json() or {}
    task = data.get('task', '')
    session_id = data.get('session_id')

    # Import context injection function
    from execution.agent_bridge_api import get_context_for_task

    result = get_context_for_task(task, session_id)

    # Optionally format for specific positions
    if data.get('format', False):
        from execution.agent_bridge_api import format_injected_context
        result['formatted'] = {
            'before_task': format_injected_context(result, 'before_task'),
            'after_task': format_injected_context(result, 'after_task'),
            'system_prompt': format_injected_context(result, 'system_prompt')
        }

    return jsonify(result)

# Inter-agent communication endpoints
@app.route('/ai/agents/message/send', methods=['POST'])
def ai_agents_send_message():
    """Send a message from one agent to another."""
    data = request.get_json() or {}
    from_agent = data.get('from_agent')
    to_agent = data.get('to_agent')
    message_type = data.get('message_type', 'data')
    content = data.get('content', {})

    if not from_agent or not to_agent:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "from_agent and to_agent are required",
            status_code=400
        ), 400

    # Import message function
    from execution.agent_bridge_api import send_agent_message

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

@app.route('/ai/agents/state/update', methods=['POST'])
def ai_agents_update_state():
    """Update shared state for an orchestration."""
    data = request.get_json() or {}
    orchestration_id = data.get('orchestration_id')
    agent_id = data.get('agent_id')
    key = data.get('key')
    value = data.get('value')

    if not orchestration_id or not agent_id or not key:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "orchestration_id, agent_id, and key are required",
            status_code=400
        ), 400

    # Import state update function
    from execution.agent_bridge_api import update_shared_state

    result = update_shared_state(
        orchestration_id=orchestration_id,
        agent_id=agent_id,
        key=key,
        value=value,
        require_lock=data.get('require_lock', False)
    )

    return jsonify(result)

# Audit trail endpoints
@app.route('/ai/audit/log', methods=['POST'])
def ai_audit_log_action():
    """Log an action to the audit trail."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    action_type = data.get('action_type')
    action_name = data.get('action_name')

    if not session_id or not action_type or not action_name:
        return make_error_response(
            ErrorCode.MISSING_PARAMETER,
            "session_id, action_type, and action_name are required",
            status_code=400
        ), 400

    # Import audit function
    from execution.agent_bridge_api import log_audit

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

    AUDIT_TRAIL.append(entry)
    ai_persistence_manager.mark_dirty()

    return jsonify({
        "success": True,
        "entry_id": entry.entry_id,
        "timestamp": entry.timestamp
    })

@app.route('/ai/audit/query', methods=['POST'])
def ai_audit_query():
    """Query the audit trail with filters."""
    data = request.get_json() or {}

    # Import audit query function
    from execution.agent_bridge_api import get_audit_trail

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

# =============================================================================
# AI SYSTEMS TOWER MAIN
# =============================================================================

def get_ai_state() -> Dict[str, Any]:
    """Get current AI systems state for persistence."""
    return {
        "session_costs": {k: v.to_dict() for k, v in SESSION_COSTS.items()},
        "conversation_memories": {k: v.to_dict() for k, v in CONVERSATION_MEMORIES.items()},
        "tool_pipelines": {k: v.to_dict() for k, v in TOOL_PIPELINES.items()},
        "webhooks": {k: v.to_dict() for k, v in WEBHOOKS.items()},
        "agent_templates": AGENT_TEMPLATES,
        "sub_agents": {k: v.to_dict() for k, v in SUB_AGENTS.items()},
        "orchestrations": {k: v.to_dict() for k, v in ORCHESTRATIONS.items()},
        "knowledge_bases": {k: v.to_dict() for k, v in KNOWLEDGE_BASES.items()},
        "scheduled_tasks": {k: v.to_dict() for k, v in SCHEDULED_TASKS.items()},
        "tool_plugins": {k: v.to_dict() for k, v in TOOL_PLUGINS.items()},
        "task_outcomes": {k: v.to_dict() for k, v in TASK_OUTCOMES.items()},
        "learning_entries": {k: v.to_dict() for k, v in LEARNING_ENTRIES.items()},
        "recorded_workflows": {k: v.to_dict() for k, v in RECORDED_WORKFLOWS.items()},
        "context_injection_rules": {k: v.to_dict() for k, v in CONTEXT_INJECTION_RULES.items()},
        "agent_messages": AGENT_MESSAGES,
        "shared_states": SHARED_STATES,
        "agent_personas": {k: v.to_dict() for k, v in AGENT_PERSONAS.items()},
        "goals": {k: v.to_dict() for k, v in GOALS.items()},
        "tool_macros": {k: v.to_dict() for k, v in TOOL_MACROS.items()},
        "audit_trail": [e.to_dict() for e in AUDIT_TRAIL[-10000:]],  # Keep last 10k entries
        "behavior_profiles": {k: v.to_dict() for k, v in BEHAVIOR_PROFILES.items()},
        "saved_at": datetime.now().isoformat()
    }

# Start auto-save
ai_persistence_manager.start_auto_save(get_ai_state)

# Cleanup on exit
@atexit.register
def ai_cleanup():
    """Clean up AI systems tower on exit."""
    ai_persistence_manager.stop_auto_save(get_ai_state)

def main():
    """Main entry point for AI Systems tower."""
    parser = argparse.ArgumentParser(description='AI Systems Tower')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                       help=f'Port to run on (default: {DEFAULT_PORT})')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--debug', action='store_true',
                       help='Run in debug mode')

    args = parser.parse_args()

    print("🚀 Starting AI Systems Tower...")
    print(f"📍 Port: {args.port}")
    print(f"🏠 Host: {args.host}")
    print(f"🔧 Debug: {args.debug}")
    print(f"💾 Data directory: {AI_PERSISTENCE_DIR}")

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        threaded=True
    )

if __name__ == '__main__':
    main()