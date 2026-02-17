# Demand Gen Automation Architecture — parcelLab

## Overview

Automated system that replaces 60-70% of the manual tooling work described in parcelLab's "Demand Generation & Growth Marketer USA" job posting. Built on n8n with integrations to HubSpot, Clay, Salesforce, and AI tools.

## What We're Automating (Mapped to Job Description)

### 1. Campaign Execution Automation

| JD Requirement | Automation | n8n Workflow |
|---------------|------------|--------------|
| Multi-channel campaign execution (paid, email, ABM) | Trigger-based campaign orchestration — new lead enters CRM → auto-enrolled in correct sequence | `wf-campaign-orchestrator` |
| Email and outreach workflows via HubSpot | HubSpot API: create/update contacts, enroll in sequences, trigger workflows | `wf-hubspot-sequence-manager` |
| Event lead capture → follow-up | Webhook receives event scan data → enriches via Clay → creates HubSpot contact → triggers nurture sequence | `wf-event-lead-capture` |
| Drive ABM activations, direct mail, gifting | ABM account list → trigger personalized outreach flows per tier | `wf-abm-activation-engine` |

### 2. Marketing Automation & Tooling

| JD Requirement | Automation | n8n Workflow |
|---------------|------------|--------------|
| Build automation flows across Clay, HubSpot, Salesforce | n8n as orchestration layer connecting all three via API | `wf-crm-sync-engine` |
| UTM tracking + CRM sync | Auto-append UTMs to all campaign links, sync attribution data to Salesforce | `wf-utm-attribution-tracker` |
| Campaign tracking via pixels | Webhook listener for conversion events → update campaign records | `wf-conversion-tracker` |
| Notion marketing board alignment | n8n → Notion API: auto-update task status, deadlines, campaign metrics | `wf-notion-board-sync` |

### 3. ABM & Sales Alignment

| JD Requirement | Automation | n8n Workflow |
|---------------|------------|--------------|
| ABM landing page personalization | Dynamic content injection based on account data from Salesforce/6Sense | `wf-abm-personalization` |
| Personalized outreach flows | Account tier → template selection → Clay enrichment → HubSpot sequence | `wf-personalized-outreach` |
| Deal acceleration for Tier 1 accounts | Trigger alerts to AEs when target accounts show intent signals | `wf-intent-signal-alerts` |

### 4. Reporting & Optimization

| JD Requirement | Automation | n8n Workflow |
|---------------|------------|--------------|
| Performance reporting across channels | Aggregate data from HubSpot, Google Ads, LinkedIn Ads → unified dashboard | `wf-campaign-reporting` |
| Pipeline influence tracking | Match campaign touches to Salesforce opportunities → attribution model | `wf-pipeline-attribution` |
| Data hygiene and enrichment | Scheduled Clay enrichment runs, dedup logic, field standardization | `wf-data-hygiene-engine` |

### 5. AI-Powered Enhancements (Differentiator)

| Capability | How It Works | n8n Workflow |
|-----------|-------------|--------------|
| Lead scoring with LLM | Claude API analyzes firmographic + behavioral data → score 1-10 | `wf-ai-lead-scorer` |
| Email copy optimization | Claude generates A/B variants, selects winner based on engagement data | `wf-ai-copy-optimizer` |
| Campaign brief → execution | Natural language campaign brief → auto-generates UTMs, sequences, targeting | `wf-ai-campaign-builder` |
| Intent signal classification | Classify website visits, content downloads, email engagement into intent tiers | `wf-ai-intent-classifier` |

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    n8n (Orchestrator)                │
│                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  Triggers    │  │  AI Layer    │  │ Reporting  │  │
│  │  - Webhooks  │  │  - Claude    │  │ - Agg      │  │
│  │  - Cron      │  │  - Scoring   │  │ - Dashboard│  │
│  │  - CRM events│  │  - Copy Gen  │  │ - Alerts   │  │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘  │
│         │                 │                │         │
└─────────┼─────────────────┼────────────────┼─────────┘
          │                 │                │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │  HubSpot  │    │   Clay    │    │ Salesforce│
    │  - Contacts│    │  - Enrich │    │  - Opps   │
    │  - Sequences│   │  - Score  │    │  - Pipeline│
    │  - Email   │    │  - Clean  │    │  - Reports │
    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
          │                │                │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │ LinkedIn  │    │  Notion   │    │  Google   │
    │  Ads API  │    │  Board    │    │  Ads API  │
    └───────────┘    └───────────┘    └───────────┘
```

## Demo Build Plan (What We Build Before Pitching)

### Phase 1: Core Demo (Week 1) — Build These First

1. **`wf-event-lead-capture`** — Most visual, easy to demo
   - Webhook → Clay enrichment → HubSpot contact creation → Sequence enrollment
   - Demo: "Scan a badge at a trade show → 30 seconds later they're in a personalized email sequence"

2. **`wf-crm-sync-engine`** — Shows technical depth
   - Bi-directional sync between HubSpot ↔ Salesforce
   - Field mapping, dedup logic, conflict resolution

3. **`wf-ai-lead-scorer`** — The "wow" factor
   - Claude API analyzes lead data → scores 1-10 with reasoning
   - "Here's why this lead scored 9: VP-level, company matches ICP, visited pricing page 3x"

### Phase 2: Supporting Workflows (Week 2) — If They're Interested

4. **`wf-utm-attribution-tracker`** — Solves real pain
5. **`wf-data-hygiene-engine`** — Saves hours/week
6. **`wf-campaign-reporting`** — Aggregated dashboard

### Phase 3: Advanced (Post-Engagement)

7. ABM personalization engine
8. AI copy optimization
9. Intent signal classification

## Tech Stack

| Component | Tool | Cost |
|-----------|------|------|
| Orchestration | n8n (self-hosted on EC2) | ~$20/mo EC2 |
| CRM | HubSpot API (their existing) | $0 (their account) |
| Enrichment | Clay API (their existing) | $0 (their account) |
| CRM | Salesforce API (their existing) | $0 (their account) |
| AI | Claude API (our account for demo) | ~$2-5 for demo |
| Project tracking | Notion API (their existing) | $0 (their account) |

**Total demo build cost: <$30**

## Pricing Model (For Pitch)

| Option | What They Get | Price |
|--------|--------------|-------|
| **Build** | Full automation stack (Phase 1-2), documentation, handoff | $5,000 one-time |
| **Build + Maintain** | Build + monthly maintenance, monitoring, optimization | $5,000 + $1,500/mo |
| **Fractional** | Ongoing automation engineering, 20 hrs/mo | $3,000/mo |

## ROI Argument

- Demand Gen Marketer salary: $40K/yr ($19.50/hr)
- 60-70% of that role's time is tooling/plumbing work
- Automation cost: $5K build + $1.5K/mo = $23K/yr
- **Net savings: $17K/yr + the marketer focuses on strategy**
- Or: they hire FEWER people and spend budget on tools/ads instead

## Files to Create

- [ ] `demos/event-lead-capture-demo.json` — n8n workflow export
- [ ] `demos/crm-sync-demo.json` — n8n workflow export
- [ ] `demos/ai-lead-scorer-demo.json` — n8n workflow export
- [ ] `outreach/pitch-deck.md` — Slide outline for Zack Hamilton
- [ ] `outreach/cold-message-linkedin.md` — LinkedIn DM template
- [ ] `outreach/cold-email.md` — Email template
