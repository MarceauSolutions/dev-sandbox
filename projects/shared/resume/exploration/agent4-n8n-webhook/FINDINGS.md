# Agent 4: n8n Webhooks + Landing Page Approach

## Summary

**Viable: YES** -- This is the fastest path to market with the lowest incremental cost.

The n8n webhook approach leverages nearly all existing infrastructure: the EC2 instance already running n8n with 73+ endpoints, the Python Bridge API (localhost:5010), Stripe payments, Google Drive sharing, pandoc for PDF generation, and Claude Sonnet for AI generation. The only net-new work is: (1) one n8n workflow, (2) 3-4 Python scripts adapted from the existing manual workflow, and (3) a static landing page. Estimated **3-5 days** to a working MVP, with marginal cost per resume generation around **$0.08-0.15**.

The tradeoff is honest: this approach sacrifices scalability and real-time UX for speed-to-market. It is NOT a SaaS platform -- it is a "done-for-you" automated service that happens to be instant. That positioning is actually a strength for the initial target market.

---

## Revenue Model

### Pricing Strategy: Per-Use with Tiered Packages

Based on competitive analysis of the resume service market:

| Service Type | Price Range (Market) | Our Price | Rationale |
|-------------|---------------------|-----------|-----------|
| **DIY Resume Builders** (Canva, Resume.io) | $3-8/mo subscription | N/A | Different segment |
| **AI Resume Tools** (Teal, Rezi, Kickresume) | $5-29/mo subscription | N/A | We compete on quality, not features |
| **Professional Resume Writers** | $100-400 one-time | N/A | Too expensive for most job seekers |
| **Per-Use AI Resume Generation** | $5-19 per resume | **$9.99** | Sweet spot |

**Recommended Pricing Tiers:**

| Tier | Price | Includes | Target |
|------|-------|----------|--------|
| **Single** | $9.99 | 1 tailored resume + cover letter (PDF) | Casual job seeker |
| **Job Hunt Pack** | $24.99 | 3 tailored resume+cover letter pairs | Active applicant |
| **Unlimited Month** | $49.99 | Unlimited generations for 30 days | Serious job search |

### Margin Analysis (Per Single Generation @ $9.99)

| Cost Component | Amount | Notes |
|---------------|--------|-------|
| Claude Sonnet API (job parsing) | $0.015 | ~1K input + 500 output tokens |
| Claude Sonnet API (resume tailoring) | $0.04 | ~3K input (resume_data.json + job) + 2K output |
| Claude Sonnet API (cover letter) | $0.03 | ~2K input + 1K output |
| EC2 compute (marginal) | $0.001 | Already running 24/7; negligible per-request |
| Pandoc PDF generation | $0.00 | Free, local process |
| Google Drive storage | $0.00 | Within free tier |
| Email delivery (Gmail API) | $0.00 | Using existing OAuth |
| Stripe fee (2.9% + $0.30) | $0.59 | Per transaction |
| **Total Cost Per Generation** | **~$0.68** | |
| **Revenue** | **$9.99** | |
| **Gross Margin** | **$9.31 (93.2%)** | |

### Break-Even Analysis

| Fixed Cost | Monthly Amount |
|-----------|---------------|
| EC2 t3.medium (already running) | $0 incremental |
| Domain/hosting for landing page | $0 (GitHub Pages) |
| Stripe subscription | $0 (pay-as-you-go) |
| **Total Fixed Costs** | **$0/month incremental** |

Since fixed costs are zero (infrastructure already exists), **every sale is profit minus the ~$0.68 variable cost**. Break-even is literally the first sale.

To hit meaningful revenue targets:

| Monthly Revenue Target | Sales Needed (Single tier) | Sales/Day |
|----------------------|---------------------------|-----------|
| $100/mo | 11 sales | 0.35/day |
| $500/mo | 51 sales | 1.7/day |
| $1,000/mo | 101 sales | 3.4/day |
| $5,000/mo | 501 sales | 16.7/day |

---

## Target Market

### Primary: Active Job Seekers Who Value Quality Over Speed

**Who pays $10 for a tailored resume?**

1. **Career changers** -- Need resumes that reframe experience for a new industry. The manual 10-step workflow excels at this (see existing L3Harris, Trane HVAC, Boston Dynamics examples).
2. **Experienced professionals applying to specific roles** -- They know generic resumes get filtered by ATS. They want exact keyword matching for a specific posting.
3. **Job seekers applying to 5-15 positions** -- The "Job Hunt Pack" at $24.99 targets this: most serious applicants send 10+ tailored applications.
4. **People who hate writing cover letters** -- Cover letters are the #1 pain point. "Paste the job posting, get a perfect cover letter in 2 minutes" is a strong hook.

**Who does NOT pay (and we should not pursue):**

- People applying to 100+ jobs spray-and-pray style (they use free tools)
- Students (no budget)
- People who want to edit/tweak templates themselves (they want Canva/Resume.io)

### Market Sizing

- ~6.3 million Americans actively looking for work at any given time (BLS)
- ~40% use online tools for resume help
- Addressable: professionals willing to pay for per-use AI generation
- Conservative estimate: 0.01% conversion from organic/SEO = ~250 users/month
- Realistic with paid ads: 50-200 users/month in first 6 months

---

## Technical Architecture

### System Flow

```
User Journey:
┌─────────────┐    ┌──────────────┐    ┌───────────────┐
│ Landing Page │───>│ Stripe       │───>│ n8n Webhook   │
│ (GitHub      │    │ Checkout     │    │ /webhook/     │
│  Pages)      │    │ Session      │    │ resume-builder│
└─────────────┘    └──────────────┘    └───────┬───────┘
                                               │
                   ┌───────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │ n8n Workflow        │
        │                     │
        │ 1. Parse job posting│──> Claude Sonnet (API)
        │ 2. Match skills     │
        │ 3. Tailor resume    │──> Claude Sonnet (API)
        │ 4. Write cover ltr  │──> Claude Sonnet (API)
        │ 5. Generate PDFs    │──> Python Bridge (pandoc)
        │ 6. Upload to Drive  │──> Google Drive API
        │ 7. Email delivery   │──> Gmail API
        │ 8. Update status    │
        └─────────────────────┘
```

### n8n Workflow Design (Single Workflow)

**Trigger:** Webhook node (`POST /webhook/resume-builder`)

**Input payload:**
```json
{
  "email": "customer@example.com",
  "name": "Jane Doe",
  "job_posting_url": "https://...",
  "job_posting_text": "Full job description pasted here...",
  "resume_data": { /* customer's resume JSON, same schema as resume_data.json */ },
  "stripe_session_id": "cs_live_xxx",
  "preferences": {
    "role_type": "software_engineer",
    "include_cover_letter": true
  }
}
```

**Node Pipeline (8 nodes):**

| # | Node Type | Name | What It Does |
|---|-----------|------|-------------|
| 1 | Webhook | Resume Builder Trigger | Receives POST with job + resume data |
| 2 | IF | Payment Verified? | Calls Stripe API to verify session was paid |
| 3 | HTTP Request (Python Bridge) | Parse Job Posting | POST to localhost:5010 → `job_parser.py` extracts requirements, keywords, company info |
| 4 | HTTP Request (Python Bridge) | Tailor Resume | POST to localhost:5010 → `resume_generator.py` uses Claude to match resume to job |
| 5 | HTTP Request (Python Bridge) | Generate Cover Letter | POST to localhost:5010 → `cover_letter_gen.py` uses Claude to write tailored cover letter |
| 6 | HTTP Request (Python Bridge) | Generate PDFs | POST to localhost:5010 → `pdf_builder.py` runs pandoc to create resume.pdf + cover_letter.pdf |
| 7 | HTTP Request (Python Bridge) | Upload to Drive | POST to localhost:5010 → `google_drive_share.py` uploads PDFs, returns shareable link |
| 8 | Gmail | Deliver to Customer | Sends email with Google Drive link + inline preview |

**Error Handling:**
- Each Python Bridge call includes try/catch with retry (n8n native retry on HTTP nodes)
- Failed generations trigger an error email to William + refund flag in Stripe
- Timeout set to 120 seconds per node (Claude can take 10-30s per generation)

### Python Bridge Scripts (New, on EC2)

**1. `job_parser.py`** -- Extracts structured data from job posting text
```python
# Input: raw job posting text or URL
# Output: {required_skills, preferred_skills, company, role_title, industry, keywords}
# Uses: Claude Sonnet for NLP extraction
# Reuses: Existing Step 1 logic from tailor-resume-for-role.md
```

**2. `resume_generator.py`** -- Tailors resume to match job
```python
# Input: parsed job requirements + customer resume_data.json
# Output: tailored resume markdown (same format as existing output/)
# Uses: Claude Sonnet for content generation
# Reuses: Steps 2-7 from tailor-resume-for-role.md (summary, skills reorder, bullet tailoring, ATS keywords)
```

**3. `cover_letter_gen.py`** -- Writes tailored cover letter
```python
# Input: parsed job requirements + tailored resume + customer data
# Output: cover letter markdown (same format as existing output/)
# Uses: Claude Sonnet for prose generation
# Reuses: Steps 8-10 from tailor-resume-for-role.md
```

**4. `pdf_builder.py`** -- Converts markdown to PDF
```python
# Input: resume.md + cover_letter.md paths
# Output: resume.pdf + cover_letter.pdf paths
# Uses: pandoc with pdflatex engine
# Reuses: Exact pandoc commands from tailor-resume-for-role.md Step 10
#   Resume: pandoc resume.md -o resume.pdf --pdf-engine=pdflatex -V geometry:margin=0.75in -V fontsize=11pt
#   Cover:  pandoc cover.md -o cover.pdf --pdf-engine=pdflatex -V geometry:margin=1in -V fontsize=11pt
```

### Landing Page (Static HTML on GitHub Pages)

**Pages needed:**

| Page | Purpose |
|------|---------|
| `index.html` | Sales page with benefits, sample outputs, pricing, Stripe checkout button |
| `upload.html` | Post-payment form: paste job posting + upload resume data (or fill form) |
| `status.html` | Simple polling page: "Your resume is being generated..." → "Ready! Check email" |
| `assets/` | CSS, sample resume screenshots, favicon |

**Key UX Decision:** The landing page uses Stripe Checkout (hosted by Stripe) for payment, then redirects to `upload.html` where the user pastes the job posting. On submit, JavaScript POSTs to the n8n webhook. The `status.html` page polls a simple status endpoint (or just says "check your email in 2-3 minutes").

### Data Flow for Customer Resume Input

**Option A: Paste-in form (MVP)**
- Customer fills out a structured web form: name, email, phone, LinkedIn, skills, experience entries
- Form JavaScript assembles into `resume_data.json` format and POSTs to webhook

**Option B: Upload existing resume (Phase 2)**
- Customer uploads a PDF resume
- Python Bridge uses Claude to parse PDF into `resume_data.json` format
- Adds ~$0.03 in API cost per parse

**Recommendation:** Start with Option A (form-based input). It is simpler, produces structured data, and avoids the complexity of PDF parsing. Add Option B as a Phase 2 upgrade.

---

## Cost Analysis

### Marginal Cost Per Resume Generation

| Component | Cost | Calculation |
|-----------|------|-------------|
| **Claude Sonnet API** | $0.085 | 3 calls: parse ($0.015) + resume ($0.04) + cover letter ($0.03) |
| **EC2 compute** | ~$0.001 | t3.medium already running; CPU burst for pandoc is negligible |
| **Pandoc PDF** | $0.00 | Local process, ~2 seconds |
| **Google Drive** | $0.00 | 15 GB free; two PDFs = ~200KB |
| **Gmail API** | $0.00 | Within daily limits (500/day for workspace) |
| **Stripe processing** | $0.59 | 2.9% + $0.30 on $9.99 |
| **TOTAL variable cost** | **$0.68** | Per single generation |
| **TOTAL for 3-pack** | **$0.98** | 3x Claude + 1x Stripe on $24.99 |

### Monthly Infrastructure Cost (Already Paid)

| Item | Monthly Cost | Status |
|------|-------------|--------|
| EC2 t3.medium | ~$30/mo | Already running for n8n + other services |
| Domain (marceausolutions.com) | ~$1/mo | Already owned |
| GitHub Pages hosting | $0 | Free |
| Google Workspace | ~$7/mo | Already active |
| Anthropic API | Pay-as-you-go | Already active, billed per token |
| **Incremental monthly cost** | **$0** | Everything is already running |

### Cost Comparison to Alternatives

| Approach | Monthly Fixed Cost | Per-Generation Cost | Time to Market |
|----------|-------------------|--------------------|----|
| **n8n Webhook (this)** | **$0** | **$0.68** | **3-5 days** |
| SaaS (Railway/Vercel) | $20-50 | $0.12 | 2-4 weeks |
| Full Platform (Next.js) | $50-100 | $0.10 | 4-8 weeks |
| MCP Server | $0 | $0.08 | 1-2 weeks |

---

## Pros

1. **Fastest time to market (3-5 days).** Nearly all infrastructure exists. The n8n workflow is the only significant new build. Python scripts adapt directly from the proven 10-step manual workflow.

2. **Zero incremental infrastructure cost.** EC2, n8n, Stripe, Google Drive, Gmail, pandoc -- all running and paid for. First dollar of revenue is almost entirely profit.

3. **Proven quality pipeline.** 107 PDF resume+cover letter pairs already generated using this exact workflow. The output quality is validated across defense, medical, software, sales, and other verticals.

4. **Battle-tested payment and delivery.** `stripe_payments.py` handles checkout sessions, `google_drive_share.py` handles file delivery, `send_onboarding_email.py` provides email templates. These are production code, not prototypes.

5. **Low-risk experiment.** If the product fails, total investment is 3-5 days of dev time. No new servers, no new subscriptions, no new infrastructure to maintain or shut down.

---

## Cons

1. **No real-time in-browser experience.** Users cannot watch their resume being generated or make edits. The flow is: pay -> paste job -> wait for email. This is a "done-for-you" service, not a SaaS product. Some users expect instant interactive tools.

2. **Single point of failure (EC2).** If the EC2 instance goes down, the entire service stops. n8n, Python Bridge, and all processing run on one t3.medium. No redundancy, no failover. Downtime = lost orders and refund requests.

3. **No customer self-service.** Cannot edit generated resume, cannot tweak formatting, cannot regenerate with different emphasis. Each generation is a one-shot output. Revisions require a new payment or manual intervention.

4. **Scaling ceiling is low.** The t3.medium (2 vCPU, 4GB RAM) can handle ~5-10 concurrent generations before performance degrades. At peak, this means ~50-100 resumes/hour max. Beyond that requires instance upgrade.

5. **Landing page UX is limited.** A static HTML page with Stripe checkout is functional but feels less polished than competitors with branded dashboards, template galleries, and interactive editors. May hurt conversion rate on paid traffic.

---

## Risks

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **EC2 downtime** | Medium | High | Cloudwatch alarm, n8n error workflow sends Telegram alert |
| **Claude API timeout** | Low | Medium | n8n retry logic (3 attempts), 120s timeout per node |
| **Pandoc fails on complex markdown** | Low | Low | Tested on 107 resumes; edge cases caught by try/catch |
| **Stripe webhook mismatch** | Low | High | Verify payment before generation; log all webhook events |
| **Gmail daily send limit (500)** | Low | Medium | Only matters at 500+ sales/day -- upgrade to SendGrid if hit |
| **Python Bridge crash** | Low | High | Systemd auto-restart configured; health check endpoint |

### Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Low conversion rate** | High | Medium | Test pricing, improve landing page copy, add sample outputs |
| **Refund requests** | Medium | Low | Clearly state "AI-generated, no revisions" in checkout |
| **Quality inconsistency** | Low | High | Use proven prompts from 107 successful generations; add quality check node |
| **Customer data security** | Medium | Medium | Resume data contains PII; need privacy policy, data retention limits |
| **SEO competition** | High | Medium | "AI resume builder" is saturated; differentiate on "per-use" and quality |

### Legal/Compliance

- Need a **privacy policy** (handling PII: names, emails, work history)
- Need **terms of service** (no revisions, AI-generated content, no guarantees)
- Stripe requires a **refund policy** for digital goods
- GDPR consideration if any EU customers (data deletion capability needed)

---

## Time to Market

### Estimated Build Schedule: 3-5 Days

| Day | Task | Hours | Deliverable |
|-----|------|-------|-------------|
| **Day 1** | Python scripts: `job_parser.py`, `resume_generator.py` | 4-6h | Two scripts adapted from workflow Steps 1-7 |
| **Day 1** | Python scripts: `cover_letter_gen.py`, `pdf_builder.py` | 2-3h | Two scripts adapted from workflow Steps 8-10 |
| **Day 2** | n8n workflow: build 8-node pipeline, test with sample data | 4-6h | Working webhook-to-email pipeline |
| **Day 2** | Stripe integration: create product, configure webhook | 1-2h | Payment link + webhook handler |
| **Day 3** | Landing page: `index.html`, `upload.html`, `status.html` | 4-6h | Static site on GitHub Pages |
| **Day 3** | End-to-end testing: 5 test generations | 2-3h | Verified pipeline |
| **Day 4** | Error handling, edge cases, monitoring setup | 3-4h | Production-ready error flows |
| **Day 5** | Final testing, soft launch, first real customer test | 2-3h | Live service |

**Total estimated hours: 22-33 hours**

### What Accelerates This Build

- `tailor-resume-for-role.md` is a complete 10-step spec that maps directly to code
- `resume_data.json` is the exact input schema customers will provide
- 107 existing PDF outputs serve as test cases and quality benchmarks
- `stripe_payments.py` has `create_checkout_session()` ready to use
- `google_drive_share.py` has `upload_and_share()` ready to use
- `send_onboarding_email.py` has email template infrastructure ready
- `pdf_outputs.py` and `markdown_to_pdf.py` have pandoc integration ready
- Python Bridge API (`agent_bridge_api.py`) has `/command/execute` for running any script

---

## Infrastructure Reuse

### Existing Components That Map Directly

| Component | Existing Code | Reuse Level | Adaptation Needed |
|-----------|--------------|-------------|-------------------|
| **Resume data schema** | `resume/src/resume_data.json` | 100% | None -- this IS the input format |
| **Tailoring workflow** | `resume/workflows/tailor-resume-for-role.md` | 95% | Convert 10 manual steps to Python |
| **107 example outputs** | `resume/output/*.pdf` | 100% | Use as test cases and quality benchmarks |
| **Stripe checkout** | `execution/stripe_payments.py` | 90% | Add "resume_generation" to service catalog |
| **Stripe webhook** | `execution/stripe_webhook_server.py` | 80% | Add resume-specific event handler |
| **Google Drive delivery** | `execution/google_drive_share.py` | 100% | Use `upload_and_share()` directly |
| **Email templates** | `execution/send_onboarding_email.py` | 70% | Adapt template for "your resume is ready" |
| **PDF generation** | `execution/markdown_to_pdf.py` + `pdf_outputs.py` | 90% | Use existing pandoc commands |
| **n8n instance** | EC2 at 34.193.98.97:5678 | 100% | Add one new workflow |
| **Python Bridge** | `execution/agent_bridge_api.py` on :5010 | 100% | Use `/command/execute` endpoint |
| **Claude API** | Anthropic credentials on EC2 | 100% | Use existing key |
| **Error alerting** | n8n error workflow → Telegram | 100% | Already configured |

### Net-New Code Required

| Component | Effort | Size |
|-----------|--------|------|
| `job_parser.py` | 2-3 hours | ~100 lines |
| `resume_generator.py` | 3-4 hours | ~200 lines |
| `cover_letter_gen.py` | 2-3 hours | ~150 lines |
| `pdf_builder.py` | 1-2 hours | ~80 lines |
| n8n workflow (8 nodes) | 4-6 hours | Visual editor |
| Landing page (3 HTML files) | 4-6 hours | ~500 lines total |
| **Total new code** | **16-24 hours** | **~1,030 lines + workflow** |

---

## Scalability Limits

### EC2 t3.medium Capacity

| Resource | Available | Per Generation | Max Concurrent |
|----------|-----------|----------------|----------------|
| vCPU | 2 (burstable) | 0.1 CPU avg (mostly waiting on Claude API) | ~20 |
| RAM | 4 GB | ~50 MB per Python process | ~60 |
| Network | Up to 5 Gbps | ~500KB (PDFs + API calls) | Not a bottleneck |
| Disk I/O | Moderate | ~1MB temp files | Not a bottleneck |

**Realistic throughput: 5-10 concurrent generations** (limited by CPU burst credits and n8n worker threads).

**At 5 concurrent = ~100-200 resumes/hour** (each generation takes 30-90 seconds).

### Scaling Path

| Scale | Monthly Volume | Infrastructure | Cost |
|-------|---------------|----------------|------|
| **MVP** (current) | 0-500 resumes | EC2 t3.medium as-is | $0 incremental |
| **Growth** | 500-2,000 | Upgrade to t3.large (8GB RAM) | +$30/mo |
| **Scale** | 2,000-10,000 | Dedicated c5.xlarge or queue system | +$100/mo |
| **Beyond** | 10,000+ | Migrate to SaaS architecture (different agent's approach) | Redesign |

The n8n approach works well up to ~2,000 resumes/month. Beyond that, the queue becomes a bottleneck and you should migrate to a proper SaaS (see other agents' proposals).

---

## Competitive Positioning

### "Done-For-You AI Resume Tailoring" vs. Market

| Feature | DIY Builders (Canva, Resume.io) | AI Assistants (Teal, Rezi) | Pro Writers ($200+) | **Us (n8n webhook)** |
|---------|------|------|------|------|
| Price | $3-8/mo | $5-29/mo | $100-400 | **$9.99 one-time** |
| ATS optimization | Basic | Good | Excellent | **Excellent** |
| Cover letter | Template | AI-assisted | Human-written | **AI-tailored to specific job** |
| Personalization | You do it | Semi-auto | Full | **Full auto (paste job, get resume)** |
| Time to result | 30-60 min | 15-30 min | 3-7 days | **2-3 minutes** |
| Output format | PDF | PDF | PDF/DOCX | **PDF via Google Drive** |
| Revisions | Unlimited | Unlimited | 1-2 rounds | **None (new generation = new purchase)** |

### Unique Selling Proposition

**"Paste the job posting. Get a tailored resume and cover letter in 2 minutes. $9.99."**

This positions us between the DIY tools (cheaper but require effort) and professional writers (better quality but expensive and slow). The key differentiator is:

1. **Zero effort from the customer** -- they paste, we generate
2. **Job-specific tailoring** -- not a template, but Claude analyzing THEIR experience against THIS job
3. **Instant delivery** -- not days, not hours, but minutes
4. **Affordable** -- less than lunch, for a professionally tailored resume

### Weaknesses vs. Competitors

- No template gallery or visual editor (users who want control will go elsewhere)
- No revision capability (one-shot output)
- No ATS score preview (competitors show "match percentage")
- No LinkedIn optimization or interview prep bundled in
- Brand new with no reviews or social proof

---

## SCORES

| Criterion | Score | Justification |
|-----------|-------|---------------|
| **Revenue Potential** | 3/5 | Solid per-use margins (93%), but ceiling is low. Per-use pricing means revenue scales linearly with sales, no recurring MRR. At $10/sale, need volume to reach meaningful revenue. Tops out at ~$5K/mo before scaling issues force a rewrite. |
| **Time to Market** | 5/5 | Fastest of all approaches. 3-5 days to MVP. Nearly everything exists: Stripe, n8n, Python Bridge, Google Drive, email, pandoc. Just need to wire them together. |
| **Build Complexity** | 5/5 | (5 = low complexity, easy to build). ~1,030 lines of new code + one n8n workflow. All patterns are proven: webhook triggers, Claude API calls, pandoc PDFs, Gmail delivery. No new frameworks, no new infrastructure. |
| **Target Market Size** | 3/5 | Large addressable market (~6M active job seekers) but highly competitive. Per-use model appeals to a subset who want "done for them" rather than DIY tools. Niche but real. |
| **Maintenance Burden** | 4/5 | Very low. n8n workflows are visual and easy to update. Python scripts are simple (100-200 lines each). No database to manage, no user accounts, no sessions. Main risk: EC2 uptime and Claude API changes. |
| **Scalability** | 2/5 | Hard ceiling at ~2,000 resumes/month on current EC2. Single point of failure. No queue, no workers, no horizontal scaling. Migration to SaaS required for serious growth. |
| **Infrastructure Reuse** | 5/5 | Maximum reuse of any approach. EC2, n8n, Python Bridge, Stripe, Google Drive, Gmail, pandoc, Claude API credentials -- all existing and production-ready. Net new infrastructure: zero. |

### Score Summary

| Criterion | Stars |
|-----------|-------|
| Revenue Potential | 3 |
| Time to Market | 5 |
| Build Complexity | 5 |
| Target Market Size | 3 |
| Maintenance Burden | 4 |
| Scalability | 2 |
| Infrastructure Reuse | 5 |
| **Average** | **3.86 / 5** |

---

## Recommendation

**Ship this first as a validation experiment, then decide on scaling approach.**

The n8n webhook approach is the perfect "proof of concept with revenue." For 3-5 days of work and $0 in new infrastructure costs, we get a live product that tests whether people will pay $10 for an AI-tailored resume. If they do, the revenue from early sales funds the migration to a more scalable architecture (SaaS platform from another agent's approach). If they don't, we've lost 3-5 days instead of 4-8 weeks.

This is the **lean startup play**: build the simplest version that can take real money, measure demand, then invest in scale only after validation.

**Key decision point:** If this service generates >100 sales/month within 60 days, invest in the SaaS migration. If <20 sales/month after 60 days, the market signal is weak and we should not invest further.
