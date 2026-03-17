# Education Scenarios: Revenue Analytics

*Tool: `get_revenue_report`*
*Module: revenue_analytics.py*
*Category: 2 (Requires Google Sheets API credentials)*

## Persona

**Marcus J., Fitness Influencer Business Owner**
- Multiple revenue streams (sponsorships, courses, affiliate)
- Tracks finances in Google Sheets
- Needs monthly/quarterly reports
- Wants to understand profit margins

---

## Prerequisites

### Required: Google Sheets API Credentials

1. **Create Google Cloud Project**
   - Go to: https://console.cloud.google.com
   - Create new project
   - Enable Google Sheets API

2. **Create Service Account**
   - Go to: IAM & Admin → Service Accounts
   - Create service account
   - Download JSON credentials

3. **Configure Credentials**
   ```bash
   # Save credentials file
   cp path/to/credentials.json ~/.google/sheets_credentials.json

   # Or set environment variable
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
   ```

4. **Share Spreadsheet**
   - Share your Google Sheet with the service account email
   - Grant "Viewer" or "Editor" access

---

## Scenario 1: Monthly Revenue Report

**Goal:** Generate report for current month

**Input:**
```python
{
    "sheet_id": "your-google-sheet-id",
    "month": "2026-01"
}
```

**Expected Output:**
```json
{
    "success": true,
    "report": {
        "period": "2026-01",
        "revenue": {
            "total": 15000,
            "by_source": {
                "sponsorships": 8000,
                "courses": 5000,
                "affiliate": 2000
            }
        },
        "expenses": {
            "total": 3000,
            "by_category": {
                "equipment": 1000,
                "software": 500,
                "marketing": 1500
            }
        },
        "profit": 12000,
        "margin": "80%"
    }
}
```

**Test Command (Dry Run):**
```bash
python -c "
from src.revenue_analytics import RevenueAnalytics

# Initialize without sheet_id to test import
analytics = RevenueAnalytics(sheet_id='test')
print('✅ RevenueAnalytics imported')

# Check authentication
service = analytics.authenticate()
if service:
    print('✅ Google Sheets authentication successful')
else:
    print('⚠️ Authentication failed - check credentials')
    print('   See: https://console.cloud.google.com')
"
```

**Pass Criteria:**
- [ ] Module imports successfully
- [ ] Authentication method exists
- [ ] With valid credentials: returns structured report

---

## Scenario 2: Year-to-Date Summary

**Goal:** Get cumulative yearly data

**Input:**
```python
{
    "sheet_id": "your-google-sheet-id",
    "month": None  # All available data
}
```

**Expected Output:**
- Annual totals
- Monthly breakdown
- Growth trends

**Pass Criteria:**
- [ ] Aggregates multiple months
- [ ] Shows growth/decline trends

---

## Scenario 3: Revenue by Source Analysis

**Goal:** Deep dive into revenue sources

**Expected Insight:**
- Which revenue stream is most profitable?
- Month-over-month changes per source
- Recommendations for optimization

**Pass Criteria:**
- [ ] Breaks down by revenue source
- [ ] Calculates percentages
- [ ] Identifies top performers

---

## Scenario 4: Expense Tracking

**Goal:** Analyze expense categories

**Expected Output:**
- Expense breakdown by category
- Percentage of revenue
- Comparison to previous periods

**Pass Criteria:**
- [ ] Categorizes expenses correctly
- [ ] Calculates expense ratios

---

## Edge Cases

### Edge Case 1: Missing Credentials

**Test Command:**
```bash
python -c "
import os
# Check for credentials
cred_file = os.path.expanduser('~/.google/sheets_credentials.json')
env_cred = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

print('Credentials check:')
print(f'  File exists (~/.google/): {os.path.exists(cred_file)}')
print(f'  Env var set: {bool(env_cred)}')

from src.revenue_analytics import RevenueAnalytics
analytics = RevenueAnalytics(sheet_id='test')
service = analytics.authenticate()
print(f'  Authentication: {\"Success\" if service else \"Failed\"}')"
```

**Pass Criteria:**
- [ ] Clear error message if credentials missing
- [ ] No crash

---

### Edge Case 2: Invalid Sheet ID

**Input:**
```python
{
    "sheet_id": "invalid-sheet-id-12345"
}
```

**Pass Criteria:**
- [ ] Handles invalid sheet ID gracefully
- [ ] Returns helpful error message

---

### Edge Case 3: Empty Spreadsheet

**Input:**
```python
{
    "sheet_id": "empty-spreadsheet-id"
}
```

**Expected Output:**
- Report with zero values
- Or message indicating no data

**Pass Criteria:**
- [ ] Does not crash on empty data
- [ ] Returns meaningful response

---

### Edge Case 4: Future Month Request

**Input:**
```python
{
    "sheet_id": "valid-id",
    "month": "2030-12"  # Future date
}
```

**Pass Criteria:**
- [ ] Handles future date gracefully
- [ ] Returns empty or error

---

## Batch Test Script (Module Verification)

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer

python -c "
import os
print('Testing Revenue Analytics...')
print('=' * 50)

# Test 1: Import
try:
    from src.revenue_analytics import RevenueAnalytics
    print('✅ RevenueAnalytics imported')
except Exception as e:
    print(f'❌ Import failed: {e}')
    exit(1)

# Test 2: Check credentials
cred_locations = [
    os.path.expanduser('~/.google/sheets_credentials.json'),
    os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
]

creds_found = any(os.path.exists(p) for p in cred_locations if p)
if creds_found:
    print('✅ Credentials file found')
else:
    print('⚠️ No credentials found')
    print('   Expected at: ~/.google/sheets_credentials.json')
    print('   Or set: GOOGLE_APPLICATION_CREDENTIALS env var')

# Test 3: Initialize
try:
    analytics = RevenueAnalytics(sheet_id='test')
    print('✅ RevenueAnalytics initialized')
except Exception as e:
    print(f'❌ Initialization failed: {e}')

# Test 4: Authentication test
try:
    service = analytics.authenticate()
    if service:
        print('✅ Google Sheets API authentication successful')
    else:
        print('⚠️ Authentication returned None (credentials may be invalid)')
except Exception as e:
    print(f'❌ Authentication error: {e}')

# Test 5: Check methods
methods = ['authenticate', 'generate_report', 'get_revenue_data', 'get_expense_data']
for method in methods:
    has_method = hasattr(analytics, method)
    status = '✅' if has_method else '⚠️'
    print(f'{status} Method: {method}')

print('=' * 50)
print('Full testing requires:')
print('1. Valid Google Sheets API credentials')
print('2. A spreadsheet with financial data')
print('3. Sheet shared with service account')
"
```

---

## Google Sheets Template

For testing, create a Google Sheet with this structure:

### Sheet: "Revenue"
| Date | Source | Amount |
|------|--------|--------|
| 2026-01-01 | Sponsorship | 5000 |
| 2026-01-15 | Course Sales | 3000 |
| 2026-01-20 | Affiliate | 1000 |

### Sheet: "Expenses"
| Date | Category | Amount |
|------|----------|--------|
| 2026-01-05 | Equipment | 500 |
| 2026-01-10 | Software | 200 |
| 2026-01-15 | Marketing | 800 |

---

## Success Criteria Summary

| Scenario | Prerequisites | Key Check |
|----------|---------------|-----------|
| Monthly report | Sheet + creds | Structured JSON |
| YTD summary | Sheet + creds | Aggregated data |
| Revenue by source | Sheet + creds | Breakdown correct |
| Expense tracking | Sheet + creds | Categories work |
| Edge: No creds | None | Error handled |
| Edge: Invalid sheet | Creds only | Error message |
| Edge: Empty data | Sheet + creds | No crash |
| Edge: Future date | Sheet + creds | Graceful handling |

---

## Setup Instructions

### Step 1: Google Cloud Console
```
1. Go to: https://console.cloud.google.com
2. Create new project (or select existing)
3. Enable "Google Sheets API"
4. Go to APIs & Services → Credentials
5. Create Service Account
6. Download JSON key file
```

### Step 2: Configure Credentials
```bash
# Create directory
mkdir -p ~/.google

# Move credentials
mv ~/Downloads/your-credentials.json ~/.google/sheets_credentials.json

# Set permissions
chmod 600 ~/.google/sheets_credentials.json
```

### Step 3: Share Your Spreadsheet
```
1. Open your Google Sheet
2. Click "Share"
3. Add service account email (from JSON file)
4. Grant "Viewer" access
5. Copy Sheet ID from URL
```

### Step 4: Test Connection
```bash
python -c "
from src.revenue_analytics import RevenueAnalytics
analytics = RevenueAnalytics(sheet_id='YOUR_SHEET_ID')
service = analytics.authenticate()
print('Connected!' if service else 'Failed')
"
```
