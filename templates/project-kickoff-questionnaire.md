# Project Kickoff Questionnaire

Complete this questionnaire BEFORE starting any new project. This ensures proper app type selection, cost analysis, and template decisions are made upfront.

## Instructions

1. Copy this template to your project folder as `KICKOFF.md`
2. Answer all 19 questions
3. Review the Decision Output section
4. Proceed to SOP 1 (New Project Initialization) with clarity

---

## Part 1: Business & Purpose (Questions 1-5)

### Q1. What problem does this solve?
> _One sentence describing the core problem_

**Answer:**

---

### Q2. Who are the primary users?
- [ ] AI Agents (via MCP Aggregator)
- [ ] Developers (CLI/API)
- [ ] End Users (Web/Mobile/Desktop interface)
- [ ] Internal (Personal automation)
- [ ] Other: _______________

---

### Q3. What's the success metric?
- [ ] Revenue (per-transaction, subscription)
- [ ] Time Saved (hours/month)
- [ ] User Count (MAU target)
- [ ] Other: _______________

**Target:**

---

### Q4. What's the timeline constraint?
- [ ] Days (< 1 week)
- [ ] Weeks (1-4 weeks)
- [ ] Months (1-3 months)
- [ ] No constraint

---

### Q5. Is this MCP Aggregator compatible?

Check if ALL are true:
- [ ] Value is in data/computation (not UI/UX differentiation)
- [ ] Transaction-based revenue makes sense
- [ ] Natural AI agent integration
- [ ] Multi-platform distribution helps

**MCP Compatible:** Yes / No / Hybrid

---

## Part 2: Technical Requirements (Questions 6-10)

### Q6. What's the primary connectivity pattern?
- [ ] HTTP - Real-time APIs (<500ms response)
- [ ] EMAIL - Email-based workflows (hours/days)
- [ ] OAUTH - Token-based auth services
- [ ] WEBHOOK - Inbound push notifications
- [ ] GRAPHQL - Complex query APIs
- [ ] ASYNC - Long-running batch operations
- [ ] None (standalone app)

---

### Q7. Does it need persistent data storage?
- [ ] No - Stateless operations
- [ ] Yes - Simple key-value / JSON files
- [ ] Yes - Relational database (PostgreSQL, SQLite)
- [ ] Yes - Document database (MongoDB)
- [ ] Yes - Time-series / analytics data

**Data volume estimate:**

---

### Q8. Real-time or batch processing?
- [ ] Real-time only (immediate response required)
- [ ] Batch only (can process in background)
- [ ] Both (real-time with async fallback)

---

### Q9. What external integrations are needed?
> _List all external services, APIs, or platforms_

| Service | Purpose | Has Free Tier? |
|---------|---------|----------------|
| | | |
| | | |
| | | |

---

### Q10. Security/privacy requirements?
- [ ] Standard (basic auth, HTTPS)
- [ ] High (encryption at rest, audit logs)
- [ ] Regulated (HIPAA, GDPR, PCI compliance)

**Specific requirements:**

---

## Part 3: App Type Decision (Questions 11-13)

### Q11. How will users access this?
- [ ] CLI (command line)
- [ ] Web Browser
- [ ] Desktop Application
- [ ] AI Agent (MCP protocol)
- [ ] API (programmatic access)
- [ ] Multiple access methods

---

### Q12. Does it need a user interface?
- [ ] No UI needed (AI handles presentation)
- [ ] Simple UI (terminal output, basic forms)
- [ ] Complex UI (dashboard, visualizations, rich interactions)

---

### Q13. What's the deployment target?
- [ ] Local only (runs on user's machine)
- [ ] Cloud only (hosted service)
- [ ] Both (local dev, cloud production)
- [ ] Edge (CDN, serverless)

---

## Part 4: Resource Assessment (Questions 14-16)

### Q14. Estimated development hours?

Use the [Cost-Benefit Templates](../docs/cost-benefit-templates.md) matrix:

| App Type | Hours |
|----------|-------|
| CLI Tool | 8-24 |
| Python Skill | 16-40 |
| MCP Server | 24-100 |
| Web API | 40-80 |
| Full-Stack Web | 120-240 |
| Desktop | 160-320 |
| Hybrid | 80-160 |

**Estimated hours:**
**Complexity factors:**

---

### Q15. Monthly operational budget?
- [ ] $0 (free tier only)
- [ ] $0-50 (minimal hosting)
- [ ] $50-200 (production hosting + services)
- [ ] $200+ (scale infrastructure)

---

### Q16. Who maintains this long-term?
- [ ] William (manual maintenance)
- [ ] Automated (self-healing, monitoring)
- [ ] Team (multiple maintainers)
- [ ] Community (open source)

**Maintenance hours/month estimate:**

---

## Part 5: Template Decision (Questions 17-19)

### Q17. Does a similar project exist in dev-sandbox?

Check existing projects:
- [ ] Yes - Similar structure exists (specify): _______________
- [ ] Yes - But significantly different approach
- [ ] No - Novel project type

---

### Q18. What's the innovation level?

| Level | Description | Template Recommendation |
|-------|-------------|------------------------|
| Low | Standard implementation, proven pattern | Use full template |
| Medium | Some innovation, adapting known patterns | Adapt template |
| High | Novel architecture, exploring unknown | Clean slate |

**Innovation level:** Low / Medium / High

---

### Q19. Template decision?

Based on Q17 and Q18:

- [ ] **Use template** - Copy structure from: _______________
- [ ] **Adapt template** - Use structure from _______________, customize: _______________
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
- [ ] Full-Stack Web App
- [ ] Desktop App
- [ ] Hybrid (MCP + Web Interface)

### Cost Summary

| Item | Estimate |
|------|----------|
| Development Hours | |
| Development Cost (@ $___/hr) | |
| Monthly Hosting | |
| Monthly APIs/Services | |
| Monthly Maintenance Hours | |

### Revenue/Value Summary

| Item | Estimate |
|------|----------|
| Revenue Model | |
| Expected Monthly Revenue | |
| OR Time Saved (hours/month) | |
| Break-Even Timeline | |

### Go/No-Go Decision

- [ ] **GO** - Build this project (break-even < 6 months OR clear strategic value)
- [ ] **CAUTION** - Build MVP first (break-even 6-12 months)
- [ ] **NO-GO** - Do not build (break-even > 12 months AND no strategic value)

### Next Steps

1. [ ] Proceed to SOP 1 (New Project Initialization)
2. [ ] Use SOP 9 (Architecture Exploration) first - if multiple approaches possible
3. [ ] Create directive: `directives/[project-name].md`
4. [ ] Create project folder: `projects/[project-name]/`

---

## Questionnaire Completed

**Date:**
**Completed by:**
**Approved by:**

---

## Reference Links

- [App Type Decision Guide](../docs/app-type-decision-guide.md)
- [Cost-Benefit Templates](../docs/cost-benefit-templates.md)
- [Development to Deployment Pipeline](../docs/development-to-deployment.md)
- [SOP 1: New Project Initialization](../CLAUDE.md#sop-1-new-project-initialization)
- [SOP 9: Architecture Exploration](../CLAUDE.md#sop-9-multi-agent-architecture-exploration)
