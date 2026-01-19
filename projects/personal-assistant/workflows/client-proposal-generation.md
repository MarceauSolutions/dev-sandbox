# Workflow: Client Proposal Generation

**Created:** 2026-01-19
**Purpose:** Generate professional client proposals for Marceau Solutions automation projects
**Output:** PDF proposal document with pricing, scope, timeline, and terms

---

## Overview

This workflow creates customized client proposals based on discovery call information. Similar to the Naples Weather Report generation workflow - uses template + data → generates formatted PDF output.

---

## Use Cases

- Prospect completed discovery call, ready for formal proposal
- Need to send pricing for Digital Storefront, Growth System, or Enterprise Package
- Client requested quote for website + automation bundle
- Follow-up proposal after demo/consultation

---

## Prerequisites

Before generating proposal:
- ✅ Discovery call completed (pain points identified)
- ✅ Tier selected (Digital Storefront / Growth System / Enterprise)
- ✅ Client information collected (business name, contact, services offered)
- ✅ Automation workflow identified (which automations they need)

---

## Input Data Required

```json
{
  "client": {
    "business_name": "Tony's Pizza Naples",
    "owner_name": "Tony Marconi",
    "email": "tony@tonyspizza.com",
    "phone": "+1 239-555-1234",
    "industry": "Restaurant",
    "employees": 8,
    "current_website": "No",
    "current_automation": "No"
  },
  "pain_points": [
    "Missing 20-30% of calls during dinner rush",
    "No online ordering (losing customers to competitors)",
    "Staff overwhelmed taking phone orders",
    "No way to track customer orders"
  ],
  "tier_selected": "growth_system",
  "automations_needed": [
    "Voice AI call answering",
    "Online ordering form",
    "Order confirmation SMS",
    "CRM order tracking"
  ],
  "pricing": {
    "setup_fee": 9997,
    "optional_retainer": 747
  },
  "timeline_weeks": 6
}
```

---

## Steps

### Step 1: Prepare Client Discovery Summary

**Objective:** Consolidate discovery call notes into structured data

**Actions:**
1. Review discovery call notes
2. Identify primary pain points (3-5 max)
3. Determine which tier fits their needs
4. List specific automations they need
5. Calculate timeline based on tier

**Tools:**
- Discovery call template (Google Doc)
- Client intake form responses

**Output:**
- Structured JSON with client data (see above)

---

### Step 2: Select Proposal Template

**Objective:** Choose correct template based on tier

**Templates:**
- `templates/proposals/digital-storefront-proposal.md`
- `templates/proposals/growth-system-proposal.md`
- `templates/proposals/enterprise-package-proposal.md`

**Actions:**
1. Match tier to template
2. Open template in editor
3. Verify all sections present:
   - Executive Summary
   - Pain Points Identified
   - Proposed Solution
   - What's Included
   - What's NOT Included
   - Timeline & Milestones
   - Pricing & Payment Terms
   - Next Steps

---

### Step 3: Generate Proposal Content

**Objective:** Populate template with client-specific data

**Actions:**
1. Replace placeholders:
   - `{CLIENT_BUSINESS_NAME}` → "Tony's Pizza Naples"
   - `{OWNER_NAME}` → "Tony Marconi"
   - `{PAIN_POINT_1}` → "Missing 20-30% of calls..."
   - `{SETUP_FEE}` → "$9,997"
   - `{TIMELINE}` → "6 weeks"

2. Customize "Proposed Solution" section:
   - Reference specific automations they need
   - Explain how each automation solves their pain points
   - Use industry-specific examples

3. Verify "What's Included" matches tier exactly:
   - Copy from `STRIPE-PRODUCTS-V2-BUNDLED-OFFERINGS.md`
   - Don't deviate from documented scope

4. Add "What's NOT Included" (prevent scope creep):
   - Copy exclusions from tier documentation
   - Add any client-specific exclusions discussed

**Tools:**
- Text editor or Google Docs
- Reference: `docs/STRIPE-PRODUCTS-V2-BUNDLED-OFFERINGS.md`

---

### Step 4: Add Visual Elements (Optional)

**Objective:** Make proposal visually professional

**Actions:**
1. Add Marceau Solutions logo/header
2. Include mockup screenshots (website design concepts)
3. Add workflow diagrams (how automation will work)
4. Include testimonials (from similar businesses if available)

**Tools:**
- Canva (for mockups/visuals)
- Lucidchart (for workflow diagrams)
- Previous client testimonials

---

### Step 5: Convert to PDF

**Objective:** Generate professional PDF output

**Actions:**
1. Save completed proposal as Markdown
2. Use markdown-to-PDF converter:
   ```bash
   cd projects/md-to-pdf
   python -m src.md_to_pdf_mcp convert \
       --input proposals/tony-pizza-proposal.md \
       --output proposals/tony-pizza-proposal.pdf \
       --theme professional
   ```

3. Review PDF output:
   - Check formatting (headers, lists, spacing)
   - Verify all placeholder text replaced
   - Check page breaks (no awkward splits)
   - Verify pricing accuracy

**Tools:**
- `md-to-pdf` MCP (already deployed)
- PDF viewer (Preview on Mac, Adobe Reader)

---

### Step 6: Add Contract/Terms Page

**Objective:** Include legal terms and signature page

**Actions:**
1. Append standard terms to proposal:
   - Payment terms (50% deposit, 50% at launch)
   - Timeline contingencies (client delays)
   - Warranty terms (30/60/90 days based on tier)
   - Scope change process
   - Cancellation policy

2. Add signature block:
   ```
   Client Signature: ______________________  Date: __________

   Marceau Solutions Representative: ______________________  Date: __________
   ```

**Tools:**
- Standard terms template: `templates/proposals/standard-terms.md`
- DocuSign (for electronic signatures) OR print/scan for physical signatures

---

### Step 7: Review Checklist

**Objective:** Ensure proposal is complete and accurate before sending

**Checklist:**
- [ ] Client name/business name spelled correctly throughout
- [ ] All placeholders replaced (no `{BUSINESS_NAME}` left)
- [ ] Pricing matches selected tier exactly
- [ ] "What's Included" matches tier documentation
- [ ] "What's NOT Included" present (prevents scope creep)
- [ ] Timeline realistic (4/6/8-10 weeks based on tier)
- [ ] Contact information accurate
- [ ] No typos or grammatical errors
- [ ] PDF renders correctly (no formatting issues)
- [ ] File named correctly: `{business-name}-proposal-{date}.pdf`

---

### Step 8: Send Proposal

**Objective:** Deliver proposal to client and schedule follow-up

**Actions:**
1. Email proposal:
   - Subject: "Proposal: [Business Name] Digital Transformation"
   - Body: Brief cover letter (see template below)
   - Attach PDF
   - CC yourself (for records)

2. Schedule follow-up:
   - Add calendar reminder (3 days after sending)
   - Create ClickUp task: "Follow up with [Client Name] on proposal"

3. Log in CRM:
   - Update ClickUp list status: "Proposal Sent"
   - Add note with proposal details

**Email Template:**
```
Subject: Proposal: Tony's Pizza Naples Digital Transformation

Hi Tony,

Great talking with you yesterday about automating phone orders and capturing more customers online.

Attached is your custom proposal for the Growth System. This includes:
- Professional website with online ordering
- Voice AI to handle calls 24/7
- Automated order confirmations
- CRM to track all orders

Based on your current call volume (missing 20-30% during dinner rush), we estimate this system will capture an additional 40-60 orders per month, paying for itself within 4 months.

Next steps:
1. Review the proposal
2. Let's schedule a 15-minute call to answer any questions
3. If it looks good, we can start immediately (6-week timeline to launch)

Let me know when you're available for a quick call this week.

Best,
William Marceau
Marceau Solutions
wmarceau@marceausolutions.com
+1 239-555-XXXX
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Placeholder text still visible in PDF | Forgot to replace all `{PLACEHOLDERS}` | Search for `{` in markdown before converting |
| Pricing doesn't match tier | Used wrong template or modified pricing | Always reference STRIPE-PRODUCTS-V2 for pricing |
| Client says "I thought X was included" | Scope not clear in proposal | Always include "What's NOT Included" section |
| PDF formatting broken | Markdown syntax error | Validate markdown before converting to PDF |
| Timeline too aggressive | Didn't account for client delays | Add buffer: Digital Storefront = 4-5 weeks, not 3 |

---

## Success Criteria

**Proposal is ready when:**
- ✅ All client-specific data populated
- ✅ Pricing matches tier documentation exactly
- ✅ Scope clearly defined (included + excluded)
- ✅ Timeline realistic
- ✅ PDF renders professionally
- ✅ Legal terms appended
- ✅ Sent via email with follow-up scheduled

---

## Templates Location

**Proposal Templates:**
- `projects/personal-assistant/templates/proposals/digital-storefront-proposal.md`
- `projects/personal-assistant/templates/proposals/growth-system-proposal.md`
- `projects/personal-assistant/templates/proposals/enterprise-package-proposal.md`
- `projects/personal-assistant/templates/proposals/standard-terms.md`

**Reference Documentation:**
- `docs/STRIPE-PRODUCTS-V2-BUNDLED-OFFERINGS.md` (tier definitions, pricing)
- `docs/MARCEAU-SOLUTIONS-COMPLETE-SERVICE-OFFERING.md` (service descriptions)

---

## Related Workflows

- `discovery-call-intake.md` - How to conduct discovery call (before proposal)
- `client-onboarding.md` - What happens after proposal accepted (contract → kickoff)
- `md-to-pdf-conversion.md` - How to convert markdown to professional PDF

---

## Version History

- **v1.0 (2026-01-19):** Initial workflow created based on bundled pricing strategy
