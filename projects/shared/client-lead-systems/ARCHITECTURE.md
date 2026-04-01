# Client Lead Management Systems

## Overview
Reusable lead management infrastructure deployable for Marceau Solutions clients.
Each client gets their own isolated lead funnel with:
- Webhook intake (n8n)
- Lead storage (Google Sheets per client)
- Automated email sequences
- Abandonment recovery
- Optional SMS follow-ups

## Directory Structure
```
client-lead-systems/
├── ARCHITECTURE.md          # This file
├── templates/               # Reusable workflow templates
│   ├── signup-workflow.json
│   ├── abandon-workflow.json
│   └── drip-sequence.json
├── boabfit/                 # First client implementation
│   ├── config.json          # Client-specific settings
│   ├── email-templates/     # HTML email templates
│   └── sequences/           # Drip campaign definitions
└── [future-client]/         # Additional clients
```

## BoabFit Implementation
- **Product**: 6-Week Barbie Body Program
- **Signup Webhook**: /webhook/boabfit-signup
- **Abandon Webhook**: /webhook/boabfit-abandon
- **Lead Sheet**: Google Sheets (BoabFit Leads)
- **Email From**: julia@boabfit.com (or configured sender)

## Email Sequences
### Signup Sequence
1. Immediate: Welcome + Program Access
2. Day 1: Getting Started Guide
3. Day 3: Check-in + Tips
4. Day 7: Motivation + Progress Check
5. Day 14: Halfway point celebration
6. Day 30: Completion + Upsell

### Abandon Sequence
1. +1 hour: "You didn't finish signing up"
2. +24 hours: "Still thinking about it?"
3. +72 hours: Final reminder with urgency
