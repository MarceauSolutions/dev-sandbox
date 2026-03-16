# SMS Outreach Optimization Strategy

> This document guides the AutoIterator when proposing SMS template variants.
> It encodes brand voice, compliance rules, proven patterns, and optimization targets.

## Domain Context

Marceau Solutions runs two categories of SMS outreach:

1. **Warm Outreach** — Personal network for PT coaching ($197/mo, evidence-based training + peptide protocols)
2. **B2B Cold Outreach** — Local businesses for digital services (Voice AI, automation, websites)

Both operate through Twilio (toll-free: +1 855-239-9364, A2P registered).

## Brand Voice Rules

- **Direct & personal** — Always open with "Hey {name}" or "Hi {name}". Never generic corporate.
- **Problem-first** — Lead with the pain point, then the solution. Never lead with features.
- **Conversational, no fluff** — Short sentences. Real language. "No pitch, just an honest convo."
- **Signature** — Close with "— William" or include phone number for credibility.
- **Evidence framing** — Use "evidence-based", "peptide-informed", "data-driven" — never hype words like "revolutionary", "game-changing", "incredible results".
- **Naples local** — Reference local context when relevant ("here in Naples", "SW Florida").
- **Professional warmth** — Friendly but not salesy. Think helpful neighbor who happens to be an expert.

## Compliance Constraints (Non-Negotiable)

These are HARD constraints. Any variant violating these MUST be rejected:

| Rule | Requirement |
|------|-------------|
| **Opt-out** | Every SMS must include "Reply STOP to opt out" |
| **Character limit** | Max 160 characters per segment (prefer single-segment) |
| **Identification** | Must identify sender by name in first message of sequence |
| **Quiet hours** | No sends before 8 AM or after 9 PM recipient local time |
| **No spam triggers** | Never use ALL CAPS words, "URGENT", "LIMITED TIME OFFER", excessive punctuation (!!!), or dollar signs ($$$) |
| **Truthful claims** | No fabricated statistics, fake testimonials, or misleading urgency |
| **A2P compliance** | Messages must match registered campaign use case |

## Current Best Performers

### Warm Outreach (PT Coaching)

**Best intro template** — `gym_friend`:
```
Hey {name}! It's William. I just launched my fitness coaching business — evidence-based training with peptide-informed protocols. I built a free body recomp calculator that gives you custom macros and a training plan. Try it out: {quiz_url}

Would love your feedback. And if you know anyone looking for a coach, send them my way!
```
- Why it works: Personal, value-first (free calculator), low-pressure CTA, referral ask

**Best follow-up** — `follow_up`:
```
Hey {name}, just following up! I know you're busy. Quick reminder about my free Body Recomp Calculator: {quiz_url}

Takes 2 minutes, gives you personalized macros and training recommendations. No strings attached. Let me know what you think!
```
- Why it works: Acknowledges their time, re-states value prop, zero pressure

### B2B Cold Outreach (Digital Services)

**Best intro** — HVAC Voice AI:
```
Hi, William from SW Florida Comfort. How many AC service calls do you miss after 5 PM? Our Voice AI answers 24/7. Want a free demo? (239) XXX-XXXX. Reply STOP to opt out.
```
- Why it works: Problem-first question, specific pain point (after 5 PM), clear CTA

**Best breakup** — HVAC scarcity:
```
Last text - SW Florida Comfort. Only setting up 2 more HVAC businesses with Voice AI this month. Want 24/7 coverage? Text YES or call (239) XXX-XXXX. Reply STOP to opt out.
```
- Why it works: Clear finality, real scarcity (2 slots), binary CTA (YES/call)

## Proven Optimization Patterns

These patterns have been validated through past campaigns. Use them as building blocks:

1. **Question Engagement** — Opening with a specific question drives 2-3x more responses than a statement. The question must reference a real pain point, not be generic.

2. **Scarcity + Specificity** — "Only taking 3 more clients this month" outperforms vague urgency. The number must be believable (2-5 range).

3. **Micro-Commitment CTA** — "Quick yes or no" or "Text YES" outperforms "Schedule a call" or "Visit this URL". Lower friction = higher response.

4. **Three-Touch Hormozi Structure**:
   - Touch 1 (Day 0): Problem-first intro with value offer
   - Touch 2 (Day 2-3): Engagement question, softer tone
   - Touch 3 (Day 5-7): Breakup with scarcity — "Last text"

5. **Social Proof Injection** — "Just helped a client..." mid-sequence lifts response rates. Must be specific (not "many clients have seen results").

6. **Value Before Ask** — Free tool/guide/quiz before any sales ask. The free offer should be genuinely useful standalone.

## What to Optimize

### Primary Metrics (Composite Score)
- **Response Rate** (weight: 0.40) — Any reply (positive, negative, or question)
- **Hot Lead Rate** (weight: 0.30) — Replies indicating buying intent ("yes", "interested", "tell me more")
- **Opt-Out Rate** (weight: -0.30) — "STOP" or unsubscribe replies (penalty)

### Target Benchmarks
| Metric | Warm Outreach | B2B Cold | Stretch Goal |
|--------|--------------|----------|-------------|
| Response Rate | 15-25% | 5-8% | +3% over baseline |
| Hot Lead Rate | 8-12% | 2-4% | +2% over baseline |
| Opt-Out Rate | <1% | <2% | Maintain or reduce |

## Variant Generation Guidelines

When proposing a new variant:

1. **Change ONE variable at a time** — Don't rewrite the entire template. Test: opener, CTA, value prop, tone, or structure individually. This isolates what works.

2. **Stay within brand voice** — Variants that sound like a different person will be rejected. William's voice is warm but direct, expert but approachable.

3. **Preserve compliance elements** — STOP language, sender ID, and truthful claims are non-negotiable. Build around them.

4. **Include a hypothesis** — Every variant must state what it's testing and why. "Testing whether a question opener outperforms a statement opener because questions require mental engagement."

5. **Consider the sequence position** — An intro variant is different from a follow-up variant. Don't optimize a Day 0 message with Day 7 tactics.

6. **Respect the audience** — Warm contacts get different treatment than cold B2B. Never use cold outreach aggression on personal network.

## Template Variables Available

| Variable | Description | Example |
|----------|-------------|---------|
| `{name}` | Recipient first name | "Mike" |
| `{business_name}` | Recipient's business | "Naples AC Pros" |
| `{quiz_url}` | Body recomp calculator link | Short URL |
| `{calendly_url}` | Free strategy call booking | calendly.com/wmarceau/... |
| `{phone}` | William's phone number | (239) 398-5676 |

## Anti-Patterns (Never Do These)

- Generic openers: "Dear valued customer" or "Attention business owner"
- Feature dumps: Listing 5+ features in a single SMS
- Fake urgency: "LAST CHANCE!!!" or "EXPIRES IN 24 HOURS"
- Aggressive follow-ups: More than 3 touches without a response
- Copying competitors: Templates that read like every other coach/agency
- Over-personalization: Using data the recipient didn't knowingly share
- Long URLs: Always use short links — raw URLs eat character budget

## Measurement & Evaluation

- **Minimum sample**: 30 sends before evaluating a variant
- **Measurement window**: 7 days from first send
- **Statistical significance**: Wait for the evaluator's confidence check before declaring a winner
- **Revert threshold**: If opt-out rate exceeds 3% at any point, auto-revert immediately
- **Approval required**: All SMS variants require human approval before deployment (William reviews via Telegram)
