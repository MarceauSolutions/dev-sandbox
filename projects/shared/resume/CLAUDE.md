# Resume & Job Application Prep

## What This Does

Generate tailored resumes and cover letters from a master data file. Supports multiple role types (Software Engineer, AI/ML, Tech Lead, Product Manager, and custom roles).

## Key Files

| File | Purpose |
|------|---------|
| `src/resume_data.json` | Master resume data (experience, skills, projects) |
| `output/` | Generated resumes (89+ versions, PDF + MD) |
| `workflows/tailor-resume-for-role.md` | Step-by-step resume tailoring workflow |
| `CLAUDE-CODE-HANDOFF-JOB-PREP.md` | Full job prep guide (resume + LinkedIn + GitHub + interview) |

## Quick Start

### View existing resume versions
```bash
ls output/*.pdf
```

### Generate a tailored resume for a specific job
1. Read the job posting
2. Follow `workflows/tailor-resume-for-role.md`
3. Use `src/resume_data.json` as the source of truth for all experience/skills

### Generate PDF from markdown
```bash
cd output
pandoc resume_[company]_[role].md -o resume_[company]_[role].pdf \
  --pdf-engine=pdflatex -V geometry:margin=0.75in -V fontsize=11pt
```

## Available Base Versions

| Role Type | File |
|-----------|------|
| Software Engineer | `output/resume_software_engineer.pdf` |
| AI/ML Engineer | `output/resume_ai_ml_engineer.pdf` |
| Technical Lead | `output/resume_technical_lead.pdf` |
| Product Manager | `output/resume_product_manager.pdf` |
| Custom roles | Build from `resume_data.json` directly |

## Resume Data Structure

`src/resume_data.json` contains:
- **contact**: Name, phone, email, LinkedIn, GitHub, location
- **summaries**: Pre-written summaries per role type
- **skills**: Categorized (languages, backend, cloud, AI/ML, automation, controls)
- **experience**: Each role with company, dates, bullets, and relevance tags
- **education**: Degree, institution, relevant coursework
- **projects**: Portfolio items with descriptions and technologies

## Related Tools

- **Interview Prep**: `interview-prep-pptx/` — AI-powered company research + presentation generator
- **Full Job Prep Guide**: `CLAUDE-CODE-HANDOFF-JOB-PREP.md` — LinkedIn, GitHub, tracking
