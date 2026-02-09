# Folder Structure Guide

**Purpose**: Maintain consistent company-centric folder organization as new companies and projects are added

**Last Updated**: 2026-01-21

---

## Current Structure Pattern

```
projects/
├── [company-name]/                 ← One folder per company
│   ├── README.md                   ← Company overview
│   ├── website/                    ← Company website (if applicable)
│   ├── [project-1]/                ← Company-specific projects
│   ├── [project-2]/
│   └── [project-n]/
│
└── shared/                         ← Multi-tenant tools (serve 2+ companies)
    ├── lead-scraper/
    ├── ai-customer-service/
    ├── social-media-automation/
    └── personal-assistant/
```

---

## Decision Tree: Where to Put New Code

### Question 1: Is this for a specific company or multi-tenant?

**For a specific company** (e.g., gym software for "FitLife Gym"):
→ Go to Question 2

**Multi-tenant** (e.g., lead scraper used by 3+ companies):
→ Put in `projects/shared/[project-name]/`

---

### Question 2: Do we have a folder for this company?

**YES** (company folder exists):
→ Put in `projects/[company-name]/[project-name]/`

**NO** (new company):
→ Create new company folder using template (see below)

---

## Creating a New Company Folder

### Step 1: Use the Template Script

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

### Step 2: Add First Project

```bash
cd projects/company-name
mkdir [project-name]
cd [project-name]

# Copy project template structure
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

### Step 3: Add Website (if applicable)

If the company has a website:

```bash
cd projects/company-name
mkdir website
cd website

# Copy website template structure
cp -r ../../.demo-structure-template/website-template/* .
```

This creates:
```
projects/company-name/website/
├── index.html                      ← Homepage
├── contact.html                    ← Contact form
├── assets/                         ← CSS, JS, images
├── forms/                          ← Form handlers
└── README.md                       ← Website documentation
```

---

## Manual Creation (Without Scripts)

If you prefer manual creation:

### Step 1: Create Company Folder

```bash
cd /Users/williammarceaujr./dev-sandbox/projects
mkdir [company-name]
cd [company-name]
```

### Step 2: Create README.md

Copy this template:

```markdown
# [Company Name]

**Business Type**: [e.g., HVAC Services, E-commerce, SaaS]
**Primary Contact**: [Name, Email, Phone]
**Website**: [URL if exists]

## Overview

[Brief description of company and relationship]

## Projects

### [Project 1 Name]
- **Purpose**: [What this project does]
- **Status**: [Development, Production, Archived]
- **Version**: [Current version]

### website/
- **Purpose**: Company website and landing pages
- **URL**: [Live URL]
- **Stack**: [HTML/CSS/JS, React, etc.]

## Business Context

**Industry**: [Industry]
**Target Market**: [B2B, B2C, Local, National]
**Revenue Model**: [How they make money]

## Automation Tools Used

- [ ] Lead Scraper (projects/shared/lead-scraper)
- [ ] AI Customer Service (projects/shared/ai-customer-service)
- [ ] Social Media Automation (projects/shared/social-media-automation)
- [ ] Personal Assistant (projects/shared/personal-assistant)

## Notes

[Any important context about this company or relationship]
```

### Step 3: Add Projects as Needed

For each project under this company:

```bash
mkdir [project-name]
cd [project-name]

# Create basic structure
mkdir src workflows
touch VERSION CHANGELOG.md README.md SKILL.md
echo "1.0.0-dev" > VERSION
```

---

## Examples: Current Companies

### Marceau Solutions (Our Company)
```
projects/marceau-solutions/
├── README.md
├── website/                        ← marceausolutions.com
├── amazon-seller/                  ← MCP for Amazon Seller Central
├── fitness-influencer/             ← Fitness creator tools
│   ├── backend/
│   ├── frontend/
│   └── mcp/
├── interview-prep/                 ← Interview prep PPTX generator
├── website-builder/                ← Website generation tool
└── [8 other projects]
```

### SW Florida Comfort HVAC (Client)
```
projects/swflorida-hvac/
├── README.md
├── website/                        ← swflorida-comfort-hvac.com
└── hvac-distributors/              ← Distributor comparison tool
```

### SquareFoot Shipping (Client)
```
projects/square-foot-shipping/
├── README.md
├── website/                        ← squarefoot-shipping.com
└── lead-gen/                       ← Lead generation automation
```

---

## Project Types & Where They Go

### Type 1: Company Website
**Location**: `projects/[company-name]/website/`
**Contents**: HTML, CSS, JS, contact forms, landing pages
**Example**: `projects/swflorida-hvac/website/`

### Type 2: Custom Automation (Company-Specific)
**Location**: `projects/[company-name]/[automation-name]/`
**Contents**: Python scripts, workflows, config
**Example**: `projects/swflorida-hvac/hvac-distributors/`

### Type 3: SaaS Product (Internal Product)
**Location**: `projects/marceau-solutions/[product-name]/`
**Contents**: Full application code (backend, frontend, etc.)
**Example**: `projects/marceau-solutions/fitness-influencer/`

### Type 4: MCP Server (Claude Integration)
**Location**: `projects/marceau-solutions/[mcp-name]/` or `projects/[company]/[mcp-name]/`
**Contents**: MCP server code, PyPI package structure
**Example**: `projects/marceau-solutions/amazon-seller/`

### Type 5: Multi-Tenant Tool (Shared)
**Location**: `projects/shared/[tool-name]/`
**Contents**: Python scripts with business_id separation
**Example**: `projects/shared/lead-scraper/`
**When to use**: Tool is used by 2+ companies with business_id parameter

---

## Adding a Project to deploy_to_skills.py

When creating a new project that will be deployed as a skill:

### Step 1: Add to deploy_to_skills.py

Edit `/Users/williammarceaujr./dev-sandbox/deploy_to_skills.py`:

```python
PROJECTS = {
    # ... existing projects ...

    "[project-name]": {
        "path": "projects/[company-name]/[project-name]",
        "skill_name": "[project-name]",
        "category": "[company-name]",  # or "shared" for multi-tenant
        "prod_path": Path.home() / "[project-name]-prod",
        "files_to_copy": ["src", "workflows", "VERSION", "CHANGELOG.md", "SKILL.md", "README.md"],
    },
}
```

### Step 2: Verify Detection

```bash
python deploy_to_skills.py --list
# Should show your new project
```

---

## Updating CLAUDE.md for New Companies

When adding a new company, update the "Where to Put Things" section in CLAUDE.md:

```markdown
## Current Companies

1. **Marceau Solutions** (Our Company)
   - Location: `projects/marceau-solutions/`
   - Assets: Website + 11 internal products

2. **SW Florida Comfort HVAC** (Client)
   - Location: `projects/swflorida-hvac/`
   - Assets: Website + HVAC distributor tool

3. **SquareFoot Shipping** (Client)
   - Location: `projects/square-foot-shipping/`
   - Assets: Website + lead generation

4. **[NEW COMPANY]** (Client/Partner)
   - Location: `projects/[new-company]/`
   - Assets: [List what's included]
```

---

## Common Scenarios

### Scenario 1: New Client Onboarding

**Situation**: Just signed "Naples Dental Group" as a new client

**Steps**:
1. Create company folder: `./scripts/create-company-folder.sh "Naples Dental Group"`
2. Add their website: `cd projects/naples-dental-group && mkdir website`
3. Build first project: `mkdir lead-gen && cd lead-gen && [create project structure]`
4. Update their README.md with business context
5. Add to deploy_to_skills.py if deploying

**Result**:
```
projects/naples-dental-group/
├── README.md
├── website/
└── lead-gen/
```

---

### Scenario 2: New Internal Product

**Situation**: Building new "Email Marketing Automation" tool for Marceau Solutions

**Steps**:
1. `cd projects/marceau-solutions`
2. `mkdir email-marketing && cd email-marketing`
3. Copy project template structure
4. Start coding in `src/`
5. Add to deploy_to_skills.py when ready

**Result**:
```
projects/marceau-solutions/
├── [existing projects...]
└── email-marketing/          ← NEW
    ├── src/
    ├── workflows/
    └── [standard project files]
```

---

### Scenario 3: Multi-Tenant Tool

**Situation**: Built lead scraper that 3 companies use

**Steps**:
1. Start in company-specific location: `projects/[company-name]/lead-gen/`
2. When 2nd company needs it, move to shared: `projects/shared/lead-scraper/`
3. Add business_id parameter to all functions
4. Update all 3 companies to call shared tool with their business_id

**Result**:
```
projects/shared/lead-scraper/
└── src/
    └── scraper.py    # Has business_id parameter
```

---

## Checklist for New Company

When adding a new company, use this checklist:

- [ ] Create company folder: `projects/[company-name]/`
- [ ] Create README.md with business context
- [ ] Add website folder (if applicable): `projects/[company-name]/website/`
- [ ] Add first project folder
- [ ] Update CLAUDE.md "Current Companies" section
- [ ] Add to deploy_to_skills.py (if deploying)
- [ ] Configure business_id in shared tools (if using multi-tenant tools)
- [ ] Add company to `.env` if they need separate API keys
- [ ] Git commit: `git add projects/[company-name] && git commit -m "feat: Add [Company Name] to portfolio"`

---

## Maintaining the Pattern

### DO:
✅ Group all company assets in single folder
✅ Use kebab-case for folder names (`sw-florida-hvac`)
✅ Create README.md for each company explaining context
✅ Put websites in `[company]/website/` subfolder
✅ Use `projects/shared/` for multi-tenant tools only

### DON'T:
❌ Scatter company assets across multiple locations
❌ Put company-specific code in `projects/shared/`
❌ Create nested git repositories (no `git init` inside projects/)
❌ Use spaces in folder names ("SW Florida HVAC" → "swflorida-hvac")

---

## Quick Reference Commands

```bash
# List all companies
ls -d projects/*/

# Create new company
./scripts/create-company-folder.sh "Company Name"

# Create new project in existing company
cd projects/[company-name]
mkdir [project-name] && cd [project-name]
cp -r ../../.demo-structure-template/project-template/* .

# Check deploy_to_skills.py recognizes new project
python deploy_to_skills.py --list

# Verify no nested repos
find . -name '.git' -type d
# Should only show: ./.git
```

---

## Template Files Location

All templates are stored in:
```
.demo-structure-template/
├── project-template/           ← For new projects
│   ├── src/
│   ├── workflows/
│   ├── VERSION
│   ├── CHANGELOG.md
│   ├── SKILL.md
│   └── README.md
│
├── website-template/           ← For new company websites
│   ├── index.html
│   ├── contact.html
│   ├── assets/
│   └── README.md
│
└── company-readme-template.md  ← For new company README
```

---

## See Also

- `CLAUDE.md` - Operating principles and SOPs
- `docs/architecture-guide.md` - Code organization rules
- `docs/repository-management.md` - Git structure guidelines
- `scripts/create-company-folder.sh` - Company folder creation script
