# Peptide Video - Text Overlay Specifications

**Created:** 2026-02-03
**Style:** Clean, modern, professional fitness/science aesthetic

---

## Design System

### Color Palette
```
Background:      #0f172a (dark navy) - for full screen graphics
Primary Text:    #ffffff (white)
Accent Green:    #22c55e (for "positive" / "consider")
Accent Amber:    #f59e0b (for "caution" / "hold off")
Accent Blue:     #3b82f6 (for scientific/category headers)
Accent Red:      #ef4444 (for "hype" end of spectrum)
Shadow:          rgba(0,0,0,0.5)
```

### Typography
```
Primary Font:    Inter (Google Fonts) or SF Pro Display
Fallback:        Helvetica Neue, Arial, sans-serif
Weights Used:    Bold (700), Black (900)
```

---

## LOWER THIRDS: Peptide Names

**Purpose:** Display peptide name when first mentioned in video
**Position:** Lower left corner, 10% from bottom, 5% from left edge
**Duration:** 3-4 seconds per overlay
**Animation:** Fade in (0.3s) → Hold → Fade out (0.3s)

### Specifications

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│  ┌──────────────────┐                               │
│  │  SERMORELIN      │  ← Peptide name              │
│  │  GH Secretagogue │  ← Category (smaller)        │
│  └──────────────────┘                               │
└─────────────────────────────────────────────────────┘
```

### Style Details

| Property | Value |
|----------|-------|
| **Background** | Semi-transparent dark (#0f172a @ 80% opacity) |
| **Border** | 3px left border in category color |
| **Padding** | 16px horizontal, 12px vertical |
| **Border Radius** | 0px left, 8px right (pill shape on right) |
| **Name Font** | Inter Bold, 48px, white |
| **Category Font** | Inter Regular, 24px, category accent color |
| **Shadow** | 0 4px 12px rgba(0,0,0,0.3) |

### All Peptide Lower Thirds

#### Category 1: GH Secretagogues (Blue: #3b82f6)

| # | Peptide Name | Category Label | Insert Point |
|---|--------------|----------------|--------------|
| 1 | SERMORELIN | GH Secretagogue | Section 2, Part 2-3 |
| 2 | CJC-1295 | GH Secretagogue | Section 2, Part 3 |
| 3 | IPAMORELIN | GH Secretagogue | Section 2, Part 3 |
| 4 | TESAMORELIN | GH Secretagogue (FDA Approved) | Section 2, Part 3 |

#### Category 2: Healing & Recovery (Green: #22c55e)

| # | Peptide Name | Category Label | Insert Point |
|---|--------------|----------------|--------------|
| 5 | BPC-157 | Healing Peptide | Section 2, Part 4-5 |
| 6 | TB-500 | Recovery Peptide | Section 2, Part 5 |

#### Category 3: Performance (Amber: #f59e0b)

| # | Peptide Name | Category Label | Insert Point |
|---|--------------|----------------|--------------|
| 7 | GHRP-6 | Performance | Section 2, Part 6 |
| 8 | MK-677 | Performance* | Section 2, Part 6 |
| 9 | AOD-9604 | Body Composition | Section 2, Part 6 |

*Note: MK-677 technically not a peptide - add asterisk or note in overlay

#### Category 4: Cognitive & Longevity (Purple: #8b5cf6)

| # | Peptide Name | Category Label | Insert Point |
|---|--------------|----------------|--------------|
| 10 | EPITHALON | Longevity | Section 2, Part 7 |
| 11 | SEMAX | Cognitive | Section 2, Part 7 |
| 12 | SELANK | Cognitive | Section 2, Part 7 |

---

## FULL SCREEN: Category Headers

**Purpose:** Announce each category as a section divider
**Position:** Center screen
**Duration:** 1.5-2 seconds
**Animation:** Scale in from 80% → 100%, hold, fade out

### Specifications

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                                                     │
│                                                     │
│           GROWTH HORMONE                            │
│           SECRETAGOGUES                             │
│                                                     │
│                                                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Style Details

| Property | Value |
|----------|-------|
| **Background** | Semi-transparent dark overlay (#0f172a @ 70%) |
| **Text Font** | Inter Black, 96-120px |
| **Text Color** | White with category accent underline |
| **Alignment** | Center |
| **Animation In** | Scale from 80% + fade in (0.4s) |
| **Animation Out** | Fade out (0.3s) |
| **Underline** | 4px thick, category color, 50% of text width |

### All Category Headers

| # | Header Text | Accent Color | Insert Point |
|---|-------------|--------------|--------------|
| 1 | GROWTH HORMONE SECRETAGOGUES | Blue #3b82f6 | Section 2, before Part 2 |
| 2 | HEALING & RECOVERY | Green #22c55e | Section 2, before Part 4 |
| 3 | PERFORMANCE & BODY COMP | Amber #f59e0b | Section 2, before Part 6 |
| 4 | COGNITIVE & LONGEVITY | Purple #8b5cf6 | Section 2, before Part 7 |

---

## STATISTICS / CALLOUTS

**Purpose:** Highlight key statistics or important points
**Position:** Lower right or center (varies)
**Duration:** 3-5 seconds

### Specifications

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                                                     │
│                                 ┌────────────────┐  │
│                                 │      30+       │  │
│                                 │    YEARS       │  │
│                                 │  of Research   │  │
│                                 └────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Statistics to Add

| # | Statistic | Context | Insert Point |
|---|-----------|---------|--------------|
| 1 | "30+ YEARS" | "of Research" (GHRP history) | Section 2, Part 6 |
| 2 | "1997-2008" | "FDA Approved" (Sermorelin) | Section 2, Part 3 |
| 3 | "NOT FDA APPROVED" | "for fitness uses" | Section 2, Part 8 |

---

## DISCLAIMER OVERLAY

**Purpose:** Legal/compliance disclaimer
**Position:** Bottom of screen
**Duration:** Displayed throughout specific sections or as needed

### Specifications

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│  ────────────────────────────────────────────────   │
│  This is not medical advice. Consult a healthcare  │
│  provider before starting any supplement protocol.  │
│  ────────────────────────────────────────────────   │
└─────────────────────────────────────────────────────┘
```

### Style Details

| Property | Value |
|----------|-------|
| **Background** | Semi-transparent dark bar |
| **Font** | Inter Regular, 18px |
| **Color** | White @ 80% opacity |
| **Position** | Bottom 5% of screen |
| **Duration** | 5-8 seconds, or persistent in specific sections |

---

## SUBSCRIBE ANIMATION (CTA)

**Purpose:** Remind viewers to subscribe
**Position:** Lower right corner
**Duration:** 5 seconds
**Timing:** During CTA section

### Elements

1. **Subscribe Button**
   - Red background (#ff0000)
   - White text "SUBSCRIBE"
   - Bell icon animation

2. **Animation**
   - Slide in from right (0.3s)
   - Gentle bounce/pulse
   - Fade out (0.3s)

---

## END SCREEN ELEMENTS

**Duration:** Final 20 seconds of video
**Elements:**
1. Subscribe button (persistent)
2. Next video thumbnail placeholder (left)
3. Playlist link (right)
4. Channel avatar (optional)

### Layout

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│     ┌──────────────┐         ┌──────────────┐      │
│     │              │         │              │      │
│     │  NEXT VIDEO  │         │   PLAYLIST   │      │
│     │  [Thumbnail] │         │  [Thumbnail] │      │
│     │              │         │              │      │
│     └──────────────┘         └──────────────┘      │
│                                                     │
│              [SUBSCRIBE BUTTON]                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Export Formats

### For Video Editors
- **PNG with transparency** - Each overlay as separate PNG
- **Resolution:** 3840x2160 (4K) or 1920x1080
- **Color profile:** sRGB

### For Motion Graphics
- **After Effects project** - Layered, animated
- **MOV with alpha** - Pre-rendered animations
- **Duration:** Per spec above

---

## Quick Reference: Insert Points

| Overlay Type | Section | Part | Timestamp |
|--------------|---------|------|-----------|
| Category: GH Secretagogues | 2 | Before Part 2 | ~2:30 |
| Lower Third: Sermorelin | 2 | Part 2-3 | ~2:45 |
| Lower Third: CJC-1295 | 2 | Part 3 | ~3:00 |
| Lower Third: Ipamorelin | 2 | Part 3 | ~3:10 |
| Lower Third: Tesamorelin | 2 | Part 3 | ~3:20 |
| Category: Healing & Recovery | 2 | Before Part 4 | ~3:30 |
| Lower Third: BPC-157 | 2 | Part 4-5 | ~3:45 |
| Lower Third: TB-500 | 2 | Part 5 | ~4:00 |
| Category: Performance | 2 | Before Part 6 | ~4:15 |
| Lower Third: GHRP-6 | 2 | Part 6 | ~4:20 |
| Lower Third: MK-677 | 2 | Part 6 | ~4:30 |
| Lower Third: AOD-9604 | 2 | Part 6 | ~4:40 |
| Category: Cognitive | 2 | Before Part 7 | ~4:50 |
| Lower Third: Epithalon | 2 | Part 7 | ~4:55 |
| Lower Third: Semax | 2 | Part 7 | ~5:05 |
| Lower Third: Selank | 2 | Part 7 | ~5:10 |
| Disclaimer | 2 | Part 8 | ~5:15 |
| Spectrum Graphic | 3 | Part 3-4 | ~6:00 |
| Checklist Graphic | 4 | Part 3 | ~8:00 |
| Framework Graphic | 4 | Part 4 | ~9:15 |
| Subscribe Animation | CTA | Part 1 | ~10:30 |
| End Screen | CTA | Part 3 | ~10:40 |

---

## Checklist

- [ ] Create 12 peptide name lower thirds (PNG)
- [ ] Create 4 category header animations
- [ ] Create 3 statistic callouts
- [ ] Create disclaimer bar
- [ ] Create subscribe animation
- [ ] Create end screen template
- [ ] Export all at 4K resolution
- [ ] Test overlays in timeline
