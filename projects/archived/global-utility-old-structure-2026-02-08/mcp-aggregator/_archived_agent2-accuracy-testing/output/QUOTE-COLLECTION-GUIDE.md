# Quote Collection Guide

**Time Required:** 30-60 minutes
**Difficulty:** Easy (just need Uber/Lyft apps)

---

## Overview

To validate our price estimation algorithm, we need to compare our estimates against actual Uber and Lyft quotes. This guide walks you through collecting real quotes for the 30 test routes.

---

## Prerequisites

- [ ] Uber app installed on your phone
- [ ] Lyft app installed on your phone
- [ ] Both apps logged in with valid accounts
- [ ] Access to `actual-quotes-template.csv`

---

## Best Time to Collect Quotes

For consistent data (minimal surge/primetime), collect quotes during:

| Day | Time | Why |
|-----|------|-----|
| Tuesday-Thursday | 2:00 PM - 4:00 PM | Lowest surge probability |
| Sunday | 10:00 AM - 2:00 PM | Low demand period |

**Avoid:**
- Friday/Saturday nights (high surge)
- Morning rush (7-9 AM weekdays)
- Evening rush (5-7 PM weekdays)
- Late night (10 PM - 2 AM)
- Major events in the city

---

## Step-by-Step Process

### 1. Set Up Your Workspace

```bash
# Navigate to the workspace
cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent2-accuracy-testing/workspace

# Copy template to create working file
cp actual-quotes-template.csv actual-quotes.csv
```

### 2. Open the Routes Reference

Open `test-routes.csv` to see the exact coordinates and addresses:

```bash
open test-routes.csv
```

### 3. For Each Route (1-30):

#### Step A: Open Uber App
1. Tap "Where to?"
2. Enter the **pickup address** from the route
3. Enter the **dropoff address** from the route
4. Wait for prices to load
5. Record the **UberX price** (not XL, Black, etc.)

#### Step B: Open Lyft App
1. Tap "Where are you going?"
2. Enter the **pickup address**
3. Enter the **dropoff address**
4. Wait for prices to load
5. Record the **Lyft price** (standard Lyft, not XL, Lux, etc.)

#### Step C: Record in CSV
For each route, fill in:
- `actual_uber`: The Uber price shown (e.g., 24.50)
- `actual_lyft`: The Lyft price shown (e.g., 23.00)
- `surge_active`: "yes" if either app shows surge/primetime, "no" otherwise
- `timestamp`: Current time (e.g., 2026-01-12 14:30)
- `notes`: Any observations (optional)

---

## Route Reference (Quick Version)

| Route | City | From | To |
|-------|------|------|-----|
| 1 | san_francisco | Union Square | Mission District |
| 2 | san_francisco | SFO Airport | SOMA |
| 3 | san_francisco | Union Square | SFO Airport |
| 4 | new_york | Times Square | Wall Street |
| 5 | new_york | JFK Airport | Midtown |
| 6 | new_york | Times Square | JFK Airport |
| 7 | los_angeles | LAX Airport | Koreatown |
| 8 | los_angeles | Hollywood | Venice Beach |
| 9 | los_angeles | LAX Airport | Hollywood |
| 10 | chicago | ORD Airport | Wicker Park |
| 11 | chicago | The Loop | Lincoln Park |
| 12 | chicago | ORD Airport | The Loop |
| 13 | boston | Logan Airport | Fenway Park |
| 14 | boston | Downtown Crossing | Back Bay |
| 15 | boston | Logan Airport | Downtown Crossing |
| 16 | seattle | SeaTac Airport | Fremont |
| 17 | seattle | Pike Place Market | University District |
| 18 | seattle | SeaTac Airport | Pike Place Market |
| 19 | austin | Austin Airport | East Austin |
| 20 | austin | Downtown Austin | Zilker Park |
| 21 | austin | Austin Airport | Downtown Austin |
| 22 | miami | MIA Airport | Wynwood |
| 23 | miami | South Beach | Coral Gables |
| 24 | miami | MIA Airport | South Beach |
| 25 | denver | DEN Airport | RiNo |
| 26 | denver | Downtown Denver | Cherry Creek |
| 27 | denver | DEN Airport | Downtown Denver |
| 28 | washington_dc | DCA Airport | Dupont Circle |
| 29 | washington_dc | Capitol Hill | U Street |
| 30 | washington_dc | DCA Airport | Capitol Hill |

---

## Tips for Accuracy

1. **Be Consistent**
   - Collect all 30 routes in one sitting if possible
   - This ensures consistent surge conditions across all routes

2. **Use Exact Addresses**
   - The apps may suggest slightly different locations
   - Use the landmark names from the template for consistency

3. **Note Surge Conditions**
   - If you see "Surge pricing" (Uber) or "Primetime" (Lyft), mark `surge_active` as "yes"
   - These routes may have higher-than-normal error rates

4. **Screenshots (Optional)**
   - Take screenshots for documentation
   - Save as: `screenshots/route_XX_uber.png` and `route_XX_lyft.png`

5. **Handle Errors**
   - If a route isn't available (service area issue), enter "N/A" and note it
   - If price shows a range ($20-25), use the midpoint ($22.50)

---

## Example Entry

```csv
route_id,city,pickup_address,dropoff_address,actual_uber,actual_lyft,surge_active,timestamp,notes
1,san_francisco,Union Square,Mission District,14.50,13.25,no,2026-01-12 14:32,Clear weather normal traffic
```

---

## After Collection

Once you've collected all 30 routes:

```bash
# Run the accuracy analysis
cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent2-accuracy-testing/workspace
python3 calculate_accuracy.py
```

This will:
1. Compare your actual quotes against our estimates
2. Generate `ACCURACY-REPORT.md` with full analysis
3. Show overall accuracy percentage

---

## Expected Results

- **Target Accuracy:** 85%+ of estimates within 20% of actual price
- **Recommendation Accuracy:** 80%+ correct "which is cheaper" predictions

If accuracy is below target, the report will identify:
- Which cities have the highest error rates
- Which distance categories (short/medium/long) need calibration
- Specific routes with large discrepancies

---

## Questions?

If you encounter issues:
1. Note the problem in the `notes` column
2. Complete as many routes as possible
3. Run the analysis on partial data (it handles missing entries)

---

**Time Estimate:** 1-2 minutes per route = 30-60 minutes total
