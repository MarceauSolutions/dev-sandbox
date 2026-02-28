#!/usr/bin/env python3
"""
Generate Application — Full pipeline: job posting → tailored resume + cover letter PDFs.

This is the main orchestrator that the n8n webhook calls. Runs the full pipeline:
1. Parse job posting → structured requirements
2. Generate tailored resume markdown
3. Generate tailored cover letter markdown
4. Build PDFs from both

Usage:
    # Full pipeline from job posting text
    python -m src.engine.generate_application \
        --profile profile.json \
        --job-text "Full job posting here..." \
        --output-dir ./output/

    # Full pipeline from job posting file
    python -m src.engine.generate_application \
        --profile profile.json \
        --job-file posting.txt \
        --output-dir ./output/

    # As module (for n8n Python Bridge)
    from src.engine.generate_application import generate_full_application
    result = generate_full_application(profile_data, job_text, output_dir)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from src.engine.job_parser import parse_job_posting
from src.engine.resume_parser import parse_resume, parse_resume_text
from src.engine.resume_generator import generate_resume
from src.engine.cover_letter_gen import generate_cover_letter
from src.engine.pdf_builder import build_both


def generate_full_application(
    profile: dict,
    job_text: str,
    output_dir: str,
    model: str = "claude-sonnet-4-5-20250929",
    resume_file: str = None,
    resume_text: str = None,
) -> dict:
    """
    Run the full resume + cover letter generation pipeline.

    Accepts profile data in three ways (in priority order):
    1. resume_file: Path to PDF/DOCX — AI parses it into profile
    2. resume_text: Raw resume text — AI parses it into profile
    3. profile: Pre-structured profile dict (resume_data.json format)

    Args:
        profile: User's resume data (resume_data.json format), can be empty if resume_file/resume_text provided
        job_text: Raw job posting text
        output_dir: Directory to save outputs
        model: Claude model to use
        resume_file: Path to resume PDF/DOCX to parse (optional)
        resume_text: Raw resume text to parse (optional)

    Returns:
        Dict with paths to all generated files and metadata
    """
    start_time = time.time()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Step 0: Parse resume if file/text provided (instead of pre-built profile)
    total_steps = 5 if (resume_file or resume_text) else 4
    step = 0

    if resume_file:
        step += 1
        print(f"Step {step}/{total_steps}: Parsing uploaded resume...")
        profile = parse_resume(resume_file, model=model)
        # Save parsed profile for reference
        profile_path = output_path / "parsed_profile.json"
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)
    elif resume_text:
        step += 1
        print(f"Step {step}/{total_steps}: Parsing resume text...")
        profile = parse_resume_text(resume_text, model=model)
        profile_path = output_path / "parsed_profile.json"
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if not profile:
        raise ValueError("No profile data provided. Pass profile dict, resume_file, or resume_text.")

    # Step 1: Parse job posting
    step += 1
    print(f"Step {step}/{total_steps}: Parsing job posting...")
    parsed_job = parse_job_posting(job_text, model=model)

    company = parsed_job.get("company", "company")
    role = parsed_job.get("role_title", "role")
    company_slug = company.lower().replace(" ", "_").replace("/", "_")[:30]
    role_slug = role.lower().replace(" ", "_").replace("/", "_")[:30]

    # Save parsed job for reference
    parsed_job_path = output_path / f"parsed_job_{company_slug}_{role_slug}.json"
    with open(parsed_job_path, "w") as f:
        json.dump(parsed_job, f, indent=2)

    # Step 2: Generate tailored resume
    step += 1
    print(f"Step {step}/{total_steps}: Generating resume for {role} at {company}...")
    resume_md = generate_resume(profile, parsed_job, model=model)

    resume_md_path = output_path / f"resume_{company_slug}_{role_slug}.md"
    with open(resume_md_path, "w") as f:
        f.write(resume_md)

    # Step 3: Generate cover letter
    step += 1
    print(f"Step {step}/{total_steps}: Generating cover letter...")
    cover_letter_md = generate_cover_letter(profile, parsed_job, resume_md, model=model)

    cover_md_path = output_path / f"cover_letter_{company_slug}_{role_slug}.md"
    with open(cover_md_path, "w") as f:
        f.write(cover_letter_md)

    # Step 4: Build PDFs
    step += 1
    print(f"Step {step}/{total_steps}: Building PDFs...")
    pdf_result = build_both(
        str(resume_md_path),
        str(cover_md_path),
        str(output_path),
        company=company,
        role=role,
    )

    elapsed = time.time() - start_time

    result = {
        "success": pdf_result["all_success"],
        "company": company,
        "role_title": role,
        "industry": parsed_job.get("industry", "Unknown"),
        "role_type": parsed_job.get("role_type", "other"),
        "elapsed_seconds": round(elapsed, 1),
        "files": {
            "parsed_job": str(parsed_job_path),
            "resume_md": str(resume_md_path),
            "cover_letter_md": str(cover_md_path),
            "resume_pdf": pdf_result["resume_pdf"],
            "cover_letter_pdf": pdf_result["cover_letter_pdf"],
        },
        "ats_keywords_used": len(parsed_job.get("ats_keywords", [])),
        "match_analysis": parsed_job.get("match_analysis", {}),
    }

    # Save result metadata
    meta_path = output_path / f"generation_meta_{company_slug}_{role_slug}.json"
    with open(meta_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nDone in {elapsed:.1f}s")
    print(f"Resume PDF: {pdf_result['resume_pdf']}")
    print(f"Cover Letter PDF: {pdf_result['cover_letter_pdf']}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Generate full application (resume + cover letter)")

    profile_group = parser.add_mutually_exclusive_group(required=True)
    profile_group.add_argument("--profile", "-p", help="Path to pre-built profile JSON")
    profile_group.add_argument("--resume-file", "-r", help="Path to resume PDF/DOCX (AI will parse it)")

    job_group = parser.add_mutually_exclusive_group(required=True)
    job_group.add_argument("--job-text", "-t", help="Job posting text")
    job_group.add_argument("--job-file", "-f", help="Path to file with job posting")

    parser.add_argument("--output-dir", "-o", default="./output", help="Output directory")
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929")
    parser.add_argument("--cost", action="store_true", help="Estimate cost without running")

    args = parser.parse_args()

    if args.cost:
        print("Estimated cost per generation:")
        print("  Resume parsing:   ~$0.020 (only if uploading PDF/DOCX)")
        print("  Job parsing:      ~$0.015")
        print("  Resume tailoring: ~$0.040")
        print("  Cover letter:     ~$0.030")
        print("  PDF generation:   $0.000")
        print("  ─────────────────────────")
        print("  TOTAL:            ~$0.085 (profile) / ~$0.105 (resume upload)")
        return

    profile = {}
    resume_file = None

    if args.profile:
        with open(args.profile, "r") as f:
            profile = json.load(f)
    else:
        resume_file = args.resume_file

    if args.job_file:
        with open(args.job_file, "r") as f:
            job_text = f.read()
    else:
        job_text = args.job_text

    result = generate_full_application(
        profile, job_text, args.output_dir,
        model=args.model, resume_file=resume_file,
    )

    if result["success"]:
        print("\nGeneration successful!")
        print(json.dumps(result, indent=2))
    else:
        print("\nGeneration had errors — check output files", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
