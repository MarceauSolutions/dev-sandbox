# 🚀 Multi-Agent Testing - START HERE

## Ready to Launch Testing!

All test infrastructure is set up. Here's how to launch:

## Option 1: Copy-Paste Prompts (Easiest)

### Step 1: Open the Agent Prompts File
```bash
cat /Users/williammarceaujr./dev-sandbox/email-analyzer/testing/AGENT-PROMPTS.txt
```

### Step 2: Copy Each Prompt
You'll see 4 clearly marked prompts:
- INSTANCE 1 - AGENT 1
- INSTANCE 2 - AGENT 2
- INSTANCE 3 - AGENT 3
- INSTANCE 4 - AGENT 4

### Step 3: Paste Into 4 Claude Instances
Open 4 Claude windows and paste one prompt into each.

### Step 4: Wait for Results
Each agent will:
- Create 3 creative edge case scenarios
- Test them
- Document findings in their folder
- Report completion

---

## Option 2: Sequential Testing (One Instance)

Run one agent at a time in the same Claude instance:

1. **Agent 1**: Copy Agent 1 prompt, wait for completion
2. **Agent 2**: Copy Agent 2 prompt, wait for completion
3. **Agent 3**: Copy Agent 3 prompt, wait for completion
4. **Agent 4**: Copy Agent 4 prompt, wait for completion

---

## What Each Agent Will Do

### Agent 1: Single Email Edge Cases
- Create 3 unusual email scenarios
- Test analyze-email-from-html.md workflow
- Find what breaks it

### Agent 2: Batch Processing
- Create 3 weird batch scenarios
- Test batch-email-analysis.md workflow
- Find scale/composition issues

### Agent 3: Financial Comparisons
- Create 3 complex comparison scenarios
- Test compare-financial-offers.md workflow
- Find calculation/logic issues

### Agent 4: Integration
- Create 3 multi-step scenarios
- Test all workflows together
- Find UX/transition issues

---

## Expected Output

Each agent creates `FINDINGS.md` in their folder:
- `agent-1/FINDINGS.md`
- `agent-2/FINDINGS.md`
- `agent-3/FINDINGS.md`
- `agent-4/FINDINGS.md`

Each contains:
- 3 edge case scenarios
- Test results
- Issues found (🔴 Critical, 🟡 Warning, 🟢 Pass)
- Suggested fixes

---

## Timeline

**Parallel** (4 instances): ~30-40 minutes total
**Sequential** (1 instance): ~2 hours total

---

## After Testing

Once all agents complete:

1. **Review findings**:
   ```bash
   cat agent-1/FINDINGS.md
   cat agent-2/FINDINGS.md
   cat agent-3/FINDINGS.md
   cat agent-4/FINDINGS.md
   ```

2. **Consolidate results** in `consolidated-results/`

3. **Update workflows** based on findings

---

## Quick Launch Command

### See All Agent Prompts:
```bash
cat /Users/williammarceaujr./dev-sandbox/email-analyzer/testing/AGENT-PROMPTS.txt
```

### Or Open in Editor:
```bash
open /Users/williammarceaujr./dev-sandbox/email-analyzer/testing/AGENT-PROMPTS.txt
```

---

## Files You Need

✅ **AGENT-PROMPTS.txt** - Copy-paste prompts (THIS IS THE MAIN FILE)
✅ **LAUNCH-INSTRUCTIONS.md** - Detailed instructions
✅ **TEST-PLAN.md** - Full test plan
✅ **AGENT-INSTRUCTIONS.md** - Quick reference for agents

---

## Ready?

**Open AGENT-PROMPTS.txt and copy the prompts into Claude instances!**

```bash
cat /Users/williammarceaujr./dev-sandbox/email-analyzer/testing/AGENT-PROMPTS.txt
```

🚀 **Let's find those edge cases!**
