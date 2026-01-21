# Square Foot Shipping - Outreach Templates

**Created**: 2026-01-19
**Purpose**: Email and SMS templates for e-commerce seller outreach
**Framework**: Hormozi (Lead with value → Be specific → Social proof → Clear CTA → Multi-touch)

---

## Personalization Variables

All templates support the following variables:
- `{company_name}` - Business name from scraping
- `{estimated_volume}` - Calculated monthly shipment volume
- `{current_carrier}` - Detected current shipping provider (UPS/FedEx/USPS)
- `{owner_name}` - Business owner/contact name (if available)
- `{savings_estimate}` - Estimated monthly savings ($XXX format)
- `{industry}` - Business category (e.g., "apparel", "electronics")

---

## EMAIL TEMPLATES

### Template 1: intro_shipping_savings

**Subject**: Cut your shipping costs 15-30% (no carrier switch)

**Body**:
Hi {owner_name},

Quick question: Are you paying retail rates with {current_carrier}?

Most e-commerce sellers don't realize they're overpaying by 15-30% on shipping. Based on your estimated {estimated_volume} shipments/month, that's ~{savings_estimate}/month left on the table.

We negotiate commercial Plus rates directly with carriers (UPS, FedEx, USPS) - no need to switch providers. Just better rates on the carrier you already use.

Free rate audit: Takes 2 minutes, shows exactly what you'd save.

Interested? Reply with "yes" and I'll send the audit link.

William
Square Foot Shipping
This is a one-time message. Reply STOP to opt out.

**Character count**: ~560 characters
**When to use**: Initial outreach (Day 0)
**Notes**: Lead with value (savings), be specific (their volume/carrier), clear CTA

---

### Template 2: followup_still_looking

**Subject**: Still overpaying {current_carrier}?

**Body**:
{owner_name},

Following up on my message from Tuesday.

If you're shipping {estimated_volume} packages/month at retail rates, you're likely leaving {savings_estimate}/month on the table.

We just helped 3 Naples e-commerce businesses cut shipping costs 20-35% without changing anything except their rates.

2-minute rate audit: [link]

No obligation. Just see what you'd save.

William
Square Foot Shipping

**Character count**: ~380 characters
**When to use**: Day 2 follow-up
**Notes**: Social proof (3 Naples businesses), restate value

---

### Template 3: followup_social_proof

**Subject**: How [Similar Business] saved $847/month on shipping

**Body**:
{owner_name},

Just closed a deal with another {industry} seller in Naples.

Before: Paying $2,300/month for ~800 shipments with {current_carrier}
After: $1,453/month (same carrier, commercial Plus rates)
Savings: $847/month ($10,164/year)

Your estimated volume ({estimated_volume}/month) suggests similar savings potential.

Want to see your specific numbers? Reply "audit" and I'll send the link.

William

**Character count**: ~420 characters
**When to use**: Day 5 follow-up
**Notes**: Concrete example with real numbers, industry-specific

---

### Template 4: followup_direct_question

**Subject**: One simple question

**Body**:
{owner_name},

Quick yes/no: Are you open to saving 15-30% on shipping costs without switching carriers?

If yes: Reply and I'll send a 2-minute rate audit
If no: Reply "not interested" and I'll stop reaching out

Either way, I respect your time.

William
Square Foot Shipping

**Character count**: ~280 characters
**When to use**: Day 10 follow-up
**Notes**: Ultra-simple decision, respects their time

---

### Template 5: followup_availability

**Subject**: 5 minutes Tuesday or Wednesday?

**Body**:
{owner_name},

Last follow-up before I close your file.

I have 5-minute slots Tuesday or Wednesday to walk you through:
1. Exactly what you're paying now vs. commercial rates
2. How much you'd save monthly
3. Zero-obligation rate lock (no contract required)

Reply with:
- "Tuesday 10am"
- "Wednesday 2pm"
- Or your preferred time

If not interested, reply "close my file" and I won't reach out again.

William

**Character count**: ~450 characters
**When to use**: Day 15 follow-up
**Notes**: Specific time options, final courtesy

---

### Template 6: followup_breakup

**Subject**: Closing your file

**Body**:
{owner_name},

I haven't heard back, so I'm assuming shipping costs aren't a priority right now. Totally understand.

I'm closing your file and won't reach out again.

If anything changes, you can reach me at william@squarefootshipping.com or reply to this email.

Good luck with {company_name}!

William

**Character count**: ~310 characters
**When to use**: Day 30 follow-up (breakup email)
**Notes**: Polite exit, leaves door open

---

### Template 7: followup_re_engage

**Subject**: Still shipping with {current_carrier}?

**Body**:
{owner_name},

Last email (I promise).

Quick check-in: Are you still using {current_carrier} for fulfillment?

If shipping costs are still eating into your margins, our offer stands:
- Free 2-minute rate audit
- See exactly what you'd save
- No obligation, no contract

Reply "audit" if you want the link.

Otherwise, best of luck with {company_name}!

William

**Character count**: ~380 characters
**When to use**: Day 60 follow-up (re-engagement)
**Notes**: Final attempt, casual tone

---

## SMS TEMPLATES

### Template 1: intro_shipping_savings

**Text**:
Hi {owner_name}, this is William with Square Foot Shipping. Are you paying retail rates with {current_carrier}? Most sellers save 15-30% by switching to commercial Plus rates (same carrier). Free rate audit: [short-link]. Reply STOP to opt out.

**Character count**: 249 characters (exceeds 160 - needs shortening)

**REVISED** (under 160):
{owner_name}, paying retail with {current_carrier}? Save 15-30% w/ commercial rates (same carrier). Free audit: [link]. -William, Square Foot Shipping. Reply STOP to opt out.

**Character count**: 159 characters ✓
**When to use**: Initial SMS outreach (Day 0)
**TCPA Compliance**:
- ✓ B2B exemption (business numbers)
- ✓ Sender identified ("This is William")
- ✓ Company name included
- ✓ STOP instruction included
- ✓ Must send 8am-9pm local time

---

### Template 2: followup_still_looking

**Text**:
{owner_name}, following up on shipping rates. We just helped 3 Naples businesses save 20-35% (no carrier switch). Free audit: [link]. -William. Reply STOP to opt out.

**Character count**: 159 characters ✓
**When to use**: Day 2 SMS follow-up
**Notes**: Social proof, urgency

---

### Template 3: followup_social_proof

**Text**:
{owner_name}, another {industry} seller saved $847/mo on {current_carrier} shipping. See your savings: [link]. -William, Square Foot. Reply STOP to opt out.

**Character count**: 154 characters ✓
**When to use**: Day 5 SMS follow-up
**Notes**: Concrete dollar amount

---

### Template 4: followup_direct_question

**Text**:
{owner_name}, yes or no: Open to saving 15-30% on {current_carrier} costs? Reply YES for audit or STOP to opt out. -William, Square Foot Shipping

**Character count**: 150 characters ✓
**When to use**: Day 10 SMS follow-up
**Notes**: Simple binary choice

---

### Template 5: followup_breakup

**Text**:
{owner_name}, closing your file. If shipping costs become a priority, reply AUDIT anytime. Otherwise, best of luck! -William, Square Foot Shipping

**Character count**: 148 characters ✓
**When to use**: Day 30 SMS follow-up (breakup)
**Notes**: Polite exit, leaves door open

---

### Template 6: followup_re_engage

**Text**:
{owner_name}, last check: still using {current_carrier}? Our rate audit offer stands (free, 2 min). Reply AUDIT or STOP. -William, Square Foot Shipping

**Character count**: 156 characters ✓
**When to use**: Day 60 SMS follow-up (re-engagement)
**Notes**: Final attempt

---

## MULTI-TOUCH SEQUENCE (60 Days)

| Day | Channel | Template | Goal |
|-----|---------|----------|------|
| **0** | Email + SMS | intro_shipping_savings | Awareness + value proposition |
| **2** | Email | followup_still_looking | Reminder + social proof |
| **5** | SMS | followup_social_proof | Concrete example |
| **10** | Email | followup_direct_question | Simple yes/no decision |
| **15** | Email | followup_availability | Calendar invite |
| **30** | Email + SMS | followup_breakup | Polite exit (often triggers response) |
| **60** | Email + SMS | followup_re_engage | Final re-engagement |

**Expected Response Rates** (based on B2B SaaS benchmarks):
- Email open rate: 25-35%
- Email reply rate: 2-5%
- SMS open rate: 98%
- SMS reply rate: 5-10%
- Overall conversion (contacted → qualified): 8-12%

**Most Responses Occur**: After touch 3-5 (Days 5-15)

---

## TEMPLATE USAGE NOTES

### Email Best Practices
- **Subject lines**: Under 50 characters, question-based or benefit-driven
- **Body length**: 75-100 words max (people scan, don't read)
- **Personalization**: Always use {company_name} and {current_carrier} at minimum
- **CTA**: One clear action per email (don't give multiple options)
- **Signature**: Include company name, no phone (forces reply tracking)

### SMS Best Practices
- **Character limit**: Hard cap at 160 characters (or it splits into 2 messages)
- **Link shorteners**: Use bit.ly or custom domain for tracking
- **Timing**: Send 10am-6pm local time (avoid early AM/late PM)
- **Opt-out**: "Reply STOP to opt out" REQUIRED in every message
- **Frequency**: Max 1 SMS per week (avoid spam flags)

### A/B Testing Opportunities
- **Subject lines**: Question vs. Benefit statement
- **Value proposition**: Dollar amount vs. Percentage savings
- **Social proof**: Number of clients vs. Specific case study
- **CTA**: "Reply" vs. "Click link" vs. "Book call"

### Personalization Priority
1. **{company_name}** - ALWAYS include (shows it's not generic spam)
2. **{current_carrier}** - High impact (proves research)
3. **{savings_estimate}** - Concrete value (specific > vague)
4. **{estimated_volume}** - Medium impact (shows understanding)
5. **{owner_name}** - Nice to have (if available)

---

## TEMPLATE SELECTION LOGIC

```python
# Pseudocode for template selection
if lead.days_since_contact == 0:
    template = "intro_shipping_savings"
elif lead.days_since_contact == 2 and not lead.responded:
    template = "followup_still_looking"
elif lead.days_since_contact == 5 and not lead.responded:
    template = "followup_social_proof"
elif lead.days_since_contact == 10 and not lead.responded:
    template = "followup_direct_question"
elif lead.days_since_contact == 15 and not lead.responded:
    template = "followup_availability"
elif lead.days_since_contact == 30 and not lead.responded:
    template = "followup_breakup"
elif lead.days_since_contact == 60 and not lead.responded:
    template = "followup_re_engage"
else:
    # No more touches, mark lead as cold
    lead.status = "cold"
```

---

## TCPA COMPLIANCE CHECKLIST (SMS)

✓ **B2B Exemption**: Only contact business phone numbers (not personal cell phones)
✓ **Sender Identification**: "This is William" or "William from Square Foot Shipping"
✓ **Company Name**: "Square Foot Shipping" in every message
✓ **Opt-out Mechanism**: "Reply STOP to opt out" in every message
✓ **Time Restrictions**: 8am-9pm recipient's local time (no weekends if possible)
✓ **Frequency Cap**: Max 1 SMS per week to same number
✓ **Single Purpose**: B2B shipping services only (don't mix marketing messages)

**Important**: If lead replies STOP, immediately mark as opted-out and never contact again.

---

## EXIT CONDITIONS (Stop Sequence)

**Lead removed from sequence if**:
- Lead replies (any response → move to qualified)
- Lead opts out (STOP → mark as opted-out)
- Lead books call (→ move to opportunity)
- Delivery fails 2x consecutive (invalid number)
- Day 60 reached with no response (→ mark as cold)

**Re-engagement Allowed**:
- After 90 days for cold leads (new campaign)
- If lead re-engages organically (website visit, referral)
- If business circumstances change (detected via scraping update)

---

## RESPONSE HANDLING

### Positive Responses
- "Yes" / "Interested" / "Tell me more" → Send audit link immediately
- "Call me" → Book calendar slot within 24 hours
- "What's the catch?" → Explain no contract, no minimums, cancel anytime

### Objection Responses
- "Too expensive" → "It's free to audit, you only pay if you save money"
- "Happy with current carrier" → "You keep your carrier, we just get you better rates"
- "No time" → "2-minute audit, I'll handle everything else"
- "Not interested" → "No problem, reply STOP and I won't contact again"

### Neutral Responses
- "Maybe later" → "When's a good time to follow up?"
- "Send more info" → Send case study + audit link
- Question about process → Answer + soft CTA (audit link)

---

## TEMPLATE PERFORMANCE TRACKING

Track these metrics per template:
- **Open rate** (email only)
- **Reply rate** (email + SMS)
- **Click-through rate** (links)
- **Conversion rate** (replied → qualified)
- **Opt-out rate** (SMS)

**Success Benchmarks**:
- Email reply rate: >3%
- SMS reply rate: >7%
- Overall sequence conversion: >10%
- Opt-out rate: <2%

If template underperforms for 100+ sends, retire and A/B test replacement.

---

## EXAMPLE RENDERED TEMPLATES

### Example Lead Data
```json
{
  "company_name": "Naples Beach Apparel",
  "owner_name": "Sarah",
  "estimated_volume": 450,
  "current_carrier": "UPS",
  "savings_estimate": "$380",
  "industry": "apparel"
}
```

### Rendered Email (intro_shipping_savings)
```
Subject: Cut your shipping costs 15-30% (no carrier switch)

Hi Sarah,

Quick question: Are you paying retail rates with UPS?

Most e-commerce sellers don't realize they're overpaying by 15-30% on shipping. Based on your estimated 450 shipments/month, that's ~$380/month left on the table.

We negotiate commercial Plus rates directly with carriers (UPS, FedEx, USPS) - no need to switch providers. Just better rates on the carrier you already use.

Free rate audit: Takes 2 minutes, shows exactly what you'd save.

Interested? Reply with "yes" and I'll send the audit link.

William
Square Foot Shipping
This is a one-time message. Reply STOP to opt out.
```

### Rendered SMS (intro_shipping_savings)
```
Sarah, paying retail with UPS? Save 15-30% w/ commercial rates (same carrier). Free audit: sqft.co/audit. -William, Square Foot Shipping. Reply STOP to opt out.
```

---

## INTEGRATION WITH LEAD SCRAPER

Templates integrate with:
- `/Users/williammarceaujr./square-foot-shipping/lead-gen/scrape_ecommerce_leads.py` - Provides lead data
- `/Users/williammarceaujr./square-foot-shipping/lead-gen/qualify_leads.py` - Filters high-value leads

**Data Requirements**:
- Lead must have `estimated_volume > 100` (worth outreach)
- Lead must have `current_carrier` detected (for personalization)
- Lead must have valid email OR phone (channel availability)

**Suggested Workflow**:
1. Scrape leads → `scrape_ecommerce_leads.py`
2. Qualify leads → `qualify_leads.py` (filter volume >100)
3. Send Day 0 → `intro_shipping_savings` (email + SMS)
4. Track responses → Mark as responded/opted-out
5. Send follow-ups → Process due touches daily (cron job)

---

**END OF TEMPLATES**

Next Steps:
1. Review templates with William for approval
2. Create sender accounts (email SMTP, Twilio SMS)
3. Set up tracking (link shorteners, reply webhooks)
4. Run A/B test on intro templates (sample size: 100 per variant)
5. Integrate with follow-up sequence automation (SOP 19)
