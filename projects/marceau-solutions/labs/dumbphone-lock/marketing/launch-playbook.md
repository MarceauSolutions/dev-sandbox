# DumbPhone Lock — Launch Playbook

> Complete step-by-step guide to validate market demand using the Hormozi framework.
> Goal: 100+ waitlist signups in 48 hours = GO on $99 Apple Developer account.

---

## Phase 1: Pre-Launch Checklist (Before Posting)

- [ ] Landing page live at marceausolutions.com/dumbphone
- [ ] Link-in-bio page live at marceausolutions.com/links
- [ ] n8n workflows active (3): Waitlist Capture, Email Confirm, SMS Drip
- [ ] Google Sheets tab "DumbPhone Waitlist" exists with headers
- [ ] Test signup works end-to-end (form → sheet → email → SMS)
- [ ] Bio links updated on all social platforms to marceausolutions.com/links

---

## Phase 2: Organic Launch (Day 1 — Free)

### Reddit Thread Hunting (Do First — 30 min)

Before posting your own threads, find and comment on existing conversations. This looks organic and builds credibility.

**Subreddits to Search:**

| Subreddit | Size | Search Keywords |
|-----------|------|----------------|
| r/nosurf | ~400K | "screen time", "block apps", "dumb phone" |
| r/digitalminimalism | ~250K | "light phone", "phone addiction", "app blocker" |
| r/productivity | ~2.5M | "focus app", "phone distraction", "deep work" |
| r/dumbphones | ~50K | "iPhone", "want dumb phone but", "best app" |
| r/getdisciplined | ~1M | "phone addiction", "can't stop scrolling" |
| r/selfimprovement | ~1.5M | "screen time", "digital detox" |

**How to Find Threads:**
1. Go to each subreddit
2. Use the search bar with the keywords above
3. Sort by "New" or "Hot"
4. Look for threads where people are asking for solutions

**Comment Templates:**

For "what app should I use" threads:
> I've been working on something for this exact problem. Most apps just send you a notification you can dismiss. I'm building one that uses Apple's FamilyControls API — the same system parents use to lock their kids' phones. You literally can't access blocked apps. Still in early development but I have a waitlist if you want to try it: marceausolutions.com/dumbphone

For "I want a dumb phone but need X" threads:
> This is exactly why I started building DumbPhone Lock. I didn't want to spend $300 on a Light Phone and lose maps/banking. So I'm making an app that turns your iPhone into a dumb phone on demand — keep the apps you need, block everything else. Waitlist here if you're interested: marceausolutions.com/dumbphone

For "screen time limits don't work" threads:
> Screen Time limits fail because you can dismiss them in one tap. I'm building an app that uses Apple's FamilyControls API — the same blocking tech parents use for kids' phones. You literally can't bypass it. Still early stage: marceausolutions.com/dumbphone

### Reddit Posts (30 min apart, after commenting)

Post dedicated threads in this order:

| Order | Subreddit | Post | UTM |
|-------|-----------|------|-----|
| 1 | r/nosurf | "I built an app that turns your iPhone into a dumb phone..." | `?utm_source=reddit&utm_medium=post&utm_campaign=nosurf` |
| 2 | r/productivity | "It takes 23 minutes to refocus after a distraction..." | `?utm_source=reddit&utm_medium=post&utm_campaign=productivity` |
| 3 | r/digitalminimalism | "Instead of buying a dumb phone, I'm building an app..." | `?utm_source=reddit&utm_medium=post&utm_campaign=digitalminimalism` |
| 4 | r/dumbphones | "I want a dumb phone but need maps, banking, and Uber..." | `?utm_source=reddit&utm_medium=post&utm_campaign=dumbphones` |

Full copy for each post: see `dumbphone-launch-copy.md`

### Twitter/X Thread

Post the 9-tweet thread from `dumbphone-launch-copy.md`. Key tips:
- Post all 9 tweets as a thread (not individually)
- Pin the thread to your profile
- Reply to your own thread 1-2 hours later with a screenshot of the app

### Instagram Reel

- Upload your screen recording of the app in action
- Use the caption from `dumbphone-launch-copy.md`
- Add all 10 hashtags
- Add "Link in bio" as the CTA

### TikTok Video

- Upload same screen recording (vertical 9:16)
- Keep under 30 seconds
- Text overlay: "Turn your iPhone into a dumb phone"
- Caption from `dumbphone-launch-copy.md`

### Hacker News — Show HN

- Post the technical version from `dumbphone-launch-copy.md`
- Best posting times: 6-9am EST weekdays
- Respond to every comment within the first 2 hours

---

## Phase 3: Paid Ads (Day 1-5 — $100 Total)

### Meta Ads — $50 (Facebook + Instagram)

**Setup:** business.facebook.com > Ads Manager > New Campaign

| Setting | Value |
|---------|-------|
| Objective | Leads (or Traffic if no pixel) |
| Budget | $5-10/day for 5 days |
| Placement | IG Feed, IG Stories, IG Reels, FB Feed |
| Schedule | Start today, run 5 days |

**Ad Set 1: "Digital Minimalism"**
- Age: 18-44, US
- Interests: Digital minimalism, Cal Newport, Deep Work, Productivity, Focus

**Ad Set 2: "Phone Addiction"**
- Age: 18-34, US
- Interests: Screen time, Digital detox, Dopamine detox, Mindfulness, Self-improvement

**3 Creative Variants:** Problem Hook (video), Comparison Hook (video), Stat Hook (static image)
Full specs in `dumbphone-ad-briefs.md`

### TikTok Ads — $25

**Setup:** ads.tiktok.com > New Campaign

| Setting | Value |
|---------|-------|
| Objective | Traffic |
| Budget | $5-10/day for 5 days |
| Placement | TikTok Feed |
| Age | 18-34, US |
| Interests | Self improvement, Productivity, Technology |

### Reddit Ads — $25

**Setup:** ads.reddit.com > New Campaign

| Setting | Value |
|---------|-------|
| Objective | Traffic |
| Budget | $5/day for 5 days |
| Subreddit targeting | r/nosurf, r/productivity, r/digitalminimalism, r/getdisciplined, r/selfimprovement, r/dumbphones, r/minimalism |

---

## Phase 4: Competitor Positioning

Use these angles when people mention competitors:

| Competitor | Price | Their Weakness | Your Angle |
|-----------|-------|---------------|------------|
| Opal | $79.99/yr | Too expensive | "Free/cheap, same result" |
| One Sec | $4.99/mo | Just pauses, doesn't block | "Real lock, not a nudge" |
| AppBlock | Free-$5/mo | Android-first, iOS limited | "Built native for iOS" |
| Forest | Free-$4 | Gamification, no real block | "Uses Apple's actual blocking API" |
| Freedom | $8.99/mo | No FamilyControls lock | "Can't bypass — same tech as parental controls" |
| ScreenZen | Free | No enforcement | "Real enforcement, not suggestions" |
| Light Phone | $299 + plan | Separate device, no maps/banking | "Uses your existing iPhone, keeps essential apps" |

**Key differentiator:** Apple's FamilyControls API = same system parents use to lock kids' phones. You can't dismiss it with one tap like Screen Time limits.

---

## Phase 5: Monitoring & Metrics

### Check Every 12 Hours

- [ ] Google Sheets "DumbPhone Waitlist" — count new signups
- [ ] UTM breakdown — which source is converting best
- [ ] n8n execution logs — any failed workflows
- [ ] Reddit post engagement — upvotes, comments, saves
- [ ] Ad dashboards — CPC, CTR, cost per lead

### Ad Kill Criteria

| Metric | Kill If | After |
|--------|---------|-------|
| CPC (Cost per Click) | > $1.00 | 48 hours |
| CTR (Click-Through Rate) | < 0.5% | 48 hours |
| Cost per Lead | > $5.00 | 48 hours |

### Good Metrics

| Metric | Good | Great |
|--------|------|-------|
| CPC | < $0.50 | < $0.25 |
| CTR | > 1% | > 2% |
| Cost per Lead | < $3 | < $1.50 |

---

## Phase 6: Go/No-Go Decision

### 48-Hour Check (Organic Only)

| Result | Signups | Action |
|--------|---------|--------|
| **GO** | 100+ | Scale paid ads, buy $99 Apple Developer account |
| **PIVOT** | 50-100 | Iterate copy and positioning, don't invest yet |
| **NO-GO** | Under 50 | Rethink the product or the audience |

### 5-Day Check (After Paid Ads)

| Result | Cost per Lead | Action |
|--------|--------------|--------|
| **GO** | Under $2 | Validated demand — invest in development |
| **MODERATE** | $2-5 | Optimize funnel first, then re-test |
| **NO-GO** | Over $5 | Pivot positioning or reconsider entirely |

### Ultimate Validation Signal

If people reply to the Day 3 and Day 7 SMS drip texts with feature requests, you have **real demand** — people are engaged enough to text back about what they want.

---

## Quick Reference

| Asset | Location |
|-------|----------|
| Landing page | marceausolutions.com/dumbphone |
| Link-in-bio | marceausolutions.com/links |
| Ready-to-paste copy | `marketing/dumbphone-launch-copy.md` |
| Ad specs & briefs | `marketing/dumbphone-ad-briefs.md` |
| Google Sheet | "Challenge Leads" > "DumbPhone Waitlist" tab |
| n8n Waitlist Capture | Workflow ID: A9TdMLSIjUBXYXiI |
| n8n Email Confirm | Workflow ID: ilNn24FqfZcYGxcT |
| n8n SMS Drip | Workflow ID: 4GKRU7i0JOh01yVT |

---

*Marceau Solutions — Embrace the Pain & Defy the Odds*
