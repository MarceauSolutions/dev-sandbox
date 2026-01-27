# Clawdbot to Project Folder Integration System

*Created: 2026-01-27*

## Overview

This document defines how Clawdbot (running on VPS) can interact with dev-sandbox projects, including:
- Triggering Claude Code actions
- Merging Clawdbot-generated content into projects
- Moving completed work to appropriate locations
- Monitoring and notifications

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLAWDBOT VPS (44.193.244.59)                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Telegram/WhatsApp → Clawdbot → Claude Max               │    │
│  │                         │                               │    │
│  │                         ▼                               │    │
│  │              Clawdbot Output Files                      │    │
│  │         /home/clawdbot/output/[request-id]/             │    │
│  └─────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │ SSH/SCP
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LOCAL MAC (dev-sandbox)                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Integration Daemon / Manual Trigger                     │    │
│  │                         │                               │    │
│  │                         ▼                               │    │
│  │ Pull Clawdbot outputs → Process → Route to Project      │    │
│  │                                                         │    │
│  │ /Users/williammarceaujr./dev-sandbox/                   │    │
│  │   └── projects/[company]/[project]/                     │    │
│  │       └── clawdbot-contributions/                       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Integration Methods

### Method 1: Manual Pull (Current)

For ad-hoc retrieval of Clawdbot-generated content:

```bash
# Pull specific output from Clawdbot VPS
scp -r clawdbot@44.193.244.59:~/output/request-123/ \
    /Users/williammarceaujr./dev-sandbox/.tmp/clawdbot-pull/

# Review and merge manually
```

### Method 2: Webhook Trigger (Recommended)

Clawdbot notifies Claude Code when work is complete:

```
┌──────────────────────────────────────────────────┐
│ 1. User messages Clawdbot: "Build HVAC template" │
├──────────────────────────────────────────────────┤
│ 2. Clawdbot generates content                    │
├──────────────────────────────────────────────────┤
│ 3. Clawdbot saves to ~/output/req-001/           │
├──────────────────────────────────────────────────┤
│ 4. Clawdbot POST to webhook:                     │
│    {                                             │
│      "request_id": "req-001",                    │
│      "type": "content_ready",                    │
│      "project": "swflorida-hvac",                │
│      "files": ["template.txt", "research.md"],   │
│      "message": "HVAC template ready for review" │
│    }                                             │
├──────────────────────────────────────────────────┤
│ 5. Webhook handler (on Mac) receives, notifies  │
│    Claude Code or queues for action             │
└──────────────────────────────────────────────────┘
```

### Method 3: Scheduled Sync (Background)

Periodic sync of Clawdbot outputs:

```bash
# Cron job on Mac (every 15 minutes)
*/15 * * * * /Users/williammarceaujr./dev-sandbox/scripts/sync-clawdbot-outputs.sh
```

## Project Folder Structure for Clawdbot Content

```
projects/[company]/[project]/
├── src/                          # Human/Claude Code work
├── clawdbot-contributions/       # Clawdbot-generated content
│   ├── PENDING/                  # Awaiting review
│   │   └── req-001/
│   │       ├── MANIFEST.json     # What's in this contribution
│   │       ├── template.txt
│   │       └── research.md
│   ├── APPROVED/                 # Merged into project
│   └── REJECTED/                 # Not used (keep for reference)
```

### MANIFEST.json Schema

```json
{
  "request_id": "req-001",
  "created_at": "2026-01-27T10:30:00Z",
  "source_channel": "telegram",
  "user_message": "Create an HVAC service template",
  "clawdbot_response_summary": "Generated professional HVAC template with 3 sections",
  "files": [
    {
      "filename": "template.txt",
      "type": "text_template",
      "description": "HVAC service description template"
    },
    {
      "filename": "research.md",
      "type": "research_notes",
      "description": "Competitor analysis for HVAC messaging"
    }
  ],
  "suggested_destination": "projects/swflorida-hvac/templates/",
  "requires_action": "review_and_merge"
}
```

## Integration Workflows

### Workflow 1: Research → Implementation

**Scenario**: User asks Clawdbot to research something that needs implementation

```
1. USER → Clawdbot: "Research best practices for HVAC pricing pages"

2. CLAWDBOT: Performs research, generates report
   → Saves to ~/output/req-002/pricing-research.md
   → Sends webhook or notification

3. CLAUDE CODE: Receives notification
   → Pulls research file
   → Shows user: "Clawdbot research ready. Review at clawdbot-contributions/PENDING/req-002/"

4. USER → Claude Code: "Use Clawdbot's research to update pricing page"

5. CLAUDE CODE: Reads research, implements changes
   → Moves to APPROVED/
   → Commits changes
```

### Workflow 2: Content Generation → Merge

**Scenario**: User asks Clawdbot to generate content for a project

```
1. USER → Clawdbot: "Write 5 SMS templates for gym leads"

2. CLAWDBOT: Generates templates
   → Saves to ~/output/req-003/
   → Templates: intro.txt, followup.txt, offer.txt, etc.

3. CLAUDE CODE: Pulls templates
   → Places in clawdbot-contributions/PENDING/req-003/

4. USER → Claude Code: "Merge the gym SMS templates"

5. CLAUDE CODE:
   → Reads templates from PENDING
   → Integrates into projects/shared/lead-scraper/templates/
   → Updates template registry
   → Moves contribution to APPROVED/
   → Commits with reference to Clawdbot request
```

### Workflow 3: App Build Request → Ralph

**Scenario**: User asks Clawdbot to build an app (complex task)

```
1. USER → Clawdbot (WhatsApp): "Build me a fitness tracker app"

2. CLAWDBOT: Recognizes as complex development task
   → Creates initial PRD outline
   → Saves to ~/output/req-004/prd-outline.json
   → Sends notification: "Complex task - routing to Claude Code"

3. WEBHOOK → Claude Code notified

4. CLAUDE CODE:
   → Pulls PRD outline
   → Runs decision engine
   → "Clawdbot created a PRD outline for fitness tracker.
      This looks like a Ralph task (score: 8.5).
      Shall I refine the PRD and start Ralph?"

5. USER → Claude Code: "Yes, use Ralph"

6. RALPH executes autonomously
```

## Scripts and Tools

### sync-clawdbot-outputs.sh

```bash
#!/bin/bash
# /Users/williammarceaujr./dev-sandbox/scripts/sync-clawdbot-outputs.sh

CLAWDBOT_HOST="clawdbot@44.193.244.59"
LOCAL_INBOX="/Users/williammarceaujr./dev-sandbox/.tmp/clawdbot-inbox"
PROCESSED_LOG="$LOCAL_INBOX/.processed"

# Ensure directories exist
mkdir -p "$LOCAL_INBOX"
touch "$PROCESSED_LOG"

# Get list of new outputs from Clawdbot
ssh $CLAWDBOT_HOST "ls ~/output/" 2>/dev/null | while read request_id; do
    if ! grep -q "^$request_id$" "$PROCESSED_LOG"; then
        echo "Syncing: $request_id"
        scp -r "$CLAWDBOT_HOST:~/output/$request_id" "$LOCAL_INBOX/"
        echo "$request_id" >> "$PROCESSED_LOG"

        # Notify (could trigger Claude Code action)
        echo "New Clawdbot output: $request_id" | tee -a "$LOCAL_INBOX/notifications.log"
    fi
done
```

### route-clawdbot-contribution.py

```python
#!/usr/bin/env python3
"""Route Clawdbot contributions to appropriate project folders."""

import json
import shutil
from pathlib import Path
from datetime import datetime

DEV_SANDBOX = Path("/Users/williammarceaujr./dev-sandbox")
INBOX = DEV_SANDBOX / ".tmp" / "clawdbot-inbox"

def route_contribution(request_id: str, project: str):
    """Move Clawdbot contribution to project's pending folder."""
    source = INBOX / request_id
    dest = DEV_SANDBOX / "projects" / project / "clawdbot-contributions" / "PENDING" / request_id

    if not source.exists():
        print(f"Source not found: {source}")
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest)

    # Create manifest if not exists
    manifest_path = dest / "MANIFEST.json"
    if not manifest_path.exists():
        manifest = {
            "request_id": request_id,
            "created_at": datetime.now().isoformat(),
            "routed_at": datetime.now().isoformat(),
            "project": project,
            "files": [f.name for f in dest.iterdir() if f.is_file()],
            "status": "pending_review"
        }
        manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"Routed {request_id} to {project}/clawdbot-contributions/PENDING/")
    return True

def approve_contribution(request_id: str, project: str):
    """Move contribution from PENDING to APPROVED."""
    pending = DEV_SANDBOX / "projects" / project / "clawdbot-contributions" / "PENDING" / request_id
    approved = DEV_SANDBOX / "projects" / project / "clawdbot-contributions" / "APPROVED" / request_id

    if pending.exists():
        approved.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(pending), str(approved))
        print(f"Approved: {request_id}")
        return True
    return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        route_contribution(sys.argv[1], sys.argv[2])
```

## Communication Patterns

### Claude Code to Clawdbot

| Scenario | Action |
|----------|--------|
| "Send via Clawdbot" | Route message through Clawdbot Telegram |
| "Clawdbot, research X" | Forward request to Clawdbot VPS |
| "Check Clawdbot outputs" | Run sync script, show pending |

### Clawdbot to Claude Code

| Scenario | Action |
|----------|--------|
| Complex dev request | Create PRD outline, notify Claude Code |
| Research complete | Save output, send webhook |
| Content generated | Save to output/, create manifest |

## Monitoring Dashboard

### Check Pending Contributions

```bash
# List all pending Clawdbot contributions
find /Users/williammarceaujr./dev-sandbox/projects/*/clawdbot-contributions/PENDING -type d -maxdepth 1
```

### View Recent Notifications

```bash
tail -20 /Users/williammarceaujr./dev-sandbox/.tmp/clawdbot-inbox/notifications.log
```

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| Unauthorized access | SSH key authentication only |
| Malicious content | Review in PENDING before merge |
| Data leakage | VPS isolated from production |
| Webhook spoofing | Signed webhooks with shared secret |

## Future Enhancements

1. **Real-time WebSocket** - Live updates when Clawdbot completes
2. **Auto-routing** - AI-based project detection from content
3. **Conflict detection** - Warn if Clawdbot content overlaps with recent edits
4. **Bi-directional sync** - Push Claude Code results back to Clawdbot

## Related Documents

- [CLAWDBOT-CAPABILITIES.md](CLAWDBOT-CAPABILITIES.md) - Clawdbot overview
- [SOP-27-CLAWDBOT-USAGE.md](SOP-27-CLAWDBOT-USAGE.md) - When to use Clawdbot
- [SOP-28-RALPH-USAGE.md](SOP-28-RALPH-USAGE.md) - Complex task routing
