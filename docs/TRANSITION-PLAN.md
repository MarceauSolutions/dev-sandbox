# SYSTEM TRANSITION PLAN
**Date:** March 25, 2026  
**Goal:** Consolidate scattered architecture into clean, maintainable system

---

## PHASE 1: IMMEDIATE FIXES (Tonight)

Run these commands on EC2:

```bash
# 1. Install Ralph as permanent service
sudo cp /home/clawdbot/dev-sandbox/ralph/ralph.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ralph
sudo systemctl start ralph

# 2. Restart sales pipeline (loads new call/visit endpoints)
sudo systemctl restart sales-pipeline

# 3. Verify both running
systemctl status ralph sales-pipeline
```

**Apollo (Manual in Browser):**
1. Go to app.apollo.io
2. Settings → Email Accounts → Connect your email
3. Sequences → "General AI service" → Activate
4. Add contacts to sequence

---

## PHASE 2: CONSOLIDATION (This Week)

### Step 1: Create Unified Workspace Structure

```bash
# On EC2
mkdir -p /home/clawdbot/workspace/{agents,projects,services,data,config}

# Move Clawdbot agent files
mv /home/clawdbot/clawd/* /home/clawdbot/workspace/agents/clawdbot/

# Move Ralph
mv /home/clawdbot/dev-sandbox/ralph /home/clawdbot/workspace/agents/ralph/

# Move active projects
mv /home/clawdbot/dev-sandbox/projects/shared/sales-pipeline /home/clawdbot/workspace/projects/
mv /home/clawdbot/dev-sandbox/projects/shared/lead-scraper /home/clawdbot/workspace/projects/
mv /home/clawdbot/dev-sandbox/projects/shared/ai-customer-service /home/clawdbot/workspace/projects/

# Consolidate data
mv /home/clawdbot/workspace/projects/sales-pipeline/data/* /home/clawdbot/workspace/data/

# Move credentials
mv /home/clawdbot/dev-sandbox/.env /home/clawdbot/workspace/config/
mv /home/clawdbot/dev-sandbox/token*.json /home/clawdbot/workspace/config/
```

### Step 2: Update Service Paths

For each service in `/etc/systemd/system/`:
- Update `WorkingDirectory` to new location
- Update `ExecStart` path
- Run `sudo systemctl daemon-reload`

### Step 3: Create Service Registry

Create `/home/clawdbot/workspace/config/services.json`:

```json
{
  "services": {
    "sales-pipeline": {
      "port": 8785,
      "path": "/home/clawdbot/workspace/projects/sales-pipeline",
      "systemd": "sales-pipeline.service",
      "url": "https://pipeline.marceausolutions.com"
    },
    "ralph": {
      "path": "/home/clawdbot/workspace/agents/ralph",
      "systemd": "ralph.service"
    }
  },
  "data": {
    "pipeline_db": "/home/clawdbot/workspace/data/pipeline.db",
    "call_log": "/home/clawdbot/workspace/data/call_log.json",
    "visit_log": "/home/clawdbot/workspace/data/visit_log.json"
  },
  "credentials": {
    "env": "/home/clawdbot/workspace/config/.env",
    "google_personal": "/home/clawdbot/workspace/config/token.json",
    "google_business": "/home/clawdbot/workspace/config/token_marceausolutions.json"
  }
}
```

### Step 4: Update Git

```bash
cd /home/clawdbot/workspace
git init
git remote add origin git@github.com:MarceauSolutions/workspace.git
git add .
git commit -m "Consolidated workspace structure"
git push -u origin main
```

---

## PHASE 3: CLEANUP (Next Week)

### Delete Old Locations

```bash
# After verifying everything works
rm -rf /home/clawdbot/clawd
rm -rf /home/clawdbot/dev-sandbox
rm -rf /home/clawdbot/accountability
rm -rf /home/clawdbot/keyvault
rm -rf /home/clawdbot/email-assistant
rm -rf /home/clawdbot/claimback
```

### Archive Unused Projects

```bash
# Move to cold storage or delete
mv /home/clawdbot/workspace/projects/archived /home/clawdbot/cold-storage/
```

### Audit Execution Scripts

Go through `/home/clawdbot/dev-sandbox/execution/` (97 scripts):
- Keep: `agent_bridge_api.py`, `accountability_handler.py`, `branded_pdf_engine.py`
- Archive: Anything not used in 30+ days
- Delete: Obvious cruft

---

## NEW STRUCTURE (Final State)

```
/home/clawdbot/workspace/
├── config/
│   ├── .env                    # All API keys
│   ├── token.json              # Google personal
│   ├── token_marceausolutions.json
│   └── services.json           # Service registry
├── agents/
│   ├── clawdbot/
│   │   ├── SOUL.md
│   │   ├── MEMORY.md
│   │   ├── memory/             # Daily logs
│   │   └── HEARTBEAT.md
│   └── ralph/
│       ├── ralph_service.py
│       ├── handoffs.json
│       └── prd/
├── projects/
│   ├── sales-pipeline/         # Active CRM
│   ├── lead-scraper/           # Apollo + enrichment
│   └── ai-customer-service/    # Client delivery
├── data/
│   ├── pipeline.db
│   ├── call_log.json
│   ├── visit_log.json
│   └── outreach/
└── scripts/
    ├── agent_bridge_api.py
    ├── accountability_handler.py
    └── core/                   # Shared utilities
```

---

## BENEFITS

1. **Single source of truth** — No more wondering which folder is correct
2. **Clear ownership** — Agents have their own directories
3. **Portable** — One git repo to clone
4. **Service registry** — Know what's running where
5. **Data consolidation** — All state in `/data/`

---

## ROLLBACK PLAN

If anything breaks:
```bash
# Restore from dev-sandbox backup
cp -r /home/clawdbot/dev-sandbox.backup/* /home/clawdbot/dev-sandbox/
sudo systemctl restart sales-pipeline
```

Before starting, create backup:
```bash
cp -r /home/clawdbot/dev-sandbox /home/clawdbot/dev-sandbox.backup
cp -r /home/clawdbot/clawd /home/clawdbot/clawd.backup
```

---

*Created by Clawdbot — March 25, 2026*
