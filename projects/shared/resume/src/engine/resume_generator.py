#!/usr/bin/env python3
"""
Resume Generator — Tailor a resume to a specific job posting.

Takes parsed job data + user profile and generates a tailored resume
in markdown format, following the proven 10-step workflow.

Usage:
    # From CLI
    python -m src.engine.resume_generator --profile profile.json --job parsed_job.json
    python -m src.engine.resume_generator --profile profile.json --job parsed_job.json --output resume.md

    # As module
    from src.engine.resume_generator import generate_resume
    resume_md = generate_resume(profile_data, parsed_job)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

try:
    import anthropic
except ImportError:
    print("ERROR: pip install anthropic")
    sys.exit(1)


RESUME_PROMPT = """You are an expert resume writer specializing in ATS-optimized, tailored resumes.

Generate a tailored resume in clean markdown format for this candidate, optimized for this specific job.

## CANDIDATE PROFILE:
{profile_json}

## TARGET JOB:
{job_json}

## INSTRUCTIONS (follow the proven 10-step workflow):

1. **Select the right base summary** based on role_type: {role_type}
2. **Rewrite the summary** to match the exact job title in the first sentence, lead with strongest relevant qualification, include 2-3 ATS keywords from the posting
3. **Reorder skills** — put the most relevant skills first in each category. Only include skill categories relevant to this role.
4. **Select 3-5 experience entries** most relevant to this job. For each:
   - Use the role-specific bullet variant if available (e.g. software_engineer bullets for SWE roles)
   - Reword bullets using EXACT terminology from the job posting
   - Quantify achievements (percentages, counts, timeframes)
   - Keep 3-5 bullets per role
5. **ATS keyword optimization** — ensure resume includes exact phrases from the job posting's ats_keywords list
6. **Include education** and relevant projects (max 2 projects)

## OUTPUT FORMAT (clean markdown, no code fences):

# [Full Name]
[Phone] | [Email] | [LinkedIn] | [GitHub] | [Location]

---

## Professional Summary
[2-3 sentence tailored summary]

## Technical Skills
**[Category]:** [skill1, skill2, ...]
**[Category]:** [skill1, skill2, ...]

## Professional Experience

### [Job Title] | [Company] | [Location]
*[Dates]*
- [Quantified achievement bullet using job posting terminology]
- [Quantified achievement bullet]
- [Quantified achievement bullet]

### [Job Title] | [Company] | [Location]
*[Dates]*
- [bullet]

## Education
**[Degree]** — [School], [Location] | [Dates]
GPA: [GPA] | [Honors]

## Projects
**[Project Name]** — [One-line description]
[Tech stack] | [Key highlight]

CRITICAL ANTI-FABRICATION RULES (override all other instructions):
- DO NOT claim qualifications, certifications, licenses, or credentials not present in the candidate profile. NEVER write "clean driving record," "EIT certification," "PE license," "security clearance," "Six Sigma certified," "X years of experience" unless those facts appear in the profile data.
- DO NOT invent specific incidents, troubleshooting stories, project numbers, percentages, or quantified achievements not present in the profile bullets. If the profile says "Troubleshot PLC systems," do NOT expand to "Troubleshot 12 PLC systems with 99% uptime." If the profile says "Reduced costs," do NOT expand to "Reduced costs by 30%."
- DO NOT fabricate dates, durations, or tenure beyond what the profile lists.
- DO NOT apply industry-specific regulatory terminology to work in industries where it does not apply. Examples of overreach to AVOID:
  * Applying FDA/ISO 13485/Design Control/DHF/CAPA/QSR terminology to non-medical-device work (e.g., Marceau Solutions commercial software, AXI fuel systems, Collier wastewater, Codecademy coursework).
  * Applying medical-device manufacturing QMS terminology (First Article Inspection, pFMEA, GD&T, SPC, validation protocols) to hospital BMET work, which uses different terminology.
  * Reframing a candidate's actual work using regulatory keywords from the job posting to inflate apparent fit. Use the candidate's REAL terminology and let the hiring manager see the transferable skill.
- DO NOT misclassify products or facts. Verify before stating regulatory class (Class I/II/III), industry (medical device vs commercial), or scope (production vs research).
- If a job requirement is NOT met by the profile, OMIT it. Do NOT create a false match.
- Preserve the EXACT job dates and tenses from the profile data — if a role is dated "April 2026 – May 2026," it is PAST work. Use past tense bullets.
- Preserve the EXACT degree titles, school names, GPA values, and education `status` field from the profile verbatim. If an education entry includes a `formatting_note`, OBEY it exactly. NEVER add a graduation date, "Expected [term/year]," "in progress," "currently pursuing," "currently enrolled," or any active-coursework language to a degree unless that exact wording is present in the profile data. If a degree's status indicates a Leave of Absence (or similar), render it factually as written and do NOT imply ongoing study or a return date.
- For the "relocation" field in the profile contact section, respect the candidate's stated relocation constraints verbatim. If the profile says "Not currently relocating," do NOT claim "willing to relocate."

OTHER REQUIREMENTS:
- Keep to 1-2 pages of content
- Match the job posting's exact terminology for ATS parsing (but only for qualifications the candidate actually has)
- Lead with the most relevant experience
- Output ONLY the markdown resume, nothing else"""


def generate_resume(
    profile: dict,
    parsed_job: dict,
    model: str = "claude-sonnet-4-5-20250929",
) -> str:
    """
    Generate a tailored resume in markdown format.

    Args:
        profile: User's resume data (resume_data.json format)
        parsed_job: Parsed job posting (from job_parser.py)
        model: Claude model to use

    Returns:
        Tailored resume as markdown string
    """
    role_type = parsed_job.get("role_type", "software_engineer")

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model=model,
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": RESUME_PROMPT.format(
                profile_json=json.dumps(profile, indent=2),
                job_json=json.dumps(parsed_job, indent=2),
                role_type=role_type
            )
        }]
    )

    return response.content[0].text.strip()


def main():
    parser = argparse.ArgumentParser(description="Generate tailored resume")
    parser.add_argument("--profile", "-p", required=True, help="Path to profile JSON")
    parser.add_argument("--job", "-j", required=True, help="Path to parsed job JSON")
    parser.add_argument("--output", "-o", help="Output markdown file path")
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929")
    parser.add_argument("--cost", action="store_true", help="Estimate cost without running")

    args = parser.parse_args()

    if args.cost:
        print("Estimated cost: ~$0.04 (Sonnet, ~4K input + 2K output tokens)")
        return

    with open(args.profile, "r") as f:
        profile = json.load(f)
    with open(args.job, "r") as f:
        parsed_job = json.load(f)

    print(f"Generating resume for {parsed_job.get('role_title', 'Unknown Role')} at {parsed_job.get('company', 'Unknown Company')}...")

    resume_md = generate_resume(profile, parsed_job, model=args.model)

    if args.output:
        with open(args.output, "w") as f:
            f.write(resume_md)
        print(f"Resume saved to {args.output}")
    else:
        print(resume_md)


if __name__ == "__main__":
    main()
