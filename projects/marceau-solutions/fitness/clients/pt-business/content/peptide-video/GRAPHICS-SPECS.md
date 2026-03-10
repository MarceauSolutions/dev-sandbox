# Peptide Video - Graphics Specifications

**Created:** 2026-02-03
**Format:** 3840x2160 (4K) or 1920x1080 (1080p)
**Style:** Clean, modern infographic aesthetic

---

## Design System (Shared with Text Overlays)

### Colors
```
Background:      #0f172a (dark navy)
Primary Text:    #ffffff (white)
Green:           #22c55e (proven/positive)
Amber:           #f59e0b (caution/promising)
Red:             #ef4444 (hype/negative)
Blue:            #3b82f6 (scientific/neutral)
Purple:          #8b5cf6 (cognitive category)
Gray:            #64748b (secondary text)
```

### Typography
```
Headers:         Inter Black, 72-96px
Body:            Inter Bold, 36-48px
Labels:          Inter Medium, 24-32px
```

---

## GRAPHIC #1: Science vs Hype Spectrum

**Insert Point:** Section 3 (Science vs Hype), ~6:00
**Duration:** 6-8 seconds on screen
**Purpose:** Visualize the evidence spectrum from proven to hype

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                    PEPTIDE EVIDENCE SPECTRUM                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ PROVEN        │    PROMISING     │      MOSTLY HYPE      │   │
│  │   ████████    │     ████████     │       ████████        │   │
│  │   (Green)     │     (Amber)      │       (Red)           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  • Tesamorelin     • BPC-157           • "Miracle" claims       │
│  • Sermorelin*     • TB-500            • Extreme fat loss       │
│  • GHRP family     • Most healing      • "No side effects"      │
│  • Insulin           peptides          • Quick fixes            │
│                                                                  │
│  *Was FDA approved                                               │
│   1997-2008                                                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Specifications

| Element | Details |
|---------|---------|
| **Title** | "PEPTIDE EVIDENCE SPECTRUM" - Inter Black, 72px, white |
| **Spectrum Bar** | 1200px wide x 60px tall, rounded corners 30px |
| **Gradient** | Left to right: #22c55e → #f59e0b → #ef4444 |
| **Section Labels** | Inter Bold, 32px, centered above each third |
| **Bullet Points** | Inter Medium, 28px, white, aligned under each section |
| **Footnote** | Inter Regular, 20px, gray (#94a3b8) |

### Animation Sequence (if animated)

```
0.0s - Background fades in
0.3s - Title animates in (fade + slide down)
0.6s - Spectrum bar animates in (expand from center)
0.9s - "PROVEN" label + bullets fade in
1.2s - "PROMISING" label + bullets fade in
1.5s - "MOSTLY HYPE" label + bullets fade in
1.8s - Footnote fades in
2.0s - Hold for 4-6 seconds
```

### Export Files
- `spectrum-static.png` - Static version for quick use
- `spectrum-animated.mov` - Animated version with alpha

---

## GRAPHIC #2: 5 Key Learnings Checklist

**Insert Point:** Section 4 (What I've Learned), ~8:00
**Duration:** 8-10 seconds on screen
**Purpose:** Summarize the 5 key takeaways

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                   WHAT I'VE LEARNED                              │
│                                                                  │
│     ┌────────────────────────────────────────────────────────┐  │
│     │                                                        │  │
│     │  ✓  Do your own research                              │  │
│     │                                                        │  │
│     │  ✓  Work with a healthcare provider                   │  │
│     │                                                        │  │
│     │  ✓  Quality matters enormously                        │  │
│     │                                                        │  │
│     │  ✓  Start conservative                                │  │
│     │                                                        │  │
│     │  ✓  Track everything                                  │  │
│     │                                                        │  │
│     └────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Specifications

| Element | Details |
|---------|---------|
| **Title** | "WHAT I'VE LEARNED" - Inter Black, 64px, white |
| **Container** | Dark card (#1e293b), rounded 16px, subtle border |
| **Checkmark** | Circle icon, green (#22c55e), 32px |
| **List Items** | Inter Bold, 36px, white |
| **Spacing** | 48px between items |
| **Padding** | 48px all sides |

### The 5 Items

1. ✓ Do your own research
2. ✓ Work with a healthcare provider
3. ✓ Quality matters enormously
4. ✓ Start conservative
5. ✓ Track everything

### Animation Sequence (if animated)

```
0.0s - Background + container fades in
0.3s - Title animates in
0.6s - Item 1: Checkmark bounces in, text fades in
0.9s - Item 2: Checkmark bounces in, text fades in
1.2s - Item 3: Checkmark bounces in, text fades in
1.5s - Item 4: Checkmark bounces in, text fades in
1.8s - Item 5: Checkmark bounces in, text fades in
2.2s - Hold for 6-8 seconds
```

### Export Files
- `checklist-static.png` - Static version
- `checklist-animated.mov` - Animated version with alpha

---

## GRAPHIC #3: Decision Framework

**Insert Point:** Section 5 (Decision Framework), ~9:15
**Duration:** 10-12 seconds on screen
**Purpose:** Two-column comparison to help viewer decide

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                    DECISION FRAMEWORK                            │
│                                                                  │
│   ┌────────────────────────┐    ┌────────────────────────┐      │
│   │    CONSIDER IT IF      │    │     HOLD OFF IF        │      │
│   │    ═══════════════     │    │    ═══════════════     │      │
│   │    (Green header)      │    │    (Amber header)      │      │
│   │                        │    │                        │      │
│   │ ✓ Maxed out basics     │    │ ✗ Under 25 years old   │      │
│   │   (training/nutrition/ │    │                        │      │
│   │   sleep)               │    │ ✗ Haven't dialed in    │      │
│   │                        │    │   the basics           │      │
│   │ ✓ Specific issue       │    │                        │      │
│   │   (injury recovery)    │    │ ✗ Looking for a        │      │
│   │                        │    │   shortcut             │      │
│   │ ✓ Can afford medical   │    │                        │      │
│   │   supervision          │    │ ✗ Can't afford quality │      │
│   │                        │    │   products + monitoring│      │
│   │ ✓ Willing to do        │    │                        │      │
│   │   blood work           │    │                        │      │
│   └────────────────────────┘    └────────────────────────┘      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Specifications

| Element | Details |
|---------|---------|
| **Title** | "DECISION FRAMEWORK" - Inter Black, 64px, white, centered |
| **Left Column Header** | "CONSIDER IT IF" - Inter Bold, 40px, green (#22c55e) |
| **Right Column Header** | "HOLD OFF IF" - Inter Bold, 40px, amber (#f59e0b) |
| **Underline** | 3px thick, matches header color, 80% width |
| **Cards** | Dark card (#1e293b), rounded 16px |
| **Card Border** | 2px left border in column color |
| **Checkmarks (left)** | Green circles with white check |
| **X marks (right)** | Amber circles with white X |
| **List Items** | Inter Medium, 28px, white |
| **Item Spacing** | 32px between items |

### Content

**CONSIDER IT IF:**
- ✓ Maxed out training, nutrition, and sleep
- ✓ Specific issue (injury recovery, etc.)
- ✓ Can afford proper medical supervision
- ✓ Willing to do blood work

**HOLD OFF IF:**
- ✗ Under 25 years old
- ✗ Haven't dialed in the basics
- ✗ Looking for a shortcut
- ✗ Can't afford quality products and monitoring

### Animation Sequence (if animated)

```
0.0s - Background fades in
0.3s - Title animates in (fade + slide down)
0.6s - Left column header slides in from left
0.8s - Right column header slides in from right
1.0s - Left item 1 fades in
1.2s - Right item 1 fades in
1.4s - Left item 2 fades in
1.6s - Right item 2 fades in
1.8s - Left item 3 fades in
2.0s - Right item 3 fades in
2.2s - Left item 4 fades in
2.4s - Right item 4 fades in
2.6s - Hold for 7-9 seconds
```

### Export Files
- `framework-static.png` - Static version
- `framework-animated.mov` - Animated version with alpha

---

## GRAPHIC #4: Category Summary (Optional)

**Insert Point:** End of Section 2, ~5:00
**Duration:** 5-7 seconds
**Purpose:** Quick visual recap of all 4 categories

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                    THE 4 CATEGORIES                              │
│                                                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────┐ │
│   │     GH       │  │   HEALING    │  │ PERFORMANCE  │  │COGNI│ │
│   │SECRETAGOGUES │  │  & RECOVERY  │  │  & BODY COMP │  │TIVE │ │
│   │    (Blue)    │  │   (Green)    │  │   (Amber)    │  │(Purp│ │
│   │              │  │              │  │              │  │le)  │ │
│   │ Sermorelin   │  │  BPC-157     │  │   GHRP-6     │  │Epith│ │
│   │ CJC-1295     │  │  TB-500      │  │   MK-677     │  │Semax│ │
│   │ Ipamorelin   │  │              │  │   AOD-9604   │  │Selan│ │
│   │ Tesamorelin  │  │              │  │              │  │k    │ │
│   └──────────────┘  └──────────────┘  └──────────────┘  └─────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Export Files
- `categories-summary-static.png`
- `categories-summary-animated.mov`

---

## File Organization

```
Peptide-Video/
├── Graphics/
│   ├── Source/                    ← Design files
│   │   ├── spectrum.fig           (Figma)
│   │   ├── checklist.fig
│   │   ├── framework.fig
│   │   └── categories.fig
│   │
│   ├── Static/                    ← PNG exports
│   │   ├── spectrum-static.png
│   │   ├── checklist-static.png
│   │   ├── framework-static.png
│   │   └── categories-static.png
│   │
│   └── Animated/                  ← MOV exports (with alpha)
│       ├── spectrum-animated.mov
│       ├── checklist-animated.mov
│       ├── framework-animated.mov
│       └── categories-animated.mov
```

---

## Production Notes

### Creating in Figma
1. Create frame at 3840x2160 (4K)
2. Use Auto Layout for consistent spacing
3. Export PNG at 2x for 4K, 1x for 1080p
4. Use plugins like "Motion" for basic animations

### Creating in After Effects
1. Composition: 3840x2160, 30fps
2. Use Essential Graphics for reusability
3. Export: Apple ProRes 4444 with alpha
4. Or: PNG sequence for flexibility

### Creating in Canva
1. Custom dimensions: 3840x2160
2. Use brand kit for consistent colors
3. Export as PNG (static) or MP4 (animated)
4. Note: MP4 won't have alpha - use on dark background

### Creating in DaVinci Resolve Fusion
1. Create compound clip at timeline resolution
2. Use Text+ for typography
3. Animate with keyframes
4. Render with alpha if needed

---

## Quick Creation Option: AI Image Generation

If you need quick static graphics, use this prompt structure for AI image generators:

```
Professional infographic design, dark navy background (#0f172a),
clean modern typography, [SPECIFIC CONTENT], minimalist style,
high contrast white text, accent colors green and amber,
4K resolution, no watermarks, suitable for YouTube video overlay
```

Example for spectrum graphic:
```
Professional infographic showing evidence spectrum for peptides,
dark navy background, horizontal gradient bar from green to amber
to red, labeled "PROVEN" "PROMISING" "MOSTLY HYPE", clean modern
Inter font, minimalist style, 4K resolution
```

---

## Checklist

### Spectrum Graphic
- [ ] Create design in chosen tool
- [ ] Add gradient bar (green → amber → red)
- [ ] Add section labels
- [ ] Add bullet point items
- [ ] Add footnote
- [ ] Export static PNG (4K)
- [ ] Create animation (optional)
- [ ] Export animated MOV

### Checklist Graphic
- [ ] Create card container
- [ ] Add title
- [ ] Add 5 checkmark items
- [ ] Style checkmarks green
- [ ] Export static PNG
- [ ] Create item-by-item animation (optional)
- [ ] Export animated MOV

### Framework Graphic
- [ ] Create two-column layout
- [ ] Add "Consider" column (green)
- [ ] Add "Hold Off" column (amber)
- [ ] Add checkmarks and X marks
- [ ] Add all list items
- [ ] Export static PNG
- [ ] Create column animation (optional)
- [ ] Export animated MOV

### Categories Summary (Optional)
- [ ] Create 4-column layout
- [ ] Color-code each category
- [ ] List peptides under each
- [ ] Export static PNG
- [ ] Export animated MOV
