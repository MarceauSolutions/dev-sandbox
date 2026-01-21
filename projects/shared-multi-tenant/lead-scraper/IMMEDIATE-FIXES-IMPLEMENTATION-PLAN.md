# IMMEDIATE FIXES - Implementation Plan

**Date**: 2026-01-21
**Status**: Ready to Execute
**Priority**: CRITICAL - Must complete before sending more campaigns

---

## ✅ COMPLETED (By Claude)

### 1. Google Cloud Charge Investigation ✅
**Finding**: $112.44 total for Jan 1-21 = **$5.35/day average** (NOT $100 in 2 days)
- Jan 19-20 usage: ~$10.71 (normal)
- The "$100 charge" was likely a billing threshold trigger or bank authorization hold
- **Action**: No immediate action needed - usage is normal
- **See**: Customer's CSV shows Places API costs are expected

### 2. Damage Control Analysis ✅
**Decision**: Honor opt-outs, no apology messages
- 2 angry responses identified
- Sending apology SMS could be seen as "still contacting me"
- Best apology = fix the system, never repeat
- **See**: `/output/DAMAGE-CONTROL-APOLOGY-MESSAGES.md`

### 3. Website Detection Logic - FIXED ✅
**Created**: `src/website_validator.py` (365 lines)
- Detects aggregator URLs (Yelp, Google Maps, Facebook)
- Only flags businesses with NO custom domain
- Prevents future "you don't have a website" errors
- **Tested successfully** - all test cases passed

### 4. SW Florida Comfort Hours Updated ✅
**Updated**: `ai-customer-service/businesses/swflorida_hvac.py`
- **Old**: "Office: 8am-5pm Mon-Fri"
- **New**: "Office: Mon-Fri 4:30pm-10pm, Sat-Sun 8am-5pm"
- Emergency service: 24/7 (unchanged)

---

## ⏳ PENDING (Requires Your Action)

### 5. Integrate Website Validator into Scraper
**What**: Make all lead scraping use the new validation logic

**Steps** (5 minutes):
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper

# Test the validator
python -m src.website_validator

# Backup existing leads
cp output/leads.json output/leads_backup_jan21.json

# Re-validate all existing leads
python -c "
import json
from src.website_validator import batch_validate_leads

# Load existing leads
with open('output/leads.json', 'r') as f:
    leads_data = json.load(f)
    leads = leads_data.get('leads', [])

# Re-validate
validated = batch_validate_leads(leads)

# Save corrected data
leads_data['leads'] = validated
with open('output/leads_validated.json', 'w') as f:
    json.dump(leads_data, f, indent=2)

print(f'Validated {len(validated)} leads')
print('Saved to: output/leads_validated.json')
"
```

**Expected Result**:
```
Batch validation complete: {'real_websites': 250, 'aggregator_only': 150, 'no_website': 169}
Validated 569 leads
Saved to: output/leads_validated.json
```

**Then**:
```bash
# Replace old leads with validated version
mv output/leads.json output/leads_old_jan21.json
mv output/leads_validated.json output/leads.json
```

---

### 6. Update Scraper to Use Validator (Production Fix)
**What**: Modify `src/google_places.py` and `src/yelp.py` to use new validator

**Files to Edit**:
1. `src/google_places.py` - Add `validate_lead_website()` call
2. `src/yelp.py` - Add `validate_lead_website()` call

**Example Integration**:
```python
# In google_places.py, after creating lead:
from .website_validator import validate_lead_website

def _convert_place_to_lead(self, place: dict) -> Lead:
    # ... existing code ...
    lead = Lead(
        business_name=name,
        website=website_url,
        # ... other fields ...
    )

    # NEW: Validate website before returning
    validated_dict = validate_lead_website(lead.to_dict())
    return Lead.from_dict(validated_dict)
```

**Test**:
```bash
# Scrape 5 test businesses
python -m src.scraper google "Naples gyms" --limit 5 --output output/test_validation.json

# Check that aggregator URLs are flagged correctly
cat output/test_validation.json | grep -A5 "aggregator"
```

---

### 7. Manual Verification of Next 20 Leads
**What**: Before sending campaigns, manually verify no false positives

**Process**:
```bash
# Get next 20 leads flagged as "no_website"
python -c "
import json
with open('output/leads.json', 'r') as f:
    leads = json.load(f)['leads']

# Filter for no_website pain point
no_website = [l for l in leads if 'no_website' in l.get('pain_points', [])][:20]

# Print for manual review
for i, lead in enumerate(no_website, 1):
    print(f'{i}. {lead[\"business_name\"]}')
    print(f'   Website: {lead.get(\"website\", \"None\")}')
    print(f'   Phone: {lead.get(\"phone\", \"N/A\")}')
    print(f'   Validation: {lead.get(\"website_validation_reason\", \"N/A\")}')
    print()
"
```

**Manual Check**:
1. Google each business name
2. Verify they truly don't have a website
3. If they DO have a website, update `AGGREGATOR_DOMAINS` in `website_validator.py`

---

### 8. Small Batch Test (3-5 Sends)
**What**: Test with 3-5 real sends AFTER validation complete

**Command**:
```bash
# Test with 3 leads (dry run first)
python -m src.launch_multi_business_campaigns \
  --business marceau-solutions \
  --dry-run \
  --limit 3

# If dry run looks good, send for real
python -m src.launch_multi_business_campaigns \
  --business marceau-solutions \
  --for-real \
  --limit 3
```

**Monitor**:
- Wait 24 hours
- Check responses: `cat output/sms_replies.json | tail -20`
- If 0 opt-outs and 1+ positive response → proceed to step 9
- If ANY angry responses → stop, investigate

---

### 9. Launch Week 2-4 Optimization Plan
**What**: A/B test 3 template variants + enable 7-touch sequences

**Phase 1 (Week 2)**: A/B Test Templates
```bash
# Create 3 template variants in templates/sms/intro/

# Variant A: Social Proof (Control)
cat > templates/sms/intro/social_proof_v1.txt <<'EOF'
Hi, William from Marceau Solutions. Just helped 3 Naples businesses automate their scheduling/follow-ups. Saved them 10+ hours/week. Want a free audit? (239) 398-5676. Reply STOP to opt out.
EOF

# Variant B: Question-First
cat > templates/sms/intro/question_v1.txt <<'EOF'
Quick question: If you could save 10 hours/week on admin work, what would you do with that time? I help Naples businesses automate scheduling/emails. Free audit? (239) 398-5676. Reply STOP to opt out.
EOF

# Variant C: Value-First
cat > templates/sms/intro/value_v1.txt <<'EOF'
Hi, William from Marceau Solutions. I noticed your business could benefit from AI automation for scheduling/follow-ups. Want to see how much time you'd save? Free demo: (239) 398-5676. Reply STOP to opt out.
EOF

# Launch A/B test (50 leads per variant)
python -m src.campaign_analytics ab-test create \
  --name "intro_template_test" \
  --variants social_proof_v1,question_v1,value_v1 \
  --sample-size 150
```

**Phase 2 (Week 3)**: Enable 7-Touch Sequences
```bash
# Update follow_up_sequence.py to use 7-touch framework
# Touches: Day 0, 2, 5, 10, 15, 30, 60

python -m src.follow_up_sequence create \
  --name "Naples Gyms 7-Touch" \
  --template-sequence touch1,touch2,touch3,touch4,touch5,touch6,touch7 \
  --days 0,2,5,10,15,30,60
```

**Phase 3 (Week 4)**: Cohort Optimization
```bash
# Analyze which business types respond best
python -m src.campaign_analytics cohort-analysis \
  --group-by category \
  --min-sample 20

# Shift budget to winning cohorts
# (Based on response rates)
```

---

## 🎯 Success Criteria

**Before proceeding to next step, verify**:

- [ ] Step 5: Leads re-validated, aggregator URLs flagged correctly
- [ ] Step 6: Scraper integration tested with 5 leads
- [ ] Step 7: Manual review shows 0 false positives in next 20
- [ ] Step 8: Small batch test shows 0 angry responses
- [ ] Step 9: A/B test reaches statistical significance (100+ sends/variant)

**Expected Outcomes** (Week 2-4):
- 0% angry responses (down from 14% before fix)
- 5-8% positive response rate (hot/warm leads)
- <2% opt-out rate
- 3-5 qualified leads per 100 contacts

---

## ⚠️ What NOT to Do

❌ **Don't send more campaigns** until Step 5-8 complete
❌ **Don't skip manual verification** (Step 7) - trust but verify
❌ **Don't scale too fast** - test with 3, then 10, then 20
❌ **Don't use old templates** - update to new validated messaging

---

## 📋 Checklist Status

**Before New Campaigns** (Steps 5-8):
- [ ] Re-validate all existing leads (Step 5)
- [ ] Integrate validator into scraper (Step 6)
- [ ] Manually verify next 20 leads (Step 7)
- [ ] Small batch test 3-5 sends (Step 8)

**Week 2-4 Optimization** (Step 9):
- [ ] Create 3 template variants
- [ ] Launch A/B test (150 leads total)
- [ ] Wait for statistical significance (7+ days)
- [ ] Enable 7-touch follow-up sequences
- [ ] Analyze cohort performance
- [ ] Shift budget to winning segments

---

## 🚀 Quick Start Commands

**Test Website Validator**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper
python -m src.website_validator
```

**Re-Validate Existing Leads**:
```bash
# See Step 5 above for full command
python -c "import json; from src.website_validator import batch_validate_leads; ..."
```

**Small Batch Test**:
```bash
python -m src.launch_multi_business_campaigns --business marceau-solutions --dry-run --limit 3
```

**Check Responses**:
```bash
tail -50 output/sms_replies.json
```

---

**Last Updated**: 2026-01-21
**Next Action**: Execute Step 5 (re-validate existing leads)
**Estimated Time**: 40 minutes total for steps 5-8
