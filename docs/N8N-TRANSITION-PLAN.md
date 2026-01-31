# n8n Transition Plan

*Created: 2026-01-30*
*Status: In Progress*

## Executive Summary

This document outlines the strategy for transitioning existing Python-based automation workflows to n8n, leveraging its visual workflow builder, built-in integrations, and execution monitoring.

---

## Current State Analysis

### Existing n8n Workflows (5)

| Workflow | Nodes | Purpose | Status |
|----------|-------|---------|--------|
| TwiloInboundSMSHandler | 2 | Webhook + Twilio basic handler | Inactive |
| Naples Real Estate Lead Nurture | 5 | Grok-powered lead nurturing | Inactive |
| Ultimate Amazon Personal Assistant | 13 | AI agent with Google suite | Inactive |
| WhatsAppAgent | 6 | Scheduled WhatsApp via Grok | Inactive |
| MyAIagent | 7 | Chat-triggered Google assistant | Archived |

### Current Python Automation Systems (138 scripts)

| Category | Scripts | Key Files | Complexity |
|----------|---------|-----------|------------|
| **SMS Campaigns** | 8 | automation_daemon, sms_scheduler, follow_up_sequence, twilio_webhook | High |
| **Email** | 4 | email_scheduler, email_response_monitor | Medium |
| **Lead Management** | 6 | apollo_pipeline, apollo_to_clickup, lead_scoring | High |
| **Webhooks** | 4 | twilio_webhook, form_webhook, stripe_webhook_server | Medium |
| **Morning Digest** | 3 | digest_aggregator, morning_digest, routine_scheduler | Medium |
| **Social Media** | 5 | x_scheduler, content_generator, post_analytics | Medium |
| **Campaign Analytics** | 4 | campaign_analytics, campaign_monitor, campaign_auto_launcher | High |

---

## n8n Advantages vs Python Scripts

| Factor | n8n | Python Scripts |
|--------|-----|----------------|
| **Visual debugging** | ✅ See data flow | ❌ Log reading |
| **Error handling** | ✅ Built-in retries | ⚠️ Manual implementation |
| **Scheduling** | ✅ Native cron UI | ⚠️ System cron |
| **Webhooks** | ✅ Instant endpoints | ⚠️ Need web server |
| **Integrations** | ✅ 400+ nodes | ⚠️ Manual API calls |
| **Execution history** | ✅ Full logs | ⚠️ File-based logs |
| **Complex logic** | ⚠️ Limited | ✅ Full Python power |
| **ML/AI processing** | ⚠️ Basic | ✅ Full libraries |
| **Statistical analysis** | ❌ Not suited | ✅ pandas, numpy |

---

## Transition Decision Matrix

### MIGRATE TO n8n (High Priority)

| Workflow | Current | n8n Benefit | Priority |
|----------|---------|-------------|----------|
| **SMS Inbound Webhook** | twilio_webhook.py | Existing workflow, just enhance | P1 |
| **Form Submission Handler** | form_webhook.py | Native webhook + sheets + ClickUp nodes | P1 |
| **Morning Digest** | morning_digest.py | Schedule + Gmail + aggregation | P1 |
| **Follow-up Sequences** | follow_up_sequence.py | Wait nodes perfect for multi-day | P2 |
| **Stripe Webhooks** | stripe_webhook_server.py | Native Stripe trigger | P2 |
| **Email Response Monitor** | email_response_monitor.py | Gmail trigger node | P2 |

### KEEP IN PYTHON (Complex Logic)

| Workflow | Reason |
|----------|--------|
| **Lead Scoring** | ML-based scoring with weighted algorithms |
| **Campaign Analytics** | Statistical significance calculations, A/B testing |
| **Apollo Pipeline** | Complex enrichment logic, deduplication |
| **Video Generation** | Shotstack API with template processing |
| **Campaign Auto-Launcher** | Multi-agent coordination, complex state |

### HYBRID APPROACH (n8n triggers Python)

| Workflow | n8n Role | Python Role |
|----------|----------|-------------|
| **SMS Campaigns** | Scheduling, webhook handling | Template rendering, compliance checks |
| **Lead Management** | ClickUp sync, notifications | Scoring, enrichment |
| **Social Media** | Scheduling, posting | Content generation |

---

## Implementation Plan

### Phase 1: Enhance Existing n8n Workflows (Week 1)

#### 1.1 Upgrade TwiloInboundSMSHandler
**Current**: Basic webhook + Twilio (2 nodes)
**Target**: Full response handler with categorization and actions

```
Webhook → Function (categorize) → Switch
  ├─ Hot Lead → Google Sheets + ClickUp + Email Alert
  ├─ Warm Lead → Google Sheets + Follow-up Queue
  ├─ Opt Out → Google Sheets + Remove from sequences
  └─ Unknown → Google Sheets + Manual Review Flag
```

#### 1.2 Activate Naples Real Estate Lead Nurture
- Review and test current workflow
- Add error handling
- Connect to production Twilio

### Phase 2: New High-Priority Workflows (Week 2)

#### 2.1 Form Submission Handler
```
Webhook (form submit)
  → Validate Data
  → Google Sheets (log)
  → Switch (lead quality)
    ├─ High → ClickUp Task + SMS Alert + Email
    └─ Low → Google Sheets only
```

#### 2.2 Morning Digest Workflow
```
Schedule Trigger (8 AM daily)
  → Gmail (fetch unread, last 24h)
  → Google Sheets (get campaign stats)
  → Function (aggregate & format)
  → Gmail (send digest email)
```

#### 2.3 Follow-Up Sequence Engine
```
Webhook (enroll lead)
  → Google Sheets (add to sequence)
  → Wait (2 days)
  → Twilio (send follow-up 1)
  → Wait (3 days)
  → Twilio (send follow-up 2)
  → ... (continue 7-touch sequence)
```

### Phase 3: Integration Workflows (Week 3)

#### 3.1 Stripe Payment Handler
```
Stripe Trigger (payment.succeeded)
  → Google Sheets (log payment)
  → Gmail (send receipt)
  → ClickUp (update customer status)
```

#### 3.2 Email Response Monitor
```
Gmail Trigger (new email)
  → Function (categorize sender)
  → Switch
    ├─ Lead Response → Google Sheets + Alert
    ├─ Customer → ClickUp Task
    └─ Other → Archive
```

### Phase 4: Hybrid Python-n8n Integration (Week 4)

#### 4.1 n8n → Python Bridge
Create HTTP endpoints in Python for complex operations:
- `/api/score-lead` - Lead scoring
- `/api/enrich-lead` - Apollo enrichment
- `/api/analyze-campaign` - Statistical analysis

n8n calls these via HTTP Request node when needed.

#### 4.2 Python → n8n Bridge
Python scripts can trigger n8n workflows via webhook:
```python
import requests
requests.post('http://localhost:5678/webhook/trigger-followup', json=lead_data)
```

---

## Priority 1 Workflows to Build NOW

### 1. Enhanced SMS Response Handler

**Workflow Name**: `SMS-Response-Handler-v2`
**Trigger**: Webhook (Twilio inbound)
**Nodes**:
1. Webhook - Receive Twilio POST
2. Set - Extract phone, message, timestamp
3. HTTP Request - Call Python categorization API (optional)
4. Switch - Route by category
5. Google Sheets - Log all responses
6. IF Hot Lead:
   - ClickUp - Create task
   - Gmail - Send alert
   - Set - Mark for immediate follow-up
7. IF Opt Out:
   - Google Sheets - Add to opt-out list
   - HTTP Request - Remove from all sequences

### 2. Form-to-CRM Pipeline

**Workflow Name**: `Form-Submission-Pipeline`
**Trigger**: Webhook (form POST)
**Nodes**:
1. Webhook - Receive form data
2. Set - Normalize fields
3. Google Sheets - Log submission
4. Switch - By lead quality (based on fields)
5. ClickUp - Create task (high quality only)
6. Twilio - Send confirmation SMS
7. Gmail - Send internal notification

### 3. Daily Operations Digest

**Workflow Name**: `Daily-Operations-Digest`
**Trigger**: Schedule (8:00 AM EST)
**Nodes**:
1. Schedule Trigger
2. Gmail - Fetch unread (last 24h)
3. Google Sheets - Get campaign metrics
4. Google Sheets - Get new leads
5. Function - Aggregate all data
6. Gmail - Send digest email

---

## Credentials Required

| Service | n8n Credential Type | Status |
|---------|---------------------|--------|
| Twilio | Twilio API | ✅ Exists |
| Google Sheets | Google OAuth2 | ✅ Exists |
| Gmail | Google OAuth2 | ✅ Exists |
| ClickUp | ClickUp API | ⚠️ Need to add |
| Stripe | Stripe API | ⚠️ Need to add |
| Grok/XAI | HTTP Header Auth | ✅ Exists |

---

## Success Metrics

| Metric | Current (Python) | Target (n8n) |
|--------|------------------|--------------|
| Workflow visibility | Low (logs) | High (UI) |
| Error recovery | Manual | Automatic retries |
| Setup time for new workflow | 2-4 hours | 30-60 min |
| Debugging time | 30-60 min | 5-10 min |
| Scheduled task reliability | 95% | 99%+ |

---

## Migration Checklist

- [ ] Phase 1: Enhance existing n8n workflows
  - [ ] Upgrade TwiloInboundSMSHandler
  - [ ] Activate Naples Real Estate workflow
- [ ] Phase 2: Build new high-priority workflows
  - [ ] Form Submission Pipeline
  - [ ] Morning Digest
  - [ ] Follow-up Sequence Engine
- [ ] Phase 3: Integration workflows
  - [ ] Stripe Payment Handler
  - [ ] Email Response Monitor
- [ ] Phase 4: Python-n8n bridge
  - [ ] Create Python API endpoints
  - [ ] Connect n8n HTTP nodes

---

## Files Reference

**Python scripts to eventually deprecate** (after n8n migration):
- `projects/shared/lead-scraper/src/twilio_webhook.py` → n8n webhook
- `projects/shared/lead-scraper/src/form_webhook.py` → n8n webhook
- `projects/shared/personal-assistant/src/morning_digest.py` → n8n scheduled
- `execution/stripe_webhook_server.py` → n8n Stripe trigger

**Python scripts to KEEP** (complex logic):
- `projects/shared/lead-scraper/src/lead_scoring.py`
- `projects/shared/lead-scraper/src/campaign_analytics.py`
- `projects/shared/lead-scraper/src/apollo_pipeline.py`
- `execution/shotstack_api.py`
