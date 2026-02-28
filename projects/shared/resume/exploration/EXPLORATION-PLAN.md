# Resume & Cover Letter Builder — Architecture Exploration

**Date**: 2026-02-17
**Project**: Sellable Resume & Cover Letter AI Assistant
**Status**: EXPLORING (SOP 9)

## Problem Statement
Transform existing resume/cover letter builder (manual workflow + 89 generated pairs + resume_data.json) into a sellable AI assistant product. Must automate: job posting parsing, resume tailoring, cover letter generation, ATS optimization, PDF output.

## What Exists Today
- `src/resume_data.json` — Master data (8 experiences, 40+ skills, 4 role summaries)
- `workflows/tailor-resume-for-role.md` — Manual 10-step tailoring workflow
- `output/` — 89+ resume/cover letter pairs (MD + PDF)
- `interview-prep-pptx/` — Related skill (deployed, separate project)
- `execution/google_drive_share.py` — File delivery
- pandoc + pdflatex — PDF generation pipeline

## 4 Approaches to Evaluate

### Approach 1: Standalone AI Assistant (SOP 31)
Self-contained GitHub repo at `~/ai-assistants/resume-builder/` with Python scripts + CLAUDE.md. Buyer clones repo, opens in Claude Code, Claude orchestrates the scripts. Sell via Gumroad/GitHub.

### Approach 2: MCP Server Package (PyPI + Registry)
Like md-to-pdf — publish as installable MCP server. Users `pip install resume-builder-mcp`, configure in Claude settings, use tools from any Claude instance. Automated resume generation via MCP tool calls.

### Approach 3: Web App (Streamlit/Gradio)
Self-service web interface. User pastes job posting URL/text, uploads their resume data, gets tailored resume + cover letter as PDF download. Host on Railway. Subscription or per-use pricing.

### Approach 4: n8n Webhook + Landing Page
Use existing EC2 n8n infrastructure. Landing page with Stripe checkout → webhook triggers n8n workflow → Claude API generates tailored resume → PDF → email delivery. Minimal new code, maximum infrastructure reuse.

## Evaluation Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Revenue Potential** | 5x | How much money can this realistically make? |
| **Time to Market** | 4x | How fast can we ship v1? |
| **Build Complexity** | 4x | How much new code/infra needed? |
| **Target Market Size** | 3x | How many potential buyers? |
| **Maintenance Burden** | 3x | Ongoing work after launch? |
| **Scalability** | 2x | Can it handle 100+ users? |
| **Infrastructure Reuse** | 2x | How much existing code/infra can we leverage? |

## Scoring System
- 5 stars: Excellent
- 4 stars: Good
- 3 stars: Acceptable
- 2 stars: Poor
- 1 star: Unusable

## Agents
- Agent 1: Standalone AI Assistant (SOP 31 path)
- Agent 2: MCP Server Package (PyPI/Registry path)
- Agent 3: Web App (Streamlit/Gradio path)
- Agent 4: n8n Webhook + Landing Page (existing infra path)
