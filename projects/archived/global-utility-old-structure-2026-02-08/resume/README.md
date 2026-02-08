# Resume Project

Resume development and optimization for William Marceau Jr.

## Quick Start

**Get a base resume:**
```
"Give me my software engineer resume"
"Show me the AI/ML version"
```

**Tailor for a job:**
```
"Tailor resume for Stripe backend engineer"
"I'm applying to Google for ML engineer"
```

## Available Versions

| Version | Target Roles | File |
|---------|--------------|------|
| Software Engineer | Backend, Frontend, Full-stack | `output/resume_software_engineer.md` |
| AI/ML Engineer | AI, ML, Data Science | `output/resume_ai_ml_engineer.md` |
| Technical Lead | Lead, Architect, Staff | `output/resume_technical_lead.md` |
| Product Manager | PM, Product Owner | `output/resume_product_manager.md` |

## Structure

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
├── SKILL.md
└── README.md
```

## Key Files

- **Master Data**: `src/resume_data.json` - All experience, skills, projects in structured format
- **Tailoring Workflow**: `workflows/tailor-resume-for-role.md` - Step-by-step job customization
- **Skill Definition**: `SKILL.md` - How this project integrates with personal assistant

## Current Positioning

**Title**: Founder & Technical Lead | Marceau Solutions

**Key differentiators**:
- Built production MCP servers (Amazon, Fitness, Aggregator platform)
- Published to PyPI and Claude MCP Registry
- Designed DOE architecture managing 10+ projects
- Full-stack Python (FastAPI, PostgreSQL, REST APIs)

## Version

Current: 1.0.0-dev
