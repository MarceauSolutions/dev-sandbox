# App Type Decision Guide

A systematic framework for deciding what type of application to build (MCP, Web App, Desktop, CLI, Hybrid, Mobile App, PWA) before implementation begins.

## When to Use This Guide

Use this guide at the START of any new project, BEFORE:
- SOP 1 (New Project Initialization)
- SOP 9 (Architecture Exploration)
- Any code writing

## Quick Decision Path

```
START: New Project Idea
    │
    ▼
[Step 1] MCP Aggregator Alignment Check
    │
    ├─ YES → [Step 2a] Select MCP Connectivity Type
    │
    └─ NO → [Step 2b] Select Standalone App Type
    │
    ▼
[Step 3] Template vs Clean Slate Decision
    │
    ▼
[Step 4] Complete Cost-Benefit Analysis
    │
    ▼
[Step 5] Document Decision → Proceed to SOP 1 or SOP 9
```

---

## Step 1: MCP Aggregator Alignment Check

The MCP Aggregator is our platform for AI agent services. First, determine if your project fits this ecosystem.

### Build as MCP if ALL of these are true:

| Criterion | Check |
|-----------|-------|
| **Value is in data/computation** | Your service provides data, analysis, or computation - not a unique UI/UX |
| **Transaction-based revenue works** | Per-request pricing ($0.01-$0.50/request) makes sense for this service |
| **Natural AI agent integration** | Users would naturally ask an AI to do this task |
| **Multi-platform distribution helps** | Being available via Claude, ChatGPT, etc. adds value |

**Examples of good MCP candidates:**
- Price comparisons (rideshare, flights, hotels)
- Data lookups (weather, stock prices, shipping rates)
- Quote systems (HVAC, insurance, contractors)
- Analysis services (email analysis, document review)

### Build as Standalone App if ANY of these are true:

| Criterion | Check |
|-----------|-------|
| **Value is in user experience** | The UI/UX itself is the product differentiator |
| **Brand relationship matters** | You need direct customer relationship, not AI-mediated |
| **Subscription model is better** | Monthly recurring revenue makes more sense than per-transaction |
| **Deep per-user customization** | Each user needs significantly different configuration |

**Examples of standalone apps:**
- Consumer mobile apps with unique interfaces
- Enterprise dashboards with complex visualizations
- Tools requiring deep personalization
- Products where brand loyalty is the moat

---

## Step 2a: MCP Connectivity Type Selection

If you're building an MCP, select the connectivity type that best fits your service:

### HTTP (Real-time APIs)

**Use when:**
- Response time should be <500ms
- Service calls external HTTP APIs
- Real-time data is essential

**Examples:** Rideshare comparison, flight search, stock quotes

**Scoring profile:** Performance-weighted (fast responses = better scores)

---

### EMAIL (Async Email-Based)

**Use when:**
- Workflow naturally involves email
- Response times of hours/days are acceptable
- You're integrating with email-based services

**Examples:** HVAC quote requests, appointment scheduling, vendor RFQs

**Scoring profile:** Health-weighted (reliability > speed)

---

### OAUTH (Token-Based Auth)

**Use when:**
- Accessing user's accounts on other platforms
- Requires user authorization flow
- Token refresh management needed

**Examples:** Bank integrations, social media APIs, calendar access

**Scoring profile:** Balanced (health + performance)

---

### WEBHOOK (Inbound Push)

**Use when:**
- External service pushes data TO you
- Event-driven architecture
- You react to external triggers

**Examples:** CRM update notifications, payment confirmations, IoT sensors

**Scoring profile:** Health-weighted (must be reliable to receive)

---

### GRAPHQL (Complex Queries)

**Use when:**
- Complex data relationships
- Client needs flexible querying
- Reducing over-fetching matters

**Examples:** Data aggregation services, complex search APIs

**Scoring profile:** Balanced

---

### ASYNC (Long-Running Operations)

**Use when:**
- Operations take minutes to hours
- Batch processing
- Report generation

**Examples:** Large document analysis, batch data processing, ML inference

**Scoring profile:** Health-weighted (completion reliability matters most)

---

## Step 2b: Standalone App Type Selection

If you're NOT building an MCP, choose the appropriate standalone type:

### CLI Tool

| Aspect | Details |
|--------|---------|
| **Best for** | Developer tools, automation scripts, command-line utilities |
| **Development cost** | Low (8-24 hours) |
| **Complexity** | Low |
| **Maintenance** | 1-2 hrs/month |
| **Distribution** | PyPI, direct download, npm |

**When to choose:**
- Target users are developers
- No UI needed
- Scripting/automation use case
- Want fast development cycle

**Reference implementation:** `hvac_cli.py`

---

### Python Skill (Claude)

| Aspect | Details |
|--------|---------|
| **Best for** | AI-assisted workflows within Claude |
| **Development cost** | Low-Medium (16-40 hours) |
| **Complexity** | Low-Medium |
| **Maintenance** | 2-4 hrs/month |
| **Distribution** | `.claude/skills/` |

**When to choose:**
- Primary interaction is through Claude
- AI orchestration adds value
- Don't need separate web/mobile interface
- Internal tools or personal automation

**Reference implementation:** `email-analyzer/`

---

### Web API (Backend Only)

| Aspect | Details |
|--------|---------|
| **Best for** | Headless services, integrations, backend systems |
| **Development cost** | Medium (40-80 hours) |
| **Complexity** | Medium |
| **Hosting** | $5-50/month |
| **Maintenance** | 4-8 hrs/month |
| **Distribution** | Railway, Heroku, AWS |

**When to choose:**
- Other systems call your service
- REST/GraphQL API is the interface
- No end-user UI needed
- Microservices architecture

**Reference implementation:** `fitness-influencer/` (API portion)

---

### Full-Stack Web App

| Aspect | Details |
|--------|---------|
| **Best for** | User-facing products with web interface |
| **Development cost** | High (120-240 hours) |
| **Complexity** | High |
| **Hosting** | $20-200/month |
| **Maintenance** | 8-16 hrs/month |
| **Distribution** | Railway + custom domain |

**When to choose:**
- End users interact via web browser
- Need rich UI/UX
- User accounts and state management
- SaaS or consumer web product

**Reference implementation:** `website-builder/` (when complete)

---

### Desktop App

| Aspect | Details |
|--------|---------|
| **Best for** | Heavy local processing, offline capability |
| **Development cost** | High (160-320 hours) |
| **Complexity** | High |
| **Hosting** | $0 (local) |
| **Maintenance** | 4-8 hrs/month |
| **Distribution** | Installer packages (DMG, EXE) |

**When to choose:**
- Needs to work offline
- Heavy local computation (video editing, etc.)
- Desktop-specific features needed
- User data stays local

---

### Hybrid (MCP + Web Interface)

| Aspect | Details |
|--------|---------|
| **Best for** | MCP with admin dashboard or user portal |
| **Development cost** | Medium-High (80-160 hours) |
| **Complexity** | Medium-High |
| **Hosting** | $10-100/month |
| **Maintenance** | 8-12 hrs/month |
| **Distribution** | MCP registration + Railway |

**When to choose:**
- Core service is MCP (transaction-based)
- Need admin/monitoring dashboard
- Users need some direct interface
- Want both distribution channels

---

### Mobile App (iOS/Android)

| Aspect | Details |
|--------|---------|
| **Best for** | Consumer apps, location-based services, frequent daily use |
| **Development cost** | High (160-320 hours for MVP) |
| **Complexity** | High |
| **Hosting** | $20-100/month + $99/year Apple + $25 Google |
| **Maintenance** | 8-16 hrs/month |
| **Distribution** | App Store, Google Play |

**When to choose:**
- Primary users are on-the-go (mobile-first)
- Needs device features (GPS, camera, push notifications)
- Daily/frequent use with short sessions
- Consumer market (B2C)
- Offline capability needed

**Framework recommendation:** React Native + Expo (fastest for solo dev)

**Mobile App Viability Scorecard** (score each 1-5):

| Factor | Question |
|--------|----------|
| Location Dependency | Is user typically mobile when using this? |
| Frequency | Daily/multiple times per day use? |
| Session Length | Quick tasks (<5 min sessions)? |
| Offline Need | Must work without internet? |
| Push Notifications | Core to the experience? |
| Device Features | Need camera/GPS/sensors? |
| Competition | Is market mobile-first? |
| Revenue Model | Consumer subscription viable? |

**Scoring thresholds:**
- 32-40: Strong mobile candidate → BUILD MOBILE APP
- 24-31: Consider mobile → Evaluate carefully
- 16-23: PWA might suffice → Build web app, make responsive
- 8-15: Not mobile fit → Choose different app type

**Reference:** See [mobile-app-development-guide.md](mobile-app-development-guide.md) for full SOP

---

### Progressive Web App (PWA)

| Aspect | Details |
|--------|---------|
| **Best for** | Mobile-accessible web apps without app store |
| **Development cost** | Medium (60-120 hours) |
| **Complexity** | Medium |
| **Hosting** | $10-50/month |
| **Maintenance** | 4-8 hrs/month |
| **Distribution** | Direct URL, no app store needed |

**When to choose:**
- Mobile Viability Score 16-23 (borderline)
- Don't need native device features
- Want to avoid app store approval process
- Rapid iteration is priority
- Cross-platform with single codebase

**PWA vs Native App:**

| Factor | PWA | Native App |
|--------|-----|------------|
| Push notifications | Limited (iOS restrictions) | Full support |
| Offline | Service workers | Full native |
| Camera/GPS | Web APIs (limited) | Full access |
| App store presence | No | Yes |
| Install friction | Low (add to home) | Higher (store download) |
| Update speed | Instant | Store review (1-7 days) |

---

## Step 3: Template vs Clean Slate Decision

### Use a Template When:

| Scenario | Why | Example |
|----------|-----|---------|
| Proven pattern exists | Skip boilerplate | New EMAIL MCP → copy HVAC structure |
| Regulatory/compliance | Ensure nothing missed | Auth flows |
| Team consistency | Same structure everywhere | All MCPs follow same registration |
| Time-critical | Speed matters most | Client demo MVP |
| Low innovation | Standard solution is fine | Basic CRUD API |

### Start Clean When:

| Scenario | Why | Example |
|----------|-----|---------|
| Novel architecture | Template assumptions wrong | New connectivity type |
| Experimental/R&D | Exploring unknown | Architecture exploration |
| Template debt | Old patterns are bad | Legacy code issues |
| Unique constraints | Nothing similar exists | Hybrid not built before |
| Learning opportunity | Need to understand | First project of type |

### Innovation Level Assessment

```
LOW INNOVATION          MEDIUM INNOVATION       HIGH INNOVATION
─────────────────────────────────────────────────────────────────
Use full template       Adapt template          Start clean
Fast delivery           Balanced                Slower but flexible
Risk: Cargo cult        Risk: Moderate          Risk: Reinvent wheel
```

---

## Step 4: Cost-Benefit Analysis

Before finalizing, complete the cost-benefit analysis using the templates in [cost-benefit-templates.md](cost-benefit-templates.md).

Key questions:
- Development hours × hourly rate = Total dev cost
- Monthly hosting + API costs = Ongoing cost
- Expected revenue or time savings = Value
- Break-even timeline?

---

## Step 5: Document the Decision

Create a decision record with:

```markdown
## Project: [Name]
## Date: [YYYY-MM-DD]

### Decision Summary
- **App Type**: [MCP / CLI / Web API / Full-Stack / Desktop / Hybrid]
- **Connectivity** (if MCP): [HTTP / EMAIL / OAUTH / WEBHOOK / GRAPHQL / ASYNC]
- **Template**: [Use X template / Adapt X template / Clean slate]

### Rationale
[Why this app type was chosen over alternatives]

### Questionnaire Answers
[Complete 19-question questionnaire - see project-kickoff-questionnaire.md]

### Cost-Benefit Summary
- Dev hours: X
- Monthly cost: $Y
- Expected value: $Z or N hours saved

### Next Step
[SOP 1 / SOP 9 / Other]
```

---

## Reference: Existing Projects by Type

| Project | App Type | Connectivity | Notes |
|---------|----------|--------------|-------|
| rideshare | MCP Server | HTTP | Flagship MCP |
| hvac-distributors | MCP Server | EMAIL | Async workflow |
| email-analyzer | Python Skill | - | Claude skill |
| fitness-influencer | Web API | - | FastAPI + frontend |
| interview-prep | Python Skill | - | PowerPoint generation |
| md-to-pdf | CLI Tool | - | Conversion utility |
| naples-weather | Python Skill | - | Report generation |
| mcp-aggregator | Platform | Multiple | Infrastructure |
| restaurant-finder | Mobile App (candidate) | - | Location-based, high mobile score |

---

## Related Documentation

- [Cost-Benefit Templates](cost-benefit-templates.md)
- [Project Kickoff Questionnaire](../templates/project-kickoff-questionnaire.md)
- [Development to Deployment Pipeline](development-to-deployment.md)
- [Architecture Guide](architecture-guide.md)
- [Mobile App Development Guide](mobile-app-development-guide.md) ⭐ NEW
