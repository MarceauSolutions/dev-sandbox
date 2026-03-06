# Universal Agent Orchestrator Guide (v3.4)

A flexible n8n workflow that allows plugging in ANY AI agent (Claude, Grok, custom personas) to perform Claude Code-like actions.

## Overview

The Universal Agent Orchestrator v3 provides:
- **Multi-provider support**: Claude (Anthropic) and Grok (xAI)
- **Tool execution**: File read/write/edit, command execution, git operations, web fetch
- **Search tools**: `grep` (content search) and `glob` (file pattern matching)
- **Agent loop**: Iterative reasoning until task completion
- **Human-in-the-loop (HITL)**: Webhook-based approval workflow for destructive actions
- **Dangerous pattern detection**: Auto-detects rm, git push --force, kill, etc.

## Architecture

```
Webhook/Manual Trigger
        ↓
  Parse Agent Request
        ↓
  Initialize State (Google Sheets)
        ↓
  ┌─────────────────────────────┐
  │      AGENT LOOP             │
  │  Agent Reasoning (AI API)   │
  │         ↓                   │
  │  Parse Tool Request         │
  │         ↓                   │
  │  Tool Router                │
  │    ├─ Python Bridge         │
  │    ├─ Web Fetch             │
  │    └─ Complete              │
  │         ↓                   │
  │  Response Handler           │
  │         ↓                   │
  │  Continue? ─Yes→ Loop       │
  └─────────────────────────────┘
        ↓ No
  Final Response
```

## Components

### 1. n8n Workflow
- **ID**: `1s52PkA1lY1lHfGP`
- **Location**: EC2 at http://34.193.98.97:5678
- **Webhook**: `POST /webhook/agent/execute`

### 2. Python Bridge API
- **Location**: EC2 localhost:5010
- **Source**: `execution/agent_bridge_api.py`

### 3. Google Sheets State
- **Sheet**: Uses existing SMS_Responses sheet ID for Agent_Sessions
- **Columns**: session_id, agent_id, task_objective, status, iteration, etc.

## API Usage

### Basic Request
```bash
curl -X POST http://34.193.98.97:5678/webhook/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent": {
      "id": "claude-code-v1",
      "provider": "anthropic"
    },
    "task": {
      "objective": "Read the CLAUDE.md file and summarize it",
      "context": "/Users/williammarceaujr./dev-sandbox"
    }
  }'
```

### Full Request Schema
```json
{
  "session_id": "optional-custom-id",
  "agent": {
    "id": "claude-code-v1",
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "system_prompt": "Custom system prompt...",
    "tools_available": ["file_read", "file_write", "command", "web_fetch", "git_status"]
  },
  "task": {
    "objective": "What you want the agent to do",
    "context": "Working directory or context",
    "constraints": ["Constraint 1", "Constraint 2"]
  },
  "config": {
    "max_iterations": 20,
    "require_approval_for": ["file_delete", "git_push --force"],
    "notification_channel": "telegram"
  }
}
```

### Using Grok Instead of Claude
```bash
curl -X POST http://34.193.98.97:5678/webhook/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent": {
      "id": "grok-creative",
      "provider": "xai",
      "model": "grok-2-latest"
    },
    "task": {
      "objective": "Generate 5 creative video ideas for fitness content"
    }
  }'
```

## Agent Presets

| Agent ID | Provider | Model | Use Case |
|----------|----------|-------|----------|
| `claude-code-v1` | anthropic | claude-3-5-sonnet | General development |
| `ralph-autonomous` | anthropic | claude-3-5-sonnet | Multi-story autonomous |
| `clawdbot-simple` | anthropic | claude-3-5-sonnet | Quick research |
| `code-reviewer` | anthropic | claude-3-5-sonnet | PR review |
| `grok-creative` | xai | grok-2-latest | Creative content |

## Available Tools

The agent can use these tools during execution:

| Tool | Description | Python Bridge Endpoint | Approval Required |
|------|-------------|------------------------|-------------------|
| `file_read` | Read file contents | `POST /files/read` | No |
| `file_write` | Write/create files | `POST /files/write` | Yes (configurable) |
| `file_edit` | Edit file (line-based) | `POST /files/edit` | Yes (configurable) |
| `file_list` | List directory contents | `POST /files/list` | No |
| `command` | Execute bash command | `POST /command/execute` | Yes (configurable) |
| `git_status` | Get git status | `POST /git/status` | No |
| `git_commit` | Commit changes | `POST /git/commit` | No |
| `git_push` | Push to remote | `POST /git/push` | Yes |
| `grep` | Search file contents (regex) | `POST /search/grep` | No |
| `glob` | Find files by pattern | `POST /files/glob` | No |
| `web_fetch` | Fetch web URL | Native n8n HTTP | No |
| `web_search` | Search the web (DuckDuckGo) | `POST /search/web` | No |
| `todo` | Manage session task list | `POST /todo/*` | No |
| `checkpoint` | Save session state | `POST /session/save` | No |

### Web Search Tool Usage
```json
{"action": "web_search", "input": {"query": "n8n workflow automation 2026", "max_results": 10}}
```

### Checkpoint Tool Usage
Save session state for later resume:
```json
{"action": "checkpoint", "input": {"name": "after-research-phase"}}
```

The checkpoint saves:
- session_id
- agent configuration
- task definition
- current state (messages, todos, plan, etc.)

List saved checkpoints via Python Bridge:
```bash
curl -X POST http://34.193.98.97:5010/session/list -d '{}'
```

Load a checkpoint:
```bash
curl -X POST http://34.193.98.97:5010/session/load \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session_123", "checkpoint_name": "after-research-phase"}'
```

## Plan Mode

Plan mode enables the agent to create a structured plan before execution, which must be approved by a human.

### Enabling Plan Mode
```bash
curl -X POST http://34.193.98.97:5678/webhook/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent": {"id": "claude-code-v1"},
    "task": {"objective": "Build a feature X", "context": "/path"},
    "config": {"plan_mode": true}
  }'
```

### Plan Response Format
When plan_mode is enabled, the agent will respond with:
```json
{"action": "plan", "input": {"title": "Plan Title", "steps": ["Step 1", "Step 2", ...]}}
```

### Approving a Plan
Plans require approval via the HITL webhook:
```bash
curl -X POST "http://34.193.98.97:5678/webhook-waiting/agent-approval/{approval_id}" \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

After approval, the agent executes each step in sequence.

### Known Issue
The n8n EC2 instance has a SQLite issue with webhook resume. If approval fails with "SQLITE_ERROR", restart n8n: `sudo systemctl restart n8n`

## Session Continuation

You can continue a conversation by passing the `session_state` from a previous response:

### Continuing a Session
```bash
curl -X POST http://34.193.98.97:5678/webhook/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "continue_session": true,
    "session_id": "session_12345",
    "session_state": { /* from previous response */ },
    "message": "Your follow-up message here"
  }'
```

### How It Works
1. First request returns session state with response
2. Store the `session_state` from the response
3. Send continuation request with `continue_session: true` and the stored state
4. The agent continues from where it left off with full conversation history

## Background Tasks

Enable background mode to get a task_id and session_state for later result retrieval:

### Enabling Background Mode
```bash
curl -X POST http://34.193.98.97:5678/webhook/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Read the README and summarize it",
    "background": true
  }'
```

### Response with Background Mode
```json
{
  "session_id": "session_123",
  "task_id": "task_abc123",
  "background_mode": true,
  "status": "completed",
  "result": "...",
  "session_state": { /* full session state for continuation */ }
}
```

### Task API (Python Bridge on port 5010)
```bash
# Check task status
curl -X POST http://34.193.98.97:5010/task/status \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_abc123"}'

# Get full result
curl -X POST http://34.193.98.97:5010/task/result \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_abc123"}'

# List all tasks
curl -X POST http://34.193.98.97:5010/task/list -d '{}'
```

## Todo Tracking

The agent can manage a task list during execution using the `todo` tool.

### Todo Operations
```json
// Add a todo
{"action": "todo", "input": {"operation": "add", "content": "Task description"}}

// List todos
{"action": "todo", "input": {"operation": "list"}}

// Update todo status
{"action": "todo", "input": {"operation": "update", "id": "abc123", "status": "completed"}}

// Delete a todo
{"action": "todo", "input": {"operation": "delete", "id": "abc123"}}

// Clear all todos
{"action": "todo", "input": {"operation": "clear"}}
```

### Todo Statuses
- `pending` - Not yet started
- `in_progress` - Currently working on
- `completed` - Done

Todos are stored per session and persist for the duration of the workflow execution.

### Grep Tool Usage
```json
{"action": "grep", "input": {"pattern": "def \\w+", "path": "/home/ec2-user/dev-sandbox", "type": "py", "context": 2, "max_results": 50}}
```

### Glob Tool Usage
```json
{"action": "glob", "input": {"pattern": "**/*.py", "path": "/home/ec2-user/dev-sandbox", "sort_by": "modified", "max_results": 100}}
```

## Human-in-the-Loop (HITL) Approval

v3 introduces webhook-based approval for destructive actions:

### How It Works
1. Agent requests a tool that requires approval (e.g., `command` with `rm -rf`)
2. Workflow detects dangerous pattern or configured approval requirement
3. Workflow pauses and creates a webhook waiting for approval
4. Send POST to `http://34.193.98.97:5678/webhook-waiting/agent-approval/{approval_id}` with `{"approved": true}` or `{"approved": false, "reason": "..."}`
5. Workflow continues based on approval decision

### Dangerous Patterns (Auto-Detected)
- `rm -rf`, `rm -r`, `rmdir`
- `git push`, `git push --force`
- `kill`, `pkill`, `killall`
- `reboot`, `shutdown`
- `chmod 777`, `chown`, `dd if=`, `mkfs`

### Configuring Approval Requirements
```json
{
  "config": {
    "require_approval_for": ["command", "file_write", "file_edit"],
    "approval_timeout_seconds": 300
  }
}
```

### Disabling Approval (Testing Only)
```json
{
  "config": {
    "require_approval_for": []
  }
}
```

## EC2 Deployment

### Deploy Python Bridge API

```bash
# SSH to EC2
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97

# Clone/update dev-sandbox
cd ~/dev-sandbox
git pull origin main

# Install dependencies
pip3 install flask flask-cors

# Start the bridge (background)
nohup python3 -m execution.agent_bridge_api --port 5010 &

# Verify it's running
curl http://localhost:5010/health
```

### Create systemd Service (Recommended)

```bash
# Create service file
sudo tee /etc/systemd/system/agent-bridge.service << EOF
[Unit]
Description=Agent Bridge API
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/dev-sandbox
ExecStart=/usr/bin/python3 -m execution.agent_bridge_api --port 5010
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable agent-bridge
sudo systemctl start agent-bridge

# Check status
sudo systemctl status agent-bridge
```

## Testing

### Test Python Bridge Directly
```bash
# Health check
curl http://localhost:5010/health

# Read file
curl -X POST http://localhost:5010/files/read \
  -H "Content-Type: application/json" \
  -d '{"path": "/home/ec2-user/dev-sandbox/CLAUDE.md"}'

# Execute command
curl -X POST http://localhost:5010/command/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la", "cwd": "/home/ec2-user/dev-sandbox"}'
```

### Test Full Workflow
```bash
# Manual trigger in n8n UI
# Or via webhook:
curl -X POST http://34.193.98.97:5678/webhook/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent": {"id": "claude-code-v1"},
    "task": {"objective": "List files in the current directory"}
  }'
```

## Troubleshooting

### Workflow Not Starting
1. Check n8n is running: `curl http://34.193.98.97:5678/healthz`
2. Activate workflow in n8n UI if inactive
3. Check for credential issues in n8n logs

### Python Bridge Errors
1. Check service status: `systemctl status agent-bridge`
2. Check logs: `journalctl -u agent-bridge -n 50`
3. Verify port 5010 is listening: `netstat -tlpn | grep 5010`

### Agent Not Responding
1. Check API credentials (Anthropic/xAI)
2. Verify model name is correct
3. Check iteration count hasn't exceeded max

### Tool Execution Failing
1. Verify Python Bridge is accessible from n8n
2. Check path is in allowed directories
3. Review Python Bridge logs for errors

## Files

| File | Purpose |
|------|---------|
| `execution/agent_bridge_api.py` | Python Bridge API server |
| `projects/shared/n8n-workflows/universal-agent-orchestrator.json` | n8n workflow |
| `docs/AGENT-ORCHESTRATOR-GUIDE.md` | This documentation |

## Related SOPs

- **SOP 27**: Clawdbot Usage (mobile agent)
- **SOP 28**: Ralph Usage (autonomous development)
- **SOP 29**: Three-Agent Collaboration
- **SOP 30**: n8n Workflow Management

## Version History

### v3.4 (2026-02-07) - Story 9: Background Task Support
- [x] **Background mode**: Enable with `"background": true` in request
- [x] **Task ID generation**: Returns `task_id` for tracking
- [x] **Result persistence**: Results stored in Python Bridge for later retrieval
- [x] **Task API**: `/task/create`, `/task/update`, `/task/status`, `/task/result`, `/task/list` endpoints
- [x] **Session state included**: Background responses include full `session_state`

### v3.3 (2026-02-07) - Story 8: Session Checkpoints
- [x] **Checkpoint tool**: Save session state with `{"action": "checkpoint", "input": {"name": "name"}}`
- [x] **Session storage**: In-memory checkpoint storage on Python Bridge
- [x] **Session API**: `/session/save`, `/session/load`, `/session/list`, `/session/delete` endpoints
- [x] **Task string format**: Accept task as string or object
- [x] **27 nodes total** (added Checkpoint HTTP node)
- [ ] **Session resume**: Resume from checkpoint (planned, not yet implemented)

### v3.2 (2026-02-07) - Stories 4-7
- [x] **Web Search tool**: DuckDuckGo search via Python Bridge (no API key needed)
- [x] **Plan Mode**: Create structured plans before execution (known n8n Wait node bug)
- [x] **Todo Tracking**: Session-based task list management (add/update/list/delete/clear)
- [x] **Session Continuation**: Continue conversations via session_state

### v3.1 (2026-02-07)
- [x] **HITL approval flow**: Webhook-based approval for destructive actions
- [x] **Grep tool**: Search file contents with regex patterns
- [x] **Glob tool**: Find files by glob patterns with sorting
- [x] **Dangerous pattern detection**: Auto-detect rm, kill, git push --force
- [x] **Configurable approvals**: Per-request approval requirements

### v2 (2026-02-06)
- [x] Multi-provider support (Anthropic, xAI)
- [x] File read/write/edit tools
- [x] Command execution
- [x] Git operations
- [x] Web fetch

## Future Enhancements (Phase 3+)

- [ ] Telegram approval buttons for destructive actions
- [ ] Agent registry in Google Sheets
- [x] ~~Checkpoint system (Ralph-style)~~ - Implemented in v3.3
- [ ] Parallel tool execution
- [ ] Execution analytics dashboard
- [ ] Full chat interface with respond action
- [ ] Session resume from checkpoint (checkpoint save done, resume pending)
- [x] ~~Background task support with status checks~~ - Implemented in v3.4
