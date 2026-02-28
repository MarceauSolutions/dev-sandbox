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

## CANDIDATE PROFILE:
{profile_json}

## TARGET JOB:
{job_json}

## TAILORED RESUME (for context — complement, don't repeat):
{resume_context}

## INSTRUCTIONS:

Write a cover letter following this exact structure (300-400 words, one page):

1. **Opening paragraph (2-3 sentences):** State the position. Express genuine interest in the company's specific mission or product. Lead with the single strongest qualification matching their primary need.

2. **Body paragraph 1 (3-4 sentences):** Tell a story about the most relevant experience. Include specific examples with quantified results. Use the company's terminology naturally woven into the narrative.

3. **Body paragraph 2 (3-4 sentences):** Connect additional experiences that round out qualifications. Show how different roles built complementary skills. Demonstrate progression or breadth.

4. **Closing paragraph (2-3 sentences):** Mention special qualifications (clearance eligibility, relocation willingness, certifications). Thank them. Express enthusiasm for discussing contribution.

## INDUSTRY KEYWORDS TO WEAVE NATURALLY:
{industry_keywords}

## WRITING RULES:
- Write in natural, flowing prose — NOT bullet points
- Sound like a professional human, not a template
- Use complete sentences with varied structure
- Reference the company by name and their specific products/mission
- Include numbers and concrete examples
- NEVER use generic phrases like "I am a hard worker" or "passionate team player"
- Keep under one page (300-400 words)
- Use the candidate's REAL experience only

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

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model=model,
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": COVER_LETTER_PROMPT.format(
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
