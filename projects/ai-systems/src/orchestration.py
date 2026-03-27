"""
AI Systems Tower - Agent Templates, Multi-Agent Orchestration, And Scheduling

Agent templates, multi-agent orchestration, and scheduling.
Extracted from monolithic agent_bridge_api.py, refactored into Flask blueprint.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify

from .models import (
    AGENT_TEMPLATES,
    ORCHESTRATIONS,
    SUB_AGENTS,
    SCHEDULED_TASKS,
    ScheduledTask,
    create_orchestration,
)

orchestration_bp = Blueprint('orchestration', __name__)


@orchestration_bp.route('/templates/list', methods=['GET', 'POST'])
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


@orchestration_bp.route('/templates/get', methods=['POST'])
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


@orchestration_bp.route('/templates/apply', methods=['POST'])
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


@orchestration_bp.route('/orchestration/create', methods=['POST'])
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


@orchestration_bp.route('/orchestration/list', methods=['GET', 'POST'])
def orchestration_list():
    """List all orchestrations."""
    orchestrations = [o.to_dict() for o in ORCHESTRATIONS.values()]
    return jsonify({
        "success": True,
        "orchestrations": orchestrations,
        "total": len(orchestrations)
    })


@orchestration_bp.route('/orchestration/status', methods=['POST'])
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


@orchestration_bp.route('/orchestration/update-agent', methods=['POST'])
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


@orchestration_bp.route('/scheduler/create', methods=['POST'])
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


@orchestration_bp.route('/scheduler/list', methods=['GET', 'POST'])
def scheduler_list():
    """List all scheduled tasks."""
    tasks = [t.to_dict() for t in SCHEDULED_TASKS.values()]
    return jsonify({
        "success": True,
        "tasks": tasks,
        "total": len(tasks),
        "scheduler_running": SCHEDULER_RUNNING
    })


@orchestration_bp.route('/scheduler/toggle', methods=['POST'])
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


@orchestration_bp.route('/scheduler/delete', methods=['POST'])
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


@orchestration_bp.route('/scheduler/run-now', methods=['POST'])
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
