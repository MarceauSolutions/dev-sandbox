#!/usr/bin/env python3
"""
PDF Builder — Convert markdown resume/cover letter to PDF.

Wraps pandoc with the proven settings from the tailor-resume workflow.

Usage:
    # From CLI
    python -m src.engine.pdf_builder --input resume.md --output resume.pdf
    python -m src.engine.pdf_builder --input resume.md --output resume.pdf --type cover_letter
    python -m src.engine.pdf_builder --resume resume.md --cover cover.md --output-dir ./output/

    # As module
    from src.engine.pdf_builder import build_pdf, build_resume_pdf, build_cover_letter_pdf
    build_resume_pdf("resume.md", "resume.pdf")
    build_cover_letter_pdf("cover.md", "cover.pdf")
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def build_pdf(
    input_path: str,
    output_path: str,
    margin: str = "0.75in",
    fontsize: str = "11pt",
    pdf_engine: str = "pdflatex",
) -> bool:
    """
    Convert markdown to PDF using pandoc.

    Args:
        input_path: Path to input markdown file
        output_path: Path to output PDF file
        margin: Page margin (default 0.75in for resumes)
        fontsize: Font size (default 11pt)
        pdf_engine: PDF engine (pdflatex or xelatex)

    Returns:
        True if successful
    """
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "pandoc",
        input_path,
        "-o", output_path,
        f"--pdf-engine={pdf_engine}",
        f"-V", f"geometry:margin={margin}",
        f"-V", f"fontsize={fontsize}",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"ERROR: pandoc failed: {result.stderr}", file=sys.stderr)
            return False
        return True
    except FileNotFoundError:
        print("ERROR: pandoc not found. Install: brew install pandoc", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print("ERROR: pandoc timed out after 30 seconds", file=sys.stderr)
        return False


def build_resume_pdf(input_path: str, output_path: str) -> bool:
    """Build resume PDF with tight margins for content density."""
    return build_pdf(input_path, output_path, margin="0.75in", fontsize="11pt")


def build_cover_letter_pdf(input_path: str, output_path: str) -> bool:
    """Build cover letter PDF with standard margins for readability."""
    return build_pdf(input_path, output_path, margin="1in", fontsize="11pt")


def build_both(
    resume_md: str,
    cover_letter_md: str,
    output_dir: str,
    company: str = "company",
    role: str = "role",
) -> dict:
    """
    Build both resume and cover letter PDFs.

    Args:
        resume_md: Path to resume markdown
        cover_letter_md: Path to cover letter markdown
        output_dir: Output directory
        company: Company name (for filename)
        role: Role name (for filename)

    Returns:
        Dict with paths to generated PDFs and success status
    """
    # Sanitize names for filenames
    company_slug = company.lower().replace(" ", "_").replace("/", "_")[:30]
    role_slug = role.lower().replace(" ", "_").replace("/", "_")[:30]

    resume_pdf = str(Path(output_dir) / f"resume_{company_slug}_{role_slug}.pdf")
    cover_pdf = str(Path(output_dir) / f"cover_letter_{company_slug}_{role_slug}.pdf")

    resume_ok = build_resume_pdf(resume_md, resume_pdf)
    cover_ok = build_cover_letter_pdf(cover_letter_md, cover_pdf)

    return {
        "resume_pdf": resume_pdf if resume_ok else None,
        "cover_letter_pdf": cover_pdf if cover_ok else None,
        "resume_success": resume_ok,
        "cover_letter_success": cover_ok,
        "all_success": resume_ok and cover_ok,
    }


def main():
    parser = argparse.ArgumentParser(description="Build PDF from markdown")
    parser.add_argument("--input", "-i", help="Input markdown file")
    parser.add_argument("--output", "-o", help="Output PDF file")
    parser.add_argument("--type", choices=["resume", "cover_letter"], default="resume",
                        help="Document type (affects margins)")
    parser.add_argument("--resume", help="Resume markdown (for batch mode)")
    parser.add_argument("--cover", help="Cover letter markdown (for batch mode)")
    parser.add_argument("--output-dir", help="Output directory (for batch mode)")
    parser.add_argument("--company", default="company", help="Company name for filename")
    parser.add_argument("--role", default="role", help="Role name for filename")

    args = parser.parse_args()

    if args.resume and args.cover and args.output_dir:
        # Batch mode
        result = build_both(args.resume, args.cover, args.output_dir, args.company, args.role)
        if result["all_success"]:
            print(f"Resume PDF: {result['resume_pdf']}")
            print(f"Cover Letter PDF: {result['cover_letter_pdf']}")
        else:
            print("Some PDFs failed to generate", file=sys.stderr)
            sys.exit(1)
    elif args.input and args.output:
        # Single file mode
        if args.type == "cover_letter":
            ok = build_cover_letter_pdf(args.input, args.output)
        else:
            ok = build_resume_pdf(args.input, args.output)

        if ok:
            print(f"PDF generated: {args.output}")
        else:
            sys.exit(1)
    else:
        parser.error("Provide --input/--output for single file, or --resume/--cover/--output-dir for batch")


if __name__ == "__main__":
    main()
