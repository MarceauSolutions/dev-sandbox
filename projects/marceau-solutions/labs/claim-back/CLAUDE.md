# ClaimBack — Medical Billing Dispute Platform

> AI-powered platform that automates medical billing disputes and insurance claim denials. Turns a 5-15 hour manual process into a 15-minute guided workflow.

## Overview

ClaimBack helps patients fight back against medical billing errors and wrongful insurance denials by:
- **Guided intake** — step-by-step wizard collects dispute details and documents
- **AI analysis** — Claude analyzes bills, EOBs, and policies to find errors and applicable regulations
- **Letter generation** — produces professional appeal letters, dispute letters, and regulatory complaints
- **PDF packages** — assembles court-ready dispute packages with evidence, timelines, and legal citations
- **Deadline tracking** — monitors appeal windows and sends reminders

## Quick Commands

```bash
# Launch the app
./scripts/claim-back.sh          # Opens http://127.0.0.1:8790

# Or manually
cd projects/marceau-solutions/labs/claim-back
python src/app.py
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask (Python) |
| Frontend | Jinja2 templates + Tailwind CSS |
| AI | Claude API (Anthropic SDK) |
| PDF | ReportLab (via branded_pdf_engine.py) |
| Database | SQLite (local) |
| File Storage | Local filesystem (data/) |

## Architecture

```
claim-back/
├── CLAUDE.md              # This file
├── src/
│   ├── app.py             # Flask web app (main entry)
│   ├── ai_analyzer.py     # Claude API integration for bill analysis
│   ├── letter_generator.py # Appeal/dispute letter generation
│   ├── pdf_packager.py    # Professional PDF dispute package assembly
│   ├── ocr_processor.py   # Document text extraction
│   └── regulations.py     # Federal + state regulation database
├── templates/             # Jinja2 HTML templates
├── static/                # CSS, JS, images
│   ├── css/
│   └── js/
├── data/                  # User data (gitignored)
│   ├── disputes/          # Per-dispute folders
│   ├── uploads/           # Uploaded documents
│   └── claimback.db       # SQLite database
└── reference/             # Medical billing reference data
    ├── cpt_codes.json     # Common CPT code descriptions
    ├── denial_codes.json  # CARC/RARC denial reason codes
    └── regulations.json   # Federal + state law database
```

## Dispute Types Supported

| Type | Description |
|------|------------|
| Insurance Denial | Claim denied by insurer — internal/external appeal |
| Billing Error | Incorrect charges, upcoding, unbundling, duplicates |
| Surprise Bill | Out-of-network charges at in-network facility |
| Balance Billing | Provider billing beyond allowed amount |
| Service Not Rendered | Charged for services never received |
| Wrong Code | Incorrect CPT/ICD-10 coding |

## User Flow

1. **Start Dispute** → Select type, enter basic details
2. **Upload Documents** → Bill, EOB, insurance card, denial letter
3. **AI Analysis** → Claude identifies errors, applicable laws, deadlines
4. **Review Strategy** → User reviews findings, selects approach
5. **Generate Letters** → Appeal to insurer, dispute to provider, complaints
6. **Download Package** → Professional PDF with all documents
7. **Track Progress** → Dashboard with deadlines and escalation paths

## Revenue Model

- Per-dispute: $49-149 (tiered by bill amount)
- Subscription: $19.99/mo (unlimited disputes)
- B2B: Custom (employers, advocacy orgs)

## Status

- **Phase**: MVP Development
- **Port**: 8790
- **URL**: http://127.0.0.1:8790

## Key Regulations Referenced

- No Surprises Act (2022) — surprise billing protections
- ERISA — employer plan appeal requirements
- ACA — internal/external appeal rights
- FDCPA — medical debt collection protections
- State-specific balance billing laws (50 states)
