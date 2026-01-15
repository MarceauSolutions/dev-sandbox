# Method: Project Scoping & Estimation

*Created: 2026-01-15*
*Version: 2026-01-15*

## Problem Statement

We need a consistent, reliable method to:
1. Classify incoming project requests by scope/complexity
2. Provide accurate time and cost estimates to customers
3. Avoid scope creep by setting clear boundaries upfront
4. Price projects appropriately for the Naples market

## Who Uses This Method

- **William**: During discovery calls and proposal creation
- **Claude**: When helping draft proposals or classify project requests

## Success Criteria

- Estimate accuracy within 20% of actual delivery time
- Clear tier classification that customers understand
- Pricing that's competitive but profitable
- Reduced scope creep incidents

## Inputs

- Customer inquiry (email, call notes, form submission)
- Project requirements (pages, features, integrations)
- Timeline expectations
- Budget range (if disclosed)

## Outputs

1. **Project Tier Classification** (Starter/Standard/Professional/Enterprise)
2. **Estimated Hours** (low-mid-high range)
3. **Price Quote** (based on tier + complexity multipliers)
4. **Scope Document** (what's included/excluded)
5. **Timeline Estimate** (delivery date range)

## Draft Classification Framework

| Tier | Type | Typical Scope | Price Range |
|------|------|---------------|-------------|
| **Starter** | Landing page | 1-3 pages, no CMS, basic form | $500-1,500 |
| **Standard** | Small business | 4-7 pages, simple CMS, contact forms | $1,500-3,500 |
| **Professional** | Full website | 8-15 pages, full CMS, integrations | $3,500-7,500 |
| **Enterprise** | Custom platform | 15+ pages, custom features, API | $7,500+ |

## Complexity Multipliers (Draft)

| Factor | Multiplier | Example |
|--------|------------|---------|
| E-commerce | 1.5-2x | Shopping cart, payment processing |
| Membership/Login | 1.3x | User accounts, gated content |
| Third-party API | 1.2x per API | CRM, booking, payments |
| Custom animations | 1.2x | Complex motion design |
| Rush timeline (<2 weeks) | 1.5x | Expedited delivery |
| Content creation | 1.2-1.5x | Copywriting, photography |

## Research Questions (for Multi-Agent Exploration)

### Agent 1: Pricing Research
- What do competitors charge in Naples/SW Florida?
- What's the national average for similar services?
- Value-based vs hourly pricing: pros/cons?
- How to handle recurring revenue (maintenance)?

### Agent 2: Intake Process
- What questions qualify leads effectively?
- How to scope without over-promising?
- Red flags that indicate difficult clients?
- Discovery call best practices?

### Agent 3: Estimation Models
- Fixed price vs Time & Materials?
- How to handle scope creep?
- Contingency buffer percentages?
- Milestone-based payment structures?

### Agent 4: Tooling & Automation
- Can we automate estimates from intake forms?
- CRM integration for tracking?
- Proposal template automation?
- Contract/SOW generators?

## Next Steps

1. Complete multi-agent exploration (SOP 9)
2. Consolidate findings into final classification matrix
3. Create intake questionnaire
4. Build proposal templates
5. Validate on 3-5 past/hypothetical projects
6. Integrate into workflows
