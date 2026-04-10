# FULL SYSTEM AUDIT — March 25, 2026

## Executive Summary

Your current architecture is a sprawling mess accumulated over months with no clear boundaries. Things are duplicated across locations, services are running but not connected, and there's no single source of truth for anything.

**Total stats:**
- 22 custom systemd services running
- 347MB in `/projects/` alone
- 97 Python scripts in `/execution/`
- 2 git repos (clawd + dev-sandbox)
- 18 stale CSV files (>30 days old)
- Multiple locations storing the same type of data

---

## CRITICAL ISSUES

### 1. TWO SEPARATE WORKSPACES (CONFUSION)

**Problem:**
- `/home/clawdbot/clawd/` — Clawdbot's workspace (memory, SOUL.md, etc.)
- `/home/clawdbot/dev-sandbox/` — Development workspace (projects, execution scripts)

**Why it's bad:**
- Memory files in `clawd/memory/` but project state in `dev-sandbox/`
- No clear ownership of which agent owns what
- Claude Code on Mac uses `dev-sandbox` but I (Clawdbot) use `clawd`

### 2. DUPLICATED PROJECT LOCATIONS

**Examples:**
- `/home/clawdbot/sales-pipeline/` AND `/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/`
- `/home/clawdbot/accountability/` AND accountability tracked via n8n
- `/home/clawdbot/keyvault/` AND `/home/clawdbot/dev-sandbox/projects/marceau-solutions/labs/` has similar tools

**Why it's bad:**
- Which one is the source of truth?
- Services point to different locations
- Updates get made in one place, not synced to another

### 3. 97 LOOSE SCRIPTS IN `/execution/`

**Problem:**
- `agent_bridge_api.py` (5,000+ lines)
- `accountability_handler.py`
- `branded_pdf_engine.py`
- 94 more scripts with no clear organization

**Why it's bad:**
- No way to know which are actively used
- No tests
- No documentation
- Impossible to maintain

### 4. N8N HAS 0 ACTIVE WORKFLOWS

Despite having n8n running, ALL workflows are disabled. This means:
- No morning accountability
- No EOD check-ins
- No weekly reports
- No automated anything

### 5. APOLLO SEQUENCES NEVER ACTIVATED

- 9 sequences created
- 0 activated
- 0 emails sent ever

### 6. SCATTERED CREDENTIALS

- `.env` in `/dev-sandbox/`
- `token.json`, `token_marceausolutions.json`, `token_sheets.json` in root
- `.anthropic_key` in home
- `.telegram_env` in home

### 7. NO UNIFIED STATE

- Pipeline state in SQLite at `/projects/shared/sales-pipeline/data/pipeline.db`
- Call log in JSON at same location
- Mem0 running at `localhost:5020` (separate memory)
- Clawdbot memory in `/clawd/memory/`
- Handoffs in `/dev-sandbox/ralph/handoffs.json`

---

## RECOMMENDED ARCHITECTURE

### Option A: Consolidate Everything Under One Workspace

```
/home/clawdbot/workspace/
├── .env                          # Single source for all credentials
├── agents/
│   ├── clawdbot/
│   │   ├── SOUL.md
│   │   ├── memory/               # Daily logs
│   │   └── MEMORY.md             # Long-term
│   ├── ralph/
│   │   ├── config.json
│   │   ├── prd/                  # Active PRDs
│   │   └── completed/            # Done PRDs
│   └── handoffs.json             # Cross-agent tasks
├── projects/
│   ├── active/                   # Currently working on
│   │   ├── sales-pipeline/
│   │   ├── ai-customer-service/
│   │   └── lead-scraper/
│   ├── labs/                     # Experiments
│   └── archived/                 # Done/abandoned
├── services/                     # All running services
│   ├── sales-pipeline/
│   ├── accountability/
│   ├── keyvault/
│   └── ...
├── execution/                    # Shared scripts (reorganized)
│   ├── core/                     # Core utilities
│   ├── integrations/             # API integrations
│   └── automation/               # Scheduled tasks
├── data/                         # Single data location
│   ├── pipeline.db
│   ├── call_log.json
│   ├── visit_log.json
│   └── outreach/
└── config/
    ├── services.json             # Service catalog
    └── credentials/              # All tokens
```

### Option B: Keep Current Structure But Add Manifests

Add manifest files that define what's active:

```
/home/clawdbot/MANIFEST.json
{
  "active_workspaces": ["clawd", "dev-sandbox"],
  "primary_data": "/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/data/",
  "services": {
    "sales-pipeline": {
      "path": "/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline",
      "port": 8785,
      "systemd": "sales-pipeline.service"
    }
  },
  "credentials": {
    "env": "/home/clawdbot/dev-sandbox/.env",
    "tokens": "/home/clawdbot/dev-sandbox/"
  }
}
```

---

## IMMEDIATE FIXES (Do Now)

### 1. Enable n8n Workflows
```bash
# These need to be activated via n8n UI or API
- Morning-Accountability-v3
- EOD-Check-In
- Weekly-Report
- Treatment-Day-Detector
```

### 2. Clean Up Duplicate Locations
```bash
# Remove stale duplicates
rm -rf /home/clawdbot/sales-pipeline  # Use dev-sandbox version
rm -rf /home/clawdbot/pipeline        # Use dev-sandbox version
```

### 3. Install Ralph Service
```bash
sudo cp /home/clawdbot/dev-sandbox/ralph/ralph.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ralph
sudo systemctl start ralph
```

### 4. Restart Sales Pipeline (Load New Endpoints)
```bash
sudo systemctl restart sales-pipeline
```

### 5. Apollo — Activate Sequence
- Go to app.apollo.io
- Connect email account
- Activate "General AI service" sequence
- Add contacts

---

## LONG-TERM RECOMMENDATIONS

1. **Single Git Repo** — Merge `clawd` and `dev-sandbox` into one repo with clear boundaries

2. **Service Registry** — Create a `/config/services.json` that documents every running service

3. **Data Consolidation** — One `/data/` directory for all persistent state

4. **Script Audit** — Go through 97 execution scripts, delete unused, document active

5. **n8n as Automation Hub** — All scheduled tasks through n8n, not cron

6. **Daily Automated Tests** — Verify all services respond, all integrations work

---

## TRANSITION PLAN

### Phase 1: Stabilize (Today)
- Enable n8n workflows
- Install Ralph service
- Restart pipeline service
- Delete duplicate folders

### Phase 2: Document (This Week)
- Create MANIFEST.json
- Document all active services
- Map data flows

### Phase 3: Consolidate (Next Week)
- Merge git repos
- Reorganize into clean structure
- Update all service paths

### Phase 4: Test (Ongoing)
- Add health checks to all services
- Create daily integration test
- Monitor for regressions

---

## Files Created/Updated This Session

- `/home/clawdbot/dev-sandbox/ralph/ralph_service.py` — Ralph service
- `/home/clawdbot/dev-sandbox/ralph/ralph.service` — systemd unit
- `/home/clawdbot/dev-sandbox/ralph/handoffs.json` — Updated structure
- `/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/src/call_logger.py`
- `/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/src/visit_scheduler.py`
- `/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/src/unified_tracker.py`
- Updated `app.py` with new endpoints

---

*Audit performed by Clawdbot — March 25, 2026*
