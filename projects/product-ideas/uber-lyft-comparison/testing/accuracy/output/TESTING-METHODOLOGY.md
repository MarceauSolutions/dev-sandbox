# Real-World Testing Methodology

**Purpose:** Define a rigorous, repeatable procedure for validating algorithm accuracy against actual Uber/Lyft quotes.

---

## Executive Summary

| Parameter | Recommendation |
|-----------|----------------|
| Routes per test | 30 |
| Test sessions | 3 minimum (different conditions) |
| Refresh interval | Weekly during validation phase |
| Samples per route | 3 (across different sessions) |
| Total data points | 180 (30 routes × 3 sessions × 2 services) |

---

## Testing Schedule

### Phase 1: Initial Validation (Week 1)

Collect 3 complete datasets under different conditions:

| Session | Day | Time | Condition | Routes |
|---------|-----|------|-----------|--------|
| Session 1 | Tuesday | 2:00 PM | Off-peak baseline | 30 |
| Session 2 | Friday | 6:00 PM | Evening rush | 30 |
| Session 3 | Saturday | 11:00 PM | Late night/surge | 30 |

**Why these times:**
- **Off-peak (Tue 2PM):** Establishes baseline accuracy without surge
- **Rush hour (Fri 6PM):** Tests surge prediction accuracy
- **Late night (Sat 11PM):** Tests high-surge prediction accuracy

### Phase 2: Ongoing Monitoring (Post-Launch)

| Frequency | What to Test | Why |
|-----------|--------------|-----|
| Weekly | 10 random routes | Detect rate card changes |
| Monthly | Full 30 routes | Comprehensive accuracy check |
| After rate changes | Full 30 routes | Validate updated rate cards |

---

## Sample Size Justification

### Statistical Basis

For 85% accuracy target with 95% confidence:

```
Minimum sample size = (Z² × p × (1-p)) / E²
Where:
  Z = 1.96 (95% confidence)
  p = 0.85 (expected accuracy)
  E = 0.10 (±10% margin of error)

Minimum = (1.96² × 0.85 × 0.15) / 0.10² = 49 samples
```

**Our approach:** 90 samples per service (30 routes × 3 sessions) exceeds minimum.

### Per-Route Sampling

| Samples per Route | Purpose |
|-------------------|---------|
| 1 | Single point (unreliable) |
| 2 | Can identify outliers |
| **3** | Establishes pattern, identifies variance |
| 5+ | Diminishing returns for validation |

**Recommendation:** 3 samples per route is optimal for validation.

---

## Detailed Testing Procedure

### Before Each Session

1. **Check conditions:**
   ```
   - No major events in test cities
   - No severe weather warnings
   - Apps updated to latest version
   ```

2. **Prepare workspace:**
   ```bash
   cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent2-accuracy-testing/workspace

   # Create session-specific file
   cp actual-quotes-template.csv actual-quotes-session-X.csv
   ```

3. **Record session metadata:**
   - Date and time
   - Weather conditions
   - Any known events

### During Each Session

**For each of the 30 routes:**

1. **Open Uber app**
   - Enter pickup address
   - Enter dropoff address
   - Wait for prices to fully load (5-10 seconds)
   - Record UberX price
   - Note if surge is active and multiplier

2. **Open Lyft app**
   - Enter same pickup address
   - Enter same dropoff address
   - Wait for prices to fully load
   - Record Lyft price
   - Note if Primetime is active and percentage

3. **Record in CSV:**
   ```csv
   route_id,actual_uber,actual_lyft,uber_surge,lyft_primetime,timestamp
   1,24.50,22.75,1.0,0%,2026-01-14 14:32
   ```

4. **Timing:**
   - Complete all 30 routes within 60-90 minutes
   - Minimizes time-based price variation within session

### After Each Session

1. **Validate data:**
   - Check for missing values
   - Verify prices are reasonable
   - Note any anomalies

2. **Run analysis:**
   ```bash
   python3 calculate_accuracy.py
   ```

3. **Archive results:**
   ```bash
   mkdir -p ../output/sessions/session-X
   cp actual-quotes-session-X.csv ../output/sessions/session-X/
   cp ../output/ACCURACY-REPORT.md ../output/sessions/session-X/
   ```

---

## Data Refresh Schedule

### During Validation Phase (Weeks 1-2)

| When | What | Action |
|------|------|--------|
| Day 1 | Session 1 | Collect off-peak data |
| Day 3 | Session 2 | Collect rush hour data |
| Day 5 | Session 3 | Collect late night data |
| Day 7 | Analysis | Aggregate results, identify issues |
| Day 8-14 | Fixes | Update rate cards if needed |
| Day 14 | Retest | Verify fixes with new session |

### Post-Launch Monitoring

| Frequency | Routes | Time Required | Purpose |
|-----------|--------|---------------|---------|
| Weekly | 10 random | 20-30 min | Drift detection |
| Monthly | 30 full | 60-90 min | Full validation |
| Quarterly | 30 × 3 sessions | 3-4 hours | Comprehensive audit |

### Triggering Full Retest

Immediately run full 30-route test when:

- [ ] Uber or Lyft announces rate changes
- [ ] Weekly spot-check shows >25% error on any route
- [ ] User reports consistently wrong estimates
- [ ] New city added to coverage

---

## Handling Variance

### Expected Variance Sources

| Source | Impact | Mitigation |
|--------|--------|------------|
| Surge pricing | High | Test multiple times, record surge |
| Route variation | Low | Use consistent landmark names |
| Time of day | Medium | Test same routes at different times |
| App updates | Low | Note app version |
| Weather | Medium | Record conditions |

### Calculating Accuracy with Variance

For routes with multiple samples:

```python
# Use median (not mean) to reduce outlier impact
route_accuracy = median([sample1_error, sample2_error, sample3_error])

# Flag high-variance routes
variance = max(samples) - min(samples)
if variance > 5.00:  # $5 variance threshold
    flag_for_review(route)
```

### Acceptable Variance Thresholds

| Condition | Max Acceptable Variance |
|-----------|------------------------|
| Off-peak | ±$2.00 or ±10% |
| Rush hour | ±$5.00 or ±15% |
| Late night/surge | ±$8.00 or ±20% |

---

## File Naming Convention

```
actual-quotes-YYYY-MM-DD-condition.csv

Examples:
actual-quotes-2026-01-14-offpeak.csv
actual-quotes-2026-01-17-rush.csv
actual-quotes-2026-01-18-latenight.csv
```

---

## Aggregating Multiple Sessions

### Combined Analysis Script

After collecting 3 sessions, combine for statistical analysis:

```bash
# Create combined dataset
python3 aggregate_sessions.py \
  --sessions session-1 session-2 session-3 \
  --output combined-analysis.csv
```

### Metrics to Calculate

| Metric | Formula | Target |
|--------|---------|--------|
| Overall accuracy | % within 20% across all samples | ≥85% |
| Per-condition accuracy | % within 20% for each condition | ≥80% |
| Recommendation accuracy | % correct cheaper service | ≥85% |
| Consistency score | % routes with low variance | ≥90% |

---

## Decision Matrix

### Based on Results

| Overall Accuracy | Recommendation Accuracy | Action |
|------------------|------------------------|--------|
| ≥85% | ≥85% | PASS - Ready for production |
| ≥85% | 75-84% | REVIEW - Check recommendation logic |
| 75-84% | Any | IMPROVE - Update rate cards |
| <75% | Any | FAIL - Major recalibration needed |

### Per-City Actions

| City Accuracy | Action |
|---------------|--------|
| ≥85% | No action needed |
| 75-84% | Review rate cards, retest |
| <75% | Update rate cards immediately |
| <60% | Consider removing city until fixed |

---

## Automation Opportunities

### What Can Be Automated

| Task | Automation Level | Notes |
|------|------------------|-------|
| Generate test routes | Fully automated | `generate_test_routes.py` |
| Run algorithm | Fully automated | `run_algorithm.py` |
| Calculate accuracy | Fully automated | `calculate_accuracy.py` |
| Aggregate sessions | Can be automated | Create `aggregate_sessions.py` |
| Generate reports | Fully automated | Built into analysis |

### What Requires Human

| Task | Why Human Needed |
|------|------------------|
| Collect actual quotes | Requires mobile apps |
| Interpret anomalies | Judgment calls |
| Update rate cards | Requires research |
| Final go/no-go decision | Business decision |

---

## Checklist: Complete Validation

### Pre-Validation
- [ ] Test routes generated (30 routes)
- [ ] Algorithm estimates generated
- [ ] Apps installed and logged in
- [ ] Schedule 3 test sessions

### Session 1: Off-Peak
- [ ] Date/time recorded
- [ ] All 30 routes collected
- [ ] Data validated
- [ ] Analysis run

### Session 2: Rush Hour
- [ ] Date/time recorded
- [ ] All 30 routes collected
- [ ] Data validated
- [ ] Analysis run

### Session 3: Late Night
- [ ] Date/time recorded
- [ ] All 30 routes collected
- [ ] Data validated
- [ ] Analysis run

### Post-Collection
- [ ] All sessions aggregated
- [ ] Combined accuracy calculated
- [ ] Problem areas identified
- [ ] Rate cards updated (if needed)
- [ ] Retest completed (if fixes made)
- [ ] Final accuracy ≥85%
- [ ] Documentation complete

---

## Summary

| Question | Answer |
|----------|--------|
| How many routes? | 30 per session |
| How many sessions? | 3 minimum (different conditions) |
| How often to refresh? | Weekly spot-check, monthly full test |
| Total samples needed? | 90 per service (180 total) |
| Time investment? | ~4-5 hours total for initial validation |
| Ongoing maintenance? | ~2 hours/month |

---

*This methodology ensures statistically valid accuracy measurements while remaining practical for manual data collection.*
