# Directive: ClickUp CRM Operations

## Goal
Manage client projects, tasks, and workflows in ClickUp CRM (Template Creative Agency space) through natural language commands.

## Inputs
- **Action**: What to do (list, create, update, get, etc.)
- **Entity**: What to act on (tasks, spaces, lists, folders)
- **Parameters**: Specific details (task name, status, assignee, etc.)
- **Space**: Usually "Template Creative Agency"

## Tools
- `execution/clickup_api.py` - Python wrapper for ClickUp API
  - `list-workspaces` - Show all workspaces
  - `list-spaces` - Show all spaces in workspace
  - `list-tasks --space "NAME"` - List tasks in a space
  - `create-task "NAME" --list ID` - Create new task
  - `update-task ID --status "STATUS"` - Update task
  - `get-task ID` - Get task details

## Process

### 1. List Tasks in Template Creative Agency
```bash
python execution/clickup_api.py list-tasks --space "Template Creative Agency"
```

### 2. Create a New Client Project Task
```bash
python execution/clickup_api.py create-task "Client: John Smith" --list LIST_ID
```

### 3. Update Task Status
```bash
python execution/clickup_api.py update-task TASK_ID --status "in progress"
```

### 4. Get Task Details
```bash
python execution/clickup_api.py get-task TASK_ID
```

## Common Workflows

### New Client Onboarding in ClickUp
1. User says: "Add new client John Smith to ClickUp for website redesign"
2. Get list ID for appropriate list (e.g., "New Clients" or "Active Projects")
3. Create task with client name and project description
4. Optionally: Send onboarding email using `send_onboarding_email.py`
5. Return confirmation with task URL

### Update Project Status
1. User says: "Move John Smith's project to In Progress"
2. Search for task by name
3. Update status to "in progress"
4. Confirm update

### Check All Active Projects
1. User says: "Show me all active projects"
2. List all tasks in Template Creative Agency space
3. Filter by status if needed
4. Display formatted list

## Outputs
- **Task list**: Formatted list of tasks with status and assignees
- **Task details**: Full information about a specific task
- **Confirmation**: Success message with task ID and URL
- **Error messages**: Clear feedback if something fails

## Edge Cases
- **Missing API token**: Prompt user to add CLICKUP_API_TOKEN to .env
- **Space not found**: Check space name spelling, list available spaces
- **Invalid task ID**: Verify task exists before updating
- **Rate limiting**: ClickUp API has rate limits (100 requests/minute), implement retry logic
- **Multiple spaces with same name**: Use space ID instead of name
- **Task already exists**: Check for duplicates before creating
- **Invalid status**: Check valid statuses for the list before updating

## Configuration Required

In `.env`:
```
CLICKUP_CLIENT_ID=DDD9MRAU4YGM2F0B9LOW4YVJLPLNZW7X
CLICKUP_CLIENT_SECRET=HIBFCMFWMNU2WQBLKKCYUHHKVOXW51R64SD335I7EAGDDV39D8Q3FGUNK7L64MR9
CLICKUP_API_TOKEN=your-clickup-api-token
CLICKUP_WORKSPACE_ID=your-workspace-id
CLICKUP_SPACE_NAME=Template Creative Agency
```

## Integration with Other Workflows

### Client Onboarding (Combined)
1. User: "Onboard john@example.com with name John Smith for website redesign"
2. Send onboarding email (`send_onboarding_email.py`)
3. Create ClickUp task for the project
4. Link task URL in confirmation

### Status Updates
1. Client books kickoff call (from Calendly webhook)
2. Update ClickUp task status to "Kickoff Scheduled"
3. Add comment with meeting details

## Learnings
(Updated as system self-anneals)
- Initial creation: 2026-01-03
- ClickUp API requires personal API token for authentication
- OAuth is for third-party apps, API token is simpler for personal use
