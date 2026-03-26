# Descript Project Setup Guide - Vuori Lead Magnet Video

## Asset Verification

| Asset | File | Type | Verified |
|-------|------|------|----------|
| Messy Spreadsheet | `assets/messy-spreadsheet.html` | Static HTML (scrollable) | ✅ |
| Stats Slide | `assets/stats-slide.html` | Static HTML | ✅ |
| Dashboard | `assets/dashboard-demo.html` | Interactive mockup (CSS hover states) | ✅ |

**Interactivity Note:**
- Messy spreadsheet & stats slide: Static, use mouse movement for visual interest
- Dashboard: Has CSS hover effects on stat cards, queue items, activity feed, filter chips, and status badges

**Dashboard Hover Effects:**
- Stat cards: Lift up with purple border glow
- Queue items: Slide right with purple background
- Activity items: Subtle background highlight
- Filter chips: Scale up slightly
- Status badges: Pop with shadow

**Future Vision:** Dashboard could include click actions, modals, and live data. Current version demonstrates UI polish for video demo.

---

## Overview

This guide walks you through recording and organizing clips for the 30-second Vuori influencer outreach video using Descript.

---

## Pre-Recording Setup

### 1. Open All Assets in Browser Tabs

```bash
open /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/vuori-lead-magnet/assets/messy-spreadsheet.html
open /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/vuori-lead-magnet/assets/stats-slide.html
open /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/vuori-lead-magnet/assets/dashboard-demo.html
```

### 2. Browser Setup
- Use Chrome or Safari in **full screen mode** (Cmd+Shift+F)
- Hide bookmarks bar (Cmd+Shift+B)
- Close all other tabs
- Set zoom to 100% (Cmd+0)

---

## Clips to Record

Record each clip separately using QuickTime (Cmd+Shift+5 → Screen Recording) or Descript's built-in recorder.

### Clip 1: Messy Spreadsheet (5-8 seconds)
**File name:** `01-messy-spreadsheet.mov`

**What to show:**
1. Start with spreadsheet visible
2. Slowly scroll down to reveal chaos
3. Hover over highlighted red cells (missed follow-ups)
4. Scroll right to show "DUPLICATE?" and "MISSING" entries

**Actions:**
- Scroll speed: Slow, deliberate
- Mouse: Visible, pointing at problem areas
- Duration: 5-8 seconds total

---

### Clip 2: Stats Slide (4-5 seconds)
**File name:** `02-stats-slide.mov`

**What to show:**
1. Full stats slide visible
2. Hold still for 4-5 seconds (text will be read over this)

**Actions:**
- No scrolling needed
- Just a clean, static shot
- Duration: 4-5 seconds

---

### Clip 3: Dashboard - Overview (3-4 seconds)
**File name:** `03-dashboard-overview.mov`

**What to show:**
1. Full dashboard visible
2. Brief pause to show clean layout

**Actions:**
- No clicking yet
- Just establishing shot
- Duration: 3-4 seconds

---

### Clip 4: Dashboard - Stats Cards (3 seconds)
**File name:** `04-dashboard-stats.mov`

**What to show:**
1. Slowly move mouse across the 4 stat cards at the top
2. Hover on each card to trigger the lift effect
3. Pause on "Response Rate" (28.5%) - this is the impressive number

**Actions:**
- Mouse glides left-to-right across stat cards
- Cards lift up with purple glow on hover
- Pause briefly on "Response Rate" card
- Duration: 3 seconds

---

### Clip 5: Dashboard - Creator Pipeline (4-5 seconds)
**File name:** `05-dashboard-pipeline.mov`

**What to show:**
1. Move mouse to the Creator Pipeline table
2. Point at Jordan Williams row (highlighted yellow with "HOT LEAD" badge)
3. Hover over status badges to trigger pop effect

**Actions:**
- Mouse traces down the creator rows (rows highlight on hover)
- Hover on status badges - they pop with shadow effect
- Pause on "Interested!" badge for Jordan Williams
- Duration: 4-5 seconds

---

### Clip 6: Dashboard - Today's Queue (3-4 seconds)
**File name:** `06-dashboard-queue.mov`

**What to show:**
1. Move to "Today's Queue" panel on the right
2. Hover over queue items to trigger slide effect

**Actions:**
- Mouse moves through queue items
- Items slide right with purple background on hover
- Shows automated scheduling in action
- Duration: 3-4 seconds

---

### Clip 7: Dashboard - Recent Activity (3-4 seconds)
**File name:** `07-dashboard-activity.mov`

**What to show:**
1. Move to "Recent Activity" feed at bottom right
2. Hover over activity items to trigger highlight effect

**Actions:**
- Mouse moves through activity items (subtle background on hover)
- Pause on Jordan Williams reply: "Sounds great! What are the details?"
- Shows real-time activity tracking
- Duration: 3-4 seconds

---

## Talking Head Recording (Recommended)

**Why talking head?** Face-on-camera builds trust and professionalism. Vuori sees a real person, not just a faceless pitch.

### Recording Setup
**File name:** `talking-head-full.mov`

**Equipment:**
- Webcam or phone camera (front-facing)
- Good lighting (face the window or use a ring light)
- Clean background (plain wall, bookshelf, or blurred)
- Eye-level camera position

**Recording Options:**
1. **Loom** - Records face + screen together, easy to share
2. **QuickTime** - Record face separately, combine in Descript
3. **Descript** - Built-in webcam recording

### Script to Deliver (on camera)

**Target Audience:** Catherine Johnston, Vuori's Influencer Partnership Manager (and similar brand-side roles)

```
[HOOK - 3 sec] (Look directly at camera, confident)
"Managing influencer outreach in spreadsheets? There's a better way."

[PROBLEM - 5 sec] (Slight head shake, empathetic)
"You're probably losing creators because you can't track who you've contacted,
who's responded, and who needs follow-up."

[SOCIAL PROOF - 7 sec] (Lean in slightly, credible)
"We've helped fitness brands cut admin time by 70% while tripling their
creator response rates—without sacrificing personalization."

[SOLUTION - 10 sec] (Gestures welcome, enthusiastic)
"Our AI handles your outreach, follow-ups, and scheduling automatically.
You focus on strategy. We handle the pipeline."

[CTA - 5 sec] (Warm smile, inviting)
"Want to see how it works for Vuori? I'd love to show you a quick demo."
```

**Delivery Tips:**
- Look directly at camera lens (not screen)
- Speak conversationally, like talking to a friend
- Use hand gestures naturally
- Smile at the end during CTA
- Don't worry about mistakes—Descript can edit them out

### Backup: AI Voice
If needed, Descript can generate voiceover from script. Less personal, use only as fallback.

---

## Descript Project Organization

### Folder Structure in Descript

```
Vuori Lead Magnet/
├── Media/
│   ├── Screen Clips/
│   │   ├── 01-messy-spreadsheet.mov
│   │   ├── 02-stats-slide.mov
│   │   ├── 03-dashboard-overview.mov
│   │   ├── 04-dashboard-stats.mov
│   │   ├── 05-dashboard-pipeline.mov
│   │   ├── 06-dashboard-queue.mov
│   │   └── 07-dashboard-activity.mov
│   └── Talking Head/
│       └── talking-head-full.mov
└── Compositions/
    └── vuori-30sec-final
```

---

## Assembly in Descript

### Step 1: Import All Media
1. Create new project "Vuori Lead Magnet"
2. Drag all clips into Media panel
3. Drag voiceover into Media panel

### Step 2: Create Composition
1. New Composition → "vuori-30sec-final"
2. Add talking head video to timeline first
3. Descript will auto-transcribe your speech

### Step 3: Match Clips to Transcript

| Transcript Section | Clip to Use | Duration |
|-------------------|-------------|----------|
| "Managing influencer outreach in spreadsheets?" | 01-messy-spreadsheet | 3 sec |
| "You're probably losing creators because..." | 01-messy-spreadsheet (continued) | 5 sec |
| "We've helped fitness brands cut admin time by 70%..." | 02-stats-slide | 7 sec |
| "Our AI handles your outreach..." | 03-dashboard-overview | 2 sec |
| "...follow-ups..." | 04-dashboard-stats | 2 sec |
| "...and scheduling automatically" | 06-dashboard-queue | 2 sec |
| "You focus on strategy. We handle the pipeline." | 05-dashboard-pipeline | 4 sec |
| "Want to see how it works for Vuori?" | 07-dashboard-activity | 3 sec |
| "I'd love to show you a quick demo" | 03-dashboard-overview (or logo) | 2 sec |

### Step 4: Fine-Tune
1. Adjust clip timing to match speech
2. Add transitions (cross-dissolve, 0.3s works well)
3. Add captions (Descript auto-generates from transcript)

### Step 5: Export
- Format: MP4
- Resolution: 1080x1920 (vertical for Instagram/TikTok) or 1920x1080 (horizontal for LinkedIn)
- Quality: High

---

## Recording Checklist

Before you start:
- [ ] All 3 HTML assets open in browser tabs
- [ ] Browser in full screen, bookmarks hidden
- [ ] Screen recorder ready (QuickTime or Descript)
- [ ] Good lighting for talking head (face window or ring light)
- [ ] Script printed or on second monitor

Clips to record:
- [ ] 01-messy-spreadsheet.mov (5-8 sec)
- [ ] 02-stats-slide.mov (4-5 sec)
- [ ] 03-dashboard-overview.mov (3-4 sec)
- [ ] 04-dashboard-stats.mov (3 sec)
- [ ] 05-dashboard-pipeline.mov (4-5 sec)
- [ ] 06-dashboard-queue.mov (3-4 sec)
- [ ] 07-dashboard-activity.mov (3-4 sec)
- [ ] talking-head-full.mov (~30 sec)

---

## Time Estimate

| Task | Time |
|------|------|
| Setup browser/assets | 5 min |
| Record 7 screen clips | 15 min |
| Record talking head | 10 min |
| Import to Descript | 5 min |
| Assemble & sync | 20 min |
| Fine-tune & export | 10 min |
| **Total** | **~65 min** |

---

## Quick Start Commands

```bash
# Open all assets
cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/vuori-lead-magnet
open assets/messy-spreadsheet.html assets/stats-slide.html assets/dashboard-demo.html

# Create output folder for recordings
mkdir -p recordings

# After recording, your files go here:
# recordings/01-messy-spreadsheet.mov
# recordings/02-stats-slide.mov
# etc.
```

---

## Next Steps After Video Complete

1. Export from Descript
2. Upload to:
   - Instagram Reels
   - TikTok
   - LinkedIn
3. Send to Catherine Johnston at Vuori with personalized email
4. Track engagement metrics

---

**Created:** 2026-01-23
**Project:** Vuori Lead Magnet Video
**Tool:** Descript
