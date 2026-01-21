# Zapier Integration: Apollo.io → ClickUp

**Purpose**: Automatically create ClickUp tasks when new contacts are added to Apollo

**Date Created**: 2026-01-21
**Last Updated**: 2026-01-21

---

## Integration Flow

```
Apollo.io              Zapier              ClickUp
    ↓                    ↓                   ↓
New Contact     →   Filter/Transform  →  Create Task
(Instant)            by Quality          in Pipeline
```

---

## Setup Steps

### Step 1: Connect Apollo.io to Zapier

1. Go to Zapier: https://zapier.com/apps/apollo/integrations
2. Click "Make a Zap"
3. Select Trigger App: **Apollo.io**
4. Select Trigger Event: **New Contact** (Instant)
   - Note: "New Contact" triggers when a contact is added to Apollo
   - There may be up to 30 min delay while Apollo verifies contact info
5. Connect Apollo.io account:
   - In Apollo: Settings → Integrations → API → API keys
   - Create new key named "Zapier" (set as master key)
   - Copy and paste into Zapier
6. Test trigger (should retrieve recent contacts)

### Step 2: Add Filter (Optional but Recommended)

**Purpose**: Only create ClickUp tasks for high-quality leads

1. Click "+ Add Step" → Choose "Filter by Zapier"
2. Add Filter Conditions:

   **Option A - Filter by email presence (recommended for quality)**:
   ```
   Field: Email
   Condition: Exists
   ```

   **Option B - Filter by specific saved search/list**:
   ```
   Field: Contact Stage
   Condition: Text Contains
   Value: [your stage name]
   ```

   **Option C - Multiple conditions**:
   ```
   Condition 1: Email (Exists)
   AND
   Condition 2: Phone (Exists)
   ```

3. Continue only if filter passes

### Step 3: Add ClickUp Action

1. Click "+ Add Step" → Choose "ClickUp"
2. Select Action: **Create Task**
3. Connect ClickUp account
4. Configure Task Settings:
   - **List**: "Leads Pipeline" (or your preferred list)
   - **Task Name**: `{{First Name}} {{Last Name}} - {{Organization Name}}`
   - **Description**:
     ```
     Lead from Apollo.io

     **Contact Info:**
     - Email: {{Email}}
     - Phone: {{Phone Number}} / {{Corporate Phone}} / {{Mobile Phone}}
     - Title: {{Title}}

     **Company Info:**
     - Company: {{Organization Name}}
     - Website: {{Website URL}}

     **Source:** Apollo.io - New Contact Trigger
     ```
   - **Assignee**: (Your ClickUp user)
   - **Status**: "New Lead"
   - **Priority**: Normal (or set manually based on your criteria)
   - **Tags**: `apollo, new-lead`

5. Map Custom Fields (if you have them in ClickUp):
   - **Email** (custom field) → `{{Email}}`
   - **Phone** (custom field) → `{{Phone Number}}` or `{{Mobile Phone}}`
   - **Company** (custom field) → `{{Organization Name}}`
   - **Source** (custom field) → "Apollo.io"

### Step 4: Test and Activate

1. Click "Test & Review"
2. Zapier will create a test task in ClickUp
3. Verify the task appears correctly
4. Turn on Zap

---

## Field Mapping Reference

### Apollo Contact Fields Available in Zapier

| Apollo Field | Zapier Variable | ClickUp Mapping | Notes |
|--------------|-----------------|-----------------|-------|
| First Name | `{{First Name}}` | Task Name | Contact's first name |
| Last Name | `{{Last Name}}` | Task Name | Contact's last name |
| Email | `{{Email}}` | Custom Field: Email | Primary email address |
| Title | `{{Title}}` | Description | Job title |
| Organization Name | `{{Organization Name}}` | Custom Field: Company | Company name |
| Phone Number | `{{Phone Number}}` | Custom Field: Phone | Direct phone |
| Corporate Phone | `{{Corporate Phone}}` | Description | Company phone |
| Mobile Phone | `{{Mobile Phone}}` | Custom Field: Phone | Cell number |
| Home Phone | `{{Home Phone}}` | Description | Personal phone |
| Website URL | `{{Website URL}}` | Description | Contact/company website |
| Address | `{{Address}}` | Description | Full address |
| Account ID | `{{Account ID}}` | Description | Apollo internal ID |

### Apollo Account Fields (if using "New Account" trigger)

| Apollo Field | Zapier Variable | Notes |
|--------------|-----------------|-------|
| Company Name | `{{Name}}` | Account/company name |
| Domain | `{{Domain}}` | Company website domain |
| Phone | `{{Phone}}` | Company phone number |
| Raw Address | `{{Raw Address}}` | Company address |
| Account ID | `{{ID}}` | Apollo internal ID |

---

## Advanced Configuration

### Multi-Condition Filters

Create sophisticated filtering logic:

```
Condition 1: Email (Exists)
AND
Condition 2: Organization Name (Text Contains) "Naples"
AND
Condition 3: Phone Number (Exists)
```

This ensures only contacts with valid contact info create tasks.

### Using Formatter for Task Names

Use Zapier's "Formatter" step to create clean task names:

1. Add "Formatter by Zapier" step
2. Select: **Text → Concatenate**
3. Inputs: `{{First Name}}`, ` `, `{{Last Name}}`, ` - `, `{{Organization Name}}`
4. Use output as Task Name in ClickUp

### Automated Task Assignment by Industry

Use Zapier Paths to route leads:

```
Path A: If Organization Name contains "HVAC" → Assign to Sarah
Path B: If Organization Name contains "Restaurant" → Assign to Mike
Path C: If Organization Name contains "Fitness" → Assign to Alex
Default: Assign to William
```

### Available Apollo Triggers

| Trigger | When it Fires | Use Case |
|---------|---------------|----------|
| **New Contact** (Instant) | Contact added to Apollo | Main trigger for lead pipeline |
| **New Account** (Instant) | Company account created | Track new companies |
| **Contact Updated** | Existing contact modified | Sync updates to ClickUp |
| **Account Updated** | Company info changed | Keep company data current |

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

1. ⬜ Create Zapier account (https://zapier.com)
2. ⬜ Get Apollo API key (Settings → Integrations → API → Create master key)
3. ⬜ Connect Apollo.io to Zapier
4. ⬜ Connect ClickUp to Zapier
5. ⬜ Select "New Contact" trigger
6. ⬜ Add filter (Email exists + Phone exists)
7. ⬜ Configure ClickUp "Create Task" action
8. ⬜ Map fields (see Field Mapping Reference above)
9. ⬜ Test with sample lead
10. ⬜ Activate Zap
11. ⬜ Monitor for 7 days
12. ⬜ Optimize based on results

---

## Resources

- **Zapier Apollo Integration**: https://zapier.com/apps/apollo/integrations
- **Apollo Zapier Docs**: https://knowledge.apollo.io/hc/en-us/articles/4415362778509-Zapier-Integration-Overview
- **ClickUp API Docs**: https://clickup.com/api
- **Apollo API Docs**: https://apolloio.github.io/apollo-api-docs/
- **Our ClickUp Setup**: `execution/clickup_api.py`

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No contacts triggering | No new contacts in Apollo | Add a contact manually to test |
| 30+ min delay | Apollo verifies contact info first | Normal behavior - wait for verification |
| Missing phone/email | Contact not enriched | Only enriched contacts have full data |
| API key invalid | Wrong key type | Use "master key" not limited key |
| Duplicate tasks | Multiple Zaps or re-triggers | Check for duplicate Zaps |

---

**Status**: Ready to implement
**Estimated Setup Time**: 15-30 minutes
**Monthly Cost**: Free tier (100 tasks) or $19.99 (Zapier Starter for 750 tasks)
