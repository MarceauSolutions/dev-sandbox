# Workflow: Tailor Resume & Cover Letter for Job Application

## Overview

A complete workflow for customizing your resume and writing a cover letter for a specific job posting. The goal is to maximize keyword matches for ATS systems while telling a compelling, natural story about your qualifications.

## Prerequisites

- Job posting or job description
- Company name and role title
- Base resume data from `src/resume_data.json`

---

## Part 1: Resume Tailoring

### Step 1: Analyze the Job Posting

Read the job description and extract:

| Category | What to Look For |
|----------|------------------|
| **Required skills** | Languages, frameworks, tools, certifications |
| **Preferred skills** | Nice-to-haves that differentiate candidates |
| **Domain expertise** | Industry knowledge (defense, medical, fintech) |
| **Soft skills** | Leadership, communication, collaboration |
| **Special requirements** | Clearance, relocation, physical demands |

Create a quick match table to assess fit before proceeding.

### Step 2: Select Base Version

| Role Type | Base Version |
|-----------|--------------|
| Software/Backend/Full-stack | `resume_software_engineer.md` |
| AI/ML/Data Science | `resume_ai_ml_engineer.md` |
| Tech Lead/Architect | `resume_technical_lead.md` |
| Product Manager | `resume_product_manager.md` |
| Technician/Assembler/Hardware | `resume_anduril_production_tech.md` |

For roles that don't fit existing templates, build from `resume_data.json` directly.

### Step 3: Customize Professional Summary

Rewrite the summary to:
1. **Match the job title** in the first sentence
2. **Lead with your strongest relevant qualification**
3. **Include 2-3 keywords** from the job posting
4. **Mention the company or mission** if it adds value

**Example:**
- Generic: "Full-stack software engineer with production experience..."
- Tailored: "Electro/Mechanical Assembler with hands-on experience in cable wiring, soldering, and diagnostic troubleshooting in defense manufacturing environments..."

### Step 4: Reorder Skills Section

Put the most relevant skills first. The hiring manager's eye goes to the top.

- Job emphasizes Python → Python listed first in Languages
- Job emphasizes cleanroom → Cleanroom listed first in Assembly skills
- Job emphasizes AWS → Cloud/DevOps section moves up

### Step 5: Tailor Experience Bullets

For each role:
1. **Keep** bullets that match job requirements
2. **Reword** bullets using the job posting's exact terminology
3. **Quantify** achievements (percentages, counts, timeframes)
4. **Remove** irrelevant bullets (keep 3-5 per role)
5. **Reorder** most relevant roles to the top

**Rewording example:**
- Original: "Built MCP Aggregator platform"
- For backend role: "Designed RESTful API with intelligent routing, serving 1000+ requests/day"
- For defense role: "Architected multi-tier system with reliability scoring and compliance tracking"

### Step 6: ATS Keyword Optimization

Ensure resume includes **exact phrases** from the job posting:

| Job Says | Include (Not) |
|----------|---------------|
| "React" | React (not "JavaScript frameworks") |
| "CI/CD" | CI/CD (not "deployment automation") |
| "AS9100" | AS9100 (not "quality standards") |
| "wire bonding" | wire bonding (not "soldering") |

### Step 7: Review Checklist

- [ ] Summary matches target role
- [ ] Top skills align with requirements
- [ ] Experience bullets use job's terminology
- [ ] Quantified achievements included
- [ ] 1-2 pages maximum
- [ ] Contact info correct
- [ ] No typos

---

## Part 2: Cover Letter Creation

### Step 8: Write the Cover Letter

Write in natural, flowing prose—not bullet points. The cover letter should complement your resume by providing context and narrative, not repeating it verbatim.

**Structure (300-400 words, one page):**

```
[Header - matching resume style]
# Your Name
Phone | Email | LinkedIn

---

Date

Company Name
Hiring Manager
Location

**RE: Position Title**

Dear Hiring Manager,

[OPENING PARAGRAPH - 2-3 sentences]
State the position. Express genuine interest in the company's specific mission
or product. Lead with your single strongest qualification that matches their
primary need.

[BODY PARAGRAPH 1 - 3-4 sentences]
Tell a story about your most relevant experience. Include specific examples
with quantified results. Use their terminology naturally woven into your
narrative.

[BODY PARAGRAPH 2 - 3-4 sentences]
Connect additional experiences that round out your qualifications. Show how
different roles built complementary skills. Demonstrate progression or
breadth.

[CLOSING PARAGRAPH - 2-3 sentences]
Mention special qualifications (clearance eligibility, relocation, certifications).
Thank them. Express enthusiasm for discussing how you can contribute.

Sincerely,

Your Name
```

### Step 9: Cover Letter Writing Tips

**Write naturally:**
- Use complete sentences that flow together
- Vary sentence length and structure
- Connect ideas with transitions
- Sound like a professional human, not a template

**Be specific:**
- Name the company and role
- Reference their products, mission, or recent news
- Include numbers and concrete examples
- Mention specific technologies or standards they use

**Avoid:**
- Generic phrases ("I am a hard worker", "passionate team player")
- Repeating your resume verbatim
- More than one page
- Different formatting than your resume

### Step 10: Industry-Specific Keywords

Weave these naturally into your cover letter:

| Industry | Include Naturally |
|----------|-------------------|
| Defense/Aerospace | Security clearance eligible, AS9100, mission-critical, ITAR |
| Medical Device | FDA compliance, ISO 13485, patient safety, quality systems |
| Semiconductor | Cleanroom, ESD handling, precision, yield, wafer |
| Software | Scalable, production, deployed, agile, collaborative |

---

## Part 3: Output & Delivery

### File Naming Convention

```
output/resume_[company]_[role].md
output/resume_[company]_[role].pdf
output/cover_letter_[company]_[role].md
output/cover_letter_[company]_[role].pdf
```

**Examples:**
- `resume_l3harris_em_assembler.md`
- `cover_letter_l3harris_em_assembler.pdf`

### PDF Generation

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/resume/output

# Resume (tighter margins for more content)
pandoc resume_[company]_[role].md -o resume_[company]_[role].pdf \
  --pdf-engine=pdflatex -V geometry:margin=0.75in -V fontsize=11pt

# Cover Letter (standard margins for readability)
pandoc cover_letter_[company]_[role].md -o cover_letter_[company]_[role].pdf \
  --pdf-engine=pdflatex -V geometry:margin=1in -V fontsize=11pt
```

---

## Final Checklist

### Resume
- [ ] Summary matches target role
- [ ] Skills prioritized to match job
- [ ] Experience uses job's terminology
- [ ] Achievements quantified
- [ ] 1-2 pages max
- [ ] ATS keywords included

### Cover Letter
- [ ] Addressed to correct company/position
- [ ] Opens with strongest qualification
- [ ] Tells a cohesive story (not bullets)
- [ ] Uses natural, flowing language
- [ ] Includes industry keywords naturally
- [ ] Mentions clearance/relocation if relevant
- [ ] Under one page (300-400 words)
- [ ] Matches resume formatting

### Files
- [ ] `resume_[company]_[role].md` created
- [ ] `resume_[company]_[role].pdf` generated
- [ ] `cover_letter_[company]_[role].md` created
- [ ] `cover_letter_[company]_[role].pdf` generated

---

## Quick Reference: Example Cover Letter

> I am writing to express my strong interest in the Electro/Mechanical Assembler position at L3Harris Technologies. With hands-on experience in cable assembly, soldering, and diagnostic troubleshooting—including prior work at Marmon Aerospace & Defense—I am excited about the opportunity to contribute to building Unmanned Underwater Vehicles that support our nation's defense.
>
> At Marmon, I performed complex cable assembly operations for military-grade cables, conducted VNA testing, and provided manufacturability feedback that reduced production costs by 12%. This defense industry experience gave me familiarity with AS9100 quality standards and the precision required for mission-critical systems. At Insulet Corporation, I worked on electro-mechanical medical device assembly in a cleanroom environment, performing rework on complex assemblies and maintaining 99%+ equipment uptime through careful preventive maintenance.
>
> I am a U.S. citizen eligible for security clearance and willing to relocate to Fall River. Thank you for considering my application—I would welcome the opportunity to discuss how my skills can contribute to L3Harris's mission of delivering trusted solutions for national security.
