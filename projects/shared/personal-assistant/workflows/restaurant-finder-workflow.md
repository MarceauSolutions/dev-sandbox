# Workflow: Restaurant Finder

**Created:** 2026-01-19
**Purpose:** Find healthy, reasonably priced restaurants nearby using Google Places and AI ranking
**Output:** Ranked list of restaurants matching criteria (cuisine, budget, location, open now)

---

## Overview

This workflow uses Google Places API to search for restaurants near a location, then uses Claude AI to rank results based on preferences. Optimized for finding healthy, affordable options quickly.

---

## Use Cases

- Find healthy lunch options near office/home
- Locate affordable restaurants while traveling
- Filter by cuisine type (Asian, Mediterranean, Mexican, etc.)
- Find open restaurants right now
- Get ordering URLs for delivery/pickup
- Discover highly-rated local spots

---

## Prerequisites

Before running restaurant finder:
- ✅ `GOOGLE_PLACES_API_KEY` set in `.env`
- ✅ `ANTHROPIC_API_KEY` set in `.env` (optional, for AI ranking)
- ✅ Internet connection for API calls

---

## Input Parameters

| Parameter | Options | Default | Description |
|-----------|---------|---------|-------------|
| `--location` | Address string | Required* | "Naples, FL" or "3228 Sassafras Way, Pittsburgh PA 15201" |
| `--lat` | Float | Required* | Latitude coordinate (alternative to --location) |
| `--lng` | Float | Required* | Longitude coordinate (alternative to --location) |
| `--cuisine` | String | "healthy" | healthy, asian, mexican, italian, mediterranean, vegan, etc. |
| `--budget` | cheap/moderate/expensive | "moderate" | Price filter ($ / $$ / $$$) |
| `--radius` | Meters | 3000 | Search radius (3000m = ~2 miles) |
| `--open-now` | Flag | True | Only show currently open restaurants |
| `--open-url` | Flag | False | Open top result's ordering page in browser |
| `--json` | Flag | False | Output as JSON instead of formatted text |

*Either `--location` OR both `--lat` and `--lng` required

---

## Steps

### Step 1: Determine Search Location

**Objective:** Get coordinates for restaurant search

**Option A: Use Address**
```bash
python -m src.restaurant_finder --location "Naples, FL"
```
- Script geocodes address to lat/lng automatically
- Works with full addresses or city names

**Option B: Use Coordinates**
```bash
python -m src.restaurant_finder --lat 40.4774 --lng -79.9619
```
- Useful if you already have exact coordinates
- Faster (skips geocoding step)

**Tools:**
- Google Geocoding API (automatic via Places API)

**Output:**
```
📍 Geocoding: Naples, FL
   Found: 26.1420, -81.7948
```

**Verification:**
- ✅ Coordinates returned successfully
- ✅ Location is correct (check lat/lng makes sense)

---

### Step 2: Configure Search Criteria

**Objective:** Set cuisine type, budget, and radius preferences

**Cuisine Types:**
- `healthy` → "healthy salad bowl" (default)
- `asian` → Asian restaurants
- `mexican` → Mexican cuisine
- `italian` → Italian restaurants
- `mediterranean` → Mediterranean + healthy
- `vegan` → Vegan/vegetarian options
- `fast` → Fast casual dining
- Custom → Any keyword

**Budget Levels:**
- `cheap` → $ (price_level 1-2, adds "affordable" keyword)
- `moderate` → $$ (price_level 1-3, default)
- `expensive` → $$$ (price_level 1-4)

**Example Commands:**
```bash
# Healthy Mediterranean within 1 mile, open now
python -m src.restaurant_finder \
    --location "Naples, FL" \
    --cuisine mediterranean \
    --budget moderate \
    --radius 1600 \
    --open-now

# Cheap Asian food, 3km radius, include closed restaurants
python -m src.restaurant_finder \
    --location "Pittsburgh, PA" \
    --cuisine asian \
    --budget cheap \
    --radius 3000

# Vegan options near coordinates
python -m src.restaurant_finder \
    --lat 26.1420 --lng -81.7948 \
    --cuisine vegan \
    --open-now
```

---

### Step 3: Execute Search via Google Places API

**Objective:** Retrieve restaurant data from Google

**Actions:**
1. Script calls Google Places Nearby Search API with:
   - Location (lat/lng)
   - Radius in meters
   - Type: "restaurant"
   - Keyword: Built from cuisine + budget
   - Open now filter (if enabled)

2. API returns up to 10 results with:
   - Name, address, rating
   - Price level (1-4)
   - Cuisine types (tags)
   - Distance from search point
   - Open/closed status
   - Google Place ID

**Tools:**
- Google Places API Nearby Search endpoint
- `restaurant_finder.py` (handles API calls)

**Output:**
```
🔍 Searching for healthy restaurants within 3000m...
```

**Verification:**
- ✅ API call succeeds (status: OK or ZERO_RESULTS)
- ✅ Results returned (if ZERO_RESULTS, try expanding radius or changing cuisine)

---

### Step 4: Filter by Price Level

**Objective:** Apply budget constraints to results

**Actions:**
- Script automatically filters results based on `--budget` flag:
  - `cheap`: Keep only price_level 1-2 ($ and $$)
  - `moderate`: Keep price_level 1-3 ($, $$, $$$)
  - `expensive`: Keep all (1-4)

**Logic:**
```python
if budget == "cheap" and price_level > 2:
    skip_this_result
elif budget == "moderate" and price_level > 3:
    skip_this_result
```

**Verification:**
- ✅ No results exceed budget constraints
- ✅ If no results after filtering, try next budget level up

---

### Step 5: Calculate Distance and Sort

**Objective:** Rank results by distance and rating

**Actions:**
1. Calculate distance from search point to each restaurant:
   - Uses Haversine formula (accurate for Earth curvature)
   - Returns distance in meters

2. Initial sort by rating (highest first)

**Distance Display:**
- `< 1000m` → "850m"
- `>= 1000m` → "2.3km"

**Output:**
- Results sorted by rating (best first)
- Distance included for reference

---

### Step 6: AI Ranking (Optional but Recommended)

**Objective:** Use Claude to re-rank results based on preferences

**Actions:**
1. If `ANTHROPIC_API_KEY` is set, script automatically:
   - Sends top 10 results to Claude
   - Provides user preference string (e.g., "healthy and affordable")
   - Claude re-ranks based on actual menu fit, not just tags

2. Claude considers:
   - Cuisine type alignment with preference
   - Price level vs budget
   - Rating quality
   - Distance trade-off
   - Cuisine tag relevance

**Prompt Structure:**
```
Given these restaurants and the user's preference for "healthy and affordable",
rank them from best to worst match.

Restaurants:
1. Farmer's Table - $$ - 4.6⭐ - 850m - Types: healthy_food, salad, organic
2. Chipotle - $ - 4.2⭐ - 1.2km - Types: mexican, fast_food
...

Return ONLY the numbers in order of best match, comma-separated.
```

**Tools:**
- Claude 3.5 Haiku (fast and cheap)
- Anthropic Messages API

**Verification:**
- ✅ Claude returns ranking as comma-separated numbers
- ✅ All restaurants included in ranked list
- ✅ Ranking makes sense (healthy options ranked higher if preference is "healthy")

**Fallback:**
- If AI ranking fails → falls back to rating-based sort

---

### Step 7: Display Results

**Objective:** Show ranked restaurants in readable format

**Text Output (default):**
```
✅ Found 5 restaurants:

1. Farmer's Table
   $$ | 4.6⭐ | 850m | 🟢 Open
   123 Main St, Naples, FL

2. Chipotle Mexican Grill
   $ | 4.2⭐ | 1.2km | 🟢 Open
   456 Oak Ave, Naples, FL

3. Whole Foods Market Cafe
   $$ | 4.4⭐ | 1.5km | 🔴 Closed
   789 Pine Rd, Naples, FL
```

**JSON Output (with --json flag):**
```json
[
  {
    "name": "Farmer's Table",
    "address": "123 Main St, Naples, FL",
    "rating": 4.6,
    "price": "$$",
    "distance": "850m",
    "is_open": true,
    "place_id": "ChIJ..."
  }
]
```

**Actions:**
- Review top 3-5 results
- Check "is_open" status (🟢 Open / 🔴 Closed)
- Note distance for travel time estimate

---

### Step 8: Get Ordering URL (Optional)

**Objective:** Open restaurant's ordering page automatically

**Actions:**
1. Use `--open-url` flag to fetch ordering link:
   ```bash
   python -m src.restaurant_finder \
       --location "Naples, FL" \
       --cuisine healthy \
       --open-url
   ```

2. Script calls Google Place Details API for top result:
   - Fetches: website URL, Google Maps URL, phone number
   - Prefers website (often has ordering)
   - Falls back to Google Maps link

3. Opens URL in default browser automatically

**Tools:**
- Google Place Details API
- Python `webbrowser` module

**Output:**
```
🌐 Getting order URL for Farmer's Table...
   Opening: https://farmerstablenaples.com/order
```

**Fallback:**
- If no website → opens Google Maps link: `https://www.google.com/maps/place/?q=place_id:{place_id}`

**Verification:**
- ✅ Browser opens with ordering page
- ✅ If website doesn't work, Google Maps link always works

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `GOOGLE_PLACES_API_KEY not set` | Missing API key in .env | Add key to `/Users/williammarceaujr./dev-sandbox/.env` |
| `Could not geocode address` | Invalid address format | Use more specific address or try lat/lng instead |
| `No restaurants found` | Criteria too strict (radius too small, budget too low) | Increase `--radius` to 5000m or change budget to "moderate" |
| `ZERO_RESULTS` from API | No restaurants match filters in area | Remove `--open-now` filter or expand radius |
| API quota exceeded | Too many requests | Wait until quota resets (daily limit) or upgrade API plan |
| AI ranking failed | Missing ANTHROPIC_API_KEY | Add key or accept non-AI sorted results (still works) |
| Results don't match cuisine | Google's cuisine tags are broad | Use AI ranking to improve relevance or try different keyword |

---

## Success Criteria

**Search is successful when:**
- ✅ At least 3-5 restaurants returned
- ✅ All results match cuisine preference
- ✅ All results within budget constraints
- ✅ Distance shown for each result
- ✅ Open/closed status accurate (if --open-now used)
- ✅ Top result is actually a good match (use AI ranking for best results)
- ✅ Ordering URL opens successfully (if --open-url used)

---

## Example Use Cases

### Use Case 1: Quick Lunch Near Home
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/personal-assistant
python -m src.restaurant_finder \
    --location "Naples, FL" \
    --cuisine healthy \
    --budget cheap \
    --radius 2000 \
    --open-now \
    --open-url
```
**Result:** Opens ordering page for nearest cheap healthy restaurant that's open now

---

### Use Case 2: Exploring New City
```bash
python -m src.restaurant_finder \
    --location "Pittsburgh, PA" \
    --cuisine asian \
    --budget moderate \
    --radius 5000
```
**Result:** Lists top 5 Asian restaurants within 3 miles, ranked by AI for quality

---

### Use Case 3: JSON Output for Integration
```bash
python -m src.restaurant_finder \
    --location "Miami, FL" \
    --cuisine mediterranean \
    --json > restaurants.json
```
**Result:** Saves JSON data for use in other scripts or apps

---

### Use Case 4: Coordinates from GPS
```bash
# Using exact coordinates (e.g., from phone GPS)
python -m src.restaurant_finder \
    --lat 26.1420 --lng -81.7948 \
    --cuisine vegan \
    --open-now
```
**Result:** Finds vegan restaurants near exact coordinates

---

## Data Sources

**Google Places API:**
- Restaurant name, address, location
- Rating (1-5 stars)
- Price level (1-4, displayed as $-$$$$)
- Cuisine types/tags
- Open hours and current status
- Place ID (for details lookup)
- Distance calculation (Haversine formula)

**Google Place Details API:**
- Website URL (for ordering)
- Phone number
- Full address
- Reviews (not used in this workflow)

**Claude AI (optional):**
- Intelligent ranking based on preferences
- Understands nuance (e.g., "healthy" means salads not just vegetarian tag)

---

## Integration with Other Workflows

**Morning Digest:**
- Can be automated to suggest lunch options in morning email
- Integration: `digest_aggregator.py` could call restaurant finder for location

**Calendar Integration:**
- Find restaurants near upcoming meeting location
- Automatically suggest options before lunch meetings

**Slack/Discord Bot:**
- Respond to "where should we eat?" with top 3 options
- Integration: Bot calls this script and returns formatted list

---

## Related Workflows

- `digest-aggregator-workflow.md` - Morning digest could include restaurant suggestions
- `daily-routine-sop.md` - Use as part of lunch planning routine

---

## API Costs

**Google Places API Pricing (as of 2026):**
- Nearby Search: $32 per 1,000 requests
- Place Details: $17 per 1,000 requests
- Geocoding: $5 per 1,000 requests

**Typical Usage:**
- Single search: 1 Nearby Search + 1 Geocoding = ~$0.037
- With --open-url: +1 Place Details = ~$0.054 total

**Anthropic API Pricing:**
- Claude 3.5 Haiku: ~$0.0001 per ranking request (negligible)

**Monthly Estimate:**
- 1 search/day for 30 days = ~$1.11/month
- Reasonable for personal use

---

## Version History

- **v1.0 (2026-01-19):** Initial workflow created for personal assistant project
