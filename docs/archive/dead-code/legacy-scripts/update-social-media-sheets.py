#!/usr/bin/env python3
"""
update-social-media-sheets.py - Update n8n workflows with new Google Sheets ID

This script updates the X-Social-Post-Scheduler and Grok B-Roll Generator
workflows to use the correct Google Sheets spreadsheet ID.

USAGE:
    python scripts/update-social-media-sheets.py NEW_SPREADSHEET_ID

EXAMPLE:
    python scripts/update-social-media-sheets.py 1abcdef123456789

The script will:
1. Read the exported workflow JSON files
2. Replace all old/placeholder spreadsheet IDs with the new one
3. Output updated workflow files ready for import

NOTE: To deploy to n8n, use the mcp__n8n__update_workflow_from_file tool
or manually import the updated JSON via n8n UI.
"""

import json
import sys
import os
from pathlib import Path

# Workflow file locations
WORKFLOWS_DIR = Path(__file__).parent.parent / "projects" / "shared" / "n8n-workflows"

WORKFLOWS = {
    "x-social-post-scheduler": {
        "source": "x-social-post-scheduler-latest.json",
        "output": "x-social-post-scheduler-updated.json",
        "workflow_id": "yBcHFdspRnc4gVUB",
        "old_ids": [
            "1AgdGdTLi0E8eZBUZ3yHVCCdVSlXOuxFhOZ7BSXmNbZM",  # Lead Captures (wrong)
        ],
    },
    "grok-broll-generator": {
        "source": "grok-broll-generator-latest.json",
        "output": "grok-broll-generator-updated.json",
        "workflow_id": "sYvUyTooDcHQQuKN",
        "old_ids": [
            "YOUR_GOOGLE_SHEET_ID_HERE",  # Placeholder
        ],
    },
}

# Sheet names expected by each workflow
EXPECTED_SHEETS = {
    "x-social-post-scheduler": ["X_Post_Queue", "X_Post_Analytics"],
    "grok-broll-generator": ["B_Roll_Prompts", "B_Roll_Generated"],
}


def update_workflow(workflow_name: str, new_spreadsheet_id: str) -> dict:
    """Update a workflow with the new spreadsheet ID."""
    config = WORKFLOWS[workflow_name]
    source_path = WORKFLOWS_DIR / config["source"]
    output_path = WORKFLOWS_DIR / config["output"]

    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}")
        return None

    # Read the workflow
    with open(source_path, 'r') as f:
        workflow = json.load(f)

    # Convert to string for replacement
    workflow_str = json.dumps(workflow)

    # Replace all old IDs
    replacements = 0
    for old_id in config["old_ids"]:
        count = workflow_str.count(old_id)
        if count > 0:
            workflow_str = workflow_str.replace(old_id, new_spreadsheet_id)
            replacements += count
            print(f"  Replaced '{old_id}' → '{new_spreadsheet_id}' ({count} times)")

    # Parse back to JSON
    updated_workflow = json.loads(workflow_str)

    # Write the updated workflow
    with open(output_path, 'w') as f:
        json.dump(updated_workflow, f, indent=2)

    print(f"  Output: {output_path}")
    print(f"  Total replacements: {replacements}")

    return {
        "workflow_name": workflow_name,
        "workflow_id": config["workflow_id"],
        "output_path": str(output_path),
        "replacements": replacements,
        "expected_sheets": EXPECTED_SHEETS.get(workflow_name, []),
    }


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        print("\nERROR: Please provide the new spreadsheet ID as an argument.")
        print("\nTo get the spreadsheet ID:")
        print("1. Open your Google Sheet")
        print("2. Look at the URL: docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
        print("3. Copy the ID between /d/ and /edit")
        sys.exit(1)

    new_spreadsheet_id = sys.argv[1]

    # Validate ID format (basic check)
    if len(new_spreadsheet_id) < 20 or " " in new_spreadsheet_id:
        print(f"WARNING: '{new_spreadsheet_id}' doesn't look like a valid Google Sheets ID")
        print("Google Sheet IDs are typically 44 characters of alphanumeric chars")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Updating workflows with new spreadsheet ID:")
    print(f"  {new_spreadsheet_id}")
    print(f"{'='*60}\n")

    results = []

    for workflow_name in WORKFLOWS:
        print(f"\n→ Processing: {workflow_name}")
        result = update_workflow(workflow_name, new_spreadsheet_id)
        if result:
            results.append(result)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    for result in results:
        print(f"\n{result['workflow_name']}:")
        print(f"  Workflow ID: {result['workflow_id']}")
        print(f"  Updated file: {result['output_path']}")
        print(f"  Replacements: {result['replacements']}")
        print(f"  Required sheets: {', '.join(result['expected_sheets'])}")

    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("""
1. Ensure the Google Sheet has the required tabs:
   - X_Post_Queue (with columns: Post_ID, Content, Media_URL, Scheduled_Time, Status, etc.)
   - X_Post_Analytics (with columns: Tweet_ID, Post_ID, Content, Posted_At, etc.)
   - B_Roll_Prompts (with columns: Prompt_ID, Prompt, Category, Status, etc.)
   - B_Roll_Generated (with columns: Image_ID, Prompt_ID, Image_URL, Provider, etc.)

2. Deploy updated workflows to n8n:

   # Option A: Use Claude Code with n8n MCP tools
   # Call mcp__n8n__update_workflow_from_file for each workflow

   # Option B: Manual import via n8n UI
   # 1. Open n8n at http://34.193.98.97:5678
   # 2. For each workflow:
   #    a. Open the workflow
   #    b. Click Settings → Import from File
   #    c. Select the updated JSON file
   #    d. Save and activate

3. Add to .env:
   SOCIAL_MEDIA_SPREADSHEET_ID={new_spreadsheet_id}
""".format(new_spreadsheet_id=new_spreadsheet_id))


if __name__ == "__main__":
    main()
