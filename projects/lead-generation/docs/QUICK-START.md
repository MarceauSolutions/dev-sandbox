# Quick Start Guide - Campaign Analytics

**Your analytics system is already built. Here's how to use it.**

---

## 🔥 Most Important Commands

### Daily Health Check (2 minutes)
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper

# Dashboard (last 24 hours)
python -m src.campaign_analytics dashboard --days 1
```

### Check New Responses (1 minute)
```bash
# Last 10 responses
python -c "
import json
with open('output/sms_replies.json') as f:
    data = json.load(f)
    for r in data['replies'][:10]:
        print(f\"{r['business_name']}: {r['category']} - {r['body'][:40]}\")
"
```

### Template Performance (3 minutes)
```bash
# Which templates are winning?
python -m src.campaign_analytics template-scores
```

---

## 📊 Analytics Commands (Copy-Paste Ready)

### Dashboard & Reports
```bash
# 7-day dashboard
python -m src.campaign_analytics dashboard --days 7

# 30-day dashboard
python -m src.campaign_analytics dashboard --days 30

# Comprehensive report
python -m src.campaign_analytics report

# Template comparison
python -m src.campaign_analytics templates

# Conversion funnel
python -m src.campaign_analytics funnel
```

### Performance Analysis
```bash
# Template leaderboard (0-100 scores)
python -m src.campaign_analytics template-scores

# Multi-touch attribution (which touch drives responses)
python -m src.campaign_analytics attribution

# Cohort analysis by category
python -m src.campaign_analytics cohorts --group-by category

# Cohort analysis by location
python -m src.campaign_analytics cohorts --group-by location

# AI recommendations
python -m src.campaign_optimizer recommend
```

### Recording Data
```bash
# Record a response manually
python -m src.campaign_analytics response \
    --phone "+1..." \
    --text "Yes, interested" \
    --category hot_lead

# Categories: hot_lead, warm_lead, cold_lead, opt_out

# Record a conversion
python -m src.campaign_analytics convert \
    --lead-id "abc123" \
    --value 500.00
```

---

## 🧪 A/B Testing Commands

### Create Test
```bash
python -m src.ab_testing create \
    --name "current_vs_social_proof" \
    --control no_website_intro \
    --variant social_proof_intro \
    --sample-size 200 \
    --business marceau-solutions
```

### Check Results
```bash
# View specific test
python -m src.ab_testing results --name "current_vs_social_proof"

# List all tests
python -m src.ab_testing list
```

---

## 📈 What to Monitor

### Daily
- **Response rate**: Target >10%
- **Opt-out rate**: Target <5%
- **Hot+Warm leads**: Any new qualified leads?

### Weekly
- **Template scores**: Which templates are winners (>75/100)?
- **Cohort performance**: Which segments respond best?
- **A/B test progress**: Has winner been declared?

### Monthly
- **Conversion rate**: Target 1.5-2.5%
- **Revenue**: Track total conversions × avg deal size
- **Attribution**: Which touches drive most responses?

---

## 🚨 Current Status (Jan 21, 2026)

```
Campaign: wave_1_no_website_jan15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 METRICS
   Sent:        98
   Delivered:   98 (100%)
   Responses:   14 (14.3%)

⚠️  PROBLEM
   Hot Leads:   0
   Warm Leads:  0
   Opt-outs:    14 (100% of responses)

💡 ACTION REQUIRED
   1. Fix targeting (businesses marked "no website" actually have websites)
   2. Test new message variants (add social proof)
   3. See OPTIMIZATION-PLAYBOOK.md for full plan
```

---

## 🎯 Immediate Actions

**DO THIS FIRST** (before sending more campaigns):

```bash
# 1. Validate targeting accuracy
python -m src.scraper validate-websites --sample 100

# 2. Analyze which cohorts to target
python -m src.campaign_analytics cohorts --group-by category

# 3. Get AI recommendations
python -m src.campaign_optimizer recommend
```

**THEN**:
1. Fix website detection logic (if false positives >10%)
2. Create 3 new template variants
3. Launch A/B test with 200 leads
4. Monitor daily for 7 days

See **OPTIMIZATION-PLAYBOOK.md** for complete step-by-step plan.

---

## 📁 File Structure

```
/Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper/
├── QUICK-START.md              ← YOU ARE HERE (daily reference)
├── EXECUTIVE-SUMMARY.md         ← 5-min overview
├── OPTIMIZATION-PLAYBOOK.md     ← Complete 90-day plan
├── AGENT2-FINDINGS.md           ← Technical deep dive
│
├── src/
│   ├── campaign_analytics.py   ← Analytics engine (1,743 lines)
│   ├── ab_testing.py            ← A/B testing framework (544 lines)
│   └── campaign_optimizer.py   ← AI recommendations
│
└── output/
    ├── sms_campaigns.json       ← Raw campaign data
    ├── sms_replies.json         ← Response data
    ├── campaign_analytics.json  ← Aggregated metrics
    └── lead_records.json        ← Lead-level tracking
```

---

## 🆘 Help

### Common Issues

**Q: Dashboard shows 0% response rate but I see responses**
```bash
# Update analytics from raw data
python -m src.campaign_analytics update
```

**Q: How do I export data to CSV?**
```bash
python -m src.campaign_analytics export --format csv
```

**Q: Where are my ClickUp tasks?**
- Only hot/warm leads get tasks auto-created
- Check: `CLICKUP_API_TOKEN` and `CLICKUP_LIST_ID` in `.env`

**Q: How do I see multi-business performance?**
```bash
# Filter by business
python -m src.campaign_analytics dashboard --business marceau-solutions
python -m src.campaign_analytics dashboard --business swflorida-hvac
```

### Get Full Help
```bash
# Analytics help
python -m src.campaign_analytics --help

# A/B testing help
python -m src.ab_testing --help

# Optimizer help
python -m src.campaign_optimizer --help
```

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| **QUICK-START.md** (this file) | Daily command reference |
| **EXECUTIVE-SUMMARY.md** | 5-minute overview |
| **OPTIMIZATION-PLAYBOOK.md** | 90-day action plan |
| **AGENT2-FINDINGS.md** | Technical analysis |

---

## 🎓 Learning Resources

### Understanding Your Data

**Funnel Stages**:
1. **Contacted**: Message sent
2. **Responded**: Any reply received
3. **Qualified**: Hot or warm lead (interested)
4. **Converted**: Became paying customer

**Response Categories**:
- **Hot Lead**: "Yes, interested", "Call me", "Sounds good"
- **Warm Lead**: "Maybe", "Tell me more", "Later"
- **Cold Lead**: "No thanks", "Not interested"
- **Opt-out**: "STOP", "Unsubscribe", "Remove"

**Template Score** (0-100):
- Response rate: 40% weight
- Qualification rate: 30% weight (hot+warm/total responses)
- Conversion rate: 20% weight
- Opt-out penalty: 5% weight
- Delivery rate: 5% weight

**Cohorts**:
- Group leads by category, location, pain point, or scrape date
- Find which segments have best response rates
- Allocate budget to winners

---

## ✅ Success Checklist

### Week 1
- [ ] Run daily dashboard
- [ ] Validate website targeting (<10% false positives)
- [ ] Identify top 3 cohorts

### Week 2-4
- [ ] Create 3 template variants
- [ ] Launch A/B test (200 leads)
- [ ] Monitor daily
- [ ] Declare winner

### Week 5-8
- [ ] Enable multi-touch sequences
- [ ] Attribution showing 50%+ from touch 2+
- [ ] 3-5 qualified leads in pipeline

### Week 9-12
- [ ] Shift budget to winning cohorts
- [ ] 12%+ positive response rate
- [ ] 3+ conversions
- [ ] $900+ revenue

---

**Remember**: The analytics system is world-class. Focus on **targeting and messaging**, not building more tracking.

**Start here**: Run dashboard, check responses, read OPTIMIZATION-PLAYBOOK.md
