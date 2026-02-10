# Folder Structure Guide (Hybrid Architecture)

**Purpose**: Maintain consistent company-centric folder organization with proper website deployment as new companies and projects are added

**Last Updated**: 2026-02-09 (Added SOP 32 cross-reference)

> **Prerequisite**: Run **SOP 32 (Project Routing & Classification)** first to determine the project type and general location. This guide provides detailed folder placement AFTER SOP 32 has classified the project.

---

## Current Structure Pattern (Hybrid)

```
projects/
├── [company-name]/                 ← One folder per company
│   ├── README.md                   ← Company overview
│   ├── website/                    ← Git submodule → production repo (if hosted)
│   ├── [project-1]/                ← Company-specific projects (regular folders)
│   ├── [project-2]/
│   └── [project-n]/
│
└── shared/                         ← Multi-tenant tools (serve 2+ companies)
    ├── lead-scraper/
    ├── ai-customer-service/
    ├── social-media-automation/
    └── personal-assistant/
```

**Key Point**: Websites are git submodules, everything else is regular folders.

---

## Decision Tree: Where to Put New Code

### Question 1: Is this for a specific company or multi-tenant?

**For a specific company** (e.g., gym software for "FitLife Gym"):
→ Go to Question 2

**Multi-tenant** (used by 2+ companies):
→ Put in `projects/shared/[project-name]/`
→ Examples:
  - `lead-scraper` - Used by Naples Dental Group, SW Florida HVAC, Square Foot Shipping
  - `ai-customer-service` - Voice AI used by multiple businesses
  - `social-media-automation` - Content scheduling for multiple brands
  - `personal-assistant` - Serves all companies with unified dashboard
→ Structure: Same as company projects (src/, workflows/, VERSION, CHANGELOG.md)
→ Deploy via: `python deploy_to_skills.py --project [name] --version X.Y.Z`
→ See: CLAUDE.md SOPs 1-7 for development/deployment pipeline

---

### Question 2: Do we have a folder for this company?

**YES** (company folder exists):
→ Go to Question 3

**NO** (new company):
→ Create new company folder (see "Creating a New Company" section)

---

### Question 3: Is this a website or a project?

**WEBSITE** (needs public hosting):
→ Create as git submodule (see "Adding a Website" section)

**PROJECT** (automation, tool, backend, etc.):
→ Create as regular folder in `projects/[company-name]/[project-name]/`

---

## Creating a New Company Folder

### Quick Start

```bash
cd /Users/williammarceaujr./dev-sandbox
./scripts/create-company-folder.sh "Company Name"
```

This creates:
```
projects/company-name/
├── README.md                       ← Auto-generated from template
└── .gitkeep                        ← Ensures folder is tracked by git
```

Then choose whether to add a website (submodule) or project (regular folder).

---

## Adding a Website (Git Submodule)

**When to use**: Company needs a public website hosted on GitHub Pages, Netlify, or Vercel

### Step 1: Create Production Repo on GitHub

```bash
# Create the repo (public for GitHub Pages)
gh repo create [CompanyOrg]/company-website --public --description "Company website"

# Example:
# gh repo create MarceauSolutions/naples-dental-group-website --public
```

### Step 2: Clone Production Repo (Outside dev-sandbox)

```bash
cd ~
gh repo clone [CompanyOrg]/company-website

# Example:
# gh repo clone MarceauSolutions/naples-dental-group-website
```

### Step 3: Add Initial Website Files

```bash
cd ~/company-website

# Copy template
cp -r /Users/williammarceaujr./dev-sandbox/.demo-structure-template/website-template/* .

# Customize for company
vim index.html  # Update company name, info, etc.

# Commit and push
git add .
git commit -m "Initial website structure

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push origin main
```

### Step 4: Add as Submodule in dev-sandbox

```bash
cd /Users/williammarceaujr./dev-sandbox

# Add submodule
git submodule add https://github.com/[CompanyOrg]/company-website projects/company-name/website

# Example:
# git submodule add https://github.com/MarceauSolutions/naples-dental-group-website projects/naples-dental-group/website

# Commit the submodule
git commit -m "Add [Company] website as submodule"
git push origin main
```

### Step 5: Configure GitHub Pages (If Using)

```bash
# Enable GitHub Pages on production repo
gh repo edit [CompanyOrg]/company-website --enable-pages --pages-branch main

# Or do it via GitHub web UI:
# 1. Go to repo settings
# 2. Pages section
# 3. Source: main branch
# 4. Save
```

### Result

```
dev-sandbox/projects/company-name/
└── website/  ← Git submodule pointing to production repo

~/company-website/  ← Production repo (outside dev-sandbox)
└── [website files tracked here]
```

**Benefits**:
- Work in dev-sandbox context (alongside other company projects)
- Website deploys automatically to GitHub Pages
- Clean separation: development (dev-sandbox) vs production (website repo)

---

## Adding a Project (Regular Folder)

**When to use**: Automation, backend service, MCP server, tool - anything that's NOT a website

### Step 1: Create Project Folder

```bash
cd projects/company-name
mkdir [project-name]
cd [project-name]
```

### Step 2: Copy Template Structure

```bash
cp -r ../../.demo-structure-template/project-template/* .
```

This creates:
```
projects/company-name/[project-name]/
├── src/                            ← Python source code
├── workflows/                      ← Task procedures (markdown)
├── VERSION                         ← e.g., "1.0.0-dev"
├── CHANGELOG.md                    ← Version history
├── SKILL.md                        ← Skill definition (if deploying)
└── README.md                       ← Project documentation
```

### Step 3: Commit to dev-sandbox

```bash
cd /Users/williammarceaujr./dev-sandbox
git add projects/company-name/[project-name]
git commit -m "feat: Add [project-name] for [Company Name]"
git push origin main
```

**Result**: Regular folder tracked in dev-sandbox repo (NOT a submodule)

---

## Complete Example: Adding Naples Dental Group

### Scenario: New client "Naples Dental Group" needs website + lead automation

```bash
# 1. Create company folder
cd /Users/williammarceaujr./dev-sandbox
./scripts/create-company-folder.sh "Naples Dental Group"

# 2. Create website as submodule
gh repo create NaplesDentalGroup/naples-dental-group-website --public
cd ~
gh repo clone NaplesDentalGroup/naples-dental-group-website
cd naples-dental-group-website
cp -r /Users/williammarceaujr./dev-sandbox/.demo-structure-template/website-template/* .
# Customize index.html, contact.html for dental practice
git add .
git commit -m "Initial dental practice website"
git push origin main

# 3. Add website as submodule
cd /Users/williammarceaujr./dev-sandbox
git submodule add https://github.com/NaplesDentalGroup/naples-dental-group-website projects/naples-dental-group/website
git commit -m "Add Naples Dental Group website as submodule"

# 4. Add lead automation project (regular folder)
cd projects/naples-dental-group
mkdir lead-automation
cd lead-automation
cp -r ../../.demo-structure-template/project-template/* .
# Build the automation tool
cd /Users/williammarceaujr./dev-sandbox
git add projects/naples-dental-group/lead-automation
git commit -m "feat: Add lead automation for Naples Dental Group"

# 5. Push everything
git push origin main
```

**Result**:
```
projects/naples-dental-group/
├── README.md
├── website/                        ← Submodule → NaplesDentalGroup/naples-dental-group-website
└── lead-automation/                ← Regular folder in dev-sandbox
```

---

## Working with Websites (Submodules)

### Editing a Website

```bash
# Navigate to website in company folder
cd /Users/williammarceaujr./dev-sandbox/projects/company-name/website

# Pull latest from production
git pull origin main

# Make changes
vim index.html

# Commit to PRODUCTION repo (because it's a submodule)
git add .
git commit -m "feat: Update homepage hero section"
git push origin main
# ↑ This deploys to GitHub Pages automatically

# Update dev-sandbox submodule reference
cd /Users/williammarceaujr./dev-sandbox
git add projects/company-name/website
git commit -m "chore: Update website submodule"
git push origin main
```

### Updating All Website Submodules

```bash
cd /Users/williammarceaujr./dev-sandbox

# Pull latest from all submodules
git submodule update --remote --merge

# Commit the updates
git add .
git commit -m "chore: Update all website submodules"
git push origin main
```

---

## Working with Projects (Regular Folders)

### Editing a Project

```bash
# Navigate to project
cd /Users/williammarceaujr./dev-sandbox/projects/company-name/project-name

# Make changes
vim src/main.py

# Commit to dev-sandbox (normal git workflow)
cd /Users/williammarceaujr./dev-sandbox
git add projects/company-name/project-name
git commit -m "feat: Add new feature"
git push origin main
```

**No submodule complexity** - just regular git workflow.

---

## When to Use Submodules vs Regular Folders

### Use Git Submodule When:
✅ Public website that needs hosting (GitHub Pages, Netlify, Vercel)
✅ Website needs to be deployed from its own repo
✅ Want clean separation between website and dev code
✅ Multiple people working on just the website

### Use Regular Folder When:
✅ Automation/backend/tool/MCP server
✅ Internal tool that doesn't need separate hosting
✅ Anything that's not a public-facing website
✅ Mockups or non-production sites

**Rule of Thumb**: Only websites are submodules, everything else is regular folders.

---

## Cloning dev-sandbox on New Machine

When cloning dev-sandbox fresh:

```bash
# Clone dev-sandbox
git clone https://github.com/MarceauSolutions/dev-sandbox.git
cd dev-sandbox

# Initialize all submodules (pulls all websites)
git submodule init
git submodule update --recursive

# Now all websites are present
ls projects/marceau-solutions/website  # Works!
```

---

## Checklist: Adding New Company

- [ ] Create company folder: `./scripts/create-company-folder.sh "Company Name"`
- [ ] Update company README.md with business context
- [ ] **If website needed**:
  - [ ] Create GitHub repo: `gh repo create [Org]/company-website --public`
  - [ ] Clone outside dev-sandbox: `cd ~ && gh repo clone [Org]/company-website`
  - [ ] Add initial files and push
  - [ ] Add as submodule: `git submodule add https://github.com/[Org]/company-website projects/company-name/website`
  - [ ] Enable GitHub Pages on website repo
- [ ] **If projects needed**:
  - [ ] Create project folders in `projects/company-name/[project-name]/`
  - [ ] Use template structure
  - [ ] Commit to dev-sandbox
- [ ] Add to `CLAUDE.md` "Current Companies" section
- [ ] Add to deploy_to_skills.py if deploying any projects
- [ ] Configure business_id in shared tools if using multi-tenant tools
- [ ] Git commit: `git add projects/company-name && git commit -m "feat: Add [Company Name] to portfolio"`

---

## Verification Commands

### Check all submodules
```bash
git submodule status
# Shows all website submodules with their commit hashes
```

### List all companies
```bash
ls -d projects/*/
# Shows: projects/marceau-solutions/ projects/swflorida-hvac/ etc.
```

### Check if website is submodule
```bash
cd projects/company-name/website
git remote -v
# Should show the production website repo, not dev-sandbox
```

### Verify no nested repos (except submodules)
```bash
find . -name '.git' -type d
# Should show:
# ./.git (main dev-sandbox repo)
# ./projects/*/website/.git (submodules - these are OK)
```

---

## Common Mistakes to Avoid

❌ **Don't create websites as regular folders if they need hosting**
- Use git submodules for production websites

❌ **Don't create projects as submodules**
- Only websites should be submodules
- Projects, automation, tools = regular folders

❌ **Don't forget to update submodule reference in dev-sandbox**
- After pushing website changes, commit the submodule update in dev-sandbox

❌ **Don't clone production website repos inside dev-sandbox**
- Clone them outside (~/company-website)
- Then add as submodule

---

## Quick Reference

### New Company with Website
```bash
./scripts/create-company-folder.sh "Company"
gh repo create Org/company-website --public
cd ~ && gh repo clone Org/company-website
# Add files, commit, push
cd ~/dev-sandbox
git submodule add https://github.com/Org/company-website projects/company/website
```

### New Company with Project (No Website)
```bash
./scripts/create-company-folder.sh "Company"
cd projects/company && mkdir project-name
cp -r ../.demo-structure-template/project-template/* project-name/
cd ~/dev-sandbox && git add projects/company && git commit -m "Add company"
```

### Edit Website
```bash
cd projects/company/website
# Edit, commit, push (goes to production repo)
cd ~/dev-sandbox && git add projects/company/website && git commit -m "Update submodule"
```

### Edit Project
```bash
cd projects/company/project
# Edit files
cd ~/dev-sandbox && git add . && git commit -m "Update project"
```

---

## See Also

- `docs/HYBRID-ARCHITECTURE-SOLUTION.md` - Why we use this architecture
- `docs/COMPANY-LIFECYCLE-MANAGEMENT.md` - Managing company status changes
- `CLAUDE.md` - Operating principles and SOPs
- `.demo-structure-template/` - Templates for new companies and projects
