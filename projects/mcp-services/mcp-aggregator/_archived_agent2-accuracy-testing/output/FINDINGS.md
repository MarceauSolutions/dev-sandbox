# Agent 2 Findings: Accuracy Validation Infrastructure

**Agent:** Agent 2 - Accuracy Testing
**Mode:** Autonomous
**Date:** 2026-01-12

---

## Summary

Successfully built complete accuracy validation infrastructure for the rideshare price comparison algorithm. All automated components are complete; human quote collection is the only remaining step.

---

## What Was Built

### 1. Test Route Generator (`workspace/generate_test_routes.py`)

**Purpose:** Generate diverse test routes across all supported cities

**Design Decisions:**
- 30 routes total (3 per city, 10 cities)
- Balanced distribution: 10 short, 10 medium, 10 long distances
- Uses real landmarks for reproducible testing
- Time-of-day categories for surge testing potential

**Output:** `workspace/test-routes.csv`

### 2. Algorithm Runner (`workspace/run_algorithm.py`)

**Purpose:** Run our comparison algorithm on all test routes

**Implementation:**
- Imports directly from `src/mcps/rideshare/comparison.py`
- Generates estimates for both Uber and Lyft
- Records surge multipliers, distances, durations
- Handles errors gracefully

**Output:** `workspace/estimated-quotes.csv`

### 3. Quote Collection Template (`workspace/actual-quotes-template.csv`)

**Purpose:** Pre-formatted CSV for human to fill in

**Design:**
- Pre-filled with route IDs and addresses
- Columns: actual_uber, actual_lyft, surge_active, timestamp, notes
- Human copies to `actual-quotes.csv` and fills in

### 4. Accuracy Calculator (`workspace/calculate_accuracy.py`)

**Purpose:** Compare estimates vs actuals, generate metrics

**Features:**
- Calculates absolute and percentage errors
- Tracks "within 20%" accuracy (our target metric)
- Analyzes by city and distance category
- Generates comprehensive markdown report
- Exports raw metrics to CSV

**Outputs:**
- `output/ACCURACY-REPORT.md`
- `workspace/accuracy-metrics.csv`

---

## Algorithm Analysis (Pre-Validation)

Based on running the algorithm on 30 test routes:

### Estimate Distribution

| Service | Min | Max | Average |
|---------|-----|-----|---------|
| Uber | $7.16 | $57.76 | $24.48 |
| Lyft | $6.63 | $58.16 | $23.84 |

### Initial Observations

1. **Lyft Generally Cheaper:** Lyft recommended 86.7% of routes (26/30)
2. **Average Savings:** $0.70 per ride when choosing cheapest
3. **Max Savings:** $1.85 on a single ride

### Potential Concerns

1. **New York High Prices:** NYC estimates ($57-58) are high - may need validation
2. **Lyft Bias:** Strong Lyft recommendation rate may indicate rate card calibration needed
3. **Surge Not Active:** All estimates assumed 1.0x surge (off-peak testing)

---

## Technical Notes

### Path Configuration

The algorithm runner uses absolute paths:
```python
MCP_SRC_PATH = '/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/src'
```

This ensures the script works from any directory.

### Error Handling

The `run_algorithm.py` script handles:
- Missing rate cards (logs ERROR, continues)
- Invalid coordinates (logs ERROR, continues)
- Route-level failures (doesn't abort entire run)

### CSV Format

All CSVs use standard format:
- Header row included
- Comma-separated
- No quotes around values unless necessary
- Numbers stored as floats (e.g., 24.50, not $24.50)

---

## Recommendations

### For Human Quote Collection

1. **Timing:** Collect all 30 routes in one session (2-4 PM weekday)
2. **Consistency:** Use exact landmark names from template
3. **Surge:** Note if surge/primetime is active
4. **Screenshots:** Optional but helpful for verification

### For Algorithm Improvement (Post-Validation)

If accuracy < 85%:

1. **Rate Cards:** Check cities with highest error rates
2. **Surge Model:** Current model is simple time-of-day heuristics
3. **Distance Calculation:** Haversine is straight-line; actual routes are longer
4. **Duration Estimation:** City-specific speeds may need tuning

### For Production

1. **Monthly Rate Card Updates:** Uber/Lyft change rates periodically
2. **Surge Prediction:** Consider historical surge data integration
3. **City Expansion:** Add more cities as rate cards become available

---

## Files Created

| File | Location | Purpose |
|------|----------|---------|
| generate_test_routes.py | workspace/ | Route generation |
| test-routes.csv | workspace/ | 30 test routes |
| run_algorithm.py | workspace/ | Estimate generation |
| estimated-quotes.csv | workspace/ | Algorithm predictions |
| actual-quotes-template.csv | workspace/ | Human input template |
| calculate_accuracy.py | workspace/ | Accuracy analysis |
| QUOTE-COLLECTION-GUIDE.md | output/ | Human instructions |
| ANALYSIS-INSTRUCTIONS.md | output/ | How to run analysis |
| HUMAN-TODO.md | output/ | Required human actions |
| FINDINGS.md | output/ | This file |

---

## Time Spent

- Route generator: 15 minutes
- Algorithm runner: 20 minutes
- Analysis tool: 30 minutes
- Documentation: 25 minutes
- **Total automated work:** ~90 minutes

---

## Next Steps

1. Human collects quotes (30-45 minutes)
2. Human runs analysis (5 minutes)
3. Review accuracy report
4. Iterate if needed (update rate cards, re-validate)
5. Production deployment when accuracy >= 85%

---

*Generated by Agent 2 - Accuracy Testing*
