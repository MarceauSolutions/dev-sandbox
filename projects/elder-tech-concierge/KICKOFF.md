# Project Kickoff Questionnaire: Elder Tech Concierge

**Completed:** 2026-01-16
**Completed by:** Agent 6 (SOP 0)
**Based on:** Market Viability Analysis (SOP 17) - Score: 4.55/5

---

## Part 1: Business & Purpose (Questions 1-5)

### Q1. What problem does this solve?
> _One sentence describing the core problem_

**Answer:** Seniors are being left behind by rapidly advancing technology, leading to social isolation, vulnerability to scams, missed medical appointments, and health impacts from forgotten medications.

---

### Q2. Who are the primary users?
- [ ] AI Agents (via MCP Aggregator)
- [ ] Developers (CLI/API)
- [x] End Users (Web/Mobile/Desktop interface)
- [ ] Internal (Personal automation)
- [x] Other: Adult children/family members (as purchasers and remote monitors)

**Details:**
- **Primary:** Seniors aged 65+ who struggle with technology
- **Secondary:** Adults aged 55-65 needing tech assistance
- **Tertiary:** Adult children wanting to help aging parents remotely

---

### Q3. What's the success metric?
- [x] Revenue (per-transaction, subscription)
- [x] Time Saved (hours/month)
- [x] User Count (MAU target)
- [x] Other: NPS (Net Promoter Score), Churn Rate

**Targets:**
| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| Customers | 50-100 | 200-400 | 500-1,000 |
| MRR | $2,500-7,500 | $12,000-30,000 | $35,000-75,000 |
| Churn Rate | <5%/month | <4%/month | <3%/month |
| NPS | 50+ | 60+ | 70+ |

---

### Q4. What's the timeline constraint?
- [ ] Days (< 1 week)
- [ ] Weeks (1-4 weeks)
- [x] Months (1-3 months)
- [ ] No constraint

**Details:**
- **MVP Target:** 8-14 weeks (conservative)
- **Beta Launch:** 10 customers within Month 2-3
- **Full Launch:** Month 4+

---

### Q5. Is this MCP Aggregator compatible?

Check if ALL are true:
- [ ] Value is in data/computation (not UI/UX differentiation) - **NO: UX is critical for senior accessibility**
- [ ] Transaction-based revenue makes sense - **Partially: Subscription model preferred**
- [ ] Natural AI agent integration - **Yes: Uses Claude as backend**
- [ ] Multi-platform distribution helps - **No: Local service business**

**MCP Compatible:** No

**Rationale:** This is a consumer service business targeting seniors who are NOT Claude users. The value proposition is human service + simplified AI interface, not AI capability distribution. The differentiator is the white-glove setup and ongoing support, not the underlying technology.

---

## Part 2: Technical Requirements (Questions 6-10)

### Q6. What's the primary connectivity pattern?
- [x] HTTP - Real-time APIs (<500ms response)
- [x] EMAIL - Email-based workflows (hours/days)
- [x] OAUTH - Token-based auth services
- [ ] WEBHOOK - Inbound push notifications
- [ ] GRAPHQL - Complex query APIs
- [ ] ASYNC - Long-running batch operations
- [ ] None (standalone app)

**Details:**
- **Claude API:** HTTP (real-time voice/text responses)
- **Gmail API:** OAuth + HTTP (email reading/sending)
- **Google Calendar API:** OAuth + HTTP (appointment management)
- **Twilio:** HTTP (SMS messaging)

---

### Q7. Does it need persistent data storage?
- [ ] No - Stateless operations
- [ ] Yes - Simple key-value / JSON files
- [x] Yes - Relational database (PostgreSQL, SQLite)
- [ ] Yes - Document database (MongoDB)
- [ ] Yes - Time-series / analytics data

**Data volume estimate:**
- User profiles: ~100-1,000 records (Year 1-3)
- Conversation logs: ~10-50 MB/month
- Contact directories: ~500-5,000 contacts total
- Calendar events: ~1,000-10,000/year

**Database choice:** PostgreSQL via Supabase (managed, includes auth)

---

### Q8. Real-time or batch processing?
- [ ] Real-time only (immediate response required)
- [ ] Batch only (can process in background)
- [x] Both (real-time with async fallback)

**Details:**
- **Real-time:** Voice interactions, quick queries
- **Batch/Async:** Email digests, daily briefings, reminder scheduling

---

### Q9. What external integrations are needed?
> _List all external services, APIs, or platforms_

| Service | Purpose | Has Free Tier? | Existing in dev-sandbox? |
|---------|---------|----------------|--------------------------|
| Claude API (Anthropic) | Core AI assistant | Yes (limited) | Yes |
| Twilio | SMS messaging | Yes ($15 credit) | Yes (`execution/twilio_sms.py`) |
| Gmail API | Email read/send | Yes (free) | Yes (`execution/gmail_monitor.py`) |
| Google Calendar API | Appointments | Yes (free) | Yes (`execution/calendar_reminders.py`) |
| Apple Speech Framework | Voice-to-text | Yes (on-device) | No (iOS SDK) |
| ElevenLabs (optional) | Premium TTS | Yes (limited) | No |
| Firebase/Supabase | Auth + Database | Yes (generous) | No |
| APNS/FCM | Push notifications | Yes (free) | No |

---

### Q10. Security/privacy requirements?
- [ ] Standard (basic auth, HTTPS)
- [x] High (encryption at rest, audit logs)
- [ ] Regulated (HIPAA, GDPR, PCI compliance)

**Specific requirements:**
- **Encryption:** TLS 1.3 in transit, AES-256 at rest
- **Authentication:** Multi-factor for family accounts, simplified for seniors
- **Data retention:** User-controlled deletion, clear privacy policy
- **Audit logging:** All access logged for security
- **HIPAA note:** Avoid storing PHI in Claude conversations; extract locally only

**Why not HIPAA-regulated:**
- Not storing protected health information (PHI)
- Appointment booking via email (not accessing medical records)
- If health features expand, may need HIPAA compliance later

---

## Part 3: App Type Decision (Questions 11-13)

### Q11. How will users access this?
- [ ] CLI (command line)
- [ ] Web Browser
- [ ] Desktop Application
- [ ] AI Agent (MCP protocol)
- [ ] API (programmatic access)
- [x] Multiple access methods

**Primary:** Tablet app (iPad) with voice interface
**Secondary:** SMS (text messaging)
**Tertiary:** Family web dashboard (future)

---

### Q12. Does it need a user interface?
- [ ] No UI needed (AI handles presentation)
- [ ] Simple UI (terminal output, basic forms)
- [x] Complex UI (dashboard, visualizations, rich interactions)

**Details:**
- **Senior Interface:** Large buttons, high contrast, voice-first, minimal cognitive load
- **Family Interface:** Dashboard showing senior's status, calendar, alerts
- **Admin Interface:** Customer management, support ticketing

---

### Q13. What's the deployment target?
- [ ] Local only (runs on user's machine)
- [ ] Cloud only (hosted service)
- [x] Both (local dev, cloud production)
- [ ] Edge (CDN, serverless)

**Details:**
- **Backend API:** Cloud (Railway or AWS Lambda)
- **Database:** Cloud (Supabase)
- **Tablet App:** Local (iOS app on senior's device)
- **Voice Processing:** Hybrid (on-device STT preferred, cloud fallback)

---

## Part 4: Resource Assessment (Questions 14-16)

### Q14. Estimated development hours?

Using the Cost-Benefit matrix:

| Component | Type | Hours |
|-----------|------|-------|
| iOS Tablet App | Mobile | 80-120 |
| Backend API | Web API | 40-60 |
| Integrations | Existing code leverage | 20-30 |
| Family Dashboard | Web | 40-60 |
| **Total** | Hybrid | **180-270** |

**Estimated hours:** 200 hours (conservative)

**Complexity factors:**
- Senior-accessible UX design (+30%)
- Voice interface tuning (+20%)
- Existing integrations available (-20%)

---

### Q15. Monthly operational budget?
- [ ] $0 (free tier only)
- [x] $0-50 (minimal hosting)
- [ ] $50-200 (production hosting + services)
- [ ] $200+ (scale infrastructure)

**Monthly cost breakdown (at 50 users):**
| Service | Cost |
|---------|------|
| Claude API | $250-500 |
| Hosting (Railway/Supabase) | $30-50 |
| Twilio SMS | $10-20 |
| Apple Developer | $8 (annual amortized) |
| Other | $20-30 |
| **Total** | **$320-600** |

**Per-user cost:** ~$8-12/user/month
**Subscription price:** $49-99/month
**Margin:** 70%+

---

### Q16. Who maintains this long-term?
- [x] William (manual maintenance)
- [ ] Automated (self-healing, monitoring)
- [ ] Team (multiple maintainers)
- [ ] Community (open source)

**Maintenance hours/month estimate:**
- Year 1: 20-40 hours/month (active development + support)
- Year 2: 10-20 hours/month (feature additions + support)
- Year 3: 5-10 hours/month (maintenance mode if team hired)

**Scaling plan:**
- 50 customers: Solo (William)
- 100 customers: First technician hire
- 200+ customers: Support team needed

---

## Part 5: Template Decision (Questions 17-19)

### Q17. Does a similar project exist in dev-sandbox?

Check existing projects:
- [x] Yes - Similar structure exists (specify): `personal-assistant` (Claude integration patterns)
- [x] Yes - Similar structure exists (specify): `fitness-influencer` (user-facing service with MCP backend)
- [ ] Yes - But significantly different approach
- [ ] No - Novel project type

**Reusable components:**
- `execution/twilio_sms.py` - SMS sending
- `execution/gmail_monitor.py` - Email reading
- `execution/calendar_reminders.py` - Calendar integration
- Claude API patterns from multiple projects

---

### Q18. What's the innovation level?

| Level | Description | Template Recommendation |
|-------|-------------|------------------------|
| Low | Standard implementation, proven pattern | Use full template |
| **Medium** | Some innovation, adapting known patterns | **Adapt template** |
| High | Novel architecture, exploring unknown | Clean slate |

**Innovation level:** Medium

**Rationale:**
- Core AI integration patterns exist
- Novel: Senior-accessible UX, voice-first interface
- Novel: Family dashboard and monitoring
- Adaptation: Mobile app vs CLI/web focus of existing projects

---

### Q19. Template decision?

Based on Q17 and Q18:

- [ ] **Use template** - Copy structure from: _______________
- [x] **Adapt template** - Use structure from `personal-assistant` and `fitness-influencer`, customize: Voice interface, senior UX, family dashboard
- [ ] **Clean slate** - Start fresh because: _______________

**Adaptation plan:**
1. Copy integration patterns from `execution/` (Twilio, Gmail, Calendar)
2. Build new iOS app (no existing mobile template)
3. Build new voice interface layer
4. Adapt backend API structure from existing FastAPI projects

---

## Decision Output

### App Type Selection

Based on answers above:

**Primary App Type:**
- [ ] CLI Tool
- [ ] Python Skill (Claude)
- [ ] MCP Server - Connectivity: _______________
- [ ] Web API (Backend Only)
- [ ] Full-Stack Web App
- [ ] Desktop App
- [x] Hybrid (Mobile App + Backend API + Family Web Dashboard)

**Specific type:** iOS Tablet App + FastAPI Backend + Web Dashboard (future)

### Cost Summary

| Item | Estimate |
|------|----------|
| Development Hours | 200 hours |
| Development Cost (@ $100/hr) | $20,000 (opportunity cost) |
| Monthly Hosting | $30-50 |
| Monthly APIs/Services | $300-500 |
| Monthly Maintenance Hours | 20-40 hours |

### Revenue/Value Summary

| Item | Estimate |
|------|----------|
| Revenue Model | Setup fee ($299-499) + Subscription ($49-99/mo) |
| Expected Monthly Revenue (Year 1) | $2,500-7,500 |
| Expected Monthly Revenue (Year 3) | $35,000-75,000 |
| Break-Even Timeline | 10 customers (~Month 3-4) |

### Go/No-Go Decision

- [x] **GO** - Build this project (break-even < 6 months OR clear strategic value)
- [ ] **CAUTION** - Build MVP first (break-even 6-12 months)
- [ ] **NO-GO** - Do not build (break-even > 12 months AND no strategic value)

**Rationale:**
- Market viability score: 4.55/5 (STRONG GO)
- Technical feasibility: 4/5 (existing integrations available)
- Break-even: 10 customers covers monthly costs
- LTV:CAC ratio: 10x+
- Demographic tailwind: 10,000 Americans turn 65 daily

### Next Steps

1. [x] Complete SOP 0 (Project Kickoff) - THIS DOCUMENT
2. [ ] Proceed to SOP 1 (New Project Initialization)
3. [ ] Create directive: `directives/elder-tech-concierge.md`
4. [x] Create project folder: `projects/elder-tech-concierge/`
5. [ ] Build MVP tablet interface (Phase 1)
6. [ ] Beta test with 5-10 seniors

---

## Questionnaire Completed

**Date:** 2026-01-16
**Completed by:** Agent 6 (Multi-Agent SOP 0)
**Approved by:** Pending William's review
**Market Analysis Reference:** `market-analysis/VIABILITY-SCORECARD.md`

---

## Reference Links

- [Market Viability Scorecard](market-analysis/VIABILITY-SCORECARD.md)
- [Technical Feasibility Report](market-analysis/TECHNICAL-FEASIBILITY.md)
- [Go/No-Go Decision](market-analysis/GO-NO-GO-DECISION.md)
- [App Type Decision Guide](../../docs/app-type-decision-guide.md)
- [Cost-Benefit Templates](../../docs/cost-benefit-templates.md)
- [SOP 1: New Project Initialization](../../CLAUDE.md#sop-1-new-project-initialization)
