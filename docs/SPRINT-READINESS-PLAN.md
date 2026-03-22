# Sprint Readiness Plan — AI Client Acquisition (March 23 – April 5, 2026)

> Consolidated plan: website updates, architecture improvements, and resource inventory.
> Created: 2026-03-22 | Sprint starts: 2026-03-23 | Job orientation: 2026-04-06

---

## Goal

Land **1 paying AI automation client** before William starts at Collier County Wastewater (April 6).

---

## 1. Website Restructure — Status

Based on [WEBSITE-RESTRUCTURE-PLAN.md](../projects/marceau-solutions/digital/website/WEBSITE-RESTRUCTURE-PLAN.md) (created Feb 3, 2026):

### Phase 1 (Core Pages) — DONE
| Task | Status | Notes |
|------|--------|-------|
| Create `peptides.html` | ✅ Live | Evidence-based positioning, medical disclaimer |
| Rewrite `index.html` | ✅ Live | Dual offering: fitness + AI services |
| Update navigation across all pages | ✅ Uncommitted | Consistent nav on all 10 pages |

### Phase 2 (Secondary Pages) — DONE
| Task | Status | Notes |
|------|--------|-------|
| Create `coaching.html` | ✅ Live | $197/mo offer, FAQ accordion, Calendly |
| Create `programs.html` | ✅ Live | 4-tier funnel (Free → Premium), Stripe links |
| Create `for-influencers.html` | ✅ Live | B2B backend automation pitch |

### Phase 3 (Polish) — PARTIAL
| Task | Status | Notes |
|------|--------|-------|
| Update `about.html` | ✅ Uncommitted | Strong narrative, proper meta tags |
| Add testimonials/social proof | ❌ Not done | No testimonials on any page yet |
| Embed YouTube content | ❌ Not done | `peptides.html` has video placeholder only |
| Set up form flows | ⚠️ Partial | Calendly embedded; contact form → n8n unclear |

### Additional Work (Not in Original Plan)
| Work | Status | Notes |
|------|--------|-------|
| `ai-automation.html` major rewrite | ✅ Uncommitted (+758/-373 lines) | **Key sprint asset** — SEO, OG tags, Calendly, 4 service cards, case study metrics, pricing |
| `challenge.html` updates | ✅ Uncommitted | 7-day challenge signup, webhook wired |
| `quiz.html` updates | ✅ Uncommitted | Body recomp calculator, n8n integration |
| `contact.html` updates | ✅ Uncommitted | Multiple CTAs, Calendly embed |

### Website Files Ready to Commit & Deploy
| File | Ready? | Issue |
|------|--------|-------|
| `about.html` | ✅ Yes | — |
| `ai-automation.html` | ⚠️ 95% | Missing phone link in footer |
| `challenge.html` | ✅ Yes | — |
| `coaching.html` | ✅ Yes | — |
| `contact.html` | ✅ Yes | — |
| `for-influencers.html` | ✅ Yes | — |
| `index.html` | ✅ Yes | — |
| `peptides.html` | ⚠️ 94% | Video placeholder — remove or embed real video |
| `programs.html` | ✅ Yes | "Coming soon" premium tier is clearly labeled |
| `quiz.html` | ✅ Yes | — |

---

## 2. Architecture & Systems Improvements — Status

### Session 14 (March 22) — 5 Prevention Systems Built

Root cause: Audit of 40 historical EC2/Clawdbot failures; 37 were preventable.

| System | What It Does | File | Status |
|--------|-------------|------|--------|
| **Credential Lifecycle** | Live validation of Google token + Twilio webhooks (not just key existence) | `scripts/health_check.py` | ✅ Deployed |
| **Sync Verification** | EC2 sync verified after every push; Telegram alert on drift | `.claude/hooks/post-push-ec2-sync.sh` | ✅ Deployed |
| **Service Stability** | Clawdbot restart count, n8n symlink, journald size monitoring | `scripts/health_check.py` | ✅ Deployed |
| **Workflow Validator** | Scans all n8n workflows for 7 silent failure patterns | `scripts/n8n_workflow_validator.py` | ✅ Deployed |
| **Quality Drift** | SOUL.md version check, ARCHITECTURE-DECISIONS.md presence on EC2 | `scripts/health_check.py` | ✅ Deployed |

### Cross-Agent Quality Standards (Session 14)
| Improvement | Status |
|------------|--------|
| ARCHITECTURE-DECISIONS.md updated with E10, interface-first, sync architecture | ✅ |
| Clawdbot SOUL.md upgraded to v2.1.0 | ✅ |
| Gmail re-authed with 6 scopes, `/gmail/draft` endpoint on agent bridge | ✅ |
| Calendar reorganized (training 3pm, recurring events for new job) | ✅ |
| Post-push hook upgraded from fire-and-forget to verified sync | ✅ |

### Infrastructure State
- **38 active n8n workflows, 0 failures**
- **EC2**: All 6 services running (n8n, Clawdbot, mem0, FitAI, voice-api, webhook_server)
- **Daily health check**: 7am launchd (Mac) — covers all 5 prevention systems
- **Accountability**: Morning briefing 5am, EOD 7pm, Weekly Sunday 7pm

---

## 3. Sprint Resource Inventory

### Sales Pages & Landing
| Resource | Location | State |
|----------|----------|-------|
| AI Automation sales page | `projects/marceau-solutions/digital/website/ai-automation.html` | ✅ Complete (uncommitted) |
| Voice AI landing page | `projects/shared/ai-customer-service/static/voice-ai-landing.html` | ✅ Complete |

### Case Studies & Proof
| Resource | Location | State |
|----------|----------|-------|
| HVAC case study (1,330% ROI, $12.4K/month) | `projects/shared/ai-customer-service/marketing/HVAC-CASE-STUDY.md` | ✅ Production-ready |
| Live voice AI demo | Call (239) 766-6129 | ✅ Live |

### Discovery & Sales Scripts
| Resource | Location | State |
|----------|----------|-------|
| Discovery call script (20-30 min) | `projects/shared/ai-customer-service/marketing/DISCOVERY-CALL-SCRIPT.md` | ✅ Complete |
| Proposal template (3 tiers + ROI calculator) | `projects/shared/ai-customer-service/marketing/PROPOSAL-TEMPLATE.md` | ✅ Complete |

### Outreach Templates
| Resource | Location | State |
|----------|----------|-------|
| SMS templates (6 variants + follow-up sequence) | `projects/shared/ai-customer-service/marketing/SMS-OUTREACH-TEMPLATES.md` | ✅ Complete |
| First 10 Naples leads (hand-picked) | `projects/shared/ai-customer-service/marketing/VOICE-AI-FIRST-10-LEADS.md` | ✅ Ready |
| Product marketing strategy (TAM/SAM analysis) | `projects/shared/ai-customer-service/marketing/PRODUCT-MARKETING-STRATEGY.md` | ✅ Complete |

### Video & Demo Assets
| Resource | Location | State |
|----------|----------|-------|
| YouTube script: "Dispatch vs My System" (14 min) | `projects/marceau-solutions/media/tools/youtube-creator/scripts/dispatch-vs-my-system-video-script.md` | ✅ Ready to film |
| Video script (JSON + PDF versions) | Same dir, `.json` and `.pdf` | ✅ Generated |
| Loom demo playbook | `docs/loom-demo-playbook.pdf` | ✅ PDF ready |

### Booking & Scheduling
| Resource | URL | State |
|----------|-----|-------|
| AI Services Discovery Call | `calendly.com/wmarceau/ai-services-discovery-call` | ✅ Live, embedded on website |
| Voice AI Demo Call | `calendly.com/wmarceau/voice-ai-demo` | ✅ Live |
| Fitness Strategy Call | `calendly.com/wmarceau/free-fitness-strategy-call` | ✅ Live |

### Outreach Automation
| Resource | Location | State |
|----------|----------|-------|
| SMS outreach (webhook-triggered) | n8n: `Fitness-SMS-Outreach` (`89XxmBQMEej15nak`) | ✅ Active |
| Follow-up drip sequence | n8n: `Fitness-SMS-Followup-Sequence` (`VKC5cifm595JNcwG`) | ✅ Active |
| Automation lead capture | n8n: `Automation-Lead-Capture` (`dATO8F4MoPcpOKiA`) | ✅ Active |
| Naples prospect list builder | `scripts/build-naples-prospect-list.py` | ✅ Ready to run |
| Lead manager | `execution/lead_manager.py` | ✅ Ready |
| Warm SMS outreach | `execution/warm_outreach_sms.py` | ✅ Ready |

### Sprint Calendar
| Resource | Location | State |
|----------|----------|-------|
| 14-day sprint calendar (JSON) | `scripts/sprint-calendar-events.json` | ✅ Ready for Google Calendar import |

### Leave-Behind / Print Materials
| Resource | Location | State |
|----------|----------|-------|
| Leave-behind PDF template | `execution/pdf_templates/leave_behind_template.py` | ⚠️ Template exists, PDF not yet generated |

### Proposal Templates
| Resource | Location | State |
|----------|----------|-------|
| Voice AI proposal (3 tiers + ROI) | `projects/shared/ai-customer-service/marketing/PROPOSAL-TEMPLATE.md` | ✅ |
| Digital storefront proposal | `projects/shared/personal-assistant/templates/proposals/digital-storefront-proposal.md` | ✅ |
| Enterprise package proposal | `projects/shared/personal-assistant/templates/proposals/enterprise-package-proposal.md` | ✅ |
| Growth system proposal | `projects/shared/personal-assistant/templates/proposals/growth-system-proposal.md` | ✅ |

---

## 4. What Needs to Happen Today (March 22)

### CRITICAL — Must complete before sprint starts
| # | Task | Time | Why |
|---|------|------|-----|
| 1 | Commit & deploy website changes (10 files) | 15 min | ai-automation.html is the main sales page for the sprint |
| 2 | Generate leave-behind PDF from template | 20 min | In-person visits start Mar 25 — need printed materials |
| 3 | Run prospect list builder (500 Naples businesses) | 10 min | Cold outreach wave 1 starts Mar 25 |

### HIGH — Should complete today
| # | Task | Time | Why |
|---|------|------|-----|
| 4 | Fix `ai-automation.html` footer (add phone link) | 2 min | Polish before deploy |
| 5 | Fix `peptides.html` video placeholder (remove or embed) | 2 min | Don't leave "coming soon" placeholder live |
| 6 | Import sprint calendar events to Google Calendar | 5 min | Daily structure starts tomorrow |

### MEDIUM — Can do Day 1 of sprint
| # | Task | Time | Why |
|---|------|------|-----|
| 7 | Create cold email 3-step sequence templates | 30 min | Cold email starts Mar 25 |
| 8 | Add AI-automation-specific SMS templates to `warm_outreach_sms.py` | 15 min | SMS outreach starts Mar 23 |
| 9 | Set up Loom account + test recording | 10 min | Loom demos start Mar 25 |

---

## 5. Sprint Milestones (from memory)

| Date | Milestone |
|------|-----------|
| Mar 25 | YouTube video filmed |
| Mar 27 | First outreach batch sent (50+ actions) |
| Apr 2 | Follow-ups complete, second batch, 2-3 calls booked |
| Apr 3 | GOAL — first client signed |
| Apr 6 | Job orientation (Collier County Wastewater) |

---

## 6. Communication Flow

```
Prospect List (Apollo) → Cold Email/SMS → Auto Follow-up (n8n)
                                              ↓
                                    Calendly Booking
                                              ↓
                                  Telegram Alert → William
                                              ↓
                                    Discovery Call (script ready)
                                              ↓
                                    Custom Proposal (template ready)
                                              ↓
                                    Close → Stripe → Welcome Workflow
```

---

*This document replaces scattered context across HANDOFF.md, session-history.md, and memory files with a single sprint reference.*
