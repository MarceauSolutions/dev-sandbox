# Unified Business Operations Architecture

> Two businesses, one stack. This document defines tool ownership, shared layers, and operational boundaries.

## Business Units

| Business | Hub | Revenue Model | Clients |
|----------|-----|---------------|---------|
| **PT Coaching** | `projects/marceau-solutions/pt-business/` | $197/mo subscription | Individual fitness clients |
| **Website Development** | `projects/marceau-solutions/web-dev/` | Per-project + optional hosting | Small businesses (HVAC, candles, etc.) |

## Tool Ownership Map

### Shared Layer (Both Businesses Use)

| Tool | Location | What It Does |
|------|----------|-------------|
| Twilio SMS | `execution/twilio_sms.py` | Client communication (templates per business) |
| Twilio Inbox Monitor | `execution/twilio_inbox_monitor.py` | Read inbound SMS replies |
| Branded PDF Engine | `execution/branded_pdf_engine.py` | Generate dark+gold PDFs |
| Markdown to PDF | `projects/shared/md-to-pdf/` | Convert docs to PDF |
| Gmail API | `execution/send_onboarding_email.py` | Email (extend for web dev) |
| Stripe Payments | `execution/stripe_payments.py` | Billing + invoicing |
| Stripe Webhooks | `execution/stripe_webhook_server.py` | Payment event handling |
| Deploy Script | `scripts/deploy_website.sh` | GitHub Pages deployment |
| n8n (platform) | EC2 `n8n.marceausolutions.com` | Workflow automation |
| Telegram Notifications | n8n → Telegram | Admin alerts |
| Google Sheets | via n8n credentials | CRM / tracking |

### PT Coaching Only

| Tool | Location | What It Does |
|------|----------|-------------|
| Workout Generator | `execution/workout_plan_generator.py` | Custom workout programs |
| Nutrition Generator | `execution/nutrition_guide_generator.py` | Nutrition guides |
| Coaching Analytics | `execution/coaching_analytics.py` | SMS metrics, funnel stats |
| Coaching Tracker Sheet | `scripts/create-coaching-tracker-sheet.py` | Per-client Google Sheets |
| Drive Folder Creator | `scripts/create-coaching-drive-folders.py` | Per-client Drive folders |
| Fitness Influencer Platform | `projects/marceau-solutions/fitness-influencer/` | SaaS product (future B2B) |
| n8n: Coaching-Monday-Checkin | `aBxCj48nGQVLRRnq` | Weekly check-in SMS |
| n8n: Coaching-Payment-Welcome | `1wS9VvXIt95BrR9V` | Payment → onboarding |
| n8n: Coaching-Cancellation-Exit | `uKjqRexDIheaDJJH` | Cancellation flow |
| n8n: Fitness-SMS-Outreach | `89XxmBQMEej15nak` | Prospect outreach |
| n8n: Fitness-SMS-Followup | `VKC5cifm595JNcwG` | Drip sequence |

### Website Development Only

| Tool | Location | What It Does |
|------|----------|-------------|
| Website Builder (AI) | `projects/marceau-solutions/website-builder/` | FastAPI site generator |
| Client websites | `projects/{client}/website/` | Per-client static HTML |
| n8n: Flames-Form-Pipeline | `mrfVYqg5H12Z2l5K` | Client form submissions |
| EC2 /forms/ hosting | `api.marceausolutions.com/forms/` | Fallback static hosting |

### Marketing/Lead Gen (Shared — Website Funnels)

| Tool | Location | Used By |
|------|----------|---------|
| n8n: Website-Lead-Capture | `WHFIE3Ej7Y3SCtHk` | marceausolutions.com |
| n8n: Lead-Magnet-Capture | `hgInaJCLffLFBX1G` | marceausolutions.com |
| n8n: Creator-Lead-Capture | `8pvrmdtI0MfPbdsC` | For-influencers funnel |
| n8n: Challenge-Signup-7Day | `WTZDxLDQuSkIkcqf` | PT lead gen |
| n8n: Premium-Waitlist-Capture | `j306crRxCmWW3dMo` | PT premium |
| n8n: Non-Converter-Followup | `Y2jfeIlTRDlbCHeS` | All leads |

---

## Operational Standards (Both Businesses)

### Communication
- **Phone**: Toll-free +1 (855) 239-9364 for ALL automated SMS
- **Local**: +1 (239) 880-3365 reserved for personal/manual use only
- **Email**: wmarceau@marceausolutions.com
- **Admin alerts**: Telegram → William

### Client Websites (Web Dev Standard)
- **Registrar + DNS**: Client's existing (help them add records) or Namecheap
- **Hosting**: GitHub Pages (free, reliable)
- **Forms**: n8n webhook → Google Sheets + Telegram notification
- **Deployment**: `scripts/deploy_website.sh {client}`
- **Fallback hosting**: EC2 `api.marceausolutions.com/forms/`

### DNS Records (GitHub Pages)
```
A     @    185.199.108.153
A     @    185.199.109.153
A     @    185.199.110.153
A     @    185.199.111.153
CNAME www  marceausolutions.github.io
```

### Billing
- PT Coaching: Stripe subscription ($197/mo)
- Web Dev: Stripe invoice (per-project, custom amount)

---

## Decision Rules

1. **"Which SMS templates do I use?"** → Check the `business_context` field in template metadata. PT templates are in `twilio_sms.py` with `coaching_*` prefix. Web dev templates use `webdev_*` prefix.
2. **"Which n8n workflows are mine?"** → PT workflows start with `Coaching-` or `Fitness-`. Web dev workflows start with client name (e.g., `Flames-`).
3. **"Where do I track this client?"** → PT clients: Google Sheets tracker + Drive folder. Web dev clients: `projects/{client}/` directory + project tracker sheet.
4. **"Which phone number?"** → Always toll-free for automated. Local only for manual/personal calls.
5. **"New tool or existing?"** → Run `python scripts/inventory.py search <keyword>` FIRST. Always.

---

## Adding a New Web Dev Client

See `projects/marceau-solutions/web-dev/workflows/client-onboarding.md` for the full workflow.

Quick reference:
1. Create `projects/{client-name}/` with `CLAUDE.md` and `website/`
2. Create GitHub Pages repo `MarceauSolutions/{client}-website`
3. Add client to `scripts/deploy_website.sh`
4. Create n8n form pipeline (clone `Flames-Form-Pipeline` pattern)
5. Set up DNS (client adds records or William manages via Namecheap)
6. Send welcome SMS + instructions
7. Deploy with `./scripts/deploy_website.sh {client}`

## Adding a New PT Client

See `projects/marceau-solutions/pt-business/workflows/client-onboarding.md` — fully automated via n8n.
