# Clawdbot Request Monitoring & Action System

*Created: 2026-01-27*

## Overview

This system monitors Clawdbot activity and triggers appropriate actions when:
1. Clawdbot completes a task requiring Claude Code follow-up
2. Complex development requests need to be routed to Ralph
3. Content is ready for integration into projects

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLAWDBOT VPS                                │
│  User Request → Clawdbot → Output + Notification               │
│                              │                                  │
│                              ▼                                  │
│                    ~/output/[request-id]/                       │
│                    notification.json (webhook payload)          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
     ┌──────────────┐  ┌─────────────┐  ┌──────────────┐
     │ Webhook      │  │ Polling     │  │ Manual       │
     │ (Instant)    │  │ (Scheduled) │  │ (On-demand)  │
     └──────┬───────┘  └──────┬──────┘  └──────┬───────┘
            │                 │                │
            └─────────────────┼────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────────┐
            │        Action Router                │
            │  ┌─────────────────────────────┐    │
            │  │ Classify Request Type       │    │
            │  │ - research_complete         │    │
            │  │ - content_ready             │    │
            │  │ - complex_dev_request       │    │
            │  │ - simple_notification       │    │
            │  └─────────────────────────────┘    │
            └──────────────────┬──────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
     ┌──────────────┐  ┌─────────────┐  ┌──────────────┐
     │ Notify User  │  │ Route to    │  │ Trigger      │
     │ (Terminal)   │  │ Project     │  │ Ralph        │
     └──────────────┘  └─────────────┘  └──────────────┘
```

## Notification Types

| Type | Description | Action |
|------|-------------|--------|
| `research_complete` | Clawdbot finished researching | Route to project, notify user |
| `content_ready` | Generated content (templates, copy) | Route to project, await review |
| `complex_dev_request` | User asked Clawdbot to build something | Create PRD outline, route to Ralph |
| `simple_notification` | Informational message | Display notification only |
| `error` | Clawdbot encountered error | Log and alert |

## Notification Schema

```json
{
  "request_id": "req-001",
  "timestamp": "2026-01-27T10:30:00Z",
  "type": "content_ready",
  "source_channel": "telegram",
  "user_message": "Create 5 SMS templates for gym leads",
  "summary": "Generated 5 SMS templates with personalization",
  "files": [
    {"name": "intro.txt", "type": "template", "size": 245},
    {"name": "followup.txt", "type": "template", "size": 189}
  ],
  "suggested_project": "shared/lead-scraper",
  "suggested_action": "route_and_review",
  "priority": "normal",
  "metadata": {
    "tokens_used": 1234,
    "duration_ms": 5600
  }
}
```

## Components

### 1. Webhook Receiver (webhook_receiver.py)

Local HTTP server that receives webhooks from Clawdbot VPS.

```bash
# Start webhook receiver
python scripts/clawdbot-webhook-receiver.py --port 8765
```

### 2. Polling Monitor (polling_monitor.py)

Checks VPS for new outputs on a schedule.

```bash
# Run once
python scripts/clawdbot-polling-monitor.py

# Run continuously (every 5 minutes)
python scripts/clawdbot-polling-monitor.py --daemon --interval 300
```

### 3. Action Router (action_router.py)

Processes notifications and routes to appropriate handlers.

### 4. Terminal Notifier

Displays notifications in Claude Code terminal.

## Implementation Files

### scripts/clawdbot-webhook-receiver.py

```python
#!/usr/bin/env python3
"""
Webhook receiver for Clawdbot notifications.
Listens for POST requests and routes to action handler.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from pathlib import Path

NOTIFICATIONS_DIR = Path("/Users/williammarceaujr./dev-sandbox/.tmp/clawdbot-notifications")
NOTIFICATIONS_DIR.mkdir(parents=True, exist_ok=True)

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data)
            request_id = payload.get('request_id', 'unknown')

            # Save notification
            notification_file = NOTIFICATIONS_DIR / f"{request_id}.json"
            notification_file.write_text(json.dumps(payload, indent=2))

            # Trigger action router
            from action_router import route_notification
            route_notification(payload)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "received"}')

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'{{"error": "{str(e)}"}}'.encode())

def run(port=8765):
    server = HTTPServer(('localhost', port), WebhookHandler)
    print(f"Clawdbot webhook receiver listening on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    import sys
    port = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--port" else 8765
    run(port)
```

### scripts/clawdbot-action-router.py

```python
#!/usr/bin/env python3
"""
Route Clawdbot notifications to appropriate actions.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

DEV_SANDBOX = Path("/Users/williammarceaujr./dev-sandbox")
NOTIFICATIONS_LOG = DEV_SANDBOX / ".tmp" / "clawdbot-notifications" / "actions.log"

def log_action(request_id: str, action: str, details: str = ""):
    """Log action taken."""
    NOTIFICATIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(NOTIFICATIONS_LOG, "a") as f:
        f.write(f"[{timestamp}] {request_id}: {action} - {details}\n")

def notify_terminal(message: str, title: str = "Clawdbot"):
    """Display notification in terminal and macOS notification center."""
    print(f"\n{'='*60}")
    print(f"🤖 {title}")
    print(f"{'='*60}")
    print(message)
    print(f"{'='*60}\n")

    # Also send macOS notification
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ], capture_output=True)
    except:
        pass

def route_notification(payload: dict):
    """Route notification to appropriate handler."""
    request_id = payload.get("request_id", "unknown")
    notification_type = payload.get("type", "simple_notification")
    summary = payload.get("summary", "No summary")
    suggested_project = payload.get("suggested_project", "")
    suggested_action = payload.get("suggested_action", "")

    if notification_type == "content_ready":
        # Content generated - route to project
        notify_terminal(
            f"Request: {request_id}\n"
            f"Summary: {summary}\n"
            f"Suggested project: {suggested_project}\n"
            f"\nRun: ./scripts/sync-clawdbot-outputs.sh\n"
            f"Then: python scripts/route-clawdbot-contribution.py route {request_id} {suggested_project}",
            title="Clawdbot Content Ready"
        )
        log_action(request_id, "content_ready", f"Project: {suggested_project}")

    elif notification_type == "complex_dev_request":
        # Complex request - route to Ralph
        notify_terminal(
            f"Request: {request_id}\n"
            f"Summary: {summary}\n"
            f"\n⚠️ This looks like a complex development task.\n"
            f"Clawdbot has created a PRD outline.\n"
            f"\nRun: ./scripts/sync-clawdbot-outputs.sh\n"
            f"Then review PRD at: .tmp/clawdbot-inbox/{request_id}/prd-outline.json\n"
            f"Consider using Ralph for implementation.",
            title="Clawdbot → Ralph Handoff"
        )
        log_action(request_id, "complex_dev_request", "Routed to Ralph consideration")

    elif notification_type == "research_complete":
        # Research done - notify and route
        notify_terminal(
            f"Request: {request_id}\n"
            f"Summary: {summary}\n"
            f"Suggested project: {suggested_project}\n"
            f"\nResearch files ready for review.\n"
            f"Run: ./scripts/sync-clawdbot-outputs.sh",
            title="Clawdbot Research Complete"
        )
        log_action(request_id, "research_complete", f"Project: {suggested_project}")

    elif notification_type == "error":
        # Error occurred
        error_msg = payload.get("error", "Unknown error")
        notify_terminal(
            f"Request: {request_id}\n"
            f"Error: {error_msg}\n"
            f"\nCheck Clawdbot logs for details.",
            title="⚠️ Clawdbot Error"
        )
        log_action(request_id, "error", error_msg)

    else:
        # Simple notification
        notify_terminal(
            f"Request: {request_id}\n"
            f"{summary}",
            title="Clawdbot Notification"
        )
        log_action(request_id, notification_type, summary)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Load notification from file
        notification_file = Path(sys.argv[1])
        if notification_file.exists():
            payload = json.loads(notification_file.read_text())
            route_notification(payload)
        else:
            print(f"File not found: {notification_file}")
    else:
        print("Usage: python clawdbot-action-router.py <notification.json>")
```

## Clawdbot VPS Setup

To enable notifications from Clawdbot, add this to the Clawdbot skill that handles task completion:

```python
# On Clawdbot VPS - after completing a task

import requests
import json
from datetime import datetime

def notify_claude_code(request_id, notification_type, summary, files=None, suggested_project=None):
    """Send notification to Claude Code."""
    payload = {
        "request_id": request_id,
        "timestamp": datetime.now().isoformat(),
        "type": notification_type,
        "summary": summary,
        "files": files or [],
        "suggested_project": suggested_project,
        "source_channel": "clawdbot"
    }

    # Save locally first
    output_dir = Path.home() / "output" / request_id
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "notification.json").write_text(json.dumps(payload, indent=2))

    # Try webhook (if Claude Code is listening)
    try:
        # This requires port forwarding or ngrok from Mac
        # Alternative: polling-based detection
        pass
    except:
        pass
```

## Communication Patterns

| Claude Code Says | System Does |
|------------------|-------------|
| "Check Clawdbot notifications" | List pending notifications |
| "Process Clawdbot output" | Sync + route latest |
| "Start Clawdbot monitor" | Launch polling daemon |
| "Show Clawdbot activity" | Display recent actions log |

## Monitoring Commands

```bash
# Check for new outputs
./scripts/sync-clawdbot-outputs.sh

# View action log
tail -20 .tmp/clawdbot-notifications/actions.log

# List pending contributions
python scripts/route-clawdbot-contribution.py list

# Start webhook receiver (requires port forwarding)
python scripts/clawdbot-webhook-receiver.py --port 8765
```

## Integration with Claude Code

When Claude Code starts, it should:
1. Check for pending Clawdbot notifications
2. Display any unprocessed items
3. Offer to route/process them

Example startup check:
```
🤖 Clawdbot Status:
   - 2 unprocessed notifications
   - 1 pending contribution (req-003 → shared/lead-scraper)

   Run "Check Clawdbot notifications" for details.
```

## Related Documents

- [CLAWDBOT-PROJECT-INTEGRATION.md](CLAWDBOT-PROJECT-INTEGRATION.md) - Full integration guide
- [CLAWDBOT-CAPABILITIES.md](CLAWDBOT-CAPABILITIES.md) - Clawdbot overview
- [SOP-27-CLAWDBOT-USAGE.md](SOP-27-CLAWDBOT-USAGE.md) - When to use Clawdbot
