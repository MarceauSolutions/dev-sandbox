"""
Lead Generation ClickUp CRM API - Tower-specific CRM operations.

Extracted from monolithic agent_bridge_api.py to restore tower independence.
Provides ClickUp task management for the lead-generation tower.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_clickup_headers() -> tuple:
    """Get ClickUp API token and headers. Returns (headers, error)."""
    api_token = os.getenv('CLICKUP_API_TOKEN')
    if not api_token:
        return None, "ClickUp API token not configured"
    return {'Authorization': api_token, 'Content-Type': 'application/json'}, None


def list_tasks(list_id: Optional[str] = None) -> Dict[str, Any]:
    """
    List tasks from a ClickUp list.

    Args:
        list_id: ClickUp list ID (falls back to CLICKUP_LIST_ID env var)

    Returns:
        Dict with task list
    """
    import requests

    list_id = list_id or os.getenv('CLICKUP_LIST_ID')
    headers, error = _get_clickup_headers()
    if not headers:
        return {"success": False, "error": error}

    try:
        url = f'https://api.clickup.com/api/v2/list/{list_id}/task'
        response = requests.get(url, headers=headers)
        result = response.json()
        if 'tasks' in result:
            tasks = [{
                'id': t['id'],
                'name': t['name'],
                'status': t['status']['status'] if t.get('status') else None
            } for t in result['tasks']]
            return {"success": True, "tasks": tasks, "count": len(tasks)}
        return {"success": False, "error": result.get('err', 'Unknown error')}
    except Exception as e:
        logger.error(f"Failed to list ClickUp tasks: {e}")
        return {"success": False, "error": str(e)}


def create_task(name: str, description: str = "", list_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a task in ClickUp.

    Args:
        name: Task name
        description: Task description
        list_id: ClickUp list ID

    Returns:
        Dict with created task info
    """
    import requests

    list_id = list_id or os.getenv('CLICKUP_LIST_ID')
    headers, error = _get_clickup_headers()
    if not headers:
        return {"success": False, "error": error}

    try:
        url = f'https://api.clickup.com/api/v2/list/{list_id}/task'
        payload = {'name': name, 'description': description}
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        if 'id' in result:
            return {"success": True, "task_id": result['id'], "name": result['name']}
        return {"success": False, "error": result.get('err', 'Unknown error')}
    except Exception as e:
        logger.error(f"Failed to create ClickUp task: {e}")
        return {"success": False, "error": str(e)}


def update_task(task_id: str, **fields) -> Dict[str, Any]:
    """
    Update a task in ClickUp.

    Args:
        task_id: ClickUp task ID
        **fields: Fields to update (name, description, priority, status, due_date)

    Returns:
        Dict with update status
    """
    import requests

    headers, error = _get_clickup_headers()
    if not headers:
        return {"success": False, "error": error}

    try:
        url = f'https://api.clickup.com/api/v2/task/{task_id}'
        payload = {k: v for k, v in fields.items() if k in ['name', 'description', 'priority', 'status', 'due_date']}
        response = requests.put(url, headers=headers, json=payload)
        result = response.json()
        if 'id' in result:
            return {"success": True, "task_id": result['id'], "updated_fields": list(payload.keys())}
        return {"success": False, "error": result.get('err', 'Unknown error')}
    except Exception as e:
        logger.error(f"Failed to update ClickUp task: {e}")
        return {"success": False, "error": str(e)}


def get_tower_capabilities() -> Dict[str, Any]:
    """Return tower capabilities for ClickUp operations."""
    return {
        "name": "lead-generation-clickup",
        "description": "ClickUp CRM integration for lead management",
        "functions": ["list_tasks", "create_task", "update_task"],
        "protocols": ["direct_import", "api"]
    }
