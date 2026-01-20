# Ralph for Claude Code - Autonomous Development Loop

**Adapted from**: [snarktank/ralph](https://github.com/snarktank/ralph) - Geoffrey Huntley's Ralph pattern

## Key Differences from Original Ralph

| Original Ralph | Ralph for Claude Code |
|----------------|----------------------|
| Uses Amp CLI (`amp` command) | Uses Claude Code native tools |
| Spawns fresh Amp instances in bash loop | Manual iteration (or future automation via Task tool) |
| Browser verification with `dev-browser` skill | Manual browser verification or screenshot uploads |
| Thread URLs for memory | Full conversation context preserved |

## Core Concept (Unchanged)

**Autonomous loop that completes PRD items one-by-one until all pass.**

Memory between iterations:
- Git history (commits)
- `progress.txt` (learnings)
- `prd.json` (task status)

## Setup for Claude Code

### 1. Copy Ralph Files

```bash
cd /Users/williammarceaujr./dev-sandbox
mkdir -p [project]/ralph/
cp ralph/prd.json.example [project]/ralph/prd.json
cp ralph/prompt.md [project]/ralph/prompt-claude.md
touch [project]/ralph/progress.txt
```

### 2. Create Your PRD

Edit `[project]/ralph/prd.json`:

```json
{
  "branchName": "ralph/feature-name",
  "userStories": [
    {
      "id": "001",
      "title": "Add X functionality",
      "acceptanceCriteria": [
        "Feature works as expected",
        "Tests pass",
        "No breaking changes"
      ],
      "priority": 1,
      "passes": false
    }
  ]
}
```

**Critical**: Keep stories SMALL (completable in one iteration). Right-sized stories:
- Add a database column
- Add a UI component
- Update one function with new logic
- Add a filter to a list

**Too big** (split these):
- "Build the entire dashboard"
- "Add authentication system"
- "Refactor the API"

## Workflow

### Iteration 1: Read Instructions

Copy-paste into Claude Code:

```markdown
I'm starting a Ralph iteration for [project-name].

INSTRUCTIONS:
1. Read `[project]/ralph/prd.json` for all user stories
2. Read `[project]/ralph/progress.txt` for learnings from previous iterations
3. Check git branch matches PRD `branchName` (checkout or create if needed)
4. Pick the HIGHEST PRIORITY story where `passes: false`
5. Implement that ONE story
6. Run quality checks (typecheck, lint, test - whatever the project uses)
7. If checks pass: Commit ALL changes with message: `feat: [Story ID] - [Story Title]`
8. Update `prd.json` to set `passes: true` for completed story
9. Append progress to `progress.txt` in this format:

## [Date/Time] - [Story ID]
- What was implemented
- Files changed
- **Learnings for future iterations:**
  - Patterns discovered
  - Gotchas encountered
  - Useful context
---

10. If ALL stories have `passes: true`, reply with: <promise>COMPLETE</promise>

CRITICAL:
- Work on ONE story only
- Keep changes minimal and focused
- Do NOT commit broken code
- Read Codebase Patterns section in progress.txt FIRST
```

### Iteration 2+: Same Instructions

After Claude Code completes an iteration, paste the same prompt again. Claude will:
- Read updated `prd.json` (previous story marked complete)
- Read updated `progress.txt` (learnings from previous iteration)
- Pick next story where `passes: false`
- Repeat

### Stop Condition

When Claude outputs `<promise>COMPLETE</promise>`, all stories are done.

## Quality Requirements

**Before marking story as `passes: true`:**
- ✅ All quality checks pass (typecheck, tests, lint)
- ✅ Code committed to git
- ✅ Progress appended to `progress.txt`
- ✅ `prd.json` updated

**For frontend stories:**
- ✅ Manual browser verification OR screenshot uploaded
- Add to acceptance criteria: "Verified in browser"

## Progress.txt Best Practices

### Codebase Patterns Section (Top of File)

Create this section at the TOP after first few iterations:

```markdown
## Codebase Patterns
- Use `execution/` for shared utilities (2+ projects)
- Use `projects/[name]/src/` for project-specific code
- Always run tests before committing
- Follow DOE architecture (Directive → Orchestration → Execution)
```

### Per-Iteration Learnings

```markdown
## 2026-01-20 09:45 - Story 001
- Implemented SMS follow-up automation
- Files changed: src/follow_up_sequence.py, crontab
- **Learnings for future iterations:**
  - SMS "queued" status must be in success conditions
  - Business hours logic runs 9 AM - 8 PM EST
  - Cron jobs need absolute paths to python interpreter
---
```

## Integration with Claude Code Workflow

Ralph fits into the development pipeline:

```
0. KICKOFF (SOP 0)
1. DESIGN (Directive)
2. DEVELOP (SOP 1)
   └── For complex multi-story features: Use Ralph
       - Create prd.json
       - Run iterations until <promise>COMPLETE</promise>
3. TEST (SOP 2)
4. DEPLOY (SOP 3)
```

## Example: Using Ralph for Social Media Content System

**Scenario**: Add Grok image generation to social media automation (4 stories)

### prd.json

```json
{
  "branchName": "ralph/grok-image-generation",
  "userStories": [
    {
      "id": "001",
      "title": "Add Grok API client to shared utilities",
      "acceptanceCriteria": [
        "execution/grok_image_gen.py created",
        "Handles XAI API key from .env",
        "Returns image path or error"
      ],
      "priority": 1,
      "passes": false
    },
    {
      "id": "002",
      "title": "Update content generator to flag 50% for images",
      "acceptanceCriteria": [
        "generate_post() has generate_image parameter",
        "50% of posts flagged based on template type",
        "No actual image generation yet (placeholder)"
      ],
      "priority": 2,
      "passes": false
    },
    {
      "id": "003",
      "title": "Integrate Grok generation into scheduler",
      "acceptanceCriteria": [
        "Calls Grok API for flagged posts",
        "Saves images to output/images/",
        "Updates post media_paths field"
      ],
      "priority": 3,
      "passes": false
    },
    {
      "id": "004",
      "title": "Update X posting to attach images",
      "acceptanceCriteria": [
        "X API call includes media upload",
        "Images attached to tweets",
        "Verified manually with test post"
      ],
      "priority": 4,
      "passes": false
    }
  ]
}
```

### Iteration 1

Claude Code receives prompt → implements Story 001 → commits → updates prd.json → appends progress.txt

### Iteration 2

Claude Code receives same prompt → reads updated prd.json → sees Story 001 complete → implements Story 002 → commits → updates → appends

### Iteration 3-4

Same pattern until all 4 stories complete

### Completion

After Story 004 complete, Claude outputs:

```
All user stories in prd.json now have passes: true.

<promise>COMPLETE</promise>
```

## Archiving Previous Runs

Ralph auto-archives when branch changes. For Claude Code, manually archive:

```bash
# When starting new feature
DATE=$(date +%Y-%m-%d)
FEATURE="previous-feature-name"
mkdir -p [project]/ralph/archive/$DATE-$FEATURE
cp [project]/ralph/prd.json [project]/ralph/archive/$DATE-$FEATURE/
cp [project]/ralph/progress.txt [project]/ralph/archive/$DATE-$FEATURE/

# Reset for new feature
echo "# Ralph Progress Log" > [project]/ralph/progress.txt
echo "Started: $(date)" >> [project]/ralph/progress.txt
echo "---" >> [project]/ralph/progress.txt
```

## Limitations vs Original Ralph

**Original Ralph advantages:**
- Fully automated bash loop (no manual re-prompting)
- Fresh context each iteration (prevents context pollution)
- Browser automation via dev-browser skill

**Claude Code advantages:**
- Native tool integration (Bash, Read, Edit, Write)
- Full conversation context (no thread URL needed)
- Direct file editing (no context switching)

**Workaround for automation**: Could use Claude Code's Task tool to spawn agents for each story, but manual iteration gives more control.

## Communication Pattern

| User Says | Claude Does |
|-----------|-------------|
| "Start Ralph for [project]" | Read prd.json, progress.txt, implement first story |
| "Continue Ralph" | Read updated files, implement next story |
| "Ralph status" | Show which stories complete/pending |

## Success Criteria

- ✅ Each story completes in one iteration
- ✅ All commits pass quality checks
- ✅ Progress.txt has learnings from each iteration
- ✅ All stories marked `passes: true` before completion
- ✅ `<promise>COMPLETE</promise>` signal when done

## References

- Original Ralph: https://github.com/snarktank/ralph
- Geoffrey Huntley's article: https://ghuntley.com/ralph/
- Interactive flowchart: https://snarktank.github.io/ralph/
