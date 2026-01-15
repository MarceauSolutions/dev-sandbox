# Analysis Instructions

How to run the accuracy analysis after collecting quotes.

---

## Prerequisites

Before running the analysis, ensure:

- [ ] `actual-quotes.csv` exists in the workspace folder
- [ ] At least some routes have `actual_uber` and `actual_lyft` filled in
- [ ] Python 3 is available

---

## Quick Start

```bash
# Navigate to workspace
cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent2-accuracy-testing/workspace

# Run analysis
python3 calculate_accuracy.py
```

---

## Expected Output

The script will:

1. **Load Data**
   - Read `estimated-quotes.csv` (our predictions)
   - Read `actual-quotes.csv` (your collected quotes)

2. **Calculate Metrics**
   - Error percentage for each route (Uber and Lyft separately)
   - Recommendation accuracy (did we pick the right service?)
   - Analysis by city and distance category

3. **Generate Reports**
   - `output/ACCURACY-REPORT.md` - Full analysis report
   - `workspace/accuracy-metrics.csv` - Raw metrics for further analysis

4. **Print Summary**
   - Overall accuracy percentage
   - PASS/FAIL status against 85% target

---

## Understanding the Report

### Key Metrics

| Metric | Target | What It Means |
|--------|--------|---------------|
| Uber within 20% | 85% | % of Uber estimates within 20% of actual |
| Lyft within 20% | 85% | % of Lyft estimates within 20% of actual |
| Recommendation Accuracy | 80% | % of times we correctly identified cheaper option |
| Overall Accuracy | 85% | Combined accuracy across all estimates |

### Error Calculation

```
Error % = |Estimated - Actual| / Actual × 100

Example:
  Estimated: $25.00
  Actual:    $22.00
  Error:     $3.00 / $22.00 = 13.6%
```

---

## Partial Data

The analysis handles partial data:

- Routes without actual quotes are skipped
- You can run analysis with 10 routes, then add more and re-run
- Each run regenerates the full report

---

## Troubleshooting

### "actual-quotes.csv not found"

```bash
# Copy template to create the file
cp actual-quotes-template.csv actual-quotes.csv
# Then fill in the data
```

### "No valid comparison data found"

- Open `actual-quotes.csv`
- Ensure `actual_uber` and `actual_lyft` columns have numeric values
- Check for typos (must be numbers like 24.50, not "$24.50")

### Low Accuracy Results

If accuracy is below 85%:

1. Check `ACCURACY-REPORT.md` for problem areas
2. Look at "Analysis by City" - some cities may need rate card updates
3. Look at "Analysis by Distance" - algorithm may need tuning for certain trip lengths
4. Review high-error individual routes for patterns

---

## Re-Running Analysis

You can re-run the analysis at any time:

```bash
python3 calculate_accuracy.py
```

Each run:
- Overwrites previous reports
- Uses latest data from `actual-quotes.csv`
- Recalculates all metrics

---

## Next Steps After Analysis

### If Accuracy >= 85%
1. Document the validation results
2. Proceed to production deployment
3. Set up monthly rate card updates

### If Accuracy < 85%
1. Identify problem cities/categories from report
2. Update rate cards for high-error cities
3. Adjust surge prediction model if needed
4. Re-collect quotes and re-run analysis

---

## Files Reference

| File | Location | Purpose |
|------|----------|---------|
| estimated-quotes.csv | workspace/ | Our algorithm's predictions |
| actual-quotes-template.csv | workspace/ | Template for human input |
| actual-quotes.csv | workspace/ | Your collected data |
| calculate_accuracy.py | workspace/ | Analysis script |
| ACCURACY-REPORT.md | output/ | Generated report |
| accuracy-metrics.csv | workspace/ | Raw metrics data |

---

## Contact

For questions about the algorithm or analysis methodology, see:
- `src/mcps/rideshare/comparison.py` - Main algorithm
- `src/mcps/rideshare/rate_cards.py` - Pricing data
