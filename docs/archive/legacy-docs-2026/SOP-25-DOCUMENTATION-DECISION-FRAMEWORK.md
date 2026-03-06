# SOP 25: Documentation Decision Framework

**Created:** 2026-01-20
**Purpose:** Systematically decide when and how to document work to avoid repeating large efforts
**Trigger:** Completing any significant task, setup, or decision

---

## Problem Statement

**What happened:** We created 7 Stripe products with detailed descriptions, pricing, and tier structures - but didn't document the setup process, rationale, or configuration details. When we needed to reference them later, we had to reconstruct everything from screenshots.

**Cost:** ~3 hours spent re-documenting what should have been captured initially.

**Lesson:** Large efforts need documentation AT THE TIME OF COMPLETION, not retroactively.

---

## The Documentation Decision Tree

### Step 1: Is This Worth Documenting?

Ask these questions:

| Question | If YES → Document | If NO → Skip |
|----------|------------------|--------------|
| **Would repeating this take >30 minutes?** | Yes | No |
| **Will I need to reference this later?** | Yes | No |
| **Did I make decisions that need context?** | Yes | No |
| **Would someone else need to replicate this?** | Yes | No |
| **Is this a one-time setup (Stripe, DNS, API keys)?** | Yes | No |

**Scoring:**
- **3+ YES answers:** Document immediately (high priority)
- **1-2 YES answers:** Document if time permits (medium priority)
- **0 YES answers:** Skip documentation (low value)

---

### Step 2: What Type of Documentation?

Based on what you just completed:

| What You Did | Document Type | Location | Example |
|--------------|---------------|----------|---------|
| **One-time setup** (Stripe, DNS, OAuth) | Setup Guide | `docs/` or `projects/[name]/setup/` | STRIPE-PRODUCTS-MASTER-REFERENCE.md |
| **Recurring process** (deploying, testing) | SOP | `docs/` (SOP-XX-NAME.md) | SOP-3-VERSION-CONTROL-DEPLOYMENT.md |
| **Task procedure** (specific to one project) | Workflow | `projects/[name]/workflows/` | `sms-campaign-sop.md` |
| **Strategic decision** (pricing, positioning) | Decision Record | `docs/` | PRODUCT-EVOLUTION-HISTORY.md |
| **Tool/integration config** (API keys, webhooks) | Configuration Guide | `docs/` or `projects/[name]/config/` | NGROK-AI-GATEWAY-SETUP.md |
| **Learning/mistake** | Session History | `docs/session-history.md` | Entry about testing issues |
| **Code architecture** (why we built it this way) | Architecture Doc | `projects/[name]/` or `docs/` | architecture-guide.md |

---

### Step 3: When to Document?

| Timing | When to Use | Example |
|--------|-------------|---------|
| **Immediately (same session)** | One-time setups, critical decisions | Stripe product setup |
| **End of day** | Daily learnings, small procedures | Session history entries |
| **End of task** | Workflows, procedures | After completing SMS campaign |
| **Before deployment** | Architecture, testing guides | Before shipping to production |
| **Never retroactively** | ❌ Don't document after forgetting details | ❌ Reconstructing from memory |

**Golden Rule:** Document WHILE doing the work, not AFTER forgetting the details.

---

## SOP: The Documentation Process

### Phase 1: During Work (Capture Context)

As you work, capture these in notes (scratch file, comments, etc.):

1. **What you're doing** (task description)
2. **Why you're doing it** (rationale, decision context)
3. **Key decisions made** (what alternatives were considered)
4. **Configuration values** (API keys stored where, product IDs, etc.)
5. **Gotchas/mistakes** (what went wrong, how you fixed it)

**Tool:** Use a scratch file (e.g., `.tmp/scratch.md`) to capture notes during work.

---

### Phase 2: Immediately After Completion (10-30 min)

**Task:** Convert scratch notes into proper documentation.

**Template for Setup Guides:**
```markdown
# [Tool/Service] Setup Guide

**Created:** YYYY-MM-DD
**Last Updated:** YYYY-MM-DD
**Status:** Active | Deprecated

## Overview
[What this setup achieves]

## Prerequisites
- [ ] Requirement 1
- [ ] Requirement 2

## Setup Steps

### Step 1: [Action]
**What:** [What you're doing]
**Why:** [Why this step matters]
**How:**
\`\`\`bash
[Commands or actions]
\`\`\`
**Verification:** ✅ You should see [expected output]

[Repeat for each step]

## Configuration Details

| Item | Value | Location | Notes |
|------|-------|----------|-------|
| Product ID | prod_XXX | Stripe Dashboard | Created Jan 17 |
| API Key | STRIPE_SECRET_KEY | .env | Needs refresh annually |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| [Common error] | [Why it happens] | [How to fix] |

## References
- Link to official docs
- Related internal docs

## Change Log
- YYYY-MM-DD: Initial setup
- YYYY-MM-DD: Updated configuration
```

---

### Phase 3: Link Documentation (5 min)

**Task:** Make documentation discoverable.

1. **Update CLAUDE.md:**
   - Add to "Documentation Map" table
   - Add to "Where to Put Things" section if new location

2. **Update README** (if project-specific):
   - Link to setup guide
   - Add to "Getting Started" section

3. **Cross-reference:**
   - If related to SOP, link from SOP
   - If related to workflow, link from workflow

---

## Scenarios That ALWAYS Require Documentation

### 1. One-Time Setups (External Services)

**Examples:**
- Stripe product configuration
- DNS/domain setup
- OAuth application registration
- Webhook endpoints
- API key generation
- Payment processor setup
- Email service configuration

**Why:** You'll never remember the details 6 months later, and redoing setup is costly.

**Document:**
- All configuration values (store securely if sensitive)
- Setup steps (so you can replicate for new projects)
- Rationale for choices (why this tier structure, why these prices)

**Template:** Setup Guide (see Phase 2 above)

---

### 2. Strategic Decisions (Business/Product)

**Examples:**
- Pricing decisions (why $7,497 not $5,000?)
- Product positioning (why multi-industry not HVAC-only?)
- Target market selection (why restaurants first?)
- Business model choice (why done-for-you not SaaS?)

**Why:** Prevents daily strategy changes, provides context for future decisions.

**Document:**
- Decision made
- Alternatives considered
- Rationale (data, assumptions, constraints)
- Outcome metrics (how will we know if it worked?)

**Template:** Decision Record

```markdown
# Decision: [Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated

## Context
[What led to this decision]

## Decision
[What we decided]

## Alternatives Considered
1. **Option A:** [Description] - Why not: [Reason]
2. **Option B:** [Description] - Why not: [Reason]

## Rationale
[Why we chose this option]

## Consequences
- Positive: [Expected benefits]
- Negative: [Trade-offs, risks]

## Success Metrics
How we'll measure if this was the right decision:
- Metric 1: [Target]
- Metric 2: [Target]

## Review Date
[When we'll revisit this decision]
```

---

### 3. Integration/Tool Setup (Technical)

**Examples:**
- Twilio Voice API setup
- ClickUp CRM integration
- Google OAuth configuration
- MCP server deployment
- GitHub Actions workflows

**Why:** Complex integrations have many steps, easy to miss one when repeating.

**Document:**
- Step-by-step setup
- Configuration values
- Testing/verification steps
- Common issues and fixes

**Template:** Integration Guide

---

### 4. Workflows/Procedures (Repeatable Tasks)

**Examples:**
- SMS campaign execution
- Multi-agent testing
- Deployment process
- Client onboarding
- Monthly reporting

**Why:** You'll do this 10+ times, consistency matters.

**Document:**
- Checklist (step-by-step)
- Prerequisites
- Success criteria
- Troubleshooting

**Template:** Workflow (see SOP 6)

---

### 5. Architecture Decisions (Code Structure)

**Examples:**
- Why we use multi-business config system
- Why execution/ vs projects/src/ split
- Why DOE architecture (Directive-Orchestration-Execution)
- Why separate prod repos

**Why:** Future developers (or future you) need to understand the system design.

**Document:**
- Problem being solved
- Design choices made
- Alternatives considered
- Trade-offs

**Template:** Architecture Decision Record (ADR)

---

## Scenarios That DON'T Require Documentation

### 1. Trivial Tasks (<30 min, no decisions)

**Examples:**
- Reading a file
- Running a single command
- Checking status

**Why not:** More overhead to document than to repeat.

---

### 2. Exploratory Work (Not Finalized)

**Examples:**
- Trying different approaches
- Prototyping
- Researching options

**Why not:** Wait until decision is made, THEN document the final choice.

---

### 3. Self-Documenting Code

**Examples:**
- Well-named functions
- Clear variable names
- Simple scripts with comments

**Why not:** The code itself is the documentation.

---

## Documentation Quality Standards

### Minimum Viable Documentation:

**Good documentation includes:**
1. ✅ **Title** (what is this)
2. ✅ **Date** (when was this created/updated)
3. ✅ **Purpose** (why does this exist)
4. ✅ **Steps** (how to do it)
5. ✅ **Verification** (how to know it worked)

**Bad documentation:**
- ❌ Vague ("configure Stripe") - needs specific steps
- ❌ Missing context ("set X to Y") - why? what does it do?
- ❌ No verification ("run command") - what should I see?
- ❌ Outdated (references old URLs, deprecated features)

---

## Documentation Maintenance

### When to Update Documentation:

| Trigger | Update What | Example |
|---------|-------------|---------|
| **Process changed** | Update workflow/SOP | Deployment process now includes new step |
| **Tool upgraded** | Update setup guide | Stripe API version changed |
| **Decision reversed** | Update decision record | Changed from HVAC-only to multi-industry |
| **Found error** | Fix documentation | Discovered missing step in setup |
| **Quarterly review** | Archive outdated docs | Old pricing models no longer used |

### Archiving Old Documentation:

**When to archive:**
- Strategy changed (old pricing, old positioning)
- Tool deprecated (old integration, sunset service)
- Approach abandoned (tried and rejected)

**How to archive:**
```bash
# Move to archive folder
mv docs/OLD-STRATEGY.md docs/archive/OLD-STRATEGY-deprecated-2026-01-20.md

# Add deprecation notice at top
# Archive Notice: This document is deprecated as of 2026-01-20.
# Reason: [Why deprecated]
# Replaced by: [New document]
```

---

## Integration with CLAUDE.md

### Add to Communication Patterns:

| User Says | Claude Does |
|-----------|-------------|
| "Document this setup" | Create setup guide using SOP 25 template |
| "Save this decision" | Create decision record with rationale |
| "This should be in the SOPs" | Evaluate using documentation decision tree |
| "Don't forget this" | Determine doc type, create immediately |

### Add to Operating Principles:

**11. Document Large Efforts Immediately**
- One-time setups (Stripe, OAuth, DNS) → Setup Guide
- Strategic decisions (pricing, positioning) → Decision Record
- Repeatable processes → SOP or Workflow
- Architecture choices → Architecture Decision Record
- Use SOP 25 decision tree to determine if/how to document
- Document DURING work, not AFTER forgetting details

---

## Self-Annealing: Documentation About Documentation

**Meta-lesson:** This SOP (SOP 25) exists BECAUSE we failed to document Stripe setup initially.

**Triggers for updating SOP 25:**
- Discover new scenario that should be documented
- Find documentation type we didn't account for
- Learn better template or process
- Identify common documentation mistakes

**Keep SOP 25 up-to-date as we learn what works.**

---

## Quick Reference: Documentation Checklist

**After completing ANY significant task, ask:**

1. ✅ **Did this take >30 minutes?** → If yes, document
2. ✅ **What type:** Setup | Decision | Workflow | Architecture | Integration?
3. ✅ **Where:** `docs/` | `projects/[name]/` | `workflows/` ?
4. ✅ **Template:** Use appropriate template from this SOP
5. ✅ **Link:** Add to CLAUDE.md, README, or related docs
6. ✅ **Verify:** Can someone else (or future you) replicate this?

**Time investment:** 10-30 min to document saves 1-3 hours later.

---

## Examples of Good Documentation (Reference)

### Example 1: Stripe Products Setup

**Good:**
- ✅ All 7 products listed with IDs, prices, descriptions
- ✅ Created date, rationale for pricing
- ✅ Target market for each tier
- ✅ Revenue modeling
- ✅ Strategic decisions locked in

**File:** `docs/STRIPE-PRODUCTS-MASTER-REFERENCE.md`

---

### Example 2: Business Config Architecture

**Good:**
- ✅ Why multi-business system exists
- ✅ Design choices (one config file vs separate)
- ✅ How to add new business
- ✅ Examples of each field

**File:** `execution/form_handler/business_config.py` (inline comments + architecture doc)

---

### Example 3: Product Evolution

**Good:**
- ✅ Timeline of decisions
- ✅ Why we pivoted (Fitness → Websites → Multi-Industry)
- ✅ Context for current strategy
- ✅ Prevents daily strategy changes

**File:** `docs/PRODUCT-EVOLUTION-HISTORY.md`

---

## Success Metrics for SOP 25

**How to know if this SOP is working:**

1. **Reduced rework:** We DON'T spend hours reconstructing past work
2. **Faster onboarding:** New developers/collaborators can get up to speed quickly
3. **Consistent decisions:** We reference past decision records instead of re-debating
4. **Living docs:** Documentation stays up-to-date (updated within 1 week of changes)

**Review this SOP quarterly** - Update based on what documentation patterns emerged.

---

## Next Steps: Apply SOP 25 Immediately

**Task:** Audit recent work for missing documentation.

**Check:**
1. ✅ Stripe products → NOW DOCUMENTED (STRIPE-PRODUCTS-MASTER-REFERENCE.md)
2. 🔲 HVAC + Shipping setup → NOT DOCUMENTED YET
   - What integrations were configured?
   - What ClickUp lists/fields exist?
   - What Voice AI prompts are configured?
3. 🔲 Multi-business form routing → PARTIALLY DOCUMENTED
   - `business_config.py` has inline comments
   - Missing: How to add new business (step-by-step)
4. 🔲 Lead scraping setup → NOT DOCUMENTED
   - How to scrape new industries?
   - What fields are captured?
   - How to export to ClickUp?

**Action:** Create missing documentation using SOP 25 templates.

---

**Status:** SOP 25 complete - Add to CLAUDE.md next.
