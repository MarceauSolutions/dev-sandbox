# Multi-Agent Testing - Launch Instructions

## Quick Launch

### Step 1: Open 4 Claude Instances
Open 4 separate Claude chat windows (or browser tabs with Claude)

### Step 2: Assign Each Agent

Copy and paste these prompts into each instance:

---

### **Instance 1 - Agent 1**
```
You are Agent 1 testing the Email Analyzer project.

Your workspace: /Users/williammarceaujr./dev-sandbox/email-analyzer/testing/agent-1/

Your task:
1. Read ../TEST-PLAN.md and find the Agent 1 section
2. Come up with 3 creative edge case scenarios for single email analysis
3. Test each scenario using the workflow in ../../workflows/analyze-email-from-html.md
4. Document findings in FINDINGS.md in your folder

Focus: Edge cases in single email analysis that could break the workflow.

Be creative! Think about unusual emails, weird formats, or edge cases a real user might encounter.

When done, report: "Agent 1 testing complete. [X] critical issues, [Y] warnings, [Z] passes found."
```

---

### **Instance 2 - Agent 2**
```
You are Agent 2 testing the Email Analyzer project.

Your workspace: /Users/williammarceaujr./dev-sandbox/email-analyzer/testing/agent-2/

Your task:
1. Read ../TEST-PLAN.md and find the Agent 2 section
2. Come up with 3 creative edge case scenarios for batch email processing
3. Test each scenario using the workflow in ../../workflows/batch-email-analysis.md
4. Document findings in FINDINGS.md in your folder

Focus: Batch processing scenarios with unusual scale, composition, or performance issues.

Be creative! Think about weird batch compositions, edge cases in categorization, or scale problems.

When done, report: "Agent 2 testing complete. [X] critical issues, [Y] warnings, [Z] passes found."
```

---

### **Instance 3 - Agent 3**
```
You are Agent 3 testing the Email Analyzer project.

Your workspace: /Users/williammarceaujr./dev-sandbox/email-analyzer/testing/agent-3/

Your task:
1. Read ../TEST-PLAN.md and find the Agent 3 section
2. Come up with 3 creative edge case scenarios for financial offer comparison
3. Test each scenario using the workflow in ../../workflows/compare-financial-offers.md
4. Document findings in FINDINGS.md in your folder

Focus: Complex financial comparisons that are hard to calculate or compare fairly.

Be creative! Think about apples-to-oranges comparisons, missing data, or complex calculations.

When done, report: "Agent 3 testing complete. [X] critical issues, [Y] warnings, [Z] passes found."
```

---

### **Instance 4 - Agent 4**
```
You are Agent 4 testing the Email Analyzer project.

Your workspace: /Users/williammarceaujr./dev-sandbox/email-analyzer/testing/agent-4/

Your task:
1. Read ../TEST-PLAN.md and find the Agent 4 section
2. Come up with 3 creative edge case scenarios for workflow integration
3. Test each scenario using all workflows in ../../workflows/
4. Document findings in FINDINGS.md in your folder

Focus: Multi-step workflows, transitions between workflows, user experience issues.

Be creative! Think about confusing sequences, workflow conflicts, or unexpected user behavior.

When done, report: "Agent 4 testing complete. [X] critical issues, [Y] warnings, [Z] passes found."
```

---

## Step 3: Monitor Progress

Check on each agent periodically. They should:
1. Read their instructions ✓
2. Create 3 edge cases ✓
3. Test each case ✓
4. Document in FINDINGS.md ✓
5. Report completion ✓

## Step 4: Consolidation (After All Complete)

When all 4 agents report completion:

1. **Read all FINDINGS.md files**:
   - agent-1/FINDINGS.md
   - agent-2/FINDINGS.md
   - agent-3/FINDINGS.md
   - agent-4/FINDINGS.md

2. **Consolidate results**:
   - Count total critical issues (🔴)
   - Count total warnings (🟡)
   - Count total passes (🟢)
   - Identify common themes
   - Prioritize fixes

3. **Create consolidated report** in `consolidated-results/SUMMARY.md`

4. **Update workflows** based on findings

## Expected Timeline

- Agent setup: 5 minutes per agent
- Testing: 15-20 minutes per agent (can run in parallel)
- Documentation: 10 minutes per agent
- **Total with parallel execution**: ~30-40 minutes
- **Total with sequential**: ~2 hours

## What Each Agent Should Produce

Each `FINDINGS.md` should contain:

```markdown
# Agent [N] Test Findings

## Edge Case Scenarios Created
1. [Scenario name]
2. [Scenario name]
3. [Scenario name]

## Test Results

### Scenario 1: [Name]
**Severity**: 🔴/🟡/🟢
**Description**: [what you tested]
**Expected**: [what should happen]
**Actual**: [what happened]
**Issues**: [problems found]
**Suggested Fix**: [how to solve]

[Repeat for scenarios 2 and 3]

## Summary
- Critical Issues: [N] 🔴
- Warnings: [N] 🟡
- Passes: [N] 🟢

## Top 3 Recommendations
1. [Priority fix]
2. [Priority fix]
3. [Priority fix]
```

## Success Criteria

✅ All 4 agents complete testing
✅ 12 edge cases created (3 per agent)
✅ All FINDINGS.md files created
✅ Issues categorized by severity
✅ Suggested fixes provided
✅ Consolidated report created

## Troubleshooting

**If an agent gets stuck**:
- Remind them they only need 3 test cases
- Suggest they can create hypothetical scenarios
- They don't need actual email files to test logic
- Focus on workflow analysis, not perfect execution

**If agents duplicate scenarios**:
- That's okay! It validates the issue
- Note it in consolidation as "multiple agents found this"

**If you want to run sequentially**:
- Do Agent 1, wait for completion
- Then Agent 2, wait for completion
- Continue through Agent 4
- Same consolidation process

---

## Launch Command Summary

**Parallel (Recommended)**:
- Open 4 Claude instances
- Paste Agent 1-4 prompts above
- Wait ~30 minutes
- Consolidate results

**Sequential**:
- Use 1 Claude instance
- Paste Agent 1 prompt, wait for completion
- Paste Agent 2 prompt, wait for completion
- Continue through Agent 4
- Consolidate results

---

**Ready to launch?** Copy the agent prompts above into your Claude instances!
