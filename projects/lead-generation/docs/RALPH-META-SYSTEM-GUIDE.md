# Ralph Meta-System Quick Reference

**Status**: ✅ All systems operational (6/6 stories complete)

---

## 1. Ralph Decision Engine

**Purpose**: Automatically decide when to use Ralph for a request

### Commands

```bash
# Analyze a request
python -m src.ralph_decision_engine analyze "Create templates for HVAC outreach campaign"

# Output:
# {
#   "use_ralph": true,
#   "confidence": "high",
#   "estimated_stories": 5,
#   "autonomous_mode": true,
#   "reasoning": "Multi-step workflow with template creation, validation..."
# }
```

### Decision Criteria

| Complexity Score | Recommendation | Example |
|-----------------|----------------|---------|
| 1-3 | ❌ Don't use Ralph | Fix typo, single file edit |
| 4-6 | ⚠️ Maybe Ralph | 2-3 file changes |
| 7-10 | ✅ Definitely Ralph | Multi-step system, 4+ files |

**Auto-detected signals for Ralph**:
- 3+ related tasks/files to modify
- Multi-step workflow with dependencies
- Repeatable pattern (migrations, refactoring)
- Needs checkpoint review midway
- User explicitly says "use ralph"

---

## 2. Docket System (Request Queue)

**Purpose**: Queue requests made during active work, prioritize, and sequence execution

### Core Commands

```bash
# View all requests
python -m src.docket status

# Add new request
python -m src.docket add "Create shipping templates" --priority high

# Get next recommended task
python -m src.docket next

# View optimized execution sequence
python -m src.docket sequence

# Mark request complete
python -m src.docket complete req_001

# Block a request
python -m src.docket block req_002 --reason "Waiting for template approval"
```

### Request Schema

```json
{
  "request_id": "req_001",
  "description": "Create HVAC templates",
  "priority": "high",  // urgent/high/normal/low
  "status": "pending", // pending/in_progress/blocked/complete
  "dependencies": ["req_000"],
  "ralph_decision": {
    "use_ralph": true,
    "autonomous": true,
    "estimated_time": "30-60 min"
  }
}
```

### Priority Rules

| Priority | Symbol | When |
|----------|--------|------|
| `urgent` | 🔥 | Blocking other work, customer waiting |
| `high` | ⚡ | Important, should do soon |
| `normal` | 📋 | Regular work |
| `low` | 💤 | Nice to have, do when free |

### Dependency Resolution

The docket automatically:
- ✅ Detects circular dependencies (warns user)
- ✅ Identifies parallel tasks (can run simultaneously)
- ✅ Respects priorities while honoring dependencies
- ✅ Excludes blocked tasks from sequence

**Example Output**:
```
OPTIMIZED EXECUTION SEQUENCE:

1. PARALLEL: req_003, req_001, req_006
   ├─ Build analytics dashboard (urgent)
   ├─ Create HVAC templates (high)
   ├─ Task C independent (normal)

2. SEQUENTIAL: req_002
   └─ Test HVAC templates (depends on req_001)

⚠️  WARNING: Circular dependency detected!
  - req_007 depends on req_008
  - req_008 depends on req_007
```

---

## 3. Ralph Auto-Invocation

**Purpose**: Automatically launch Ralph when request matches criteria

### Workflow

```bash
# Analyze request and auto-invoke if recommended
python -m src.ralph_auto_invoke "Create templates for all 3 businesses"

# Steps executed:
# 1. Run ralph_decision_engine.analyze()
# 2. If use_ralph=yes, generate PRD automatically
# 3. Ask user: "Use Ralph? (5 stories, recommended)"
# 4. If yes, launch Ralph with generated PRD
# 5. Add to docket if user says "queue for later"
```

### Auto-Generated PRD

Ralph can now generate PRDs automatically:
- Breaks request into discrete stories
- Identifies checkpoints (every 3 stories)
- Estimates completion time
- Includes acceptance criteria

---

## 4. Ralph Meta-PRD Generator (Meta-Circular)

**Purpose**: Ralph can improve Ralph (with user approval)

### Commands

```bash
# Analyze a Ralph subsystem
python -m src.ralph_meta_prd_generator analyze docket

# Generate improvement PRD
python -m src.ralph_meta_prd_generator improve docket "Add export to CSV feature"

# Output: PRD with stories for self-improvement
# User must approve before Ralph modifies itself (safety mechanism)
```

### Self-Improvement Flow

```
User: "Ralph, improve the docket system to support CSV export"
  ↓
Ralph analyzes docket.py
  ↓
Ralph generates 4-story PRD:
  - Story 1: Add CSV export method
  - Story 2: Add CLI command
  - Story 3: Add tests
  - Story 4: Update documentation
  ↓
Ralph asks: "I have a 4-story plan. Approve?"
  ↓
User approves → Ralph executes PRD autonomously
  ↓
Ralph reports completion with before/after metrics
```

**Safety**: User approval ALWAYS required before Ralph modifies itself

---

## 5. Integration with Workflow

### Scenario 1: New Request While Working

**Before Meta-System**:
```
User: "Create HVAC templates"
Claude: [starts working]
User: "Also create shipping templates"
Claude: [confused, context switches]
```

**After Meta-System**:
```
User: "Create HVAC templates"
Claude: [analyzes → recommends Ralph → launches]
User: "Also create shipping templates"
Claude: [adds to docket]
  → "Added to docket (req_002). Pause current work or queue?"
User: "Queue it"
Claude: [continues HVAC work, shipping queued for later]
```

### Scenario 2: Complex Multi-Step Request

**User**: "Optimize the entire cold outreach system"

**Ralph Meta-System**:
1. Decision engine analyzes → complexity: 9/10
2. Recommendation: "Use Ralph (15+ stories, autonomous with checkpoints)"
3. Auto-generates PRD with stories
4. User approves
5. Ralph executes autonomously
6. Checkpoint at story 3, 6, 9, 12, 15
7. Completion report with metrics

---

## 6. Communication Patterns

| User Says | Claude Does |
|-----------|-------------|
| "Use Ralph for this" | Run decision engine, launch if recommended |
| "Add to docket" | Add request to queue with priority |
| "What's next?" | `python -m src.docket next` |
| "Show queue" | `python -m src.docket status` |
| "Optimize sequence" | `python -m src.docket sequence` |
| "Ralph, improve [system]" | Generate meta-PRD for self-improvement |

---

## 7. Success Metrics

**Ralph Decision Accuracy**: 95%+ correct use_ralph recommendations
**Docket Completion Rate**: 90%+ of docketed items completed
**Time to Decision**: <5 seconds to analyze and recommend
**User Satisfaction**: User says "yes" to Ralph recommendation 90%+ of time

---

## Current Status

✅ **All 6 Stories Complete**:
1. Ralph Decision Engine → `ralph_decision_engine.py` (300+ lines)
2. Docket System → `docket.py` (480+ lines)
3. Docket CLI → CLI commands working
4. Auto-Invocation → `ralph_auto_invoke.py` (400+ lines)
5. Dependency Resolution → Topological sort, circular detection, parallel tasks
6. Meta-Workflow → `ralph_meta_prd_generator.py` (500+ lines)

**Files Created**:
- `src/ralph_decision_engine.py`
- `src/docket.py`
- `src/ralph_auto_invoke.py`
- `src/ralph_meta_prd_generator.py`
- `config/ralph_decision_rules.json`
- `ralph/ralph-meta-system-prd.json`

**Example Docket State**:
```bash
$ python -m src.docket status

Total Requests: 8
Completed: 0
Pending: 8

NEXT RECOMMENDED: req_003 (Build analytics dashboard - URGENT)

PARALLEL OPPORTUNITIES:
  - req_003, req_001, req_006, req_004 can run simultaneously

WARNINGS:
  - Circular dependency: req_007 ↔ req_008
```

---

## Next Steps (When Needed)

1. **Use the docket**: Start adding real requests as they come in
2. **Test auto-invocation**: Let Ralph auto-detect when to use Ralph
3. **Meta-improvement**: Have Ralph improve its own decision engine
4. **Integration**: Wire docket checks into main workflow loops

**The system is ready to use!** 🚀
