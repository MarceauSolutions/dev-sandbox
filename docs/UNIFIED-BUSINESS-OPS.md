# Unified Business Operations Architecture

> Four towers, one shared stack. Inspired by Marmon Group's sector model — each tower groups related businesses by market/customer, sharing centralized services while operating independently.

## Tower Structure

| Tower | Hub | What's Inside | Revenue Model |
|-------|-----|---------------|---------------|
| **Marceau Fitness** | `projects/marceau-solutions/fitness/` | 1:1 PT coaching, Trainerize MCP | $197/mo subscription |
| **Marceau Digital** | `projects/marceau-solutions/digital/` | Client websites, AI website builder, marceausolutions.com | Per-project + hosting |
| **Marceau Media** | `projects/marceau-solutions/media/` | Fitness influencer platform, social content creators | SaaS / content licensing (future) |
| **Marceau Labs** | `projects/marceau-solutions/labs/` | DumbPhone Lock, Vuori lead magnet, Amazon, Miko's Lab, Legal | TBD (app sales, R&D) |

## Tower Contents

### Fitness Tower (`fitness/`)
| Project | Purpose |
|---------|---------|
| `pt-business/` | 1:1 PT coaching hub ($197/mo) |
| `trainerize-mcp/` | Trainerize platform integration |

### Digital Tower (`digital/`)
| Project | Purpose |
|---------|---------|
| `website/` | marceausolutions.com (static HTML) |
| `web-dev/` | Client website business (HVAC, BoabFit, Flames) |
| `website-builder/` | AI website generation service |

### Media Tower (`media/`)
| Project | Purpose |
|---------|---------|
| `fitness-influencer/` | AI fitness content platform (FitAI) |
| `fitness-influencer-mcp/` | MCP package for fitness influencer |
| `instagram-creator/` | Instagram content automation |
| `youtube-creator/` | YouTube content automation |
| `tiktok-creator/` | TikTok content automation |

### Labs Tower (`labs/`)
| Project | Purpose |
|---------|---------|
| `dumbphone-lock/` | iOS focus/app blocking |
| `vuori-lead-magnet/` | Vuori partnership lead gen |
| `amazon-seller/` | Amazon SP-API seller tools |
| `mikos-lab/` | Miko's Lab project |
| `legal-case-manager/` | Legal case management |

## Shared Services Layer (All Towers)

> The "holding company" equivalent — centralized infrastructure that every tower uses.

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

## Tool Ownership by Tower

### Fitness Tower Tools
| Tool | Location | What It Does |
|------|----------|-------------|
| Workout Generator | `execution/workout_plan_generator.py` | Custom workout programs |
| Nutrition Generator | `execution/nutrition_guide_generator.py` | Nutrition guides |
| Coaching Analytics | `execution/coaching_analytics.py` | SMS metrics, funnel stats |
| Coaching Tracker Sheet | `scripts/create-coaching-tracker-sheet.py` | Per-client Google Sheets |
| Drive Folder Creator | `scripts/create-coaching-drive-folders.py` | Per-client Drive folders |
| n8n: Coaching-Monday-Checkin | `aBxCj48nGQVLRRnq` | Weekly check-in SMS |
| n8n: Coaching-Payment-Welcome | `1wS9VvXIt95BrR9V` | Payment → onboarding |
| n8n: Coaching-Cancellation-Exit | `uKjqRexDIheaDJJH` | Cancellation flow |
| n8n: Fitness-SMS-Outreach | `89XxmBQMEej15nak` | Prospect outreach |
| n8n: Fitness-SMS-Followup | `VKC5cifm595JNcwG` | Drip sequence |

### Digital Tower Tools
| Tool | Location | What It Does |
|------|----------|-------------|
| Website Builder (AI) | `projects/marceau-solutions/digital/website-builder/` | FastAPI site generator |
| Client websites | `digital/clients/{client}/website/` | Per-client static HTML |
| n8n: Flames-Form-Pipeline | `mrfVYqg5H12Z2l5K` | Client form submissions |
| n8n: Webdev-Payment-Welcome | `5GXwor2hHuij614l` | Onboard new web dev clients |
| n8n: Webdev-Monthly-Checkin | `N8HIFsZdE5Go7Lky` | 1st of month SMS |
| n8n: Webdev-Deploy-Notification | `E0DivEtTGgVZm3v6` | Deploy webhook → client SMS |
| n8n: Webdev-Cross-Referral | `eoQMjVYQSibMALaZ` | PT→WebDev handoff |
| EC2 /forms/ hosting | `api.marceausolutions.com/forms/` | Fallback static hosting |

### Marketing/Lead Gen (Cross-Tower — primarily Fitness + Digital)
| Tool | Location | Used By |
|------|----------|---------|
| n8n: Website-Lead-Capture | `WHFIE3Ej7Y3SCtHk` | marceausolutions.com |
| n8n: Lead-Magnet-Capture | `hgInaJCLffLFBX1G` | marceausolutions.com |
| n8n: Creator-Lead-Capture | `8pvrmdtI0MfPbdsC` | Media tower |
| n8n: Challenge-Signup-7Day | `WTZDxLDQuSkIkcqf` | Fitness tower |
| n8n: Premium-Waitlist-Capture | `j306crRxCmWW3dMo` | Fitness tower |
| n8n: Non-Converter-Followup | `Y2jfeIlTRDlbCHeS` | All towers |

---

## Operational Standards (All Towers)

### Communication
- **Phone**: Toll-free +1 (855) 239-9364 for ALL automated SMS
- **Local**: +1 (239) 880-3365 reserved for personal/manual use only
- **Email**: wmarceau@marceausolutions.com
- **Admin alerts**: Telegram → William

### Client Websites (Digital Tower Standard)
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
- Fitness Tower: Stripe subscription ($197/mo)
- Digital Tower: Stripe invoice (per-project, custom amount)

---

## Decision Rules

1. **"Which tower does this belong to?"** → By customer/market: fitness clients → Fitness, business clients → Digital, content/audience → Media, experiments → Labs.
2. **"Which SMS templates do I use?"** → Check the `business_context` field. PT = `coaching_*` prefix. Web dev = `webdev_*` prefix.
3. **"Which n8n workflows are mine?"** → PT = `Coaching-`/`Fitness-`. Web dev = `Webdev-`/client name. Content = `X-`/`Creator-`.
4. **"Where do I track this client?"** → PT: Google Sheets tracker + Drive folder. Web dev: `digital/clients/{client}/` + tracker sheet.
5. **"Which phone number?"** → Always toll-free for automated. Local only for manual/personal calls.
6. **"New tool or existing?"** → Run `python scripts/inventory.py search <keyword>` FIRST. Always.

---

## Adding a New Web Dev Client

See `projects/marceau-solutions/digital/web-dev/workflows/client-onboarding.md` for the full workflow.

Quick reference:
1. Create `projects/marceau-solutions/digital/clients/{client-name}/` with `CLAUDE.md` and `website/`
2. Create GitHub Pages repo `MarceauSolutions/{client}-website`
3. Add client to `scripts/deploy_website.sh`
4. Create n8n form pipeline (clone `Flames-Form-Pipeline` pattern)
5. Set up DNS (client adds records or William manages via Namecheap)
6. Send welcome SMS + instructions
7. Deploy with `./scripts/deploy_website.sh {client}`

## Adding a New PT Client

See `projects/marceau-solutions/fitness/pt-business/workflows/client-onboarding.md` — fully automated via n8n.

## Backward Compatibility

Symlinks exist at old paths (e.g., `projects/marceau-solutions/pt-business` → `fitness/pt-business`) so legacy references still resolve. These can be removed once all references are verified migrated.
