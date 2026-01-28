# Autonomous Development Architecture

*Last Updated: 2026-01-28*
*Vision: Mobile-first, 24/7 autonomous software development*

---

## Executive Summary

This document defines the long-term architecture for enabling fully autonomous software development from mobile devices. The goal: pick up your phone anytime, tell Clawdbot to build something, and wake up to completed, tested, deployed code.

---

## The Three-Tier AI Development System

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER (Mobile/Desktop)                             │
│                    Telegram | WhatsApp | iMessage | Terminal             │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLAWDBOT      │    │   CLAUDE CODE   │    │     RALPH       │
│   (VPS 24/7)    │◄──►│   (Mac Local)   │◄──►│   (VPS 24/7)    │
│                 │    │                 │    │                 │
│ • Mobile access │    │ • Interactive   │    │ • Autonomous    │
│ • Quick tasks   │    │ • Complex dev   │    │ • PRD execution │
│ • Research      │    │ • File editing  │    │ • Multi-story   │
│ • PRD creation  │    │ • Git ops       │    │ • Quality gates │
│ • Orchestration │    │ • Deployment    │    │ • Auto-commit   │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │   SHARED RESOURCES    │
                    │                       │
                    │ • GitHub (dev-sandbox)│
                    │ • Webhook Hub (EC2)   │
                    │ • Docket Queue        │
                    │ • Progress Log        │
                    └───────────────────────┘
```

---

## Infrastructure Map

| Component | Location | IP/Host | Availability | Purpose |
|-----------|----------|---------|--------------|---------|
| **Clawdbot** | EC2 VPS | 44.193.244.59 | 24/7 | Mobile AI assistant, orchestration |
| **Claude Code** | Mac Local | localhost | When Mac awake | Interactive development |
| **Ralph** | EC2 VPS | 44.193.244.59 | 24/7 | Autonomous PRD execution |
| **Web Services** | EC2 | 34.193.98.97 | 24/7 | Websites, APIs, Webhooks |
| **dev-sandbox** | GitHub | github.com/wmarceau | 24/7 | Central code repository |

---

## The Complete Autonomous Flow

### Scenario: Mobile Request → Autonomous Build → Completed Code

```
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 1: USER → CLAWDBOT (Mobile, any time)                              │
│                                                                          │
│ User (WhatsApp, 2 AM): "Build a campaign template system for dentists"  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────┐
│ STEP 2: CLAWDBOT ANALYZES & ROUTES                                       │
│                                                                          │
│ Clawdbot (VPS):                                                          │
│   ✅ Recognizes as development task (complexity score: 7.5)              │
│   ✅ Creates PRD with 5 stories                                          │
│   ✅ Saves to /home/clawdbot/ralph/prd-dental-templates.json            │
│   ✅ Responds: "Created PRD. Starting autonomous development..."         │
│   ✅ Triggers Ralph via systemd                                          │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────┐
│ STEP 3: RALPH EXECUTES AUTONOMOUSLY                                      │
│                                                                          │
│ Ralph (VPS, runs while you sleep):                                       │
│   Story 1: Database schema for templates         ✅ (12 min)            │
│   Story 2: Template service with CRUD            ✅ (18 min)            │
│   Story 3: API endpoints                         ✅ (15 min)            │
│   Story 4: Personalization engine                ✅ (22 min)            │
│   Story 5: Tests and documentation               ✅ (10 min)            │
│   ───────────────────────────────────────────────────────────           │
│   TOTAL: 77 minutes autonomous execution                                 │
│                                                                          │
│   ✅ All quality gates passed (typecheck, lint, tests)                  │
│   ✅ Committed to dev-sandbox: feat(dental): Add template system        │
│   ✅ Pushed to GitHub                                                    │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────┐
│ STEP 4: COMPLETION NOTIFICATION                                          │
│                                                                          │
│ Clawdbot → User (WhatsApp, 3:17 AM):                                    │
│   "🎉 Dental template system complete!                                   │
│    ✅ 5/5 stories done (77 min)                                         │
│    📁 Created: template_service.py, api.py, tests/, README.md           │
│    🔗 Committed: feat(dental): Add template system                      │
│    📊 Quality: All checks passed                                        │
│                                                                          │
│    Ready for your review when you wake up!"                             │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────┐
│ STEP 5: MORNING REVIEW (Optional)                                        │
│                                                                          │
│ User (8 AM): "Show me what Ralph built"                                 │
│ Clawdbot: [Provides code summary, key files, test results]              │
│                                                                          │
│ User: "Looks good, deploy to PyPI"                                      │
│ Clawdbot: [Triggers SOP 11-13 via Ralph]                                │
│                                                                          │
│ User: [Goes to gym while deployment runs]                               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Clawdbot (Orchestration Layer)

**Current State:**
- ✅ Running 24/7 on EC2 VPS
- ✅ Accessible via Telegram (@W_marceaubot), WhatsApp
- ✅ Claude Max OAuth (unlimited conversations)
- ⚠️ Memory disabled (OpenAI quota exceeded)
- ❌ Cannot trigger Ralph (not installed on VPS)

**Target State:**
- ✅ Memory restored (Ollama embeddings)
- ✅ Can create PRDs for development requests
- ✅ Can trigger Ralph on VPS
- ✅ Receives completion notifications
- ✅ Can read code from dev-sandbox for review
- ✅ Can trigger deployments

**Directory Structure (VPS):**
```
/home/clawdbot/
├── .clawdbot/
│   ├── clawdbot.json           # Main config
│   ├── .env                     # Environment (+ OLLAMA_API_URL)
│   ├── agents/main/agent/
│   │   └── auth-profiles.json  # Claude Max OAuth
│   ├── skills/                  # 54+ skills
│   └── plugins/
│       ├── memory-lancedb/     # → Update for Ollama
│       ├── telegram/            # Active
│       └── whatsapp/           # Active
├── output/                      # Generated content
│   └── req-{id}/               # Per-request outputs
├── ralph/                       # NEW: Ralph execution space
│   ├── prd-*.json              # PRD files
│   ├── progress.txt            # Learning log
│   └── AGENTS.md               # Codebase patterns
└── dev-sandbox/                 # NEW: Git clone of main repo
    └── (synced with GitHub)
```

### 2. Ralph (Autonomous Execution Layer)

**Current State:**
- ✅ Working on local Mac
- ✅ PRD-based multi-story execution
- ✅ Fresh context per iteration (memory via git/progress.txt)
- ✅ Quality gates (typecheck, lint, tests)
- ❌ Not installed on VPS

**Target State:**
- ✅ Installed on Clawdbot VPS
- ✅ Can be triggered by Clawdbot
- ✅ Commits directly to dev-sandbox clone
- ✅ Pushes to GitHub when complete
- ✅ Sends completion webhook

**Ralph Execution Loop:**
```
1. Load PRD (prd-{name}.json)
2. Pick next uncompleted story
3. Fresh Claude instance implements story
4. Run quality checks
5. If pass → commit → mark story complete
6. Log learnings to progress.txt
7. Repeat until all stories done
8. Send completion notification
```

**Key Files (VPS):**
```
/home/clawdbot/ralph/
├── ralph.sh                    # Execution script
├── prompt.md                   # Agent instructions
├── AGENTS.md                   # Codebase knowledge
├── prd-{name}.json            # Active PRD
└── progress.txt               # Learning log
```

### 3. Claude Code (Interactive Layer)

**Role in Autonomous System:**
- Interactive development (when user is at Mac)
- Complex debugging and exploration
- Review and polish Ralph's work
- Deployment verification
- Manual overrides when needed

**Integration Points:**
- Pulls from same GitHub repo as Ralph
- Can review Ralph's commits
- Can continue Ralph's work if interrupted
- Shares AGENTS.md patterns with Ralph

### 4. Webhook Hub (Communication Layer)

**Location:** EC2 Web Services (34.193.98.97)

**Endpoints:**
```
POST /webhook/clawdbot/task-created
  → Logs new task, updates docket

POST /webhook/ralph/story-complete
  → Updates progress, notifies Clawdbot

POST /webhook/ralph/prd-complete
  → Final notification, triggers sync

POST /webhook/deployment/status
  → Tracks deployment progress
```

**Docket System:**
```json
{
  "tasks": [
    {
      "id": "req-001",
      "type": "development",
      "description": "Build dental template system",
      "priority": "high",
      "status": "in_progress",
      "prd_path": "/home/clawdbot/ralph/prd-dental.json",
      "created_at": "2026-01-28T02:00:00Z",
      "started_at": "2026-01-28T02:01:00Z",
      "completed_at": null,
      "stories_complete": 3,
      "stories_total": 5
    }
  ]
}
```

### 5. Git Sync (Data Layer)

**Bidirectional Sync Pattern:**
```
GitHub (dev-sandbox main)
        ↑↓
   ┌────┴────┐
   │         │
   ▼         ▼
VPS Clone   Mac Local
(Ralph)     (Claude Code)
```

**Sync Rules:**
- VPS pulls before Ralph starts
- VPS pushes after Ralph completes
- Mac pulls on session start
- Mac pushes on session end
- Conflicts: VPS creates branch, Mac resolves

**Cron Jobs (VPS):**
```bash
# Every 5 minutes: Check for new PRDs
*/5 * * * * /home/clawdbot/ralph/check-for-prds.sh

# Before Ralph starts: Pull latest
0 * * * * cd /home/clawdbot/dev-sandbox && git pull origin main
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal:** Fix Clawdbot memory, establish basic sync

| Task | Time | Owner |
|------|------|-------|
| Fix Ollama memory integration | 2h | Claude Code |
| Test Clawdbot memory persistence | 1h | Manual |
| Create sync daemon script | 2h | Claude Code |
| Test Clawdbot output sync | 1h | Manual |

**Success Criteria:**
- [ ] Clawdbot remembers context between conversations
- [ ] Clawdbot outputs sync to Mac within 5 minutes

### Phase 2: Ralph on VPS (Week 2)
**Goal:** Enable autonomous code execution

| Task | Time | Owner |
|------|------|-------|
| SSH into VPS, install Amp CLI | 1h | Manual |
| Copy Ralph scripts to VPS | 30m | Claude Code |
| Clone dev-sandbox to VPS | 30m | Manual |
| Configure git credentials on VPS | 30m | Manual |
| Test Ralph execution on VPS | 2h | Manual |
| Create PRD trigger mechanism | 2h | Claude Code |

**Success Criteria:**
- [ ] Ralph runs on VPS successfully
- [ ] Ralph commits push to GitHub
- [ ] PRD creation triggers Ralph automatically

### Phase 3: Webhook Orchestration (Week 3)
**Goal:** Full communication between all components

| Task | Time | Owner |
|------|------|-------|
| Deploy webhook server on EC2 | 3h | Claude Code |
| Implement docket system | 2h | Claude Code |
| Add completion notifications | 2h | Claude Code |
| Connect Clawdbot to webhooks | 2h | Claude Code |
| End-to-end testing | 3h | Manual |

**Success Criteria:**
- [ ] Mobile request → Clawdbot → Ralph → Completion notification
- [ ] Full audit trail in docket
- [ ] User notified via Telegram when done

### Phase 4: Polish & Hardening (Week 4)
**Goal:** Production-ready autonomous system

| Task | Time | Owner |
|------|------|-------|
| Add error handling and retries | 3h | Claude Code |
| Implement security (webhook signing) | 2h | Claude Code |
| Add monitoring and health checks | 2h | Claude Code |
| Create status dashboard skill | 3h | Claude Code |
| Document everything | 2h | Claude Code |

**Success Criteria:**
- [ ] System recovers from failures gracefully
- [ ] Webhooks are secure (HMAC signing)
- [ ] User can check status via Telegram
- [ ] All documentation complete

---

## Security Considerations

### Authentication
- **Clawdbot → Ralph:** Shared secret in environment
- **Webhooks:** HMAC-SHA256 signing with secret key
- **Git:** SSH keys (no passwords)
- **Claude Max:** OAuth with auto-refresh

### Access Control
- VPS only accepts SSH from known IPs
- Webhook endpoints rate-limited (10 req/min)
- Ralph executions logged with full audit trail
- No production credentials in PRDs

### Data Protection
- `.env` files never committed
- Secrets in AWS Secrets Manager (future)
- PRDs may contain project details (not public)
- Git history preserved for accountability

---

## Monitoring & Observability

### Health Checks
```bash
# Clawdbot health
ssh clawdbot@44.193.244.59 "systemctl status clawdbot"

# Ralph status
ssh clawdbot@44.193.244.59 "cat /home/clawdbot/ralph/status.json"

# Webhook health
curl https://34.193.98.97/webhook/health
```

### Metrics to Track
- PRDs created per day
- Ralph execution time (avg, p95)
- Story completion rate
- Quality gate pass rate
- Time from request to completion

### Alerting
- Telegram notification if Ralph fails
- Email if VPS goes down
- Slack (optional) for status updates

---

## Rollback & Recovery

### If Ralph Fails Mid-Execution
1. PRD preserved with `passes: false` on failed story
2. Clawdbot notified of failure
3. User can: retry, skip story, or hand off to Claude Code

### If VPS Goes Down
1. All PRDs backed up to GitHub
2. Can restore from snapshot
3. Fall back to local Ralph on Mac

### If Git Conflicts Occur
1. Ralph creates feature branch instead of main
2. User notified of conflict
3. Claude Code resolves manually

---

## Communication Patterns

| User Says (Mobile) | System Does |
|--------------------|-------------|
| "Build [description]" | Clawdbot creates PRD → triggers Ralph |
| "Status of [project]" | Clawdbot queries docket → returns progress |
| "Stop Ralph" | Clawdbot sends kill signal → preserves state |
| "Continue Ralph" | Ralph resumes from last checkpoint |
| "Review the code" | Clawdbot reads from git → summarizes |
| "Deploy to production" | Triggers SOP 3 via Ralph |
| "What's in the queue" | Returns docket status |

---

## Future Enhancements

### Near-Term (1-3 months)
- Voice commands via Telegram voice messages
- Real-time WebSocket updates during Ralph execution
- Auto-retry failed stories with different approach
- Cost tracking per execution

### Medium-Term (3-6 months)
- Multiple Ralph instances for parallel PRDs
- AI-based complexity scoring for better estimates
- Integration with external services (GitHub Actions, Vercel)
- Mobile app for status monitoring

### Long-Term (6-12 months)
- Self-improving Ralph (meta-PRD for optimization)
- Cross-project pattern learning
- Automated testing in staging environment
- One-click rollback from mobile

---

## Related Documents

- [AI-ROUTING-OPTIMIZATION.md](AI-ROUTING-OPTIMIZATION.md) - **Intelligent routing between agents** ⭐
- [CLAWDBOT-CAPABILITIES.md](CLAWDBOT-CAPABILITIES.md) - Clawdbot details
- [RALPH-CAPABILITIES.md](RALPH-CAPABILITIES.md) - Ralph details
- [SOP-27-CLAWDBOT-USAGE.md](../directives/SOP-27-CLAWDBOT-USAGE.md) - When to use Clawdbot
- [SOP-28-RALPH-USAGE.md](../directives/SOP-28-RALPH-USAGE.md) - When to use Ralph

---

*This architecture enables true 24/7 autonomous development. Pick up your phone, describe what you want, go to sleep, wake up to completed code.*
