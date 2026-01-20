# Human Actions Required

**Estimated Time:** 4-5 hours total (for rigorous validation)

---

## Overview

Agent 2 has completed all automated work for accuracy validation. The following tasks require human action.

**IMPORTANT:** For statistically valid results, collect data across 3 sessions under different conditions. See `TESTING-METHODOLOGY.md` for full details.

---

## Testing Schedule (Recommended)

| Session | When | Condition | Time Required |
|---------|------|-----------|---------------|
| 1 | Tuesday 2PM | Off-peak baseline | 45-60 min |
| 2 | Friday 6PM | Evening rush | 45-60 min |
| 3 | Saturday 11PM | Late night/surge | 45-60 min |

**Why 3 sessions?** Single session only tests one condition. Multiple sessions provide:
- Baseline accuracy (no surge)
- Surge prediction accuracy
- Statistical confidence (90+ samples per service)

---

## Task 1: Collect Actual Quotes (30-45 minutes per session)

**What:** Collect real Uber and Lyft quotes for 30 test routes
**Why:** To validate our price estimation algorithm

### Steps:

1. **Prepare**
   ```bash
   cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent2-accuracy-testing/workspace
   cp actual-quotes-template.csv actual-quotes.csv
   ```

2. **Collect quotes** for each of the 30 routes:
   - Open Uber app, enter route, record UberX price
   - Open Lyft app, enter route, record Lyft price
   - Fill in `actual-quotes.csv`

3. **Best time:** Tuesday-Thursday, 2-4 PM (minimal surge)

**Detailed guide:** `output/QUOTE-COLLECTION-GUIDE.md`

---

## Task 2: Run Analysis (5 minutes)

**What:** Run the accuracy analysis script
**Why:** Compare our estimates against actual quotes

### Steps:

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent2-accuracy-testing/workspace
python3 calculate_accuracy.py
```

**Output:**
- `output/ACCURACY-REPORT.md` - Full analysis
- `workspace/accuracy-metrics.csv` - Raw data

---

## Task 3: Review Results (5-10 minutes)

**What:** Check if we meet accuracy targets
**Why:** Determine if algorithm is ready for production

### Success Criteria:

| Metric | Target |
|--------|--------|
| Overall accuracy | 85%+ within 20% |
| Recommendation accuracy | 80%+ correct |

### If targets met:
- Algorithm validated
- Ready for production deployment

### If targets not met:
- Review high-error cities/routes
- Update rate cards
- Re-run validation

---

## Quick Reference

| Action | Command | Time |
|--------|---------|------|
| Start quote collection | `cp actual-quotes-template.csv actual-quotes.csv` | 1 min |
| Run analysis | `python3 calculate_accuracy.py` | 1 min |
| View report | `open output/ACCURACY-REPORT.md` | 5 min |

---

## Files You'll Work With

| File | What It Is | Your Action |
|------|------------|-------------|
| `workspace/actual-quotes-template.csv` | Empty template | Copy to actual-quotes.csv |
| `workspace/actual-quotes.csv` | Your data file | Fill in with real quotes |
| `output/QUOTE-COLLECTION-GUIDE.md` | Detailed instructions | Read before collecting |
| `output/TESTING-METHODOLOGY.md` | Full testing procedure | Read for rigorous validation |
| `output/ACCURACY-REPORT.md` | Results | Review after analysis |

---

## Multi-Session Workflow (Recommended)

For rigorous validation with 3 sessions:

```bash
# Session 1 (e.g., Tuesday 2PM)
cp actual-quotes-template.csv actual-quotes-session-1.csv
# Collect quotes, then:
mkdir -p ../output/sessions/session-1
cp actual-quotes-session-1.csv ../output/sessions/session-1/
cp actual-quotes-session-1.csv actual-quotes.csv
python3 calculate_accuracy.py
cp ../output/ACCURACY-REPORT.md ../output/sessions/session-1/

# Session 2 (e.g., Friday 6PM)
cp actual-quotes-template.csv actual-quotes-session-2.csv
# Collect quotes, then:
mkdir -p ../output/sessions/session-2
cp actual-quotes-session-2.csv ../output/sessions/session-2/
cp actual-quotes-session-2.csv actual-quotes.csv
python3 calculate_accuracy.py
cp ../output/ACCURACY-REPORT.md ../output/sessions/session-2/

# Session 3 (e.g., Saturday 11PM)
cp actual-quotes-template.csv actual-quotes-session-3.csv
# Collect quotes, then:
mkdir -p ../output/sessions/session-3
cp actual-quotes-session-3.csv ../output/sessions/session-3/
cp actual-quotes-session-3.csv actual-quotes.csv
python3 calculate_accuracy.py
cp ../output/ACCURACY-REPORT.md ../output/sessions/session-3/

# Aggregate all sessions
python3 aggregate_sessions.py
# Review: output/AGGREGATE-ACCURACY-REPORT.md
```

---

## When Complete

Check the report summary:

```
Overall Accuracy: XX% within 20%
Target: 85%+
Status: PASS / NEEDS IMPROVEMENT
```

If PASS: Algorithm is validated and ready for production.
If NEEDS IMPROVEMENT: See report recommendations for next steps.

---

**Total Estimated Time: 45-60 minutes**
