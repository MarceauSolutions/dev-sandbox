# Asset Organization Standard

## Directory Structure

```
/home/clawdbot/dev-sandbox/
├── assets/                              # GLOBAL shared assets
│   ├── stock/                           # Stock photos (licensed)
│   ├── icons/                           # Common icons
│   └── templates/                       # Design templates
│
├── projects/
│   ├── marceau-solutions/
│   │   ├── brand/                       # COMPANY brand assets (shared across sites)
│   │   │   ├── logos/
│   │   │   ├── colors.md
│   │   │   └── fonts/
│   │   │
│   │   └── website/                     # marceausolutions.com
│   │       └── assets/images/
│   │           ├── william/             # William's personal photos
│   │           ├── brand/               # Site-specific brand (favicon, og-image)
│   │           └── portfolio/           # Work samples, case studies
│   │
│   ├── flames-of-passion/               # SEPARATE business - Ericka's fire performance
│   │   └── website/
│   │       └── assets/images/
│   │           ├── ericka/              # Ericka's performance photos
│   │           ├── brand/               # FOP logos
│   │           └── events/              # Event photos
│   │
│   └── [client-name]/                   # FUTURE CLIENTS
│       ├── brand/
│       └── website/
│           └── assets/images/
│               ├── team/
│               ├── products/
│               ├── portfolio/
│               └── brand/
```

## Naming Conventions

### Photos
- `[subject]-[description].jpg` — e.g., `william-gym-pose.jpg`
- Lowercase, hyphens, no spaces
- Descriptive but concise

### Logos
- `logo-[variant].png` — e.g., `logo-dark.png`, `logo-light.png`, `logo-icon.png`

### Favicons
- `favicon.ico`, `favicon-32x32.png`, `apple-touch-icon.png`

## Current Cleanup Needed

### Marceau Solutions Website
The `/assets/images/` folder currently contains Flames of Passion photos mixed in.

**To move to flames-of-passion project:**
- `artistic-fire-crown-blue.jpg`
- `beach-sunset-fire-staff.jpg`
- `fire-hoop-poolside.jpg`
- `handstand-fire-inverted.jpg`
- `handstand-splits-fire.jpg`
- `hero-fire-poi-closeup.jpg`
- `performance-fire-staff-theatrical.jpg`
- `portrait-fire-blue-wall.jpg`
- `crowd-watching-event.jpg`
- `LogoDark.png` (Flames of Passion logo)
- `logo.jpg` (Flames of Passion logo)

**William's photos (keep in william/):**
- `gym-pose.jpg`
- `gym-front.jpg`
- `gym-side.jpg`
- `gym-twist.jpg`
- `bicep-pose.jpg`

**Brand assets (keep in brand/ or root):**
- `favicon.ico`
- `favicon-32x32.png`
- `apple-touch-icon.png`

## For New Clients

1. Create `/projects/[client-name]/` directory
2. Create `brand/` for logos, colors, fonts
3. Create `website/assets/images/` with subdirectories:
   - `team/` — headshots, team photos
   - `products/` — product images
   - `portfolio/` — work samples
   - `brand/` — site-specific assets

## Notes
- Never mix client assets
- Keep source files (PSD, AI, etc.) in `brand/source/` if provided
- Optimize images before deployment (max 500KB for web)
