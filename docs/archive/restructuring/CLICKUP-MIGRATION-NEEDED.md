# ClickUp Integration Migration Needed

**Issue**: ClickUp integration exists in old `execution/clickup_api.py` location
**Should Be**: Proper project structure in `projects/shared/clickup-crm/` or as MCP

---

## Current State

```
execution/
├── clickup_api.py              ← Old location (9KB)
└── clickup_oauth.py            ← OAuth helper (6KB)

directives/
├── clickup_crm.md              ← Directive exists
└── sales_crm.md                ← References ClickUp
```

**Usage**: Multi-tenant (used across multiple companies for CRM)

---

## Recommended Migration Path

### Option 1: Shared CRM Tool (Recommended)

Move to shared multi-tenant location:

```
projects/shared/clickup-crm/
├── src/
│   ├── clickup_api.py          ← Move from execution/
│   ├── clickup_oauth.py        ← Move from execution/
│   └── crm_operations.py       ← Higher-level CRM ops
├── workflows/
│   └── client-onboarding.md    ← Document CRM workflows
├── VERSION                     ← 1.0.0-dev
├── CHANGELOG.md
├── SKILL.md                    ← If deploying as skill
└── README.md
```

**Why**: ClickUp CRM is used across all companies (multi-tenant use case)

---

### Option 2: ClickUp MCP Server

If you want Claude.ai integration:

```
projects/marceau-solutions/clickup-mcp/
└── src/
    └── clickup_mcp/
        ├── __init__.py
        ├── server.py           ← MCP server
        ├── clickup_api.py      ← API wrapper
        └── tools.py            ← MCP tools (create task, update, etc.)
```

**Why**: Makes ClickUp accessible to Claude via MCP protocol

---

## Migration Commands

### Move to Shared CRM (Option 1)

```bash
cd /Users/williammarceaujr./dev-sandbox

# Create project structure
mkdir -p projects/shared/clickup-crm/src projects/shared/clickup-crm/workflows

# Move files
git mv execution/clickup_api.py projects/shared/clickup-crm/src/
git mv execution/clickup_oauth.py projects/shared/clickup-crm/src/

# Copy directive to workflows
cp directives/clickup_crm.md projects/shared/clickup-crm/workflows/

# Create project files
echo "1.0.0-dev" > projects/shared/clickup-crm/VERSION

cat > projects/shared/clickup-crm/README.md <<'EOF'
# ClickUp CRM Operations

**Category**: Shared Multi-Tenant Tool
**Version**: 1.0.0-dev
**Status**: Development

## Overview

ClickUp CRM integration for managing client projects, tasks, and workflows across all companies.

## Usage

\`\`\`bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/clickup-crm
python -m src.clickup_api list-tasks --space "Template Creative Agency"
\`\`\`

## Multi-Tenant Use

This tool is used by:
- Marceau Solutions (internal project management)
- SW Florida HVAC (client project tracking)
- SquareFoot Shipping (lead pipeline management)

## Environment Variables

Required in `.env`:
\`\`\`
CLICKUP_API_TOKEN=your-clickup-api-token
CLICKUP_WORKSPACE_ID=workspace-id
CLICKUP_LIST_ID=default-list-id
\`\`\`
EOF

# Update directive reference
vim directives/clickup_crm.md
# Change: execution/clickup_api.py → projects/shared/clickup-crm/src/clickup_api.py

# Git commit
git add -A
git commit -m "refactor: Move ClickUp integration to shared project structure

Moved from:
  execution/clickup_api.py → projects/shared/clickup-crm/src/
  execution/clickup_oauth.py → projects/shared/clickup-crm/src/

Rationale: ClickUp is multi-tenant tool used across all companies.
Follows company-centric architecture pattern.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Files to Update After Migration

### 1. directives/clickup_crm.md
```markdown
## Tools
- `projects/shared/clickup-crm/src/clickup_api.py` - ClickUp API wrapper
```

### 2. directives/sales_crm.md
```markdown
- `projects/shared/clickup-crm/src/clickup_api.py` - ClickUp API wrapper
```

### 3. Any scripts that import clickup
Search and replace:
```bash
# Find all references
grep -r "from execution.clickup" projects/ --include="*.py"
grep -r "import execution.clickup" projects/ --include="*.py"

# Update imports
# Old: from execution.clickup_api import ClickUpAPI
# New: from projects.shared.clickup_crm.src.clickup_api import ClickUpAPI
# OR: sys.path.insert(0, 'projects/shared/clickup-crm/src')
#     from clickup_api import ClickUpAPI
```

---

## Why This Wasn't Done During Migration

The company-centric migration focused on:
1. Consolidating company folders (websites + projects)
2. Moving external folders into dev-sandbox
3. Renaming shared → shared

It **did not** migrate individual execution scripts to project structure because:
- Not all execution scripts are ready to be projects
- Some are truly one-off utilities
- Migration script focused on folder moves, not code refactoring

**ClickUp integration should be migrated** because:
- Has a directive (directives/clickup_crm.md)
- Multi-tenant (used by multiple companies)
- Non-trivial functionality (9KB + 6KB files)
- Active use case (CRM operations)

---

## Decision Needed

**Question for William**:
1. Should ClickUp integration be in `projects/shared/clickup-crm/` (recommended)?
2. OR should it become an MCP server in `projects/marceau-solutions/clickup-mcp/`?
3. OR keep as-is in `execution/` (old architecture)?

**Recommendation**: Option 1 (shared project) matches the new company-centric pattern.

---

## Other Execution Scripts to Review

Check if these should also migrate:

```bash
ls -la execution/
```

Candidates for migration to `projects/shared/`:
- `clickup_api.py` ← **YES** (discussed above)
- `clickup_oauth.py` ← **YES** (goes with clickup_api)
- Any other multi-tenant tools currently in execution/

Keep in `execution/` if:
- True one-off utility scripts
- Not tied to a specific business capability
- Used by deployment/infrastructure only
