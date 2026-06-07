#!/usr/bin/env python3
"""
Cover Letter Generator — Generate a tailored cover letter for a job posting.

Takes parsed job data + user profile + tailored resume and generates a
compelling cover letter in markdown format.

Usage:
    # From CLI
    python -m src.engine.cover_letter_gen --profile profile.json --job parsed_job.json
    python -m src.engine.cover_letter_gen --profile profile.json --job parsed_job.json --resume resume.md

    # As module
    from src.engine.cover_letter_gen import generate_cover_letter
    cover_letter_md = generate_cover_letter(profile_data, parsed_job)
"""

import argparse
import json
import os
import sys
from pathlib import Path

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


COVER_LETTER_PROMPT = """You are an expert cover letter writer. Write a compelling, professional cover letter.

## TODAY'S DATE (use this exact date in the letter — do not substitute or hallucinate):
{today_date}

## CANDIDATE PROFILE:
{profile_json}

## TARGET JOB:
{job_json}

## TAILORED RESUME (for context — complement, don't repeat):
{resume_context}

## INSTRUCTIONS:

Write a cover letter following this exact structure (300-400 words, one page):

1. **Opening paragraph (2-3 sentences):** State the position. Express genuine interest in the company's specific mission or product. Lead with the single strongest qualification matching their primary need.

2. **Body paragraph 1 (3-4 sentences):** Tell a story about the most relevant experience, drawn EXCLUSIVELY from the profile data. Use only the capabilities, skills, and accomplishments present in the profile bullets. Use the company's terminology naturally woven into the narrative. Do NOT invent specific incidents, dates, customer interactions, or quantified results not in the profile.

3. **Body paragraph 2 (3-4 sentences):** Connect additional experiences that round out qualifications. Show how different roles built complementary skills. Demonstrate progression or breadth — using only what's actually in the profile.

4. **Closing paragraph (2-3 sentences):** ONLY mention special qualifications (clearance, certifications, relocation willingness, clean driving record, language fluency, etc.) that are explicitly listed in the profile. Do NOT claim qualifications the profile does not confirm. Thank them. Express enthusiasm for discussing contribution.

## INDUSTRY KEYWORDS TO WEAVE NATURALLY:
{industry_keywords}

## CRITICAL ANTI-FABRICATION RULES (override all other instructions):
- DO NOT invent specific incidents, troubleshooting stories, customer interactions, or project events. If the profile says "Troubleshot PLC systems," do NOT write "Last month at the Smith Plant I traced a fault to a failing transmitter and restored service in 90 minutes."
- DO NOT claim qualifications not present in the profile (clean driving record, EIT, PE license, certifications, clearances, X years of experience, Six Sigma).
- DO NOT fabricate dates, durations, percentages, or numeric results not in the profile.
- For education: use the profile's education `status` field verbatim and obey any `formatting_note`. NEVER write "in progress," "currently pursuing," "Expected [term/year]," "currently enrolled," or imply active coursework for a degree unless that exact wording is in the profile. If a degree status is a Leave of Absence (or similar), do NOT promote it as an active credential — omit it rather than overstate.
- DO NOT apply industry-specific regulatory terminology (FDA, ISO 13485, Design Controls, DHF, CAPA, First Article Inspection, pFMEA) to work in industries where it does not apply. Marceau Solutions = commercial software, NOT medical device. Hospital BMET work = clinical environment, NOT FDA manufacturing QMS. Use the candidate's REAL terminology.
- DO NOT misclassify products or facts. Verify regulatory class (Class I/II/III), industry, scope before stating.
- For relocation: respect the profile's "relocation" field verbatim. If profile says "Not currently relocating," do NOT claim relocation willingness. Frame commute-distance roles as commuting, not relocating.
- If a role is dated in the past, use PAST TENSE — never "currently working at" or "I am serving as" for a role that has ended.

## WRITING RULES:
- Write in natural, flowing prose — NOT bullet points
- Sound like a professional human, not a template
- Use complete sentences with varied structure
- Reference the company by name and their specific products/mission
- Include numbers and concrete examples ONLY when they appear in the profile
- NEVER use generic phrases like "I am a hard worker" or "passionate team player"
- Keep under one page (300-400 words)

## OUTPUT FORMAT (clean markdown):

# [Full Name]
[Phone] | [Email] | [LinkedIn]

---

[Date]

[Company Name]
Hiring Manager
[Location]

**RE: [Exact Job Title]**

Dear Hiring Manager,

[Opening paragraph]

[Body paragraph 1]

[Body paragraph 2]

[Closing paragraph]

Sincerely,

[Full Name]

Output ONLY the cover letter markdown, nothing else."""


def generate_cover_letter(
    profile: dict,
    parsed_job: dict,
    resume_md: str = "",
    model: str = "claude-sonnet-4-5-20250929",
) -> str:
    """
    Generate a tailored cover letter in markdown format.

    Args:
        profile: User's resume data
        parsed_job: Parsed job posting
        resume_md: Optional tailored resume for context
        model: Claude model to use

    Returns:
        Cover letter as markdown string
    """
    # Build industry keywords hint
    industry = parsed_job.get("industry", "Technology")
    industry_keywords_map = {
        "Defense": "security clearance eligible, AS9100, mission-critical, ITAR, defense systems",
        "Aerospace": "AS9100, flight systems, mission-critical, reliability, clearance eligible",
        "Medical Device": "FDA compliance, ISO 13485, patient safety, quality systems, GMP",
        "Semiconductor": "cleanroom, ESD handling, precision, yield, wafer processing",
        "Software": "scalable, production, deployed, agile, collaborative, CI/CD",
        "SaaS": "scalable, cloud-native, microservices, API-first, customer-centric",
        "Fintech": "compliance, regulatory, secure, real-time, financial systems",
    }
    industry_keywords = industry_keywords_map.get(industry, "professional, results-driven, collaborative")

    resume_context = resume_md if resume_md else "Not provided — generate cover letter from profile and job data only."

    from datetime import date
    today_str = date.today().strftime("%B %-d, %Y")  # e.g. "May 22, 2026"

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model=model,
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": COVER_LETTER_PROMPT.format(
                today_date=today_str,
                profile_json=json.dumps(profile, indent=2),
                job_json=json.dumps(parsed_job, indent=2),
                resume_context=resume_context,
                industry_keywords=industry_keywords
            )
        }]
    )

    return response.content[0].text.strip()


def main():
    parser = argparse.ArgumentParser(description="Generate tailored cover letter")
    parser.add_argument("--profile", "-p", required=True, help="Path to profile JSON")
    parser.add_argument("--job", "-j", required=True, help="Path to parsed job JSON")
    parser.add_argument("--resume", "-r", help="Path to tailored resume markdown (optional)")
    parser.add_argument("--output", "-o", help="Output markdown file path")
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929")
    parser.add_argument("--cost", action="store_true", help="Estimate cost without running")

    args = parser.parse_args()

    if args.cost:
        print("Estimated cost: ~$0.03 (Sonnet, ~3K input + 1K output tokens)")
        return

    with open(args.profile, "r") as f:
        profile = json.load(f)
    with open(args.job, "r") as f:
        parsed_job = json.load(f)

    resume_md = ""
    if args.resume:
        with open(args.resume, "r") as f:
            resume_md = f.read()

    company = parsed_job.get("company", "Unknown Company")
    role = parsed_job.get("role_title", "Unknown Role")
    print(f"Generating cover letter for {role} at {company}...")

    cover_letter = generate_cover_letter(profile, parsed_job, resume_md, model=args.model)

    if args.output:
        with open(args.output, "w") as f:
            f.write(cover_letter)
        print(f"Cover letter saved to {args.output}")
    else:
        print(cover_letter)


if __name__ == "__main__":
    main()
