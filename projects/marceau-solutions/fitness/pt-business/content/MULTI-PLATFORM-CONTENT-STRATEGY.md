# Multi-Platform Content Strategy

**Created**: 2026-02-09
**Business**: Personal Training + Peptide Education
**Goal**: Build-in-public business journey + Fitness/Peptide expertise positioning

---

## Critical Finding: TikTok Peptide Ban

**TikTok explicitly prohibits peptide-related content** as part of their "Drugs and Controlled Substances" policy:

> "Performance-enhancing drugs (peptides, steroids, HGH, etc.)" are listed under prohibited content.

This fundamentally changes our platform strategy. **Do NOT use TikTok for peptide education content.**

---

## Recommended Platform Strategy

| Content Type | PRIMARY | SECONDARY | AVOID |
|--------------|---------|-----------|-------|
| **Business Journey** (Build-in-Public) | X/Twitter | YouTube (monthly vlogs) | TikTok, Instagram |
| **Peptide Education** | YouTube (long-form) | X/Twitter (threads) | TikTok (BANNED) |
| **Fitness/Workouts** | Instagram Reels | TikTok | Facebook organic |
| **Client Transformations** | Instagram | YouTube | - |

---

## Platform Breakdown

### X/Twitter - BUILD IN PUBLIC HUB (Daily)

**Why X is ideal for build-in-public:**
- Strong #buildinpublic community (400K+ followers on hashtag)
- Real-time engagement and feedback
- Thread format perfect for journey documentation
- Business builders actively follow these accounts
- Examples: Alex Hormozi, Codie Sanchez, Sahil Bloom, Dan Koe

**Content Mix (4 posts/day, weekdays):**

| Time (EST) | Content Type | Example |
|------------|--------------|---------|
| 9:00 AM | Morning metric/update | "Week 3 revenue: $X. Here's what's working..." |
| 12:00 PM | Behind-the-scenes | "Just finished editing a peptide explainer. The hardest part..." |
| 3:00 PM | Lesson learned | "Made a $500 mistake yesterday. Here's what I learned..." |
| 6:00 PM | Engagement/question | "What would you want to know about building a fitness business?" |

**Build-in-Public Post Categories:**
1. **Revenue Updates** - Weekly/monthly revenue, costs, margins
2. **Wins & Milestones** - Client signups, content milestones, tool launches
3. **Failures & Lessons** - What didn't work and why
4. **Tech Stack & Automation** - Tools being built (n8n workflows, AI agents)
5. **Process Documentation** - How things get done
6. **Decision Points** - Sharing thought process on key decisions

**Hashtags:**
- #buildinpublic
- #indiehacker
- #solopreneur
- #fitnessbusiness
- #creatoreconomy

---

### YouTube - PEPTIDE EDUCATION HUB (Weekly)

**Why YouTube for peptides:**
- Long-form content allows proper context and education
- No explicit ban on peptide content (unlike TikTok)
- SEO-driven discovery - people actively search for peptide info
- Gary Brecka's model: 2.5M+ subscribers on health optimization content
- Monetization potential through ads and memberships

**Content Types:**

| Format | Frequency | Example Topics |
|--------|-----------|----------------|
| Deep-dive explainers | 1-2/week | "BPC-157 Explained: What the Science Says" |
| Research breakdowns | 1/week | "New Study on Peptides for Recovery - My Analysis" |
| Personal protocol updates | 1-2/month | "My 90-Day Peptide Stack: Results and Blood Work" |
| Q&A compilations | 1/month | "Answering Your Top Peptide Questions" |

**Compliance Notes:**
- Always include medical disclaimers
- Present as "educational content" not medical advice
- Reference peer-reviewed studies
- Avoid making specific claims about treating conditions

**Cross-promotion to X:**
- Post YouTube video link on X with key takeaway
- Create thread summarizing video for X audience
- Drive YouTube subscribers to X for daily updates

---

### Instagram - FITNESS CONTENT HUB (3-5x/week)

**Why Instagram for fitness:**
- Visual-first platform perfect for workout demos
- Reels algorithm rewards fitness content
- Client transformation photos work well
- Direct link to coaching services in bio

**Content Types:**

| Format | Frequency | Purpose |
|--------|-----------|---------|
| Workout Reels | 3-4/week | Demonstrate exercises, form tips |
| Transformation posts | 1-2/week | Client before/afters (with permission) |
| Educational carousels | 1/week | Training tips, nutrition basics |
| Stories | Daily | Behind-the-scenes, day-in-life |

**Instagram Strategy:**
- Focus on ACTION content (workouts, exercises)
- Minimal peptide discussion (save for YouTube)
- Drive to DM for coaching inquiries
- Use Stories for daily engagement

---

### TikTok - FITNESS ONLY (If Used)

**Why limited TikTok:**
- Peptide content BANNED - will get shadowbanned or removed
- Algorithm unpredictable for business content
- Best for viral workout clips only

**If using TikTok:**
- Workout form tips only
- Fitness humor/trends
- NO peptide or supplement content
- Cross-post from Instagram Reels

---

## Content Calendar Integration

The n8n workflow (X-Social-Post-Scheduler) should be updated to:

1. **Category field in Google Sheets queue:**
   - `bip_revenue` - Revenue/metric updates
   - `bip_lesson` - Lessons learned
   - `bip_behind_scenes` - Behind-the-scenes
   - `bip_milestone` - Wins and milestones
   - `bip_tech` - Tech/automation updates
   - `bip_engagement` - Questions and engagement

2. **Optimal posting schedule:**
   - Weekdays: 9am, 12pm, 3pm, 6pm EST
   - Weekends: Optional 10am, 4pm EST

3. **Content themes by day:**
   - Monday: Week preview, goals
   - Tuesday-Thursday: Core content mix
   - Friday: Week recap, wins

---

## Creator Examples to Study

| Creator | Platform Focus | Content Style |
|---------|----------------|---------------|
| **Alex Hormozi** | X, YouTube, IG | Business education, build-in-public |
| **Codie Sanchez** | X, YouTube | "Boring business" acquisitions |
| **Sahil Bloom** | X, YouTube | Newsletter growth, frameworks |
| **Dan Koe** | X, YouTube | One-person business philosophy |
| **Gary Brecka** | YouTube, X, IG | Health optimization, peptides |
| **Thomas DeLauer** | YouTube | Keto, fasting, supplements |

---

## Metrics to Track

### X/Twitter
- Follower growth (target: +100/week)
- Engagement rate (target: 2-5%)
- Profile clicks per post
- Thread completion rate

### YouTube
- Subscriber growth
- Watch time per video
- Click-through rate
- Comments per video

### Instagram
- Follower growth
- Reel views
- DM inquiries
- Profile visits

---

## Phase 1 Implementation (Next 30 Days)

### Week 1-2: X Focus
- [ ] Update n8n workflow with build-in-public categories
- [ ] Create 20 build-in-public post templates
- [ ] Schedule first 2 weeks of content
- [ ] Establish daily posting rhythm

### Week 3-4: YouTube Setup
- [ ] Create YouTube channel with brand consistency
- [ ] Record first 3 peptide education videos
- [ ] Create video templates (intro, outro, thumbnails)
- [ ] Cross-promote on X

### Ongoing: Instagram
- [ ] Post 3-4 workout Reels per week
- [ ] Cross-post from TikTok if created
- [ ] Engage with fitness community

---

## Content Generation Pipeline

```
1. Ideas Queue (Telegram → ideas_queue.py)
   ↓
2. Content Generator (business_content_generator.py)
   ↓
3. Google Sheets Queue (X_Post_Queue)
   ↓
4. n8n Workflow (X-Social-Post-Scheduler)
   ↓
5. Posted to X/Twitter
   ↓
6. Analytics Tracked (X_Post_Analytics)
```

---

## Key Takeaways

1. **X/Twitter** is the primary platform for build-in-public business content
2. **YouTube** replaces TikTok for peptide education (TikTok bans this content)
3. **Instagram** for fitness/workout content only
4. **TikTok** optional and limited to fitness-only if used at all
5. Focus on 2 platforms maximum at first (X + YouTube)
6. Use existing automation (n8n + content generator) for X content
