# Decision Validation Matrix

**Created:** 2026-03-04
**Purpose:** Map every major business decision to its rationale, alternatives considered, and review criteria. Prevents re-debating settled questions and provides context for future pivots.

---

## Decision 1: Pricing at $197/month

| Aspect | Detail |
|--------|--------|
| **Decision** | Core coaching offer at $197/month, cancel anytime, no contracts |
| **Date** | February 2026 |
| **Status** | Active |

### Rationale
- **Market positioning**: $197 is the sweet spot for online fitness coaching. High enough to attract serious clients (not tire-kickers at $49-99), low enough to not require a sales call to close ($300+ typically needs a call).
- **Unit economics**: Net $190.99/client after Stripe fees. At 10 clients = $1,910 MRR. At 30 clients = $5,730 MRR. Covers personal burn rate ($4,950/mo) at ~26 clients.
- **Propane Fitness validation**: Propane's students average 30 clients at similar price points ($150-250/mo). Proven model, not speculative.
- **No-contract advantage**: "Cancel anytime" removes the biggest purchase objection. Clients who stay voluntarily churn less and refer more.
- **Price anchoring**: The $497/mo Premium tier (waitlist) makes $197 feel like the "affordable" option.

### Alternatives Considered
1. **$99/month** -- Too low. Attracts price-sensitive clients who churn fast. Would need 50+ clients to match revenue targets.
2. **$299/month** -- Viable but requires sales calls for most buyers. Creates a bottleneck since William is a solo operator.
3. **$497/month only** -- Too high for launch with 0 social proof. Premium tier reserved for when physician partnerships are established.
4. **Per-session pricing ($100/session)** -- Abandoned. Caps income at hours-worked. Subscription model enables scalable online delivery.

### Review Criteria
- Revisit if close rate drops below 15% (price too high) or churn exceeds 25%/month (perceived value too low)
- Consider price increase after 20+ testimonials and demonstrated results

---

## Decision 2: Peptide Focus as Differentiator

| Aspect | Detail |
|--------|--------|
| **Decision** | Position as "fitness coach + peptide educator" rather than generic PT |
| **Date** | February 2026 |
| **Status** | Active |

### Rationale
- **Differentiation**: Naples has hundreds of personal trainers. Zero combine evidence-based training with peptide education. This is a blue ocean niche.
- **Knowledge depth**: William has invested significant time studying peptide research (Tesamorelin, GH secretagogues, BPC-157, etc.). This is genuine expertise, not surface-level marketing.
- **Market demand**: Google Trends shows rising search interest for peptides, GH secretagogues, and BPC-157. Gary Brecka (2.5M+ YouTube subscribers) proved massive demand for health optimization content.
- **Revenue expansion**: Peptide education creates a natural pathway to a higher-tier offering ($497/mo Premium with physician referrals) and digital products (Peptide Masterclass at $97).
- **Legal safety**: The "educator + referral partner" model avoids scope-of-practice issues. William educates; licensed physicians prescribe.

### Alternatives Considered
1. **Generic PT / body recomp only** -- No differentiation in a crowded market. Competes on price, not expertise.
2. **Full peptide clinic** -- Requires medical licensing William doesn't have. Legal risk too high.
3. **Supplement affiliate only** -- Low-value, commodity business. No recurring revenue or relationship.

### Review Criteria
- If peptide regulation tightens (FDA action on BPC-157, etc.), adjust content to focus on FDA-approved compounds (Tesamorelin, Sermorelin)
- If TikTok-style bans spread to YouTube/Instagram, pivot peptide content to long-form blog/email format

---

## Decision 3: Naples FL + Online Hybrid

| Aspect | Detail |
|--------|--------|
| **Decision** | Serve both local Naples clients (in-person relationship) and online clients (scalable delivery) |
| **Date** | February 2026 |
| **Status** | Active |

### Rationale
- **Local trust**: In-person clients trust you faster. They see you at the gym, know you're real. Local clients become your best testimonials and referral sources.
- **Naples demographics**: Affluent retirees and professionals 35-65. High disposable income. Strong demand for health optimization. Peptide clinics already exist in the area (referral partners).
- **Online scale**: Local caps at ~20-30 clients (time-limited). Online coaching via the client portal (fitai.marceausolutions.com/client/) can serve 50-100+ clients with the same systems.
- **Snowbird hedge**: Naples population fluctuates seasonally. Online clients provide revenue stability year-round.

### Alternatives Considered
1. **Online only** -- Faster to scale but harder to build initial trust with 0 social proof. Local relationships jumpstart testimonials.
2. **Local only** -- Caps revenue at hours-in-the-day. Doesn't leverage the tech infrastructure already built.
3. **Different market (Tampa, Miami)** -- More competition, higher cost of living. Naples has ideal client demographics for peptide-interested affluent adults.

### Review Criteria
- If local client acquisition stalls after 8 weeks, shift focus to online-first with Naples as secondary
- If online outperforms local 3:1, consider dropping in-person and going fully remote

---

## Decision 4: Stripe over Square/PayPal

| Aspect | Detail |
|--------|--------|
| **Decision** | Use Stripe as sole payment processor |
| **Date** | February 2026 |
| **Status** | Active |

### Rationale
- **Subscription management**: Stripe handles recurring billing, failed payment retries, and customer portal natively. Square requires workarounds for subscriptions.
- **Webhook automation**: Stripe's webhook system integrates directly with n8n workflows. `checkout.session.completed` triggers portal account creation, welcome SMS, email, and sheet updates. This automation chain is the backbone of the no-touch onboarding system.
- **Developer-friendly API**: Existing `execution/stripe_payments.py` and `execution/stripe_webhook_server.py` are already built and tested.
- **Payment links**: Stripe generates shareable payment links that work in SMS and email. No need for a checkout page.
- **Industry standard**: 2.9% + $0.30 per transaction is comparable to all alternatives.

### Alternatives Considered
1. **Square** -- Good for in-person POS. Weak on subscription management and webhook automation. No API integration advantage over existing Stripe setup.
2. **PayPal** -- Higher fees for subscriptions (3.49% + $0.49). Consumer-facing brand feels less professional for B2B coaching.
3. **GoHighLevel** -- All-in-one platform with payments. Too expensive ($297-497/mo) and locks you into their ecosystem. Violates the "own your data" principle.

### Review Criteria
- If Stripe raises fees above 3.5%, evaluate alternatives
- If in-person payments become common, add Square as a secondary POS (not a replacement)

---

## Decision 5: n8n over Zapier

| Aspect | Detail |
|--------|--------|
| **Decision** | Use self-hosted n8n for all workflow automation |
| **Date** | 2025 (pre-dates coaching business) |
| **Status** | Active |

### Rationale
- **Cost**: n8n is free (self-hosted on existing EC2 instance). Zapier costs $20-70/mo for comparable workflow volume. At 16+ active workflows, Zapier would cost $50+/mo.
- **No execution limits**: Zapier free tier caps at 100 tasks/month. n8n self-hosted has unlimited executions.
- **Data ownership**: All workflow data stays on your EC2 instance. No third-party data processing concerns for client phone numbers, emails, and health data.
- **Complexity support**: n8n handles multi-step webhook chains (Lead-Magnet-Capture -> Nurture-Sequence-7Day -> Non-Converter-Followup) that would require Zapier's most expensive tier.
- **Already operational**: 16+ workflows running on EC2 with SSL, auto-backups, and health checks. Migration cost would be high for zero benefit.

### Alternatives Considered
1. **Zapier** -- Easier setup, worse economics. $50+/mo for the workflow volume needed. Data leaves your infrastructure.
2. **Make (Integromat)** -- Cheaper than Zapier but still SaaS-hosted. No cost advantage over free self-hosted n8n.
3. **Custom Python scripts** -- Maximum control but high maintenance. n8n's visual editor makes debugging and iteration faster than pure code.

### Review Criteria
- If EC2 costs increase significantly, evaluate n8n Cloud ($20/mo) as an alternative to self-hosting
- If n8n reliability drops (3+ incidents/month), consider migration

---

## Decision 6: Twilio over Alternatives

| Aspect | Detail |
|--------|--------|
| **Decision** | Use Twilio for all SMS communication (client messaging, nurture sequences, outreach) |
| **Date** | 2025 (pre-dates coaching business) |
| **Status** | Active |

### Rationale
- **Already integrated**: `execution/twilio_sms.py` has 19 coaching-specific templates. `execution/twilio_inbox_monitor.py` handles inbound. n8n workflows use Twilio nodes directly.
- **Usage-based pricing**: ~$0.0079/outbound SMS + $1/mo per number. At ~200 messages/month = ~$12/mo. Far cheaper than platform pricing ($25-100/mo for SimpleTexting, EZTexting, etc.).
- **API flexibility**: Full programmatic control over send timing, template selection, and response handling. Platform tools limit customization.
- **TCPA compliance**: Twilio handles number registration (10DLC) and provides opt-out handling infrastructure.
- **Dedicated business number**: +1 (855) 239-9364 toll-free number, separate from William's personal phone. Local 239 number available but not currently active.

### Alternatives Considered
1. **SimpleTexting** -- $25/mo minimum. GUI-based, less flexible. No API integration with n8n without workarounds.
2. **Google Voice** -- Free but no API, no automation, no TCPA compliance tools. Not suitable for business SMS.
3. **WhatsApp Business** -- Popular but SMS has 98% open rates in the US market. WhatsApp adoption is lower for the target demographic (35-55 affluent Americans).

### Review Criteria
- If Twilio 10DLC fees increase or message deliverability drops, evaluate alternatives
- If client volume exceeds 200 SMS/day, negotiate volume pricing

---

## Decision 7: Static HTML Website over WordPress/Webflow

| Aspect | Detail |
|--------|--------|
| **Decision** | Build marceausolutions.com as static HTML/CSS/JS hosted on GitHub Pages |
| **Date** | February 2026 |
| **Status** | Active |

### Rationale
- **Zero hosting cost**: GitHub Pages is free. WordPress hosting starts at $4-30/mo. Webflow starts at $14/mo.
- **Zero dependencies**: No CMS to update, no plugins to patch, no database to maintain. The site is 6 HTML files that will work for years without touching them.
- **Full control**: Every pixel is customizable. No theme constraints. The dark+gold brand identity is implemented exactly as designed.
- **Performance**: Static HTML loads in <1 second. No server-side rendering, no database queries, no plugin overhead. Google PageSpeed scores are excellent.
- **Developer workflow**: Edit files in VS Code, deploy with `./scripts/deploy_website.sh marceau-solutions`. Changes live in 1-2 minutes.
- **Claude Code compatibility**: Claude can edit HTML files directly. CMS-based sites require browser interaction that agents can't do.

### Alternatives Considered
1. **WordPress** -- Most popular CMS. But requires hosting ($4-30/mo), plugin management, security updates, and theme constraints. Overkill for 6 pages.
2. **Webflow** -- Beautiful visual editor. But $14-39/mo, proprietary platform lock-in, and limited customization at lower tiers.
3. **Squarespace** -- Easy but expensive ($16-49/mo) and template-constrained. No API access for quiz/challenge integrations.
4. **Carrd** -- Free tier is single-page only. Multi-page requires $19/year. Too limited for a 6-page funnel.

### Review Criteria
- If the site needs blog functionality (SEO-driven content marketing), consider adding a lightweight static site generator (Hugo, 11ty) rather than switching to WordPress
- If a client-facing admin panel is needed for content updates, re-evaluate. Currently William is the sole editor, so developer workflow is fine.

---

## Decision 8: Google Sheets as CRM (Not SaaS CRM)

| Aspect | Detail |
|--------|--------|
| **Decision** | Use Google Sheets for lead tracking and client management instead of HubSpot, GoHighLevel, or other CRM platforms |
| **Date** | February 2026 |
| **Status** | Active (with planned upgrade path) |

### Rationale
- **Free**: $0/month vs. $20-497/month for CRM platforms
- **n8n native integration**: Google Sheets nodes in n8n read/write directly. No API keys or OAuth complexity beyond initial setup.
- **Scale-appropriate**: At 0-30 clients, a CRM is overhead. Sheets handles lead capture, nurture status tracking, client roster, and billing logs without friction.
- **Familiar**: William can view and edit data in the browser without learning a new platform.
- **Exportable**: CSV export means data can migrate to any CRM later without vendor lock-in.

### Alternatives Considered
1. **HubSpot Free** -- 1M contacts, feature-rich. But onboarding overhead is not justified at 0 clients. Planned upgrade when reaching 100+ leads/month.
2. **GoHighLevel** -- $297-497/mo. Full marketing automation suite. Massive overkill and expensive for current stage.
3. **ClickUp** -- Already configured for other projects. Could work but mixing business operations with development task management creates confusion.

### Review Criteria
- **Upgrade trigger**: When reaching 100+ leads/month or 30+ active clients, migrate to HubSpot Free or similar
- If data integrity issues emerge (duplicate entries, lost rows), upgrade immediately

---

## Decision 9: Subscription Model over Per-Session Pricing

| Aspect | Detail |
|--------|--------|
| **Decision** | Sell coaching as a $197/month subscription, not per-session packages |
| **Date** | February 2026 |
| **Status** | Active |

### Rationale
- **Predictable revenue (MRR)**: Subscriptions create Monthly Recurring Revenue. 20 clients = $3,940 predictable income vs. variable session bookings.
- **Scalability**: Per-session pricing caps income at hours-available. Subscription model with online delivery (portal, SMS check-ins, async coaching) can serve 50-100+ clients.
- **Client commitment**: Monthly subscription encourages ongoing engagement vs. sporadic sessions. Consistency drives better results, which drives retention and referrals.
- **Automation-friendly**: Stripe handles recurring billing automatically. No invoicing, no session tracking, no payment chasing.
- **No-call conversion**: $197/mo can be sold through SMS nurture sequences and payment links. Per-session pricing requires booking and selling each session.

### Alternatives Considered
1. **Per-session ($100/session)** -- Familiar model but caps revenue at hours. Also requires in-person presence, limiting online scalability.
2. **Hybrid (subscription + sessions)** -- Complexity for the client. Hard to automate billing for variable session counts.
3. **Tiered sessions (4-pack $380, 8-pack $720)** -- Better than per-session but still not recurring. Client must re-purchase every month.

### Review Criteria
- If client churn exceeds 30%/month, the subscription model may need additional perceived value (more touchpoints, more features)
- If local in-person demand outstrips online, consider adding a separate per-session add-on for in-person training

---

*Last updated: 2026-03-04*
*Review frequency: Quarterly or when a decision is questioned*
