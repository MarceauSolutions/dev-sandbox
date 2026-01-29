# Cold Outreach Lessons Learned

*Last Updated: 2026-01-22*

---

## Our Niche (Defined 2026-01-22)

**We specialize in two things:**

1. **Finding problems clients don't know they have**
   - They know something's broken, but can't articulate it
   - We diagnose and propose solutions they hadn't considered

2. **Building better solutions than what clients originally asked for**
   - Client comes with an idea
   - We dig deeper, understand the full picture
   - We deliver something more comprehensive than their original vision

**This is our differentiator.** We're not product pushers. We're consultants who uncover the full picture.

**How this changes outreach:**
- Lead with discovery questions, not product pitches
- Position as "consultant who finds gaps" not "vendor selling X"
- Emphasize that we build BETTER solutions than expected

**Recommended templates:**
- `discovery_question` - Pure discovery, no pitch
- `consultant_intro` - Positions us as consultants
- `gap_finder` - Emphasizes finding hidden problems
- `better_solution` - For clients who have an idea already

---

## Key Incidents

### Inhale Exhale Wellness Spa (2026-01-22)

**What happened:**
- Sent: "Hi, calling about a gym near Inhale Exhale Wellness Spa that just got 23 new members from their website. Call back if interested."
- Response: "What am I supposed to be interested in?"
- Response: "Are you trying to give me these clients from the gym or are you trying to sell me on a website? Your message is not clear."

**Root cause:**
- Template (`competitor_hook`) made no sense for a wellness spa
- Message implied we were either:
  a) Offering to send gym members to the spa (confusing)
  b) Selling websites (but framed weirdly)
- No clear value proposition or ask

**Fix applied:**
- Deprecated `competitor_hook` template
- Created new automation-focused templates
- Lead with discovery questions, not confusing pitches

---

## Core Principles (Updated)

### 1. Lead with Discovery, Not Pitch
**Bad:** "I do X. Want it?"
**Good:** "What's taking up your time? Curious if I can help."

The best conversations start by understanding the prospect's actual pain points, not assuming we know what they need.

### 2. Make the Offer Clear
Every message should pass the "What are you selling?" test. If someone reading it can't tell what you're offering in 5 seconds, rewrite it.

**Bad:** "A gym near you got 23 new members..."
**Good:** "I help businesses automate follow-ups and scheduling."

### 3. Match Template to Business Type
Don't use gym-specific templates for spas. Don't use website templates for businesses with websites.

| Business Type | Good Templates |
|---------------|----------------|
| Wellness/Spa | `wellness_automation`, `automation_discovery` |
| Gym/Fitness | `fitness_automation`, `automation_discovery` |
| Service (HVAC, etc) | `service_business_automation` |
| No website | `no_website_intro` |
| Few reviews | `few_reviews` |
| Any | `automation_discovery`, `automation_time_saver` |

### 4. Automation > Specific Products
"Automation" is a better umbrella than:
- Voice AI (not our strongest offering yet)
- Websites (too commoditized)
- Reviews (narrow pain point)

Automation encompasses:
- Customer follow-ups
- Appointment booking
- Lead response
- Review requests
- Email/SMS sequences
- CRM integrations
- AI assistants

### 5. One Clear CTA
Don't confuse people with multiple options. One ask per message.

**Bad:** "Want a website mockup? Or an SEO audit? Or a demo?"
**Good:** "Worth a quick call?"

---

## Template Performance (To Track)

| Template | Sent | Responses | Opt-outs | Response Rate |
|----------|------|-----------|----------|---------------|
| automation_discovery | 0 | 0 | 0 | - |
| automation_time_saver | 0 | 0 | 0 | - |
| competitor_hook (DEPRECATED) | ~100 | ~1 | ~15 | ~1% (terrible) |
| no_website_intro | ~150 | ~3 | ~20 | ~2% |

*Update this table as we collect data*

---

## What We're Actually Selling

**Our real specialty:** Working closely with clients to figure out exactly what their needs are - and filling gaps they don't even know exist yet.

We're not pushing a single product. We're consultants who:
1. **Diagnose** - Find where time/money is leaking
2. **Prescribe** - Recommend the right automation for THEIR situation
3. **Implement** - Build and deploy custom solutions
4. **Optimize** - Iterate based on results

**Products we can offer (based on what they need):**

| Client Need | Our Solution |
|-------------|--------------|
| "I'm overwhelmed" | AI Assistant that handles repetitive tasks |
| "Need more leads" | Lead generation + outreach automation |
| "Missing calls" | Voice AI (with honest caveats) |
| "No follow-up system" | Automated sequences (SMS, email) |
| "Disorganized data" | CRM integration + dashboards |
| "Can't scale" | Business process automation |
| "Don't know what I need" | **Discovery session - THIS IS OUR SPECIALTY** |

**Positioning:** "AI Automation Consultants" - We find the gaps you didn't know you had.

**Key differentiator:** We don't pitch a product and hope it fits. We listen first, then build exactly what you need.

---

## Next Actions

1. [ ] Run A/B test: `automation_discovery` vs `automation_time_saver`
2. [ ] Track template performance for next 100 sends
3. [ ] Create industry-specific templates as needed
4. [ ] Update follow-up sequences to match new positioning

---

## Archive: Deprecated Templates

### competitor_hook (Removed 2026-01-22)
```
"Hi, calling about a gym near $business_name that just got 23 new members from their website. Call back if interested. -William. Reply STOP to opt out."
```
**Why removed:** Confusing, doesn't make sense for non-gym businesses, unclear value proposition.
