# Claude Code Handoff: Fitness Coaching Client Acquisition

**Date:** 2026-01-30
**From:** Clawdbot (EC2)
**To:** Claude Code (MacBook)
**Priority:** HIGH - This is the new direction

---

## Strategic Context

William decided to pursue **Online Fitness Coaching** as the fastest path to $5K/month. This leverages:
- His athletic background (Junior Olympic swimmer, BMX, running)
- His personal training experience (2x)
- His tech skills (for delivery and systematization)
- Fast feedback loops (important for ADHD)

**Goal:** Acquire coaching clients organically via X (and Instagram later)

**Target:** 10 clients × $500/month = $5,000/month

---

## New Strategy: Client Acquisition Focus

### Previous Strategy (DEPRECATED)
- "AI Builder in Public"
- Target: AI developers, small business owners
- Goal: Followers and thought leadership

### New Strategy (ACTIVE)
- "Fitness Coach + Tech Edge"
- Target: Busy professionals wanting to get fit
- Goal: **DMs and coaching clients**

**Key Difference:** We don't care about follower count. We care about client sign-ups.

---

## Template File

**Location:** `templates/fitness-coach-client-acquisition.json`

Contains:
- Content pillars and percentages
- Post templates for each type
- 20+ sample posts ready to use
- Commenting strategy
- DM-to-client conversation flow
- Profile optimization
- Metrics to track

---

## Implementation Tasks

### 1. Profile Optimization

**Update X bio to:**
```
Online Fitness Coach | Helping busy pros get lean without living at the gym | DM 'START' for free consult
```

Or:
```
Results-driven coaching for people who've tried everything | Engineering brain + athlete experience | DM 'FREE' for consult
```

**Link in bio:** Set up a Calendly or simple landing page

**Pinned tweet:** Best testimonial or high-value tip post

### 2. Content Schedule

**Frequency:** 1-2 posts per day (quality > quantity)

**Times:** 9 AM and 6 PM EST

**Content Mix:**
| Type | % | Purpose |
|------|---|---------|
| Credibility (tips, myths) | 35% | Establish expertise |
| Relatability | 25% | Build connection |
| Results/proof | 25% | Social proof |
| Direct CTA | 15% | Drive DMs |

### 3. Generate Initial Queue

Create 2 weeks of posts (14-28 posts) from the templates.

**Sample posts to queue immediately:**

```
Simple tip that changed everything for my clients:

Eat protein first at every meal.

Why it works: You fill up on what matters, naturally eat less junk, and recovery improves.

Try it this week. DM me how it goes.
```

```
Not seeing results?

Here's the fix: Track what you actually eat for 3 days. Not to restrict - just to see reality.

90% of people are shocked. That awareness alone changes behavior.

Takes 5 minutes. Works every time.
```

```
"You need to eat 6 meals a day to boost metabolism."

This is wrong. Here's why:

Meal frequency doesn't affect metabolism. Total calories and protein do.

What actually works: Eat in a pattern that fits YOUR life.

Save this.
```

```
I have 3 coaching spots opening up in February.

What you get:

✅ Custom training program (not cookie-cutter)
✅ Nutrition guidance that fits your life
✅ Weekly check-ins (accountability that works)
✅ Direct access to me via text

DM 'COACH' if you're serious about results.
```

```
Quick poll:

What's holding you back from your fitness goals?

A) Time
B) Motivation
C) Don't know what to do
D) Consistency

Drop your letter below 👇 I'll reply to everyone.
```

### 4. Commenting Strategy (MORE IMPORTANT THAN POSTING)

**This is the primary client acquisition method.**

**Daily routine (30-60 minutes):**
1. Go to 3-5 large fitness accounts (100K+ followers)
2. Look at recent posts
3. Find questions in the comments
4. Answer them helpfully (NOT salesy)
5. Add value to discussions
6. Repeat

**What to do:**
- Answer questions with actual helpful advice
- Share relevant personal experience
- Add insights the original post missed
- Be genuinely helpful

**What NOT to do:**
- Pitch in comments
- Comment generic stuff ("Great post! 🔥")
- Spam the same comment
- Be argumentative

**Expected results:**
- 10-20 profile visits per day
- 3-10 DMs per week
- 1-2 clients per month initially

### 5. DM Conversation Flow

When someone DMs asking about coaching:

**Step 1:** "Hey! Thanks for reaching out. Quick question - what's your main fitness goal right now?"

**Step 2:** (After they share) "Got it. And what have you tried so far? What's worked, what hasn't?"

**Step 3:** (After they share history) "Makes sense. I think I can help. Want to jump on a quick 15-min call? I'll show you what I'd do differently. No pressure either way. [Calendly link]"

**Step 4:** On call → Qualify, present offer, close or follow up

---

## What to Do With Previous Posts

### From "AI Builder in Public" Strategy
- **Don't delete** the existing template file (keep for reference)
- **Don't queue** any AI/automation focused posts
- **This new fitness strategy takes priority**

### From Old Fitness Content
- Review any existing fitness-related posts
- Keep ones that align with new client-acquisition focus
- Remove or archive generic content

---

## Files to Update

| File | Action |
|------|--------|
| `templates/fitness-coach-client-acquisition.json` | ✅ CREATED - New strategy |
| `templates/ai-builder-content.json` | KEEP but don't use for now |
| `templates/marceau-solutions-content.json` | KEEP but deprioritize |
| `output/scheduled_posts.json` | REPLACE with fitness coaching posts |

---

## Metrics to Track

**Weekly:**
- Profile visits
- DMs received  
- Calls booked
- Clients signed

**Target Funnel:**
| Metric | Weekly Target |
|--------|---------------|
| Profile visits | 50+ |
| DMs | 5+ |
| Calls | 2+ |
| Clients/month | 2-4 |

**Focus on DMs and calls, not followers. Followers don't pay bills.**

---

## Cost Per Client

| Method | Cost | Time | Expected Clients/Month |
|--------|------|------|----------------------|
| Organic (commenting + posting) | $0 | 1-2 hrs/day | 2-4 |
| Paid ads | $50-200/client | Less time | Variable |

**Start with organic. Only add paid after organic is working.**

---

## Quick Start Commands

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation

# View new strategy
cat templates/fitness-coach-client-acquisition.json | python3 -m json.tool

# Clear old queue
python -m src.x_scheduler clear
python -m src.x_scheduler clear-archived

# Add new posts
python -m src.x_scheduler add "POST_TEXT" --campaign fitness-coaching

# View queue
python -m src.x_scheduler list
```

---

## Additional Setup Needed

### Calendly or Booking System
- Set up free 15-min consultation slots
- Link in bio

### Simple Landing Page (Optional)
- One-page "About my coaching" 
- Testimonials
- "Book a call" button

### Instagram (Phase 2)
- Same strategy applies
- Commenting even more powerful there
- But start with X to test messaging

---

## Summary

**The goal is not followers. The goal is clients.**

1. **Post** 1-2 quality pieces per day (from templates)
2. **Comment** 30-60 min per day on large accounts
3. **Respond** to DMs with qualification questions
4. **Book** calls via Calendly
5. **Close** clients on calls

**First client goal:** Within 2-3 weeks of consistent execution.

---

*Generated by Clawdbot on 2026-01-30*
