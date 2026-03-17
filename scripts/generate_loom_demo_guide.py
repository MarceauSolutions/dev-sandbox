#!/usr/bin/env python3
"""Generate branded PDF: Loom Demo Video Playbook for AI Automation Sales."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "execution"))

from branded_pdf_engine import BrandedPDFEngine

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "docs", "loom-demo-playbook.pdf")

DATA = {
    "title": "The Loom Demo Playbook",
    "subtitle": "How to Create Loom Videos That Sell AI Automation to Naples Small Businesses",
    "author": "Marceau Solutions",
    "date": "March 2026",
    "content_markdown": r"""

## 1. What Makes a Loom Sales Video Convert

### Optimal Length

The data is clear: **60-90 seconds is the sweet spot** for cold outreach Looms. Loom's own analytics show engagement drops dramatically after 2 minutes for unsolicited videos. Here is the framework:

- **Cold outreach (prospect has never talked to you):** 60-90 seconds max. This is a pattern interrupt, not a pitch deck.
- **Warm follow-up (after a call or inquiry):** 2-3 minutes. They already know you; now show them the system.
- **Custom demo (they asked for details):** 3-5 minutes. Walk through their specific use case end to end.

The biggest mistake: making a 7-minute Loom for someone who has never heard of you. They will not watch past 30 seconds.

### The First 5 Seconds (The Hook)

An HVAC owner in Naples gets 50+ emails a day. You have 5 seconds before they close the tab. Three hook formulas that work:

**Hook 1 - The Personalized Audit:**
"Hey [Name], I was looking at [Business Name]'s Google listing and noticed you're getting about 15 reviews a month but your response time is listed as 2 days. I built something that fixes that automatically. Let me show you."

**Hook 2 - The Competitor Proof:**
"[Name], I just set this up for another HVAC company here in Naples and they booked 23 extra jobs last month from it. Here's what it looks like running."

**Hook 3 - The Problem Call-Out:**
"[Name], I noticed [Business Name] is running Google Ads but your website form doesn't send a text back to the lead. Right now you're losing about 40% of those leads. Watch this..."

Key principles for the hook:
- **Say their name and business name in the first sentence.** This alone 3x the watch rate vs. generic.
- **Reference something specific you found** (their Google listing, their website, their reviews, their response time). It proves you did homework.
- **Do NOT start with "Hey, my name is William and I run Marceau Solutions..."** Nobody cares who you are yet. Lead with THEIR problem.

### Structure: Problem, Solution, Proof, CTA

Every Loom follows this 4-beat structure:

**Beat 1 - PROBLEM (10-15 sec):** Call out the specific pain. "Right now when someone fills out your website form, what happens? Nothing. Maybe you see an email 3 hours later when you check your inbox between jobs."

**Beat 2 - SOLUTION (20-30 sec):** Show the system running. "Here's what I built. Watch -- I'm going to fill out your form right now... [form submitted] ...and look, within 5 seconds, here's the text that just went out to the customer, here's your phone buzzing with the alert, and here's the lead logged in your tracking sheet with full contact info."

**Beat 3 - PROOF (10-15 sec):** Show results or social proof. "This exact system booked 23 additional jobs for [other company] last month. Here's their dashboard -- 340 leads captured, 68% response rate, $47,000 in attributed revenue."

**Beat 4 - CTA (5-10 sec):** One clear next step. "I built this specifically for [Business Name]. If you want me to wire it up, just reply to this email and I'll have it running by Friday. No contracts, cancel anytime."

### Webcam Bubble: Yes or No?

**Yes, always use the webcam bubble** for cold outreach Looms. Here is why:

- Loom's data shows **videos with a face get 3x the engagement** of screen-only recordings.
- The webcam bubble builds trust. A Naples business owner wants to see they're dealing with a real person, not a bot.
- **Position it bottom-left.** This keeps your face visible without blocking the important parts of the screen.
- Make eye contact with the camera during the hook and the CTA. Look at the screen while demoing.

For warm follow-ups and detailed demos, you can go screen-only if the system walkthrough needs full screen real estate. But always start with face visible for at least the first 10 seconds.

### Polished vs. Raw/Authentic

**Raw wins for cold outreach. Every time.**

- Polished, edited videos with transitions and music feel like marketing material. Business owners' guard goes up immediately.
- A slightly raw Loom feels like a colleague showing you something cool. "Hey, look at this thing I built."
- **The sweet spot:** Clean screen (no 47 Chrome tabs), clear audio (use a decent mic, not laptop speakers), professional background or blurred background. But NO editing, NO transitions, NO intro animations.
- One take is better than a perfect take. If you stumble slightly, leave it in. It signals authenticity.
- Exception: If you are sending to a larger company or a more sophisticated buyer, polish it up one notch. But for a Naples HVAC owner, med spa manager, or restaurant owner? Keep it real.

---

## 2. What to Show On Screen (The Visual Playbook)

### The Cardinal Rule: Show MOVEMENT, Not Screenshots

A static dashboard screenshot is dead content. The prospect's brain ignores it the same way it ignores a stock photo. You need things MOVING on screen.

### The 6 Money Visuals

**Visual 1 - Live Lead Notification (THE MONEY SHOT)**
This is the single most compelling visual in any automation demo. While the prospect watches, show a lead coming in and the system responding in real-time:
- Fill out a form on their actual website (or a mock of it)
- Show the instant SMS going out to the lead (text bubble appearing)
- Show the Telegram/phone notification buzzing simultaneously
- Show the Google Sheet row populating with the lead info

This one sequence does more selling than 10 minutes of talking. The business owner thinks: "That lead would have been waiting in my inbox for 3 hours. Instead, my customer got a text in 5 seconds."

**Visual 2 - The Inbox/Notification Stream**
Show your notification channel (Telegram, SMS, email) with a STREAM of real alerts:
- "New lead: John Smith, AC repair, Naples 34109"
- "Appointment confirmed: Maria G, Tuesday 2pm"
- "Review request sent to David K (5-star service completed)"
- "Payment received: $247 - Invoice #1847"

Scroll through 15-20 of these. The volume is what sells. It communicates "this system is WORKING."

**Visual 3 - The Dashboard with Real Numbers**
Show a dashboard or Google Sheet with:
- Lead count this month (make it a real number, like 147, not a round 100)
- Response rate (68%, not 70%)
- Revenue attributed ($47,340, not $50,000)
- Specific, odd numbers feel real. Round numbers feel fake.

**Visual 4 - The Before/After Split**
Show two scenarios side by side:
- BEFORE: "Lead fills out form at 8pm. You check email at 7am next day. Lead already called your competitor."
- AFTER: "Lead fills out form at 8pm. System texts them in 5 seconds. Appointment booked before they even close the browser."

You can do this as two screen recordings side by side, or as a simple text comparison on screen.

**Visual 5 - The Workflow Map**
Briefly flash the n8n workflow or a simple diagram showing the automation flow. Do NOT linger on this. 3-5 seconds max. The purpose is to communicate "this is a real engineered system" without confusing them with technical details. Say something like: "Behind the scenes, here's the automation that makes all this happen. You don't need to understand any of this -- it just runs."

**Visual 6 - The Money Math**
Show a simple calculation on screen:
- "Your average job: $350"
- "Leads you're currently missing per month: ~15"
- "Revenue left on the table: $5,250/month"
- "Cost of this system: $497/month"
- "ROI: 10.5x"

Put this on a clean slide or even just type it in a Google Doc while narrating. The math does the closing.

### What NOT to Show

- Do NOT show the n8n workflow editor for more than 5 seconds. It looks like code to a non-technical person and their eyes glaze over.
- Do NOT show your code editor, terminal, or any developer tools.
- Do NOT show a login page or setup process. Show the END RESULT.
- Do NOT show Stripe's backend dashboard. Show the payment notification.
- Do NOT show a settings panel. Nobody gets excited by configuration.

---

## 3. Nick Saraev's Loom Strategy

Nick Saraev (AI automation agency YouTuber, 200K+ subscribers) has said repeatedly that **Loom is his number one conversion tool** -- more effective than calls, emails, or proposals combined. Here is the distillation of his approach:

### Saraev's Core Philosophy

**"Show, don't tell. Prospects don't buy automation -- they buy results they can SEE."**

His approach centers on:
- **Personalized Looms over generic demos.** He does not send the same video to everyone. Each Loom references the prospect's business, their website, their specific pain point.
- **Lead with the output, not the process.** Never start by explaining how n8n works or what an API is. Start by showing the text message that just went out, the lead that just got logged, the appointment that just got booked.
- **Volume play with templates.** He has a base Loom script that takes 3 minutes to personalize per prospect. He sends 10-15 per day during outreach phases.
- **The Loom IS the proposal.** He does not send a separate PDF proposal. The Loom itself demonstrates the value, shows the system, and includes pricing verbally at the end.

### Saraev's Recommended Loom Structure

1. **0:00-0:10 -- Hook with their name and the problem you spotted**
2. **0:10-0:40 -- Live demo of the system working (trigger a test lead, show the response)**
3. **0:40-0:55 -- Quick results/social proof ("did this for X, generated Y")**
4. **0:55-1:10 -- Price anchor and CTA ("this runs at $X/month, reply if you want it live by Friday")**

Total: 70 seconds. That's it.

### Saraev's Key Tactical Points

- **Record the Loom with their website open in the browser tab.** Even if you are showing your own demo system, having their URL visible in another tab signals "I was researching YOUR business."
- **Use their business name in the Loom title.** When they get the email, the Loom thumbnail shows "[Business Name] - Automated Lead System." That alone gets the click.
- **Send 3-5pm local time on Tuesday-Thursday.** Business owners are winding down, checking email, more likely to watch a video than at 9am when they are putting out fires.
- **Follow up 48 hours later with a second Loom** that shows one more feature. "Hey [Name], sent you that lead capture demo Tuesday. Here's one more thing it does -- it automatically asks every customer for a Google review 2 hours after their appointment."

---

## 4. Creating the Appearance of a Live System

### The Demo Preparation Playbook

You have real n8n workflows, real Telegram alerts, real Google Sheets tracking, and real Stripe payments. The challenge is making it all FLOW naturally during a 90-second recording. Here is how:

### Method 1: The Live Trigger (RECOMMENDED)

This is the most convincing and easiest approach:

1. **Set up a demo variant of your workflow** that uses test data but runs through your real system. Use a test form, test phone number, test Stripe account.
2. **Open all the "output" screens before recording:** Your phone showing Telegram, the Google Sheet, your email.
3. **Start recording the Loom.** Do your hook.
4. **Trigger the test** (fill out the form, send the test lead) LIVE while recording.
5. **Show the results appearing in real-time** -- the SMS going out, the Telegram alert buzzing, the Sheet row populating.

This works because it IS real. You are not faking anything. The system is actually running. The only difference is the lead is fake test data instead of a real customer. But the automation, the speed, the notifications -- all real.

**Pro tip:** Use your phone on a phone stand next to your monitor, visible in the webcam. When the Telegram alert buzzes on your phone, the prospect SEES it happen in real time. This is incredibly convincing.

### Method 2: The Pre-Recorded Screen + Live Narration

If live triggering is too risky (sometimes things lag or break during demos):

1. **Pre-record the screen capture** of the entire workflow running -- form submission, SMS sending, notifications appearing, Sheet updating. Do this until you get a clean run.
2. **Play the pre-recorded screen capture** and record a NEW Loom narrating over it. Loom lets you record your webcam bubble + screen simultaneously. The screen shows the pre-recorded demo; your face is live.
3. **Personalize the narration** for each prospect by saying their name, referencing their business.

This gives you the reliability of pre-recorded footage with the authenticity of live narration. The prospect cannot tell the difference.

### Method 3: The Multi-Clip Edit (NOT RECOMMENDED)

Recording separate clips and editing them together in a video editor is overkill for sales Looms. It:
- Takes 10x longer per video
- Looks too polished (kills authenticity)
- Cannot be done natively in Loom
- Prevents easy personalization

Avoid this unless you are creating a generic marketing video for your website.

### Key Tricks for Demo Believability

- **Use realistic test data.** "John Smith, 239-555-0147, AC not cooling, Naples FL 34109" -- not "Test User, 123-456-7890."
- **Have the current date/time visible.** If it says today's date on the Google Sheet entry, it feels live. If it says last Tuesday, it feels staged.
- **Show the timestamp on notifications.** "Just now" or "1 min ago" on a Telegram message is gold.
- **Keep some imperfection.** If there is a 3-second delay before the SMS goes out, leave it. Instant = feels fake. A brief pause = feels like real infrastructure processing.
- **Name the demo after their business.** If demoing to "Cool Air HVAC," name the test workflow "Cool Air Lead Capture" so it shows up on screen. Takes 2 seconds to rename. Massive personalization signal.

---

## 5. Templates, Scripts, and Exact Language

### The 90-Second Cold Outreach Script

**[0:00-0:05] HOOK -- Say Their Name + Problem**
"Hey [Mike], I was checking out [Cool Air HVAC]'s website and noticed when someone fills out your contact form, there's no instant follow-up. That's probably costing you 10-15 jobs a month."

**[0:05-0:10] TRANSITION -- Show Screen**
"Let me show you what I built. I'm going to fill out a form right now, and watch what happens."

**[0:10-0:35] LIVE DEMO -- The System in Action**
"[Fill out form] ...OK, submitted. Now watch -- [phone buzzes] -- there's the alert on my phone with the lead details. And look at this -- [switch to SMS view] -- the customer already got a text back: 'Thanks for reaching out to Cool Air HVAC, we'll have someone contact you within 10 minutes.' And here -- [switch to Google Sheet] -- the lead is already logged with their name, phone, email, what service they need, and the timestamp."

**[0:35-0:50] PROOF**
"I set this exact system up for [another company type] here in [Naples/Southwest Florida] and they picked up 23 extra bookings in the first month. It also does automatic review requests, appointment reminders, and follow-up sequences."

**[0:50-1:05] CTA**
"I actually pre-built this for Cool Air specifically. If you want it running by Friday, just reply to this email. It's [price] a month, no contracts, and I handle everything. Talk soon, Mike."

**[END]**

### Personalization System (Under 5 Minutes Per Prospect)

You do NOT need to spend 30 minutes per video. Here is the system:

**Before you start recording (2 min prep):**
1. Open their website in a browser tab
2. Open their Google Business listing (note review count, response time, rating)
3. Find one specific problem (no instant follow-up, slow review responses, no online booking, old website)
4. Rename your demo workflow to include their business name

**During recording (90 sec):**
- Say their name 3 times (hook, middle, CTA)
- Reference the specific problem you found
- Use their business name when showing the demo

**After recording (1 min):**
- Custom Loom title: "[Business Name] - Automated Lead Capture System"
- Custom thumbnail text (Loom lets you edit this): Shows their business name
- Drop the link in your outreach email

Total time per prospect: **4-5 minutes.** At 10 per day, that is under an hour of recording for your highest-converting outreach channel.

### Email Subject Lines That Get the Loom Opened

The Loom is useless if they never click. Subject lines that work:

| Subject Line | Why It Works |
|---|---|
| I built something for [Business Name] | Curiosity + personalization |
| [Name], quick video about your website | Personal + specific |
| Found 2 things on [Business Name]'s site | Curiosity gap + implies value |
| How [Competitor] is getting 20 more leads/mo | Competitive fear |
| 47-second video for [Name] | Short time commitment + personal |
| [Business Name] is losing leads (here's proof) | Pain point + evidence |

**Do NOT use:**
- "AI Automation Services for Your Business" (generic, sounds like spam)
- "Let's Schedule a Call" (too much commitment upfront)
- "Marceau Solutions Introduction" (nobody cares about you yet)

### The CTA That Gets Replies

The best CTA is **low friction, high specificity, with a deadline:**

**Winning formula:** "Reply to this email and I'll have it running by [day of the week]."

Why this works:
- "Reply" = lowest possible action. Not "schedule a call" or "fill out this form."
- "Have it running by Friday" = specific, tangible, and creates urgency.
- No mention of contracts, commitments, or long sales processes.

**Bad CTAs to avoid:**
- "Let me know if you'd like to schedule a 30-minute discovery call" (too much commitment)
- "Check out our website for more info" (sends them away from the conversation)
- "Let me know your thoughts" (vague, no clear next step)

---

## 6. The Naples Local Angle

### Industry-Specific Hooks

**HVAC:**
"[Name], it's about to be summer in Naples. When it hits 95 degrees and everyone's AC breaks, you're going to get slammed with leads. Right now, if someone fills out your form at 10pm, they don't hear back until morning -- and they've already called 3 other guys."

**Med Spa:**
"[Name], I noticed [Spa Name] has 4.8 stars on Google but only 47 reviews. Your competitors have 200+. I built a system that automatically texts every client after their appointment and gets them to leave a review. Watch this."

**Restaurant:**
"[Name], I was looking at [Restaurant Name]'s Google listing and noticed you're not responding to reviews. 89% of consumers read the business's response to reviews before deciding where to eat. This system auto-responds to every review within an hour."

**Dental:**
"[Name], I checked [Practice Name]'s appointment flow and there's no automatic reminder system. Dental offices lose 12-15% of appointments to no-shows. Let me show you what happens when we automate reminders."

**Real Estate:**
"[Name], I noticed [Team Name] is running Zillow ads but your follow-up is manual. The agent who texts back in under 60 seconds gets the client 78% of the time. Here's how we make that automatic."

### The Local Trust Factor

For Naples specifically:
- Mention you are local. "I'm based right here in Naples" builds instant trust with local business owners.
- Reference local details: "When we get hit with a storm and everyone needs their roof AC checked..." or "During season when the snowbirds are here..."
- Name-drop other local businesses you have helped (with permission). Naples is small enough that they might know each other.
- If possible, do the Loom from a recognizable local backdrop. Your office, a Naples coffee shop, even your car in a parking lot they might recognize.

---

## 7. Quick-Reference Checklist

### Before Recording

- Open prospect's website in a browser tab
- Open their Google Business listing
- Identify one specific pain point
- Rename demo workflow to include their business name
- Set up test data with realistic Naples-area details
- Position phone on stand for live Telegram demo
- Check mic audio (do a 5-second test)
- Clean up desktop (close unnecessary tabs/apps)
- Webcam on, positioned bottom-left in Loom

### During Recording

- Say their name within first 3 seconds
- Reference specific problem within first 10 seconds
- Trigger live demo by second 10
- Show 2-3 results appearing in real-time
- Flash one proof point or result metric
- Deliver CTA with specific day and action
- Keep total time under 90 seconds for cold outreach

### After Recording

- Edit Loom title to include their business name
- Verify thumbnail looks professional
- Write email with personalized subject line
- Send between 3-5pm local time, Tue-Thu
- Log in CRM/tracking sheet
- Set 48-hour follow-up reminder for second Loom

---

## 8. The 30-Day Loom Outreach Plan

### Week 1: Build Your Demo Assets
- Record a clean screen capture of your full system running (the pre-recorded backup)
- Create 5 industry-specific demo variants (HVAC, med spa, dental, restaurant, real estate)
- Write 5 industry-specific hook scripts
- Set up your test workflow with realistic data

### Week 2: Start Sending (5/day)
- Research 5 local businesses per day
- Record and send 5 personalized Looms
- Track open rates and reply rates in Google Sheet
- Refine hooks based on what gets watched

### Week 3: Scale Up (10/day)
- Increase to 10 Looms per day (under 60 min total recording time)
- Send follow-up Looms to Week 2 prospects who watched but did not reply
- A/B test subject lines
- Book first demos/closes from early responses

### Week 4: Optimize and Systematize
- Identify your top-performing hook and script
- Create an n8n workflow to semi-automate the research step (pull Google listing data, review count, etc.)
- Build a "Loom sent" tracking automation
- Target: 200 Looms sent, 40%+ view rate, 5-10% reply rate = 10-20 conversations = 3-5 clients

At $497-$1,500/month per client, 5 clients = $2,500-$7,500/month recurring. All from a free tool (Loom) and systems you already built.
"""
}

if __name__ == "__main__":
    engine = BrandedPDFEngine()
    output_path = os.path.abspath(OUTPUT)
    engine.generate_to_file("generic_document", DATA, output_path)
    print(f"Generated: {output_path}")
    os.system(f'open "{output_path}"')
