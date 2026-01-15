# Workflow: Tailor Resume for Specific Job

## Overview
How to customize a base resume version for a specific job posting.

## Prerequisites
- Base resume version from `output/` folder
- Job posting or job description
- Company name and role title

## Steps

### 1. Select Base Version

| Target Role Contains | Use Base Version |
|---------------------|------------------|
| Software Engineer, Backend, Full-stack, Developer | `resume_software_engineer.md` |
| AI, ML, Machine Learning, Data Scientist | `resume_ai_ml_engineer.md` |
| Tech Lead, Architect, Staff Engineer, Principal | `resume_technical_lead.md` |
| Product Manager, PM, Product Owner | `resume_product_manager.md` |

### 2. Extract Keywords from Job Posting

Identify:
- **Required skills** (languages, frameworks, tools)
- **Nice-to-have skills**
- **Domain expertise** (e-commerce, healthcare, fintech, etc.)
- **Soft skills** (leadership, communication, collaboration)

### 3. Customize Professional Summary

Rewrite first sentence to match job title exactly:
- Original: "Full-stack software engineer..."
- Tailored: "Backend engineer with production experience..." (if applying to backend role)

Add company-specific angle if relevant:
- "...excited to bring AI automation expertise to [Company]'s mission of..."

### 4. Reorder Skills Section

Move most relevant skills to top:
- If job emphasizes AWS → move Cloud/DevOps section up
- If job emphasizes ML → move AI/ML section up
- If job emphasizes specific language → list that first in Languages

### 5. Tailor Bullet Points

For each experience section:
1. Keep bullets that match job requirements
2. Reword bullets to use job posting's terminology
3. Add quantified metrics where possible
4. Remove irrelevant bullets (keep 3-5 per role)

**Example transformation:**
- Original: "Built MCP Aggregator platform"
- Tailored (for backend role): "Designed and implemented RESTful API serving 1000+ requests/day with <100ms latency"

### 6. Highlight Relevant Projects

Reorder projects section:
1. Most relevant project first
2. Add/emphasize tech stack that matches job
3. Expand highlights that align with job requirements

### 7. ATS Keyword Check

Ensure resume includes exact phrases from job posting:
- Job says "React" → include "React" (not just "JavaScript")
- Job says "CI/CD" → include "CI/CD" (not just "deployment")
- Job says "agile" → include "agile" somewhere

### 8. Final Review Checklist

- [ ] Professional summary mentions target role type
- [ ] Top 3 skills match job requirements
- [ ] Each experience section has relevant bullets
- [ ] Projects demonstrate required tech stack
- [ ] Resume is 1-2 pages max
- [ ] Contact info is correct
- [ ] No typos or formatting issues

## Example: Tailoring for "Backend Engineer at Stripe"

**Job emphasizes:** Python, APIs, payments, scale, reliability

**Changes to make:**
1. Summary: "Backend engineer with production experience building payment and transaction systems..."
2. Skills: Move Python, REST APIs, PostgreSQL to top
3. Founder bullets: Emphasize Stripe integration, transaction tracking, billing system
4. Projects: Lead with MCP Aggregator (has billing/transaction focus)

## Tips

- **Don't lie** – only claim skills you actually have
- **Be specific** – "Python" is better than "programming"
- **Quantify** – "50+ clients" beats "many clients"
- **Match language** – use their terminology, not synonyms
- **One page if possible** – easier for busy recruiters

## Output

Save tailored resume as:
`output/resume_[company]_[role].md`

Example: `output/resume_stripe_backend_engineer.md`
