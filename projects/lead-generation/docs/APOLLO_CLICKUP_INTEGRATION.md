# Apollo → ClickUp Direct Integration

**Purpose**: Sync qualified Apollo leads directly to ClickUp CRM without Zapier

**Date Created**: 2026-01-21
**Last Updated**: 2026-01-21

---

## Why Direct Integration (Not Zapier)

| Factor | Zapier | Direct API |
|--------|--------|------------|
| **Cost** | $0-49/month (task quota) | $0 (free) |
| **Speed** | 30+ min delay | Instant |
| **Filtering** | Limited text matching | Full Apollo filters + Python logic |
| **Custom Fields** | Basic mapping | Complete field control |
| **Batch Size** | 1 lead at a time | Bulk operations |
| **Deduplication** | Manual | Automatic |

**Bottom line**: Direct integration gives you complete control, costs nothing, and syncs only qualified leads.

---

## Architecture

```
Apollo.io Search (100 leads)
        ↓
    Apollo API
   (with filters)
        ↓
Python Scoring & Qualification
        ↓
Filter: Score ≥ 6 + Verified Email
        ↓
Qualified Leads Only (20 leads)
        ↓
    ClickUp API
   (with custom fields)
        ↓
CRM Tasks with Full Apollo Data
```

**Key Principle**: Only qualified leads enter ClickUp. Cold/unqualified leads stay in Apollo or local JSON.

---

## Setup (One-Time)

### Step 1: Set Environment Variables

```bash
# Add to your .env file
APOLLO_API_KEY=your_apollo_api_key
CLICKUP_API_TOKEN=your_clickup_token
CLICKUP_LIST_ID=901709133703  # Optional: defaults to Intake list
```

### Step 2: Create Apollo Custom Fields in ClickUp

Run once to add Apollo-specific fields:

```bash
cd /Users/williammarceaujr./dev-sandbox
python execution/setup_apollo_custom_fields.py
```

This creates:
- **Apollo ID** (text) - for deduplication
- **Apollo Score** (number) - 0-10 lead quality score
- **Email Verified** (checkbox)
- **Phone Available** (checkbox)
- **Search Profile** (dropdown) - naples_gyms, naples_hvac, etc.
- **Data Source** (dropdown) - apollo, form, sms_reply, etc.
- **Campaign Name** (text)
- **Seniority** (dropdown) - Owner, Founder, C-Suite, etc.
- **Industry** (text)
- **Company Size** (number)
- **LinkedIn** (url)
- **Website** (url)

### Step 3: Verify Field IDs Saved

```bash
cat execution/custom_field_ids.json
```

This file maps field names to ClickUp IDs for programmatic access.

---

## Usage

### Option A: Full Automated Pipeline

Run Apollo search and sync qualified leads in one command:

```python
from src.apollo import ApolloClient, SearchProfiles
from src.apollo_to_clickup import ApolloClickUpSync, LeadQualification

# Initialize
apollo = ApolloClient()
sync = ApolloClickUpSync()

# Search Apollo with filters
filters = SearchProfiles.naples_gyms()
results = apollo.search_people_advanced(filters)
leads = results.get("people", [])

# Sync qualified leads to ClickUp
sync_results = sync.sync_apollo_leads(
    leads=leads,
    campaign_name="Naples Gyms Q1",
    search_profile="naples_gyms",
    min_score=6.0,
    min_qualification=LeadQualification.WARM,
    require_verified_email=True,
    dry_run=False  # Set to True for testing
)

print(f"Synced {sync_results['summary']['synced']} leads to ClickUp")
```

### Option B: CLI Commands

```bash
# Step 1: Export Apollo search to JSON
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper

python -c "
from src.apollo import ApolloClient, SearchProfiles
import json

client = ApolloClient()
filters = SearchProfiles.naples_gyms()
results = client.search_people_advanced(filters)

with open('output/apollo_leads.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f'Exported {len(results.get(\"people\", []))} leads')
"

# Step 2: Dry run (see what would sync)
python -m src.apollo_to_clickup sync \
    --input output/apollo_leads.json \
    --campaign "Naples Gyms Q1" \
    --profile naples_gyms \
    --min-score 6.0 \
    --verified-only \
    --dry-run

# Step 3: Actual sync
python -m src.apollo_to_clickup sync \
    --input output/apollo_leads.json \
    --campaign "Naples Gyms Q1" \
    --profile naples_gyms \
    --min-score 6.0 \
    --verified-only \
    --for-real
```

### Option C: Hot Leads Only

Sync only the highest-quality leads (score ≥ 8, verified email, has phone):

```bash
python -m src.apollo_to_clickup sync \
    --input output/apollo_leads.json \
    --campaign "Naples Gyms Q1" \
    --min-score 8.0 \
    --hot-only \
    --for-real
```

---

## Lead Qualification Logic

### Scoring (0-10 Scale)

| Factor | Points | Details |
|--------|--------|---------|
| **Email Verified** | +2 | Verified = +2, Guessed = +1 |
| **Phone Available** | +2 | Mobile = +2, Direct = +1.5, Corporate = +1 |
| **Decision Maker** | +2 | Owner/Founder/C-Suite = +2, VP/Director = +1.5, Manager = +1 |
| **Small Business** | +2 | 1-10 employees = +2, 11-50 = +1.5, 51-200 = +1 |
| **LinkedIn Profile** | +1 | Has LinkedIn URL |
| **Company Website** | +1 | Has website/domain |

**Maximum Score**: 10

### Qualification Levels

| Level | Criteria | ClickUp Priority |
|-------|----------|------------------|
| **HOT 🔥** | Score ≥ 8 + verified email + phone | High (2) |
| **WARM 🌡️** | Score ≥ 6 + has email | Normal (3) |
| **COLD ❄️** | Score < 6 or limited contact info | Low (4) |
| **UNQUALIFIED** | No contact info or excluded title | Not synced |

### Excluded Titles

These titles are automatically excluded:
- Intern
- Assistant
- Coordinator
- Receptionist

---

## ClickUp Task Format

When a lead is synced, the ClickUp task includes:

### Task Name
```
John Smith - Acme Gym 🔥
```
(🔥 emoji for HOT leads)

### Description
```markdown
## Contact Information
**Name:** John Smith
**Title:** Owner
**Email:** john@acmegym.com (verified)
**Phone:** +1 239 555 1234 (mobile)
**LinkedIn:** https://linkedin.com/in/johnsmith

## Company Information
**Company:** Acme Gym
**Website:** acmegym.com
**Industry:** Health & Fitness
**Size:** 15 employees
**Location:** Naples, FL

## Lead Scoring
**Apollo Score:** 9.0/10
**Qualification:** HOT
**Email Verified:** ✅ Yes

## Source
**Campaign:** Naples Gyms Q1
**Search Profile:** naples_gyms
**Apollo ID:** abc123xyz
**Scraped:** 2026-01-21T10:30:00
```

### Custom Fields Populated
- Email: john@acmegym.com
- Phone: +1 239 555 1234
- Company: Acme Gym
- Apollo ID: abc123xyz
- Apollo Score: 9.0
- Email Verified: ✅
- Phone Available: ✅
- Search Profile: naples_gyms
- Data Source: apollo
- Campaign Name: Naples Gyms Q1
- Seniority: Owner
- Industry: Health & Fitness
- Company Size: 15
- LinkedIn: https://linkedin.com/in/johnsmith
- Website: acmegym.com
- Lead Temperature: Hot 🔥

### Tags
- `apollo`
- `naples-gyms-q1`
- `hot`
- `naples-gyms`

---

## Deduplication

The sync system automatically prevents duplicates via three checks:

1. **Apollo ID** - Same person won't be synced twice
2. **Email** - Same email address won't create duplicate tasks
3. **Phone** - Same phone number won't create duplicate tasks

If a duplicate is detected:
- **In sync log**: Lead is skipped entirely
- **In ClickUp**: Comment added to existing task with new touchpoint info

### Check Sync Status

```bash
python -m src.apollo_to_clickup status
```

Shows:
- Total synced Apollo IDs
- Total synced emails
- Total synced phones
- Recent sync history

### Clear Sync Log (Reset Deduplication)

```bash
python -m src.apollo_to_clickup clear-log
```

---

## Recommended Workflow

### Daily Lead Generation

```bash
# 1. Run Apollo search for target industry
python -c "
from src.apollo import ApolloClient, SearchProfiles
import json

client = ApolloClient()
filters = SearchProfiles.naples_gyms()
results = client.search_people_advanced(filters)

with open('output/today_leads.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f'Found {len(results.get(\"people\", []))} leads')
"

# 2. Sync qualified leads to ClickUp
python -m src.apollo_to_clickup sync \
    --input output/today_leads.json \
    --campaign "Naples Gyms $(date +%Y-%m-%d)" \
    --profile naples_gyms \
    --min-score 6.0 \
    --verified-only \
    --for-real

# 3. Work leads in ClickUp pipeline
```

### Campaign-Based Workflow

```python
from src.apollo import ApolloClient, PeopleSearchFilters, Seniority, EmailStatus, EmployeeRange
from src.apollo_to_clickup import ApolloClickUpSync, LeadQualification

# Custom search for specific campaign
filters = PeopleSearchFilters(
    person_seniorities=[Seniority.OWNER, Seniority.FOUNDER],
    person_locations=["Naples, FL", "Fort Myers, FL"],
    organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
    contact_email_status=[EmailStatus.VERIFIED],
    q_keywords="hvac air conditioning",
    per_page=100
)

# Search
apollo = ApolloClient()
results = apollo.search_people_advanced(filters)

# Sync only HOT leads
sync = ApolloClickUpSync()
sync.sync_apollo_leads(
    leads=results.get("people", []),
    campaign_name="SW Florida HVAC Q1",
    search_profile="custom",
    min_score=8.0,
    min_qualification=LeadQualification.HOT,
    require_verified_email=True,
    require_phone=True,
    dry_run=False
)
```

---

## Filter Options

### By Score
```bash
--min-score 8.0  # Only 8+ scores
--min-score 6.0  # 6+ scores (default)
--min-score 0.0  # All scores
```

### By Qualification
```bash
--hot-only       # Only HOT leads (score ≥ 8, verified email, phone)
# Default is WARM+ (score ≥ 6, has email)
```

### By Contact Quality
```bash
--verified-only  # Only verified emails
# Add in code: require_phone=True for phone required
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "CLICKUP_API_TOKEN not set" | Add to .env file |
| "custom_field_ids.json not found" | Run `python execution/setup_apollo_custom_fields.py` |
| Duplicate tasks created | Check sync log with `python -m src.apollo_to_clickup status` |
| Fields not populating | Verify field IDs match between config and ClickUp |
| 0 leads synced | Lower --min-score or remove --verified-only |

### Check ClickUp API Connection

```bash
python execution/clickup_api.py list-workspaces
```

### View Sync Results

```bash
cat projects/shared/lead-scraper/output/last_sync_results.json
```

---

## File Reference

| File | Purpose |
|------|---------|
| `src/apollo_to_clickup.py` | Main sync module |
| `src/apollo.py` | Apollo search with filters |
| `execution/setup_apollo_custom_fields.py` | Create ClickUp custom fields |
| `execution/custom_field_ids.json` | Field ID mapping |
| `output/apollo_clickup_sync.json` | Sync log (deduplication) |
| `output/last_sync_results.json` | Most recent sync results |

---

## Migration from Zapier

If you previously used the Zapier integration:

1. **Disable Zapier Zap** - Turn off the Apollo → ClickUp Zap
2. **Run custom field setup** - Creates new Apollo fields
3. **Clear sync log** - Start fresh with direct integration
4. **Test with dry-run** - Verify sync works correctly
5. **Enable live sync** - Switch from `--dry-run` to `--for-real`

The direct integration is fully compatible with existing ClickUp tasks and won't create duplicates for leads already in your CRM.

---

## Cost Comparison

| Scenario | Zapier Cost | Direct Integration Cost |
|----------|-------------|------------------------|
| 100 leads/month | Free tier | $0 |
| 500 leads/month | ~$20/month | $0 |
| 2000 leads/month | ~$49/month | $0 |
| 10000 leads/month | ~$299/month | $0 |

**Savings**: $240-3,588/year depending on volume

---

**Status**: Ready for production
**Replaces**: ZAPIER_APOLLO_CLICKUP.md (Zapier approach deprecated)
