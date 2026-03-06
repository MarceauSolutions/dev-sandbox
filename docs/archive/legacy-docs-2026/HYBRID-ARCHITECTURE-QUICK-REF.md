# Hybrid Architecture Quick Reference

**Last Updated**: 2026-01-21

## What This Is

Company-centric folder structure + Website git submodules = Best of both worlds

## Directory Structure

```
dev-sandbox/ (main development repo)
├── projects/
│   ├── marceau-solutions/        ← All Marceau assets
│   │   ├── website/              ← Git submodule → marceausolutions.com
│   │   ├── amazon-seller/        ← Regular folder
│   │   ├── fitness-influencer/   ← Regular folder
│   │   └── [8 other projects]
│   │
│   ├── swflorida-hvac/           ← All HVAC assets
│   │   ├── website/              ← Git submodule → swflorida-comfort-hvac
│   │   └── hvac-distributors/    ← Regular folder
│   │
│   └── shared/                   ← Multi-tenant tools
│       ├── lead-scraper/
│       ├── ai-customer-service/
│       └── social-media-automation/
│
└── scripts/
    ├── create-company-folder.sh  ← Add new company
    └── add-company-project.sh    ← Add project to company
```

## Quick Commands

### Add a New Company

```bash
cd /Users/williammarceaujr./dev-sandbox
./scripts/create-company-folder.sh "Company Name"
```

### Add a Project to Existing Company

```bash
# Add a tool/automation
./scripts/add-company-project.sh company-name "project-name" tool

# Add an MCP server
./scripts/add-company-project.sh company-name "mcp-server" mcp

# Add workflows/documentation
./scripts/add-company-project.sh company-name "procedures" workflow
```

### Add a Website (as submodule)

```bash
# 1. Create GitHub repo
gh repo create [CompanyOrg]/company-website --public

# 2. Clone OUTSIDE dev-sandbox
cd ~
gh repo clone [CompanyOrg]/company-website

# 3. Add initial files
cd ~/company-website
cp -r /Users/williammarceaujr./dev-sandbox/.demo-structure-template/website-template/* .
git add . && git commit -m "Initial website" && git push origin main

# 4. Add as submodule IN dev-sandbox
cd /Users/williammarceaujr./dev-sandbox
git submodule add https://github.com/[CompanyOrg]/company-website projects/company-name/website
git commit -m "Add company website as submodule"
git push origin main
```

### Edit a Website

```bash
# Navigate to website submodule
cd projects/company-name/website

# Make changes
vim index.html

# Commit to PRODUCTION repo (because it's a submodule)
git add .
git commit -m "feat: Update homepage"
git push origin main  # ← Deploys to GitHub Pages

# Update dev-sandbox to reference new commit
cd /Users/williammarceaujr./dev-sandbox
git add projects/company-name/website
git commit -m "chore: Update website submodule"
git push origin main
```

### Edit a Project (non-website)

```bash
# Navigate to project
cd projects/company-name/project-name

# Make changes
vim src/main.py

# Commit to dev-sandbox (regular git workflow)
cd /Users/williammarceaujr./dev-sandbox
git add projects/company-name/project-name
git commit -m "feat: Add feature"
git push origin main
```

## Key Differences

| Item | Website | Project |
|------|---------|---------|
| **Type** | Git submodule | Regular folder |
| **Location in dev-sandbox** | `projects/company/website/` | `projects/company/project/` |
| **Production repo** | Separate (e.g., marceausolutions.com) | None (tracked in dev-sandbox) |
| **Deployment** | GitHub Pages (automatic) | Via deploy_to_skills.py |
| **Git workflow** | Commit to submodule → update dev-sandbox | Commit to dev-sandbox directly |
| **When to use** | Public website needing hosting | Automation, tools, backends, MCPs |

## Verification Commands

```bash
# Check submodule status
git submodule status

# Update all submodules to latest
git submodule update --remote --merge

# Check for nested repos (should only show ./.git and submodules)
find . -name ".git" -type d

# List all companies
ls -d projects/*/
```

## Common Workflows

### Clone dev-sandbox on New Machine

```bash
git clone https://github.com/MarceauSolutions/dev-sandbox.git
cd dev-sandbox

# Initialize all submodules (pulls websites)
git submodule init
git submodule update --recursive

# All websites now present!
```

### Add New Service to Multi-Tenant Tool

```bash
# If 2+ companies use this tool, put in projects/shared/
cd projects/shared/lead-scraper
# Make changes

# Commit to dev-sandbox
cd /Users/williammarceaujr./dev-sandbox
git add projects/shared/lead-scraper
git commit -m "feat(lead-scraper): Add feature"
```

## Benefits

✅ **Company-Centric**: All client assets in one folder
✅ **Proper Deployment**: Websites have separate repos for hosting
✅ **Development Convenience**: Work on everything in dev-sandbox context
✅ **No Manual Sync**: Changes to websites automatically reference production
✅ **Future-Proof**: Scripts ensure pattern is maintained for new companies

## Documentation

- **Full Guide**: [docs/FOLDER-STRUCTURE-GUIDE.md](FOLDER-STRUCTURE-GUIDE.md)
- **Hybrid Architecture Details**: [docs/HYBRID-ARCHITECTURE-SOLUTION.md](HYBRID-ARCHITECTURE-SOLUTION.md)
- **Company Lifecycle**: [docs/COMPANY-LIFECYCLE-MANAGEMENT.md](COMPANY-LIFECYCLE-MANAGEMENT.md)

---

**Created**: 2026-01-21
**Scripts**: `scripts/create-company-folder.sh`, `scripts/add-company-project.sh`
