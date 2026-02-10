# SOP: Daily Routine & Schedule (Hormozi Framework)

*Last Updated: 2026-02-09*
*Version: 3.0.0*

## Overview

Structured daily schedule built on the **Alex Hormozi high-agency framework**: proactive, high-willpower tasks (learning, studying, strategic thinking) come FIRST in the morning when energy and discipline peak. Reactive, low-leverage tasks (editing, admin, emails, social media) are pushed to the afternoon. Built around a non-negotiable 2-hour workout block at 9 AM.

**Core Principle**: Your morning willpower is a depleting resource. Spend it on tasks that compound — learning, reading, strategic thinking. Never waste peak hours on email or social media.

---

## Daily Schedule

### 7:00 AM - 7:30 AM | Morning Startup (30 min)

| Time | Activity | Details |
|------|----------|---------|
| 7:00 - 7:15 | Wake + Hydrate | Water, electrolytes, morning peptide protocol |
| 7:15 - 7:30 | Dog Walk | Short morning walk (15 min) |

**No screens, no email, no social media.** Protect the morning.

---

### 7:30 AM - 9:00 AM | HIGH-AGENCY BLOCK (1.5 hrs - PEAK WILLPOWER)

This is the most valuable block of your day. Use it for learning and strategic thinking ONLY.

| Time | Activity | Details |
|------|----------|---------|
| 7:30 - 8:15 | Peptide Research & Deep Study | Research protocols, mechanisms, new compounds |
| 8:15 - 8:45 | Business Education & Strategy | Marketing, sales, content strategy, competitor analysis |
| 8:45 - 9:00 | Pre-Workout Nutrition | Meal prep or shake, review workout plan |

**Why this comes first**: Reading, studying, and strategic thinking require the highest cognitive load. Hormozi's rule — do the thing that makes everything else easier or unnecessary FIRST.

**Peptide Study Focus Areas** (rotate weekly):
- Week 1: BPC-157 / TB-500 (healing/recovery)
- Week 2: GH secretagogues (MK-677, CJC-1295, Ipamorelin)
- Week 3: Performance peptides (Selank, Semax, PT-141)
- Week 4: Review, summarize, create content from learnings

**Business Education Focus**:
- Content strategy optimization (analytics review)
- Competitor analysis (what's working in fitness niche)
- Platform algorithm changes (TikTok, YouTube, IG updates)
- Revenue diversification (sponsorships, affiliates, courses)
- Lead generation and client acquisition tactics

**Reading List Rotation**:
- Business/Entrepreneurship (Mon/Wed)
- Fitness/Exercise Science (Tue/Thu)
- Psychology/Habits/Productivity (Fri)
- Personal interest / biohacking (Weekends)

---

### 9:00 AM - 11:00 AM | WORKOUT (2 hrs - NON-NEGOTIABLE)

| Time | Activity | Details |
|------|----------|---------|
| 9:00 - 9:15 | Warmup | Dynamic stretching, mobility work |
| 9:15 - 10:30 | Training Session | Primary workout (push/pull/legs rotation) |
| 10:30 - 10:45 | Cooldown + Stretch | Static stretching, foam rolling |
| 10:45 - 11:00 | Post-Workout | Nutrition, shower, recover |

**Recording Notes** (if filming during workout):
- Set up camera/phone on tripod BEFORE warmup
- Film key sets (2-3 exercises minimum per session)
- Capture both angles: wide shot + close-up form
- Raw footage goes to `data/raw_footage/` for pipeline processing

---

### 11:00 AM - 1:00 PM | Video Recording & Content Creation (2 hrs)

| Time | Activity | Details |
|------|----------|---------|
| 11:00 - 11:15 | Review content calendar | Check today's planned topic from strategy |
| 11:15 - 12:15 | Record Video Content | Film talking-head, tutorials, B-roll |
| 12:15 - 12:45 | Quick Edit Pass | Import to pipeline, select preset, review |
| 12:45 - 1:00 | Publish/Schedule | Post to TikTok, queue for YouTube/IG |

Recording is still a proactive/creative task, so it sits right after the workout when energy is high.

**Content Calendar Command**:
```bash
curl https://fitai.marceausolutions.com/api/content/calendar/week/plan
```

**Pipeline Quick Edit**:
```bash
# Upload raw footage and run Humiston preset
curl -X POST https://fitai.marceausolutions.com/api/video/pipeline/run \
  -F "video=@raw_footage.mp4" \
  -F "preset_id=humiston_style"
```

**Recording Priorities** (rotate through the week):
- **Mon**: Quick workout tip / gym hack (30-60s short)
- **Tue**: Full exercise tutorial (2-3 min)
- **Wed**: Peptide education / science content
- **Thu**: Client transformation / before-after
- **Fri**: Week recap + motivation
- **Sat**: Longer-form workout follow-along
- **Sun**: Rest day content (nutrition, lifestyle, dog content)

---

### 1:00 PM - 1:30 PM | Lunch Break (30 min)

---

### 1:30 PM - 3:30 PM | Video Editing & Post-Production (2 hrs) — REACTIVE

| Time | Activity | Details |
|------|----------|---------|
| 1:30 - 2:00 | Review pipeline output | Check auto-edits, adjust step params |
| 2:00 - 3:00 | Fine-tune edits | Manual cuts, B-roll placement, captions |
| 3:00 - 3:30 | Export & package | Run export packaging, prep thumbnails |

Editing is mechanical and reactive — it doesn't require peak willpower. Afternoon is the right time.

**Editing Pipeline Commands**:
```bash
# Check job status
curl https://fitai.marceausolutions.com/api/video/pipeline/status/{job_id}

# Re-run with different preset
curl -X POST https://fitai.marceausolutions.com/api/video/pipeline/run \
  -F "video=@footage.mp4" \
  -F "preset_id=maximum_viral"

# Create export packages for all platforms
curl -X POST https://fitai.marceausolutions.com/api/video/pipeline/package/{job_id} \
  -F "platforms=tiktok,youtube_shorts,instagram_reels,youtube"
```

---

### 3:30 PM - 5:00 PM | Business Operations & Admin (1.5 hrs) — REACTIVE

| Time | Activity | Details |
|------|----------|---------|
| 3:30 - 3:45 | Check SMS/lead replies | Respond to hot leads, schedule callbacks |
| 3:45 - 4:00 | Review morning digest | Check overnight leads, emails, urgent items |
| 4:00 - 4:30 | Review analytics | Campaign performance, content metrics |
| 4:30 - 5:00 | Social engagement | Reply to comments, DMs, community building |

Email, social media, and admin are the lowest-leverage tasks. They go last in the workday. Never let these bleed into the morning.

**Morning Digest Command** (reviewed in afternoon, not morning):
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/personal-assistant
python -m src.morning_digest --preview
```

**Lead Check Commands**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper
python -m src.twilio_webhook stats
python -m src.campaign_analytics report
```

---

### 5:00 PM - 6:00 PM | Plan Tomorrow + Dog Training (1 hr)

| Time | Activity | Details |
|------|----------|---------|
| 5:00 - 5:15 | Plan tomorrow | Set content topic, prep workout, review calendar |
| 5:15 - 6:00 | Dog Training + Walk | Evening walk with training exercises |

**Dog Training Focus**:
- Obedience drills during walk (heel, sit, stay, recall)
- Socialization if possible
- Mental stimulation (puzzle toys, scent work) on return

---

### 6:00 PM - 7:00 PM | Dinner & Wind Down (1 hr)

| Time | Activity | Details |
|------|----------|---------|
| 6:00 - 6:30 | Dinner | Meal prep or cook |
| 6:30 - 7:00 | Wind down | Light stretching, prep for next day |

---

## Hormozi Framework: Why This Order

```
MORNING (High-Agency / Proactive)         AFTERNOON (Reactive / Low-Leverage)
─────────────────────────────────         ──────────────────────────────────
7:30  Peptide Study & Reading             1:30  Video Editing
8:15  Business Education & Strategy       3:30  Email, Leads, Admin
9:00  WORKOUT                             4:30  Social Media Engagement
11:00 Video Recording                     5:00  Planning & Dog Training
```

**High-agency tasks** = tasks where YOU set the agenda. Learning, creating, strategic thinking.
**Reactive tasks** = tasks where the WORLD sets the agenda. Email, social, admin, editing.

The morning is when you have the most willpower, focus, and discipline. Spend it on things that compound — studying peptides makes your content better, reading business books improves your strategy, and strategic thinking prevents wasted effort.

---

## Weekly Variations

| Day | Workout Focus | Content Theme | Morning Study Focus |
|-----|--------------|---------------|---------------------|
| **Mon** | Push (Chest/Shoulders/Tri) | Gym hack / quick tip | Business/Entrepreneurship + Weekly planning |
| **Tue** | Pull (Back/Biceps) | Exercise tutorial | Fitness/Exercise Science + Peptide deep-dive |
| **Wed** | Legs (Quads/Hams/Glutes) | Science/peptide content | Business/Entrepreneurship + Analytics review |
| **Thu** | Push variation | Transformation / results | Fitness/Exercise Science + Lead follow-up |
| **Fri** | Pull variation | Week recap + motivation | Psychology/Productivity + Business review |
| **Sat** | Full body / Active recovery | Long-form workout | Personal interest / biohacking |
| **Sun** | Rest / Light cardio | Lifestyle / nutrition / dog | Personal reading + Meal prep, relax |

---

## Time Allocation Summary

| Category | Hours/Day | Hours/Week | Priority Level |
|----------|-----------|------------|----------------|
| **High-Agency Study** | 1.5 | 10.5 | HIGHEST (morning peak) |
| **Workout** | 2.0 | 14.0 | NON-NEGOTIABLE |
| **Recording** | 2.0 | 14.0 | HIGH (creative/proactive) |
| **Editing** | 2.0 | 14.0 | MEDIUM (reactive/mechanical) |
| **Business Ops/Admin** | 1.5 | 10.5 | LOW (reactive) |
| **Dog Training + Planning** | 1.0 | 7.0 | MEDIUM (personal growth) |
| **Morning Startup** | 0.5 | 3.5 | ROUTINE |
| **Total Productive** | **10.5** | **73.5** | |

---

## Quick Reference Commands

```bash
# Morning digest (review in AFTERNOON, not morning)
cd /Users/williammarceaujr./dev-sandbox/projects/shared/personal-assistant
python -m src.morning_digest --preview

# Content calendar
curl https://fitai.marceausolutions.com/api/content/calendar/week/plan

# Lead stats
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper
python -m src.twilio_webhook stats

# Campaign analytics
python -m src.campaign_analytics report

# Run video pipeline
curl -X POST https://fitai.marceausolutions.com/api/video/pipeline/run \
  -F "video=@raw.mp4" -F "preset_id=humiston_style"

# Check pipeline presets
curl https://fitai.marceausolutions.com/api/video/pipeline/presets
```

---

## Success Criteria

- [ ] High-agency study completed every morning by 9 AM (minimum 5 days/week)
- [ ] Workout completed every day by 11 AM (minimum 5 days/week)
- [ ] At least 1 piece of content recorded daily
- [ ] At least 1 edited video published daily (short-form)
- [ ] NO email or social media before 3:30 PM
- [ ] Hot leads contacted same day (afternoon)
- [ ] Dog walked and trained daily
- [ ] Tomorrow planned before bed

---

## References

- [Weekly Routine SOP](weekly-routine-sop.md)
- [Multi-Platform Content Strategy](../../marceau-solutions/fitness-influencer/MULTI-PLATFORM-CONTENT-STRATEGY.md)
- [Video Pipeline Presets](../../marceau-solutions/fitness-influencer/backend/pipeline_orchestrator.py)
