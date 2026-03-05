# Cold Outreach Strategy

**Based on**: SOP 23 (Cold Outreach Strategy Development), SOP 18 (SMS Campaign)
**Status**: Framework ready — execute when you have prospect lists

---

## Target Segment

| Field | Definition |
|-------|-----------|
| **Who** | Men and women 25-50 in Naples, FL area |
| **Pain point** | Plateaued, inconsistent, or overwhelmed by conflicting fitness info |
| **Evidence** | Quiz archetype data shows 60%+ select "plateau" or "inconsistent" as frustration |
| **Where to find them** | Local gyms, Instagram fitness hashtags, Facebook groups, Nextdoor |
| **Disqualifiers** | Already has a coach, not in target area, under 18 |

## Core Positioning

**What makes you different (pick ONE lead angle per message):**

1. **Peptide angle**: "I help people over 35 optimize their training with evidence-based peptide protocols"
2. **Personal story angle**: "TBI survivor who rebuilt his body from scratch — now I coach others"
3. **Tech angle**: "AI-powered coaching with real-time progress tracking + gamification"
4. **Local angle**: "Naples-based fitness coach — in-person or online"

## Message Hypotheses

### Control (Current)
```
Hey {name}, I noticed you're into fitness. I'm William — I run a coaching practice
in Naples focused on evidence-based training. Would you be open to a quick chat about
your goals? No pressure.

— William, Marceau Solutions
Reply STOP to opt out
```

### Variant A (Peptide Lead)
```
Hey {name}, quick question — have you heard about how GH secretagogues can accelerate
body recomp? I'm a Naples-based coach who combines smart training with peptide science.
Happy to share what I've learned if you're curious.

— William, Marceau Solutions
Reply STOP to opt out
```

### Variant B (Personal Story Lead)
```
Hey {name}, I'm William. After a TBI, I had to rebuild my body from zero. That process
taught me more about training than any certification. Now I coach others through
plateaus using what actually works. Interested in a free strategy call?

— William, Marceau Solutions
Reply STOP to opt out
```

## A/B Test Plan

**When you reach 100 prospects:**

| Group | Size | Message | Track |
|-------|------|---------|-------|
| Control | 34 | Current template | Reply rate, booking rate |
| Variant A | 33 | Peptide lead | Reply rate, booking rate |
| Variant B | 33 | Personal story | Reply rate, booking rate |

**Decision threshold**: 85% confidence, minimum 100 contacts per variant
**Winner criteria**: Highest reply rate → becomes new Control

## Execution Steps (Per SOP 18)

1. **Dry run**: Send Control to yourself → verify formatting, links work
2. **Batch 1**: Send to 5 prospects → wait 24h → check delivery + replies
3. **Batch 2**: Send to 10 prospects → wait 24h → check metrics
4. **Full campaign**: Send to remaining prospects
5. **Track**: Delivery rate >95%, reply rate 2-5%, opt-out <2%

## Follow-Up Sequence (Per SOP 19)

If no reply to initial message:

| Day | Message |
|-----|---------|
| 2 | "Still looking for a training approach that actually works? Happy to chat." |
| 5 | "Quick follow-up — {name}, a recent client lost 22 lbs in 12 weeks. Want to know how?" |
| 10 | "Last check-in — would a free strategy call be useful? No commitment: calendly.com/wmarceau/30min" |
| 15 | "Haven't heard back — totally fine. If you ever want to talk training, I'm here. — William" |
| 30 | [Breakup] "Removing you from my list. If things change, you know where to find me." |

**Remove from sequence if**: They reply (any response), opt out, delivery fails 2x, or Day 30 reached.

## Metrics to Track

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Delivery rate | >95% | Twilio delivery receipts |
| Reply rate | 2-5% | Inbound SMS webhook |
| Opt-out rate | <2% | STOP replies |
| Booking rate | >1% of contacted | Calendly bookings |
| Conversion rate | >10% of booked calls | Stripe payments |

## Prospect Sources (Build Your List)

| Source | How | Volume |
|--------|-----|--------|
| Gym conversations | Ask for number, note interest | 3-5/week |
| Instagram DMs | Engage with local fitness accounts | 5-10/week |
| Facebook groups | Naples fitness groups, offer value first | 5-10/week |
| Nextdoor | Post helpful fitness content | 2-3/week |
| Warm network | Text 20 people you know | One-time batch |
| Referrals | Ask clients "who else would benefit?" | Ongoing |
