# Grok Imagine B-Roll Generation Guide

**Created:** 2026-02-02
**Tool:** Grok Imagine (xAI)
**Script:** `/execution/grok_video_gen.py`

---

## Quick Start

```bash
# Generate a single B-roll clip
cd /Users/williammarceaujr./dev-sandbox
python execution/grok_video_gen.py \
    --prompt "Athletic male torso doing deadlift in modern gym, documentary style" \
    --duration 15 \
    --aspect-ratio 16:9 \
    --output projects/marceau-solutions/fitness-influencer/content/Peptide-Video/B-Roll/gym-training.mp4
```

---

## Grok Imagine Prompting Best Practices

### Structure Your Prompts

Grok Imagine follows structured prompts better than vague ones. Use this format:

```
[SUBJECT] + [ACTION] + [SETTING] + [CAMERA/STYLE] + [LIGHTING] + [MOOD]
```

### Key Elements to Include

| Element | Why It Matters | Example |
|---------|----------------|---------|
| **Subject** | Who/what is in frame | "Athletic male torso (no face)" |
| **Action** | What's happening | "performing controlled deadlift" |
| **Setting** | Environment details | "modern commercial gym, rubber flooring, squat rack" |
| **Camera** | Shot type & movement | "medium shot, slight tripod movement, follows motion" |
| **Lighting** | Light quality | "natural window light mixed with overhead fluorescents" |
| **Style** | Visual aesthetic | "documentary fitness content, raw authentic feel" |

### What Grok Imagine Does Well

✅ Realistic human motion and physics
✅ Consistent lighting throughout clip
✅ Natural camera movements
✅ Synchronized ambient audio
✅ Documentary/authentic aesthetic

### What to Avoid

❌ Faces (can be inconsistent)
❌ Text/graphics in the video (add in post)
❌ Complex multi-character scenes
❌ Specific brand logos or products

---

## Your 6 B-Roll Prompts (Optimized for Grok Imagine)

### B-Roll #1: Gym Training
**Duration:** 15 seconds | **Insert:** Section 1 (0:30)

```
Documentary fitness B-roll: Athletic male torso in black compression shirt performing
controlled deadlift. Modern commercial gym with rubber flooring, weight plates, mirrors
in background. Camera at torso level, medium shot, subtle tripod movement following
the lift. Natural window light mixed with overhead gym fluorescents, high key lighting.
Raw authentic training footage aesthetic, no filters. Ambient gym sounds - distant
weight clinks, soft HVAC hum.
```

### B-Roll #2: Amino Acid Animation
**Duration:** 12 seconds | **Insert:** Section 1 (0:45)

```
Scientific visualization: 3D molecular model of peptide chain floating in dark navy
space with subtle grid lines. Ball-and-stick representation with glossy spheres -
carbon gray, oxygen red, nitrogen blue, hydrogen white. Camera slowly orbits the
molecule, gentle zoom into peptide bond connection. Soft key light from above-left,
subtle glow on molecular bonds. Clean educational aesthetic, modern science documentary
style. Soft ambient electronic tone.
```

### B-Roll #3: Research Lab Scene
**Duration:** 15 seconds | **Insert:** Section 3 (5:00)

```
Clinical research footage: Close-up of hands in blue nitrile gloves holding small
glass vial with clear liquid. Modern laboratory bench with white surface, beakers,
pipette rack visible. Camera slightly above bench level, 30-degree angle, shallow
depth of field. Cool blue-white clinical lighting, overhead fluorescents. Hand picks
up vial, rotates to catch light, returns to rack. Quiet lab ambience, soft equipment
hum. Professional documentary style, trustworthy scientific aesthetic.
```

### B-Roll #4: Supplement Organization
**Duration:** 12 seconds | **Insert:** Section 4 (7:15)

```
Lifestyle content: Organized supplement shelf in modern home bathroom. Various bottles
and containers neatly arranged on white shelving. Camera at eye level, static shot.
Soft natural window light from left side, warm tones. Male hand enters frame from
right, fingers trace along bottles selecting one, picks up and exits frame. Quiet
home ambience. Clean minimal aesthetic, authentic but aspirational lifestyle footage.
```

### B-Roll #5: Morning Routine
**Duration:** 15 seconds | **Insert:** Section 4 (7:45)

```
Morning lifestyle footage: Bedroom nightstand with glass water bottle, small supplement
container, smartphone showing health app. Soft golden morning light through sheer
curtains. Camera at bed-level perspective, subtle handheld micro-movement. Male hand
reaches for water bottle, opens supplement container, tips capsules into palm. Warm
cozy tones, soft contrast. Quiet morning ambience with distant birds. Authentic
intentional living aesthetic.
```

### B-Roll #6: Decision Framework (Motion Graphic Style)
**Duration:** 12 seconds | **Insert:** Section 5 (9:15)

```
Clean motion graphic: Dark navy gradient background. Two-column comparison framework
animating in. Left column with green accent header "CONSIDER IT IF" with bullet points
fading in sequentially. Right column with amber accent header "HOLD OFF IF" with
bullets animating in. Modern sans-serif typography, white text. Elements slide and
fade smoothly. Subtle whoosh sounds on appearances. Professional infographic style,
empowering and clear.
```

---

## Generation Workflow

### Option A: Command Line (One at a Time)

```bash
# Create output folder
mkdir -p projects/marceau-solutions/fitness-influencer/content/Peptide-Video/B-Roll

# Generate each clip
python execution/grok_video_gen.py \
    --prompt "YOUR PROMPT HERE" \
    --duration 15 \
    --output projects/marceau-solutions/fitness-influencer/content/Peptide-Video/B-Roll/01-gym-training.mp4
```

### Option B: Batch Script

```bash
#!/bin/bash
# generate_broll.sh

OUTPUT_DIR="projects/marceau-solutions/fitness-influencer/content/Peptide-Video/B-Roll"
mkdir -p "$OUTPUT_DIR"

# B-Roll 1
python execution/grok_video_gen.py \
    --prompt "Documentary fitness B-roll: Athletic male torso in black compression shirt performing controlled deadlift..." \
    --duration 15 \
    --output "$OUTPUT_DIR/01-gym-training.mp4"

# B-Roll 2
python execution/grok_video_gen.py \
    --prompt "Scientific visualization: 3D molecular model of peptide chain..." \
    --duration 12 \
    --output "$OUTPUT_DIR/02-amino-acid.mp4"

# ... continue for all 6
```

### Option C: n8n Workflow (Recommended)

Use Google Sheet for prompts + n8n for orchestration:
- Sheet columns: clip_name, prompt, duration, status, output_url
- n8n triggers on new rows or manual trigger
- Calls Grok API, saves outputs, updates sheet

---

## Cost Estimate

| Clip | Duration | Est. Cost |
|------|----------|-----------|
| #1 Gym Training | 15s | ~$0.30 |
| #2 Amino Acid | 12s | ~$0.24 |
| #3 Lab Scene | 15s | ~$0.30 |
| #4 Supplements | 12s | ~$0.24 |
| #5 Morning | 15s | ~$0.30 |
| #6 Framework | 12s | ~$0.24 |
| **TOTAL** | **81s** | **~$1.62** |

*Much cheaper than Sora 2 subscription*

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Grainy output | Add "high quality, sharp detail" to prompt |
| Wrong aspect ratio | Explicitly set `--aspect-ratio 16:9` |
| Motion too fast | Add "slow, controlled movement" to prompt |
| Lighting inconsistent | Be specific about light source and quality |
| Audio doesn't match | Describe ambient sounds in prompt |

---

## Post-Generation Checklist

- [ ] Review each clip for quality
- [ ] Check duration matches script timing
- [ ] Verify no faces visible (as intended)
- [ ] Color grade to match talking head footage
- [ ] Adjust audio levels in editor
