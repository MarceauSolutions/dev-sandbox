# Video Script: I Built a Better Claude Dispatch — Before It Even Existed

**Title Options:**
- "I Built a Better Claude Dispatch — Before It Even Existed"
- "Claude Dispatch vs. My 3-Agent AI System (It's Not Even Close)"
- "Why Claude Dispatch Can't Replace What I Built in 3 Months"

**Target Length:** 10-14 minutes
**Style:** Educational + Build-in-public, conversational
**Tone:** Confident but not arrogant — showing what you built, not bashing Anthropic
**Thumbnail Concept:** Split screen — left: Claude Dispatch logo + phone, right: your terminal/Telegram with 3 agent icons. Text overlay: "MINE IS BETTER"

---

## HOOK (0:00 - 0:45)

```
[Face to camera, sitting at desk with monitors visible behind you]

"Four days ago, Anthropic released Claude Dispatch. It lets you send tasks
to Claude from your phone, and Claude executes them on your desktop.

Cool feature. One problem — I built something that does all of that and
more, three months ago. And it runs 24/7 without my laptop even being
turned on.

I'm going to show you both systems side by side, break down exactly what
I built, and by the end of this video you'll understand why the future of
AI isn't a single chatbot — it's a system of specialized agents working
together.

Let's get into it."
```

**[VISUAL: Quick flash montage — Telegram messages dispatching tasks, terminal running, n8n workflows executing, PDFs generating]**

---

## SECTION 1: What Is Claude Dispatch? (0:45 - 2:30)

```
[Screen recording of Claude Dispatch setup + demo]

"First, let me be fair to Dispatch and explain what it actually does.

Claude Dispatch is a new feature inside Claude Desktop. You pair your
phone to your Mac by scanning a QR code, and then you can send tasks
to Claude from anywhere. Claude runs those tasks in a sandboxed
environment on your desktop.

So you could be at the gym, send a message like 'summarize my recent
emails' or 'find that screenshot from yesterday,' and Claude does it
on your Mac while you're away.

Here's the catch though —"
```

**[VISUAL: Bullet points appearing on screen]**

```
"Your Mac has to be on. Claude Desktop has to be open. It only runs
one task at a time. There's no notifications when it's done. And
according to MacStories who did a hands-on review, it has about a
50/50 success rate on tasks.

No scheduling. No webhooks. No API access. No automation.

It's basically remote-controlling a chatbot from your phone. Which
is fine! It's a research preview. But I needed something production-grade
three months ago, so I built it."
```

---

## SECTION 2: The Three-Agent Architecture (2:30 - 5:00)

```
[Switch to diagram/whiteboard showing the three agents]

"So here's what I built instead. I call it the three-agent model, and
it's been running my entire business since January.

Agent one — Claude Code. This runs on my Mac, in my terminal. It's
the power tool. I use it for complex debugging, deployments, anything
that needs my Mac-specific tools. But just like Dispatch, it only works
when my Mac is on and I'm sitting in front of it.

So I needed something for when I'm NOT at my desk. That's where
agent two comes in."
```

**[VISUAL: Highlight Clawdbot on the diagram]**

```
"Clawdbot. This is a Claude-powered bot running on an AWS EC2 server,
accessible through Telegram. It's up 24/7. Three in the morning?
Clawdbot is awake. My Mac is off? Doesn't matter. I pull out my phone,
open Telegram, and tell Clawdbot what I need.

Simple to medium complexity tasks — research, content generation, code
commits, quick builds. Complexity 0 through 6 on my scale. Clawdbot
handles it.

And here's the thing Dispatch can't do — Clawdbot can trigger agent
three."
```

**[VISUAL: Highlight Ralph on the diagram]**

```
"Ralph. Ralph is my autonomous build agent. Also on EC2. When I have
a complex feature — something that's going to touch 8 files, needs
multiple user stories, quality gates at each step — I write a PRD,
a Product Requirements Document, and Ralph executes it story by story.
Overnight. While I sleep.

Three agents. One on my laptop for interactive work, two on a server
for everything else. No single point of failure."
```

---

## SECTION 3: The Automation Layer — n8n (5:00 - 7:30)

```
[Screen recording of n8n dashboard]

"But agents alone aren't enough. You need automation. Things that happen
on a schedule, or in response to events, without anyone — human or AI —
telling them to.

I use n8n. It's an open-source workflow automation platform. Think Zapier
but self-hosted and way more powerful. I have 41 active workflows running
right now."
```

**[VISUAL: n8n workflow categories appearing as a list]**

```
"Let me walk you through what these actually do, because this is where
it gets real.

When someone pays for my coaching service through Stripe — automatically,
a welcome SMS goes out via Twilio, an onboarding email sends, their data
gets logged to Google Sheets, and a billing entry is created. Zero manual
work.

Every Monday at 9am, every active client gets a personalized check-in
SMS. Automated.

If a payment fails? The client gets an SMS about it, and I get a
Telegram notification. Automated.

I have lead capture workflows for five different funnels, each one
feeding into a 7-day nurture sequence that sends follow-up emails
automatically.

And here's my favorite — the self-annealing error handler. If ANY of
my 36 wired workflows fail, this handler catches it, logs it, and
alerts me on Telegram. The system monitors itself."
```

**[VISUAL: Show the self-annealing error handler workflow in n8n]**

```
"Claude Dispatch can't do any of this. Not one piece. It has no
scheduling, no webhooks, no event triggers, no integrations with
Stripe or Twilio or Google Sheets. It's a remote chat window."
```

---

## SECTION 4: Real Demo — Side by Side (7:30 - 10:00)

```
[Split screen demo time]

"Alright, let's do a live comparison. Same tasks, both systems.

Task one: Send myself a status update from my phone."
```

**[VISUAL: Left side — Dispatch sending a message. Right side — Telegram to Clawdbot]**

```
"Dispatch — I type the message, Claude processes it on my Mac...
assuming my Mac is on. Maybe it works, maybe it doesn't. 50/50
according to reviewers.

My system — I open Telegram, tell Clawdbot 'give me a system
status.' Instant. It checks the EC2 services, n8n workflows,
and reports back. My Mac could be powered off in a drawer.

Task two: Generate a branded report."
```

**[VISUAL: Show Telegram command → PDF generation → PDF opening]**

```
"In my system, I have a branded PDF engine. I say 'generate the
weekly revenue report' and it pulls data from Google Sheets,
formats it with my brand colors, and I've got a professional PDF.

Task three: Handle a client payment at 2am."
```

**[VISUAL: Show n8n Stripe webhook workflow]**

```
"This is where it's not even a competition. At 2am, someone signs
up for coaching. My n8n workflow fires — welcome SMS, onboarding
email, Google Sheets update, Telegram notification to me. All
automated.

With Dispatch? Nothing happens. It doesn't have webhooks. It
doesn't have event triggers. And your Mac would need to be awake
at 2am with Claude Desktop running."
```

---

## SECTION 5: What This Actually Cost (10:00 - 11:30)

```
[Face to camera, casual]

"Let's talk about what this costs to run, because people always ask.

EC2 instance — about $15 a month for a t3.small. That's running
Clawdbot, Ralph, n8n, my memory API, everything.

Claude API for Clawdbot — this runs on my Claude Max subscription.
Same $20 a month you'd pay for Dispatch anyway.

Twilio for SMS — pennies per message.

n8n — free. It's self-hosted, open-source.

Domain and SSL — already had those.

So for roughly the same price as a Claude Pro subscription, I have
a 24/7 three-agent system with 41 automated workflows, SMS
capabilities, email automation, and full API access to everything.

Dispatch gives you... remote chat with your Mac. For $20 a month.
And you need Max at $100 for early access."
```

---

## SECTION 6: Should YOU Build This? (11:30 - 13:00)

```
[Face to camera, genuine]

"Now, I want to be honest. Building this took work. I spent three
months iterating on this system. I have 33 standard operating
procedures documented. I went through 13 working sessions debugging
n8n workflows, fixing credential issues, building error handling.

But here's the thing — most of that work is done. The patterns are
established. The architecture is proven. And the individual pieces
are all open-source or free-tier tools.

If you're a developer, a solopreneur, anyone running a business
where you need AI to do real work — not just answer questions, but
actually execute tasks, handle events, run automations — you can
build this.

And honestly? With Claude Code and the tools available today, you
could probably get a basic version running in a weekend."
```

---

## CTA + CLOSE (13:00 - 14:00)

```
[Face to camera, direct]

"Here's what I want to know from you. If I open-sourced this —
the three-agent architecture, the n8n workflow templates, the
setup guides — would you use it? Drop a comment below and tell
me.

If this video helped you understand what's actually possible
with AI agents versus what these companies are shipping as
'features,' hit subscribe. I'm building all of this in public
and there's a lot more coming.

I'll drop links to everything I mentioned in the description —
n8n, Claude Code, the Telegram bot framework, all of it.

Thanks for watching. Go build something."
```

**[VISUAL: End screen with subscribe button + related video suggestions]**

---

## B-ROLL SHOT LIST

| Timestamp | Shot | Type |
|-----------|------|------|
| 0:00-0:10 | Flash montage of system in action | Screen recording |
| 0:45-2:30 | Claude Dispatch demo/setup flow | Screen recording (from Anthropic demo or own setup) |
| 2:30-5:00 | Three-agent architecture diagram | Whiteboard/animated diagram |
| 5:00-5:30 | n8n dashboard overview | Screen recording |
| 5:30-7:30 | Individual n8n workflows executing | Screen recording |
| 7:30-10:00 | Split-screen live demos | Screen recording (both systems) |
| 10:00-11:30 | Cost breakdown graphics | Motion graphics/text overlay |
| 11:30-13:00 | Quick montage of building process | Screen recording + face cam |

## DESCRIPTION TEMPLATE

```
I built a three-agent AI system that does everything Claude Dispatch does — and runs 24/7 without my laptop even being on.

In this video I break down:
→ What Claude Dispatch actually is (and its limitations)
→ My three-agent architecture: Claude Code + Clawdbot + Ralph
→ 41 automated workflows running my business on autopilot
→ Live side-by-side demo
→ What it costs to run (spoiler: same as a Claude subscription)
→ How you could build your own version

🔗 Tools mentioned:
- n8n (workflow automation): https://n8n.io
- Claude Code: https://claude.ai/claude-code
- Telegram Bot API: https://core.telegram.org/bots
- AWS EC2: https://aws.amazon.com/ec2

💬 Want me to open-source this? Let me know in the comments.

#ClaudeAI #AIAgents #Automation #n8n #Solopreneur #BuildInPublic

⏱️ Timestamps:
0:00 - Hook
0:45 - What is Claude Dispatch?
2:30 - My Three-Agent Architecture
5:00 - The Automation Layer (n8n)
7:30 - Live Side-by-Side Demo
10:00 - What This Costs
11:30 - Should You Build This?
13:00 - Subscribe + Open Source?
```

## THUMBNAIL OPTIONS

1. Split screen: Dispatch logo vs. your terminal — text: "MINE IS BETTER"
2. Your face (surprised) + Dispatch logo with X through it + your system diagram
3. Text-heavy: "I Built This 3 Months Ago" with Claude Dispatch screenshot underneath
