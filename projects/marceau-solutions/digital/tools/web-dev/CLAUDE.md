# Marceau Solutions — Website Development Business

> Static websites for small businesses. GitHub Pages hosting, dark+gold brand, per-project billing.
> Unified ops architecture: `docs/UNIFIED-BUSINESS-OPS.md`
> Cross-business integration: `docs/BUSINESS-INTEGRATION-PROTOCOL.md`

## Quick Reference

| Resource | Link / Value |
|----------|-------------|
| Company Website | https://marceausolutions.com |
| Stripe Dashboard | https://dashboard.stripe.com |
| n8n Dashboard | https://n8n.marceausolutions.com |
| Twilio Phone (clients) | +1 (855) 239-9364 |
| Admin Phone (notifications) | +1 239 398 5676 |
| Deploy Script | `./scripts/deploy_website.sh {client}` |
| Website Builder API | `projects/marceau-solutions/website-builder/` |
| Client Tracker Sheet | https://docs.google.com/spreadsheets/d/1gWobdkQsa8XCr7xEOXTFJ3t45e2K54bfxQpYLkCqN7Q/edit |
| Calendly (AI services) | https://calendly.com/wmarceau/ai-services-discovery-call |
| Calendly (fitness) | https://calendly.com/wmarceau/free-fitness-strategy-call |

## Status

- **Active clients**: 2 (HVAC, Flames of Passion) — BoabFit moved to Fitness Tower
- **Hosting**: All on GitHub Pages (free)
- **Billing**: Per-project invoicing via Stripe

---

## Client Registry

| Client | Slug | Domain | GitHub Pages Repo | Status |
|--------|------|--------|-------------------|--------|
| SW Florida Comfort HVAC | `hvac` | swfloridacomfort.com | `MarceauSolutions/swflorida-comfort-hvac` | Live |
| BoabFit | `boabfit` | TBD | `MarceauSolutions/boabfit-website` | Live |
| Flames of Passion | `flames` | flamesofpassionentertainment.com | `MarceauSolutions/flames-of-passion-website` | DNS pending |

## File Map

### In This Directory

| What | Path | Description |
|------|------|-------------|
| This file | `CLAUDE.md` | Hub reference (always loaded in context) |
| Client Onboarding | `workflows/client-onboarding.md` | Step-by-step new client setup |
| DNS Setup SOP | `workflows/dns-setup.md` | Reusable DNS pointing instructions |
| Client Communication | `workflows/client-communication.md` | SMS/email templates and cadence |
| Ops Runbook | `ops/web-dev-ops-runbook.md` | Day-to-day operations reference |
| Sheet Config | `data/sheet-config.json` | Google Sheets tracker ID |

### Client Project Directories

| Client | Path | CLAUDE.md |
|--------|------|-----------|
| HVAC | `digital/clients/swflorida-hvac/` | Yes |
| Flames of Passion | `digital/clients/flames-of-passion/` | Yes |
| BoabFit | `fitness/clients/boabfit/` (Fitness Tower) | Yes |

### Shared Code (DO NOT MOVE — used by multiple projects)

| What | Path | Description |
|------|------|-------------|
| Deploy script | `scripts/deploy_website.sh` | Deploys any client site to GitHub Pages |
| Twilio SMS | `execution/twilio_sms.py` | SMS with `webdev_*` templates |
| Twilio inbox | `execution/twilio_inbox_monitor.py` | Read inbound SMS |
| Branded PDF | `execution/branded_pdf_engine.py` | Generate PDF docs |
| Stripe payments | `execution/stripe_payments.py` | Invoicing |
| Website Builder | `digital/tools/website-builder/` | AI site generator |

### n8n Workflows (EC2)

| Workflow | ID | Status | What It Does |
|----------|-----|--------|------|
| Webdev-Payment-Welcome | `5GXwor2hHuij614l` | ACTIVE | Stripe payment → welcome SMS + Sheet + admin notify |
| Webdev-Monthly-Checkin | `N8HIFsZdE5Go7Lky` | ACTIVE | 1st of month → SMS check-in to all active clients |
| Webdev-Deploy-Notification | `E0DivEtTGgVZm3v6` | ACTIVE | Deploy webhook → client SMS + admin notify |
| Webdev-Cross-Referral | `eoQMjVYQSibMALaZ` | ACTIVE | Cross-business handoff → Sheet + admin notify |
| Flames-Form-Pipeline | `mrfVYqg5H12Z2l5K` | ACTIVE | Form submissions → Sheets + Telegram |

**n8n Credentials (on EC2):**
- Twilio: `hduvneOOzFzKMfOa` | Google Sheets: `RIFdaHtNYdTpFnlu` | Gmail SMTP: `xJL5bzXyMeTkr1WQ`

---

## Common Operations

| Task | How |
|------|-----|
| Deploy client website | `./scripts/deploy_website.sh {client}` |
| New client setup | `workflows/client-onboarding.md` |
| DNS setup for client | `workflows/dns-setup.md` |
| Send client SMS | `python execution/twilio_sms.py --template webdev_* --to <phone>` |
| Check client replies | `python execution/twilio_inbox_monitor.py check --hours 4` |
| Generate invoice | `python execution/stripe_payments.py` |
| Build AI website | `cd projects/marceau-solutions/website-builder && python -m src.website_builder_api` |
| Create tracker sheet | `python scripts/create-webdev-tracker-sheet.py` |
| Cross-referral (PT→Web) | POST to `https://n8n.marceausolutions.com/webhook/cross-referral` |

## Weekly Cadence

| Day | Time | What | Automated? |
|-----|------|------|-----------|
| 1st of month | 10am | Monthly check-in SMS to all active clients | YES (n8n: Webdev-Monthly-Checkin) |
| On deploy | Immediate | Client notification SMS | YES (n8n: Webdev-Deploy-Notification) |
| Weekly | - | Check Twilio inbox for client replies | Manual |
| Weekly | - | Review all client sites for uptime | Manual |

## Client Lifecycle

```
Prospect → Discovery Call → Quote/Invoice → Build → DNS Setup → Deploy → Ongoing Support
```

1. **Discovery**: Calendly 30min call, understand needs
2. **Quote**: Stripe invoice for build + optional monthly hosting
3. **Build**: Create `projects/{client}/website/`, design, iterate
4. **DNS**: Client points domain to GitHub Pages (SOP in workflows/)
5. **Deploy**: `./scripts/deploy_website.sh {client}`
6. **Support**: Bug fixes, content updates, monthly check-in
