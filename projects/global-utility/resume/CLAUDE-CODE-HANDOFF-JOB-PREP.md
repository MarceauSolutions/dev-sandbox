# Claude Code Handoff: Complete Job Application Prep

**Date:** 2026-01-30
**From:** Clawdbot (EC2)
**To:** Claude Code (MacBook)
**Priority:** High

---

## Overview

William needs to complete his profile and apply to jobs. This document covers everything needed:
1. **Resume** - Multiple versions exist, may need updates
2. **LinkedIn Profile** - Optimization needed
3. **GitHub Profile** - README and public repos
4. **Interview Prep** - PowerPoint generator ready
5. **Job Application Tracking** - Not yet built

---

## 1. Resume System Status

### ✅ Already Built

**Location:** `projects/global-utility/resume/`

**Available Versions:**
| Version | File | Status |
|---------|------|--------|
| Software Engineer | `output/resume_software_engineer.pdf` | ✅ Ready |
| AI/ML Engineer | `output/resume_ai_ml_engineer.pdf` | ✅ Ready |
| Technical Lead | `output/resume_technical_lead.pdf` | ✅ Ready |
| Product Manager | `output/resume_product_manager.pdf` | ✅ Ready |
| Anduril Production Tech | `output/resume_anduril_production_tech.pdf` | ✅ Ready |
| FGCU Endpoint Systems | `output/resume_fgcu_endpoint_systems_engineer.pdf` | ✅ Ready |
| Hayward Jr EE | `output/resume_hayward_jr_ee.pdf` | ✅ Ready |
| Honeywell Test Tech | `output/resume_honeywell_test_tech.pdf` | ✅ Ready |

**Master Data:** `src/resume_data.json` - Contains all experience, skills, projects

### Action Items for Claude Code

1. **Review master data** - Ensure it's current
   ```bash
   cat projects/global-utility/resume/src/resume_data.json
   ```

2. **Update if needed:**
   - Add any new projects (MCPs built since last update)
   - Add new skills
   - Update Marceau Solutions section with recent client work

3. **Generate tailored versions** for specific jobs William is targeting
   - Use workflow: `workflows/tailor-resume-for-role.md`
   - Output naming: `resume_[company]_[role].pdf`

4. **PDF Generation:**
   ```bash
   cd projects/global-utility/resume/output
   pandoc resume_[name].md -o resume_[name].pdf \
     --pdf-engine=pdflatex -V geometry:margin=0.75in -V fontsize=11pt
   ```

---

## 2. LinkedIn Profile Optimization

### Current State
- Profile exists: linkedin.com/in/williamjmarceau
- Needs optimization for job search

### Action Items for Claude Code

**Read the full guide:** `projects/global-utility/resume/workflows/linkedin-github-presence.md`

**Generate these assets:**

#### A. New Headline
Generate an attention-grabbing headline that positions William correctly:

Options to consider:
```
Automation Engineer | Building AI tools for small businesses | Python, MCP, Claude
```
```
Technical Founder | 12 MCPs Built | Voice AI & Automation for Small Business
```
```
AI/Automation Engineer | Founder @ Marceau Solutions | Python, FastAPI, MCP Protocol
```

#### B. About Section
Write a compelling about section (~300 words) that:
- Opens with impact statement
- Lists concrete achievements with numbers
- Mentions key technologies
- Has clear CTA for recruiters/clients

**Include these achievements:**
- 12 MCPs built and published
- Apollo MCP: 80% credit savings
- Voice AI: $8K recovered for HVAC client week 1
- Automated systems with 99%+ uptime

#### C. Experience Section Updates
Ensure LinkedIn experience matches resume:
- Marceau Solutions (Founder & Technical Lead)
- Include MCP Aggregator, Apollo MCP, Voice AI, Ralph pipeline

#### D. Featured Section
Suggest what to feature:
- Link to PyPI packages
- Link to MCP Registry listings
- GitHub profile
- marceausolutions.com

---

## 3. GitHub Profile Optimization

### Action Items for Claude Code

#### A. Create Profile README
Create a `README.md` for William's GitHub profile repo (`wmarceau`):

```markdown
## Hi, I'm William 👋

**Founder @ Marceau Solutions | Building AI automation for small businesses**

### 🔧 What I Build
- **MCP Servers** - Tools that let AI agents interact with real-world services
- **Voice AI Systems** - 24/7 phone coverage for small businesses
- **Automation Pipelines** - Lead gen, follow-up, CRM integration

### 📦 Published Packages
| Package | Description | Install |
|---------|-------------|---------|
| [apollo-mcp](https://pypi.org/project/apollo-mcp/) | Lead scraping for Claude | `pip install apollo-mcp` |
| [More coming...] | | |

### 🚀 Recent Projects
- **Ralph** - Autonomous AI dev agent that executes PRDs
- **MCP Aggregator** - Marketplace routing AI to 100+ services
- **Voice AI** - $8K recovered for HVAC client in week 1

### 📊 Stats
- 12 MCPs built
- 80% cost savings with automated lead qualification
- 99%+ uptime on client automation systems

### 🛠️ Tech Stack
`Python` `FastAPI` `PostgreSQL` `Claude MCP` `Twilio` `n8n`

### 📫 Connect
- 🌐 [marceausolutions.com](https://marceausolutions.com)
- 💼 [LinkedIn](https://linkedin.com/in/williamjmarceau)
- 📧 wmarceau@marceausolutions.com
```

#### B. Repository Cleanup
Decide which repos should be public to showcase skills:
- Apollo MCP (if not already public)
- Any other showcase-worthy projects

---

## 4. Interview Prep System

### ✅ Already Built

**Location:** `interview-prep-pptx/`

**Capabilities:**
- AI-powered company research
- Role analysis with skill matching
- Interview Q&A preparation
- Resume integration for personalization
- AI image generation for slides
- Multiple presentation themes

### How to Use

```bash
cd interview-prep-pptx

# Generate presentation for a job
python src/interview_research.py \
  --company "Company Name" \
  --role "Role Title" \
  --resume ~/path/to/resume.pdf \
  --generate-images

# Create PowerPoint
python src/pptx_generator.py \
  --input .tmp/interview_research_[company].json \
  --theme modern
```

### Action Items for Claude Code

1. **Verify it works** - Run a test generation
2. **Create presentations** for any companies William is targeting
3. **Consider expanding** with mock interview feature (see `EXPANDED_SCOPE.md`)

---

## 5. Job Application Tracker (TO BUILD)

### Recommended: Create Simple Tracker

**Location:** `projects/global-utility/job-tracker/`

**Structure:**
```
job-tracker/
├── src/
│   └── jobs.json         # Application data
├── output/
│   └── applications/     # Per-company folders
├── README.md
└── SKILL.md
```

**jobs.json schema:**
```json
{
  "applications": [
    {
      "id": "uuid",
      "company": "Company Name",
      "role": "Role Title",
      "status": "applied|interviewing|offer|rejected|ghosted",
      "applied_date": "2026-01-30",
      "source": "LinkedIn|Indeed|Direct|Referral",
      "contacts": [
        {"name": "Recruiter Name", "email": "email@company.com"}
      ],
      "interviews": [
        {"date": "2026-02-05", "type": "phone|video|onsite", "notes": ""}
      ],
      "follow_ups": [
        {"date": "2026-02-01", "action": "Thank you email sent"}
      ],
      "salary_range": "$100K-120K",
      "notes": "",
      "resume_version": "resume_company_role.pdf",
      "cover_letter": "cover_letter_company_role.pdf"
    }
  ]
}
```

---

## 6. Complete Checklist for Claude Code

### Resume
- [ ] Review `resume_data.json` for currency
- [ ] Update with any new projects/skills
- [ ] Regenerate PDFs if changes made
- [ ] Create tailored versions for target companies

### LinkedIn
- [ ] Draft new headline (3 options)
- [ ] Write new About section (~300 words)
- [ ] List Experience section updates
- [ ] Suggest Featured section items
- [ ] Create content calendar for job search posts

### GitHub
- [ ] Create profile README.md
- [ ] Identify repos to make public
- [ ] Clean up any sensitive data in repos

### Interview Prep
- [ ] Test interview_research.py works
- [ ] Generate prep materials for target companies

### Job Tracker
- [ ] Create `job-tracker/` directory structure
- [ ] Build basic tracker (jobs.json + README)
- [ ] Add first applications

---

## 7. Target Companies/Roles

**Ask William for:**
1. What types of roles is he targeting?
   - AI/ML Engineer
   - Software Engineer  
   - Technical Lead
   - Automation Engineer
   - Something else?

2. What companies is he interested in?
   - Specific companies to target
   - Industries to focus on
   - Location preferences (remote vs local)

3. What's his timeline?
   - Immediate job search
   - Exploratory
   - Building pipeline

**This will determine:**
- Which resume versions to prioritize
- What interview prep to generate
- LinkedIn positioning angle

---

## 8. Quick Commands

```bash
# Navigate to resume project
cd /Users/williammarceaujr./dev-sandbox/projects/global-utility/resume

# View current resume versions
ls -la output/

# View master data
cat src/resume_data.json | head -100

# Navigate to interview prep
cd /Users/williammarceaujr./dev-sandbox/interview-prep-pptx

# Generate interview prep
python src/interview_research.py --company "Target" --role "Role"
```

---

## Summary

**What Exists:**
- ✅ 8 resume versions (PDFs ready)
- ✅ Resume tailoring workflow
- ✅ Interview prep PowerPoint generator
- ✅ LinkedIn/GitHub presence guide

**What Needs Work:**
- 🔄 Update resume data if outdated
- 📝 Write new LinkedIn headline + About
- 📝 Create GitHub profile README
- 🆕 Build job application tracker
- 🎯 Tailor materials for specific target companies

**Ask William:**
- What roles/companies is he targeting?
- What's the priority order?
- Timeline for applications?

---

*Generated by Clawdbot on 2026-01-30*
