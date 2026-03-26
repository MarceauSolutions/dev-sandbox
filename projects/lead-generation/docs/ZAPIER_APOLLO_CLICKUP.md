# Zapier Integration: Apollo.io → ClickUp

**Purpose**: Automatically create ClickUp tasks when new contacts are added to Apollo

**Date Created**: 2026-01-21
**Last Updated**: 2026-01-21

---

## Two Ways to Use Apollo Filters

Apollo filtering can happen at **three levels**. Use them together for best results:

| Level | Where | Cost | Best For |
|-------|-------|------|----------|
| **1. Apollo UI** | Apollo.io web interface | Free | Manual searches, saved searches |
| **2. Apollo API** | `src/apollo.py` programmatic | Free | Automated pipelines, bulk searches |
| **3. Zapier** | Zapier filter step | Uses task quota | Last-resort filtering |

**Recommendation**: Filter at Level 1 or 2 FIRST, then Zapier only triggers for pre-qualified leads.

---

## Integration Flow

```
Apollo.io                    Zapier              ClickUp
    ↓                          ↓                   ↓
Filtered Search       →   New Contact      →  Create Task
(UI or API)              (Instant trigger)    in Pipeline
    ↓
Only qualified
leads added
```

---

## Option A: Apollo UI Filtering (Manual)

### Step 1: Create Saved Search in Apollo UI

1. Go to Apollo.io → People Search
2. Apply these filters in the UI:

| Filter | Setting | Why |
|--------|---------|-----|
| **Email Status** | Verified | Only deliverable emails |
| **Phone** | Has Mobile Phone | Callable contacts |
| **Location** | Naples, FL (your target) | Geographic targeting |
| **# Employees** | 1-50 | Small business focus |
| **Job Titles** | Owner, CEO, Founder, Manager | Decision-makers |
| **Seniority** | Owner, Founder, C-Suite | Top decision-makers |

3. Click **Save Search** → Name it (e.g., "Naples Gyms Qualified")
4. Use this saved search to find leads manually
5. Add qualified leads to a List called "Send to ClickUp"

### Step 2: Zapier Triggers from List

Zapier's "New Contact" trigger fires when contacts are added to Apollo - including when you add them to a List from your saved search.

---

## Option B: Apollo API Filtering (Automated)

Use our enhanced Apollo client with full filter support. See `APOLLO_SEARCH_FILTERS.md` for complete reference.

### Quick Start with Search Profiles

```python
from src.apollo import ApolloClient, SearchProfiles

client = ApolloClient()

# Pre-built Naples profiles
results = client.search_with_profile("naples_gyms")
results = client.search_with_profile("naples_hvac")
results = client.search_with_profile("naples_restaurants")

# Generic profile with location
results = client.search_with_profile(
    "small_business_owners",
    location="Naples, FL",
    industry_keyword="gym"
)

# Verified emails only
results = client.search_with_profile(
    "verified_contacts_only",
    location="Naples, FL",
    industry_keyword="fitness"
)
```

### Custom Filters (Full Control)

```python
from src.apollo import (
    ApolloClient,
    PeopleSearchFilters,
    Seniority,
    EmailStatus,
    EmployeeRange
)

client = ApolloClient()

# Build custom filter with all options
filters = PeopleSearchFilters(
    # Person filters
    person_seniorities=[Seniority.OWNER, Seniority.FOUNDER, Seniority.C_SUITE],
    person_locations=["Naples, FL"],

    # Contact quality
    contact_email_status=[EmailStatus.VERIFIED],  # Only verified emails

    # Organization filters
    organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],

    # Industry
    q_keywords="gym fitness",
    q_organization_keyword_tags=["fitness", "gym", "health club"],

    # Pagination
    per_page=100
)

results = client.search_people_advanced(filters)
```

### Available API Filters

| Category | Filters |
|----------|---------|
| **Person** | `person_titles`, `person_not_titles`, `person_seniorities`, `person_locations`, `person_departments` |
| **Contact Quality** | `contact_email_status` (verified/guessed/bounced), `has_email`, `has_phone` |
| **Organization** | `organization_locations`, `organization_domains`, `organization_num_employees_ranges`, `organization_not_locations` |
| **Industry** | `q_keywords`, `q_organization_keyword_tags` |
| **Technology** | `currently_using_any_of_technology_uids`, `not_using_any_of_technology_uids` |
| **Revenue** | `revenue_range` (Under 1M through Over 1B) |
| **Prospecting** | `prospected_by_current_team`, `revealed_for_current_team` |

### Seniority Values

```python
Seniority.OWNER      # Business owners
Seniority.FOUNDER    # Founders
Seniority.C_SUITE    # CEO, CFO, CTO, etc.
Seniority.VP         # Vice Presidents
Seniority.DIRECTOR   # Directors
Seniority.MANAGER    # Managers
Seniority.SENIOR     # Senior staff
Seniority.ENTRY      # Entry level
```

### Employee Range Values

```python
EmployeeRange.SOLO       # 1 employee
EmployeeRange.MICRO      # 1-10 employees
EmployeeRange.SMALL      # 11-50 employees
EmployeeRange.MEDIUM     # 51-200 employees
EmployeeRange.LARGE      # 201-500 employees
```

---

## Zapier Setup (After Apollo Filtering)

Since leads are pre-filtered in Apollo (UI or API), Zapier setup is simple:

### Step 1: Connect Apollo.io to Zapier

1. Go to Zapier: https://zapier.com/apps/apollo/integrations
2. Click "Make a Zap"
3. Select Trigger App: **Apollo.io**
4. Select Trigger Event: **New Contact** (Instant)
   - Note: There may be up to 30 min delay while Apollo verifies contact info
5. Connect Apollo.io account:
   - In Apollo: Settings → Integrations → API → API keys
   - Create new key named "Zapier" (set as master key)
   - Copy and paste into Zapier
6. Test trigger (should retrieve recent contacts)

### Step 2: Skip Zapier Filters (Already Done in Apollo!)

Since you've filtered in Apollo (UI or API), you likely don't need Zapier filters.

**Only add a Zapier filter if** you need logic Apollo can't do:
- Complex text matching on titles
- Time-based conditions
- Multi-field conditional logic

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
   - **Priority**: Normal
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

## Filter Comparison: UI vs API vs Zapier

| Filter | Apollo UI | Apollo API (`src/apollo.py`) | Zapier |
|--------|-----------|------------------------------|--------|
| Email Status | ✅ Email Status dropdown | ✅ `contact_email_status=[EmailStatus.VERIFIED]` | ❌ Not available |
| Phone Available | ✅ Has Mobile Phone checkbox | ✅ `has_phone=True` | ⚠️ Check if field exists |
| Location | ✅ Location filter | ✅ `person_locations=["Naples, FL"]` | ⚠️ Text contains |
| Employee Count | ✅ # Employees slider | ✅ `organization_num_employees_ranges=[EmployeeRange.SMALL]` | ❌ Not available |
| Seniority | ✅ Seniority dropdown | ✅ `person_seniorities=[Seniority.OWNER]` | ❌ Not available |
| Job Titles | ✅ Job Titles field | ✅ `person_titles=["owner", "ceo"]` | ⚠️ Text contains |
| Industry Tags | ✅ Industry dropdown | ✅ `q_organization_keyword_tags=["fitness"]` | ❌ Not available |
| Technologies | ✅ Technologies filter | ✅ `not_using_any_of_technology_uids=["shopify"]` | ❌ Not available |
| Revenue | ✅ Revenue filter | ✅ `revenue_range=RevenueRange.R_1M_10M` | ❌ Not available |
| **Cost** | **Free** | **Free** | **Uses task quota** |

**Conclusion**: Do filtering in Apollo (UI or API), not Zapier.

---

## Recommended Workflow

### For Manual/Low-Volume

1. Create saved search in Apollo UI with quality filters
2. Review results manually
3. Add qualified leads to "Send to ClickUp" list
4. Zapier triggers → Creates ClickUp task
5. Work leads in ClickUp

### For Automated/High-Volume

1. Run API search with `SearchProfiles` or custom filters
2. Results are already filtered (verified email, correct seniority, etc.)
3. Add to Apollo list programmatically
4. Zapier triggers → Creates ClickUp task
5. Work leads in ClickUp

### Full Pipeline (End-to-End Automation)

```bash
# Run full pipeline with API filtering
python -m src.apollo_pipeline run \
    --search "gyms in Naples FL, 1-50 employees" \
    --campaign "Naples Gyms Q1" \
    --dry-run
```

This uses `src/apollo.py` filters internally.

---

## Cost Considerations

### Zapier Pricing

| Plan | Tasks/Month | Cost/Month | Notes |
|------|-------------|------------|-------|
| Free | 100 tasks | $0 | Good for testing |
| Starter | 750 tasks | $19.99 | Ideal for 25 leads/day |
| Professional | 2,000 tasks | $49 | For scaling operations |
| Team | 50,000 tasks | $299 | Enterprise scale |

### Why Apollo Filtering Saves Money

| Approach | Contacts Found | Zapier Tasks | Cost |
|----------|----------------|--------------|------|
| No filtering | 1,000 | 1,000 | $49+/month |
| Apollo filtered (top 20%) | 200 | 200 | Free tier |
| API filtered + verified email | 50-100 | 50-100 | Free tier |

**Pre-filter in Apollo = Stay on free Zapier tier**

---

## Alternative: Direct API Integration (No Zapier)

For zero Zapier cost, use our direct integration:

```python
from src.apollo import ApolloClient, SearchProfiles
from execution.clickup_api import create_task

client = ApolloClient()

# Search with filters
filters = SearchProfiles.naples_gyms()
filters.contact_email_status = [EmailStatus.VERIFIED]
results = client.search_all_pages(filters, max_results=100)

# Create ClickUp tasks directly
for person in results:
    create_task(
        name=f"{person['first_name']} {person['last_name']} - {person.get('organization', {}).get('name', '')}",
        description=f"Email: {person.get('email')}\nPhone: {person.get('phone_numbers', [{}])[0].get('raw_number', '')}",
        list_id=os.getenv("CLICKUP_LIST_ID"),
        status="New Lead",
        tags=["apollo", "api-import"]
    )
```

**Pros**: No Zapier cost, full control, faster
**Cons**: Need to run script (cron or manual)

---

## Available Apollo Triggers in Zapier

| Trigger | When it Fires | Use Case |
|---------|---------------|----------|
| **New Contact** (Instant) | Contact added to Apollo | Main trigger for lead pipeline |
| **New Account** (Instant) | Company account created | Track new companies |
| **Contact Updated** | Existing contact modified | Sync updates to ClickUp |
| **Account Updated** | Company info changed | Keep company data current |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No contacts triggering | No new contacts in Apollo | Add a contact manually to test |
| 30+ min delay | Apollo verifies contact info first | Normal behavior - wait for verification |
| Missing phone/email | Contact not enriched | Use `contact_email_status=[EmailStatus.VERIFIED]` filter |
| API key invalid | Wrong key type | Use "master key" not limited key |
| Duplicate tasks | Multiple Zaps or re-triggers | Check for duplicate Zaps |
| Low quality leads | Not filtering in Apollo | Use SearchProfiles or UI filters FIRST |

---

## Next Steps

1. ⬜ Decide: Manual (Apollo UI) or Automated (Apollo API)
2. ⬜ If API: Test search profiles in `src/apollo.py`
3. ⬜ Create Apollo API key (Settings → Integrations → API → Create master key)
4. ⬜ Create Zapier account (https://zapier.com)
5. ⬜ Connect Apollo.io to Zapier
6. ⬜ Connect ClickUp to Zapier
7. ⬜ Select "New Contact" trigger
8. ⬜ Configure ClickUp "Create Task" action
9. ⬜ Map fields (see Field Mapping Reference above)
10. ⬜ Test with sample lead
11. ⬜ Activate Zap
12. ⬜ Monitor for 7 days

---

## Resources

- **Apollo Search Filters (API)**: `APOLLO_SEARCH_FILTERS.md`
- **Apollo Client Code**: `src/apollo.py`
- **Apollo Pipeline**: `src/apollo_pipeline.py`
- **Zapier Apollo Integration**: https://zapier.com/apps/apollo/integrations
- **Apollo API Docs**: https://docs.apollo.io/
- **ClickUp API Docs**: https://clickup.com/api
- **Our ClickUp Setup**: `execution/clickup_api.py`

---

**Status**: Ready to implement
**Estimated Setup Time**: 15-30 minutes
**Monthly Cost**: Free tier (with Apollo pre-filtering) or $19.99 (Zapier Starter)
