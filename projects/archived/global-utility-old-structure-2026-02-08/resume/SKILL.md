---
name: resume
description: Resume development and optimization for William Marceau Jr. Generate role-tailored resumes from master data for Software Engineer, AI/ML Engineer, Technical Lead, and Product Manager positions.
version: 1.0.0-dev
trigger_phrases:
  - update my resume
  - tailor resume for
  - create resume
  - resume for
  - job application
  - applying for
model: opus
allowed_tools:
  - Read
  - Write
  - Edit
  - Glob
---

# Resume Skill

## Overview

Generate and customize role-tailored resumes from structured master data. Supports multiple target roles with job-specific customization.

## Capabilities

| Capability | Description |
|------------|-------------|
| **Base Resume Generation** | 4 role-specific versions ready to use |
| **Job-Specific Tailoring** | Customize for specific job postings |
| **ATS Optimization** | Keyword matching and formatting |
| **Master Data Updates** | Add new experience, skills, or projects |

## Available Resume Versions

| Version | Target Roles | File |
|---------|--------------|------|
| Software Engineer | Backend, Frontend, Full-stack | `output/resume_software_engineer.md` |
| AI/ML Engineer | AI, ML, Data Science | `output/resume_ai_ml_engineer.md` |
| Technical Lead | Lead, Architect, Staff | `output/resume_technical_lead.md` |
| Product Manager | PM, Product Owner | `output/resume_product_manager.md` |

## How to Use

### Get a Base Resume
```
"Give me my software engineer resume"
"Show me the AI/ML version"
"I need my technical lead resume"
```
→ Returns the appropriate base version from `output/`

### Tailor for a Specific Job
```
"Tailor my resume for [Company] [Role]"
"Customize resume for this job posting: [paste posting]"
"I'm applying to Stripe for a backend engineer role"
```
→ Follows workflow in `workflows/tailor-resume-for-role.md`

### Update Master Data
```
"Add this new project to my resume"
"Update my skills to include [skill]"
"Add my new job experience"
```
→ Updates `src/resume_data.json` and regenerates versions

## File Structure

```
projects/resume/
├── src/
│   └── resume_data.json          # Master structured data
├── output/
│   ├── resume_software_engineer.md
│   ├── resume_ai_ml_engineer.md
│   ├── resume_technical_lead.md
│   └── resume_product_manager.md
├── workflows/
│   └── tailor-resume-for-role.md  # Customization workflow
├── VERSION
├── SKILL.md                       # This file
└── README.md
```

## Workflow: Tailoring for Specific Jobs

1. **Select base version** matching target role type
2. **Extract keywords** from job posting
3. **Customize summary** to match job title
4. **Reorder skills** by relevance
5. **Tailor bullet points** using job terminology
6. **Highlight relevant projects**
7. **ATS keyword check**
8. **Save as** `output/resume_[company]_[role].md`

See: `workflows/tailor-resume-for-role.md` for detailed steps.

## Master Data Structure

The `src/resume_data.json` contains:
- **Contact info**: Phone, email, LinkedIn, GitHub, location
- **Summaries**: Role-specific professional summaries (4 versions)
- **Skills**: Categorized by domain (languages, backend, cloud, AI/ML, etc.)
- **Experience**: All jobs with role-specific bullet variations
- **Projects**: Dev-sandbox projects with tech stacks and highlights
- **Education**: Degree, school, GPA, honors

## Key Positioning

**Current Framing**: Founder & Technical Lead | Marceau Solutions

**Key differentiators**:
- Built production MCP servers (Amazon, Fitness, Aggregator platform)
- Published to PyPI and Claude MCP Registry
- Designed DOE architecture managing 10+ projects
- Full-stack Python (FastAPI, PostgreSQL, REST APIs)

## Version

- **Resume Skill**: 1.0.0-dev
- **Last Updated**: 2026-01-14
