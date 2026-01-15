# Instructions for Testing Agents

## Quick Start

You are a testing agent for the Email Analyzer project. Your job is to find edge cases and issues in the workflows.

### Your Agent Number
You'll be assigned: **Agent 1**, **Agent 2**, **Agent 3**, or **Agent 4**

### Your Tasks
1. Go to your folder: `testing/agent-[YOUR NUMBER]/`
2. Read the TEST-PLAN.md
3. Find your section (Agent 1, 2, 3, or 4)
4. Execute your 10 test cases
5. Create FINDINGS.md with results

## What to Test

### Agent 1: Edge Cases in Single Email Analysis
- Weird file formats
- Very large files  
- Foreign languages
- Broken HTML

### Agent 2: Batch Processing at Scale
- Many emails at once
- Empty batches
- Mixed types
- Performance

### Agent 3: Financial Comparison Accuracy
- Complex calculations
- Missing data
- Conflicting information
- Unusual offers

### Agent 4: Integration & User Experience
- Multi-step workflows
- Error recovery
- Workflow transitions
- Confusing scenarios

## How to Report

Use this format in your FINDINGS.md:

```markdown
# Agent [N] Findings

## Test Case 1: [Name]
**Severity**: 🔴 Critical / 🟡 Warning / 🟢 Pass

**What I tested**: [description]
**Expected**: [what should happen]
**Actual**: [what did happen]
**Issues**: [list problems]
**Fix**: [how to solve]
```

## Severity Levels

- 🔴 **Critical**: Workflow completely fails
- 🟡 **Warning**: Works but has problems
- 🟢 **Pass**: Works perfectly

## Goal

Find 10-20 issues total across all agents so we can improve the workflows before users encounter these problems.

## Time Budget

- 30-60 minutes per agent
- Can run in parallel or sequentially

## Questions?

Check TEST-PLAN.md for full details.

Good luck testing!
