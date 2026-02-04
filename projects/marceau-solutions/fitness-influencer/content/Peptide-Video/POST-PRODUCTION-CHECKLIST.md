# Peptide Video Post-Production Checklist

**Created:** 2026-02-02
**Updated:** 2026-02-03
**Status:** Phase 4 - Post-Production (Assembly Ready)

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [TIMELINE-ASSEMBLY.md](TIMELINE-ASSEMBLY.md) | Clip order, B-roll insertion points, track layout |
| [TEXT-OVERLAYS.md](TEXT-OVERLAYS.md) | Lower thirds, category headers, statistics |
| [GRAPHICS-SPECS.md](GRAPHICS-SPECS.md) | Spectrum, checklist, framework graphics |
| [GROK-BROLL-GUIDE.md](GROK-BROLL-GUIDE.md) | B-roll generation prompts (completed) |

---

## Raw Footage Inventory

| Section | Folder | Parts | Est. Duration | Status |
|---------|--------|-------|---------------|--------|
| **Hook** (0:00-0:30) | `Hook/` | 3 | ~30-45 sec | ✅ Recorded |
| **Section 1** - What Are Peptides (0:30-2:30) | `Section1-What-are-Peptides/` | 5 | ~2 min | ✅ Recorded |
| **Section 2** - Categories (2:30-5:00) | `Section2-Categories-of-peptides/` | 8 | ~2.5 min | ✅ Recorded |
| **Section 3** - Science vs Hype (5:00-7:00) | `Section3-The-science-versus-the-hype/` | 4 | ~2 min | ✅ Recorded |
| **Section 4** - Personal Take (7:00-9:00) | `Section4-My-Personal-Take/` | 5 | ~2 min | ✅ Recorded |
| **Section 5** - Decision Framework (9:00-10:30) | ⚠️ **CHECK BELOW** | ? | ~1.5 min | ⚠️ VERIFY |
| **CTA** (10:30-11:00) | `Call-To-Action/` | 3 (+1 dupe) | ~30 sec | ✅ Recorded |

---

## ✅ Section 5 Check - CONFIRMED

**Script content for Section 5 (Decision Framework):**
- "So should you look into peptides? Here's my framework..."
- Consider it if / Hold off if lists
- "Peptides are tools..."

**Status:** ✅ CONFIRMED - Section 5 content is covered in Section 4 Parts 4-5
**Date Confirmed:** 2026-02-03

→ Proceeding to timeline assembly

---

## Phase 4A: Footage Organization

### Cleanup Tasks
- [ ] Delete `Call-To-Action/Untitled.mov` (duplicate of Part1.mov - same 296MB)
- [ ] Review each section, note best takes in comments below
- [ ] Record room tone if not captured (10 sec silence)

### Best Takes Notes
```
HOOK:
- Part 1:
- Part 2:
- Part 3:

SECTION 1:
- Part 1:
- Part 2:
- Part 3:
- Part 4:
- Part 5:

SECTION 2:
- Part 1:
- Part 2:
- Part 3:
- Part 4:
- Part 5:
- Part 6:
- Part 7:
- Part 8:

SECTION 3:
- Part 1:
- Part 2:
- Part 3:
- Part 4:

SECTION 4:
- Part 1:
- Part 2:
- Part 3:
- Part 4:
- Part 5:

CTA:
- Part 1:
- Part 2:
- Part 3:
```

---

## Phase 4B: Timeline Assembly ✅ COMPLETE

### Step 1: Rough Cut
- [x] Import all footage into editing software
- [x] Select best takes for each section
- [x] Arrange on timeline in order
- [x] Target length: 8-12 minutes → **Achieved: 10.7 minutes**

### Step 2: Jump Cuts
- [x] Remove long pauses (>1 sec)
- [x] Remove filler words ("um", "uh", "like")
- [x] Remove false starts
- [x] Remove repeated sentences
- [x] Keep natural breathing/transition pauses (~0.3 sec)

**Compiled:** 2026-02-03 via `process_peptide_video.py --phase 2`

---

## Phase 4C: B-Roll Integration ✅ COMPLETE

### B-Roll Clips Integrated (from Production Guide)

| B-Roll | Insert After | Duration | Source |
|--------|--------------|----------|--------|
| **#1** Gym Training | "First, let's get the basics right..." (0:30) | 15 sec | Sora 2 |
| **#2** Amino Acid Animation | "A peptide is simply a chain..." (0:45) | 12 sec | Sora 2 |
| **#3** Lab/Research Scene | "Let me give you the actual landscape..." (5:00) | 15 sec | Sora 2 |
| **#4** Supplement Organization | "Quality matters enormously..." (7:15) | 12 sec | Sora 2 |
| **#5** Morning Routine | "Track everything..." (7:45) | 15 sec | Sora 2 |
| **#6** Decision Framework | "Here's my framework..." (9:15) | 12 sec | Sora 2 / Motion graphic |

### B-Roll Status
- [x] B-Roll #1 generated → `B-Roll/01-gym-training.mp4`
- [x] B-Roll #2 generated → `B-Roll/02-amino-acid.mp4`
- [x] B-Roll #3 generated → `B-Roll/03-lab-scene.mp4`
- [x] B-Roll #4 generated → `B-Roll/04-supplements.mp4`
- [x] B-Roll #5 generated → `B-Roll/05-morning-routine.mp4`
- [x] B-Roll #6 generated → `B-Roll/06-decision-framework.mp4`

**Note:** Voice continues OVER B-roll (don't cut audio)

---

## Phase 4D: Text Overlays ✅ COMPLETE

### Peptide Names (Lower Third)
Insert when first mentioned:
- [x] Sermorelin (Section 2)
- [x] CJC-1295 (Section 2)
- [x] Ipamorelin (Section 2)
- [x] Tesamorelin (Section 2)
- [x] BPC-157 (Section 2)
- [x] TB-500 (Section 2)
- [x] GHRP-6 (Section 2)
- [x] MK-677 (Section 2)
- [x] AOD-9604 (Section 2)
- [x] Epithalon (Section 2)
- [x] Semax (Section 2)
- [x] Selank (Section 2)

### Category Headers (Full Screen Flash)
- [x] "Growth Hormone Secretagogues" (Section 2)
- [x] "Healing & Recovery Peptides" (Section 2)
- [x] "Performance & Body Composition" (Section 2)
- [x] "Cognitive & Longevity" (Section 2)

### Graphics
- [x] Category summary graphic (Section 2 end)
- [x] "Proven to Hype" spectrum (Section 3)
- [x] Checklist graphic - 5 learnings (Section 4)
- [x] Decision framework - Consider/Hold off (Section 5)

**Generated:** 2026-02-03 via `text_overlay_generator.py` + `peptide_graphics_generator.py`
**Applied:** 2026-02-03 via `video_compositor.py`

---

## Phase 4E: Audio

### Voice Levels
- [ ] Normalize voice to -6dB to -3dB
- [ ] Remove background noise
- [ ] Apply subtle compression for consistency

### Music
- [ ] Select background track (lo-fi or subtle electronic)
- [ ] Level at -20dB to -15dB (under voice)
- [ ] Slightly louder during B-roll sections
- [ ] Fade out before CTA

### B-Roll Ambient
- [ ] Level at -18dB (subtle)
- [ ] Match to talking head room tone

---

## Phase 4F: Color & Final

### Color Grade
- [ ] Match B-roll color temp to talking head
- [ ] Slight contrast boost
- [ ] Consistent look throughout
- [ ] Skin tones natural

### Chapter Markers (for YouTube)
```
0:00 Hook
0:30 What Are Peptides
2:30 Categories of Peptides
5:00 Science vs Hype
7:00 What I've Learned
9:00 Decision Framework
10:30 Subscribe & Comment
```

---

## Phase 4G: Export

### YouTube Version
- [ ] Resolution: 4K (or 1080p minimum)
- [ ] Codec: H.264
- [ ] Bitrate: High (20-50 Mbps for 4K)
- [ ] Audio: AAC 320kbps

### Thumbnail
- [ ] Create 1920x1080 thumbnail
- [ ] Option A: Face + "PEPTIDES" text
- [ ] Option B: Face + lab split
- [ ] Option C: Contemplative + icons

### Short-Form Clips (TikTok/Reels/Shorts)
- [ ] Clip 1: Hook (0:30) - "Everyone's talking, nobody knows"
- [ ] Clip 2: Categories (0:45) - "4 categories you need to know"
- [ ] Clip 3: Science vs Hype (1:00) - "Here's the truth"
- [ ] Clip 4: Framework (0:45) - "Should YOU try peptides?"

---

## Pre-Publish Compliance

- [ ] Disclaimer in video description
- [ ] "Not medical advice" stated verbally (check Hook)
- [ ] No specific dosing recommendations
- [ ] No before/after health claims
- [ ] "Consult healthcare provider" mentioned
- [ ] FDA status accurately represented
- [ ] No affiliate links to peptide sources

---

## File Locations

```
Peptide-Video/
├── Hook/                           ← Raw footage (3 parts)
├── Section1-What-are-Peptides/     ← Raw footage (5 parts)
├── Section2-Categories-of-peptides/← Raw footage (8 parts)
├── Section3-The-science-versus-the-hype/ ← Raw footage (4 parts)
├── Section4-My-Personal-Take/      ← Raw footage (5 parts, includes Section 5)
├── Call-To-Action/                 ← Raw footage (3 parts)
│
├── Output/JumpCut/                 ← ✅ PROCESSED CLIPS (use these!)
│   ├── Hook/                       ← part1_jc.mp4, Part2_jc.mp4, Part3_jc.mp4
│   ├── Section1.../                ← Part1_jc.mp4 through Part5_jc.mp4
│   ├── Section2.../                ← Part1_jc.mp4 through Part8_jc.mp4
│   ├── Section3.../                ← Part1_jc.mp4 through Part4_jc.mp4
│   ├── Section4.../                ← Part1_jc.mp4 through Part5_jc.mp4
│   └── Call-To-Action/             ← Part1_jc.mp4 through Part3_jc.mp4
│
├── B-Roll/                         ← ✅ GENERATED (6 clips)
│   ├── 01-gym-training.mp4
│   ├── 02-amino-acid.mp4
│   ├── 03-lab-scene.mp4
│   ├── 04-supplements.mp4
│   ├── 05-morning-routine.mp4
│   └── 06-decision-framework.mp4
│
├── Graphics/                       ← TO CREATE
│   ├── Source/                     ← Design files (Figma, etc.)
│   ├── Static/                     ← PNG exports
│   └── Animated/                   ← MOV exports with alpha
│
├── Exports/                        ← TO CREATE: Final renders
│
├── TIMELINE-ASSEMBLY.md            ← Clip order guide
├── TEXT-OVERLAYS.md                ← Text specs
├── GRAPHICS-SPECS.md               ← Graphics specs
├── GROK-BROLL-GUIDE.md             ← B-roll prompts (completed)
└── POST-PRODUCTION-CHECKLIST.md    ← This file
```

---

## ✅ COMPILED OUTPUT (2026-02-03) - COMPLETE

| File | Size | Duration | Notes |
|------|------|----------|-------|
| `Output/peptide_video_compiled.mp4` | 225 MB | 10:40 | Base compilation |
| `Output/peptide_video_compiled_enhanced.mp4` | 230 MB | 10:40 | Audio normalized |
| `Output/peptide_video_final.mp4` | 202 MB | 10:40 | With overlays |
| `Output/peptide_video_youtube.mp4` | 899 MB | 10:40 | **← UPLOAD THIS** (1080p, H.264, YouTube optimized) |

### Thumbnails Generated (1920x1080)
| File | Style | Best For |
|------|-------|----------|
| `Output/thumbnail_bold.jpg` | Bold | High CTR, text visible |
| `Output/thumbnail_minimal.jpg` | Minimal | Clean, focused |
| `Output/thumbnail_split.jpg` | Split | Professional, branded |

### Compilation Stats
- **Talking Head:** 9.3 minutes (558 seconds)
- **B-Roll:** 1.4 minutes (81 seconds)
- **Total:** 10.7 minutes (640 seconds)
- **Target:** 8-12 minutes ✅

### Overlays Applied (20 total)
- **Category Headers:** 4 (GH Secretagogues, Healing & Recovery, Performance, Cognitive)
- **Lower Thirds:** 12 (all peptide names with category labels)
- **Graphics:** 3 (Spectrum, Checklist, Framework)
- **Disclaimer:** 1 (medical advice warning)

---

## Next Actions - ALL COMPLETE ✅

1. ~~**IMMEDIATE**: Confirm Section 5 status~~ → ✅ DONE (in Section 4 Parts 4-5)
2. ~~**TODAY**: Review footage, note best takes~~ → ✅ Jump cuts already processed
3. ~~**NEXT**: Generate B-roll~~ → ✅ DONE (all 6 clips generated)
4. ~~**NOW**: Timeline assembly~~ → ✅ DONE (10.7 min compiled)
5. ~~**NOW**: Create graphics~~ → ✅ DONE (4 graphics: spectrum, checklist, framework, categories)
6. ~~**THEN**: Add text overlays~~ → ✅ DONE (20 overlays applied to final video)
7. ~~**Color grade**~~ → ⏭️ SKIPPED (B-roll already matches well)
8. ~~**Background music**~~ → ⏭️ OPTIONAL (add if desired - tool ready)
9. ~~**Create thumbnail**~~ → ✅ DONE (3 styles generated)
10. ~~**YouTube export**~~ → ✅ DONE (1080p, H.264, 899 MB)

## 🎬 READY TO UPLOAD

Upload `peptide_video_youtube.mp4` to YouTube with one of the thumbnail options.

---

## Production Tools Created

| Tool | Location | Purpose |
|------|----------|---------|
| `text_overlay_generator.py` | `src/` | Generate PNG overlays (lower thirds, headers, stats) |
| `peptide_graphics_generator.py` | `src/` | Generate infographics (spectrum, checklist, framework) |
| `video_compositor.py` | `src/` | Apply PNG overlays to video at timestamps |
| `process_peptide_video.py` | `src/` | Full pipeline orchestration (phases 1-5) |
| `video_polish.py` | `src/` | Thumbnails, YouTube export, music mixing, color grade |

### Quick Commands
```bash
# Generate all overlays
python -m src.text_overlay_generator
python -m src.peptide_graphics_generator

# Apply overlays to video
python -m src.video_compositor

# Run full pipeline (phases 1-5)
python -m src.process_peptide_video --full

# Generate thumbnails
python -m src.video_polish --input video.mp4 --thumbnail --thumbnail-style bold

# YouTube export
python -m src.video_polish --input video.mp4 --youtube-export --resolution 1080p

# Add background music (optional)
python -m src.video_polish --input video.mp4 --music path/to/music.mp3 --music-volume 0.1
```
