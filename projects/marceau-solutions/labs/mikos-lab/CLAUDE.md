# Miko's Lab — AI Avatar Workshop

**Status**: Active | **Type**: Workshop + Implementation Tracker | **Port**: 8766

## What It Does
Full production web app for learning AND executing AI avatar/influencer creation from Miko's Lab Telegram channel content. Not just a reference library — it tracks projects, methods tried, prompts that work, and assets generated.

## Launch
```bash
./scripts/mikos-lab.sh
# Opens http://127.0.0.1:8766
```

## Features

### Build (Actionable)
- **My Projects** — Create avatar projects with 11-step workflow pipeline (niche research → monetization). Track progress, status, persona details, character prompts.
- **Method Tracker** — 18 pre-seeded methods from Miko's content. Track status (not started → learning → tried → works/doesn't work), add notes, rate results.
- **Prompt Library** — Save and organize prompts that produce good results. Categorized by type (character, video, voice, image, social). Favorite and copy.
- **Asset Tracking** — Log generated images, videos, audio per project. Track which prompt and tool produced each asset.

### Learn (Reference)
- **Knowledge Library** — 21 PDF guides extracted into searchable categories
- **Methods Summary** — Executive overview of Miko's core workflow
- **Telegram Feed** — Latest posts with sync button (scrapes t.me/s/mikoslab)
- **PDF Library** — 23 PDFs viewable in browser
- **Available Tools** — Shows connected execution tools (image gen, video gen, social posting)

## Architecture
- **Backend**: Flask + SQLite (mikoslab.db)
- **Frontend**: Single-page app, dark+gold branded (#C9963C)
- **Database Tables**: projects, workflow_steps, assets, method_tracker, prompts
- **Scraper**: BeautifulSoup scraping public Telegram channel

## Key Locations
| What | Where |
|------|-------|
| App server | `app.py` |
| Database schema | `database.py` |
| SQLite DB | `mikoslab.db` |
| Frontend | `templates/index.html` |
| Telegram scraper | `scripts/scrape_mikoslab.py` |
| PDF parser | `scripts/parse_pdfs.py` |
| Launch script | `scripts/mikos-lab.sh` |
| Scraped posts | `posts/` |
| Downloaded PDFs | `pdfs/` (23 files, ~28MB) |
| Knowledge base | `KNOWLEDGE_BASE.md` (187KB) |
| Methods summary | `MIKO_METHODS_SUMMARY.md` |

## API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/overview` | Dashboard stats |
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/<id>` | Project detail + steps + assets |
| PUT | `/api/projects/<id>` | Update project |
| PUT | `/api/projects/<id>/steps/<id>` | Update workflow step |
| POST | `/api/projects/<id>/assets` | Log asset |
| GET | `/api/methods/tracker` | All methods with status |
| PUT | `/api/methods/tracker/<id>` | Update method status/notes |
| GET | `/api/prompts` | Prompt library |
| POST | `/api/prompts` | Save prompt |
| GET | `/api/knowledge` | Categorized guides |
| POST | `/api/sync` | Trigger Telegram sync |
| POST | `/api/generate/image` | Generate via Grok |

## Default Workflow Steps (per project)
1. Niche Research & Validation
2. Persona Design & Bio
3. Character Image Creation
4. Starting Frame Library
5. Voice & Audio Setup
6. First Video Generation
7. Content Batch (5-10 pieces)
8. Platform Account Setup
9. First Post Published
10. Consistent Posting (7 days)
11. Monetization Activation
