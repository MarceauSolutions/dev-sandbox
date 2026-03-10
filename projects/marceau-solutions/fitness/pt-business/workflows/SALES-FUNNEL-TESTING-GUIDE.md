# Sales Funnel Testing Guide

**How to test every piece of your client acquisition system as if you were a real client.**

**Version**: 1.0
**Date**: March 4, 2026
**Based on**: SOP 2 (Multi-Agent Testing), Client Acquisition System Guide v2

---

## Before You Start

### What You Need
- A phone number that ISN'T your admin phone (+1 239-398-5676) — use a Google Voice number or a friend's phone
- A test email address (e.g., `williamtest@gmail.com` or `test@marceausolutions.com`)
- Browser DevTools open (F12 → Network tab) to watch webhook calls
- n8n dashboard open in another tab: https://n8n.marceausolutions.com
- Stripe dashboard open: https://dashboard.stripe.com

### Test Environment Setup
1. Open n8n → go to each workflow → click "Executions" tab so you can see when they fire
2. Open your Leads Google Sheet so you can see entries appear in real-time
3. Have your test phone nearby to receive SMS messages
4. Use Chrome Incognito so there's no cached state

---

## Phase 1: Website Pages (Walk the Funnel)

### Test 1.1: Homepage → Quiz Entry

**Do this:**
1. Go to `https://marceausolutions.com`
2. Click every navigation link — do they all work?
3. Click "Get Your Free Custom Plan" — does it go to `/quiz.html`?
4. Click "Try the Free 7-Day Challenge" — does it go to `/challenge.html`?
5. Open on your phone — does the mobile menu work? Do buttons look right?

**Check:**
- [ ] All nav links work (Home, Coaching, Peptides, Programs, Quiz, Challenge)
- [ ] Hero section loads with video/image
- [ ] Both CTAs navigate correctly
- [ ] Mobile menu opens/closes properly
- [ ] Page loads in under 3 seconds

---

### Test 1.2: The Quiz (Full Walkthrough)

**This is the most important test. Walk through it slowly.**

**Do this:**
1. Go to `https://marceausolutions.com/quiz.html`
2. Step 1 — Select "Lose Fat" → should auto-advance after selecting
3. Insight screen should appear briefly (~2.5s) → auto-advances
4. Step 2 — Enter: Age 35, Gender Male, Weight 185, Height 5'10"
5. Click Continue → should advance to Step 3
6. Step 3 — Select "Intermediate" → auto-advances
7. Insight screen appears → auto-advances
8. Step 4 — Select "Hitting a Plateau" → auto-advances
9. Step 5 — Select "Yes, I'm interested" (peptides) → auto-advances
10. Insight screen appears → auto-advances
11. Step 6 — Select "All in — ready to start" → auto-advances
12. Step 7 — Enter your TEST name, TEST email, TEST phone number
13. Click "Get My Custom Plan"
14. Watch the 6-step processing animation
15. Results page should appear

**Verify the results (use these expected values for the test case above):**
- Archetype: **The Comeback** (all_in + plateau)
- Readiness Score: ~80-85 (high readiness + intermediate + plateau + peptide interest)
- Calories: ~2,200 (fat loss = 0.8 × TDEE)
- Protein: ~200g (1.1g/lb × 185)
- Predicted timeline: ~10 weeks
- CTAs shown: Challenge (free), Coaching ($197), **Premium Waitlist** (should appear because peptide_interest = yes)

**Check:**
- [ ] All 7 steps display correctly
- [ ] Options highlight when selected
- [ ] Progress bar updates at each step
- [ ] Can't skip steps (try clicking ahead — shouldn't work)
- [ ] Stats validation: try leaving age blank, hitting Continue → should be blocked
- [ ] Processing animation runs all 6 steps
- [ ] Results numbers animate/count up
- [ ] Archetype name + description are correct
- [ ] Macro numbers look reasonable (not NaN, not 0, not 50,000)
- [ ] All CTAs on results page are clickable

**Now check the backend:**
- [ ] Open n8n → Lead-Magnet-Capture workflow → Executions → see your test submission
- [ ] Open Google Sheets → Leads tab → your test entry should be in the last row
- [ ] Check your test phone — Day 0 SMS should arrive within 1 minute
- [ ] Check your test email — Day 0 email with macro breakdown should arrive

**Edge cases to test:**
- [ ] Submit with phone "1234567" (minimum valid) — does it accept?
- [ ] Submit with phone "123" — should be REJECTED
- [ ] Submit with email "notanemail" — should be REJECTED
- [ ] Submit with email "test@test.com" — should be ACCEPTED
- [ ] Double-click "Get My Custom Plan" rapidly — should NOT create duplicate leads
- [ ] Use browser back button after submitting — does quiz reset or show results?

---

### Test 1.3: The 7-Day Challenge Signup

**Do this:**
1. Go to `https://marceausolutions.com/challenge.html`
2. Enter your TEST name, TEST email, TEST phone
3. Click "Start My Challenge"
4. Should see "You're In!" success message

**Check:**
- [ ] Form validates (try submitting empty → blocked)
- [ ] Submit button shows loading spinner
- [ ] Success message appears after submit
- [ ] Form fields hide after success

**Backend checks:**
- [ ] n8n → Challenge-Signup-7Day workflow → Executions → see your submission
- [ ] Google Sheets → Leads tab → entry with status "challenge_signup"
- [ ] Test phone → Welcome SMS arrives
- [ ] Test email → Welcome email with week overview arrives

**Important: SMS sequence starts now.** Over the next 7 days, you should receive:
- Day 1: Workout SMS
- Day 2: Workout + nutrition tip SMS
- Day 3: Progressive overload workout SMS
- Day 4: Protein check-in SMS
- Day 5: Active recovery SMS
- Day 6: Final push workout SMS
- Day 7: Congratulations + coaching offer SMS

**Track each one as it arrives:**
| Day | Expected | Received? | Time | Content Correct? |
|-----|----------|-----------|------|-----------------|
| 0 | Welcome SMS | | | |
| 1 | Workout SMS | | | |
| 2 | Nutrition SMS | | | |
| 3 | Overload SMS | | | |
| 4 | Protein SMS | | | |
| 5 | Recovery SMS | | | |
| 6 | Final push SMS | | | |
| 7 | Offer SMS | | | |

---

### Test 1.4: Programs Page (All Tiers + Waitlist)

**Do this:**
1. Go to `https://marceausolutions.com/programs.html`
2. Scroll through all tiers — do they display correctly?
3. Click each digital product Stripe link:
   - "Get the Nutrition Blueprint" ($37) → Stripe page loads with correct price?
   - "Get the Recomp Program" ($67) → Stripe page loads with correct price?
   - "Get the Peptide Masterclass" ($97) → Stripe page loads with correct price?
4. Click "Start Coaching — $197/mo" → Stripe page loads with correct price?
5. Fill in the Premium Waitlist form (name + email) → submit

**Check:**
- [ ] All 4 Stripe links open correct products with correct prices
- [ ] Premium waitlist form submits successfully
- [ ] Success message appears after waitlist submit
- [ ] "Coming Soon" badge visible on Premium tier
- [ ] "Most Popular" badge on Coaching tier
- [ ] Mobile layout: cards stack in single column

**Backend checks:**
- [ ] n8n → Premium-Waitlist-Capture workflow → Executions → see your submission
- [ ] Google Sheets → Premium Waitlist tab → your test entry
- [ ] Test email → Confirmation email with Masterclass cross-sell

---

### Test 1.5: Coaching Page (Sales + Calendly)

**Do this:**
1. Go to `https://marceausolutions.com/coaching.html`
2. Scroll through the page — does it load completely?
3. Click each FAQ question — does it expand/collapse?
4. Scroll to #book section — does Calendly widget load?
5. Click "Start Coaching — $197/mo" → Stripe page?

**Check:**
- [ ] FAQ accordion opens/closes smoothly
- [ ] Only one FAQ open at a time (or multiple — just verify it works)
- [ ] Calendly widget loads and shows available times
- [ ] Calendly colors match brand (dark bg, gold primary)
- [ ] Stripe link opens correct product ($197/mo)
- [ ] "Book Free Strategy Call" scrolls to Calendly section

---

## Phase 2: Payment Flow (The Money Path)

### Test 2.1: Stripe Test Payment ($197/mo Coaching)

**OPTION A: Use Stripe Test Mode** (recommended — no real charge)
1. Go to Stripe Dashboard → toggle to "Test Mode" (top right)
2. Create a test payment link or use test card: `4242 4242 4242 4242`
3. Complete checkout

**OPTION B: Real Payment** (if you want to test the FULL flow including n8n)
1. Click the $197 Stripe link
2. Use your own card
3. Complete payment
4. **Immediately cancel** in Stripe dashboard after testing

**After payment, check:**
- [ ] n8n → Coaching-Payment-Welcome workflow fires
- [ ] Client Roster sheet → your name added
- [ ] Billing tab → payment logged
- [ ] Test phone → Welcome SMS with portal magic link
- [ ] Test email → Welcome email with portal CTA + Calendly + intake form
- [ ] Admin phone (+1 239-398-5676) → notification SMS received
- [ ] Portal magic link → opens `fitai.marceausolutions.com/client/` and loads dashboard
- [ ] Dashboard shows: XP bar, starter workout, quick actions

**If testing with real payment, cancel now:**
1. Stripe Dashboard → Customers → find test customer → Cancel subscription

---

### Test 2.2: Stripe Test Payment (Digital Products)

For each digital product ($37, $67, $97):
1. Click Stripe link
2. Either use test mode card or note: just verify the Stripe page loads with correct product/price
3. If you complete payment, check:
   - [ ] n8n → Digital-Product-Delivery workflow fires
   - [ ] Delivery email sent with Skool access link
   - [ ] Leads sheet updated with purchase info

---

## Phase 3: Nurture Sequence (7-Day Drip)

This tests the automated follow-up after someone takes the quiz.

### Test 3.1: Quiz → 7-Day Nurture

**After your quiz submission in Test 1.2, the nurture sequence should fire automatically.**

Track each message:

| Day | Channel | Expected Content | Received? | Notes |
|-----|---------|-----------------|-----------|-------|
| 0 | SMS | "Your custom plan is ready! Check your email." | | |
| 0 | Email | Macro breakdown (calories, protein, carbs, fat) | | |
| 1 | Email | "#1 mistake I see in every gym" | | |
| 2 | SMS | TBI recovery story (personal) | | |
| 3 | Email | "Why your coach doesn't know peptides" | | |
| 4 | SMS | Client transformation (22 lbs in 12 weeks) | | |
| 5 | Email | "3 signs your training isn't working" | | |
| 6 | SMS | What coaching week looks like | | |
| 7 | SMS + Email | THE OFFER: $197/mo, Stripe link, Calendly | | |

**Check:**
- [ ] Messages arrive on correct days (24h intervals)
- [ ] SMS messages are under 160 characters (or properly segmented)
- [ ] Emails have correct branding (dark+gold theme)
- [ ] Day 7 offer includes working Stripe payment link
- [ ] Day 7 offer includes working Calendly link
- [ ] Leads sheet "Nurture Status" updates from "Day 0" → "day7_offer_sent"

---

### Test 3.2: Non-Converter Follow-Up

**If you DON'T click the Day 7 payment link, the non-converter sequence should fire:**

| Day | Channel | Expected Content | Received? |
|-----|---------|-----------------|-----------|
| 10 | SMS | Soft check-in, offer to answer questions, Calendly link | |
| 14 | SMS | Urgency — "founding member rate won't last," Stripe link | |
| 30 | Email | Pure value — protein tracking tip using calculated target | |

- [ ] All 3 messages arrive on schedule
- [ ] Leads sheet status updates appropriately

---

## Phase 4: Portal Onboarding (Post-Payment)

### Test 4.1: Client Portal Access

**After a successful $197 payment (Test 2.1):**
1. Click the magic link from the welcome SMS
2. Portal should load at `fitai.marceausolutions.com/client/`

**Check each section:**
- [ ] **Dashboard**: XP bar, streak counter, "Today's Workout" card, quick actions
- [ ] **My Workouts**: Beginner Full Body template pre-assigned, can view exercises
- [ ] **Form Check**: Can upload a video (or at least see the upload UI)
- [ ] **Ask Coach**: AI chat loads, can send a message, gets a response
- [ ] **My Progress**: Achievements list, streak calendar, level system
- [ ] **My Profile**: Name, goals, contact info displayed

**Test gamification:**
- [ ] Complete a workout → XP increases
- [ ] Check streak counter → shows 1 day
- [ ] View achievements → "First Workout" should unlock

---

## Phase 5: Mobile Testing

Run the critical tests (quiz, challenge, coaching page) on your phone.

**iPhone / Safari:**
- [ ] Quiz: all 7 steps work, keyboard doesn't hide inputs
- [ ] Challenge: form submits, success message shows
- [ ] Coaching: Calendly widget loads
- [ ] Programs: Stripe links open correctly
- [ ] Portal: dashboard loads, workouts viewable

**Check for:**
- [ ] Buttons large enough to tap (min 44px)
- [ ] Text readable without zooming
- [ ] No horizontal scrolling
- [ ] Forms don't get cut off by keyboard

---

## Phase 6: UTM Tracking

Test that marketing attribution works.

**Do this:**
1. Visit `https://marceausolutions.com/quiz.html?utm_source=facebook&utm_medium=cpc&utm_campaign=naples_recomp`
2. Complete the quiz with test data
3. Check the webhook payload in n8n execution log

**Check:**
- [ ] `utm_source` = "facebook" in payload
- [ ] `utm_medium` = "cpc" in payload
- [ ] `utm_campaign` = "naples_recomp" in payload
- [ ] UTM values saved to Google Sheets row

---

## Phase 7: Error Scenarios

### Test 7.1: Webhook Down
1. Temporarily deactivate the Lead-Magnet-Capture workflow in n8n
2. Submit the quiz
3. What happens? Does the user see an error? Does the page hang?
4. **Re-activate the workflow immediately after testing**

### Test 7.2: Invalid Data
1. Use browser DevTools Console to bypass form validation:
   ```javascript
   document.querySelector('[type="submit"]').disabled = false;
   ```
2. Submit with empty fields — does n8n handle it gracefully?

### Test 7.3: Duplicate Submissions
1. Submit the same email/phone twice through the quiz
2. Check Google Sheets — are there 2 entries or 1?
3. Does the nurture sequence fire twice? (This would be bad — double SMS)

---

## Test Results Summary

Fill this in after running all tests:

| Phase | Tests | Passed | Failed | Critical Failures |
|-------|-------|--------|--------|-------------------|
| 1. Website Pages | | | | |
| 2. Payment Flow | | | | |
| 3. Nurture Sequence | | | | |
| 4. Portal Onboarding | | | | |
| 5. Mobile Testing | | | | |
| 6. UTM Tracking | | | | |
| 7. Error Scenarios | | | | |
| **TOTAL** | | | | |

**Critical failures** = anything that loses a lead, prevents payment, or sends wrong info.
**These must be fixed before running ads.**

---

## Quick Smoke Test (5 Minutes)

If you don't have time for the full test, run this abbreviated version:

1. **Quiz**: Submit with test data → check Sheets + SMS arrives (2 min)
2. **Challenge**: Submit with test data → check Sheets + SMS arrives (1 min)
3. **Stripe**: Click the $197 link → verify Stripe page loads with correct price (30 sec)
4. **Programs**: Click all 4 Stripe links → verify they load (1 min)
5. **Mobile**: Open quiz on phone → complete 2 steps → verify it works (30 sec)

If all 5 pass, your funnel is operational. Run the full test before scaling.

---

*Created March 4, 2026. Run this test suite monthly, or before any major campaign launch.*
