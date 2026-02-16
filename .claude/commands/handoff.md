Manage handoffs between Claude Code (Mac), Clawdbot (EC2/Telegram), and Ralph (EC2/autonomous).

**Source of truth**: `HANDOFF.md` (human-readable) + `ralph/handoffs.json` (machine-readable). Both MUST stay in sync.

## On invocation, follow this procedure:

### Step 1: Pull latest and read current state
```bash
cd ~/dev-sandbox && git pull --rebase 2>/dev/null || true
```
Then read both `HANDOFF.md` and `ralph/handoffs.json`.

### Step 2: Determine action from $ARGUMENTS

| Argument | Action |
|----------|--------|
| `status` or (empty) | Show summary: pending for Mac, pending for EC2, in-progress, recently completed |
| `to ec2: <description>` | Create task for Clawdbot/Ralph to pick up |
| `to mac: <description>` | Create task for Claude Code (normally done by Clawdbot) |
| `complete <task-title>` | Move task to "Recently Completed" with timestamp |
| `clear completed` | Archive completed tasks older than 7 days |

### Step 3: When creating a handoff task

Generate a unique ID: `handoff-YYYYMMDD-HHMM`

**Add to HANDOFF.md** in the appropriate section:
```markdown
### Task: <Title>
- **From**: claude_code | clawdbot | ralph
- **Priority**: high | medium | low
- **Created**: YYYY-MM-DD HH:MM UTC
- **Context**: <What was done, what's needed next>
- **Files**: <Key file paths involved>
- **Action**: <Specific next step for receiving agent>
```

**Add to ralph/handoffs.json** in the matching array (`pending_for_mac` or `pending_for_ec2`):
```json
{
  "id": "handoff-YYYYMMDD-HHMM",
  "title": "<Title>",
  "from": "claude_code",
  "priority": "medium",
  "created": "<ISO 8601>",
  "context": "<What was done>",
  "files": ["<paths>"],
  "action": "<Next step>"
}
```

Also update `agents.claude_code.last_seen` to current timestamp.

### Step 4: When completing a handoff task

1. Remove from `pending_for_mac` or `pending_for_ec2` in handoffs.json
2. Add to `completed` array with `completed_at` and `completed_by` fields
3. Move entry in HANDOFF.md from pending section to "Recently Completed"
4. Keep only last 10 completed entries

### Step 5: Commit and push

After any modification:
```bash
git add HANDOFF.md ralph/handoffs.json
git commit -m "handoff: <brief description of what changed>"
git push
```

### Context for good handoffs

When handing off TO EC2, include:
- What you just finished building/fixing
- What files were changed and why
- What the next step requires (and why it needs EC2 — e.g., 24/7 monitoring, bulk processing, Ralph complexity)

When handing off TO Mac, include:
- What Clawdbot/Ralph built
- What needs Mac-specific tools (deployment, PyPI, interactive testing, MCP publishing)
- Any blockers or decisions needed from William

### Three-Agent Routing Reference

| Complexity | Route To | Examples |
|-----------|----------|----------|
| 0-3 | Clawdbot | Quick research, file edits, status checks |
| 4-6 | Clawdbot | Feature additions, API integrations, content generation |
| 7-10 | Ralph (via Clawdbot) | Full system builds, multi-file refactors, new projects |
| Mac-only | Claude Code | PyPI deployment, MCP publishing, interactive debugging, OAuth |
