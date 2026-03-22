# Dystonia Research Digest — Web Dashboard

## What This Is
Automated daily research digest that searches PubMed + Semantic Scholar for papers related to secondary dystonia treatment, DBS, TMS, pain management, and emerging therapies. Results are emailed, archived in SQLite, and viewable via a branded web dashboard.

## Quick Reference
| What | Where |
|------|-------|
| **Web dashboard** | `dystonia.marceausolutions.com` (EC2) or `localhost:8792` (local) |
| **Launch locally** | `./scripts/dystonia-digest.sh` |
| **Core search logic** | `execution/dystonia_research_digest.py` (shared utility) |
| **Web app** | `projects/marceau-solutions/labs/dystonia-digest/src/app.py` |
| **Database** | `data/dystonia_digest.db` (SQLite, gitignored) |
| **Archived PDFs** | `data/pdfs/` (gitignored) |
| **Port** | 8792 |
| **Email recipients** | wmarceau@marceausolutions.com, angelamarceau2@gmail.com |

## Architecture
```
execution/dystonia_research_digest.py    ← Shared: PubMed + S2 search, email, HTML
    ↓ imported by
src/digest_runner.py                     ← Wraps with DB persistence + PDF generation
    ↓ called by
src/app.py (FastAPI)                     ← Web dashboard + API endpoints
    ↓ served by
nginx → dystonia.marceausolutions.com    ← EC2 reverse proxy
    ↓ scheduled by
n8n workflow                             ← Daily 7am ET trigger via POST /api/run-digest
```

## API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/run-digest?days_back=7` | Trigger a digest run (background) |
| GET | `/api/status` | Last run status + aggregate stats |
| GET | `/api/digest/{id}` | JSON digest data for n8n consumption |
| GET | `/health` | Health check |

## Key Files
- `src/app.py` — FastAPI routes + Jinja2 templates
- `src/database.py` — SQLite schema, CRUD, stats
- `src/digest_runner.py` — Orchestrates search → dedup → DB → PDF → email
- `templates/` — 7 Jinja2 templates (dashboard, digest list/detail, paper detail/search, categories)
- `static/style.css` — Dark+gold branded theme

## Deployment
- **EC2**: systemd service `dystonia-digest.service` on port 8792
- **nginx**: `dystonia.marceausolutions.com` → `127.0.0.1:8792`
- **SSL**: certbot managed
- **Scheduling**: n8n workflow `Dystonia-Research-Digest-Daily` (replaces Mac launchd)
