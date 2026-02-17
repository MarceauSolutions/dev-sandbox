# parcelLab — Demand Gen Automation Project

## What This Is

Productized automation solution targeting parcelLab's open Demand Gen & Growth Marketer role. Instead of applying for the $19.50/hr marketing position, we're building the automation system that does 60-70% of that role's work and pitching it as a service.

## Goal

1. Build demo automation stack (n8n workflows) mapped to their job description
2. Pitch to Zack Hamilton (SVP, Head of Growth Strategy & Enablement)
3. Close as a $5K build + $1.5K/mo maintenance engagement
4. Use as case study for future demand gen automation sales

## Key Files

| File | Purpose |
|------|---------|
| `research/company-intel.md` | Company research, org chart, pitch targets |
| `automation/architecture/demand-gen-automation-architecture.md` | Full system architecture + build plan |
| `demos/` | n8n workflow exports for demo |
| `outreach/` | LinkedIn messages, emails, pitch deck |

## Pitch Targets (Priority Order)

1. **Zack Hamilton** — SVP, Head of Growth Strategy & Enablement (owns growth in US)
2. **Hiring manager for Demand Gen role** — likely reports to Zack or interim marketing lead
3. **Anton Eder** — Co-Founder & COO (if growth team doesn't respond)

## Context

- parcelLab's CMO (Noel Hamill) left late 2025
- They're hiring 3+ marketing roles simultaneously (Director of Demand Centre, Demand Gen Marketer, ABM Manager)
- US marketing function is being built/rebuilt — they need automation more than headcount right now
- Company: ~177 employees, 1000+ brands, post-purchase experience platform
- Backed by Insight Partners

## Build Plan

**Phase 1 (Demo — build first):**
1. Event lead capture workflow (webhook → Clay → HubSpot → sequence)
2. CRM sync engine (HubSpot ↔ Salesforce)
3. AI lead scorer (Claude API)

**Phase 2 (If engaged):**
4. UTM attribution tracker
5. Data hygiene engine
6. Campaign reporting aggregator

## Apollo Enrichment

Use existing Apollo tools to find:
- Zack Hamilton email + LinkedIn at parcelLab
- US marketing team contacts
- Hiring manager identification
