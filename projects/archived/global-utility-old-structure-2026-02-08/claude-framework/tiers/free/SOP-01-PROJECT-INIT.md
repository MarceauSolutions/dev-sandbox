# SOP 1: Project Initialization

**When**: Starting any new AI-assisted development project

## Purpose

Establish a consistent project structure that enables effective collaboration with Claude. A well-organized project allows Claude to understand context faster and produce better results.

## Prerequisites

- Working development environment
- Git installed (optional but recommended)
- Claude Code or Claude access

## Steps

### Step 1: Create Project Directory

```bash
mkdir -p your-project/{src,workflows,docs}
cd your-project
```

### Step 2: Initialize Version Control

```bash
git init
echo ".tmp/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
```

### Step 3: Create Core Files

**VERSION**
```
1.0.0-dev
```

**CHANGELOG.md**
```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial project structure
```

**README.md**
```markdown
# Project Name

Brief description of what this project does.

## Setup

How to get started.

## Usage

How to use the project.
```

### Step 4: Copy CLAUDE.md

Copy the CLAUDE.md template to your project root and customize:

1. Update `## Project Overview` with your project details
2. Update `## Architecture` with your directory structure
3. Add project-specific communication patterns

### Step 5: Create Initial Workflow

Create your first workflow document:

```bash
touch workflows/main-workflow.md
```

Document your primary task flow as you complete it.

### Step 6: Start Your First Session

```bash
claude  # or however you access Claude
```

Tell Claude:
> "I'm starting a new project. Please read CLAUDE.md and help me [your first task]."

## Success Criteria

- ✅ Project directory exists with proper structure
- ✅ VERSION file shows `1.0.0-dev`
- ✅ CHANGELOG.md is initialized
- ✅ CLAUDE.md is customized for your project
- ✅ First Claude session successfully reads CLAUDE.md

## Common Mistakes

| Mistake | Solution |
|---------|----------|
| Forgetting .gitignore | Always exclude `.tmp/` and cache files |
| Generic CLAUDE.md | Take time to customize for your project |
| No VERSION file | Always track version, even for personal projects |
| Missing workflows/ | Create even if empty, documents grow organically |

## Next Steps

After initialization:
1. Complete your first task with Claude
2. Document the workflow as you work
3. Review and improve CLAUDE.md based on session

---

*Part of the Claude Development Framework - Free Tier*
