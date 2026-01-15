# Architecture Guide: Two-Tier System

**Purpose**: Comprehensive guide to dev-sandbox architecture, code organization, and decision-making

**Last Updated**: 2026-01-12

---

## Table of Contents

1. [Overview](#overview)
2. [Two-Tier Architecture](#two-tier-architecture)
3. [Decision Trees](#decision-trees)
4. [Code Organization](#code-organization)
5. [Deployment Patterns](#deployment-patterns)
6. [Examples](#examples)
7. [Migration Guide](#migration-guide)

---

## Overview

### The Problem We Solved

**Original confusion**: Mixed shared utilities and project-specific code in `execution/`, unclear where to develop, manual sync needed between folders.

**Solution**: Two-tier architecture with clear separation:
- **Tier 1**: Shared utilities (strict DOE) in `execution/`
- **Tier 2**: Projects (flexible architecture) in `projects/[name]/src/`

### Key Principles

1. **Shared utilities are stable**: Code in `execution/` should have stable APIs and be used by multiple projects
2. **Projects iterate rapidly**: Code in `projects/[name]/src/` can change frequently during development
3. **Clear ownership**: Every script has a clear home (either shared or project-specific)
4. **No duplication**: Code lives in ONE place (source of truth)
5. **Deployment flexibility**: Can deploy from either `execution/` or `projects/[name]/src/`

---

## Two-Tier Architecture

### Tier 1: Shared Utilities (Strict DOE)

**Pattern**: Directive-Orchestration-Execution

```
Layer 1: DIRECTIVE (directives/shared_utilities.md)
Layer 2: ORCHESTRATION (Claude)
Layer 3: EXECUTION (execution/*.py) ← Shared utilities
```

**Characteristics**:
- Used by 2+ projects
- Stable, versioned API
- General-purpose functionality
- Changes infrequently
- Thoroughly tested before updates

**Examples**:
- `gmail_monitor.py` - Email monitoring (used by email-analyzer, notifications, etc.)
- `twilio_sms.py` - SMS sending (used by multiple alert systems)
- `grok_image_gen.py` - Image generation (used by multiple projects)
- `amazon_sp_api.py` - Amazon API client (used by amazon-seller operations)

**Directory structure**:
```
dev-sandbox/
├── directives/
│   └── shared_utilities.md        ← What shared utilities do
├── execution/
│   ├── gmail_monitor.py           ← Shared utility
│   ├── twilio_sms.py              ← Shared utility
│   ├── grok_image_gen.py          ← Shared utility
│   └── amazon_sp_api.py           ← Shared utility
└── docs/
    └── execution-utilities.md     ← Documentation for shared utilities
```

---

### Tier 2: Projects (Flexible Architecture)

**Pattern**: Directive-Implementation (or standalone)

```
Layer 1: DIRECTIVE (directives/[project].md)
Layer 2: ORCHESTRATION (Claude or standalone)
Layer 3: IMPLEMENTATION (projects/[project]/src/*.py) ← Project-specific
```

**Characteristics**:
- Used by 1 project only
- May change frequently during development
- Project-specific logic and workflows
- Can use shared utilities as dependencies
- Tested in project context

**Examples**:
- `md_to_pdf.py` - Markdown to PDF converter (md-to-pdf project only)
- `pptx_generator.py` - PowerPoint generator (interview-prep project only)
- `email_analyzer.py` - Email analysis (email-analyzer project only)

**Directory structure**:
```
dev-sandbox/
├── directives/
│   └── md-to-pdf.md               ← What this project does
├── projects/
│   └── md-to-pdf/
│       ├── src/
│       │   ├── md_to_pdf.py       ← Project implementation
│       │   └── convert.sh         ← Project-specific wrapper
│       ├── workflows/
│       │   └── convert-md-to-pdf.md
│       ├── testing/
│       ├── demos/
│       ├── VERSION
│       ├── CHANGELOG.md
│       └── README.md
└── execution/
    └── [shared utilities it uses]
```

---

## Decision Trees

### Tree 1: Where Should I Put This Code?

```
START: I just wrote some code
│
├─ Will this code be used by 2+ projects?
│  │
│  ├─ YES → Is the API stable?
│  │        │
│  │        ├─ YES → Put in execution/ (Tier 1: Shared Utility)
│  │        │
│  │        └─ NO → Put in projects/[name]/src/ for now
│  │                 Extract to execution/ when stable
│  │
│  └─ NO → Is this project-specific logic?
│           │
│           ├─ YES → Put in projects/[name]/src/ (Tier 2: Project)
│           │
│           └─ UNSURE → Put in projects/[name]/src/ first
│                        Move to execution/ if other projects need it
```

**Default rule**: When in doubt, put in `projects/[name]/src/` first. Extract to `execution/` when you have 2+ projects using it.

---

### Tree 2: Should I Extract This to execution/?

```
START: I have code in projects/[name]/src/
│
├─ Is another project using this code?
│  │
│  ├─ YES → Extract to execution/
│  │        │
│  │        ├─ Create execution/[utility].py
│  │        ├─ Update both projects to import from execution/
│  │        ├─ Document in directives/shared_utilities.md
│  │        └─ Remove from projects/[name]/src/
│  │
│  └─ NO → Could other projects use this?
│           │
│           ├─ YES (general-purpose) → Consider extracting
│           │                           (make API stable first)
│           │
│           └─ NO (project-specific) → Keep in projects/[name]/src/
```

---

### Tree 3: How Do I Deploy This?

```
START: Ready to deploy
│
├─ Is this a shared utility in execution/?
│  │
│  ├─ YES → Deploy as dependency to skills
│  │        python deploy_to_skills.py --shared-utilities
│  │
│  └─ NO → Is this a project in projects/[name]/src/?
│           │
│           └─ YES → Deploy project to skills
│                    python deploy_to_skills.py --project [name] --version X.Y.Z
```

---

## Code Organization

### File Structure: Complete Dev-Sandbox

```
/Users/williammarceaujr./dev-sandbox/          ← ONE git repo
│
├── .git/                                       ← Dev-sandbox repo
├── CLAUDE.md                                   ← Core instructions
│
├── directives/                                 ← Layer 1: What to do
│   ├── shared_utilities.md                    ← Shared utility SOPs
│   ├── md-to-pdf.md                           ← Project-specific SOPs
│   ├── email-analyzer.md
│   └── interview-prep.md
│
├── execution/                                  ← Tier 1: Shared utilities
│   ├── gmail_monitor.py                       ← Used by multiple projects
│   ├── twilio_sms.py                          ← Used by multiple projects
│   ├── grok_image_gen.py                      ← Used by multiple projects
│   ├── amazon_sp_api.py                       ← Used by multiple projects
│   └── README.md                              ← What belongs here
│
├── projects/                                   ← Tier 2: Project implementations
│   ├── md-to-pdf/
│   │   ├── src/
│   │   │   ├── md_to_pdf.py                   ← Project-specific
│   │   │   └── convert.sh                     ← Project-specific wrapper
│   │   ├── workflows/
│   │   ├── testing/
│   │   ├── demos/
│   │   ├── VERSION                            ← 1.0.0-dev
│   │   ├── CHANGELOG.md
│   │   └── README.md
│   │
│   ├── email-analyzer/
│   │   ├── src/
│   │   │   └── email_analyzer.py              ← Project-specific
│   │   ├── workflows/
│   │   ├── testing/
│   │   └── ...
│   │
│   └── interview-prep/
│       ├── src/
│       │   ├── pptx_generator.py              ← Project-specific
│       │   └── interview_research.py          ← Project-specific
│       └── ...
│
├── docs/                                       ← Documentation
│   ├── architecture-guide.md                  ← This file
│   ├── testing-strategy.md                    ← Testing pipeline
│   ├── deployment.md                          ← Deployment process
│   └── ...
│
├── .tmp/                                       ← Temporary files (not committed)
│
└── deploy_to_skills.py                        ← Deployment automation

/Users/williammarceaujr./md-to-pdf-prod/       ← SEPARATE git repo (sibling)
/Users/williammarceaujr./email-analyzer-prod/  ← SEPARATE git repo (sibling)
/Users/williammarceaujr./interview-prep-prod/  ← SEPARATE git repo (sibling)
```

---

### File Structure: execution/ (Shared Utilities Only)

```
execution/
├── README.md                    ← Guidelines for what belongs here
│
├── Communication/
│   ├── gmail_monitor.py         ← Email monitoring
│   ├── twilio_sms.py            ← SMS sending
│   └── slack_notifier.py        ← Slack notifications
│
├── AI & Generation/
│   ├── grok_image_gen.py        ← Image generation
│   └── openai_client.py         ← OpenAI API wrapper
│
├── E-commerce/
│   ├── amazon_sp_api.py         ← Amazon Seller Central API
│   └── shopify_client.py        ← Shopify API wrapper
│
└── Data Processing/
    ├── pdf_utils.py             ← PDF manipulation utilities
    └── csv_processor.py         ← CSV processing utilities
```

**Criteria for inclusion**:
- ✅ Used by 2+ projects
- ✅ Stable API (changes are rare)
- ✅ General-purpose (not project-specific logic)
- ✅ Well-documented
- ✅ Thoroughly tested

---

### File Structure: projects/[name]/ (Project-Specific)

```
projects/md-to-pdf/
├── src/                         ← Project implementation
│   ├── md_to_pdf.py             ← Main script (source of truth)
│   ├── convert.sh               ← Wrapper for environment setup
│   └── config.py                ← Project-specific configuration
│
├── workflows/                   ← How to use this project
│   ├── convert-md-to-pdf.md     ← Basic conversion workflow
│   └── batch-convert.md         ← Batch processing workflow
│
├── testing/                     ← Multi-agent testing
│   ├── TEST-PLAN.md
│   ├── AGENT-PROMPTS.txt
│   ├── agent1/
│   ├── agent2/
│   ├── agent3/
│   ├── agent4/
│   └── consolidated-results/
│
├── demos/                       ← Client demonstrations
│   └── client-acme/
│       └── 2026-01-12/
│
├── .tmp/                        ← Temporary test files (not committed)
│
├── VERSION                      ← 1.0.0-dev
├── CHANGELOG.md                 ← Version history
├── SKILL.md                     ← Skill definition for Claude
└── README.md                    ← User-facing documentation
```

---

## Deployment Patterns

### When to Deploy to Skills

**CRITICAL RULE**: Deploy to skills ONLY after ALL testing is complete

**Complete Testing Pipeline** (see [testing-strategy.md](testing-strategy.md)):
```
1. DEVELOP in dev-sandbox
   ↓
2. Manual Testing (Scenario 1) - ALWAYS REQUIRED
   ↓
3. Multi-Agent Testing (Scenario 2) - OPTIONAL for complex projects
   ↓
4. Pre-Deployment Verification (Scenario 3) - ALWAYS REQUIRED
   ↓
5. DEPLOY to skills ← You are here
   ↓
6. Post-Deployment Verification (Scenario 4) - ALWAYS REQUIRED
```

**Never deploy before**:
- ❌ Manual testing complete
- ❌ Environment issues resolved
- ❌ Multi-agent testing complete (if applicable)
- ❌ Pre-deployment verification passed
- ❌ All critical issues fixed

**Prerequisites for deployment**:
- ✅ Directive exists (`directives/[project].md`)
- ✅ Manual testing passed (Scenario 1)
- ✅ Multi-agent testing passed (if complex, Scenario 2)
- ✅ Pre-deployment verification passed (Scenario 3)
- ✅ All critical issues resolved
- ✅ Documentation updated (README, CHANGELOG, workflows)
- ✅ Version files updated

### Why Post-Deployment Testing is Critical

**The Problem**: Dev-sandbox structure ≠ Production skills structure

**Dev-Sandbox** (`projects/[name]/src/`):
```
dev-sandbox/
├── projects/
│   └── md-to-pdf/
│       ├── src/
│       │   └── md_to_pdf.py          ← You test here
│       ├── workflows/
│       └── testing/
└── execution/
    └── shared_utilities.py            ← Dependencies
```

**Production Skills** (`[name]-prod/execution/`):
```
md-to-pdf-prod/
├── execution/
│   ├── md_to_pdf.py                   ← Deployed here (different path!)
│   └── shared_utilities.py            ← Copied here
├── README.md
└── SKILL.md
```

**What Can Go Wrong**:
1. **Import path issues**: Code imports `from execution.shared_utilities` but file not copied
2. **Relative path issues**: Script uses `./config.json` but path different in production
3. **Missing dependencies**: Shared utilities not included in deployment
4. **Structure assumptions**: Code assumes dev-sandbox folder structure
5. **Environment differences**: Different working directory when running as skill

**Post-Deployment Testing Catches**:
- ✅ Import errors in production structure
- ✅ Missing files/dependencies
- ✅ Path issues (relative vs absolute)
- ✅ Deployment process bugs (files not copied correctly)
- ✅ Documentation errors (commands don't work as documented)

**Real Example**:
```bash
# Works in dev-sandbox
cd /Users/williammarceaujr./dev-sandbox/projects/md-to-pdf
python src/md_to_pdf.py test.md test.pdf  ✅

# Might fail in production if imports broken
cd /Users/williammarceaujr./md-to-pdf-prod
python execution/md_to_pdf.py test.md test.pdf  ❌
# Error: ModuleNotFoundError: No module named 'execution.utils'
```

**Solution**: ALWAYS test in production structure after deployment

---

### Pattern 1: Shared Utility Deployment

**When**: Deploying utilities from `execution/` AFTER testing with all dependent projects

**Process**:
```bash
# 1. Develop in execution/
vim execution/gmail_monitor.py

# 2. Test with ALL projects that use it
python projects/email-analyzer/src/email_analyzer.py  # Uses gmail_monitor
python projects/notifications/src/notify.py           # Also uses gmail_monitor

# 3. Verify no breaking changes
# Test each dependent project thoroughly

# 4. AFTER all testing complete → Deploy shared utility
python deploy_to_skills.py --shared-utilities --version 1.2.0

# 5. Updates all skills that depend on it
```

**Deployment creates**:
- Updates in `/Users/williammarceaujr./[skill]-prod/execution/` folders
- Version tag for shared utilities

---

### Pattern 2: Project Deployment

**When**: Deploying project from `projects/[name]/src/` AFTER complete testing pipeline

**Process**:
```bash
# 1. Develop in projects/[name]/src/
vim projects/md-to-pdf/src/md_to_pdf.py

# 2. TEST PHASE (in dev-sandbox, BEFORE deployment)
# Manual Testing (Scenario 1)
cd projects/md-to-pdf
python src/md_to_pdf.py test.md test.pdf
# Verify output, fix bugs, repeat

# Multi-Agent Testing (Scenario 2) - if complex
# Set up testing/, run agents, consolidate findings, fix critical issues

# Pre-Deployment Verification (Scenario 3)
python src/md_to_pdf.py final-test.md final-test.pdf
# Verify everything works, no crashes, production-ready

# 3. AFTER testing complete → Update version files
# VERSION: 1.0.0-dev → 1.0.0
# CHANGELOG.md: Document changes

# 4. DEPLOY to production
python deploy_to_skills.py --project md-to-pdf --version 1.0.0

# 5. Post-Deployment Verification (Scenario 4)
cd /Users/williammarceaujr./md-to-pdf-prod
python execution/md_to_pdf.py test.md test.pdf
# Verify production deployment works

# 6. Bump dev version
# VERSION: 1.0.0 → 1.1.0-dev
```

**Deployment creates**:
- `/Users/williammarceaujr./md-to-pdf-prod/` (separate git repo)
- Copies from `projects/md-to-pdf/src/` to `-prod/execution/`
- Git tag `v1.0.0` in production repo
- Ready to distribute to end users

**Timeline**:
```
Day 1-3: Development in dev-sandbox
Day 4: Manual testing (Scenario 1)
Day 5-7: Multi-agent testing (Scenario 2) - if complex
Day 8: Fix critical issues from testing
Day 9: Pre-deployment verification (Scenario 3)
Day 10: DEPLOY to skills ← First time skills deployment happens
Day 10: Post-deployment verification (Scenario 4)
```

---

### Pattern 3: Hybrid Deployment (Project + Shared Utilities)

**When**: Project uses shared utilities from `execution/`

**Process**:
```bash
# Project uses shared utilities
# projects/email-analyzer/src/email_analyzer.py imports execution/gmail_monitor.py

# Deploy includes both:
python deploy_to_skills.py --project email-analyzer --version 2.0.0

# Deployment copies:
# - projects/email-analyzer/src/* → email-analyzer-prod/execution/
# - execution/gmail_monitor.py → email-analyzer-prod/execution/ (dependency)
```

---

## Examples

### Example 1: Creating a New Project (Tier 2)

**Scenario**: Building a new resume generator

```bash
# 1. Create directive
vim directives/resume-generator.md
# Define: What it does, SOPs, edge cases

# 2. Create project structure
mkdir -p projects/resume-generator/{src,workflows,testing,demos}

# 3. Develop in src/
vim projects/resume-generator/src/generate_resume.py
# Implementation goes here

# 4. Test manually
cd projects/resume-generator
python src/generate_resume.py input.json output.pdf

# 5. Document workflow
vim workflows/generate-resume.md

# 6. Multi-agent testing (optional, if complex)
# See testing-strategy.md Scenario 2

# 7. Deploy when ready
python deploy_to_skills.py --project resume-generator --version 1.0.0
```

**Result**: Project stays in `projects/resume-generator/src/`, deployed to `/Users/williammarceaujr./resume-generator-prod/`

---

### Example 2: Extracting Shared Utility (Tier 2 → Tier 1)

**Scenario**: PDF generation code is now used by 3 projects

**Before**:
```
projects/resume-generator/src/pdf_utils.py    ← Used here
projects/md-to-pdf/src/pdf_utils.py           ← Duplicated here
projects/invoice-generator/src/pdf_utils.py   ← Duplicated here
```

**After extraction**:
```
execution/pdf_utils.py                        ← Single source of truth

projects/resume-generator/src/generate_resume.py
# from execution.pdf_utils import create_pdf

projects/md-to-pdf/src/md_to_pdf.py
# from execution.pdf_utils import create_pdf

projects/invoice-generator/src/generate_invoice.py
# from execution.pdf_utils import create_pdf
```

**Process**:
```bash
# 1. Move to execution/
cp projects/resume-generator/src/pdf_utils.py execution/pdf_utils.py

# 2. Update all projects to import from execution/
# Edit each project's imports

# 3. Test all projects
python projects/resume-generator/src/generate_resume.py ...
python projects/md-to-pdf/src/md_to_pdf.py ...
python projects/invoice-generator/src/generate_invoice.py ...

# 4. Remove duplicates
rm projects/resume-generator/src/pdf_utils.py
rm projects/md-to-pdf/src/pdf_utils.py
rm projects/invoice-generator/src/pdf_utils.py

# 5. Document in shared utilities directive
vim directives/shared_utilities.md
# Add: pdf_utils.py - PDF generation utilities

# 6. Commit to dev-sandbox
git add execution/pdf_utils.py directives/shared_utilities.md
git add projects/*/src/  # Updated imports
git commit -m "refactor: Extract pdf_utils to shared execution/"
```

---

### Example 3: Project Using Shared Utilities

**Scenario**: Email notification system using multiple shared utilities

**Structure**:
```
execution/                               ← Tier 1: Shared utilities
├── gmail_monitor.py                     ← Used by this project
├── twilio_sms.py                        ← Used by this project
└── slack_notifier.py                    ← Used by this project

projects/notification-system/            ← Tier 2: Project
└── src/
    └── notification_manager.py          ← Orchestrates shared utilities
```

**notification_manager.py**:
```python
# Project-specific orchestration logic
from execution.gmail_monitor import check_inbox
from execution.twilio_sms import send_sms
from execution.slack_notifier import post_message

def process_notifications():
    """Project-specific workflow using shared utilities"""
    emails = check_inbox()  # Shared utility (Tier 1)

    for email in emails:
        # Project-specific logic (Tier 2)
        if email.priority == "urgent":
            send_sms(email.summary)      # Shared utility (Tier 1)
        else:
            post_message(email.summary)  # Shared utility (Tier 1)
```

**Deployment**:
```bash
python deploy_to_skills.py --project notification-system --version 1.0.0
# Copies:
# - projects/notification-system/src/notification_manager.py → prod/execution/
# - execution/gmail_monitor.py → prod/execution/ (dependency)
# - execution/twilio_sms.py → prod/execution/ (dependency)
# - execution/slack_notifier.py → prod/execution/ (dependency)
```

---

## Migration Guide

### Migrating Existing Projects to Two-Tier Architecture

**Phase 1: Audit** (Identify what goes where)

```bash
# List all scripts in execution/
ls -la execution/*.py

# For each script, ask:
# - Is this used by 2+ projects? → Keep in execution/ (Tier 1)
# - Is this used by 1 project? → Move to projects/[name]/src/ (Tier 2)
```

**Phase 2: Move Project-Specific Scripts**

```bash
# Example: email_analyzer.py is only used by email-analyzer project

# 1. Move to project
mkdir -p projects/email-analyzer/src/
git mv execution/email_analyzer.py projects/email-analyzer/src/

# 2. Update any imports (if other files reference it)
# (Usually none, since it's the main script)

# 3. Test
python projects/email-analyzer/src/email_analyzer.py [test-args]

# 4. Commit
git commit -m "refactor: Move email_analyzer to projects/email-analyzer/src/"
```

**Phase 3: Document Shared Utilities**

```bash
# Create/update execution/README.md
vim execution/README.md
```

**Content**:
```markdown
# Shared Utilities (execution/)

## What Belongs Here

Code that meets ALL criteria:
- ✅ Used by 2+ projects
- ✅ Stable API (changes are rare)
- ✅ General-purpose functionality
- ✅ Well-documented
- ✅ Thoroughly tested

## Current Shared Utilities

### Communication
- `gmail_monitor.py` - Email monitoring (used by: email-analyzer, notifications)
- `twilio_sms.py` - SMS sending (used by: alerts, notifications)
- `slack_notifier.py` - Slack integration (used by: notifications, monitoring)

### AI & Generation
- `grok_image_gen.py` - Image generation (used by: social-media, presentations)
- `openai_client.py` - OpenAI API wrapper (used by: chatbot, content-gen)

### E-commerce
- `amazon_sp_api.py` - Amazon API (used by: amazon-seller, inventory)

## Before Adding New Utilities

1. Is it used by 2+ projects? (If no → put in projects/[name]/src/)
2. Is the API stable? (If no → wait until it stabilizes)
3. Is it well-documented? (Add docstrings and examples)
4. Is it tested? (Add tests before extracting)
```

**Phase 4: Update deploy_to_skills.py**

Already supports deploying from both `execution/` and `projects/[name]/src/` (as of Phase 3 implementation plan).

**Phase 5: Update Documentation**

Update all references:
- ✅ CLAUDE.md - Architecture section (done)
- [ ] testing-strategy.md - Artifact locations
- [ ] development-to-deployment.md - Code organization
- [ ] All project READMEs

---

## Troubleshooting

### Q: I have code that MIGHT be used by another project. Where should it go?

**A**: Put it in `projects/[name]/src/` first. Extract to `execution/` when a second project actually needs it. Don't prematurely extract based on "might be used."

---

### Q: My shared utility API changed. How do I update it?

**A**:
1. Update `execution/[utility].py`
2. Test ALL projects that use it
3. Update version and document breaking changes
4. Re-deploy shared utilities: `python deploy_to_skills.py --shared-utilities --version X.Y.Z`

---

### Q: Can I have both project-specific and shared code in the same project?

**A**: Yes! Example:

```
execution/
└── pdf_utils.py                  ← Shared utility (used by many)

projects/resume-generator/
└── src/
    ├── generate_resume.py        ← Project-specific (uses pdf_utils)
    └── resume_templates.py       ← Project-specific
```

---

### Q: What if I need to deploy only the shared utilities?

**A**:
```bash
python deploy_to_skills.py --shared-utilities --version 1.3.0
```

---

### Q: How do I know if something should be in execution/?

**Use this checklist**:
- [ ] Used by 2+ projects currently (not "might be")
- [ ] API is stable (not changing frequently)
- [ ] General-purpose (not project-specific logic)
- [ ] Well-documented (docstrings, examples)
- [ ] Tested (unit tests or proven in production)

**All must be YES to put in execution/. Otherwise → projects/[name]/src/**

---

## Summary

### Key Takeaways

1. **Two tiers, two patterns**:
   - Tier 1 (execution/) = Shared utilities, strict DOE
   - Tier 2 (projects/) = Project code, flexible architecture

2. **Decision rule**: Default to `projects/[name]/src/`, extract to `execution/` when 2+ projects use it

3. **Deployment**: Can deploy from both locations, automatic dependency resolution

4. **Benefits**:
   - Clear organization (no more mixing shared and project-specific)
   - No manual sync (single source of truth for each file)
   - Flexibility (projects can iterate rapidly)
   - Stability (shared utilities change infrequently)

### Related Documentation

- [CLAUDE.md](../CLAUDE.md) - Core operating instructions
- [testing-strategy.md](testing-strategy.md) - Testing pipeline
- [deployment.md](deployment.md) - Deployment process
- [repository-management.md](repository-management.md) - Repository structure
- [COMPREHENSIVE-CONFLICT-AUDIT.md](COMPREHENSIVE-CONFLICT-AUDIT.md) - How we arrived at this solution

---

**Principle**: Keep it simple. Default to project-specific. Extract to shared when proven.
