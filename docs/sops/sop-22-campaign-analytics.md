# SOP 22: Campaign Analytics & Tracking

**When**: Tracking campaign performance, response rates, and optimizing outreach strategies

**Purpose**: Measure campaign effectiveness, identify winning templates, and track conversion funnels to continuously improve cold outreach ROI

**Agent**: Claude Code (primary, complex analysis). Clawdbot (quick status checks). Ralph: N/A.

**Prerequisites**:
- ✅ Campaign data exists in `output/sms_campaigns.json`
- ✅ At least one campaign completed (SOP 18)
- ✅ Lead scraper project dependencies installed

**Key Metrics Tracked**:
- Response rates by template
- Conversion funnel (Contacted → Responded → Qualified → Converted)
- Multi-touch attribution (which follow-up drives responses)
- A/B test performance with statistical significance

**Directory Structure**:
```
projects/shared/lead-scraper/
├── output/
│   ├── sms_campaigns.json       # Raw campaign data
│   ├── campaign_analytics.json  # Aggregated metrics
│   └── template_performance.json
├── src/
│   └── campaign_analytics.py    # Analytics engine
```

**Steps**:

1. **Record a response** when lead replies:
   ```bash
   python -m src.campaign_analytics response \
       --phone "+1XXXXXXXXXX" \
       --text "Yes, I'm interested" \
       --category hot_lead
   ```

   Categories: `hot_lead`, `warm_lead`, `cold_lead`, `not_interested`, `wrong_number`, `callback_requested`

2. **Update campaign metrics** after batch completes:
   ```bash
   python -m src.campaign_analytics update --campaign-id "wave_1_no_website_jan15"
   ```

3. **View performance report**:
   ```bash
   python -m src.campaign_analytics report
   ```

4. **Compare template performance**:
   ```bash
   python -m src.campaign_analytics templates
   ```

5. **View conversion funnel**:
   ```bash
   python -m src.campaign_analytics funnel
   ```

**Conversion Funnel Stages**:
```
CONTACTED (100%) → RESPONDED (5-10%) → QUALIFIED (50% of responded) → CONVERTED (20% of qualified)
```

**Statistical Significance for A/B Tests**:
- Minimum 100 contacts per variant
- 85% confidence threshold for declaring winner
- Run tests for minimum 7 days

**ClickUp Integration Strategy**:
- ClickUp = **Qualified leads only** (hot/warm)
- Don't create tasks for every cold contact
- Auto-create task when lead categorized as `hot_lead` or `callback_requested`

**Success Criteria**:
- ✅ Response rates tracked per template
- ✅ Funnel conversion rates calculated
- ✅ A/B tests reach statistical significance
- ✅ Winning templates identified

**Troubleshooting**:

| Issue | Cause | Solution |
|-------|-------|----------|
| No campaigns found | Missing sms_campaigns.json | Run SOP 18 first to create campaign |
| Stats not updating | Cache stale | Run `campaign_analytics update` |
| Template comparison empty | No A/B data | Ensure templates tagged in campaign creation |
| Funnel shows 0% | No responses recorded | Check webhook receiving SMS replies |

**References**: `projects/shared/lead-scraper/src/campaign_analytics.py`, SOP 18 (SMS Campaign Execution)
