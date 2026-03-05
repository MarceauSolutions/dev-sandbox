# Business Integration Protocol

> How Marceau Solutions' business units work together symbiotically.
> Each business is an expert in its domain. When a client in one business needs something from another, the handoff is automated and seamless.

## Business Units

| Unit | Expertise | Hub |
|------|-----------|-----|
| **PT Coaching** | Fitness, peptides, nutrition, accountability | `projects/marceau-solutions/pt-business/` |
| **Web Development** | Websites, DNS, hosting, online presence | `projects/marceau-solutions/web-dev/` |
| **Content/Social** | Social media, video, brand content | `projects/shared/social-media-automation/` |

## Cross-Business Referral Flows

### PT Client Needs a Website

```
PT Business identifies need (client wants online presence)
  |
  v
Handoff to Web Dev
  - Auto-create project in projects/{client}/
  - Apply PT client discount (25% off build)
  - Web Dev onboarding workflow starts
  - PT hub gets notified of project status
  |
  v
Web Dev builds + deploys
  - Website includes PT-specific pages (testimonials, before/after)
  - Forms route to existing n8n pipelines
  - DNS setup SOP runs
  |
  v
Handoff back to PT
  - PT business gets the website URL for client portal
  - Client's coaching page can link to their website
  - Monthly web dev check-in syncs with PT Monday check-in
```

### Web Dev Client Needs Fitness Content

```
Web Dev client asks about fitness features
  |
  v
Handoff to PT Business
  - Fitness landing page template applied
  - Workout/nutrition content generated via PT tools
  - Stripe coaching payment link embedded
  |
  v
PT Business handles ongoing
  - Client becomes dual client (web dev + coaching)
  - Single Twilio thread — both businesses communicate via same number
  - Google Sheet tracks both relationships
```

### Both Businesses Generate Content

```
PT creates fitness content (workout videos, peptide education)
  |
  v
Content/Social distributes
  - X/YouTube/IG posting via social-media-automation
  - Content drives traffic to marceausolutions.com
  |
  v
Website captures leads
  - Lead magnet → nurture sequence → coaching OR web dev offer
  - Lead source tracked in Google Sheets
```

## Integration Points

### 1. Shared Client Record (Google Sheets)

One master sheet with tabs per business:
- **PT Clients** tab — coaching status, check-ins, billing
- **Web Dev Clients** tab — project status, domain, hosting
- **Cross-Referrals** tab — tracks handoffs between businesses

### 2. Shared Communication (Twilio)

- Same toll-free number for both businesses
- Templates prefixed by business: `coaching_*` vs `webdev_*`
- Inbound SMS routed by `SMS-Response-Handler-v2` (categorizes by keyword)
- Client sees ONE conversation thread regardless of which business is talking

### 3. Shared Billing (Stripe)

- PT: Subscriptions ($197/mo)
- Web Dev: One-time invoices (custom amounts)
- Both tracked in same Stripe dashboard
- Webhook handlers route by event type + metadata

### 4. n8n Cross-Business Webhooks

| Webhook | What It Does |
|---------|-------------|
| `/webhook/cross-referral` | PT → Web Dev or Web Dev → PT handoff trigger |
| `/webhook/stripe-payment-welcome` | Routes to PT or Web Dev onboarding based on Stripe metadata |
| `/webhook/client-status-update` | Updates shared Sheet when any business changes client status |

## Handoff Protocol

### Triggering a Cross-Business Handoff

1. **Identify the need** — Client mentions something outside your business's expertise
2. **Check if client exists in other business** — Look at shared Sheet
3. **Create handoff record** — Add to Cross-Referrals tab with:
   - Source business
   - Target business
   - Client name + phone
   - What they need
   - Priority (standard/urgent)
4. **Target business picks up** — Runs its onboarding workflow with cross-referral context
5. **Close the loop** — Source business gets notified when handoff is complete

### Automated Handoff Triggers

| Trigger | From | To | Action |
|---------|------|----|--------|
| PT client says "I need a website" | PT | Web Dev | Create project, send web dev welcome SMS |
| Web dev client says "I want coaching" | Web Dev | PT | Send coaching info + Calendly link |
| New Stripe payment with `business=webdev` metadata | Stripe | Web Dev | Web Dev onboarding workflow |
| New Stripe subscription with `business=coaching` metadata | Stripe | PT | PT onboarding workflow |
| Client active in both businesses | Shared | Both | Combine check-ins into single Monday message |

## Standard Business Unit Template

Every business unit MUST have these components:

### Required Structure
```
projects/marceau-solutions/{business}/
├── CLAUDE.md                    # Hub — quick reference, file map, common ops
├── ops/
│   └── {business}-ops-runbook.md  # Day-to-day operations
├── workflows/
│   ├── client-onboarding.md     # Automated + manual onboarding steps
│   ├── client-offboarding.md    # Cancellation/completion flow
│   └── client-communication.md  # SMS/email templates + cadence
├── legal/                       # Contracts, waivers, policies
│   └── ...
└── data/                        # JSON data files (templates, tips, etc.)
    └── ...
```

### Required Automation (n8n)
1. **Payment-Welcome** — Stripe event → onboarding actions
2. **Scheduled Check-in** — Regular client touchpoint (weekly or monthly)
3. **Offboarding/Completion** — Cancellation or project completion → follow-up

### Required Shared Tools
1. **SMS** (`execution/twilio_sms.py`) — Templates with `{business}_*` prefix
2. **Inbox Monitor** (`execution/twilio_inbox_monitor.py`) — Read replies
3. **Stripe** (`execution/stripe_payments.py`) — Billing
4. **Google Sheets** — Client tracking
5. **Telegram** — Admin notifications

### Required Documentation
1. **CLAUDE.md** — Quick reference, client registry, file map, common operations
2. **Ops Runbook** — Daily/weekly/monthly cadence
3. **Client Onboarding** — Step-by-step with SLA
4. **Client Communication** — Template reference + cadence

## Decision Rules

1. **"Client needs X from another business"** → Check Cross-Referrals tab, run handoff protocol
2. **"Which business owns this client?"** → Primary business is whichever they paid first. Secondary business is added as cross-referral.
3. **"Duplicate communication?"** → Never. One Monday message combining both businesses if dual-client.
4. **"New business unit?"** → Must implement Standard Business Unit Template before accepting clients.
