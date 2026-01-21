# Zapier Integration: Apollo.io → ClickUp

**Purpose**: Automatically create ClickUp tasks when Apollo enriches leads

**Date Created**: 2026-01-21

---

## Integration Flow

```
Apollo.io              Zapier              ClickUp
    ↓                    ↓                   ↓
New Enriched    →   Transform Data   →  Create Task
Contact              Filter Quality      in Pipeline
```

---

## Setup Steps

### Step 1: Connect Apollo.io to Zapier

1. Go to Zapier: https://zapier.com/apps/apollo/integrations
2. Click "Make a Zap"
3. Select Trigger App: **Apollo.io**
4. Select Trigger Event: **New Enriched Contact**
5. Connect Apollo.io account (use API key from .env)
6. Test trigger (should retrieve recent enriched contacts)

### Step 2: Add Filter (Optional but Recommended)

**Purpose**: Only create ClickUp tasks for high-quality leads

1. Click "+ Add Step" → Choose "Filter"
2. Add Filter Conditions:
   ```
   Field: Lead Score
   Condition: Greater than or equal to
   Value: 8.0
   ```

   OR

   ```
   Field: Tags
   Condition: Contains
   Value: hot_lead,callback_requested
   ```

3. Continue only if filter passes

### Step 3: Add ClickUp Action

1. Click "+ Add Step" → Choose "ClickUp"
2. Select Action: **Create Task**
3. Connect ClickUp account
4. Configure Task Settings:
   - **List**: "Leads Pipeline" (or your preferred list)
   - **Task Name**: `{{apollo_name}} - {{apollo_company}}`
   - **Description**:
     ```
     Lead from Apollo.io enrichment

     **Contact Info:**
     - Email: {{apollo_email}}
     - Phone: {{apollo_phone}}
     - Title: {{apollo_title}}

     **Company Info:**
     - Company: {{apollo_company}}
     - Location: {{apollo_location}}
     - Industry: {{apollo_industry}}
     - Employee Count: {{apollo_employee_count}}

     **Lead Score:** {{apollo_lead_score}} / 10

     **Enriched:** {{apollo_enriched_date}}
     ```
   - **Assignee**: (Your ClickUp user)
   - **Status**: "New Lead"
   - **Priority**: Based on lead score:
     - Score 9-10 → High Priority
     - Score 8-9 → Normal Priority
     - Score < 8 → Low Priority
   - **Tags**: `{{apollo_campaign}}, apollo-enriched`

5. Map Custom Fields:
   - **Email** (custom field) → `{{apollo_email}}`
   - **Phone** (custom field) → `{{apollo_phone}}`
   - **Company** (custom field) → `{{apollo_company}}`
   - **Lead Score** (custom field) → `{{apollo_lead_score}}`
   - **Source** (custom field) → "Apollo.io"

### Step 4: Test and Activate

1. Click "Test & Review"
2. Zapier will create a test task in ClickUp
3. Verify the task appears correctly
4. Turn on Zap

---

## Field Mapping Reference

| Apollo Field | ClickUp Field | Notes |
|--------------|---------------|-------|
| `name` | Task Name | Combined with company name |
| `email` | Custom Field: Email | Store for outreach |
| `phone` | Custom Field: Phone | Store for SMS/calls |
| `title` | Description | Job title of contact |
| `company_name` | Custom Field: Company | Company name |
| `location` | Description | Geographic location |
| `industry` | Description | Industry category |
| `employee_count` | Description | Company size |
| `lead_score` | Custom Field: Lead Score | Quality score (0-10) |
| `enriched_date` | Description | When enriched |
| `campaign` | Tags | Campaign identifier |

---

## Advanced Configuration

### Priority Assignment (Based on Lead Score)

Use Zapier's "Formatter" step to convert lead score to priority:

1. Add "Formatter by Zapier" step
2. Select: **Numbers → Perform Math Operation**
3. Input: `{{apollo_lead_score}}`
4. Operation: Convert to priority
5. Output mapping:
   - 9-10 → "urgent" (High Priority)
   - 8-9 → "high" (Normal Priority)
   - 7-8 → "normal" (Low Priority)
   - < 7 → Don't create task (use Filter)

### Multi-Condition Filters

Create sophisticated filtering logic:

```
Condition 1: Lead Score ≥ 8
AND
Condition 2: Campaign contains "Naples"
AND
Condition 3: Phone is not empty
```

This ensures only qualified, local leads with contact info create tasks.

### Automated Task Assignment

Route leads to team members based on campaign:

```
If Campaign contains "HVAC" → Assign to Sarah
If Campaign contains "Restaurant" → Assign to Mike
If Campaign contains "Fitness" → Assign to Alex
Else → Assign to William
```

---

## Cost Considerations

### Zapier Pricing

| Plan | Tasks/Month | Cost/Month | Notes |
|------|-------------|------------|-------|
| Free | 100 tasks | $0 | Good for testing |
| Starter | 750 tasks | $19.99 | Ideal for 25 leads/day |
| Professional | 2,000 tasks | $49 | For scaling operations |
| Team | 50,000 tasks | $299 | Enterprise scale |

### Our Usage Estimate

- **Campaigns per month**: 10
- **Leads per campaign**: 20 enriched (top 20% of 100)
- **Total tasks created**: 200/month
- **Recommended plan**: Starter ($19.99/month)

---

## Alternative: Direct API Integration

Instead of Zapier, we could build a direct Apollo → ClickUp integration:

### Pros:
- No Zapier subscription cost
- More control over logic
- Faster execution
- Custom enrichment logic

### Cons:
- Requires development time
- Need to maintain code
- More complex error handling

### Implementation Estimate:
- **Time**: 4-6 hours
- **Cost**: Free (no Zapier fees)
- **Maintenance**: 1 hour/month

**Recommendation**: Start with Zapier for speed, consider direct integration if Zapier costs become significant.

---

## Webhook Alternative (Advanced)

For real-time integration without Zapier:

1. **Apollo Webhook**: Configure Apollo to send webhook when contact enriched
2. **Our Server**: Receive webhook, validate data
3. **ClickUp API**: Create task directly via ClickUp API

**Setup**:
```python
# webhook_receiver.py
from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/apollo-webhook', methods=['POST'])
def apollo_webhook():
    data = request.json

    # Validate lead score
    if data.get('lead_score', 0) < 8:
        return 'Lead score too low', 200

    # Create ClickUp task
    clickup_api_key = os.getenv('CLICKUP_API_TOKEN')
    headers = {'Authorization': clickup_api_key}

    task_data = {
        'name': f"{data['name']} - {data['company']}",
        'description': f"Email: {data['email']}\nPhone: {data['phone']}",
        'status': 'New Lead',
        'tags': [data['campaign'], 'apollo-enriched']
    }

    response = requests.post(
        'https://api.clickup.com/api/v2/list/{LIST_ID}/task',
        headers=headers,
        json=task_data
    )

    return 'Task created', 200
```

---

## Monitoring & Troubleshooting

### Zapier Task History

Check: https://zapier.com/app/history

**What to Monitor**:
- Success rate (should be >95%)
- Failed tasks (check error messages)
- Task volume trends

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Tasks not creating | Zap turned off | Turn on Zap in Zapier dashboard |
| Duplicate tasks | Multiple Zaps running | Disable duplicate Zaps |
| Missing fields | Field mapping error | Review and update field mappings |
| Slow creation | Zapier tier limits | Upgrade to Professional plan |

### ClickUp Verification

After Zap runs:
1. Go to ClickUp "Leads Pipeline" list
2. Check for new task
3. Verify all fields populated correctly
4. Test email/phone links work

---

## Success Metrics

Track these to measure integration effectiveness:

- **Task creation rate**: 100% of enriched leads → ClickUp tasks
- **Data accuracy**: 95%+ of fields populated correctly
- **Time savings**: Manual task creation eliminated (~5 min/lead)
- **Lead response time**: Faster follow-up (task created immediately)

---

## Next Steps

1. ✅ Create Zapier account
2. ✅ Connect Apollo.io
3. ✅ Connect ClickUp
4. ✅ Configure Zap with filters
5. ✅ Test with sample lead
6. ✅ Activate Zap
7. ⏳ Monitor for 7 days
8. ⏳ Optimize based on results

---

## Resources

- **Zapier Apollo Integration**: https://zapier.com/apps/apollo/integrations/clickup
- **ClickUp API Docs**: https://clickup.com/api
- **Apollo Webhook Docs**: https://apolloio.github.io/apollo-api-docs/
- **Our ClickUp Setup**: `execution/clickup_api.py`

---

**Status**: Ready to implement
**Estimated Setup Time**: 30 minutes
**Monthly Cost**: $19.99 (Zapier Starter)
