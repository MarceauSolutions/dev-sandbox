# Email Analyzer Testing Plan

## Overview
Multiple Claude instances will test the email-analyzer workflows in parallel, focusing on edge cases and potential issues.

## Testing Structure

```
testing/
├── agent-1/          # Agent 1 workspace
├── agent-2/          # Agent 2 workspace
├── agent-3/          # Agent 3 workspace
├── agent-4/          # Agent 4 workspace
├── consolidated-results/  # Merged findings
└── TEST-PLAN.md      # This file
```

## Test Agent Assignments

### Agent 1: Single Email Analysis Edge Cases
**Focus**: Test analyze-email-from-html.md workflow with unusual inputs

**Your Mission**: Come up with 3 creative edge case scenarios that could break the workflow. Think about unusual email formats, unexpected content, or edge cases a normal user might encounter.

**Example Edge Cases** (don't use these - create your own!):
- Email with all text in images
- Foreign language promotional email
- Email that's actually a calendar invite saved as HTML

**Deliverable**: `agent-1/FINDINGS.md` with:
- Your 3 edge case scenarios
- Test results for each
- Issues found
- Suggested fixes

### Agent 2: Batch Processing & Performance
**Focus**: Test batch-email-analysis.md with scale and variety

**Your Mission**: Come up with 3 creative batch processing scenarios that could cause problems. Think about unusual batch compositions, scale issues, or mixed content that's hard to compare.

**Example Edge Cases** (don't use these - create your own!):
- Batch with 1 email from each of 20 different categories
- All emails are duplicates of the same offer
- Batch contains emails spanning 5 years

**Deliverable**: `agent-2/FINDINGS.md` with:
- Your 3 edge case scenarios
- Test results for each
- Performance observations
- Suggested improvements

### Agent 3: Financial Comparison Accuracy
**Focus**: Test compare-financial-offers.md with complex scenarios

**Your Mission**: Come up with 3 creative financial comparison scenarios that are hard to compare fairly. Think about offers that aren't apples-to-apples, missing critical data, or complex calculations.

**Example Edge Cases** (don't use these - create your own!):
- Comparing a 0% APR credit card to a high-yield savings account
- One offer in USD, one in EUR, one in GBP
- Bonus requires spending vs bonus is automatic

**Deliverable**: `agent-3/FINDINGS.md` with:
- Your 3 edge case scenarios
- Calculation verification
- Comparison logic assessment
- Suggested improvements

### Agent 4: Integration & Workflow Flow
**Focus**: Test complete workflows end-to-end and cross-workflow integration

**Your Mission**: Come up with 3 creative multi-step or workflow transition scenarios. Think about confusing user interactions, workflow conflicts, or unexpected sequencing.

**Example Edge Cases** (don't use these - create your own!):
- User asks to compare before analyzing
- User changes criteria mid-analysis
- User wants to analyze the analysis summary email

**Deliverable**: `agent-4/FINDINGS.md` with:
- Your 3 edge case scenarios
- Workflow flow assessment
- User experience observations
- Suggested improvements

## Testing Methodology

### Phase 1: Setup (Each Agent)
1. Navigate to assigned agent folder: `cd testing/agent-[N]/`
2. Create test email samples (or use provided samples)
3. Read assigned test plan section
4. Prepare test data

### Phase 2: Execution (Parallel)
1. Run each test case systematically
2. Document observations in real-time
3. Capture error messages verbatim
4. Note workarounds discovered
5. Track time spent on each test

### Phase 3: Documentation (Each Agent)
1. Create `FINDINGS.md` in agent folder
2. Use standard format (see template below)
3. Include severity ratings:
   - 🔴 Critical: Workflow fails completely
   - 🟡 Warning: Works but with issues
   - 🟢 Pass: Works as expected
4. Suggest fixes for each issue

### Phase 4: Consolidation (After All Tests)
1. Merge all FINDINGS.md into `consolidated-results/`
2. Identify common issues across agents
3. Prioritize fixes by severity and frequency
4. Update workflows based on learnings

## Findings Template

Each agent should use this structure in their FINDINGS.md:

```markdown
# Agent [N] Test Findings
**Focus Area**: [Area name]
**Test Date**: [Date]
**Duration**: [Time spent]

## Summary
- Total Test Cases: [N]
- Pass: [N] 🟢
- Warning: [N] 🟡
- Critical: [N] 🔴

## Test Results

### Test Case [N]: [Name]
**Severity**: [🔴/🟡/🟢]
**Status**: [Pass/Fail/Partial]

**What I Tested**:
[Description]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happened]

**Issues Found**:
- [Issue 1]
- [Issue 2]

**Suggested Fix**:
[How to resolve]

**Workaround**:
[Temporary solution if any]

---

[Repeat for each test case]

## Overall Workflow Assessment

**Strengths**:
- [What worked well]

**Weaknesses**:
- [What needs improvement]

**Critical Issues**:
- [Must-fix problems]

**Nice-to-Have Improvements**:
- [Enhancement suggestions]

## Example Edge Cases for Documentation

[Provide 2-3 well-documented examples of edge cases that should be added to workflow docs]

## Time Analysis
- Fastest test: [Test name] - [Time]
- Slowest test: [Test name] - [Time]
- Average per test: [Time]

## Recommendations
1. [Priority 1 fix]
2. [Priority 2 fix]
3. [Priority 3 fix]
```

## Sample Test Data

### Creating Test Emails

**Agent 1 - Edge Cases**:
```bash
# Create test HTML files
echo "<html><head><title>Huge Email</title></head><body>$(seq 1 100000 | sed 's/.*/<p>&<\/p>/')</body></html>" > agent-1/huge-email.html

echo "<html><head><title>Bonjour!</title></head><body><p>Cette offre expire demain</p></body></html>" > agent-1/french-email.html
```

**Agent 2 - Batch**:
```bash
# Create 20 test emails
for i in {1..20}; do
  echo "<html><head><title>Offer $i</title></head><body><p>Test email $i</p></body></html>" > agent-2/email-$i.html
done
```

**Agent 3 - Financial**:
Create emails with:
- Different APY values
- Various bonus structures
- Conflicting information
- Missing key data

**Agent 4 - Integration**:
Use mix of emails from agents 1-3

## Success Criteria

### Per-Agent Success
- All test cases attempted
- Issues documented with severity
- Fixes suggested for critical issues
- Examples provided for edge cases

### Overall Success
- All critical issues identified
- Workflow improvements documented
- Edge cases added to documentation
- Performance baselines established

## Post-Testing Actions

After consolidation, William/Claude will:
1. Review all findings
2. Prioritize fixes by severity
3. Update workflows with:
   - Edge case handling
   - Error messages
   - Troubleshooting sections
   - Example scenarios
4. Add discovered edge cases to documentation
5. Create issue tracking if needed
6. Plan v1.1.0 improvements

## Running the Tests

### For William
1. Open 4 Claude instances (or run sequentially)
2. Assign each instance an agent number
3. Point each to: `/dev-sandbox/email-analyzer/testing/agent-[N]/`
4. Give directive: "You are Agent [N]. Review the TEST-PLAN.md and execute your test cases. Document findings in FINDINGS.md."
5. Let agents work in parallel
6. Review consolidated results

### For Testing Agents
1. Read TEST-PLAN.md
2. Navigate to your agent-[N] folder
3. Execute assigned test cases
4. Document in FINDINGS.md
5. Report completion

## Timeline

- **Setup**: 10 min per agent
- **Execution**: 30-60 min per agent (parallel)
- **Documentation**: 20 min per agent
- **Consolidation**: 30 min
- **Total**: ~2-3 hours with parallel execution

## Questions for Agents

While testing, consider:
- Does the workflow clearly explain what to do?
- Are error messages helpful?
- Can a user recover from errors easily?
- Are examples sufficient?
- Is the output format useful?
- What would confuse a new user?
- What automation would help most?

---

**Ready to Test**: YES
**Agents Required**: 4 (can run sequentially if needed)
**Test Data**: Agents create own OR use samples from William
**Expected Issues**: 10-20 (mix of critical, warning, pass)
