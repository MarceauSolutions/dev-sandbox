# Complete Handoff: Fitness Coaching Business Setup

**Date:** 2026-01-31
**From:** Clawdbot (EC2)
**To:** Cline with XAI Extension (MacBook)
**Purpose:** Set up everything for William's fitness coaching business

---

## 📋 Context Summary

William is pivoting to **online fitness coaching** as the fastest path to $5K/month. This handoff contains everything needed to set up:

1. Calendly booking link
2. Landing page redesign for coaching
3. Client onboarding automation
4. Social media content strategy

### William's Background (Use for Landing Page)
- Biomedical Engineering degree, 3.8 GPA, Math minor
- Junior Olympic swimmer (butterfly), 1st in state BMX
- Personal training experience (2x - during and after college)
- Cancer survivor who rebuilt fitness
- Tech-savvy (built AI tools, MCPs, automation systems)

### Target Market
- Busy professionals who want to get fit
- People who've tried things before and failed
- Those who need accountability and structure

### Unique Value Proposition
"Results-driven coaching with AI-powered accountability systems"
- Tech-savvy coach with real tracking systems
- Not just a guy with a clipboard
- Engineering brain + athlete experience

---

## 🗓️ Task 1: Calendly Setup

### What to Create

**Consultation Type:** Free 15-Minute Fitness Consultation

**Questions to Add (Intake Form):**
1. What's your primary fitness goal? (dropdown)
   - Build muscle
   - Lose fat
   - Get stronger
   - Improve overall health
   - Athletic performance
   - Other

2. What's your biggest challenge right now? (text)

3. Have you worked with a trainer before? (Y/N)

4. How many days per week can you commit to training? (dropdown: 2-6)

5. Do you have gym access or prefer home workouts? (dropdown)

6. Phone number (optional, for follow-up)

**Booking Settings:**
- Duration: 15 minutes
- Buffer: 5 minutes between calls
- Availability: Set to William's preferred times
- Confirmation email: On
- Reminder: 1 hour before

**Link Format:** `calendly.com/williammarceaujr/fitness-consult` (or similar)

---

## 🌐 Task 2: Landing Page Redesign

### Current State
The existing landing page is at: `projects/marceau-solutions/fitness-influencer-mcp/landing-page/index.html`

It's currently positioned as "Fitness Influencer AI - Coming Soon" (a waitlist for tools).

### New Purpose
Needs to be repositioned as William's **personal coaching offer** page.

### New Landing Page Structure

```html
<!-- SECTION 1: Hero -->
<header>
  <h1>Get in the Best Shape of Your Life</h1>
  <h2>Online Coaching for Busy Professionals</h2>
  <p>Personalized training and nutrition that fits YOUR life. No cookie-cutter programs.</p>
  <button>Book Free Consultation</button> <!-- Links to Calendly -->
</header>

<!-- SECTION 2: About / Credibility -->
<section id="about">
  <h2>Your Coach: William Marceau</h2>
  <img src="william-photo.jpg" />
  <p>
    Former Junior Olympic swimmer. Biomedical engineering degree (3.8 GPA).
    Cancer survivor who rebuilt from scratch. I've been on both sides — 
    the struggling beginner and the competitive athlete.
  </p>
  <p>
    I combine an engineering mindset with real athletic experience to build 
    programs that actually work for YOUR life. No generic templates. 
    No one-size-fits-all. Just results.
  </p>
</section>

<!-- SECTION 3: What You Get -->
<section id="services">
  <h2>What's Included</h2>
  <div class="feature">
    <h3>Custom Training Program</h3>
    <p>Built specifically for your goals, schedule, and equipment. Updated as you progress.</p>
  </div>
  <div class="feature">
    <h3>Nutrition Guidance</h3>
    <p>Flexible approach that fits your lifestyle. No extreme diets. Sustainable results.</p>
  </div>
  <div class="feature">
    <h3>Weekly Check-ins</h3>
    <p>Accountability that keeps you on track. Adjustments based on your progress.</p>
  </div>
  <div class="feature">
    <h3>Direct Access</h3>
    <p>Message me anytime with questions. Real support, not automated responses.</p>
  </div>
</section>

<!-- SECTION 4: Results / Social Proof -->
<section id="results">
  <h2>Results</h2>
  <!-- Add testimonials when available -->
  <p>Testimonials coming soon. Be one of my first success stories.</p>
  <!-- Or use William's own transformation story -->
</section>

<!-- SECTION 5: How It Works -->
<section id="process">
  <h2>How It Works</h2>
  <ol>
    <li><strong>Book a Call</strong> - 15-minute consultation to understand your goals</li>
    <li><strong>Get Your Plan</strong> - Custom program built for you within 48 hours</li>
    <li><strong>Start Training</strong> - Access via Trainerize app with video demos</li>
    <li><strong>Check In Weekly</strong> - Track progress, make adjustments, stay accountable</li>
  </ol>
</section>

<!-- SECTION 6: Pricing (Optional) -->
<section id="pricing">
  <h2>Investment</h2>
  <div class="price-card">
    <h3>1-on-1 Coaching</h3>
    <p class="price">$XXX/month</p>
    <ul>
      <li>Custom training program</li>
      <li>Nutrition guidance</li>
      <li>Weekly check-ins</li>
      <li>Direct messaging access</li>
      <li>Program adjustments as needed</li>
    </ul>
    <button>Book Free Consultation</button>
  </div>
</section>

<!-- SECTION 7: FAQ -->
<section id="faq">
  <h2>Common Questions</h2>
  <details>
    <summary>Do I need a gym membership?</summary>
    <p>No. Programs can be designed for home, gym, or minimal equipment.</p>
  </details>
  <details>
    <summary>How much time do I need?</summary>
    <p>Programs are designed for 3-5 hours/week total. Quality over quantity.</p>
  </details>
  <details>
    <summary>What if I've tried everything and nothing works?</summary>
    <p>Most people fail because of inconsistent execution, not bad programs. My job is to find what works for YOUR life and keep you accountable.</p>
  </details>
</section>

<!-- SECTION 8: Final CTA -->
<section id="cta">
  <h2>Ready to Get Started?</h2>
  <p>Book a free 15-minute call. No pressure. Just a conversation about your goals.</p>
  <button>Book Free Consultation</button>
</section>

<!-- Footer -->
<footer>
  <p>William Marceau | Online Fitness Coaching</p>
  <p>Naples, FL</p>
  <a href="mailto:wmarceau26@gmail.com">wmarceau26@gmail.com</a>
</footer>
```

### Design Notes
- Keep the purple/gradient aesthetic from current page (or go cleaner)
- Mobile-responsive (most traffic will be mobile from X/Instagram)
- Fast loading (no heavy images)
- Clear CTAs to Calendly
- Professional but personal (not corporate)

### Form Handling
The current page has a form. Options:
1. Replace form with Calendly embed
2. Keep form for lead capture (email list) + add Calendly link
3. Use Calendly's embed widget

**Recommendation:** Embed Calendly widget directly for simplicity.

---

## 📱 Task 3: Client Onboarding Automation

### Current Assets

**Existing directive:** `directives/onboard_client.md`
- Has email template structure
- Uses `execution/send_onboarding_email.py`
- Requires SMTP setup

**Trainerize MCP:** `projects/marceau-solutions/trainerize-mcp/`
- 27 tools for client management
- Can create clients, assign programs, send messages

### Recommended Onboarding Flow

```
Client Signs Up (Payment)
        │
        ▼
┌─────────────────────────────┐
│ 1. Welcome Email            │
│    - Thanks for signing up  │
│    - What to expect         │
│    - Link to intake form    │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ 2. Intake Form (Google Form)│
│    - Training history       │
│    - Goals and timeline     │
│    - Injuries/limitations   │
│    - Equipment available    │
│    - Schedule/availability  │
│    - Nutrition preferences  │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ 3. Trainerize Invite        │
│    - Create client account  │
│    - Send app invite        │
│    - Assign initial program │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ 4. Kickoff Call             │
│    - Review goals           │
│    - Explain program        │
│    - Answer questions       │
│    - Set expectations       │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ 5. Week 1 Check-in          │
│    - How's it going?        │
│    - Any questions?         │
│    - Adjustments needed?    │
└─────────────────────────────┘
```

### Implementation Options

**Option A: Manual (Start Here)**
- Use templates for emails
- Manually create clients in Trainerize
- Schedule calls via Calendly
- Use this until you have 5+ clients

**Option B: Semi-Automated (After 5 Clients)**
- Zapier/n8n triggers on payment
- Auto-send welcome email
- Auto-create intake form submission
- Manual Trainerize setup

**Option C: Full Automation (After 10+ Clients)**
- Payment → Stripe webhook
- Auto-create Trainerize client (via MCP)
- Auto-assign program template
- Auto-send all emails
- Auto-schedule kickoff call

**Recommendation:** Start with Option A. Build automation when manual becomes painful.

### Welcome Email Template

```
Subject: Welcome to Coaching! Let's Get Started 🏋️

Hey [Name],

Welcome aboard! I'm pumped to help you [reach goal].

Here's what happens next:

1. FILL OUT YOUR INTAKE FORM (5 min)
   [Link to Google Form]
   This helps me build your custom program.

2. DOWNLOAD TRAINERIZE APP
   You'll get an invite email shortly. This is where your 
   workouts, progress tracking, and our communication lives.

3. SCHEDULE YOUR KICKOFF CALL
   [Calendly Link]
   We'll review your goals, go over your program, and 
   make sure you're set up for success.

Questions before then? Just reply to this email.

Let's get to work.

William
```

### Intake Form Questions (Google Form)

1. Full name
2. Email
3. Phone (optional)
4. Age
5. Height
6. Current weight
7. Goal weight (if applicable)
8. Primary goal (dropdown)
9. Secondary goal
10. Training experience level (beginner/intermediate/advanced)
11. Current training (what are you doing now?)
12. Any injuries or limitations?
13. Equipment available (gym/home/list)
14. Days per week available
15. Preferred training times
16. Nutrition: Any dietary restrictions?
17. Nutrition: Do you track macros currently?
18. What's the #1 thing holding you back?
19. Anything else I should know?

---

## 📲 Task 4: Social Media Content Queue

### Strategy Summary (from previous handoff)

**Goal:** Acquire clients via X (and Instagram later)

**Primary method:** Value-first commenting on large accounts

**Content mix:**
- 35% Credibility (tips, myth-busting)
- 25% Relatability (personal story, struggles)
- 25% Results/proof (testimonials, transformations)
- 15% Direct CTA (DM prompts)

### Template File
Located at: `projects/shared/social-media-automation/templates/fitness-coach-client-acquisition.json`

Contains 20+ ready-to-use post templates.

### X Bio Update

```
Online Fitness Coach | Helping busy pros get lean without living at the gym | Former athlete, engineer, cancer survivor | DM 'START' for free consult
```

Or:

```
Results-driven fitness coaching | Custom programs for YOUR life | Junior Olympic swimmer → Engineer → Coach | Book free call 👇
```

### Pin a Tweet

Create a strong pinned tweet that establishes credibility and drives action:

```
I help busy professionals get in the best shape of their life.

What you get:
✅ Custom training (not cookie-cutter)
✅ Nutrition that fits your lifestyle
✅ Weekly accountability check-ins
✅ Direct access to me

3 spots available this month.

DM 'COACH' or book a free call: [calendly link]
```

---

## 🎯 Priority Order for Cline

### Session 1: Foundation (Do First)

1. **Set up Calendly**
   - Create account if needed
   - Set up "Free 15-min Consultation" 
   - Add intake questions
   - Get shareable link

2. **Update X profile**
   - New bio (coaching focused)
   - Link to Calendly
   - Pin a strong tweet

3. **Create Google Form** for client intake
   - Questions listed above
   - Get shareable link

### Session 2: Landing Page

4. **Redesign landing page**
   - Use structure above
   - Replace "Fitness Influencer AI" content
   - Focus on coaching offer
   - Embed Calendly widget
   - Mobile-responsive

5. **Deploy to GitHub Pages**
   - Test all links work
   - Verify Calendly embed functions

### Session 3: Content & Automation

6. **Queue 2 weeks of X content**
   - Use templates from `fitness-coach-client-acquisition.json`
   - Mix of tips, stories, CTAs
   - Schedule via X scheduler

7. **Create email templates**
   - Welcome email
   - Kickoff call reminder
   - Week 1 check-in

8. **Set up Trainerize** (William doing this)
   - Create account
   - Build 2-3 program templates
   - Connect payment

---

## 💬 Prompt for Cline (Copy This)

```
# Fitness Coaching Business Setup

I'm setting up an online fitness coaching business and need help with the following tasks in order:

## Context
- I'm William Marceau, pivoting to online fitness coaching
- Target: Busy professionals, goal $5K/month (10 clients × $500)
- Background: Biomedical engineering (3.8 GPA), former Junior Olympic swimmer, personal training experience, cancer survivor
- Tech stack: Trainerize for delivery, Stripe for payments, X for client acquisition

## Today's Tasks

### 1. Calendly Setup
Set up a free 15-minute fitness consultation booking page with these intake questions:
- Primary fitness goal (dropdown: Build muscle, Lose fat, Get stronger, Improve health, Athletic performance, Other)
- Biggest challenge right now (text)
- Worked with trainer before? (Y/N)
- Days per week available (2-6)
- Gym or home? (dropdown)
- Phone number (optional)

### 2. Landing Page Redesign
The existing page is at: `projects/marceau-solutions/fitness-influencer-mcp/landing-page/index.html`

Redesign it as a coaching offer page with:
- Hero: "Get in the Best Shape of Your Life - Online Coaching for Busy Professionals"
- About section with my background (engineering, athlete, cancer survivor)
- What's included (custom training, nutrition, weekly check-ins, direct access)
- How it works (book call → get plan → start training → weekly check-ins)
- FAQ section
- Calendly embed for booking
- Keep mobile-responsive, clean design

### 3. X Profile Update
Create new bio focused on coaching and suggest a strong pinned tweet.

### 4. Client Intake Form
Create a Google Form with comprehensive intake questions (training history, goals, injuries, equipment, schedule, nutrition, etc.)

### 5. Email Templates
Create templates for:
- Welcome email (after sign-up)
- Kickoff call reminder
- Week 1 check-in

## Files to Reference
- `projects/shared/social-media-automation/templates/fitness-coach-client-acquisition.json` - Content templates
- `projects/shared/social-media-automation/CLAUDE-CODE-HANDOFF-FITNESS-COACHING.md` - Strategy details
- `AUDIT-FITNESS-COACHING-ASSETS.md` - What tools are available
- `directives/onboard_client.md` - Existing onboarding flow

## Output
After each task, show me what you created and ask for approval before moving to the next task.
```

---

## 📁 Files to Pull

Before starting, `git pull` to get these new files:

```
/home/clawdbot/dev-sandbox/
├── AUDIT-FITNESS-COACHING-ASSETS.md           # Full asset audit
├── CLINE-HANDOFF-FITNESS-COACHING.md          # This file
├── WILLIAM-STRATEGIC-ANALYSIS.md              # Strategy analysis
└── projects/shared/social-media-automation/
    ├── CLAUDE-CODE-HANDOFF-FITNESS-COACHING.md
    └── templates/
        └── fitness-coach-client-acquisition.json
```

---

## ✅ Success Criteria

By end of session:

- [ ] Calendly link working with intake questions
- [ ] Landing page redesigned for coaching (deployed)
- [ ] X bio updated with coaching positioning
- [ ] Pinned tweet live
- [ ] Google Form created for detailed intake
- [ ] Welcome email template ready
- [ ] 14+ posts queued in X scheduler

---

## 🚨 Notes on Cline + XAI

Using Cline with XAI extension shouldn't change anything significant. The handoff is the same — Cline will read these files and execute the tasks.

**Tips for Cline:**
- Be explicit about file paths
- Ask for one task at a time
- Review output before moving on
- If Cline gets stuck, provide more context from the referenced files

---

*Handoff complete. William has everything needed to launch coaching business.*

*Generated 2026-01-31 by Clawdbot*
