# SOP 29: Three-Agent Collaboration

**When**: Deciding which agent (Claude Code, Clawdbot, Ralph) should handle a task

**Purpose**: Optimize development workflow by routing tasks to the agent best suited for each type of work, enabling 24/7 development, efficient mobile access, and intelligent complexity management

**Last Updated**: 2026-01-28

---

## The Three Agents

### Claude Code (Mac Local)
**Platform**: Mac terminal (VSCode/iTerm)
**Availability**: When Mac is awake and user is present
**Best For**:
- Interactive debugging sessions
- Mac-specific tools (Xcode, PyPI deployment, MCP Registry)
- Final polish and production deployment
- Complex refactoring with human oversight
- Live editing with immediate feedback

**Limitations**:
- Only available when Mac is on
- Requires user presence
- Can't work while user is mobile/away

### Clawdbot (EC2 24/7)
**Platform**: AWS EC2 instance
**Availability**: 24/7 via Telegram/WhatsApp
**Best For**:
- Simple to medium builds (complexity 0-6)
- Quick tasks while mobile
- Research and information gathering
- Content generation
- Code that doesn't require Mac-specific tools
- Building and committing to GitHub
- Triggering Ralph for complex work

**Limitations**:
- Phase 1: No external API keys (building trust)
- Can't run Mac-specific tools
- Text-only interaction (no IDE integration)

### Ralph (EC2 24/7)
**Platform**: AWS EC2 instance (autonomous)
**Availability**: 24/7 via Clawdbot or Claude Code trigger
**Best For**:
- Complex multi-story development (complexity 7-10)
- Large refactoring with >7 components
- Test suite generation
- Database migrations
- Projects requiring quality gates
- Autonomous execution while you sleep

**Limitations**:
- Requires PRD (Product Requirements Document)
- No interactive debugging
- Works autonomously (can't ask questions mid-execution)

---

## Decision Matrix

### Task Complexity Scale (0-10)

| Score | Description | Examples | Agent |
|-------|-------------|----------|-------|
| **0-3** | Trivial | Research, status check, typo fix, simple question | Clawdbot |
| **4-6** | Medium | 3-4 file build, Flask API, SMS script, calculator app | Clawdbot |
| **7-8** | Complex | 8+ user stories, multi-component system, test suite | Ralph |
| **9-10** | Very Complex | Full application with database, API, tests, docs | Ralph |

**Mac-Specific** (any complexity): Claude Code on Mac

---

## Routing Decision Tree

```
START: New Task
    ↓
Is Mac-specific? (PyPI, MCP Registry, Xcode, iOS)
├─ YES → Use Claude Code on Mac
└─ NO ↓

Is user mobile/away from Mac?
├─ YES → Evaluate complexity for Clawdbot or Ralph
└─ NO → Evaluate all agents based on task type

Complexity 0-6?
├─ YES → Clawdbot handles directly
└─ NO ↓

Complexity 7-10?
├─ YES → Ralph (via Clawdbot or Claude Code)
└─ NO ↓

Need interactive debugging?
├─ YES → Claude Code on Mac
└─ NO → Default to Clawdbot
```

---

## Communication Patterns

### When User Says... → Use This Agent

| User Says | Use | Rationale |
|-----------|-----|-----------|
| "Quick question..." | Clawdbot | Fast text response, mobile-friendly |
| "Build X while I sleep" | Ralph (via Clawdbot PRD) | Autonomous overnight development |
| "Help me debug..." | Claude Code | Interactive session needed |
| "Research X" | Clawdbot | 24/7 web search capability |
| "Ralph: Build..." | Ralph (direct) | Explicit Ralph trigger |
| "Deploy to PyPI" | Claude Code | Mac-specific (keychain) |
| "Create Flask app" | Clawdbot | Simple build (complexity 4-5) |
| "Build analytics system" | Ralph | Complex (complexity 8+) |
| "Fix typo in file X" | Clawdbot | Trivial (complexity 1-2) |
| "Refactor entire codebase" | Ralph | Very complex (complexity 9-10) |

---

## Multi-Agent Collaboration Patterns

### Pattern 1: Sequential Handoff
**When**: Clear dependencies between phases

```
User → Clawdbot → builds simple feature → commits
User → Clawdbot → creates PRD → Ralph executes → done
Ralph → builds core → Clawdbot adds packaging → Claude Code deploys to PyPI
```

**Example**:
```
User (Telegram): "Build me a calculator CLI"
Clawdbot: Builds calculator.py → commits → done (15 minutes)

User (Telegram): "Ralph: Add comprehensive test suite"
Clawdbot: Creates PRD → triggers Ralph
Ralph: Writes 20 test cases → commits → done (45 minutes)
```

### Pattern 2: Parallel Work + Merge
**When**: Components can be developed independently

```
User: "Build HVAC campaign system"
    ↓
Clawdbot analyzes → splits work:
  - Clawdbot: UI (Flask routes, templates, forms) [branch: clawdbot/ui]
  - Ralph: Backend (database, SMS, tests) [branch: ralph/backend]
    ↓
Both work simultaneously (30 minutes)
    ↓
Clawdbot: Receives Ralph webhook → merges both branches → done
```

**Benefits**:
- 2x faster than sequential
- Each agent works on strengths
- User gets integrated system at end

### Pattern 3: Iterative Refinement (Ping-pong)
**When**: Building a system layer by layer

```
1. Clawdbot: Initial data models + API structure → commits
2. Ralph: Data pipeline (ETL, transformations, tests) → commits
3. Clawdbot: Dashboard UI consuming Ralph's pipeline → commits
4. Ralph: Optimization (caching, async) → commits
5. Clawdbot: Final polish, error handling, docs → done
```

**Benefits**:
- Each layer builds on previous
- Agents alternate based on task type
- No wasted waiting

### Pattern 4: Dependency Chain with Queue
**When**: Strict sequential dependencies but keep agents working

```
MINUTE 0:
  Clawdbot: Triggers Ralph Phase 1 (core MCP)
  Clawdbot: Starts working on documentation drafts (doesn't block!)

MINUTE 30:
  Ralph: Phase 1 complete → webhook
  Clawdbot: Interrupts docs → adds packaging → commits
  Clawdbot: Triggers Ralph Phase 2 (tests) → back to finishing docs

MINUTE 60:
  Ralph: Phase 2 complete → webhook
  Clawdbot: Receives notification → stops docs → publishes to PyPI
```

**Benefits**:
- Clawdbot never sits idle
- Dependencies respected
- Maximum throughput

### Pattern 5: Clawdbot as Project Manager
**When**: Very large project with mixed complexity

```
User: "Build fitness tracker app"
    ↓
Clawdbot: Analyzes → creates master plan:
  - Phase 1 (UI scaffolding): Clawdbot handles
  - Phase 2 (core features): Ralph PRD #1 (6 stories)
  - Phase 3 (integrations): Clawdbot handles
  - Phase 4 (testing & optimization): Ralph PRD #2 (4 stories)
    ↓
Clawdbot: Executes Phase 1 → commits
Clawdbot: Triggers Ralph PRD #1 → waits for webhook
Ralph: Completes → Clawdbot notified
Clawdbot: Executes Phase 3 → commits
Clawdbot: Triggers Ralph PRD #2 → waits
Ralph: Completes → Clawdbot does final merge
    ↓
Done - all components integrated
```

**Benefits**:
- Optimal routing at each phase
- Clawdbot orchestrates entire project
- User gets updates at each milestone

---

## Efficient Workflow Principles

### Smart Work Splitting

**DO**: Parallelize when components are independent
```
✅ UI and backend can be built simultaneously
✅ Different modules without shared state
✅ Testing different features
```

**DON'T**: Force parallelization when sequential makes sense
```
❌ Testing before code is written
❌ Building on non-existent dependencies
❌ Integrating before components exist
```

### Productive Waiting

**When Clawdbot waits for Ralph**:
- ✅ **Good**: Work on independent task if another user request pending
- ✅ **Good**: Enter standby if nothing else to do
- ❌ **Bad**: Generate busywork just to stay active

**When Ralph runs**:
- ✅ **Good**: Process queued PRDs back-to-back efficiently
- ✅ **Good**: Enter standby when queue empty
- ❌ **Bad**: Start unnecessary tasks to avoid idle time

### Integration Timing

**When to integrate**:
- ✅ Both agents completed their work
- ✅ Dependencies resolved
- ✅ Tests passing (if applicable)

**When NOT to integrate**:
- ❌ Agent still working
- ❌ Merge conflicts likely
- ❌ Missing critical dependencies

---

## Git Branching Strategy

### For Parallel Work

```
main
├─ clawdbot/[feature]    ← Clawdbot's work
├─ ralph/[feature]       ← Ralph's work
└─ merge both when complete
```

**Example**:
```bash
# Clawdbot creates branch
cd /home/clawdbot/dev-sandbox
git checkout -b clawdbot/ui

# Clawdbot works on UI
git add . && git commit -m "clawdbot: Add UI components"
git push origin clawdbot/ui

# Meanwhile, Ralph creates branch
git checkout -b ralph/backend

# Ralph works on backend
git add . && git commit -m "ralph: Story 1/5 - Database schema"
git push origin ralph/backend

# When both complete, Clawdbot merges
git checkout main
git pull origin main
git merge clawdbot/ui
git merge ralph/backend
git push origin main
```

### For Sequential Work

```
main ← all agents commit directly (no branching needed)
```

**Commit Prefixes**:
- `clawdbot: [description]` - Clawdbot's work
- `ralph: Story 3/8 - [description]` - Ralph's work
- `feat: [description]` - Claude Code's work

---

## Coordination Mechanisms

### Handoffs File
**Location**: `/home/clawdbot/dev-sandbox/ralph/handoffs.json`

**Purpose**: Track active collaborations between agents

**Format**:
```json
{
  "active_handoffs": [
    {
      "id": "handoff-001",
      "initiated_by": "clawdbot",
      "waiting_for": "ralph",
      "ralph_prd": "prd-analytics-pipeline.json",
      "next_action": "clawdbot_builds_ui",
      "status": "ralph_executing",
      "created_at": "2026-01-28T10:30:00Z"
    }
  ]
}
```

**Usage**:
```bash
# Clawdbot checks if Ralph is working on dependency
cat /home/clawdbot/dev-sandbox/ralph/handoffs.json

# Clawdbot updates when handing off to Ralph
echo '{"active_handoffs": [...]}' > ralph/handoffs.json

# Clawdbot removes handoff when Ralph completes
# (triggered by webhook notification)
```

### Webhook Coordination
**URL**: `http://localhost:5002/webhook/`

**Endpoints**:
- `POST /webhook/ralph/start` - Clawdbot triggers Ralph
- `POST /webhook/ralph/complete` - Ralph notifies completion
- `GET /webhook/status` - Check current Ralph status
- `POST /webhook/handoff/clawdbot-to-ralph` - Log handoff
- `POST /webhook/handoff/ralph-to-clawdbot` - Log return

**Telegram Notifications**:
- Ralph start: "Ralph Started - Project: [name] - Stories: [count]"
- Ralph complete: "Ralph Complete - Stories: [X/Y] passed - Iterations: [X/Y]"
- Handoff: "Clawdbot → Ralph handoff for [feature]"

---

## Task Examples by Agent

### Clawdbot Tasks (Complexity 0-6)

**Trivial (0-3)**:
- "What's the weather in Naples?"
- "Check status of campaigns"
- "Fix typo in README.md"
- "What is SOP 18?"

**Medium (4-6)**:
- "Build Flask API with 3 endpoints"
- "Create SMS campaign script"
- "Add user authentication (3-4 files)"
- "Write Python calculator"

### Ralph Tasks (Complexity 7-10)

**Complex (7-8)**:
- "Build analytics dashboard with pipeline" (8+ stories)
- "Refactor database schema" (10+ files)
- "Create MCP with full test coverage" (6+ stories)
- "Add multi-touch follow-up system" (7 components)

**Very Complex (9-10)**:
- "Build fitness tracker app" (12+ components)
- "Create lead management platform" (15+ stories)
- "Implement OAuth + billing system" (20+ files)

### Claude Code Tasks (Mac-Specific)

**Deployment**:
- "Deploy [project] to PyPI"
- "Publish to MCP Registry"
- "Update MCP version and republish"

**Mac Development**:
- "Build iOS app"
- "Create Xcode project"
- "Package desktop app with Electron"
- "Test on macOS native"

**Interactive**:
- "Help me debug this error" (with stack trace)
- "Refactor this file" (live editing)
- "Optimize this function" (performance analysis)

---

## Clawdbot Access & Credentials

### Phase 1 (Current): Minimal
- ✅ File system: `/home/clawdbot/dev-sandbox/`
- ✅ Git via SSH (commits/pushes)
- ✅ Ralph trigger (localhost webhook)
- ✅ Ollama memory (local embeddings)
- ❌ No external API keys

### Phase 2 (Week 2-3): Read-Only APIs
- Google Places API (business lookup)
- Yelp API (business data)
- Apollo API (lead data, read-only)
- ClickUp API (read-only, view tasks)

### Phase 3 (Week 4): Low-Risk Writes
- Google Sheets (logging data)
- GitHub Token (enhanced GitHub ops)
- Non-customer-facing writes only

### Phase 4 (Week 5-6): SMS/Email with Approval
- Twilio (SMS via approval workflow)
- SMTP (email via approval)
- Human approval required before sending

### Phase 5 (Month 2+): Full Autonomy
- All 65 API keys from `.env`
- Trusted after 30+ days responsible use
- Monitoring continues forever

---

## Success Metrics

### Per-Agent Metrics

**Clawdbot**:
- ✅ Building apps directly (not relaying to Claude Code)
- ✅ Commits appear on GitHub with "clawdbot:" prefix
- ✅ Response time <5 minutes for simple tasks
- ✅ Correct complexity scoring (no over/under delegation)

**Ralph**:
- ✅ PRD stories complete successfully
- ✅ Quality gates pass (tests, linting)
- ✅ Execution time reasonable (<2 hours for 8 stories)
- ✅ Webhook notifications delivered

**Claude Code**:
- ✅ Mac-specific tasks handled correctly
- ✅ PyPI/MCP deployments succeed
- ✅ Interactive debugging effective

### System-Wide Metrics

- ✅ Development continues 24/7 (Clawdbot + Ralph)
- ✅ User can trigger builds from mobile
- ✅ Complex projects complete autonomously overnight
- ✅ Each agent plays to strengths
- ✅ No unnecessary waiting or busywork

---

## Troubleshooting

### "Clawdbot didn't trigger Ralph for complex task"
- **Check**: Complexity score - may have underestimated
- **Fix**: Explicitly use "Ralph:" prefix in request
- **Check**: Ops manual loaded - `head /home/clawdbot/clawd/SOUL.md`

### "Ralph isn't starting"
- **Check**: Webhook server - `curl http://localhost:5002/health`
- **Fix**: Restart webhook - `sudo systemctl restart ralph-webhook`
- **Check**: PRD file exists and valid - `cat ralph/prd.json | python3 -m json.tool`

### "Clawdbot can't access file"
- **Check**: File path relative to `/home/clawdbot/dev-sandbox/`
- **Fix**: Use absolute paths in instructions
- **Check**: Permissions - `ls -la /home/clawdbot/dev-sandbox/[file]`

### "Agents working on same file (conflict)"
- **Cause**: Bad work splitting - components not independent
- **Fix**: Redesign split to avoid shared files
- **Prevention**: Use branching for parallel work

### "Integration failed after parallel work"
- **Check**: Merge conflicts - review branches
- **Fix**: Manually resolve conflicts
- **Prevention**: Better component boundaries in work split

---

## When to Use Each Pattern

| Pattern | Best For | Avoid When |
|---------|----------|------------|
| Sequential Handoff | Clear dependencies | Independent components |
| Parallel Work + Merge | Independent modules | Shared state/files |
| Iterative Refinement | Layer-by-layer building | Single cohesive feature |
| Dependency Chain | Must wait but can work elsewhere | No other work pending |
| Project Manager | Very large projects | Simple 1-2 file tasks |

---

## Quick Reference Commands

**Check Services**:
```bash
# Clawdbot status
ssh ec2 "sudo systemctl status clawdbot"

# Ralph webhook status
ssh ec2 "curl http://localhost:5002/health"

# Check Ralph execution
ssh ec2 "sudo -u clawdbot tail -20 /home/clawdbot/dev-sandbox/ralph/progress.txt"
```

**Trigger Ralph**:
```bash
# From Clawdbot (via script)
/home/clawdbot/scripts/clawdbot-trigger-ralph.sh [project] [iterations]

# From Mac (via Claude Code)
ssh ec2 "sudo -u clawdbot /home/clawdbot/scripts/ralph-ec2.sh 10"
```

**Check Git Commits**:
```bash
# On EC2
ssh ec2 "sudo -u clawdbot bash -c 'cd /home/clawdbot/dev-sandbox && git log --oneline --author=\"clawdbot\" | head -10'"

# On Mac (after pull)
cd ~/dev-sandbox && git log --oneline | grep -E "(clawdbot|ralph):" | head -10
```

---

## Related Documentation

- [CLAWDBOT-OPS-MANUAL.md](CLAWDBOT-OPS-MANUAL.md) - Clawdbot system prompt
- [CLAWDBOT-CAPABILITIES.md](CLAWDBOT-CAPABILITIES.md) - What Clawdbot can do
- [CLAWDBOT-TEST-PLAN.md](CLAWDBOT-TEST-PLAN.md) - Testing scenarios
- [SOP-27-CLAWDBOT-USAGE.md](SOP-27-CLAWDBOT-USAGE.md) - When/how to use Clawdbot
- [SOP-28-RALPH-USAGE.md](SOP-28-RALPH-USAGE.md) - When/how to use Ralph
- [RALPH-CAPABILITIES.md](RALPH-CAPABILITIES.md) - What Ralph can do
- [AI-ROUTING-OPTIMIZATION.md](AI-ROUTING-OPTIMIZATION.md) - Routing decision logic

---

**Remember**: The goal is efficient development, not keeping agents busy. Each agent should work on what they're best at, wait productively when needed, and collaborate seamlessly for complex projects.
