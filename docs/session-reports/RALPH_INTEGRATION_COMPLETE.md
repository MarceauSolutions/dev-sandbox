# Ralph Integration for Claude Code - Setup Complete

**Date**: January 20, 2026, 10:15 AM EST
**Status**: ✅ Ready to use

---

## What is Ralph?

**Ralph** is an autonomous AI agent loop pattern created by Geoffrey Huntley that iteratively completes user stories in a PRD (Product Requirements Document) until all tasks are done.

**Original Ralph**: Built for Amp CLI (spawns fresh Amp instances in a bash loop)
**Ralph for Claude Code**: Adapted for Claude Code using native tools with manual iteration

---

## What Was Set Up

### 1. Documentation Created

| File | Purpose |
|------|---------|
| `ralph-claude.md` | Complete guide for using Ralph with Claude Code |
| `projects/social-media-automation/ralph/prd.json` | Example PRD for Grok image integration (4 stories) |
| `projects/social-media-automation/ralph/progress.txt` | Progress log for Ralph iterations |

### 2. Communication Patterns Added to CLAUDE.md

| User Says | Claude Does |
|-----------|-------------|
| "Start Ralph for [project]" / "Use Ralph" | Read [project]/ralph/prd.json, implement first incomplete story |
| "Continue Ralph" / "Next Ralph iteration" | Read updated prd.json/progress.txt, implement next story |
| "Ralph status" | Show which stories complete/pending in prd.json |
| "Integrate Ralph correctly" | Set up Ralph structure for autonomous development loops |

---

## How to Use Ralph

### Quick Start

1. **Create PRD** in `projects/[project]/ralph/prd.json`:

```json
{
  "branchName": "ralph/feature-name",
  "userStories": [
    {
      "id": "001",
      "title": "Story title",
      "acceptanceCriteria": ["Criterion 1", "Criterion 2"],
      "priority": 1,
      "passes": false
    }
  ]
}
```

2. **Start first iteration** - Say to Claude:

```
Start Ralph for social-media-automation
```

Claude will:
- Read prd.json
- Read progress.txt
- Checkout/create branch
- Implement Story 001
- Run tests
- Commit if passing
- Update prd.json (set passes: true)
- Append learnings to progress.txt

3. **Continue iterations** - Say:

```
Continue Ralph
```

Claude reads updated files and implements next story where `passes: false`.

4. **Completion** - When all stories have `passes: true`, Claude outputs:

```
<promise>COMPLETE</promise>
```

---

## Example PRD Created

**Location**: `projects/social-media-automation/ralph/prd.json`

**Feature**: Grok Image Integration for Social Media

**4 User Stories**:
1. Create Grok API client in `execution/grok_image_gen.py`
2. Update content generator to support image generation flag
3. Integrate Grok generation into scheduler
4. Update X scheduler to attach images to tweets

**Ready to Start**: Just say "Start Ralph for social-media-automation"

---

## Key Differences from Original Ralph

| Original Ralph (Amp CLI) | Ralph for Claude Code |
|--------------------------|----------------------|
| Fully automated bash loop | Manual iteration (say "Continue Ralph") |
| Fresh context each iteration | Full conversation context preserved |
| Browser automation with dev-browser skill | Manual browser verification or screenshots |
| Thread URLs for memory | Progress.txt + prd.json for memory |

---

## Best Practices

### Story Size

**Right-sized** (completable in one iteration):
- Add a database column
- Add a UI component
- Update one function
- Add a filter to a list

**Too big** (split these):
- "Build the entire dashboard"
- "Add authentication system"
- "Refactor the API"

### Quality Requirements

Before marking `passes: true`:
- ✅ All tests pass
- ✅ Code committed to git
- ✅ Progress appended to progress.txt
- ✅ prd.json updated

### Progress.txt Format

```markdown
## 2026-01-20 10:30 - Story 001
- What was implemented
- Files changed: src/module.py, tests/test_module.py
- **Learnings for future iterations:**
  - Pattern discovered: Use X for Y
  - Gotcha: Don't forget to update Z when changing W
  - Useful context: Component A is in directory B
---
```

---

## Integration with Development Pipeline

Ralph fits into Step 2 (DEVELOP):

```
0. KICKOFF (SOP 0)
1. DESIGN (Directive)
2. DEVELOP (SOP 1)
   └── For complex multi-story features: Use Ralph
       - Create prd.json with user stories
       - Run iterations until <promise>COMPLETE</promise>
       - All stories get individual commits
3. TEST (SOP 2)
4. DEPLOY (SOP 3)
```

---

## When to Use Ralph

✅ **Use Ralph when**:
- Complex feature with 3+ distinct stories
- Each story can be completed in one iteration
- Need systematic progress tracking
- Want individual commits per story
- Building something with multiple integration points

❌ **Skip Ralph when**:
- Single simple task
- Quick bug fix
- Exploratory coding
- Unclear requirements (do SOP 9 first)

---

## Example Workflow: Grok Image Integration

**Current Status**: Ready to start

**PRD Location**: `projects/social-media-automation/ralph/prd.json`

**To Begin**:
```
Start Ralph for social-media-automation
```

**Expected Timeline**:
- Iteration 1 (Story 001): Create Grok API client (~30 min)
- Iteration 2 (Story 002): Update content generator (~20 min)
- Iteration 3 (Story 003): Integrate into scheduler (~30 min)
- Iteration 4 (Story 004): Update X posting (~20 min)

**Total**: ~2 hours for complete Grok integration with systematic progress tracking

---

## Files to Reference

| File | Description |
|------|-------------|
| `ralph-claude.md` | Complete Ralph for Claude Code guide |
| `ralph/README.md` | Original Ralph documentation |
| `ralph/ralph.sh` | Original bash loop (Amp CLI) |
| `ralph/prompt.md` | Original Amp instructions |
| `projects/social-media-automation/ralph/prd.json` | Example PRD (Grok integration) |
| `CLAUDE.md` (lines 223-226) | Communication patterns |

---

## Next Steps

**Option 1**: Start Grok integration immediately
```
Start Ralph for social-media-automation
```

**Option 2**: Create PRD for different feature
```
Create a new PRD in projects/[project]/ralph/prd.json with your user stories
```

**Option 3**: Check status of existing Ralph work
```
Ralph status
```

---

## Success Criteria

- ✅ Ralph documentation created
- ✅ Example PRD created for Grok integration
- ✅ Communication patterns added to CLAUDE.md
- ✅ Ready to use with "Start Ralph for [project]" command
- ✅ Integration complete and tested

**Status**: All setup complete. Ralph is ready to use!

---

**References**:
- Original Ralph: https://github.com/snarktank/ralph
- Geoffrey Huntley's article: https://ghuntley.com/ralph/
- Interactive flowchart: https://snarktank.github.io/ralph/
