# Elder Tech Concierge

> White-glove AI assistant setup and support for seniors

**Version:** 0.1.0-dev
**Status:** Planning/Pre-Development
**Market Score:** 4.55/5 (STRONG GO)

---

## Overview

Elder Tech Concierge is an in-home service that provides personalized AI assistant setup and ongoing support for seniors and those who struggle with technology. We leverage Claude AI to create accessible, voice-first interfaces that help seniors:

- Stay connected with family (video calls, text messages)
- Manage health (medication reminders, appointment scheduling)
- Stay safe (scam detection, emergency contacts)
- Maintain independence (email management, daily briefings)

## The Problem

**58 million Americans are 65+**, and 45% struggle with technology. This leads to:

- **Social isolation** - Can't video call grandkids or text family
- **Safety risks** - Vulnerable to phone/email scams (billions lost annually)
- **Health impacts** - Missed medications, forgotten appointments
- **Family burden** - Adult children become unpaid tech support

Current solutions (Geek Squad, YouTube tutorials) are either too generic, too intimidating, or too complex for seniors.

## Our Solution

**Human service + AI technology** = White-glove tech concierge

1. **In-home consultation** - Understand the senior's needs and setup their environment
2. **Personalized AI assistant** - Claude-powered tablet with voice-first interface
3. **Ongoing support** - Monthly check-ins, remote troubleshooting, family dashboard

## Target Market

| Segment | Description | Role |
|---------|-------------|------|
| **Primary** | Seniors 65-85 | End users |
| **Secondary** | Adult children 40-60 | Purchasers/monitors |
| **Tertiary** | Senior living communities | B2B partnership |

## Business Model

| Tier | Setup Fee | Monthly | Annual Value |
|------|-----------|---------|--------------|
| **Essential** | $299 | $49 | $887 |
| **Premium** | $499 | $99 | $1,687 |

**Unit Economics:**
- Gross margin: 70%+
- LTV:CAC ratio: 10x+
- Break-even: 10 customers

## Technical Architecture

```
+------------------+     +-------------------+     +------------------+
|  iPad Tablet     |<--->|  Backend API      |<--->|  External APIs   |
|  (Voice + Touch) |     |  (FastAPI/Python) |     |  (Claude, etc.)  |
+------------------+     +-------------------+     +------------------+
                               |
                               v
                        +------------------+
                        |  Family Dashboard |
                        |  (Web App)        |
                        +------------------+
```

**Key Integrations:**
- Claude API (Anthropic) - Core AI
- Twilio - SMS messaging
- Gmail API - Email management
- Google Calendar - Appointments
- Apple Speech - Voice interface

## Project Structure

```
elder-tech-concierge/
├── KICKOFF.md              # Completed kickoff questionnaire
├── README.md               # This file
├── VERSION                 # Current version
├── CHANGELOG.md            # Version history
├── market-analysis/        # SOP 17 research
│   ├── VIABILITY-SCORECARD.md
│   ├── TECHNICAL-FEASIBILITY.md
│   └── GO-NO-GO-DECISION.md
├── src/                    # Source code
│   └── __init__.py
├── docs/                   # Documentation
│   └── MVP-SPEC.md         # MVP specification
└── workflows/              # Task procedures
    └── setup-client.md     # Client onboarding
```

## Development Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1: Core** | Weeks 1-6 | Voice interface, SMS, email reading, reminders |
| **Phase 2: Enhancement** | Weeks 7-10 | Calendar sync, appointment booking, family notifications |
| **Phase 3: Polish** | Weeks 11-14 | Beta testing, accessibility audit, launch prep |

## Getting Started (Development)

```bash
# Navigate to project
cd /Users/williammarceaujr./dev-sandbox/projects/elder-tech-concierge

# View market research
cat market-analysis/VIABILITY-SCORECARD.md

# View MVP specification
cat docs/MVP-SPEC.md

# View client onboarding workflow
cat workflows/setup-client.md
```

## Key Documents

| Document | Purpose |
|----------|---------|
| [KICKOFF.md](KICKOFF.md) | Project kickoff questionnaire (SOP 0) |
| [VIABILITY-SCORECARD.md](market-analysis/VIABILITY-SCORECARD.md) | Market analysis results |
| [TECHNICAL-FEASIBILITY.md](market-analysis/TECHNICAL-FEASIBILITY.md) | Technical architecture research |
| [MVP-SPEC.md](docs/MVP-SPEC.md) | MVP feature specification |
| [setup-client.md](workflows/setup-client.md) | Client onboarding procedure |

## Success Metrics

**Launch Criteria (before charging full price):**
- [ ] 10 successful beta setups
- [ ] 5+ positive testimonials
- [ ] Setup time < 3 hours consistently
- [ ] Support < 2 hours/customer/month
- [ ] 3+ organic referrals

**Year 1 Targets:**
- 50-100 customers
- $50K-150K revenue
- <5% monthly churn
- NPS > 50

## Risk Factors

| Risk | Mitigation |
|------|------------|
| Senior adoption resistance | Lead with "assistant" not "AI", extensive demos |
| High churn (mortality/care transitions) | Target "younger old" (65-75), family as payers |
| Healthcare integration complexity | Start with email-based booking, build partnerships |
| Regulatory uncertainty | Conservative data handling, no PHI storage |

## Contact

**Project Lead:** William Marceau Jr.
**Location:** dev-sandbox/projects/elder-tech-concierge

---

*Created: 2026-01-16*
*Last Updated: 2026-01-16*
