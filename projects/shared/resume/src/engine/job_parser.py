#!/usr/bin/env python3
"""
Job Posting Parser — Extract structured requirements from job postings.

Uses Claude API to intelligently parse job postings into structured data
that feeds into resume_generator.py and cover_letter_gen.py.

Usage:
    # From CLI
    python -m src.engine.job_parser --text "Full job posting text here..."
    python -m src.engine.job_parser --file job_posting.txt
    python -m src.engine.job_parser --text "..." --output parsed_job.json

    # As module
    from src.engine.job_parser import parse_job_posting
    result = parse_job_posting("Full job posting text...")
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure we can find .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent  # dev-sandbox root
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


PARSE_PROMPT = """Analyze this job posting and extract structured data. Return ONLY valid JSON, no markdown fences.

Job Posting:
{job_text}

Return this exact JSON structure:
{{
  "company": "Company Name",
  "role_title": "Exact Job Title",
  "location": "City, State or Remote",
  "industry": "e.g. Defense, SaaS, Medical Device, Fintech",
  "role_type": "software_engineer | ai_ml_engineer | technical_lead | product_manager | technician | other",
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill1", "skill2"],
  "required_experience_years": 0,
  "education_requirements": "e.g. BS in CS or equivalent",
  "domain_expertise": ["industry-specific knowledge areas"],
  "soft_skills": ["leadership", "communication"],
  "special_requirements": ["security clearance", "relocation", "travel"],
  "ats_keywords": ["exact phrases from posting that should appear in resume"],
  "company_mission": "One sentence about what the company does/values",
  "key_responsibilities": ["top 3-5 responsibilities"],
  "salary_range": "if mentioned, else null",
  "match_analysis": {{
    "strongest_matches": ["areas where the candidate profile would be strongest"],
    "gaps": ["areas where the candidate may need to stretch"],
    "recommended_emphasis": "what to lead with in resume/cover letter"
  }}
}}"""


def parse_job_posting(
    job_text: str,
    model: str = "claude-sonnet-4-5-20250929",
) -> dict:
    """
    Parse a job posting into structured requirements.

    Args:
        job_text: Raw job posting text
        model: Claude model to use

    Returns:
        Parsed job data as dict
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": PARSE_PROMPT.format(job_text=job_text)
        }]
    )

    raw = response.content[0].text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[:-3]

    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description="Parse job posting into structured data")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", "-t", help="Job posting text")
    input_group.add_argument("--file", "-f", help="Path to file containing job posting")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929", help="Claude model")
    parser.add_argument("--cost", action="store_true", help="Estimate cost without running")

    args = parser.parse_args()

    if args.cost:
        print("Estimated cost: ~$0.015 (Sonnet, ~2K input + 500 output tokens)")
        return

    # Get job text
    if args.file:
        with open(args.file, "r") as f:
            job_text = f.read()
    else:
        job_text = args.text

    if not job_text or len(job_text.strip()) < 50:
        print("ERROR: Job posting text too short. Provide the full posting.")
        sys.exit(1)

    print(f"Parsing job posting ({len(job_text)} chars)...")

    result = parse_job_posting(job_text, model=args.model)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))

    # Quick summary
    print(f"\n--- Summary ---")
    print(f"Company: {result.get('company', 'N/A')}")
    print(f"Role: {result.get('role_title', 'N/A')}")
    print(f"Type: {result.get('role_type', 'N/A')}")
    print(f"Required skills: {len(result.get('required_skills', []))}")
    print(f"ATS keywords: {len(result.get('ats_keywords', []))}")


if __name__ == "__main__":
    main()
