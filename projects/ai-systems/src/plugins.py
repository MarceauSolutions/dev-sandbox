"""
AI Systems Tower - Tool Plugin Registration And Execution (Python, Http, Mcp)

Tool plugin registration and execution (Python, HTTP, MCP).
Extracted from monolithic agent_bridge_api.py, refactored into Flask blueprint.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify

from .models import (
    TOOL_PLUGINS,
    ToolPlugin,
)

plugins_bp = Blueprint('plugins', __name__)


@plugins_bp.route('/plugins/list', methods=['GET', 'POST'])
def plugins_list():
    """List all registered tool plugins."""
    plugins = [p.to_dict() for p in TOOL_PLUGINS.values()]
    return jsonify({
        "success": True,
        "plugins": plugins,
        "total": len(plugins)
    })


@plugins_bp.route('/plugins/register-python', methods=['POST'])
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


@plugins_bp.route('/plugins/register-http', methods=['POST'])
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


@plugins_bp.route('/plugins/register-mcp', methods=['POST'])
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


@plugins_bp.route('/plugins/execute', methods=['POST'])
def plugins_execute():
    """Execute a tool plugin."""
    data = request.get_json() or {}
    plugin_id = data.get('plugin_id')
    input_data = data.get('input', {})

    if not plugin_id:
        return jsonify({"success": False, "error": "Missing 'plugin_id' parameter"}), 400

    result = execute_plugin(plugin_id, input_data)

    return jsonify(result)


@plugins_bp.route('/plugins/toggle', methods=['POST'])
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


@plugins_bp.route('/plugins/delete', methods=['POST'])
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
