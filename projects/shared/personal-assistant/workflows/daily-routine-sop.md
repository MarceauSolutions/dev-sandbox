# SOP: Daily Routine & Schedule

*Last Updated: 2026-02-09*
*Version: 2.0.0*

## Overview

Structured daily schedule optimized for fitness content creation, business growth, and personal development. Built around a non-negotiable 2-hour morning workout block.

---

## Daily Schedule

### 7:00 AM - 8:00 AM | Morning Startup (1 hr)

| Time | Activity | Details |
|------|----------|---------|
| 7:00 - 7:15 | Wake + Hydrate | Water, electrolytes, morning peptide protocol |
| 7:15 - 7:30 | Dog Walk | Short morning walk (15 min) |
| 7:30 - 7:45 | Review Morning Digest | Check overnight leads, emails, urgent items |
| 7:45 - 8:00 | Pre-Workout Nutrition | Meal prep or shake, review workout plan |

**Morning Digest Command**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/personal-assistant
python -m src.morning_digest --preview
```

**Quick Checks**:
- [ ] Hot leads from overnight SMS replies
- [ ] Urgent emails flagged
- [ ] Today's calendar/commitments
- [ ] Content posting schedule for the day

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

### 1:30 PM - 3:30 PM | Video Editing & Post-Production (2 hrs)

| Time | Activity | Details |
|------|----------|---------|
| 1:30 - 2:00 | Review pipeline output | Check auto-edits, adjust step params |
| 2:00 - 3:00 | Fine-tune edits | Manual cuts, B-roll placement, captions |
| 3:00 - 3:30 | Export & package | Run export packaging, prep thumbnails |

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

### 3:30 PM - 5:00 PM | Peptide Research & Business Education (1.5 hrs)

| Time | Activity | Details |
|------|----------|---------|
| 3:30 - 4:15 | Peptide Study | Research protocols, mechanisms, new compounds |
| 4:15 - 5:00 | Business Education | Marketing, sales, content strategy, competitor analysis |

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

---

### 5:00 PM - 6:00 PM | Business Operations & Admin (1 hr)

| Time | Activity | Details |
|------|----------|---------|
| 5:00 - 5:15 | Check SMS/lead replies | Respond to hot leads, schedule callbacks |
| 5:15 - 5:30 | Review analytics | Campaign performance, content metrics |
| 5:30 - 5:45 | Social engagement | Reply to comments, DMs, community building |
| 5:45 - 6:00 | Plan tomorrow | Set content topic, prep workout, review calendar |

**Lead Check Commands**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper
python -m src.twilio_webhook stats
python -m src.campaign_analytics report
```

---

### 6:00 PM - 7:30 PM | Extracurriculars (1.5 hrs)

| Time | Activity | Details |
|------|----------|---------|
| 6:00 - 6:45 | Dog Training + Walk | Evening walk with training exercises |
| 6:45 - 7:30 | Reading | Books on business, fitness, psychology, biohacking |

**Reading List Rotation**:
- Business/Entrepreneurship (Mon/Wed)
- Fitness/Exercise Science (Tue/Thu)
- Psychology/Habits/Productivity (Fri)
- Personal interest / fiction (Weekends)

**Dog Training Focus**:
- Obedience drills during walk (heel, sit, stay, recall)
- Socialization if possible
- Mental stimulation (puzzle toys, scent work) on return

---

### 7:30 PM - 8:30 PM | Dinner & Wind Down (1 hr)

| Time | Activity | Details |
|------|----------|---------|
| 7:30 - 8:00 | Dinner | Meal prep or cook |
| 8:00 - 8:30 | Wind down | Light stretching, prep for next day |

---

## Weekly Variations

| Day | Workout Focus | Content Theme | Extra |
|-----|--------------|---------------|-------|
| **Mon** | Push (Chest/Shoulders/Tri) | Gym hack / quick tip | Weekly planning |
| **Tue** | Pull (Back/Biceps) | Exercise tutorial | Peptide deep-dive |
| **Wed** | Legs (Quads/Hams/Glutes) | Science/peptide content | Analytics review |
| **Thu** | Push variation | Transformation / results | Lead follow-up |
| **Fri** | Pull variation | Week recap + motivation | Business review |
| **Sat** | Full body / Active recovery | Long-form workout | Extended reading |
| **Sun** | Rest / Light cardio | Lifestyle / nutrition / dog | Meal prep, relax |

---

## Time Allocation Summary

| Category | Hours/Day | Hours/Week | % of Productive Day |
|----------|-----------|------------|---------------------|
| **Workout** | 2.0 | 14.0 | 18% |
| **Recording** | 2.0 | 14.0 | 18% |
| **Editing** | 2.0 | 14.0 | 18% |
| **Peptide + Business Study** | 1.5 | 10.5 | 14% |
| **Business Ops** | 1.0 | 7.0 | 9% |
| **Extracurriculars** | 1.5 | 10.5 | 14% |
| **Morning Startup** | 1.0 | 7.0 | 9% |
| **Total Productive** | **11.0** | **77.0** | **100%** |

---

## Quick Reference Commands

```bash
# Morning digest
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

- [ ] Workout completed every day by 11 AM (minimum 5 days/week)
- [ ] At least 1 piece of content recorded daily
- [ ] At least 1 edited video published daily (short-form)
- [ ] 45 min+ peptide/business study daily
- [ ] Hot leads contacted same day
- [ ] Dog walked and trained daily
- [ ] Reading 30+ min daily
- [ ] Tomorrow planned before bed

---

## References

- [Weekly Routine SOP](weekly-routine-sop.md)
- [Multi-Platform Content Strategy](../../marceau-solutions/fitness-influencer/MULTI-PLATFORM-CONTENT-STRATEGY.md)
- [Video Pipeline Presets](../../marceau-solutions/fitness-influencer/backend/pipeline_orchestrator.py)
