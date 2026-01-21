# Apollo.io Lead Scoring Guide

**Purpose**: Manually score leads 1-10 to identify top 20% for contact enrichment

**Time**: ~30 seconds per lead (25 minutes for 50 leads)

---

## Quick Scoring System

### 🔟 Score 10 (Highest Priority)
**Characteristics**:
- ❌ No website at all
- ❌ Or website returns 404/broken
- ✅ Phone visible on Google/Yelp
- ✅ Active business (recent reviews)
- ✅ Good reputation (4+ stars)

**Pain Point**: "You're losing customers who can't find you online"

**Example**: Local gym with 50 Google reviews, 4.8 stars, phone listed, but no website when you Google their name

---

### 9️⃣ Score 9 (Very High Priority)
**Characteristics**:
- ⚠️ Has website BUT it's just a Facebook page
- ⚠️ Or 1-page site with phone/address only
- ❌ No online booking
- ❌ No way to schedule appointments
- ✅ Active on social media

**Pain Point**: "Your website isn't capturing leads while you sleep"

**Example**: Yoga studio with Facebook page but no booking calendar, posts daily

---

### 8️⃣ Score 8 (High Priority)
**Characteristics**:
- ✅ Has basic website
- ❌ No online booking/scheduling
- ❌ No contact form
- ⚠️ Phone number hard to find
- ⚠️ Mobile unfriendly

**Pain Point**: "You're making customers work too hard to give you money"

**Example**: CrossFit gym with basic site listing classes, but must call to sign up

---

### 7️⃣ Score 7 (Medium-High Priority)
**Characteristics**:
- ✅ Decent website
- ⚠️ Has booking but it's third-party (Mindbody, Vagaro)
- ⚠️ Sends customers to another site
- ✅ Phone visible

**Pain Point**: "Why pay 3rd party fees when you could own the experience?"

**Example**: Pilates studio using Mindbody ($100+/month), could save with custom booking

---

### 6️⃣ Score 6 (Medium Priority)
**Characteristics**:
- ✅ Good website
- ✅ Has booking system
- ⚠️ BUT missing automation opportunities:
  - No reminder texts
  - No abandoned cart recovery
  - No lead magnets
  - No email capture

**Pain Point**: "You built the funnel but you're not optimizing it"

**Example**: Boutique fitness with online booking but 20% no-show rate (no reminders)

---

### 5️⃣ Score 5 or Lower (Low Priority - Don't Enrich)
**Characteristics**:
- ✅ Modern website with booking
- ✅ Automated reminders
- ✅ Good online presence
- ✅ Email marketing visible
- ⚠️ May still need Voice AI or content automation

**Pain Point**: "They're doing well - harder to convince"

**Example**: Orange Theory Fitness - corporate, has everything

---

## Fast Scoring Checklist

**Visit website and answer 5 questions (30 seconds)**:

| Question | Yes = +2 points | No = -2 points |
|----------|----------------|---------------|
| 1. Does website exist and load? | | ✅ +2 if NO |
| 2. Can I book online in <10 seconds? | ✅ +2 if NO | |
| 3. Is phone number visible above fold? | ✅ +2 if NO | |
| 4. Do they have <20 Google reviews? | ✅ +2 if YES | |
| 5. Does site mention "call to book"? | ✅ +2 if YES | |

**Base score**: 5 (start here)

**Add points for pain points**:
- No website: +5 (total = 10)
- No booking: +3 (total = 8)
- Third-party booking: +2 (total = 7)
- Poor mobile experience: +1
- Mentions missed calls in reviews: +2

**Subtract points for strong indicators**:
- Corporate chain: -3
- Multiple locations with centralized system: -2
- Evidence of recent tech upgrade: -2
- Active email marketing visible: -1

---

## Real Examples (Scored)

### Example 1: CrossFit Naples
**Visit**: Google "CrossFit Naples" → https://crossfitnaples.com

**Observations**:
- ✅ Website exists
- ❌ No online booking (must call or visit)
- ✅ Phone: (239) 263-8122 visible
- ✅ 42 Google reviews, 4.9 stars
- ⚠️ Mentions "call to schedule intro session"

**Score**: 8/10
**Reason**: Good website but no online booking = friction
**Pitch**: "Add online booking, reduce phone calls by 50%"

---

### Example 2: Planet Fitness
**Visit**: Google "Planet Fitness Naples"

**Observations**:
- ✅ Corporate website with online signup
- ✅ Mobile app for bookings
- ✅ Automated everything
- ⚠️ Corporate - won't have decision-making power

**Score**: 2/10
**Reason**: Corporate, fully automated, no local decision maker
**Action**: SKIP - Don't waste credits

---

### Example 3: Naples Yoga Shala
**Visit**: Google "Naples Yoga Shala" → Facebook page only

**Observations**:
- ❌ No website (404 when clicking Google link)
- ✅ Active Facebook page with posts
- ✅ Phone: (239) 692-9747
- ✅ 18 Google reviews, 5.0 stars
- ⚠️ "Message us on Facebook to book"

**Score**: 10/10
**Reason**: No website at all, relying on Facebook
**Pitch**: "Your competitor shows up first because they have a website"

---

## Scoring Spreadsheet Template

Save as `apollo_scored_leads.csv`:

```csv
Business Name,Website,Score,Pain Points,Notes
CrossFit Naples,crossfitnaples.com,8,"no_booking","Good site, must call to join"
Planet Fitness,planetfitness.com,2,"corporate","Skip - corporate chain"
Naples Yoga Shala,facebook.com/...,10,"no_website","Only Facebook page"
```

---

## After Scoring (Import Back to Claude)

**Filter for top 20%** (scores 8-10):
```bash
python -m src.apollo_import filter \
  --input apollo_scored_leads.csv \
  --min-score 8 \
  --output apollo_top_leads.json
```

**Return to Apollo.io** and reveal contacts for ONLY the top 20%:
- Saves 80% of credits
- Targets highest-value leads
- Better conversion rates

---

## Common Mistakes to Avoid

❌ **Don't score based on**:
- How much you personally like their business
- Whether you'd use their service
- Social media follower count (vanity metric)

✅ **Do score based on**:
- Tangible pain points we can solve
- Budget indicators (tech stack, employees, reviews)
- Accessibility (can we reach the owner?)
- Urgency (are they actively losing business?)

---

## Time-Saving Tips

**Use these keyboard shortcuts**:
1. Google business name + city
2. Right-click website → "Open in new tab"
3. Scan for booking button (10 seconds)
4. Check reviews for "hard to reach" mentions
5. Score and close tab
6. Repeat

**Goal**: 50 leads in 25-30 minutes

---

**Next**: After scoring, return scored CSV to Claude for automated enrichment and campaign launch
