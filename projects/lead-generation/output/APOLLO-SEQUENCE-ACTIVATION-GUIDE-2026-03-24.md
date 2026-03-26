# Apollo.io Sequence Activation Guide
**Date:** March 24, 2026
**Sprint:** 14-Day AI Client Sprint (Mar 23 – Apr 5)
**Goal:** Activate 5 email sequences covering 67 immediately sendable prospects + 64 pending reveal

---

## Status Summary

| Category | Count | Action Required |
|----------|-------|-----------------|
| Ready to send (email confirmed) | **67** | Load into sequences NOW |
| Apollo-found, email requires credit reveal | **64** | Optional — see Step 0 below |
| Total pipeline | **131** | |

---

## Master Prospect Count by Segment (Ready to Send)

| Segment | Prospects with Email |
|---------|---------------------|
| Property Management / Real Estate | 21 |
| Other | 17 |
| Dental / Medical / Healthcare | 16 |
| HVAC / Air Conditioning | 4 |
| Roofing | 3 |
| Electrical | 2 |
| Smart Home / Technology | 2 |
| Plumbing | 1 |
| Pest Control | 1 |
| **TOTAL READY** | **67** |

---

## Step 0 (Optional): Decide on Apollo Credit Reveals — 64 Additional Contacts

Apollo's search API found 64 new owner/decision-maker contacts across thin segments. All 64 have confirmed emails in Apollo (`has_email: true`) but revealing the actual email requires spending Apollo credits (~1 credit per contact).

| Segment | Apollo Found | Has Email Flag |
|---------|-------------|----------------|
| Plumbing | 18 | 18 |
| Roofing | 19 | 19 |
| Landscaping / Lawn | 12 | 12 |
| Legal | 10 | 10 |
| Pest Control | 5 | 5 |
| **TOTAL** | **64** | **64** |

Raw data saved to:
```
projects/shared/lead-scraper/output/apollo_new_prospects_2026-03-24.json
```

**To reveal emails in Apollo UI (if you choose to spend the credits):**
1. In Apollo, go to **People** → **Saved Lists** or **Search**
2. Filter by the companies/names from the JSON file above
3. Select contacts → **Export** or click the email icon → Apollo charges credits and reveals email
4. Download the enriched CSV and re-add to the master sendable list

**Recommendation for the sprint:** The 67 confirmed contacts are enough to start. Reveal Plumbing (18) and Roofing (19) first since those are hot service trades with clear pain points.

---

## Step 1: Log In and Navigate to Sequences

1. Go to [https://app.apollo.io](https://app.apollo.io)
2. Log in with your Marceau Solutions credentials
3. In the left sidebar, click **Engage** → **Sequences**
4. You'll land on the Sequences dashboard

---

## Step 2: Create 5 Sequences

Create (or activate if already existing) these 5 sequences:

| Sequence Name | Target Segment | Ready Contacts |
|---------------|----------------|----------------|
| General AI Services | Property Management + Other + Electrical + Smart Home | 42 |
| HVAC AI Automation | HVAC / Air Conditioning | 4 |
| Plumbing AI Automation | Plumbing | 1 |
| Med Spa & Healthcare AI | Dental / Medical / Healthcare | 16 |
| Roofing AI Automation | Roofing | 3 |

**For each sequence:**
1. Click **+ New Sequence** (top right)
2. Name it as shown above
3. Set **Type:** Active
4. Set **Timezone:** Eastern Time (US & Canada)

---

## Step 3: Set Up the 3-Step Email Cadence

For **each** sequence, add 3 email steps:

### Step 1 — Day 0 (Send immediately on enrollment)
- Click **+ Add Step** → **Email**
- **Delay:** 0 days
- **Subject line by sequence:**
  - General: `Quick question about {{company_name}}'s lead follow-up`
  - HVAC: `AI for HVAC service calls — 30 seconds to read`
  - Plumbing: `How Naples plumbers are automating missed calls`
  - Med Spa/Healthcare: `AI scheduling for {{company_name}} — worth 2 minutes?`
  - Roofing: `Naples roofing owners are trying this — thought of you`

### Step 2 — Day 3
- Click **+ Add Step** → **Email**
- **Delay:** 3 days after Step 1
- **Subject:** `Following up — AI automation for {{company_name}}`
- **Body focus:** Value prop — specific ROI for their trade, time saved, missed calls automated, "we handle the tech, you focus on the work"

### Step 3 — Day 7
- Click **+ Add Step** → **Email**
- **Delay:** 7 days after Step 2
- **Subject:** `Last note — free 2-week trial for {{company_name}}`
- **Body focus:** Final CTA with free onboarding offer, Calendly link, low-pressure close ("if timing isn't right, no worries — keeping this short out of respect for your day")

**For each step:**
- Click step → **Edit**
- Set **From:** William Marceau `wmarceau@marceausolutions.com`
- Add personalization tokens: `{{first_name}}`, `{{company_name}}`

---

## Step 4: Add Prospects to Each Sequence

The master sendable list is at:
```
projects/shared/lead-scraper/output/master_sendable_2026-03-24.json
```

**CSV Import method (recommended):**

Build a CSV for each segment with columns: `first_name`, `last_name`, `email`, `company_name`, `title`, `website`

In Apollo per sequence:
1. Open the sequence → click **Add People** → **Import CSV**
2. Map columns and import

**Segment routing:**

| Segment in JSON | Apollo Sequence |
|----------------|----------------|
| HVAC / Air Conditioning | HVAC AI Automation |
| Plumbing | Plumbing AI Automation |
| Dental / Medical / Healthcare | Med Spa & Healthcare AI |
| Roofing | Roofing AI Automation |
| Property Management / Real Estate | General AI Services |
| Other | General AI Services |
| Electrical | General AI Services |
| Smart Home / Technology | General AI Services |
| Pest Control | General AI Services |

---

## Step 5: Connect SendGrid for Email Delivery

1. In Apollo: **Settings** (gear icon, bottom left) → **Integrations** → **Email**
2. Under **Email Provider**, select **SendGrid**
3. Paste your SendGrid API key (from `.env` → `SENDGRID_API_KEY`)
4. Click **Verify**
5. Under **Sending Domain**, enter `marceausolutions.com`
6. Apollo shows DNS records to add — add them in Cloudflare (or your registrar)
7. Click **Verify Domain** — DNS propagation takes up to 24 hrs

**From address:** `wmarceau@marceausolutions.com`

---

## Step 6: Configure Sending Limits

In **Settings** → **Email Settings** (also configurable per-sequence):

| Setting | Value |
|---------|-------|
| Max emails per day | **50** (conservative to protect sender reputation) |
| Sending window | **9:00 AM – 5:00 PM EST only** |
| Days to send | **Monday – Friday only** |
| Min time between emails | **2 minutes** |

After 2 weeks, if deliverability is healthy (bounce rate < 2%, spam rate < 0.1%), increase to 100/day.

---

## Step 7: Activate Sequences

1. **Engage** → **Sequences**
2. For each sequence: click sequence name → **Settings** → toggle **Active** to ON
3. Verify each sequence shows a green **Active** badge
4. Confirm enrolled contacts appear in the sequence dashboard

---

## Step 8: Monitor Daily

| Metric | Target | Action if Off |
|--------|--------|---------------|
| Open rate | > 40% | Test new subject lines |
| Reply rate | > 5% | Test offer / email body |
| Bounce rate | < 2% | Pause and clean list |
| Unsubscribes | < 1% | Review targeting |

---

## Key Links

- **AI Services Discovery Call:** `https://calendly.com/wmarceau/ai-services-discovery`
- **Free 2-week onboarding offer:** Reference the marceausolutions.com AI services page
- **Apollo dashboard:** `https://app.apollo.io`

---

## File Reference

| File | Contents |
|------|---------|
| `master_sendable_2026-03-24.json` | 67 contacts with confirmed emails, grouped by segment |
| `apollo_new_prospects_2026-03-24.json` | 64 Apollo-found contacts (emails locked behind credit reveal) |
| `hunter_enrichment_run2_2026-03-24.json` | Hunter run 2 (0 new; searched 27 domains, none had indexed emails) |
| `hunter_full_enrichment_2026-03-23.json` | Previous Hunter run (11 emails, already merged into master list) |

---

## Hard Rules (Do Not Violate)

- **No cold SMS** — TCPA rules. Email + phone calls only for first contact.
- **No Apollo credit spend** unless you explicitly decide to reveal the 64 flagged contacts.
- **Opt-outs:** Honor all unsubscribes immediately. Apollo handles this automatically.
- **Sprint timeline:** Mar 23 – Apr 5. Goal: 1 signed AI services client before April 6 job start.

---

*Generated by Claude Code on 2026-03-24 for William Marceau's AI client sprint.*
