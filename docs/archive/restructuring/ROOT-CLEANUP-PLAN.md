# Root Directory Cleanup Plan

**Current State**: 60+ loose files in dev-sandbox root
**Goal**: Organized structure with files in appropriate subdirectories

---

## File Categories & Destinations

### KEEP IN ROOT (Essential Files)
```
CLAUDE.md                           ← Core operating instructions
README.md                           ← Repository overview
.env                                ← Environment variables
.env.example                        ← Template for new developers
.gitignore                          ← Git exclusions
requirements.txt                    ← Python dependencies
deploy_to_skills.py                 ← Deployment script
DOCKET.md                           ← Deferred work tracking
```

### MOVE TO docs/session-reports/ (Historical Reports)
```
AUTOMATION_STATUS.md
CLEANUP-TASKS-SUMMARY.md
CODE-QUALITY-REPORT.md
CRITICAL-FIX-APPLIED.md
FINAL-OPTIMIZATION-SUMMARY.md
FOLDER-ANALYSIS-REPORT.md
FORM-SUBMISSION-TEST-RESULTS.md
GOOGLE-ANALYTICS-SETUP.md
IMPLEMENTATION_SUMMARY.md
MONDAY_MORNING_REPORT.md
MORNING_EXECUTION_SUMMARY.md
PRODUCT-IDEAS-REVIEW.md
RALPH_INTEGRATION_COMPLETE.md
SOCIAL_MEDIA_CORRECTION.md
```

### MOVE TO docs/restructuring/ (Restructure History)
```
COMPANY-ASSET-DISTRIBUTION-ANALYSIS.md
COMPREHENSIVE-RESTRUCTURE-PLAN.md
FOLDER-RESTRUCTURE-DECISION-LOG.md
FOLDER-STRUCTURE-APPENDIX.md
FOLDER-STRUCTURE.md
HOME-DIRECTORY-REORGANIZATION-COMPLETE.md
MIGRATION-COMPLETE-SUMMARY.md
MIGRATION-EXECUTION-SUMMARY.md
PIPELINE-ALIGNMENT-VERIFICATION.md
REORGANIZATION-COMPLETE.md
RESTRUCTURE-PROPOSAL-WITH-SAFEGUARDS.md
```

### MOVE TO docs/git-setup/ (Git Configuration Docs)
```
GIT-REMOTE-VERIFICATION.md
REPO-TRANSFER-GUIDE.md
```

### MOVE TO scripts/ (Utility Scripts)
```
migrate_company_centric_autonomous.py
restructure_client_folders.sh
setup-git-remotes.sh
verify-automation-tools.sh
verify-git-remotes.sh
```

### MOVE TO .archive/migration-logs/ (Temporary Migration Files)
```
crontab-backup.txt
migration-output.txt
pre-migration-crontab.txt
pre-migration-git-status.txt
pre-migration-launchd.txt
```

### DELETE (Obsolete/Redundant)
```
ralph-autonomous.md                 ← Obsolete (Ralph concept abandoned)
ralph-claude.md                     ← Obsolete (Ralph concept abandoned)
.mcpregistry_github_token          ← Should be in .gitignore (check first)
.mcpregistry_registry_token        ← Should be in .gitignore (check first)
```

---

## New Directory Structure

```
dev-sandbox/
├── CLAUDE.md                       ← Keep
├── README.md                       ← Keep
├── DOCKET.md                       ← Keep
├── .env                            ← Keep
├── .env.example                    ← Keep
├── .gitignore                      ← Keep
├── requirements.txt                ← Keep
├── deploy_to_skills.py             ← Keep
│
├── .archive/
│   └── migration-logs/             ← NEW: Temporary migration outputs
│       ├── crontab-backup.txt
│       ├── pre-migration-*.txt
│       └── migration-output.txt
│
├── docs/
│   ├── session-reports/            ← NEW: Historical status reports
│   │   ├── AUTOMATION_STATUS.md
│   │   ├── CLEANUP-TASKS-SUMMARY.md
│   │   └── [14 other reports]
│   │
│   ├── restructuring/              ← NEW: Restructure history
│   │   ├── MIGRATION-COMPLETE-SUMMARY.md
│   │   ├── COMPREHENSIVE-RESTRUCTURE-PLAN.md
│   │   └── [9 other restructure docs]
│   │
│   └── git-setup/                  ← NEW: Git configuration
│       ├── GIT-REMOTE-VERIFICATION.md
│       └── REPO-TRANSFER-GUIDE.md
│
└── scripts/                        ← NEW: Utility scripts
    ├── migrate_company_centric_autonomous.py
    ├── restructure_client_folders.sh
    ├── setup-git-remotes.sh
    ├── verify-automation-tools.sh
    └── verify-git-remotes.sh
```

---

## Execution Steps

1. **Create new directories**
   ```bash
   mkdir -p .archive/migration-logs
   mkdir -p docs/session-reports
   mkdir -p docs/restructuring
   mkdir -p docs/git-setup
   mkdir -p scripts
   ```

2. **Move session reports**
   ```bash
   mv AUTOMATION_STATUS.md CLEANUP-TASKS-SUMMARY.md CODE-QUALITY-REPORT.md \
      CRITICAL-FIX-APPLIED.md FINAL-OPTIMIZATION-SUMMARY.md \
      FOLDER-ANALYSIS-REPORT.md FORM-SUBMISSION-TEST-RESULTS.md \
      GOOGLE-ANALYTICS-SETUP.md IMPLEMENTATION_SUMMARY.md \
      MONDAY_MORNING_REPORT.md MORNING_EXECUTION_SUMMARY.md \
      PRODUCT-IDEAS-REVIEW.md RALPH_INTEGRATION_COMPLETE.md \
      SOCIAL_MEDIA_CORRECTION.md \
      docs/session-reports/
   ```

3. **Move restructuring docs**
   ```bash
   mv COMPANY-ASSET-DISTRIBUTION-ANALYSIS.md \
      COMPREHENSIVE-RESTRUCTURE-PLAN.md \
      FOLDER-RESTRUCTURE-DECISION-LOG.md \
      FOLDER-STRUCTURE-APPENDIX.md FOLDER-STRUCTURE.md \
      HOME-DIRECTORY-REORGANIZATION-COMPLETE.md \
      MIGRATION-COMPLETE-SUMMARY.md MIGRATION-EXECUTION-SUMMARY.md \
      PIPELINE-ALIGNMENT-VERIFICATION.md REORGANIZATION-COMPLETE.md \
      RESTRUCTURE-PROPOSAL-WITH-SAFEGUARDS.md \
      docs/restructuring/
   ```

4. **Move git setup docs**
   ```bash
   mv GIT-REMOTE-VERIFICATION.md REPO-TRANSFER-GUIDE.md docs/git-setup/
   ```

5. **Move scripts**
   ```bash
   mv migrate_company_centric_autonomous.py restructure_client_folders.sh \
      setup-git-remotes.sh verify-automation-tools.sh verify-git-remotes.sh \
      scripts/
   ```

6. **Archive migration logs**
   ```bash
   mv crontab-backup.txt migration-output.txt pre-migration-*.txt \
      .archive/migration-logs/
   ```

7. **Delete obsolete files**
   ```bash
   rm ralph-autonomous.md ralph-claude.md
   # Check if tokens are in .gitignore first
   grep mcpregistry .gitignore && rm .mcpregistry_*_token
   ```

8. **Update .gitignore** (if needed)
   ```bash
   echo ".mcpregistry_*_token" >> .gitignore
   echo ".archive/" >> .gitignore
   ```

9. **Git commit**
   ```bash
   git add -A
   git commit -m "refactor: Organize root directory files

   - Move 14 session reports to docs/session-reports/
   - Move 11 restructure docs to docs/restructuring/
   - Move 2 git docs to docs/git-setup/
   - Move 5 utility scripts to scripts/
   - Archive 5 migration logs to .archive/migration-logs/
   - Delete 2 obsolete Ralph docs
   - Keep 8 essential files in root (CLAUDE.md, README.md, etc.)

   Reduces root clutter from 60 files to 8 essential files.

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

---

## Benefits

- **Clean root**: Only 8 essential files visible
- **Organized history**: Session reports grouped together
- **Archived logs**: Migration artifacts preserved but hidden
- **Logical grouping**: Related files together (git docs, scripts, etc.)
- **Easier navigation**: No more scrolling through 60 files to find what you need

---

## Files Remaining in Root (8)

1. `CLAUDE.md` - Core operating instructions
2. `README.md` - Repository overview
3. `DOCKET.md` - Deferred work tracking
4. `.env` - Environment secrets
5. `.env.example` - Environment template
6. `.gitignore` - Git exclusions
7. `requirements.txt` - Dependencies
8. `deploy_to_skills.py` - Main deployment script

Clean, minimal, intentional.
