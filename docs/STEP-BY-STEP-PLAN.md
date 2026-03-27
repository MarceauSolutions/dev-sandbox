# Company on a Laptop — Final Step-by-Step Activation Plan

**Date:** March 27, 2026
**Goal:** Move from building to using the system and land the first client.

---

## Phase 1: Today (Immediate Setup — 15–30 minutes)

### 1. Add GROQ_API_KEY to EC2

Get your key from https://console.groq.com/keys then run:

```bash
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97 \
  'echo "GROQ_API_KEY=gsk_YOUR_KEY_HERE" >> /home/clawdbot/dev-sandbox/.env'
```

### 2. Install Continue.dev in VS Code

This gives you Groq-powered file editing alongside Claude Code.

1. Open VS Code
2. Press `Cmd+Shift+X` → search "Continue" → Install
3. Click the Continue icon in the sidebar → gear icon → "Open config.json"
4. Add your Groq model:

```json
{
  "models": [
    {
      "title": "Groq Llama 3.3 70B",
      "provider": "groq",
      "model": "llama-3.3-70b-versatile",
      "apiKey": "gsk_YOUR_KEY_HERE"
    }
  ]
}
```

5. Save. Select code → `Cmd+L` to chat with Groq. `Cmd+I` for inline edits.

### 3. Run one supervised live loop (optional but recommended)

```bash
cd ~/dev-sandbox/projects/lead-generation
python3 -m src.daily_loop full --for-real
```

Watch it complete all 6 stages. Check your sent mail to confirm outreach delivered.

---

## Phase 2: Tomorrow Morning (First Real Run)

### 6:30am — Morning Digest arrives on Telegram

You'll see something like this:

```
☀️ MORNING DIGEST — Friday, March 28

🟢 SYSTEM HEALTH: All checks pass
🎯 GOAL: Land first AI client by April 6 (9d left)

📋 TODAY'S PLAN
  ❗ 09:00–11:00: Walk-in visits: A&Y Auto Service, Dolphin Cooling
  💰 Expected ROI: MEDIUM — 5 visit targets

📊 PIPELINE
  239 Contacted → 9 Qualified → 1 Trial Active

📧 EMAIL (N unread)
📅 TODAY (events)
✅ ACTION ITEMS
```

### Your actions

1. **Read the digest** — 1 minute
2. **Reply "yes schedule"** if the proposed time blocks look good — they go on your Google Calendar
3. **Go visit the leads** the system recommended

### When you get a HOT lead SMS

```
🔥 HOT LEAD — Naples Med Spa
"This sounds interesting, can we talk?"

Reply: 1 = Calendly link | 2 = I'll call | 3 = Pass
```

Reply with one digit. The system handles the rest.

### After each visit or call

Record what happened:

```bash
cd ~/dev-sandbox/projects/lead-generation

# Good conversation
python3 -m src.daily_loop record --deal 42 --outcome conversation --notes "Wants proposal"

# Meeting booked
python3 -m src.daily_loop record --deal 42 --outcome meeting_booked --notes "Thursday 2pm"

# Client won
python3 -m src.daily_loop record --deal 42 --outcome client_won --notes "Signed $2000 + $350/mo"
```

---

## Phase 3: Daily Routine (Ongoing)

### Evening (2 commands)

```bash
cd ~/dev-sandbox/projects/lead-generation
python3 -m src.daily_loop status

cd ~/dev-sandbox
./scripts/save.sh "end of day"
```

### Morning

1. Read the 6:30am Telegram digest
2. Reply "yes schedule" to accept time blocks
3. Execute the plan (visits, calls, follow-ups)

### Update goals anytime

**From your phone** (text to Twilio number):
```
goal short: Land 2 clients by April 15
goal medium: $5000/mo recurring by July
goal long: Full-time Marceau Solutions by 2027
```

**From terminal:**
```bash
cd ~/dev-sandbox/projects/personal-assistant
python3 -m src.goal_manager set --term short_term --goal "Land 2 clients by April 15" --deadline 2026-04-15
python3 -m src.goal_manager show
```

---

## Phase 4: Long-Term (Post-April 6)

### Schedule automatically adapts

After April 6, the scheduler switches to work-day blocks:
- 6:15–6:45am: Pre-work prep
- 12:00–12:45pm: Lunch outreach calls
- 3:15–5:15pm: Post-work visits
- 6:00–8:00pm: Training (protected, never scheduled over)

### Research-first policy

Every Claude Code session now reads this from CLAUDE.md before executing tasks:
1. Check data first (pipeline.db, outcomes)
2. Do NOT execute your first instinct — validate with data
3. Present alternatives with tradeoffs
4. Verify from your perspective before declaring complete
5. Never give false completion signals

### Generate branded PDFs

```bash
# Operation guides, proposals, workout plans
./make-pdf.sh docs/LIVE-OPERATION-GUIDE.md
./make-pdf.sh drafts/client-proposal.md "Naples Med Spa Proposal"
./make-pdf.sh clients/julia-week5-program.md
```

Auto-detects template from filename. Output: `projects/fitness-influencer/outputs/branded-pdfs/`

---

Print or save this to your phone. The heavy lifting is done. Now focus on visiting leads and closing clients. Check the 6:30am digest tomorrow.
