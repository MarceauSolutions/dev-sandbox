# Ralph Autonomous Mode - Enhanced Workflow

**Enhancement to**: [ralph-claude.md](ralph-claude.md)
**Purpose**: Run Ralph continuously without manual "continue ralph" prompts, with optional checkpoints for high-risk stories

---

## Two Operating Modes

### Mode 1: Autonomous (Default)
- Runs all stories continuously
- No manual intervention needed
- Stops only when all stories complete or checkpoint encountered

### Mode 2: Manual (Original)
- Requires "continue ralph" after each story
- User reviews progress between iterations
- More control, but slower

---

## Configuration

### PRD Structure with Autonomous Support

```json
{
  "branchName": "ralph/feature-name",
  "mode": "autonomous",
  "userStories": [
    {
      "id": "001",
      "title": "Low-risk story",
      "acceptanceCriteria": [...],
      "priority": 1,
      "passes": false,
      "checkpoint": false,
      "risk_level": "low"
    },
    {
      "id": "002",
      "title": "High-risk story requiring checkpoint",
      "acceptanceCriteria": [...],
      "priority": 2,
      "passes": false,
      "checkpoint": true,
      "risk_level": "high"
    }
  ]
}
```

### Story Risk Levels

| Risk Level | Checkpoint? | Examples |
|------------|-------------|----------|
| **low** | No | Add new feature, create new file, add tests |
| **medium** | Optional | Modify existing logic, refactor module |
| **high** | Yes | Database migrations, breaking API changes, delete critical code |
| **critical** | Yes | Production deployment, payment processing, security changes |

---

## Autonomous Workflow

### Starting Autonomous Ralph

```markdown
Start Ralph for [project-name] in autonomous mode.

INSTRUCTIONS:
1. Read `[project]/ralph/prd.json` for all user stories
2. Read `[project]/ralph/progress.txt` for learnings
3. Check git branch matches PRD `branchName`
4. **AUTONOMOUS MODE**: Implement ALL stories sequentially where `passes: false`
5. For each story:
   a. Implement the story
   b. Run quality checks
   c. Commit if passing
   d. Update prd.json (set passes: true)
   e. Append to progress.txt
   f. **Check if story has "checkpoint": true**
      - If YES: STOP and ask user to review before continuing
      - If NO: Continue to next story automatically
6. When all stories have `passes: true`, output: <promise>COMPLETE</promise>

CRITICAL:
- Work on stories in priority order
- Commit after each story (not at the end)
- Stop at checkpoints for user review
- If ANY story fails quality checks, mark it incomplete and STOP
```

### Checkpoint Behavior

When Ralph encounters a story with `"checkpoint": true`:

1. **Complete the checkpoint story**:
   - Implement the feature
   - Run tests
   - Commit changes
   - Update prd.json

2. **STOP and report**:
   ```
   ✅ Story [ID] complete: [Title]

   🛑 CHECKPOINT REACHED

   This story was marked as "checkpoint": true due to [reason].

   Changes made:
   - [File 1]
   - [File 2]

   Please review the changes before I continue to the next story.

   To continue: Say "Continue Ralph"
   To abort: Say "Stop Ralph" or make manual changes
   ```

3. **Wait for user approval**

---

## When to Use Checkpoints

### Always Checkpoint For:

- **Database schema changes**: Migrations, new tables, column modifications
- **Breaking API changes**: Removing endpoints, changing request/response formats
- **External integrations**: Third-party API integrations, webhook setups
- **Payment/billing logic**: Anything touching money
- **Security changes**: Authentication, authorization, encryption
- **Production deployments**: Pushing to live systems
- **Destructive operations**: Deleting data, removing features

### No Checkpoint Needed For:

- **New features**: Adding new functionality (non-breaking)
- **Bug fixes**: Fixing existing issues
- **Tests**: Adding or updating tests
- **Documentation**: README, comments, docs
- **Refactoring**: Internal code improvements (no behavior change)
- **UI updates**: Frontend changes that don't affect backend

---

## Setting Checkpoints in PRD

### Method 1: Per-Story Flag

```json
{
  "id": "003",
  "title": "Add database migration for user roles",
  "checkpoint": true,
  "risk_level": "high",
  "acceptanceCriteria": [
    "Migration file created",
    "Runs without errors on test DB",
    "Rollback tested"
  ]
}
```

### Method 2: Automatic Based on Keywords

Ralph can auto-detect high-risk stories:

- Title contains: "migration", "delete", "deploy", "production"
- Description mentions: "breaking change", "payment", "security"
- Acceptance criteria includes: "manual verification", "production test"

---

## Communication Patterns

### Autonomous Mode

| User Says | Claude Does |
|-----------|-------------|
| "Start Ralph for [project]" | Reads prd.json, checks mode, runs ALL stories until checkpoint or completion |
| "Start Ralph in autonomous mode" | Same as above (autonomous is default) |
| "Continue Ralph" (after checkpoint) | Resumes from next story after checkpoint |

### Manual Mode (Override)

| User Says | Claude Does |
|-----------|-------------|
| "Start Ralph in manual mode for [project]" | Implements ONE story, waits for "Continue Ralph" |
| "Continue Ralph" | Implements next story, waits again |

### Status Checks

| User Says | Claude Does |
|-----------|-------------|
| "Ralph status" | Shows progress: X/Y stories complete, next story, checkpoints ahead |
| "Ralph summary" | Full report: completed stories, current story, remaining work |

---

## Example: Autonomous Mode in Action

### PRD (4 stories, 1 checkpoint)

```json
{
  "branchName": "ralph/payment-integration",
  "mode": "autonomous",
  "userStories": [
    {
      "id": "001",
      "title": "Add Stripe API client",
      "checkpoint": false,
      "risk_level": "low"
    },
    {
      "id": "002",
      "title": "Create payment form UI",
      "checkpoint": false,
      "risk_level": "low"
    },
    {
      "id": "003",
      "title": "Integrate Stripe checkout",
      "checkpoint": true,
      "risk_level": "high"
    },
    {
      "id": "004",
      "title": "Add payment confirmation email",
      "checkpoint": false,
      "risk_level": "low"
    }
  ]
}
```

### User Action

```
User: "Start Ralph for payment-integration"
```

### Ralph Execution

```
[Iteration 1] Implementing Story 001... ✅ Complete
[Iteration 2] Implementing Story 002... ✅ Complete
[Iteration 3] Implementing Story 003... ✅ Complete

🛑 CHECKPOINT REACHED

Story 003 complete: "Integrate Stripe checkout"

This story was marked as high-risk because it handles payment processing.

Changes made:
- src/payment_processor.py (NEW)
- src/checkout_form.py (MODIFIED)
- .env.example (MODIFIED - added STRIPE_SECRET_KEY)

Please test the Stripe integration before I continue to Story 004.

To continue: Say "Continue Ralph"
```

### User Reviews, Then:

```
User: "Continue Ralph"
```

### Ralph Resumes

```
[Iteration 4] Implementing Story 004... ✅ Complete

<promise>COMPLETE</promise>

All 4 stories in payment-integration PRD are complete.
```

---

## Benefits of Autonomous Mode

### Time Savings

**Manual Mode**:
- 4 stories = 4 manual "continue ralph" prompts
- ~30 seconds per prompt
- Total overhead: 2 minutes

**Autonomous Mode**:
- 4 stories = 0 manual prompts (unless checkpoint)
- Total overhead: 0 minutes (or <1 minute at checkpoint)

**For 10-story feature**:
- Manual: 5 minutes overhead
- Autonomous: 0-2 minutes overhead

### Better Flow

- No context switching for William
- Ralph maintains momentum
- Learnings from previous stories immediately inform next stories

### Strategic Checkpoints

- Review ONLY when it matters (high-risk changes)
- Skip review for routine work
- Confidence that critical changes get human oversight

---

## Safeguards in Autonomous Mode

Even in autonomous mode, Ralph will STOP if:

1. **Story fails quality checks** (tests fail, lint errors)
2. **Checkpoint encountered** (story has `"checkpoint": true`)
3. **External dependency needed** (API key missing, service down)
4. **Ambiguous acceptance criteria** (can't determine if story passes)
5. **Max iterations reached** (default: 10 stories, configurable)

---

## Configuration File

Optional `[project]/ralph/config.json`:

```json
{
  "mode": "autonomous",
  "checkpoint_conditions": [
    "high_risk_story",
    "database_migration",
    "external_api_integration"
  ],
  "auto_continue": true,
  "max_iterations": 10,
  "stop_on_test_failure": true,
  "settings": {
    "commit_after_each_story": true,
    "run_tests": true,
    "update_progress": true
  }
}
```

---

## Migration from Manual to Autonomous

### Existing PRDs

If you have an existing PRD without `checkpoint` flags:

```bash
# Add checkpoint flags to existing prd.json
python -c "
import json
from pathlib import Path

prd_path = Path('projects/[project]/ralph/prd.json')
prd = json.loads(prd_path.read_text())

# Add mode
prd['mode'] = 'autonomous'

# Add checkpoint flags to each story (default: false)
for story in prd['userStories']:
    if 'checkpoint' not in story:
        story['checkpoint'] = False
    if 'risk_level' not in story:
        story['risk_level'] = 'low'

prd_path.write_text(json.dumps(prd, indent=2))
print('✅ PRD updated for autonomous mode')
"
```

### Gradual Adoption

Start conservative:
1. **Week 1**: Set all stories to `"checkpoint": true` (review every story)
2. **Week 2**: Remove checkpoints from low-risk stories
3. **Week 3**: Only checkpoint high-risk stories
4. **Week 4+**: Fully autonomous with strategic checkpoints

---

## Best Practices

### 1. Right-size Stories for Autonomy

**Good** (autonomous-friendly):
- "Add user registration endpoint"
- "Create email template for password reset"
- "Add tests for payment validation"

**Bad** (too vague for autonomous):
- "Improve user experience"
- "Optimize the database"
- "Fix bugs"

### 2. Clear Acceptance Criteria

**Good**:
- "Registration endpoint returns 201 on success"
- "Email includes reset link with 1-hour expiry token"
- "Tests cover valid card, invalid card, expired card"

**Bad**:
- "Endpoint works"
- "Email looks good"
- "Tests pass"

### 3. Checkpoint Strategically

Don't checkpoint everything - defeats the purpose of autonomous mode.

**Rule of thumb**:
- < 5 stories: 0-1 checkpoints
- 5-10 stories: 1-2 checkpoints
- 10+ stories: Split into multiple features

---

## Communication Pattern Update

Add to `CLAUDE.md`:

```markdown
| William Says | Claude Does |
|--------------|-------------|
| "Start Ralph for [project]" | Read prd.json, implement all stories autonomously, stop at checkpoints |
| "Start Ralph in manual mode" | Implement ONE story, wait for "continue ralph" |
| "Continue Ralph" | Resume after checkpoint or implement next story (manual mode) |
| "Ralph status" | Show progress: X/Y complete, next story, checkpoints ahead |
```

---

## References

- [ralph-claude.md](ralph-claude.md) - Original Ralph for Claude Code
- [Ralph by Geoffrey Huntley](https://github.com/snarktank/ralph) - Original bash loop implementation
- PRD Template: `[project]/ralph/prd-template.json`
- Config Template: `[project]/ralph/config.json`

---

**Default Mode**: Autonomous
**Override**: Add `"mode": "manual"` to prd.json or say "Start Ralph in manual mode"
