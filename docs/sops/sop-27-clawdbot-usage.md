# SOP 27: Clawdbot Usage Protocol

**Created**: 2026-01-27
**Purpose**: Define when and how to use Clawdbot vs Claude Code vs Ralph

---

## Overview

Clawdbot is a personal AI assistant accessible via Telegram, WhatsApp, and iMessage. It runs on a dedicated VPS (44.193.244.59) using Claude Max OAuth subscription.

---

## When to Use Clawdbot

### ✅ Use Clawdbot For

| Use Case | Example | Why Clawdbot |
|----------|---------|--------------|
| **Quick questions on the go** | "What's the weather in Naples?" | Mobile-friendly, instant access |
| **Scheduling & reminders** | "Remind me to call John at 3pm" | Always accessible via phone |
| **Simple lookups** | "What's the status of lead-scraper?" | Quick info without terminal |
| **Message drafting** | "Draft an email to the HVAC client" | Compose while away from desk |
| **Personal assistant tasks** | "Add milk to my shopping list" | Conversational interface |
| **Quick research** | "Find the best time to post on Instagram" | Web search while mobile |
| **Status checks** | "How many leads did we contact today?" | Quick metrics access |

### ❌ Don't Use Clawdbot For

| Use Case | Why Not | Use Instead |
|----------|---------|-------------|
| **Multi-file development** | Can't edit files directly | Claude Code |
| **Complex coding tasks** | No file system access | Claude Code |
| **Autonomous development loops** | Needs PRD structure | Ralph via Claude Code |
| **Git operations** | No repo access | Claude Code |
| **Debugging with logs** | Can't read local files | Claude Code |
| **Large refactoring** | Multi-step, file-heavy | Ralph |

---

## Access Methods

### Via Telegram (Recommended)

1. Open Telegram app
2. Search for `@W_marceaubot`
3. Send direct message
4. Receives response via Claude Max

**Best for**: Quick interactions, mobile, when away from computer

### Via WhatsApp

1. Open WhatsApp
2. Message the linked personal number
3. Clawdbot responds (if logged in and active)

**Best for**: When Telegram unavailable, personal conversations

### Via iMessage (If Configured)

1. Send iMessage to configured number
2. Response routed through Clawdbot

**Note**: Verify iMessage channel is active before relying on it

---

## Communication Patterns

### Effective Clawdbot Prompts

| Task | Good Prompt | Bad Prompt |
|------|-------------|------------|
| Research | "What are the top 3 fitness influencer pain points?" | "Research fitness" |
| Scheduling | "Schedule a call with John tomorrow at 2pm EST" | "Schedule something" |
| Drafting | "Draft a follow-up email to the HVAC lead who asked about pricing" | "Write email" |
| Status | "What's the response rate on our SMS campaign?" | "How's it going?" |

### Context Awareness

Clawdbot may not have context from:
- Previous Claude Code sessions
- Local file changes
- Recent Ralph executions

**Best Practice**: Provide relevant context in your message if needed.

---

## Clawdbot vs Claude Code vs Ralph Decision Tree

```
Is this a coding task?
├── YES: Does it involve multiple files or complex logic?
│   ├── YES: Is it a multi-story development effort?
│   │   ├── YES → Use RALPH (via Claude Code)
│   │   └── NO  → Use CLAUDE CODE
│   └── NO → Use CLAUDE CODE
└── NO: Can it be done conversationally?
    ├── YES: Are you at your computer?
    │   ├── YES → Either works (preference)
    │   └── NO  → Use CLAWDBOT
    └── NO → Use CLAUDE CODE
```

### Quick Reference Matrix

| Task Type | Clawdbot | Claude Code | Ralph |
|-----------|----------|-------------|-------|
| Quick question | ✅ Best | ✓ OK | ❌ |
| Research | ✅ Best | ✓ OK | ❌ |
| Single file edit | ❌ | ✅ Best | ❌ |
| Multi-file feature | ❌ | ✅ Best | ✓ Consider |
| Complex system build | ❌ | ✓ Trigger | ✅ Best |
| Scheduling | ✅ Best | ❌ | ❌ |
| Code debugging | ❌ | ✅ Best | ❌ |
| Git operations | ❌ | ✅ Best | ❌ |
| Mobile access | ✅ Only | ❌ | ❌ |

---

## Clawdbot Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| No file system access | Can't edit local files | Use Claude Code for file operations |
| No git access | Can't commit/push | Use Claude Code for git |
| Memory disabled | Context resets between conversations | Re-state context as needed |
| OpenAI embeddings limited | Memory plugin not fully functional | Awaiting Ollama integration |
| Single conversation thread | Can't maintain multiple parallel tasks | Use Claude Code for complex workflows |

---

## Integration with Claude Code

### Handoff Pattern: Clawdbot → Claude Code

When Clawdbot task needs development:

1. **Clawdbot**: Research/explore the task
2. **Clawdbot**: Summarize findings
3. **User**: Open Claude Code
4. **User**: "Based on [Clawdbot research], implement X"
5. **Claude Code**: Executes with file access

### Handoff Pattern: Claude Code → Clawdbot

When done coding and need follow-up:

1. **Claude Code**: Complete development
2. **User**: Switch to Clawdbot
3. **User**: "Update John that the feature is ready"
4. **Clawdbot**: Drafts/sends message

---

## Best Practices

### Do

- ✅ Use Clawdbot for quick, conversational tasks
- ✅ Provide context when needed (it may not know recent changes)
- ✅ Use Telegram for most reliable access
- ✅ Keep requests self-contained

### Don't

- ❌ Ask Clawdbot to edit files
- ❌ Expect context from Claude Code sessions
- ❌ Use for time-critical development tasks
- ❌ Rely on memory between conversations

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No response from Telegram | Service may be down | SSH to VPS, check systemctl status |
| "Cannot access files" | Clawdbot has no file system access | Use Claude Code instead |
| Slow responses | VPS resource constraints | Check EC2 instance health |
| Context seems wrong | Memory disabled | Re-state relevant context |

### Health Check Commands

```bash
# Check service status
ssh clawdbot@44.193.244.59 "systemctl status clawdbot"

# View recent logs
ssh clawdbot@44.193.244.59 "journalctl -u clawdbot --since '1 hour ago'"

# Restart service
ssh clawdbot@44.193.244.59 "sudo systemctl restart clawdbot"
```

---

## Related Documents

- [CLAWDBOT-CAPABILITIES.md](CLAWDBOT-CAPABILITIES.md) - Full capability inventory
- [SOP-28-RALPH-USAGE.md](SOP-28-RALPH-USAGE.md) - Ralph autonomous agent
- CLAUDE.md - Claude Code communication patterns
