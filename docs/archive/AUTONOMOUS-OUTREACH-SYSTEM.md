# Autonomous Cold Outreach System — Full Pipeline Design

**Goal:** Maximize automation without sacrificing outreach quality
**Philosophy:** Automate the repetitive, keep humans for high-judgment moments

---

## Executive Summary

**Recommended Hybrid System:**
- **95% Autonomous:** Lead gen → Scoring → Initial outreach → Follow-ups → Meeting booking
- **5% Human (You):** Hot lead callbacks, discovery calls, proposal customization, closing

**Expected Results:**
- 50-100 qualified leads/week on autopilot
- 3-5 booked discovery calls/week
- Your time: ~2-3 hours/week (calls + closings only)

---

## Full Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AUTONOMOUS COLD OUTREACH SYSTEM                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STAGE 1: LEAD ACQUISITION (100% Autonomous)                            │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │
│  │ Apollo.io    │   │ Sunbiz       │   │ Google Maps  │                │
│  │ People Search│ + │ FL Business  │ + │ Local Search │                │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘                │
│         └──────────────────┼──────────────────┘                         │
│                            ▼                                             │
│  STAGE 2: SCORING & QUALIFICATION (100% Autonomous)                     │
│  ┌─────────────────────────────────────────────────────┐                │
│  │ Pain Point Detection (no website, no booking, etc.) │                │
│  │ Company Size Filter (1-50 employees)                │                │
│  │ Decision Maker Verification (Owner/Manager)         │                │
│  │ Contact Quality (verified email + phone)            │                │
│  └──────────────────────┬──────────────────────────────┘                │
│                         ▼                                                │
│         ┌───────────────┼───────────────┐                               │
│         │               │               │                               │
│    Score 8-10      Score 5-7       Score 1-4                           │
│    (HOT)           (WARM)          (COLD)                              │
│         │               │               │                               │
│         ▼               ▼               ▼                               │
│                                                                          │
│  STAGE 3: MULTI-CHANNEL OUTREACH (95% Autonomous)                       │
│  ┌─────────────────────────────────────────────────────┐                │
│  │                                                      │                │
│  │  HOT (8-10):     Email Day 0 → SMS Day 1 → Call Day 2               │
│  │  WARM (5-7):     Email Day 0 → Email Day 3 → SMS Day 7              │
│  │  COLD (1-4):     Email only (3 touches, then archive)               │
│  │                                                      │                │
│  └──────────────────────┬──────────────────────────────┘                │
│                         ▼                                                │
│  STAGE 4: RESPONSE HANDLING (90% Autonomous)                            │
│  ┌─────────────────────────────────────────────────────┐                │
│  │ Email Reply Detection → Classify (interested/not)   │                │
│  │ SMS Reply Detection → Classify + Auto-respond       │                │
│  │ Call Detection → Voice AI handles initial convo     │                │
│  └──────────────────────┬──────────────────────────────┘                │
│                         ▼                                                │
│         ┌───────────────┼───────────────┐                               │
│         │               │               │                               │
│   INTERESTED      QUESTIONS        NOT NOW                             │
│         │               │               │                               │
│         ▼               ▼               ▼                               │
│   Book Call       AI Answers      Nurture Sequence                     │
│   (Calendly)      + Escalate      (Monthly touchpoint)                 │
│         │               │                                               │
│         └───────┬───────┘                                               │
│                 ▼                                                        │
│  STAGE 5: DISCOVERY CALL (Human Required)                               │
│  ┌─────────────────────────────────────────────────────┐                │
│  │ Pre-call briefing sent to you (auto-generated)      │                │
│  │ → YOU run 15-min discovery call                     │                │
│  │ → Log outcome in pipeline                           │                │
│  └──────────────────────┬──────────────────────────────┘                │
│                         ▼                                                │
│  STAGE 6: PROPOSAL (80% Autonomous)                                     │
│  ┌─────────────────────────────────────────────────────┐                │
│  │ Auto-generate proposal PDF from call notes          │                │
│  │ You review/customize (5 min)                        │                │
│  │ Auto-send via email with tracking                   │                │
│  └──────────────────────┬──────────────────────────────┘                │
│                         ▼                                                │
│  STAGE 7: CLOSING (Human Required)                                      │
│  ┌─────────────────────────────────────────────────────┐                │
│  │ Follow-up sequence until decision                   │                │
│  │ → YOU handle objections + close                     │                │
│  │ → Auto-generate agreement on close                  │                │
│  └─────────────────────────────────────────────────────┘                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quality Preservation Strategy

### Where Automation HELPS Quality:
| Task | Why Automate |
|------|--------------|
| Lead scoring | Consistent criteria, no fatigue bias |
| Follow-up timing | Perfect cadence, never forget |
| Email personalization | Merge fields + AI customization at scale |
| Response classification | Fast routing to right action |
| Meeting scheduling | No back-and-forth, instant booking |

### Where Humans are ESSENTIAL:
| Task | Why Human |
|------|-----------|
| Discovery calls | Building rapport, reading tone |
| Objection handling | Nuanced persuasion |
| Proposal customization | Tailoring to specific pain points |
| Pricing decisions | Context-dependent judgment |
| Closing | Trust-building, commitment |

---

## Recommended Tech Stack

### Email Outreach (Build Our Own)
**Why not Apollo sequences:**
- Apollo API doesn't support sequence enrollment
- We have Gmail API access already
- Full control over timing, content, tracking

**Our System:**
```
Gmail API (send) + Tracking Pixel (opens) + Reply Detection (Gmail API)
     ↓
Sequence Engine (Python) - schedules emails, handles replies
     ↓
Pipeline DB - tracks all activity per lead
```

### SMS Outreach (Already Built)
```
Twilio (send/receive) → Pipeline DB → Response Classifier
```

### Voice AI (Already Built)
```
ElevenLabs Voice AI → Call Transcripts → Auto Lead Detector
     ↓
Hot leads → Immediate notification to you
```

### Meeting Booking
```
Calendly link in all outreach → Auto-confirm → Pre-call briefing
```

---

## Implementation Plan

### Phase 1: Email Sequence Engine (Priority — 3 hours)
Build autonomous email sender with:
- Gmail API integration (we have tokens)
- Your templates from `docs/apollo-sequence-templates.txt`
- Open/click tracking
- Reply detection + auto-stop sequence
- Personalization (first name, company, pain points)

**Deliverable:** `execution/email_sequence_engine.py`

### Phase 2: Unified Pipeline Orchestrator (2 hours)
Single daily job that:
1. Pulls new leads from Apollo (auto-search based on saved criteria)
2. Scores and filters
3. Enrolls in appropriate sequence (email/SMS/call based on score)
4. Processes replies from all channels
5. Updates pipeline status

**Deliverable:** Enhanced `projects/lead-generation/src/orchestrator.py`

### Phase 3: Smart Response Handler (2 hours)
AI-powered response classification:
- "Interested" → Book meeting link + notify you
- "Questions" → AI drafts answer, you approve (one-click)
- "Not now" → Move to nurture sequence
- "Unsubscribe" → Remove + comply

**Deliverable:** `execution/response_handler.py`

### Phase 4: Pre-Call Briefing Generator (1 hour)
Before each discovery call:
- Company research summary
- Pain points detected
- Previous outreach history
- Suggested talking points
- Sent to you 30 min before call

**Deliverable:** `execution/call_prep.py`

---

## Daily Autonomous Flow

**6:00 AM — Lead Acquisition**
- Apollo search runs with saved criteria
- New leads scored and imported to pipeline

**6:30 AM — Morning Digest to You**
- New leads summary
- Today's follow-ups due
- Any hot responses overnight

**9:00 AM — Outreach Execution**
- Day 0 emails sent to new leads
- Follow-up emails sent per sequence
- SMS sent where appropriate

**Throughout Day — Response Monitoring**
- Email replies detected every 15 min
- SMS replies handled in real-time
- Voice AI calls reported

**9:00 PM — Evening Digest to You**
- Day's activity summary
- Hot leads needing callback
- Meetings booked

**Your Only Tasks:**
1. Review hot lead notifications → Call back within 1 hour
2. Take discovery calls (auto-scheduled)
3. Review/send proposals (auto-generated)
4. Close deals

---

## Quality Safeguards

### Email Quality
- Templates written in your voice (Hormozi framework)
- Personalization beyond just {{first_name}} — include pain points
- Send from your real email (wmarceau@marceausolutions.com)
- Daily send limit: 50/day (protect deliverability)

### SMS Quality  
- Only to verified mobile numbers
- Opt-out honored immediately
- Conversational tone, not salesy

### Call Quality
- Voice AI trained on your prompts
- Escalates complex questions to you
- Never pretends to be you

### Follow-up Quality
- Respectful cadence (no spam)
- Stop on any negative signal
- Value-add content, not just "checking in"

---

## Metrics to Track

| Metric | Target | How |
|--------|--------|-----|
| Leads generated/week | 100+ | Apollo + scraper |
| Emails sent/week | 300 | Sequence engine |
| Open rate | >40% | Tracking pixel |
| Reply rate | >5% | Gmail API |
| Meetings booked/week | 5+ | Calendly |
| Close rate | 20%+ | Pipeline tracking |

---

## Decision: Build vs Buy

| Option | Pros | Cons |
|--------|------|------|
| **Build Email Sequence (Recommended)** | Full control, no monthly cost, integrates with our pipeline | 3 hours to build |
| Apollo Sequences | Already exists | No API access, manual CSV upload |
| Instantly.ai / Lemlist | Built for cold email | $97+/mo, separate system, data sync issues |
| Mailshake | Good tracking | $58/mo, another tool to manage |

**Recommendation:** Build our own. We have all the pieces, it integrates directly with pipeline.db, and we control everything.

---

## Next Steps

1. **Approve this plan** → I build Phase 1-4 over ~8 hours
2. **Or adjust** → Tell me what to change
3. **Timeline:** Can have Phase 1 (email engine) working today

Want me to start building?
