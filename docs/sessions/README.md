# Session History Index

This directory contains detailed notes from each development session. Think of these as "save points" for our work together - capturing decisions, configurations, learnings, and workflows so we don't have to re-explain or rediscover things.

## Purpose

Just like Python scripts preserve workflows for reuse, these session notes preserve:
- **Decisions made** and their rationale
- **System configurations** and how to replicate them
- **Key learnings** and gotchas encountered
- **Commands and shortcuts** for common tasks
- **Workflows created** and where to find them

## How to Use

### For Claude
1. Read recent session files at start of new sessions to understand current state
2. Reference specific sessions when user mentions past work
3. Update current session file as work progresses
4. Create new session file at end of significant sessions

### For Users
1. Browse sessions to remember what was done
2. Copy commands and workflows from past sessions
3. Reference decisions when planning new work
4. Share context with team members

## Session Files

| Date | Topic | Key Accomplishments |
|------|-------|---------------------|
| [2026-01-04](2026-01-04-git-restructure-and-github-setup.md) | Git Restructure & GitHub Setup | Fixed git repo structure, pushed to GitHub org, created session memory system |
| [2026-01-04](2026-01-04-amazon-sp-api-wrapper.md) | Amazon SP-API Wrapper | Built comprehensive Amazon seller operations wrapper with inventory optimizer and cost analysis |
| [2026-01-04](2026-01-04-markdown-to-pdf-converter.md) | Markdown to PDF Converter | Created professional PDF conversion workflow with styling, TOC, and batch processing |

## Quick Reference

### Recent Important Decisions
- Use MarceauSolutions organization for all production repositories
- Each project has its own git repository (not home directory tracking)
- Built Amazon SP-API wrapper using same pattern as ClickUp CRM
- Implement aggressive caching to minimize 2026 API costs

### Current System State
- **dev-sandbox**: Private repo at `https://github.com/MarceauSolutions/dev-sandbox.git`
- **crm-onboarding-prod**: Private repo at `https://github.com/MarceauSolutions/crm-onboarding-prod.git`
- **GitHub CLI**: Installed and authenticated
- **Amazon SP-API Wrapper**: Built (setup pending - needs credentials)
- **ClickUp CRM**: Operational
- **PDF Converter**: Ready to use
- **Session Memory System**: Active (this directory)

### Most Used Commands
```bash
# Git operations
git remote -v
gh repo create MarceauSolutions/repo-name --private
git push -u origin main

# Amazon inventory optimization
python execution/amazon_inventory_optimizer.py --asin B08XYZ123

# Convert markdown to PDF
python execution/markdown_to_pdf.py --input file.md --output file.pdf
python execution/markdown_to_pdf.py --batch "docs/sessions/*.md" --output-dir pdfs/
```

## Template

Use [TEMPLATE.md](TEMPLATE.md) when creating new session files.

---

**Last Updated**: 2026-01-04
