"""
AI Systems Tower - Learning, Recording, Context Injection, Agents, Personas, Goals, Macros, Audit

Learning, recording, context injection, agents, personas, goals, macros, audit.
Extracted from monolithic agent_bridge_api.py, refactored into Flask blueprint.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify

from .models import (
    TASK_OUTCOMES,
    LEARNING_ENTRIES,
    TaskOutcome,
    LearningEntry,
    RECORDED_WORKFLOWS,
    RecordedWorkflow,
    WorkflowStep,
    CONTEXT_INJECTION_RULES,
    ContextInjectionRule,
    AGENT_MESSAGES,
    SHARED_STATES,
    AgentMessage,
    AGENT_PERSONAS,
    AgentPersona,
    DEFAULT_PERSONAS,
    GOALS,
    Goal,
    SubGoal,
    TOOL_MACROS,
    ToolMacro,
    BUILTIN_MACROS,
    AUDIT_TRAIL,
    AuditEntry,
)

intelligence_bp = Blueprint('intelligence', __name__)


@intelligence_bp.route('/learning/record', methods=['POST'])
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


@intelligence_bp.route('/learning/feedback', methods=['POST'])
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


@intelligence_bp.route('/learning/recommendations', methods=['POST'])
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


@intelligence_bp.route('/learning/patterns', methods=['GET', 'POST'])
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


@intelligence_bp.route('/learning/outcomes', methods=['GET', 'POST'])
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


@intelligence_bp.route('/recording/start', methods=['POST'])
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


@intelligence_bp.route('/recording/step', methods=['POST'])
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


@intelligence_bp.route('/recording/stop', methods=['POST'])
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


@intelligence_bp.route('/recording/list', methods=['GET', 'POST'])
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


@intelligence_bp.route('/recording/get', methods=['POST'])
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


@intelligence_bp.route('/recording/playback', methods=['POST'])
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


@intelligence_bp.route('/recording/delete', methods=['POST'])
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


@intelligence_bp.route('/context/rules/create', methods=['POST'])
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


@intelligence_bp.route('/context/rules/list', methods=['GET', 'POST'])
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


@intelligence_bp.route('/context/rules/toggle', methods=['POST'])
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


@intelligence_bp.route('/context/rules/delete', methods=['POST'])
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


@intelligence_bp.route('/context/inject', methods=['POST'])
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


@intelligence_bp.route('/agents/message/send', methods=['POST'])
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


@intelligence_bp.route('/agents/message/receive', methods=['POST'])
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


@intelligence_bp.route('/agents/message/read', methods=['POST'])
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


@intelligence_bp.route('/agents/state/get', methods=['POST'])
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


@intelligence_bp.route('/agents/state/update', methods=['POST'])
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


@intelligence_bp.route('/agents/state/lock', methods=['POST'])
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


@intelligence_bp.route('/agents/state/unlock', methods=['POST'])
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


@intelligence_bp.route('/agents/state/history', methods=['POST'])
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


@intelligence_bp.route('/personas/list', methods=['GET', 'POST'])
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


@intelligence_bp.route('/personas/create', methods=['POST'])
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


@intelligence_bp.route('/personas/get', methods=['POST'])
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


@intelligence_bp.route('/personas/prompt', methods=['POST'])
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


@intelligence_bp.route('/personas/delete', methods=['POST'])
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


@intelligence_bp.route('/goals/create', methods=['POST'])
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


@intelligence_bp.route('/goals/add-subgoal', methods=['POST'])
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


@intelligence_bp.route('/goals/next', methods=['POST'])
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


@intelligence_bp.route('/goals/update-subgoal', methods=['POST'])
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


@intelligence_bp.route('/goals/status', methods=['POST'])
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


@intelligence_bp.route('/goals/list', methods=['GET', 'POST'])
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


@intelligence_bp.route('/macros/list', methods=['GET', 'POST'])
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


@intelligence_bp.route('/macros/create', methods=['POST'])
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


@intelligence_bp.route('/macros/execute', methods=['POST'])
def macros_execute():
    """Execute a tool macro."""
    data = request.get_json() or {}
    macro_id = data.get('macro_id')
    variables = data.get('variables', {})

    if not macro_id:
        return jsonify({"success": False, "error": "Missing 'macro_id'"}), 400

    result = execute_macro(macro_id, variables)
    return jsonify(result)


@intelligence_bp.route('/macros/get', methods=['POST'])
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


@intelligence_bp.route('/macros/delete', methods=['POST'])
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


@intelligence_bp.route('/audit/log', methods=['POST'])
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


@intelligence_bp.route('/audit/query', methods=['POST'])
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


@intelligence_bp.route('/audit/summary', methods=['GET', 'POST'])
def audit_summary():
    """Get audit trail summary statistics."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    summary = get_audit_summary(session_id)
    return jsonify({
        "success": True,
        **summary
    })


@intelligence_bp.route('/audit/review-required', methods=['GET', 'POST'])
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
