# Multi-Agent Testing: Quick Start Guide

## Setup Complete ✅

All testing infrastructure is ready. Follow these steps to begin parallel testing.

## Step 1: Open 4 Claude Instances

Open 4 separate Claude Code sessions:
- Browser: 4 tabs/windows with Claude Code
- Desktop app: 4 separate windows
- Or any combination

## Step 2: Launch Agents

Open `AGENT-PROMPTS.txt` in this directory and copy-paste each agent prompt into a separate Claude instance:

1. **Instance 1** → Copy "AGENT 1: Header & TOC Edge Cases" prompt
2. **Instance 2** → Copy "AGENT 2: Content Formatting Edge Cases" prompt
3. **Instance 3** → Copy "AGENT 3: Image & Link Handling" prompt
4. **Instance 4** → Copy "AGENT 4: Large Documents & Performance" prompt

## Step 3: Monitor Progress

Each agent will:
1. Create test markdown files in their workspace
2. Run the MD-to-PDF converter
3. Review generated PDFs
4. Document findings in `FINDINGS.md`

**Estimated time**: 60-90 minutes (running in parallel)

## Step 4: Wait for Completion

All 4 agents must complete before consolidation. You'll know they're done when each has created their `FINDINGS.md` file:

- ✅ `agent1/FINDINGS.md`
- ✅ `agent2/FINDINGS.md`
- ✅ `agent3/FINDINGS.md`
- ✅ `agent4/FINDINGS.md`

## Step 5: Return Here for Consolidation

Once all agents complete, return to this main session and say:

**"All agents completed. Please consolidate the findings."**

I will then:
1. Review all 4 FINDINGS.md files
2. Create `consolidated-results/CONSOLIDATED-FINDINGS.md`
3. Categorize issues: Critical → Important → Nice-to-Have
4. Prioritize fixes
5. Implement critical fixes immediately

## Testing Structure

```
projects/md-to-pdf/testing/
├── START-HERE.md              ← You are here
├── TEST-PLAN.md              ← Detailed test strategy
├── AGENT-PROMPTS.txt         ← Copy-paste prompts
├── agent1/                   ← Agent 1 workspace
│   ├── README.md
│   ├── test-*.md             ← Test files (created by agent)
│   ├── test-*.pdf            ← Generated PDFs
│   └── FINDINGS.md           ← Issues found
├── agent2/                   ← Agent 2 workspace
├── agent3/                   ← Agent 3 workspace
├── agent4/                   ← Agent 4 workspace
└── consolidated-results/     ← Final consolidated findings
    └── CONSOLIDATED-FINDINGS.md
```

## What Each Agent Tests

### Agent 1: Header & TOC Edge Cases
- Duplicate headers
- Special characters in headers
- Very long headers
- Deep nesting (H1-H6)

### Agent 2: Content Formatting
- Complex tables
- Nested lists
- Code blocks (multiple languages)
- Mixed content (blockquotes + code + lists)

### Agent 3: Image & Link Handling
- Missing images
- Various image formats (PNG, JPG, GIF, SVG)
- External links
- Internal anchor links

### Agent 4: Large Documents & Performance
- Very large documents (100+ headers)
- Empty documents
- No headers
- UTF-8 special characters (emoji, CJK, accents)

## Expected Outcomes

After testing:
- **0 CRITICAL issues** (or all resolved)
- **Few IMPORTANT issues** (fixed in v1.0.0)
- **Some NICE-TO-HAVE improvements** (backlog for v1.1.0)

## Questions?

See `TEST-PLAN.md` for complete details on:
- Testing strategy
- Agent isolation
- Deliverables
- Success criteria

---

**Ready to begin?** Open `AGENT-PROMPTS.txt` and start launching agents! 🚀
