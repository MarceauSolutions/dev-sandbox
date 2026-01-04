#!/usr/bin/env python3
"""
ClickUp API Wrapper for Marceau Solutions CRM

Usage:
    python clickup_api.py list-spaces
    python clickup_api.py list-tasks --space "Template Creative Agency"
    python clickup_api.py create-task "Task Name" --list "List ID"
    python clickup_api.py update-task TASK_ID --status "in progress"
"""

import requests
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ClickUp API Configuration
CLICKUP_API_BASE = "https://api.clickup.com/api/v2"
CLICKUP_API_TOKEN = os.getenv('CLICKUP_API_TOKEN')


def get_headers():
    """Get API headers with authentication"""
    if not CLICKUP_API_TOKEN:
        raise ValueError(
            "CLICKUP_API_TOKEN not set in .env file.\n"
            "Get your API token from: ClickUp Settings → Apps → API Token"
        )

    return {
        "Authorization": CLICKUP_API_TOKEN,
        "Content-Type": "application/json"
    }


def list_workspaces():
    """List all workspaces (teams)"""
    url = f"{CLICKUP_API_BASE}/team"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()

    teams = response.json().get('teams', [])

    print("📊 Workspaces:")
    for team in teams:
        print(f"  - {team['name']} (ID: {team['id']})")

    return teams


def list_spaces(workspace_id=None):
    """List all spaces in a workspace"""
    if not workspace_id:
        workspace_id = os.getenv('CLICKUP_WORKSPACE_ID')
        if not workspace_id:
            print("⚠️  No workspace ID provided. Fetching all workspaces...")
            teams = list_workspaces()
            if teams:
                workspace_id = teams[0]['id']
                print(f"Using first workspace: {teams[0]['name']}")

    url = f"{CLICKUP_API_BASE}/team/{workspace_id}/space"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()

    spaces = response.json().get('spaces', [])

    print(f"\n📁 Spaces in workspace {workspace_id}:")
    for space in spaces:
        print(f"  - {space['name']} (ID: {space['id']})")

    return spaces


def get_space_by_name(space_name, workspace_id=None):
    """Get space ID by name"""
    spaces = list_spaces(workspace_id)
    for space in spaces:
        if space['name'].lower() == space_name.lower():
            return space
    return None


def list_folders(space_id):
    """List folders in a space"""
    url = f"{CLICKUP_API_BASE}/space/{space_id}/folder"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()

    folders = response.json().get('folders', [])

    print(f"\n📂 Folders in space:")
    for folder in folders:
        print(f"  - {folder['name']} (ID: {folder['id']})")

    return folders


def list_lists(space_id):
    """List all lists in a space"""
    url = f"{CLICKUP_API_BASE}/space/{space_id}/list"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()

    lists = response.json().get('lists', [])

    print(f"\n📝 Lists in space:")
    for lst in lists:
        print(f"  - {lst['name']} (ID: {lst['id']})")

    return lists


def list_tasks(list_id=None, space_name=None):
    """List tasks in a list or space"""
    if space_name:
        space = get_space_by_name(space_name)
        if not space:
            print(f"❌ Space '{space_name}' not found")
            return []

        # Get all lists in space
        lists = list_lists(space['id'])

        all_tasks = []
        for lst in lists:
            url = f"{CLICKUP_API_BASE}/list/{lst['id']}/task"
            response = requests.get(url, headers=get_headers())
            response.raise_for_status()
            tasks = response.json().get('tasks', [])
            all_tasks.extend(tasks)

        print(f"\n✅ Tasks in '{space_name}':")
        for task in all_tasks:
            status = task.get('status', {}).get('status', 'No status')
            assignees = ', '.join([a.get('username', '') for a in task.get('assignees', [])])
            print(f"  - [{status}] {task['name']} (ID: {task['id']})")
            if assignees:
                print(f"    Assigned to: {assignees}")

        return all_tasks

    elif list_id:
        url = f"{CLICKUP_API_BASE}/list/{list_id}/task"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()

        tasks = response.json().get('tasks', [])

        print(f"\n✅ Tasks in list {list_id}:")
        for task in tasks:
            print(f"  - {task['name']} (ID: {task['id']})")

        return tasks

    else:
        print("❌ Please provide either --list or --space")
        return []


def create_task(name, list_id, description="", priority=None, assignees=None):
    """Create a new task"""
    url = f"{CLICKUP_API_BASE}/list/{list_id}/task"

    data = {
        "name": name,
        "description": description
    }

    if priority:
        data["priority"] = priority

    if assignees:
        data["assignees"] = assignees

    response = requests.post(url, headers=get_headers(), json=data)
    response.raise_for_status()

    task = response.json()

    print(f"✅ Task created: {task['name']} (ID: {task['id']})")
    print(f"   URL: {task['url']}")

    return task


def update_task(task_id, status=None, name=None, description=None):
    """Update a task"""
    url = f"{CLICKUP_API_BASE}/task/{task_id}"

    data = {}
    if status:
        data["status"] = status
    if name:
        data["name"] = name
    if description:
        data["description"] = description

    response = requests.put(url, headers=get_headers(), json=data)
    response.raise_for_status()

    task = response.json()

    print(f"✅ Task updated: {task['name']}")

    return task


def get_task(task_id):
    """Get task details"""
    url = f"{CLICKUP_API_BASE}/task/{task_id}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()

    task = response.json()

    print(f"\n📋 Task: {task['name']}")
    print(f"   ID: {task['id']}")
    print(f"   Status: {task.get('status', {}).get('status', 'No status')}")
    print(f"   URL: {task['url']}")
    if task.get('description'):
        print(f"   Description: {task['description']}")

    return task


def main():
    """Main CLI handler"""
    if len(sys.argv) < 2:
        print("Usage: python clickup_api.py <command> [options]")
        print("\nCommands:")
        print("  list-workspaces              List all workspaces")
        print("  list-spaces [--workspace ID] List all spaces")
        print("  list-tasks --space NAME      List tasks in a space")
        print("  create-task NAME --list ID   Create a new task")
        print("  update-task ID --status X    Update task status")
        print("  get-task ID                  Get task details")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "list-workspaces":
            list_workspaces()

        elif command == "list-spaces":
            workspace_id = None
            if "--workspace" in sys.argv:
                idx = sys.argv.index("--workspace")
                workspace_id = sys.argv[idx + 1]
            list_spaces(workspace_id)

        elif command == "list-tasks":
            if "--space" in sys.argv:
                idx = sys.argv.index("--space")
                space_name = sys.argv[idx + 1]
                list_tasks(space_name=space_name)
            elif "--list" in sys.argv:
                idx = sys.argv.index("--list")
                list_id = sys.argv[idx + 1]
                list_tasks(list_id=list_id)

        elif command == "create-task":
            task_name = sys.argv[2]
            if "--list" in sys.argv:
                idx = sys.argv.index("--list")
                list_id = sys.argv[idx + 1]
                create_task(task_name, list_id)

        elif command == "update-task":
            task_id = sys.argv[2]
            status = None
            if "--status" in sys.argv:
                idx = sys.argv.index("--status")
                status = sys.argv[idx + 1]
            update_task(task_id, status=status)

        elif command == "get-task":
            task_id = sys.argv[2]
            get_task(task_id)

        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
