# Project Kickoff: AI Customer Service Virtual Employees

**Date**: January 17, 2026
**Status**: SOP 0 Complete
**Market Analysis**: GO (4.15/5) - See `market-analysis/consolidated/`

---

## Part 1: Business & Purpose (Questions 1-5)

### Q1. What problem does this solve?

**Answer:** Restaurant operators face an existential labor crisis (70% unfilled positions, 80%+ turnover) causing them to miss phone orders ($27K+ lost annually) and work entry-level positions themselves - AI voice ordering eliminates this pain.

---

### Q2. Who are the primary users?
- [ ] AI Agents (via MCP Aggregator)
- [ ] Developers (CLI/API)
- [x] End Users (Web/Mobile/Desktop interface) - Restaurant owners/managers
- [ ] Internal (Personal automation)
- [ ] Other: _______________

**Primary**: Independent restaurant owners (1-10 locations), "The Overwhelmed Independent" persona
**Secondary**: Multi-unit operators looking for scalable solution

---

### Q3. What's the success metric?
- [x] Revenue (per-transaction, subscription)
- [ ] Time Saved (hours/month)
- [ ] User Count (MAU target)
- [ ] Other: _______________

**Target:**
- Year 1: 100 customers, $299K ARR
- Year 2: 350 customers, $1.25M ARR
- Year 3: 800 customers, $3.35M ARR

---

### Q4. What's the timeline constraint?
- [ ] Days (< 1 week)
- [x] Weeks (1-4 weeks) - MVP
- [ ] Months (1-3 months)
- [ ] No constraint

**Notes**: Q1 2026 launch optimal (post-holiday staffing disasters = high demand)

---

### Q5. Is this MCP Aggregator compatible?

Check if ALL are true:
- [x] Value is in data/computation (not UI/UX differentiation) - Voice AI processing
- [x] Transaction-based revenue makes sense - Per-minute or per-call pricing
- [x] Natural AI agent integration - AI handling phone calls
- [ ] Multi-platform distribution helps - Needs direct restaurant relationship

**MCP Compatible:** Hybrid

**Rationale**: Core voice AI engine could be MCP, but restaurants need:
- Direct dashboard for call management
- Integration with their specific POS
- White-label branding
- Customer success relationship

Best approach: Internal MCP-style architecture with customer-facing SaaS wrapper.

---

## Part 2: Technical Requirements (Questions 6-10)

### Q6. What's the primary connectivity pattern?
- [x] HTTP - Real-time APIs (<500ms response) - Voice processing must be real-time
- [ ] EMAIL - Email-based workflows (hours/days)
- [ ] OAUTH - Token-based auth services
- [x] WEBHOOK - Inbound push notifications - Twilio/phone carrier callbacks
- [ ] GRAPHQL - Complex query APIs
- [ ] ASYNC - Long-running batch operations
- [ ] None (standalone app)

---

### Q7. Does it need persistent data storage?
- [ ] No - Stateless operations
- [ ] Yes - Simple key-value / JSON files
- [x] Yes - Relational database (PostgreSQL, SQLite)
- [ ] Yes - Document database (MongoDB)
- [x] Yes - Time-series / analytics data

**Data volume estimate:**
- 100 customers × 30 calls/day × 2 min avg = 6,000 minutes/day
- Call logs, transcripts, analytics = ~50GB/year at scale

---

### Q8. Real-time or batch processing?
- [x] Real-time only (immediate response required) - Voice must be real-time
- [ ] Batch only (can process in background)
- [ ] Both (real-time with async fallback)

---

### Q9. What external integrations are needed?

| Service | Purpose | Has Free Tier? |
|---------|---------|----------------|
| Twilio Voice | Phone calls/SIP | Pay-per-use ($0.013/min) |
| OpenAI/Anthropic | LLM for conversation | Pay-per-use |
| Deepgram/Whisper | Speech-to-text | Deepgram has free tier |
| ElevenLabs/Cartesia | Text-to-speech | Limited free |
| Toast API | POS integration | Partner program |
| Square API | POS integration | Free |
| Stripe | Billing | 2.9% + $0.30 |

---

### Q10. Security/privacy requirements?
- [x] Standard (basic auth, HTTPS)
- [x] High (encryption at rest, audit logs) - Call recordings
- [ ] Regulated (HIPAA, GDPR, PCI compliance)

**Specific requirements:**
- Call recordings encrypted at rest
- Customer data isolation (multi-tenant)
- No PCI scope (Stripe handles payments)
- TCPA compliance for any outbound

---

## Part 3: App Type Decision (Questions 11-13)

### Q11. How will users access this?
- [ ] CLI (command line)
- [x] Web Browser - Dashboard for owners
- [ ] Desktop Application
- [ ] AI Agent (MCP protocol)
- [x] API (programmatic access) - POS integrations
- [x] Multiple access methods

---

### Q12. Does it need a user interface?
- [ ] No UI needed (AI handles presentation)
- [ ] Simple UI (terminal output, basic forms)
- [x] Complex UI (dashboard, visualizations, rich interactions)

**UI needs:**
- Call history & transcripts
- Analytics dashboard
- Menu configuration
- POS integration settings
- Billing management

---

### Q13. What's the deployment target?
- [ ] Local only (runs on user's machine)
- [x] Cloud only (hosted service)
- [ ] Both (local dev, cloud production)
- [ ] Edge (CDN, serverless)

---

## Part 4: Resource Assessment (Questions 14-16)

### Q14. Estimated development hours?

| Component | Hours |
|-----------|-------|
| Voice AI Engine | 80-120 |
| Web Dashboard | 60-80 |
| POS Integrations (Toast, Square) | 40-60 |
| Billing/Stripe | 16-24 |
| Analytics | 24-32 |
| Testing & Polish | 40-60 |
| **TOTAL** | **260-376 hours** |

**Complexity factors:**
- Real-time voice processing (high complexity)
- Multi-tenant architecture (medium)
- POS integrations (medium-high, varies by POS)
- Call quality/latency optimization (high)

---

### Q15. Monthly operational budget?
- [ ] $0 (free tier only)
- [ ] $0-50 (minimal hosting)
- [x] $50-200 (production hosting + services) - Initial
- [ ] $200+ (scale infrastructure) - At scale

**Breakdown (at 100 customers)**:
- Railway hosting: $20-50/mo
- Twilio: Variable (pass-through)
- LLM costs: ~$0.01-0.05 per call (pass-through)
- Database: $20-50/mo
- Monitoring: $20-50/mo
- **Fixed: ~$100-150/mo** (variable costs passed to customers)

---

### Q16. Who maintains this long-term?
- [x] William (manual maintenance) - Initial
- [x] Automated (self-healing, monitoring) - Target state
- [ ] Team (multiple maintainers)
- [ ] Community (open source)

**Maintenance hours/month estimate:** 8-16 hours initially, 4-8 hours when stable

---

## Part 5: Template Decision (Questions 17-19)

### Q17. Does a similar project exist in dev-sandbox?

Check existing projects:
- [x] Yes - Similar structure exists: `fitness-influencer/` (FastAPI + dashboard pattern)
- [ ] Yes - But significantly different approach
- [ ] No - Novel project type

**Relevant components to reuse:**
- FastAPI backend structure from fitness-influencer
- Stripe integration patterns from existing projects
- MCP server patterns from mcp-aggregator

---

### Q18. What's the innovation level?

| Level | Description | Template Recommendation |
|-------|-------------|------------------------|
| Low | Standard implementation, proven pattern | Use full template |
| **Medium** | Some innovation, adapting known patterns | **Adapt template** |
| High | Novel architecture, exploring unknown | Clean slate |

**Innovation level:** Medium

**Rationale:** Voice AI is the innovation; web dashboard/billing are proven patterns.

---

### Q19. Template decision?

Based on Q17 and Q18:

- [ ] **Use template** - Copy structure from: _______________
- [x] **Adapt template** - Use structure from `fitness-influencer/`, customize: Voice AI engine, Twilio integration, POS connectors
- [ ] **Clean slate** - Start fresh because: _______________

---

## Decision Output

### App Type Selection

Based on answers above:

**Primary App Type:**
- [ ] CLI Tool
- [ ] Python Skill (Claude)
- [ ] MCP Server - Connectivity: _______________
- [ ] Web API (Backend Only)
- [x] Full-Stack Web App (SaaS)
- [ ] Desktop App
- [ ] Hybrid (MCP + Web Interface)

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                    AI Customer Service                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│  │   Voice AI   │   │  Dashboard  │   │ POS Integrations│   │
│  │   Engine     │   │  (React)    │   │ (Toast/Square)  │   │
│  └──────┬──────┘   └──────┬──────┘   └────────┬────────┘   │
│         │                 │                    │            │
│         └─────────┬───────┴────────────────────┘            │
│                   │                                         │
│           ┌───────▼───────┐                                 │
│           │   FastAPI     │                                 │
│           │   Backend     │                                 │
│           └───────┬───────┘                                 │
│                   │                                         │
│     ┌─────────────┼─────────────┐                          │
│     │             │             │                          │
│  ┌──▼──┐      ┌───▼───┐    ┌───▼───┐                       │
│  │Twilio│     │  LLM   │   │ DB/   │                       │
│  │Voice │     │(Claude)│   │Cache  │                       │
│  └──────┘     └────────┘   └───────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Cost Summary

| Item | Estimate |
|------|----------|
| Development Hours | 300 hours (midpoint) |
| Development Cost (@ $150/hr equivalent) | $45,000 |
| Monthly Hosting (fixed) | $100-150 |
| Monthly APIs/Services (variable) | Pass-through to customers |
| Monthly Maintenance Hours | 8-12 hours |

### Revenue/Value Summary

| Item | Estimate |
|------|----------|
| Revenue Model | SaaS Subscription + Usage |
| Expected Monthly Revenue (Year 1) | $25K MRR (100 customers) |
| OR Time Saved (hours/month) | N/A (revenue focus) |
| Break-Even Timeline | 12-18 months |

### Unit Economics (from Market Analysis)

| Metric | Value |
|--------|-------|
| CAC | $500-600 |
| LTV | $2,500-4,500 |
| LTV:CAC | 5-7:1 |
| CAC Payback | 2-3 months |
| Gross Margin | 70-78% |

### Go/No-Go Decision

- [x] **GO** - Build this project (break-even < 18 months AND strong strategic value)
- [ ] **CAUTION** - Build MVP first (break-even 6-12 months)
- [ ] **NO-GO** - Do not build (break-even > 12 months AND no strategic value)

**Rationale:**
1. Market analysis scored 4.15/5 (GO threshold: 4.0)
2. Customer pain is 9/10 (existential)
3. Unit economics are excellent (5-7x LTV:CAC)
4. Timing is optimal (2026 = "year of AI-driven restaurant")
5. Clear differentiation path (SMB focus, video avatars)

### Next Steps

1. [x] Complete SOP 0 (This document)
2. [ ] Create directive: `directives/ai-customer-service.md`
3. [ ] Create project structure: `projects/ai-customer-service/src/`
4. [ ] Build MVP Phase 1: Voice AI Engine (4 weeks)
5. [ ] Acquire 10 beta pizzerias (Naples area)

---

## Questionnaire Completed

**Date:** January 17, 2026
**Completed by:** Claude (SOP 0)
**Market Analysis by:** Claude (SOP 17, 4 agents)
**Approved by:** Pending William review

---

## Appendix: Pricing Tiers (Recommended)

| Tier | Price | Included | Target |
|------|-------|----------|--------|
| **Starter** | $149/mo | 500 min | 1 location, low volume |
| **Growth** | $249/mo | 1,500 min | 1-3 locations |
| **Pro** | $399/mo | 4,000 min | 3-10 locations |
| **Enterprise** | Custom | Unlimited | 10+ locations |

Overage: $0.10-0.20/min beyond included

---

## Appendix: Go-to-Market Strategy

1. **Beachhead**: Naples-area pizzerias (local, can support directly)
2. **Timing**: January-February launch (post-holiday staffing disasters)
3. **Message**: "Save $20K/year on phone staff" (ROI-focused)
4. **Channels**: Reddit communities, NRA partnerships, content marketing
5. **Proof**: 3 case studies with documented ROI before scaling

---

## Reference Links

- [Market Analysis](market-analysis/consolidated/GO-NO-GO-DECISION.md)
- [Viability Scorecard](market-analysis/consolidated/VIABILITY-SCORECARD.md)
- [App Type Decision Guide](../../docs/app-type-decision-guide.md)
- [Cost-Benefit Templates](../../docs/cost-benefit-templates.md)
