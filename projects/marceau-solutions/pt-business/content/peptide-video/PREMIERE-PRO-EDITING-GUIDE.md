# Peptide Video - Premiere Pro Editing Guide

**Created:** 2026-02-04
**Target Length:** 8-12 minutes (aim for ~10 min)
**Style:** Fast-paced educational with personality

---

## File Locations

```
Peptide-Video/
├── TalkingHeadRecording/    ← YOUR NEW FOOTAGE (use these!)
│   ├── Hook.mov
│   ├── Section1.mov
│   ├── Section2.mov
│   ├── Section3.mov
│   ├── Section4.mov
│   ├── Section5.mov
│   └── CallToAction.mov
│
├── B-Roll/                  ← B-ROLL CLIPS
│   ├── 01-gym-training.mp4
│   ├── 02-amino-acid.mp4
│   ├── 03-lab-scene.mp4
│   ├── 04-supplements.mp4
│   ├── 05-morning-routine.mp4
│   └── 06-decision-framework.mp4
│
├── Graphics/Static/         ← ALL GRAPHICS READY
│   ├── Lower Thirds (peptide names)
│   ├── Category Headers
│   ├── Infographics (spectrum, checklist, framework)
│   └── Stats
│
└── Output/                  ← EXPORT HERE
```

---

## Premiere Pro Project Setup

### Sequence Settings
```
Resolution: 1920x1080 (or 4K if footage supports)
Frame Rate: Match your footage (likely 30fps or 60fps)
Audio: 48kHz, Stereo
```

### Track Layout
```
V5: Text/Captions (animated text)
V4: Graphics/Infographics (full screen)
V3: Lower Thirds (peptide names)
V2: B-Roll
V1: Talking Head (main footage)
───────────────────────────────
A1: Voice (from talking head)
A2: B-Roll ambient (if any) - set to -18dB
A3: Background music - set to -20dB
```

---

# PHASE 1: CLEANUP PASS (15-20 min)

For each section, scrub through and remove mistake takes.

### How to Remove Mistakes:

1. **Play through the clip** - listen for pauses followed by restarts
2. **Mark the mistake start** - press `I` for in point just before the pause
3. **Mark the good take start** - press `O` for out point where the restart begins
4. **Ripple delete** - `Shift + Delete` to remove and close gap
5. **Repeat** for all mistakes in each section

### Cleanup Order:
- [ ] Hook.mov
- [ ] Section1.mov
- [ ] Section2.mov
- [ ] Section3.mov
- [ ] Section4.mov
- [ ] Section5.mov
- [ ] CallToAction.mov

---

# PHASE 2: ROUGH CUT ASSEMBLY

## Timeline Order

| # | Clip | Est. Duration | Notes |
|---|------|---------------|-------|
| 1 | Hook.mov | ~30-45 sec | Open strong |
| 2 | Section1.mov | ~2 min | What are peptides |
| 3 | Section2.mov | ~2.5 min | Categories (longest) |
| 4 | Section3.mov | ~2 min | Science vs hype |
| 5 | Section4.mov | ~2 min | What I've learned |
| 6 | Section5.mov | ~1.5 min | Decision framework |
| 7 | CallToAction.mov | ~30 sec | Subscribe + comment |

**Total Target: ~10-11 minutes**

---

# PHASE 3: B-ROLL INSERTION

**Rule:** Voice CONTINUES over B-roll. Only replace video, not audio.

### B-Roll Placement Map

| B-Roll | Insert During | What You're Saying | Duration |
|--------|---------------|-------------------|----------|
| **01-gym-training.mp4** | Section 1 | "...your body already makes thousands of these things naturally" | 8-12 sec |
| **02-amino-acid.mp4** | Section 1 | "...a peptide is just a chain of amino acids" | 8-10 sec |
| **03-lab-scene.mp4** | Section 3 | "The fitness industry has this tendency to take early-stage research..." | 10-15 sec |
| **04-supplements.mp4** | Section 4 | "Quality matters way more than most people realize..." | 8-12 sec |
| **05-morning-routine.mp4** | Section 4 | "Track everything. Blood work before and after..." | 10-12 sec |
| **06-decision-framework.mp4** | Section 5 | "Here's how I think about it..." | 8-12 sec |

### How to Insert B-Roll:

1. Find the timestamp in your talking head where you say the trigger phrase
2. Cut the talking head clip at that point (C for razor)
3. Drag B-roll to V2 (above talking head)
4. Trim B-roll to desired length
5. **Important:** Do NOT cut the audio - voice continues over B-roll
6. Add cross-dissolve transition (Ctrl+D) - 10-15 frames

---

# PHASE 4: LOWER THIRDS (Peptide Names)

Insert lower third graphics when you FIRST mention each peptide.

### Section 2 Lower Thirds (in order mentioned):

| Peptide | Graphic File | When to Show | Duration |
|---------|--------------|--------------|----------|
| Sermorelin | `lower_third_sermorelin.png` | "Sermorelin - this one was actually FDA approved..." | 4-5 sec |
| CJC-1295 | `lower_third_cjc_1295.png` | "CJC-1295 - extends how long..." | 4-5 sec |
| Ipamorelin | `lower_third_ipamorelin.png` | "Ipamorelin - this one mimics ghrelin..." | 4-5 sec |
| Tesamorelin | `lower_third_tesamorelin.png` | "Tesamorelin - and this is the only one..." | 4-5 sec |
| BPC-157 | `lower_third_bpc_157.png` | "BPC-157 - stands for Body Protection..." | 4-5 sec |
| TB-500 | `lower_third_tb_500.png` | "TB-500 - this is a fragment..." | 4-5 sec |
| GHRP-6 | `lower_third_ghrp_6.png` | "GHRP-6 - another growth hormone..." | 4-5 sec |
| MK-677 | `lower_third_mk_677.png` | "MK-677 - now technically this isn't..." | 4-5 sec |
| AOD-9604 | `lower_third_aod_9604.png` | "AOD-9604 - this is actually a fragment..." | 4-5 sec |
| Epithalon | `lower_third_epithalon.png` | "Epithalon - there's research on telomere..." | 4-5 sec |
| Semax | `lower_third_semax.png` | "Semax - studied for cognitive..." | 4-5 sec |
| Selank | `lower_third_selank.png` | "Selank - studied for anti-anxiety..." | 4-5 sec |

### Lower Third Placement:
- Position: Bottom left or bottom center
- Add fade in/out (10 frames)
- Track V3

---

# PHASE 5: CATEGORY HEADERS (Full Screen Flash)

These are bold category announcements that flash on screen.

| Header | Graphic File | When to Show | Duration |
|--------|--------------|--------------|----------|
| "GROWTH HORMONE SECRETAGOGUES" | `header_category_1.png` | "First up - Growth Hormone Secretagogues" | 1.5-2 sec |
| "HEALING & RECOVERY" | `header_category_2.png` | "Second category - Healing and Recovery" | 1.5-2 sec |
| "PERFORMANCE & BODY COMP" | `header_category_3.png` | "Third - Performance and Body Composition" | 1.5-2 sec |
| "COGNITIVE & LONGEVITY" | `header_category_4.png` | "And finally - Cognitive and Longevity" | 1.5-2 sec |

### Header Animation:
- Quick scale up from 90% to 100%
- Hold for 1.5 sec
- Cut back to talking head (no fade - punchy)
- Track V4

---

# PHASE 6: INFOGRAPHICS (Full Screen)

| Graphic | File | When to Show | Duration | Notes |
|---------|------|--------------|----------|-------|
| **Categories Summary** | `graphic_categories.png` | End of Section 2 | 5-7 sec | After listing all categories |
| **Spectrum (Proven→Hype)** | `graphic_spectrum.png` | Section 3 | 6-8 sec | After "proven/promising/hype" breakdown |
| **5 Key Learnings** | `graphic_checklist.png` | Section 4 | 6-8 sec | After listing all 5 points |
| **Decision Framework** | `graphic_framework.png` | Section 5 | 6-8 sec | After "consider if / hold off if" |
| **Disclaimer** | `disclaimer.png` | End of Section 2 | 3-4 sec | After FDA mention |

### Infographic Animation:
- Fade in (15 frames)
- Hold for duration
- Fade out (15 frames)
- Voice continues over graphic

---

# PHASE 7: VIRAL EDITING TACTICS

## 7A: Zoom Cuts (CRITICAL for engagement)

Add subtle zooms to emphasize key points:

| When to Zoom | Zoom Amount | What You're Saying |
|--------------|-------------|-------------------|
| Hook opener | 110% | "Peptides. Everybody in the fitness world is talking about them" |
| Key emphasis | 105-110% | "here's the thing" / "most people have no idea" |
| Each "Number one/two/three" | 108% | When listing the 5 learnings |
| "Red flag" moments | 115% | "If someone's telling you it's a miracle..." |
| CTA | 110% | "hit that subscribe button" |

### How to Add Zoom:
1. Cut clip at zoom point (C)
2. Select the segment after cut
3. Effect Controls → Scale → 105-115%
4. Optional: Add slight position adjustment to keep face centered

## 7B: Jump Cuts for Pacing

Even in clean takes, add strategic cuts to:
- Remove breaths longer than 0.5 sec
- Tighten transitions between sentences
- Create punchy rhythm

**Target pace:** Cut every 3-8 seconds (varies by energy)

## 7C: Text Pop-Ups (Animated)

Add kinetic text for key phrases (use Essential Graphics or After Effects):

| Text | When | Style |
|------|------|-------|
| "PEPTIDES" | 0:02 | Large, bold, center screen |
| "50 amino acids" | Section 1 | Pop up next to you |
| "NOT FDA APPROVED" | Section 2 | Red, warning style |
| "30+ YEARS" | Section 3 | Stats pop |
| "RED FLAG 🚩" | Section 3 | When mentioning miracles |
| "TRACK EVERYTHING" | Section 4 | Emphasis text |
| "SUBSCRIBE" | CTA | Animated button |

## 7D: Sound Design

Add subtle sound effects:
- **Whoosh** on zoom cuts
- **Pop** on text appearances
- **Ding** on graphic reveals
- Keep at -12dB (subtle, not distracting)

---

# PHASE 8: AUDIO

### Voice Levels
- Normalize to **-6dB to -3dB**
- Apply light compression (2:1 ratio, -18dB threshold)
- Add subtle EQ: slight boost at 3kHz for clarity

### Background Music
- Style: Lo-fi, chill electronic, or cinematic subtle
- Level: **-20dB to -18dB** (way under voice)
- Slightly louder during B-roll sections (-15dB)
- Fade out 3 sec before CTA

### Suggested Music Sources:
- Epidemic Sound
- Artlist
- YouTube Audio Library (free)

---

# PHASE 9: COLOR & FINAL POLISH

### Color Grade
- Match all clips (talking head should be consistent)
- Slight contrast boost (+10-15)
- Subtle saturation boost (+5-10)
- Skin tones: Keep natural, slight warmth

### B-Roll Color Match
- Adjust B-roll to match talking head temperature
- May need to cool down or warm up AI-generated B-roll

---

# PHASE 10: EXPORT SETTINGS

### YouTube Export (Main)
```
Format: H.264
Resolution: 1920x1080 (or 4K)
Frame Rate: Match source
Bitrate: VBR 2-pass
Target: 16 Mbps (1080p) or 45 Mbps (4K)
Audio: AAC, 320kbps, Stereo
```

### Instagram Reel Export (Section 3 only)
```
Format: H.264
Resolution: 1080x1920 (9:16 vertical)
Frame Rate: 30fps
Duration: 60 seconds max
Bitrate: 10-15 Mbps
```

---

# COMPLETE EDITING CHECKLIST

## Phase 1: Setup
- [ ] Create new Premiere project
- [ ] Import all footage to project
- [ ] Import all graphics
- [ ] Set up sequence with correct settings
- [ ] Create track layout (V1-V5, A1-A3)

## Phase 2: Cleanup
- [ ] Remove mistakes from Hook.mov
- [ ] Remove mistakes from Section1.mov
- [ ] Remove mistakes from Section2.mov
- [ ] Remove mistakes from Section3.mov
- [ ] Remove mistakes from Section4.mov
- [ ] Remove mistakes from Section5.mov
- [ ] Remove mistakes from CallToAction.mov

## Phase 3: Assembly
- [ ] Arrange all sections in order on V1
- [ ] Verify flow and transitions

## Phase 4: B-Roll
- [ ] Insert 01-gym-training.mp4 in Section 1
- [ ] Insert 02-amino-acid.mp4 in Section 1
- [ ] Insert 03-lab-scene.mp4 in Section 3
- [ ] Insert 04-supplements.mp4 in Section 4
- [ ] Insert 05-morning-routine.mp4 in Section 4
- [ ] Insert 06-decision-framework.mp4 in Section 5

## Phase 5: Lower Thirds
- [ ] Add all 12 peptide name lower thirds in Section 2
- [ ] Add fade in/out to each

## Phase 6: Category Headers
- [ ] Add 4 category headers in Section 2
- [ ] Add scale animation

## Phase 7: Infographics
- [ ] Add categories summary (end Section 2)
- [ ] Add spectrum graphic (Section 3)
- [ ] Add checklist graphic (Section 4)
- [ ] Add framework graphic (Section 5)
- [ ] Add disclaimer (Section 2)

## Phase 8: Viral Edits
- [ ] Add zoom cuts on key moments (10-15 throughout)
- [ ] Tighten pacing with jump cuts
- [ ] Add text pop-ups for key phrases
- [ ] Add subtle sound effects

## Phase 9: Audio
- [ ] Normalize voice levels
- [ ] Add background music
- [ ] Set music levels (-20dB)
- [ ] Add whoosh/pop sound effects

## Phase 10: Color & Export
- [ ] Color grade talking head
- [ ] Match B-roll color
- [ ] Final review playthrough
- [ ] Export YouTube version
- [ ] Export Instagram Reel (Section 3)

---

# INSTAGRAM REEL: Quick Edit

For the 60-sec reel, just use **Section 3 (Science vs Hype)**:

1. **Crop to vertical** - Use auto-reframe or manual crop
2. **Add captions** - Use Premiere's auto-caption or CapCut
3. **Keep the hook** - First 3 seconds are critical
4. **Add CTA at end** - "Full breakdown link in bio"

Export at 1080x1920, 30fps, under 60 seconds.

---

# TIME ESTIMATES

| Phase | Time |
|-------|------|
| Setup & Import | 10 min |
| Cleanup (mistakes) | 20-30 min |
| Assembly | 10 min |
| B-Roll insertion | 15 min |
| Lower thirds & headers | 20 min |
| Infographics | 10 min |
| Viral edits (zooms, text) | 30-45 min |
| Audio & music | 15 min |
| Color & polish | 15 min |
| Export | 10 min |
| **TOTAL** | **~2.5-3 hours** |

---

# PRO TIPS FOR VIRALITY

1. **First 3 seconds are everything** - Hook must grab immediately
2. **Pattern interrupt every 5-8 sec** - Zoom, B-roll, graphic, text
3. **Face on screen 70%+ of time** - People connect with faces
4. **Fast pace > slow pace** - Cut the fat, keep it moving
5. **End with clear CTA** - Tell them exactly what to do
6. **Captions = 40% more watch time** - Add them for YouTube too

---

**Ready to edit! Start with Phase 1 (Setup) and work through sequentially.**
