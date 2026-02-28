#!/usr/bin/env python3
"""
Resume Parser — Extract structured profile data from uploaded PDF/DOCX resumes.

Takes a resume file (PDF or DOCX) and uses Claude to extract structured profile
data in the same format as resume_data.json.

Usage:
    # From CLI
    python -m src.engine.resume_parser --file resume.pdf
    python -m src.engine.resume_parser --file resume.docx --output profile.json

    # As module
    from src.engine.resume_parser import parse_resume
    profile = parse_resume("/path/to/resume.pdf")

    # From raw text (for webhook usage)
    from src.engine.resume_parser import parse_resume_text
    profile = parse_resume_text(raw_resume_text)
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


PARSE_RESUME_PROMPT = """You are an expert resume parser. Extract ALL information from this resume into structured JSON.

## RESUME TEXT:
{resume_text}

## OUTPUT FORMAT (match this exactly):

```json
{{
  "contact": {{
    "name": "Full Name",
    "phone": "phone number or empty string",
    "email": "email or empty string",
    "linkedin": "linkedin URL or empty string",
    "github": "github URL or empty string",
    "location": "City, State or empty string",
    "relocation": "any relocation notes or empty string"
  }},
  "summaries": {{
    "default": "Professional summary exactly as written on the resume. If none exists, generate a 2-sentence summary from the experience."
  }},
  "skills": {{
    "languages": ["programming languages"],
    "backend": ["frameworks, databases, APIs"],
    "cloud_devops": ["cloud platforms, CI/CD, containers"],
    "ai_ml": ["AI/ML tools and frameworks"],
    "automation": ["automation tools"],
    "tools": ["other tools and software"],
    "other": ["any skills that don't fit above categories"]
  }},
  "experience": {{
    "job_1": {{
      "title": "Job Title",
      "company": "Company Name",
      "location": "City, State",
      "dates": "Start – End",
      "bullets": {{
        "default": [
          "bullet point 1 exactly as written",
          "bullet point 2 exactly as written"
        ]
      }}
    }},
    "job_2": {{
      "title": "...",
      "company": "...",
      "location": "...",
      "dates": "...",
      "bullets": {{
        "default": ["..."]
      }}
    }}
  }},
  "education": [
    {{
      "degree": "Degree Name",
      "institution": "School Name",
      "location": "City, State",
      "graduation": "Month Year or expected date",
      "gpa": "GPA if listed, empty string otherwise",
      "highlights": ["relevant coursework, honors, etc."]
    }}
  ],
  "certifications": ["cert 1", "cert 2"],
  "projects": [
    {{
      "name": "Project Name",
      "description": "1-2 sentence description",
      "tech": ["technologies used"]
    }}
  ]
}}
```

## RULES:
- Extract EVERY piece of information from the resume — don't skip anything
- Preserve exact wording of bullet points — don't rewrite or summarize
- Use empty strings "" for missing fields, never null
- Use empty arrays [] for missing list fields
- For skills, categorize intelligently — put each skill in the most relevant bucket
- Number experience entries sequentially: job_1, job_2, job_3, etc. (most recent first)
- If a section doesn't exist on the resume, include it with empty values
- Output ONLY valid JSON, no markdown fences, no commentary"""


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except ImportError:
        print("ERROR: pip install pdfplumber")
        sys.exit(1)


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        import docx
        doc = docx.Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    except ImportError:
        print("ERROR: pip install python-docx")
        sys.exit(1)


def extract_text(file_path: str) -> str:
    """Extract text from PDF or DOCX file."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    elif ext in (".txt", ".md"):
        with open(file_path, "r") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF, DOCX, or TXT.")


def parse_resume_text(
    resume_text: str,
    model: str = "claude-sonnet-4-5-20250929",
) -> dict:
    """
    Parse raw resume text into structured profile JSON using Claude.

    Args:
        resume_text: Raw text extracted from resume
        model: Claude model to use

    Returns:
        Structured profile dict matching resume_data.json format
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model=model,
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": PARSE_RESUME_PROMPT.format(resume_text=resume_text)
        }]
    )

    raw = response.content[0].text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    return json.loads(raw)


def parse_resume(
    file_path: str,
    model: str = "claude-sonnet-4-5-20250929",
) -> dict:
    """
    Parse a resume file (PDF/DOCX/TXT) into structured profile JSON.

    Args:
        file_path: Path to the resume file
        model: Claude model to use

    Returns:
        Structured profile dict matching resume_data.json format
    """
    resume_text = extract_text(file_path)

    if not resume_text.strip():
        raise ValueError(f"Could not extract any text from {file_path}")

    return parse_resume_text(resume_text, model=model)


def main():
    parser = argparse.ArgumentParser(description="Parse resume into structured profile JSON")
    parser.add_argument("--file", "-f", required=True, help="Path to resume (PDF, DOCX, or TXT)")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929")
    parser.add_argument("--cost", action="store_true", help="Estimate cost without running")

    args = parser.parse_args()

    if args.cost:
        print("Estimated cost: ~$0.02 (Sonnet, ~2K input + 2K output tokens)")
        return

    print(f"Parsing resume: {args.file}")
    profile = parse_resume(args.file, model=args.model)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(profile, f, indent=2)
        print(f"Profile saved to {args.output}")
    else:
        print(json.dumps(profile, indent=2))


if __name__ == "__main__":
    main()
