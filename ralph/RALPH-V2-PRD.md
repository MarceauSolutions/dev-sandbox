# PRD: Ralph v2 -- Autonomous Agent Rebuild on Claude Agent SDK

**Author:** William Marceau Jr.
**Date:** 2026-02-15
**Status:** Draft
**Complexity:** 9/10

---

## 1. Overview

Ralph v2 is a ground-up rebuild of the Ralph autonomous agent using the Claude Agent SDK instead of the current bash-loop-over-Amp architecture. Ralph v2 will accept Product Requirement Documents (PRDs), decompose them into executable subtasks, and autonomously implement them with full git integration, progress reporting, error recovery, and cross-agent memory sharing.

### Why Rebuild

Ralph v1 works, but it has fundamental limitations:

1. **Stateless iterations.** Each iteration spawns a fresh Amp instance. Memory persists only through `progress.txt` and `prd.json`. There is no structured state between iterations.
2. **No mid-execution intelligence.** The bash loop (`ralph.sh`) has zero awareness of what the agent is doing. It just checks for `<promise>COMPLETE</promise>` in stdout.
3. **No error recovery.** If a story fails, the next iteration retries blindly. There is no structured retry logic, fallback strategies, or escalation.
4. **No real-time progress.** Progress is only visible after the run completes. No Telegram updates, no live dashboards.
5. **Amp dependency.** The entire system is coupled to Amp CLI. The Claude Agent SDK provides a native Python runtime with tool definitions, structured output, streaming, and conversation management.
6. **No shared memory.** Ralph v1 does not read from or write to the Mem0 shared memory system that Claude Code and Clawdbot use. It is context-blind to what the other agents know.

### What v2 Delivers

- Accept PRDs and execute them end-to-end without human intervention
- Handle complexity 7-10 tasks (multi-file refactors, full system builds, new projects)
- Run on EC2 24/7 alongside Clawdbot
- Use Mem0 shared memory (localhost:5020) for cross-agent context
- Report progress in real time via Telegram through n8n webhooks
- Self-heal on failures with structured retry logic and human escalation
- Queue multiple PRDs and process them sequentially
- Hand off Mac-specific tasks (PyPI deployment, MCP publishing) via the handoff system

---

## 2. Current State (v1)

### Architecture

Ralph v1 is a bash script (`ralph.sh`) that spawns Amp CLI instances in a loop. Each iteration:

1. Reads `prompt.md` (static instructions)
2. Reads `prd.json` (task list with `passes: true/false` per story)
3. Reads `progress.txt` (append-only learnings from previous iterations)
4. Picks the highest-priority story where `passes: false`
5. Implements that single story
6. Runs quality checks (typecheck, lint, tests)
7. Commits if checks pass, updates `prd.json`, appends to `progress.txt`
8. Repeats until all stories pass or max iterations reached

### Key Files (current)

| File | Purpose |
|------|---------|
| `ralph.sh` | Bash loop spawning fresh Amp instances per iteration |
| `prompt.md` | Static instructions given to each Amp instance |
| `prd.json` | Current PRD with user stories and pass/fail status |
| `prd.json.example` | Example PRD format |
| `progress.txt` | Append-only log of learnings between iterations |
| `handoffs.json` | Tracks active agent handoffs between Claude Code, Clawdbot, Ralph |
| `pipeline/orchestrator.py` | Coordinates full Clawdbot-to-Ralph pipeline |
| `pipeline/pre_flight.py` | PRD quality gate (validates before Ralph runs) |
| `pipeline/prompt_builder.py` | Builds context-enriched prompts from PRD + project analysis |
| `pipeline/post_review.py` | Post-completion code quality review |
| `pipeline/feedback_loop.py` | Extracts learnings, updates `knowledge_base.json` |
| `pipeline/knowledge_base.json` | Accumulated patterns, gotchas, conventions from prior runs |
| `skills/prd/SKILL.md` | Amp skill for generating PRDs |
| `skills/ralph/SKILL.md` | Amp skill for converting PRDs to JSON |

### Pipeline (v1)

The v1 pipeline (`orchestrator.py`) runs 5 stages:

1. **Pre-flight** -- Validate PRD quality (score 0-100, threshold 70)
2. **Prompt build** -- Inject project context, tech stack, learnings into prompt
3. **Execute** -- Shell out to `ralph-ec2.sh` (which runs `ralph.sh`)
4. **Post-review** -- Check story completion, syntax, docstrings, code smells
5. **Feedback** -- Extract patterns from `progress.txt`, update knowledge base

### What Works Well

- PRD quality gate catches vague acceptance criteria before wasting compute
- Knowledge base accumulates learnings across runs
- Post-review catches syntax errors and code smells
- Handoff system coordinates with other agents (in theory)

### What Does Not Work

- Shell-based execution has no programmatic control over the agent
- No structured error handling (relies on `|| true`)
- No real-time progress reporting
- No Mem0 integration (context-blind)
- One-hour hard timeout with no checkpointing
- Cannot queue multiple PRDs
- No way to pause, resume, or cancel a running task
- Branch management is fragile (relies on PRD's `branchName` field)

---

## 3. v2 Architecture

### 3.1 Core Runtime: Claude Agent SDK

Ralph v2 replaces the bash-loop-over-Amp with a Python application built on the Claude Agent SDK. The SDK provides:

- **Native tool definitions** -- Define tools as Python functions with typed parameters
- **Conversation management** -- Maintain context across turns without external state files
- **Streaming** -- Real-time token-by-token output for progress monitoring
- **Structured output** -- Force the model to return typed JSON for progress reports
- **Multi-turn loops** -- The SDK handles the agent loop natively (message -> tool call -> result -> message)

### 3.2 System Diagram

```
                          +------------------+
                          |   PRD Queue      |
                          |  (JSON files or  |
                          |   Mem0 entries)  |
                          +--------+---------+
                                   |
                                   v
                     +-------------+-------------+
                     |     Ralph v2 Orchestrator  |
                     |    (Python, Agent SDK)     |
                     +--+-----+-----+-----+---+--+
                        |     |     |     |   |
              +---------+  +--+--+  |  +--+--+  +---------+
              |            |     |  |  |     |            |
              v            v     v  v  v     v            v
         +--------+  +------+ +----+ +------+ +--------+
         | Git    |  | Bash | |File| | Mem0 | |Telegram|
         | Tools  |  | Tool | |Ops | |Client| |via n8n |
         +--------+  +------+ +----+ +------+ +--------+
              |            |     |        |         |
              v            v     v        v         v
         dev-sandbox     EC2    Local   localhost  n8n
         git repo       shell   FS      :5020     :5678
```

### 3.3 Agent Loop

The core loop replaces `ralph.sh`:

```python
# Pseudocode -- actual implementation will use Claude Agent SDK primitives

class RalphAgent:
    def __init__(self, prd_path: str, config: RalphConfig):
        self.prd = load_prd(prd_path)
        self.config = config
        self.mem0 = Mem0Client(agent_id="ralph")
        self.tools = [
            file_read, file_write, file_edit,
            bash_execute, git_operations,
            mem0_search, mem0_add,
            report_progress, request_human_input
        ]

    async def run(self):
        # 1. Pre-flight
        self.validate_prd()
        self.setup_git_branch()

        # 2. Load cross-agent context from Mem0
        context = self.mem0.search(self.prd.project_name)

        # 3. Process stories sequentially
        for story in self.prd.pending_stories():
            result = await self.execute_story(story, context)

            if result.success:
                self.mark_story_complete(story)
                self.report_progress(story, result)
                self.mem0.add(f"Completed {story.id}: {story.title}")
            else:
                self.handle_failure(story, result)

        # 4. Post-completion
        self.run_post_review()
        self.notify_completion()

    async def execute_story(self, story, context):
        """Execute a single story using the Claude Agent SDK."""
        # Build story-specific prompt with context
        # Run agent loop with tools until story is complete
        # Validate acceptance criteria
        # Commit if quality checks pass
        pass

    def handle_failure(self, story, result):
        """Structured error recovery."""
        if result.retries < 3:
            # Retry with additional context about the failure
            pass
        elif result.can_skip:
            # Skip non-blocking story, continue with next
            pass
        else:
            # Escalate to human via Telegram
            self.request_human_input(story, result.error)
```

### 3.4 Tool Definitions

Ralph v2 will have the following tool categories:

#### File Operations
| Tool | Description |
|------|-------------|
| `file_read(path)` | Read file contents |
| `file_write(path, content)` | Write/overwrite file |
| `file_edit(path, old, new)` | Find-and-replace edit |
| `file_search(pattern, path)` | Glob-based file finding |
| `content_search(pattern, path)` | Ripgrep-style content search |

#### Shell / Execution
| Tool | Description |
|------|-------------|
| `bash(command, timeout)` | Execute shell command with timeout |
| `python_exec(code)` | Execute Python code in subprocess |

#### Git Operations
| Tool | Description |
|------|-------------|
| `git_status()` | Get working tree status |
| `git_diff()` | Show staged and unstaged changes |
| `git_commit(message, files)` | Stage specific files and commit |
| `git_branch(name)` | Create and checkout branch |
| `git_log(count)` | Recent commit history |
| `git_push()` | Push current branch to origin |

#### Memory (Mem0)
| Tool | Description |
|------|-------------|
| `mem0_search(query, agent_id?)` | Search memories (own or cross-agent) |
| `mem0_add(content, metadata)` | Store a new memory |
| `mem0_list(category?)` | List memories by category |

#### Progress Reporting
| Tool | Description |
|------|-------------|
| `report_progress(story_id, status, detail)` | Report progress to orchestrator |
| `request_human_input(question, context)` | Escalate to human via Telegram |
| `update_prd(story_id, passes, notes)` | Update PRD story status |

#### n8n Integration
| Tool | Description |
|------|-------------|
| `trigger_webhook(endpoint, payload)` | Call n8n webhook for notifications |
| `trigger_workflow(workflow_id, data)` | Trigger any n8n workflow by ID |

### 3.5 Structured Output

Ralph v2 will use structured output for progress reporting. After each story, the agent emits:

```json
{
    "story_id": "US-003",
    "status": "completed",
    "files_changed": ["src/api/routes.py", "src/models/task.py"],
    "tests_passed": true,
    "quality_score": 85,
    "commit_hash": "abc1234",
    "learnings": [
        "FastAPI route ordering matters -- specific routes before parameterized ones"
    ],
    "next_story": "US-004",
    "estimated_remaining_minutes": 20
}
```

### 3.6 Task Decomposition

When Ralph v2 receives a PRD, it first decomposes it into an execution plan:

1. **Parse PRD** -- Extract stories, dependencies, acceptance criteria
2. **Dependency analysis** -- Build a DAG of story dependencies (explicit `dependsOn` fields or inferred from content)
3. **Execution ordering** -- Topological sort of the DAG
4. **Context loading** -- Pull relevant Mem0 memories for the project
5. **Branch setup** -- Create `ralph/{feature}` branch from main
6. **Sequential execution** -- Process stories in dependency order

Each story within the execution plan has:
- Clear acceptance criteria (from PRD)
- Pre-loaded file context (from codebase analysis)
- Relevant memories (from Mem0)
- Quality checks to run after implementation

### 3.7 Error Recovery

Ralph v2 implements a three-tier error recovery strategy:

**Tier 1: Auto-Retry (up to 3 attempts)**
- Syntax errors -- retry with error message as context
- Test failures -- retry with failing test output
- Lint errors -- retry with lint output
- Each retry adds the error to the prompt so the agent does not repeat the mistake

**Tier 2: Skip and Continue**
- If a non-critical story fails 3 times and no other stories depend on it, skip it
- Mark as `"passes": "skipped"` with failure notes
- Continue with remaining stories

**Tier 3: Human Escalation**
- If a critical story (one that blocks others) fails 3 times, escalate
- Send Telegram notification via n8n webhook with:
  - Story title and description
  - Error details from last 3 attempts
  - Files involved
  - Suggested next steps
- Ralph pauses that story and moves to the next non-blocked story
- Human can respond with guidance via Telegram, which Ralph picks up on next check

### 3.8 Configuration

```python
@dataclass
class RalphConfig:
    # Agent
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 16384

    # Execution
    max_retries_per_story: int = 3
    max_total_iterations: int = 50
    story_timeout_seconds: int = 600  # 10 min per story
    total_timeout_seconds: int = 7200  # 2 hours total

    # Git
    auto_commit: bool = True
    auto_push: bool = True
    branch_prefix: str = "ralph/"
    commit_prefix: str = "ralph:"

    # Memory
    mem0_url: str = "http://localhost:5020"
    mem0_agent_id: str = "ralph"

    # Notifications
    n8n_webhook_url: str = "http://localhost:5678/webhook/ralph"
    telegram_on_complete: bool = True
    telegram_on_error: bool = True
    telegram_on_progress: bool = False  # Per-story updates (noisy)

    # Quality
    run_syntax_check: bool = True
    run_tests: bool = True
    run_post_review: bool = True
    min_quality_score: int = 75

    # Paths
    workspace: str = "/home/clawdbot/dev-sandbox"
    prd_queue_dir: str = "/home/clawdbot/dev-sandbox/ralph/queue"
    output_dir: str = "/home/clawdbot/dev-sandbox/ralph/output"
```

---

## 4. Integration Points

### 4.1 Mem0 API (localhost:5020)

Ralph v2 uses Mem0 for two-way cross-agent knowledge sharing.

**Reads from Mem0:**
- Project-specific context written by Claude Code or Clawdbot
- User preferences and coding standards
- Previous decisions and architectural choices
- Known gotchas for the current project

**Writes to Mem0:**
- Learnings discovered during execution (replaces `progress.txt` patterns)
- Completion status for handoff coordination
- Error patterns and workarounds
- File coupling patterns ("when X changes, also update Y")

**Memory Categories:**
```
ralph:learning     -- Patterns and gotchas discovered during execution
ralph:progress     -- Current execution state for monitoring
ralph:handoff      -- Tasks that need Mac-specific handling
project:{name}     -- Project-specific context (shared with all agents)
```

**Cross-Agent Search:**
Before starting a PRD, Ralph searches Mem0 for:
1. `agent_id="claude-code"` + project name -- What did the human do recently?
2. `agent_id="clawdbot"` + project name -- What did Clawdbot set up?
3. `agent_id="ralph"` + project name -- What did Ralph learn last time?

### 4.2 n8n Agent Orchestrator (localhost:5678)

Ralph v2 integrates with n8n for notifications and workflow triggers.

**Webhook Endpoints (Ralph -> n8n):**

| Endpoint | Trigger |
|----------|---------|
| `POST /webhook/ralph/started` | Ralph begins processing a PRD |
| `POST /webhook/ralph/story-complete` | A story passes |
| `POST /webhook/ralph/story-failed` | A story fails after retries |
| `POST /webhook/ralph/complete` | All stories done |
| `POST /webhook/ralph/escalation` | Human input needed |
| `POST /webhook/ralph/error` | Unrecoverable error |

**Payload Example (story-complete):**
```json
{
    "prd_name": "n8n-agent-v3",
    "story_id": "story-003",
    "story_title": "Add Glob File Pattern Tool",
    "stories_done": 3,
    "stories_total": 10,
    "elapsed_minutes": 12,
    "commit_hash": "abc1234"
}
```

n8n routes these to:
- Telegram notification (all events)
- Google Sheets logging (all events)
- Handoff system update (completion events)

### 4.3 Git Integration

Ralph v2 manages git branches and commits automatically:

1. **Branch creation:** `ralph/{prd-name}` from latest `main`
2. **Per-story commits:** `ralph: Story {id} - {title}`
3. **Auto-push:** Push after each successful story commit
4. **Conflict detection:** If `main` has diverged, attempt rebase. If conflicts, escalate to human.
5. **Cleanup:** After successful completion, optionally create a PR summary

**Git Safety Rules (inherited from CLAUDE.md):**
- Never force push
- Never reset --hard
- Always commit specific files (no `git add -A`)
- Never commit `.env` or credentials

### 4.4 Telegram Notifications (via n8n)

All notifications flow through n8n webhooks which route to the existing Telegram bot.

**Notification Types:**

| Event | Message Format |
|-------|---------------|
| PRD Started | `Ralph Started: {name} ({n} stories)` |
| Story Done | `Ralph: {done}/{total} -- {story_title}` |
| All Done | `Ralph Complete: {name} -- {done}/{total} stories, {minutes}min` |
| Escalation | `Ralph Needs Help: {story_title}\n{error_summary}\nReply to guide` |
| Error | `Ralph Error: {error_type}\n{details}` |

### 4.5 Handoff System (HANDOFF.md + handoffs.json)

For tasks Ralph cannot complete on EC2 (Mac-specific):

1. Ralph writes to `ralph/handoffs.json`:
```json
{
    "active_handoffs": [{
        "id": "handoff-002",
        "initiated_by": "ralph",
        "waiting_for": "claude_code",
        "task": "Publish updated md-to-pdf v1.3.0 to PyPI",
        "context": "Code is ready on branch ralph/md-to-pdf-v1.3.0, tests pass",
        "prd_name": "md-to-pdf-upgrade",
        "story_id": "US-008",
        "status": "pending",
        "created_at": "2026-02-15T03:00:00Z"
    }]
}
```

2. Ralph stores the handoff in Mem0 with `category: "handoff"`
3. n8n sends Telegram notification about pending Mac handoff
4. Claude Code picks it up on next session (checks handoffs.json at start)

### 4.6 Task Classifier Integration

The existing `execution/task_classifier.py` routes tasks to the right agent. Ralph v2 integrates as a target:

```python
# Task classifier already knows about Ralph:
# - Complexity 8-10 -> ralph
# - Multi-file builds -> ralph
# - Autonomous overnight work -> ralph

# Ralph v2 adds a feedback loop:
# After completing a PRD, Ralph updates the classifier's context
# with actual complexity data (estimated vs actual time, files touched)
```

### 4.7 Existing Pipeline Components (carried forward)

The v1 pipeline components are reused in v2:

| Component | v1 Role | v2 Role |
|-----------|---------|---------|
| `pre_flight.py` | Validate PRD quality | Same, imported as module |
| `prompt_builder.py` | Build context-enriched prompt | Adapted for Agent SDK prompts |
| `post_review.py` | Post-completion code review | Same, run after all stories |
| `feedback_loop.py` | Extract learnings to knowledge base | Extended to also write to Mem0 |
| `knowledge_base.json` | Local accumulated learnings | Migrated to Mem0 (kept as fallback) |

---

## 5. PRD Format (v2)

Ralph v2 uses an enhanced PRD format that is backward-compatible with v1:

```json
{
    "version": "2.0",
    "projectName": "my-project",
    "branchName": "ralph/my-feature",
    "description": "Feature description",
    "techStack": {
        "language": "Python 3.11",
        "framework": "FastAPI",
        "database": "SQLAlchemy + PostgreSQL",
        "testing": "pytest"
    },
    "qualityChecks": [
        "python -m py_compile {file}",
        "python -m pytest tests/",
        "python -m mypy src/"
    ],
    "codingStandards": {
        "style": "Follow existing patterns in codebase",
        "documentation": "Docstrings on all public functions",
        "errorHandling": "No bare excepts, use logging",
        "testing": "Unit tests for business logic"
    },
    "stories": [
        {
            "id": "US-001",
            "title": "Story title",
            "description": "As a developer, I need X so that Y",
            "acceptanceCriteria": [
                "Specific, testable criterion 1",
                "Specific, testable criterion 2",
                "All quality checks pass"
            ],
            "dependsOn": [],
            "priority": 1,
            "passes": false,
            "skippable": false,
            "notes": "",
            "retries": 0,
            "lastError": null
        }
    ],
    "metadata": {
        "created": "2026-02-15",
        "createdBy": "claude-code",
        "estimatedHours": 4,
        "tags": ["backend", "api"]
    }
}
```

**Changes from v1 format:**
- Added `version` field
- Added `dependsOn` to stories (enables DAG execution)
- Added `skippable` to stories (guides error recovery)
- Added `retries` and `lastError` for tracking failure state
- Added `metadata` for audit trail
- Renamed `userStories` to `stories` (simpler; v1 format still accepted)

---

## 6. Implementation Plan

### Phase 1: Core Agent Loop (Week 1)

**Goal:** Replace `ralph.sh` + Amp with a Python agent using Claude Agent SDK.

**Stories:**

| ID | Title | Description |
|----|-------|-------------|
| P1-01 | Project scaffolding | Create `ralph/v2/` directory with `__init__.py`, `agent.py`, `config.py`, `tools/`, `requirements.txt` |
| P1-02 | Configuration system | Implement `RalphConfig` dataclass with env var overrides and config file loading |
| P1-03 | Tool definitions -- file ops | Implement `file_read`, `file_write`, `file_edit`, `file_search`, `content_search` tools |
| P1-04 | Tool definitions -- shell | Implement `bash` tool with timeout, output capture, and safety guards |
| P1-05 | Tool definitions -- git | Implement `git_status`, `git_diff`, `git_commit`, `git_branch`, `git_log`, `git_push` |
| P1-06 | PRD loader | Load and validate PRD (support both v1 and v2 formats), build execution plan |
| P1-07 | Core agent loop | Implement `RalphAgent.run()` with story-by-story execution using Claude Agent SDK |
| P1-08 | Story executor | Implement `execute_story()` -- build prompt, run agent loop, validate acceptance criteria |
| P1-09 | CLI entry point | `python -m ralph.v2 run <prd.json> [--config config.yaml]` |
| P1-10 | Basic tests | Unit tests for PRD loading, config, tool definitions |

**Acceptance Criteria:**
- Can execute a simple 3-story PRD end-to-end
- Creates git branch, commits per story, pushes
- Outputs structured progress to stdout
- All unit tests pass

### Phase 2: Mem0 Integration + Progress Reporting (Week 2)

**Goal:** Connect Ralph to shared memory and real-time notifications.

**Stories:**

| ID | Title | Description |
|----|-------|-------------|
| P2-01 | Mem0 tools | Implement `mem0_search`, `mem0_add`, `mem0_list` tools using existing `Mem0Client` |
| P2-02 | Context loading | Before each PRD, search Mem0 for project context from all agents |
| P2-03 | Learning persistence | After each story, write learnings to Mem0 (replaces progress.txt for new data) |
| P2-04 | n8n webhook integration | Implement `trigger_webhook` tool, send notifications on start/complete/error |
| P2-05 | Telegram notifications | Configure n8n workflow to route Ralph webhooks to Telegram |
| P2-06 | Handoff system updates | After completion, update `handoffs.json` and Mem0 with status |
| P2-07 | Progress file compatibility | Continue appending to `progress.txt` for backward compatibility with v1 pipeline |
| P2-08 | Integration tests | Test full flow with Mem0 and n8n webhooks (mock if services unavailable) |

**Acceptance Criteria:**
- Ralph reads Mem0 context before starting
- Ralph writes learnings to Mem0 after each story
- Telegram notifications arrive for start, each story, and completion
- `handoffs.json` is updated on completion

### Phase 3: Self-Healing + Error Recovery (Week 3)

**Goal:** Make Ralph resilient to failures without human intervention.

**Stories:**

| ID | Title | Description |
|----|-------|-------------|
| P3-01 | Retry logic | Implement Tier 1 auto-retry with error context injection (up to 3 attempts per story) |
| P3-02 | Skip logic | Implement Tier 2 skip-and-continue for non-critical stories that fail 3 times |
| P3-03 | Human escalation | Implement Tier 3 escalation via Telegram with context, await response |
| P3-04 | Git conflict recovery | Detect main branch divergence, attempt rebase, escalate on conflict |
| P3-05 | Timeout handling | Per-story and total execution timeouts with graceful shutdown |
| P3-06 | Checkpoint/resume | Save execution state to disk so Ralph can resume after crash or restart |
| P3-07 | Quality gate enforcement | Run `post_review.py` checks after each story, block commit if score < threshold |
| P3-08 | Error pattern detection | If same error type occurs 3+ times across stories, stop and escalate (Rule of Three) |

**Acceptance Criteria:**
- Ralph retries failed stories with error context
- Non-critical failures are skipped with clear reporting
- Telegram escalation includes actionable error details
- Ralph can resume from checkpoint after process restart
- Rule of Three is enforced (no infinite retry loops)

### Phase 4: Multi-Task Queuing + Operations (Week 4)

**Goal:** Production-grade operations with queue management and observability.

**Stories:**

| ID | Title | Description |
|----|-------|-------------|
| P4-01 | PRD queue | Implement queue directory watcher (`ralph/queue/`) that processes PRDs sequentially |
| P4-02 | Queue management CLI | `ralph queue list`, `ralph queue add <prd>`, `ralph queue cancel <id>` |
| P4-03 | Execution history | Store completed PRD results in `ralph/output/{prd-name}/` with full report |
| P4-04 | Health endpoint | HTTP health check at `localhost:5030/health` for monitoring |
| P4-05 | Systemd service | `ralph-v2.service` unit file for EC2 deployment |
| P4-06 | Log management | Structured JSON logging to `/var/log/ralph/ralph.log` with rotation |
| P4-07 | Clawdbot trigger API | HTTP endpoint at `localhost:5030/trigger` for Clawdbot to submit PRDs |
| P4-08 | Migration from v1 | Script to migrate v1 `progress.txt` learnings and `knowledge_base.json` into Mem0 |
| P4-09 | End-to-end tests | Full integration test: submit PRD -> execute -> verify output -> check Mem0 -> check notifications |
| P4-10 | Documentation | Update SOP-28, SOP-29, and MEMORY.md with v2 architecture and endpoints |

**Acceptance Criteria:**
- Can queue 3+ PRDs and process them sequentially
- Each completed PRD produces a full output report
- Systemd service starts on boot and auto-restarts on crash
- Clawdbot can submit PRDs via HTTP API
- All existing v1 learnings are migrated to Mem0

---

## 7. Success Criteria

### Must Have (Phase 1-2)

- [ ] Can execute a simple PRD (3-5 stories) end-to-end without human intervention
- [ ] Creates proper git branch (`ralph/{feature}`) and commits per story
- [ ] Reports progress to Telegram via n8n webhooks
- [ ] Uses Mem0 to share context with Claude Code and Clawdbot
- [ ] Writes learnings to Mem0 after each story
- [ ] Reads cross-agent context from Mem0 before starting

### Should Have (Phase 3)

- [ ] Retries failed stories with error context (up to 3 times)
- [ ] Skips non-critical failures and continues
- [ ] Escalates blocking failures to human via Telegram
- [ ] Can resume from checkpoint after crash
- [ ] Enforces Rule of Three (stops after 3 same-type failures)

### Nice to Have (Phase 4)

- [ ] Processes PRD queue automatically
- [ ] Clawdbot can submit PRDs via HTTP API
- [ ] Runs as systemd service on EC2
- [ ] Full execution history with reports
- [ ] v1 knowledge base migrated to Mem0

### Performance Targets

| Metric | Target |
|--------|--------|
| Story execution time (simple) | < 5 minutes |
| Story execution time (complex) | < 15 minutes |
| Full PRD (5 stories) | < 45 minutes |
| Full PRD (10 stories) | < 90 minutes |
| Mem0 query latency | < 500ms |
| Telegram notification delay | < 10 seconds |
| Retry overhead per failure | < 2 minutes |

---

## 8. Technical Decisions

### Why Claude Agent SDK (not raw API calls)

The Claude Agent SDK provides:
1. **Built-in tool execution loop** -- No need to manually parse tool_use blocks and re-submit
2. **Streaming** -- Real-time output for progress monitoring
3. **Conversation state management** -- SDK handles message history
4. **Typed tool definitions** -- Less boilerplate, better validation
5. **Official support** -- Maintained by Anthropic, bug fixes and improvements

### Why Sonnet (not Opus) for execution

- Ralph processes many stories (5-15 per PRD), each requiring multiple tool calls
- Sonnet is significantly cheaper per token and faster
- Quality is sufficient for code implementation tasks
- Opus is reserved for architectural decisions and complex reasoning (Claude Code on Mac)

### Why keep progress.txt alongside Mem0

- Backward compatibility with v1 pipeline components
- Human-readable audit trail (Mem0 is API-only)
- Fallback if Mem0 is unavailable
- `progress.txt` is version-controlled in git; Mem0 is not

### Why sequential story execution (not parallel)

- Stories often have implicit dependencies even when not explicitly declared
- Parallel execution risks merge conflicts and inconsistent state
- Sequential is simpler to reason about, debug, and resume
- The bottleneck is LLM inference, not I/O

### Model selection for v2

- **Story execution:** `claude-sonnet-4-5-20250929` -- Best balance of speed, cost, and code quality
- **PRD analysis/decomposition:** `claude-sonnet-4-5-20250929` -- Same model for consistency
- **Task classification:** `claude-haiku-4-5-20251001` -- Fast and cheap for routing decisions (existing classifier)

---

## 9. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent SDK API changes | Breaks core loop | Pin SDK version, wrap in abstraction layer |
| Mem0 unavailable | No cross-agent context | Graceful fallback to local knowledge_base.json |
| n8n down | No notifications | Log to file, retry webhook on reconnect |
| Large PRDs exceed token limits | Stories fail to complete | Pre-flight checks enforce story size limits |
| EC2 instance restart | Loses in-progress work | Checkpoint/resume system (Phase 3) |
| Git conflicts with other agents | Blocked on push | Detect conflicts, escalate to human |
| Runaway execution (cost) | High API bills | Per-story token budget, total execution budget, hard timeout |
| Story acceptance criteria too vague | Wasted retries | Pre-flight quality gate (carried from v1) |

---

## 10. File Structure (v2)

```
ralph/
├── RALPH-V2-PRD.md          # This document
├── v2/
│   ├── __init__.py
│   ├── __main__.py           # CLI entry point
│   ├── agent.py              # Core RalphAgent class
│   ├── config.py             # RalphConfig dataclass
│   ├── prd_loader.py         # PRD parsing and validation
│   ├── story_executor.py     # Single-story execution logic
│   ├── error_handler.py      # Retry, skip, escalation logic
│   ├── progress_reporter.py  # Telegram + Mem0 + file reporting
│   ├── queue_manager.py      # PRD queue processing
│   ├── health.py             # HTTP health endpoint
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── file_ops.py       # File read/write/edit/search
│   │   ├── shell.py          # Bash execution with safety
│   │   ├── git_ops.py        # Git operations
│   │   ├── mem0_tools.py     # Mem0 search/add/list
│   │   ├── reporting.py      # Progress and escalation tools
│   │   └── n8n.py            # n8n webhook triggers
│   ├── tests/
│   │   ├── test_prd_loader.py
│   │   ├── test_config.py
│   │   ├── test_tools.py
│   │   ├── test_error_handler.py
│   │   └── test_agent.py
│   └── requirements.txt
├── queue/                     # PRD queue directory (Phase 4)
├── output/                    # Execution results
├── pipeline/                  # v1 pipeline (kept for compatibility)
│   ├── pre_flight.py
│   ├── post_review.py
│   ├── prompt_builder.py
│   ├── feedback_loop.py
│   └── knowledge_base.json
├── ralph.sh                   # v1 entry point (kept for fallback)
├── prompt.md                  # v1 prompt (kept for reference)
├── prd.json                   # Current PRD (shared between v1/v2)
├── progress.txt               # Append-only log (shared between v1/v2)
└── handoffs.json              # Agent handoff tracking
```

---

## 11. Deployment Plan

### EC2 Setup

1. Install dependencies:
```bash
cd /home/clawdbot/dev-sandbox/ralph/v2
pip install -r requirements.txt
```

2. Create systemd service:
```ini
# /etc/systemd/system/ralph-v2.service
[Unit]
Description=Ralph v2 Autonomous Agent
After=network.target

[Service]
Type=simple
User=clawdbot
WorkingDirectory=/home/clawdbot/dev-sandbox
ExecStart=/usr/bin/python3 -m ralph.v2 daemon
Restart=on-failure
RestartSec=30
Environment=ANTHROPIC_API_KEY=<from-env>
EnvironmentFile=/home/clawdbot/dev-sandbox/.env

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable ralph-v2
sudo systemctl start ralph-v2
```

### Rollback Plan

If v2 has issues, v1 remains fully functional:
- `ralph.sh` is untouched
- `prd.json` format is backward-compatible
- `progress.txt` is shared between v1 and v2
- Systemd service can be stopped and v1 invoked manually

---

## 12. Open Questions

1. **Agent SDK model:** Should we use `claude-sonnet-4-5-20250929` or wait for a newer Sonnet release? The SDK supports model switching at runtime, so this is not blocking.

2. **Token budgets:** What per-story and per-PRD token budgets are appropriate? Need to measure actual usage from v1 runs to set realistic limits.

3. **Parallel story execution:** Should Phase 5 explore parallel execution for independent stories? The DAG structure enables this, but complexity is high.

4. **Clawdbot v2:** Should Clawdbot also migrate to Claude Agent SDK? If so, should they share a common tool layer? This PRD focuses only on Ralph.

5. **PRD generation within Ralph:** Should Ralph be able to generate sub-PRDs when a story turns out to be too large? This would be a self-decomposition capability.

6. **Cost monitoring:** Should Ralph track and report per-PRD API costs? This helps with budgeting but adds complexity.

---

## 13. Related Documents

| Document | Location |
|----------|----------|
| Three-Agent Collaboration SOP | `docs/SOP-29-THREE-AGENT-COLLABORATION.md` |
| Ralph Usage SOP | `docs/sops/SOP-28-RALPH-USAGE.md` |
| Task Classifier | `execution/task_classifier.py` |
| Mem0 API | `execution/mem0_api.py` |
| Mem0 Client | `execution/mem0_client.py` |
| Agent Bridge API | `execution/agent_bridge_api.py` |
| v1 Pipeline | `ralph/pipeline/` |
| Handoff System | `ralph/handoffs.json` |
| Current Ralph Prompt | `ralph/prompt.md` |
| v1 Knowledge Base | `ralph/pipeline/knowledge_base.json` |
