# Education Scenarios: COGS Tracker

*Tools: `get_cogs_report`, `log_api_usage`*
*Module: cogs_tracker.py*
*Category: 1 (FREE - Internal tracking)*

## Persona

**Business Operations Manager**
- Tracks Cost of Goods Sold for AI API usage
- Monitors gross margins across services
- Needs alerts when margins drop below threshold
- Generates reports for financial planning

---

## Tool 1: get_cogs_report

### Scenario 1: Daily Report

**Goal:** Get today's API usage and costs

**Input:**
```python
{
    "period": "daily",
    "generate_dashboard": False
}
```

**Expected Output:**
```json
{
    "success": true,
    "report": {
        "period": "daily",
        "date": "2026-01-15",
        "services": {
            "grok_image": {"count": 10, "cost": 0.70, "revenue": 2.50},
            "shotstack_video": {"count": 5, "cost": 0.30, "revenue": 1.75},
            "video_ad": {"count": 2, "cost": 0.40, "revenue": 2.00}
        },
        "totals": {
            "cost": 1.40,
            "revenue": 6.25,
            "gross_margin": "77.6%"
        },
        "alerts": []
    }
}
```

**Test Command:**
```bash
python -c "
from src.cogs_tracker import COGSTracker
tracker = COGSTracker()
report = tracker.get_daily_report()
print('Daily Report:')
print(f'  Transactions: {report.get(\"transaction_count\", 0)}')
print(f'  Total Cost: \${report.get(\"total_cost\", 0):.2f}')
print(f'  Total Revenue: \${report.get(\"total_revenue\", 0):.2f}')
print(f'  Gross Margin: {report.get(\"gross_margin\", 0):.1%}')
"
```

**Pass Criteria:**
- [ ] Returns structured report
- [ ] Calculates gross margin correctly
- [ ] Includes all service types

---

### Scenario 2: Monthly Report

**Goal:** Get month-to-date summary

**Input:**
```python
{
    "period": "monthly",
    "generate_dashboard": False
}
```

**Expected Output:**
- Aggregated monthly totals
- Service breakdown
- Trend information

**Test Command:**
```bash
python -c "
from src.cogs_tracker import COGSTracker
tracker = COGSTracker()
report = tracker.get_monthly_report()
print('Monthly Report:')
print(f'  Total Cost: \${report.get(\"total_cost\", 0):.2f}')
print(f'  Total Revenue: \${report.get(\"total_revenue\", 0):.2f}')
print(f'  Gross Margin: {report.get(\"gross_margin\", 0):.1%}')
"
```

**Pass Criteria:**
- [ ] Returns monthly aggregation
- [ ] Includes all transactions in period

---

### Scenario 3: Dashboard Generation

**Goal:** Generate HTML dashboard for visualization

**Input:**
```python
{
    "period": "daily",
    "generate_dashboard": True
}
```

**Expected Output:**
- HTML file created
- Contains charts/visualizations
- File path returned

**Test Command:**
```bash
python -c "
from src.cogs_tracker import COGSTracker
tracker = COGSTracker()
dashboard_path = tracker.export_html_dashboard()
print('Dashboard generated:', dashboard_path)

import os
if dashboard_path and os.path.exists(dashboard_path):
    size = os.path.getsize(dashboard_path)
    print(f'File size: {size} bytes')
else:
    print('Dashboard not created')
"
```

**Pass Criteria:**
- [ ] HTML file created
- [ ] File is valid HTML
- [ ] Contains cost/revenue data

---

## Tool 2: log_api_usage

### Scenario 4: Log Image Generation

**Goal:** Track an image generation API call

**Input:**
```python
{
    "service": "grok_image",
    "user_id": "user_123",
    "quantity": 1
}
```

**Expected Output:**
```json
{
    "success": true,
    "transaction": {
        "service": "grok_image",
        "user_id": "user_123",
        "quantity": 1,
        "cost": 0.07,
        "revenue": 0.25,
        "timestamp": "2026-01-15T10:30:00"
    }
}
```

**Test Command:**
```bash
python -c "
from src.cogs_tracker import COGSTracker
tracker = COGSTracker()
txn = tracker.log_transaction(
    service='grok_image',
    user_id='test_user',
    quantity=1
)
print('Transaction logged:')
print(f'  Service: {txn.service}')
print(f'  Cost: \${txn.cost:.2f}')
print(f'  Revenue: \${txn.revenue:.2f}')
print(f'  Margin: {((txn.revenue - txn.cost) / txn.revenue * 100):.1f}%')
"
```

**Pass Criteria:**
- [ ] Transaction created successfully
- [ ] Cost calculated correctly ($0.07)
- [ ] Revenue calculated correctly ($0.25)
- [ ] Timestamp recorded

---

### Scenario 5: Log Video Generation

**Goal:** Track a video generation API call

**Input:**
```python
{
    "service": "shotstack_video",
    "user_id": "user_456",
    "quantity": 1
}
```

**Expected Costs:**
- Cost: $0.06 per video
- Revenue: $0.35 per video

**Test Command:**
```bash
python -c "
from src.cogs_tracker import COGSTracker
tracker = COGSTracker()
txn = tracker.log_transaction(
    service='shotstack_video',
    user_id='test_user',
    quantity=1
)
print(f'Video generation: cost=\${txn.cost:.2f}, revenue=\${txn.revenue:.2f}')
"
```

**Pass Criteria:**
- [ ] Cost: $0.06
- [ ] Revenue: $0.35
- [ ] Transaction persisted

---

### Scenario 6: Log Bulk Transactions

**Goal:** Track multiple items in one call

**Input:**
```python
{
    "service": "grok_image",
    "user_id": "user_789",
    "quantity": 5
}
```

**Expected Output:**
- Cost: $0.35 (5 × $0.07)
- Revenue: $1.25 (5 × $0.25)

**Test Command:**
```bash
python -c "
from src.cogs_tracker import COGSTracker
tracker = COGSTracker()
txn = tracker.log_transaction(
    service='grok_image',
    user_id='bulk_test',
    quantity=5
)
print(f'Bulk transaction (5 images):')
print(f'  Cost: \${txn.cost:.2f} (expected: \$0.35)')
print(f'  Revenue: \${txn.revenue:.2f} (expected: \$1.25)')
correct = abs(txn.cost - 0.35) < 0.01 and abs(txn.revenue - 1.25) < 0.01
print(f'  Correct: {correct}')
"
```

**Pass Criteria:**
- [ ] Correctly multiplies by quantity
- [ ] Cost = $0.35
- [ ] Revenue = $1.25

---

### Scenario 7: Video Ad Bundle

**Goal:** Track complete video ad creation

**Input:**
```python
{
    "service": "video_ad",
    "user_id": "user_ad",
    "quantity": 1
}
```

**Expected Costs:**
- Cost: $0.20 per ad
- Revenue: $1.00 per ad

**Test Command:**
```bash
python -c "
from src.cogs_tracker import COGSTracker
tracker = COGSTracker()
txn = tracker.log_transaction(
    service='video_ad',
    user_id='ad_test',
    quantity=1
)
print(f'Video ad: cost=\${txn.cost:.2f}, revenue=\${txn.revenue:.2f}')
margin = (txn.revenue - txn.cost) / txn.revenue * 100
print(f'Margin: {margin:.1f}%')
"
```

**Pass Criteria:**
- [ ] Cost: $0.20
- [ ] Revenue: $1.00
- [ ] Margin: 80%

---

## Edge Cases

### Edge Case 1: Invalid Service Type

**Input:**
```python
{
    "service": "invalid_service",
    "user_id": "user_test",
    "quantity": 1
}
```

**Expected Output:**
- Error or rejection
- No transaction created

**Test Command:**
```bash
python -c "
from src.cogs_tracker import COGSTracker
tracker = COGSTracker()
try:
    txn = tracker.log_transaction(
        service='invalid_service',
        user_id='test',
        quantity=1
    )
    print('Accepted invalid service:', txn.service)
except Exception as e:
    print('Rejected invalid service:', type(e).__name__)
"
```

**Pass Criteria:**
- [ ] Either rejects invalid service OR handles gracefully

---

### Edge Case 2: Zero Quantity

**Input:**
```python
{
    "service": "grok_image",
    "user_id": "user_test",
    "quantity": 0
}
```

**Pass Criteria:**
- [ ] Handles zero quantity
- [ ] Either rejects or returns $0 cost/revenue

---

### Edge Case 3: Negative Quantity

**Input:**
```python
{
    "service": "grok_image",
    "user_id": "user_test",
    "quantity": -1
}
```

**Pass Criteria:**
- [ ] Rejects negative quantity
- [ ] Does not create refund transaction

---

### Edge Case 4: Missing User ID

**Input:**
```python
{
    "service": "grok_image",
    "user_id": "",
    "quantity": 1
}
```

**Pass Criteria:**
- [ ] Handles missing user_id
- [ ] Either uses default or rejects

---

## Margin Alert Testing

### Scenario 8: Low Margin Alert

**Goal:** Verify alerts trigger when margin drops below 60%

**Setup:** Create transactions with low margin
**Expected:** Alert in report when margin < 60%

**Test Command:**
```bash
python -c "
from src.cogs_tracker import COGSTracker
tracker = COGSTracker()

# Get current margin status
report = tracker.get_daily_report()
margin = report.get('gross_margin', 1.0)
print(f'Current margin: {margin:.1%}')
print(f'Target margin: 60%')
print(f'Status: {\"OK\" if margin >= 0.60 else \"ALERT\"}')"
```

**Pass Criteria:**
- [ ] Margin calculated correctly
- [ ] Alerts generated when below threshold

---

## Batch Test Script

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer

python -c "
print('Testing COGS Tracker...')
print('=' * 50)

from src.cogs_tracker import COGSTracker
tracker = COGSTracker()

# Test 1: Log transactions for each service
services = [
    ('grok_image', 0.07, 0.25),
    ('shotstack_video', 0.06, 0.35),
    ('video_ad', 0.20, 1.00),
    ('claude_api', 0.002, 0.00)
]

print('Testing transaction logging...')
for service, expected_cost, expected_rev in services:
    try:
        txn = tracker.log_transaction(service=service, user_id='test', quantity=1)
        cost_ok = abs(txn.cost - expected_cost) < 0.001
        status = '✅' if cost_ok else '❌'
        print(f'{status} {service}: cost=\${txn.cost:.3f} (expected \${expected_cost:.3f})')
    except Exception as e:
        print(f'❌ {service}: Error - {e}')

# Test 2: Daily report
print('\\nTesting daily report...')
try:
    report = tracker.get_daily_report()
    print(f'✅ Daily report generated')
    print(f'   Transactions: {report.get(\"transaction_count\", \"N/A\")}')
    print(f'   Total cost: \${report.get(\"total_cost\", 0):.2f}')
except Exception as e:
    print(f'❌ Daily report failed: {e}')

# Test 3: Monthly report
print('\\nTesting monthly report...')
try:
    report = tracker.get_monthly_report()
    print(f'✅ Monthly report generated')
except Exception as e:
    print(f'❌ Monthly report failed: {e}')

# Test 4: Dashboard
print('\\nTesting dashboard generation...')
try:
    path = tracker.export_html_dashboard()
    print(f'✅ Dashboard created: {path}')
except Exception as e:
    print(f'❌ Dashboard failed: {e}')

print('=' * 50)
print('COGS Tracker tests complete!')
"
```

---

## Success Criteria Summary

| Scenario | Tool | Key Check |
|----------|------|-----------|
| Daily report | get_cogs_report | Structured data |
| Monthly report | get_cogs_report | Aggregation |
| Dashboard | get_cogs_report | HTML file created |
| Log image | log_api_usage | Cost $0.07 |
| Log video | log_api_usage | Cost $0.06 |
| Bulk log | log_api_usage | Quantity × cost |
| Video ad | log_api_usage | Cost $0.20 |
| Edge: Invalid service | log_api_usage | Handled |
| Edge: Zero qty | log_api_usage | Handled |
| Edge: Negative qty | log_api_usage | Rejected |
| Margin alert | get_cogs_report | Triggers at <60% |

---

## Service Pricing Reference

| Service | Cost | Revenue | Margin |
|---------|------|---------|--------|
| grok_image | $0.07 | $0.25 | 72% |
| shotstack_video | $0.06 | $0.35 | 83% |
| video_ad | $0.20 | $1.00 | 80% |
| claude_api | $0.002 | $0.00 | N/A (included) |

**Target Gross Margin: 60%+**
