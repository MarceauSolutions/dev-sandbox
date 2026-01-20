# Workspace Best Practices - Multi-Company Folder Structure

**Date:** 2026-01-20
**Purpose:** Define optimal workflows for working with categorized project structure

---

## Quick Reference: Which Folder to Open in VSCode?

### Rule of Thumb

**Open the SMALLEST folder that contains everything you need for the current task.**

| Task | Open in VSCode | Why |
|------|---------------|-----|
| **Working on single company** | `projects/marceau-solutions/` | Focused context, faster search, less clutter |
| **Working on single project** | `projects/shared-multi-tenant/lead-scraper/` | Maximum focus, project-specific terminal |
| **Working across companies** | Root (`dev-sandbox/`) | Full access, can navigate between companies |
| **Updating SOPs/docs** | Root (`dev-sandbox/`) | Need access to docs/, directives/, methods/ |
| **Debugging deployment** | Root (`dev-sandbox/`) | Need deploy_to_skills.py + all projects |
| **Code review across projects** | Root (`dev-sandbox/`) | Compare implementations |

---

## Workflow Scenarios

### Scenario 1: Working on Marceau Solutions Business

**Context:** Building new features for Marceau's AI automation business

**Best Practice:**
```bash
# Open VSCode at company level
code /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/

# Start Claude Code instance
# Claude automatically has context for:
# - All Marceau projects (fitness-influencer, website-builder, etc.)
# - Marceau-specific docs (when we create docs/companies/marceau-solutions/)
# - Product ideas folder (visible from parent)
```

**Benefits:**
- ✅ Fast file search (only Marceau projects)
- ✅ Terminal already in right directory for testing
- ✅ No confusion with HVAC/Shipping code
- ✅ Git commands still work (repo at root)

**Claude Communication:**
```
User: "Update the fitness influencer video editor"
Claude: Knows to look in marceau-solutions/fitness-influencer/src/
```

---

### Scenario 2: Working on Shared Multi-Tenant Systems

**Context:** Improving lead-scraper or social-media-automation used by all 3 businesses

**Best Practice:**
```bash
# Option A: Open the specific project (RECOMMENDED)
code /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper/

# Option B: Open shared-multi-tenant category
code /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/
```

**Why Option A (single project):**
- Working on lead-scraper rarely requires seeing social-media-automation code
- Faster search, cleaner terminal
- Can still access other projects via parent (`../social-media-automation/`)

**Claude Communication:**
```
User: "Add new pain point detection to lead scraper"
Claude: Focused on lead-scraper/src/, no distractions
```

**When to use Option B (category):**
- Refactoring shared logic between lead-scraper and social-media-automation
- Comparing implementations across multi-tenant projects

---

### Scenario 3: Multi-Company Campaign Management

**Context:** Running SMS campaigns for Marceau + HVAC simultaneously

**Best Practice:**
```bash
# Open root to see all company context
code /Users/williammarceaujr./dev-sandbox/

# Open terminal in lead-scraper
cd projects/shared-multi-tenant/lead-scraper/
```

**Why root:**
- Need to verify business_id separation across companies
- Compare templates between Marceau/HVAC
- Access campaign analytics that spans all 3 businesses

**Claude Communication:**
```
User: "Run SMS campaign for Marceau and HVAC, use different templates"
Claude: Can see both company contexts, templates, and business configs
```

---

### Scenario 4: Architecture/SOP Updates

**Context:** Updating CLAUDE.md, docs/, or directives/

**Best Practice:**
```bash
# ALWAYS open root for infrastructure work
code /Users/williammarceaujr./dev-sandbox/
```

**Why:**
- docs/, directives/, methods/ are at root
- SOPs reference multiple projects
- Need full context to ensure consistency

**Claude Communication:**
```
User: "Update SOP 18 with new campaign workflow"
Claude: Needs to see CLAUDE.md, docs/, and projects/shared-multi-tenant/lead-scraper/
```

---

### Scenario 5: New Project Creation

**Context:** Starting a new project, unsure which company it belongs to

**Best Practice:**
```bash
# Open root during planning phase
code /Users/williammarceaujr./dev-sandbox/

# Start Claude, run SOP 0 (Project Kickoff)
# Determine: Which company? Shared? Global utility? Product idea?

# Once decided, can narrow focus:
code /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/new-project/
```

**SOP 1 Updated (New Project Initialization):**

After determining app type and company (SOP 0), create project in correct category:

```markdown
## Step 1: Choose Project Category

**Question:** Which category does this project belong to?

| Category | When to Use | Example |
|----------|-------------|---------|
| `shared-multi-tenant/` | Used by 2+ businesses | lead-scraper, voice AI |
| `marceau-solutions/` | Marceau-only service | fitness-influencer, website-builder |
| `swflorida-hvac/` | HVAC-only | hvac-distributors |
| `square-foot-shipping/` | Shipping-only | (none yet) |
| `global-utility/` | No business affiliation | md-to-pdf, twilio-mcp |
| `product-ideas/` | Future Marceau product | crave-smart, decide-for-her |

## Step 2: Create Project Folder

```bash
# Example: New Marceau project
mkdir -p projects/marceau-solutions/new-project/src
mkdir -p projects/marceau-solutions/new-project/workflows

# Create VERSION file
echo "1.0.0-dev" > projects/marceau-solutions/new-project/VERSION
```
```

---

### Scenario 6: Deployment & Testing

**Context:** Deploying projects to production, running multi-agent testing

**Best Practice:**
```bash
# Open root (deploy_to_skills.py is at root)
code /Users/williammarceaujr./dev-sandbox/

# Deploy from root
python deploy_to_skills.py --project lead-scraper --version 1.2.0
```

**Why root:**
- deploy_to_skills.py needs to scan all project categories
- Verification requires checking multiple projects
- Git commits happen at root

---

## VSCode Workspace Files (Advanced)

### Multi-Root Workspaces for Complex Tasks

For tasks spanning multiple companies, create a VSCode workspace file:

**`dev-sandbox-all-companies.code-workspace`**
```json
{
  "folders": [
    {
      "name": "Shared (Multi-Tenant)",
      "path": "projects/shared-multi-tenant"
    },
    {
      "name": "Marceau Solutions",
      "path": "projects/marceau-solutions"
    },
    {
      "name": "SW Florida HVAC",
      "path": "projects/swflorida-hvac"
    },
    {
      "name": "Square Foot Shipping",
      "path": "projects/square-foot-shipping"
    },
    {
      "name": "Infrastructure (docs, directives, execution)",
      "path": "."
    }
  ],
  "settings": {
    "files.exclude": {
      "**/node_modules": true,
      "**/__pycache__": true,
      "**/.pytest_cache": true
    }
  }
}
```

**When to use:**
- Working on multi-company feature (e.g., unified lead attribution)
- Refactoring shared logic
- Comparing implementations across companies

**How to open:**
```bash
code dev-sandbox-all-companies.code-workspace
```

---

## Terminal Best Practices

### Working Directory Strategy

**Rule:** Always `cd` to the project you're working on, even if VSCode is open at root

```bash
# VSCode opened at root
code /Users/williammarceaujr./dev-sandbox/

# But terminal in specific project
cd projects/shared-multi-tenant/lead-scraper/

# Run commands relative to project
python -m src.scraper sms --dry-run
```

**Why:**
- Relative imports work correctly
- `python -m` resolves to right package
- Less typing for file paths

---

## Claude Code Best Practices

### Context Awareness

**When Claude starts, tell it your focus:**

```
User: "I'm working on Marceau's fitness influencer project today"
Claude: Sets mental context, prioritizes fitness-influencer/ files in searches
```

**OR (for multi-company work):**

```
User: "I need to update lead scraping for all 3 businesses"
Claude: Knows to check shared-multi-tenant/lead-scraper/ and business configs
```

### File References

**Use category-aware paths:**

```
User: "Update the lead scraper's campaign analytics"
Claude: Looks in projects/shared-multi-tenant/lead-scraper/src/campaign_analytics.py
```

**NOT:**
```
User: "Update campaign_analytics.py"  # Too vague - which project?
```

---

## Git Workflow

### Commits: Always from Root

```bash
# Even if VSCode is in projects/marceau-solutions/
cd /Users/williammarceaujr./dev-sandbox/

git add .
git commit -m "feat(fitness-influencer): Add new video editing feature"
git push
```

**Why:**
- Single repo at root
- Git can see all changes across categories
- Cleaner history

### Branch Strategy (Future Consideration)

For large multi-company features:

```bash
# Create feature branch at root
git checkout -b feature/multi-company-lead-attribution

# Work across companies
# projects/shared-multi-tenant/lead-scraper/
# projects/marceau-solutions/
# projects/swflorida-hvac/

# Commit everything together
git commit -m "feat: Unified lead attribution across all 3 companies"
```

---

## Communication Patterns: Updated

### New Patterns for Categorized Structure

| User Says | Claude Interprets | Opens/Searches |
|-----------|-------------------|----------------|
| "Work on Marceau today" | Focus on marceau-solutions/ | projects/marceau-solutions/ |
| "Update shared lead scraper" | Multi-tenant system | projects/shared-multi-tenant/lead-scraper/ |
| "Check HVAC projects" | HVAC-specific work | projects/swflorida-hvac/ |
| "Compare all 3 businesses" | Cross-company analysis | Root (all categories) |
| "Update global docs" | Infrastructure | docs/, directives/, methods/ |

### Explicit Category References

**Encourage user to specify category when ambiguous:**

```
User: "Update the social media automation"
Claude: "Which one - the shared multi-tenant version, or Marceau-specific?"

Better:
User: "Update the shared social media automation"
Claude: ✅ projects/shared-multi-tenant/social-media-automation/
```

---

## VSCode Extensions & Settings

### Recommended Extensions for Categorized Structure

**1. Project Manager** (alefragnani.project-manager)
- Save each category as a project
- Quick switch: Cmd+Shift+P → "Project Manager: List"

**2. Multi-root Workspace Support** (built-in)
- Open multiple categories simultaneously

**3. Better Comments** (aaron-bond.better-comments)
- Annotate code with company context:
```python
# ! MARCEAU-SPECIFIC: This logic only applies to AI automation business
# ? SHARED: Used by all 3 companies - test thoroughly!
```

### VSCode Settings for Category-Aware Search

**`.vscode/settings.json`** (at root):
```json
{
  "search.exclude": {
    "**/node_modules": true,
    "**/__pycache__": true,
    "**/archived": true  // Ignore archived projects
  },
  "files.watcherExclude": {
    "**/archived/**": true
  },
  "search.quickOpen.includeSymbols": true,
  "explorer.compactFolders": false  // Show full category path
}
```

---

## Folder Opening Decision Tree

```
START: What am I doing today?
│
├─ Working on 1 company only?
│  └─ YES → Open projects/[company-name]/
│     └─ Working on 1 project within that company?
│        └─ YES → Open projects/[company]/[project]/ (max focus)
│        └─ NO → Open projects/[company]/ (compare projects)
│
├─ Working on shared system (lead-scraper, social-media)?
│  └─ YES → Open projects/shared-multi-tenant/[project]/
│
├─ Working on infrastructure (docs, SOPs, deploy)?
│  └─ YES → Open ROOT
│
├─ Working across multiple companies?
│  └─ YES → Open ROOT or use multi-root workspace
│
└─ Unsure / exploring?
   └─ Open ROOT (can navigate down later)
```

---

## Examples: Real Scenarios

### Example 1: "Add new SMS template for Marceau"

**Optimal Workflow:**
```bash
# Open Marceau category (not root, not single project)
code /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/

# Claude has context for:
# - All Marceau projects
# - Can reference fitness-influencer templates
# - Can see website-builder messaging

# Terminal
cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper/
# (SMS templates are in shared lead-scraper, but Marceau context helps)
```

**User → Claude:**
```
"Add new SMS template for Marceau's no-website pain point, similar style to fitness-influencer messaging"

Claude:
1. Looks at marceau-solutions/fitness-influencer/ for tone
2. Creates template in shared-multi-tenant/lead-scraper/templates/sms/
3. Tags with business_id = "marceau-solutions"
```

### Example 2: "Run campaigns for all 3 companies"

**Optimal Workflow:**
```bash
# Open root (need all company context)
code /Users/williammarceaujr./dev-sandbox/

# Claude has context for:
# - All 3 company configs
# - Shared lead-scraper
# - Business-specific templates
```

**User → Claude:**
```
"Run SMS campaigns: Marceau (no-website), HVAC (low-reviews), Shipping (new-service)"

Claude:
1. Verifies business_id configs for all 3
2. Checks templates for each pain point
3. Runs campaigns with proper separation
4. Generates separate analytics per business
```

### Example 3: "Debug deployment issue"

**Optimal Workflow:**
```bash
# Always root for deployment
code /Users/williammarceaujr./dev-sandbox/

# Claude needs:
# - deploy_to_skills.py
# - All project categories
# - Git status
```

**User → Claude:**
```
"Deployment failed for fitness-influencer, says file not found"

Claude:
1. Checks deploy_to_skills.py project discovery
2. Verifies projects/marceau-solutions/fitness-influencer/ exists
3. Checks VERSION file, SKILL.md
4. Runs --dry-run to diagnose
```

---

## Migration Transition Period

### First 2 Weeks After Migration

**Expect muscle memory issues:**
- Typing `cd projects/lead-scraper` instead of `cd projects/shared-multi-tenant/lead-scraper`
- Opening root when you only need one company
- Forgetting which category a project belongs to

**Solutions:**
1. Create shell aliases:
```bash
# Add to ~/.zshrc or ~/.bashrc
alias goto-marceau="cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions"
alias goto-shared="cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant"
alias goto-hvac="cd /Users/williammarceaujr./dev-sandbox/projects/swflorida-hvac"
alias goto-shipping="cd /Users/williammarceaujr./dev-sandbox/projects/square-foot-shipping"
```

2. Create README.md at old locations:
```bash
# projects/lead-scraper/README.md (if someone tries old path)
echo "⚠️ MOVED: This project is now at projects/shared-multi-tenant/lead-scraper/" > projects/lead-scraper-MOVED.txt
```

3. VSCode Recent Projects (first 2 weeks):
- Manually open each category once
- VSCode remembers recent folders
- Quick switch via Cmd+R (recent)

---

## Summary: Golden Rules

1. **🎯 Open smallest folder that contains your task**
   - Single project > Category > Root

2. **🏢 Know your companies**
   - Marceau = AI automation (most projects)
   - HVAC = Service business (1 project)
   - Shipping = Logistics (0 projects yet)
   - Shared = Used by all 3

3. **📂 Category-aware file paths**
   - Always include category in discussions: "shared lead-scraper", "Marceau fitness-influencer"

4. **💻 Terminal follows focus**
   - Even if VSCode is at root, cd to active project

5. **🔧 Infrastructure work = Root**
   - docs/, SOPs, deploy, git commits

6. **🚀 Deployment = Root**
   - deploy_to_skills.py scans all categories

7. **🧠 Tell Claude your context**
   - "Working on Marceau today" sets focus
   - "Multi-company campaign" opens full context

---

## Next Steps

**After Migration:**
1. Create VSCode workspace files for common scenarios
2. Add shell aliases for quick navigation
3. Update SOP 1 with category selection step
4. Practice new workflows for 2 weeks
5. Refine based on actual usage patterns

**Create Workspace Files:**
```bash
# After migration, run:
python ralph/create_vscode_workspaces.py

# Generates:
# - dev-sandbox-all-companies.code-workspace
# - dev-sandbox-marceau.code-workspace
# - dev-sandbox-shared.code-workspace
# - dev-sandbox-infrastructure.code-workspace
```

---

**Document Version:** 1.0.0
**Created:** 2026-01-20
**To Be Updated:** After migration, based on real usage
