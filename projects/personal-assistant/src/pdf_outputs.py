#!/usr/bin/env python3
"""
PDF Output Generator for Interview Prep AI Assistant

Generates various PDF outputs from research data:
- Cheat Sheet: One-page quick reference
- Talking Points: Printable bullet points
- Flashcards: Q&A practice cards
- Day-of Checklist: Pre-interview preparation

Uses markdown-to-PDF conversion for clean, printable output.

Usage:
    # Generate cheat sheet from research
    python pdf_outputs.py --input .tmp/interview_research_google.json --output cheat-sheet

    # Generate talking points
    python pdf_outputs.py --input .tmp/interview_research_google.json --output talking-points

    # Generate flashcards
    python pdf_outputs.py --input .tmp/interview_research_google.json --output flashcards

    # Generate day-of checklist
    python pdf_outputs.py --input .tmp/interview_research_google.json --output checklist

    # All outputs
    python pdf_outputs.py --input .tmp/interview_research_google.json --output all
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def generate_cheat_sheet_markdown(research: dict) -> str:
    """Generate a one-page cheat sheet in markdown format."""
    company = research.get("company_overview", {})
    role = research.get("role_analysis", {})
    culture = research.get("company_culture", {})
    questions = research.get("interview_insights", {}).get("common_questions", [])
    talking_points = research.get("talking_points", {})

    company_name = company.get("name", "Company")
    role_name = role.get("title", "Position")

    # Get key info
    mission = company.get("mission", "")
    products = company.get("products_services", [])[:3]
    values = culture.get("core_values", [])[:4]
    skills = role.get("required_skills", [])[:5]
    responsibilities = role.get("key_responsibilities", [])[:4]

    # Build markdown
    md = f"""# {company_name} - {role_name}
## Interview Cheat Sheet
*Generated {datetime.now().strftime("%B %d, %Y")}*

---

## Company at a Glance
**Mission:** {mission}

**Key Products:** {', '.join(products) if products else 'N/A'}

**Core Values:** {', '.join(values) if values else 'N/A'}

---

## Role Overview
**Key Responsibilities:**
"""
    for resp in responsibilities:
        md += f"- {resp}\n"

    md += f"""
**Required Skills:** {', '.join(skills) if skills else 'N/A'}

---

## Top Questions to Prepare
"""
    for i, q in enumerate(questions[:5], 1):
        question = q.get("question", q) if isinstance(q, dict) else q
        md += f"{i}. {question}\n"

    md += """
---

## Your Key Messages
"""
    strengths = talking_points.get("key_strengths", [])[:3]
    for strength in strengths:
        md += f"- **{strength}**\n"

    md += """
---

## Questions to Ask Them
"""
    questions_to_ask = research.get("interview_insights", {}).get("questions_to_ask", [])[:3]
    for q in questions_to_ask:
        question = q.get("question", q) if isinstance(q, dict) else q
        md += f"- {question}\n"

    md += """
---

## Quick Reminders
- Research your interviewer(s) on LinkedIn
- Prepare 2-3 STAR format stories
- Have questions ready for each interviewer
- Review recent company news
- Arrive 10-15 minutes early (or test video setup)
"""

    return md


def generate_talking_points_markdown(research: dict) -> str:
    """Generate talking points document in markdown format."""
    company = research.get("company_overview", {})
    role = research.get("role_analysis", {})
    talking_points = research.get("talking_points", {})
    experience_highlights = research.get("experience_highlights", [])

    company_name = company.get("name", "Company")
    role_name = role.get("title", "Position")

    md = f"""# Talking Points
## {company_name} - {role_name}
*Interview Preparation*

---

## Why {company_name}?
"""
    why_company = talking_points.get("why_this_company", [])
    for point in why_company[:4]:
        md += f"- {point}\n"

    md += f"""
---

## Why This Role?
"""
    why_role = talking_points.get("why_this_role", [])
    for point in why_role[:4]:
        md += f"- {point}\n"

    md += """
---

## Your Key Strengths
"""
    strengths = talking_points.get("key_strengths", [])
    for strength in strengths[:5]:
        md += f"### {strength}\n"
        md += f"*Example story to support this...*\n\n"

    md += """
---

## Relevant Experience Highlights
"""
    for i, exp in enumerate(experience_highlights[:5], 1):
        experience = exp.get("experience", "") if isinstance(exp, dict) else exp
        relevance = exp.get("relevance", "") if isinstance(exp, dict) else ""
        md += f"""### {i}. {experience[:60]}...
**Why it matters:** {relevance}

"""

    md += """
---

## Potential Weaknesses (How to Address)
"""
    weaknesses = talking_points.get("potential_weaknesses", [])
    for w in weaknesses[:3]:
        weakness = w.get("weakness", w) if isinstance(w, dict) else w
        mitigation = w.get("mitigation", "Prepare an honest response") if isinstance(w, dict) else ""
        md += f"- **{weakness}**: {mitigation}\n"

    md += """
---

## Closing Statement
*Prepare a strong closing that reinforces your interest and fit*

"Thank you for your time today. Based on our conversation, I'm even more excited about this opportunity. [Specific reason from the interview]. I'm confident that my experience in [X] would allow me to [contribute to Y]. What are the next steps in the process?"
"""

    return md


def generate_flashcards_markdown(research: dict) -> str:
    """Generate Q&A flashcards in markdown format."""
    company = research.get("company_overview", {})
    questions = research.get("interview_insights", {}).get("common_questions", [])
    company_name = company.get("name", "Company")

    md = f"""# Interview Flashcards
## {company_name}
*Practice these Q&A pairs*

---

"""
    for i, q in enumerate(questions[:10], 1):
        if isinstance(q, dict):
            question = q.get("question", "")
            strategy = q.get("strategy", "Use STAR format to structure your response")
        else:
            question = q
            strategy = "Use STAR format to structure your response"

        md += f"""## Card {i}

**Q:** {question}

**Strategy:** {strategy}

**Your Answer:**
_______________________
_______________________
_______________________

---

"""

    # Add behavioral questions
    behavioral_questions = [
        ("Tell me about yourself", "2-minute pitch: current role → past experience → why this role"),
        ("Why do you want to work here?", "Research-based answer + personal connection"),
        ("What's your greatest weakness?", "Genuine weakness + steps you're taking to improve"),
        ("Tell me about a challenge you overcame", "STAR format with quantifiable results"),
        ("Where do you see yourself in 5 years?", "Growth within company/industry alignment"),
    ]

    md += "## Bonus: Common Behavioral Questions\n\n"
    for q, hint in behavioral_questions:
        md += f"""### {q}
**Hint:** {hint}

---

"""

    return md


def generate_checklist_markdown(research: dict) -> str:
    """Generate day-of preparation checklist in markdown format."""
    company = research.get("company_overview", {})
    role = research.get("role_analysis", {})
    checklist = research.get("preparation_checklist", [])

    company_name = company.get("name", "Company")
    role_name = role.get("title", "Position")

    md = f"""# Interview Day Checklist
## {company_name} - {role_name}

---

## Week Before
- [ ] Research your interviewer(s) on LinkedIn
- [ ] Review company's recent news and press releases
- [ ] Practice answering common interview questions
- [ ] Prepare your STAR format stories
- [ ] Plan your outfit
- [ ] Confirm interview time, location, and format

---

## Day Before
- [ ] Review this cheat sheet one more time
- [ ] Prepare your bag/materials:
    - [ ] Extra copies of resume
    - [ ] Notepad and pen
    - [ ] List of questions to ask
    - [ ] Portfolio/work samples (if applicable)
- [ ] Plan your route (add 15 min buffer)
- [ ] Get a good night's sleep
- [ ] Set multiple alarms

---

## Morning Of
- [ ] Eat a good breakfast
- [ ] Review your talking points
- [ ] Check the news for {company_name} updates
- [ ] Dress professionally
- [ ] Leave with plenty of time

---

## For Virtual Interviews
- [ ] Test your camera and microphone
- [ ] Check your internet connection
- [ ] Find a quiet, well-lit space
- [ ] Close unnecessary applications
- [ ] Have backup phone number ready
- [ ] Log in 5 minutes early

---

## Right Before
- [ ] Use the restroom
- [ ] Silence your phone
- [ ] Take 3 deep breaths
- [ ] Smile and be confident!

---

## Questions to Ask (Pick 2-3)
"""
    questions_to_ask = research.get("interview_insights", {}).get("questions_to_ask", [])
    for q in questions_to_ask[:5]:
        question = q.get("question", q) if isinstance(q, dict) else q
        md += f"- [ ] {question}\n"

    md += """
---

## Post-Interview
- [ ] Send thank-you email within 24 hours
- [ ] Note key discussion points for follow-up
- [ ] Reflect on what went well and areas to improve
- [ ] Follow up if you haven't heard back in 1 week

---

*Good luck! You've got this!*
"""

    return md


def markdown_to_pdf(markdown_content: str, output_path: str) -> bool:
    """Convert markdown to PDF using pandoc or fallback to HTML."""
    # First, save markdown
    md_path = output_path.replace(".pdf", ".md")
    with open(md_path, "w") as f:
        f.write(markdown_content)

    # Try pandoc first
    try:
        subprocess.run(
            ["pandoc", md_path, "-o", output_path, "--pdf-engine=xelatex"],
            capture_output=True,
            check=True,
        )
        print(f"  ✓ Created PDF: {output_path}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Try pandoc with different engine
    try:
        subprocess.run(
            ["pandoc", md_path, "-o", output_path],
            capture_output=True,
            check=True,
        )
        print(f"  ✓ Created PDF: {output_path}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback: keep markdown file
    print(f"  ✓ Created Markdown: {md_path}")
    print(f"    (Install pandoc for PDF output: brew install pandoc)")
    return False


def generate_outputs(research_path: str, output_type: str, output_dir: str = ".tmp") -> dict:
    """Generate requested output(s) from research data."""
    # Load research
    with open(research_path) as f:
        research = json.load(f)

    company_name = research.get("company_overview", {}).get("name", "company")
    company_slug = company_name.lower().replace(" ", "_")

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    results = {}
    generators = {
        "cheat-sheet": ("cheat_sheet", generate_cheat_sheet_markdown),
        "talking-points": ("talking_points", generate_talking_points_markdown),
        "flashcards": ("flashcards", generate_flashcards_markdown),
        "checklist": ("checklist", generate_checklist_markdown),
    }

    if output_type == "all":
        types_to_generate = generators.keys()
    else:
        types_to_generate = [output_type]

    for out_type in types_to_generate:
        if out_type not in generators:
            print(f"  ⚠ Unknown output type: {out_type}")
            continue

        suffix, generator_func = generators[out_type]
        print(f"\nGenerating {out_type}...")

        # Generate markdown
        markdown_content = generator_func(research)

        # Output paths
        md_path = f"{output_dir}/{company_slug}_{suffix}.md"
        pdf_path = f"{output_dir}/{company_slug}_{suffix}.pdf"

        # Save markdown
        with open(md_path, "w") as f:
            f.write(markdown_content)
        print(f"  ✓ Created: {md_path}")

        # Try to create PDF
        pdf_created = markdown_to_pdf(markdown_content, pdf_path)

        results[out_type] = {
            "markdown": md_path,
            "pdf": pdf_path if pdf_created else None,
        }

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate PDF outputs from interview research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output types:
    cheat-sheet     One-page quick reference with key info
    talking-points  Your key messages and stories to communicate
    flashcards      Q&A practice cards for common questions
    checklist       Day-of preparation checklist
    all             Generate all output types

Examples:
    python pdf_outputs.py --input .tmp/interview_research_google.json --output cheat-sheet
    python pdf_outputs.py --input .tmp/interview_research_google.json --output all
        """
    )

    parser.add_argument("--input", required=True, help="Path to research JSON file")
    parser.add_argument(
        "--output",
        choices=["cheat-sheet", "talking-points", "flashcards", "checklist", "all"],
        default="cheat-sheet",
        help="Output type to generate"
    )
    parser.add_argument("--output-dir", default=".tmp", help="Output directory (default: .tmp)")

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Research file not found: {args.input}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print("Interview Prep - PDF Output Generator")
    print(f"{'=' * 60}")

    results = generate_outputs(args.input, args.output, args.output_dir)

    print(f"\n{'=' * 60}")
    print("Generation Complete!")
    print(f"{'=' * 60}")

    for out_type, paths in results.items():
        print(f"\n{out_type}:")
        print(f"  Markdown: {paths['markdown']}")
        if paths.get('pdf'):
            print(f"  PDF: {paths['pdf']}")

    # Copy to Downloads suggestion
    print(f"\n💡 To copy to Downloads folder:")
    for out_type, paths in results.items():
        filename = Path(paths['markdown']).name
        print(f"   cp {paths['markdown']} ~/Downloads/{filename}")


if __name__ == "__main__":
    main()
