# LaunchPad — Iterative Product Launch Platform

**Status**: Active Development | **Type**: Web App (SaaS)
**URL**: `http://localhost:8765` (local) | Future: hosted SaaS

## What It Does
A web-based SaaS platform that runs the full iterative product launch pipeline for any product:
1. Pre-launch checklist verification
2. 48h organic validation window with content posting schedule
3. Real-time signup tracking (Sheets + UTM breakdown)
4. Validation gate (GO / PIVOT / NO-GO decision engine)
5. Content generation (AI images + platform copy)
6. Manual post flow with download packages per platform
7. Paid ad phase management

## Project Structure
```
launch-platform/
├── CLAUDE.md               # This file
├── src/
│   └── app.py              # Flask web server + API endpoints
├── templates/
│   └── index.html          # Single-page dashboard
├── static/
│   ├── css/style.css       # Dark + gold brand theme
│   ├── js/app.js           # Frontend logic
│   └── img/                # UI assets
├── workflows/              # SOPs and workflows for this product
└── requirements.txt
```

## Launch
```bash
# From dev-sandbox root
python projects/marceau-solutions/labs/launch-platform/src/app.py --product dumbphone-lock
# OR via launch.py
python scripts/launch.py  # → select product → "Open Web Dashboard"
```

## Architecture
- Flask backend reads from product's `launch/launch_manager.py` + `content_pipeline.py`
- Products registered via `launch/launch_state.json` + `launch/content_pipeline.py` presence
- Generic: any product with a `launch/` directory auto-registers
- API-first: all actions via JSON REST endpoints

## API Endpoints
| Method | Endpoint | What |
|--------|----------|------|
| GET | `/api/state` | Launch state + phase |
| GET | `/api/metrics` | Live signups, UTM, velocity |
| GET | `/api/platforms` | All platforms with status |
| POST | `/api/mark/<key>` | Mark post as done |
| GET | `/api/content/<key>/copy` | Raw post copy |
| GET | `/api/content/<key>/image` | Generated image |
| GET | `/api/content/<key>/download` | Zip: image + copy + guide |
| POST | `/api/generate/<key>` | Trigger image generation |
| POST | `/api/gate` | Run gate evaluation |
| GET | `/api/report` | Generate + serve PDF |

## Platform Connection Status
Each platform shows connection status:
- **Connected** (API key present + verified) → Auto-post button
- **Pending** (applied, waiting) → Shows wait status
- **Manual** (no API) → Manual post flow with download

## SOP References
- SOP 32: Project Routing (this is a Labs/SaaS project)
- SOP 0: Kickoff decisions documented in KICKOFF.md
- SOP 9: Architecture — single-page Flask app with REST API
