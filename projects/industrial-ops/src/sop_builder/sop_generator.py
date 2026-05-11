#!/usr/bin/env python3
"""
SOP Generator — Collier County Standard Operating Procedures

Generates professional, county-neutral SOPs as Markdown + PDF.

Modes:
    1. Structured input (JSON):  --input sop.json
    2. Rough notes (text):       --from-notes notes.txt --title "..." --sop-number "..."
       (Requires ANTHROPIC_API_KEY — uses Claude to structure notes into SOP JSON)

Usage:
    python -m projects.industrial-ops.src.sop_builder.sop_generator \\
        --input notes.txt --from-notes \\
        --sop-number WW-SOP-001 \\
        --title "Front Desk Agent Daily Procedures" \\
        --department "Wastewater Operations" \\
        --prepared-by "William Marceau" \\
        --output-dir output/

Output:
    output/WW-SOP-001_front-desk-agent.md
    output/WW-SOP-001_front-desk-agent.pdf
"""

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

import markdown as md_lib
from weasyprint import HTML, CSS

CSS_PATH = Path(__file__).parent / "county_sop.css"


def _render_pdf(markdown_text: str, pdf_path: Path, css_path: Path) -> None:
    """Convert markdown → HTML → PDF using weasyprint (no phantom table headers)."""
    html_body = md_lib.markdown(markdown_text, extensions=["tables", "sane_lists"])
    html_doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>{html_body}</body></html>"""
    HTML(string=html_doc).write_pdf(
        str(pdf_path),
        stylesheets=[CSS(filename=str(css_path))],
    )


def render_markdown(data: dict[str, Any]) -> str:
    """
    Render an SOP dict into Collier County markdown format.

    Required keys: sop_number, title, department, version, effective_date,
                   prepared_by, approved_by, purpose, scope, procedure
    Optional keys: definitions, responsibilities, exceptions, references,
                   revision_history
    """
    lines: list[str] = []

    # Header block
    lines.append(f"# Collier County — {data.get('department', '[Department]')}")
    lines.append("")
    lines.append("**Standard Operating Procedure**")
    lines.append("")

    # Metadata block as a 2-column table
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append(f"| **SOP Number** | {data.get('sop_number', '[TBD]')} |")
    lines.append(f"| **Title** | {data.get('title', '[Untitled]')} |")
    lines.append(f"| **Effective Date** | {data.get('effective_date', date.today().isoformat())} |")
    lines.append(f"| **Version** | {data.get('version', '1.0')} |")
    lines.append(f"| **Prepared by** | {data.get('prepared_by', '[Author]')} |")
    lines.append(f"| **Approved by** | {data.get('approved_by', '[Supervisor Name]')} |")
    lines.append("")

    # 1. Purpose
    lines.append("## 1. Purpose")
    lines.append("")
    lines.append(data.get("purpose", "[Define the purpose of this SOP.]"))
    lines.append("")

    # 2. Scope
    lines.append("## 2. Scope")
    lines.append("")
    lines.append(data.get("scope", "[Define who and what this SOP applies to.]"))
    lines.append("")

    # 3. Definitions
    definitions = data.get("definitions") or []
    if definitions:
        lines.append("## 3. Definitions")
        lines.append("")
        lines.append("| Term | Definition |")
        lines.append("|---|---|")
        for d in definitions:
            term = d.get("term", "").replace("|", "\\|")
            defn = d.get("definition", "").replace("|", "\\|")
            lines.append(f"| **{term}** | {defn} |")
        lines.append("")

    # 4. Responsibilities
    responsibilities = data.get("responsibilities") or []
    if responsibilities:
        lines.append("## 4. Responsibilities")
        lines.append("")
        lines.append("| Role | Responsibility |")
        lines.append("|---|---|")
        for r in responsibilities:
            role = r.get("role", "").replace("|", "\\|")
            owns = r.get("owns", "").replace("|", "\\|")
            lines.append(f"| **{role}** | {owns} |")
        lines.append("")

    # 5. Procedure
    lines.append("## 5. Procedure")
    lines.append("")
    procedure = data.get("procedure") or []
    if not procedure:
        lines.append("[Procedure phases and steps go here.]")
        lines.append("")
    for i, phase in enumerate(procedure, start=1):
        phase_name = phase.get("phase", f"Phase {i}")
        lines.append(f"### 5.{i} {phase_name}")
        lines.append("")
        steps = phase.get("steps") or []
        for j, step in enumerate(steps, start=1):
            lines.append(f"{j}. {step}")
        lines.append("")

    # 6. Exceptions & Escalation
    exceptions = data.get("exceptions")
    if exceptions:
        lines.append("## 6. Exceptions & Escalation")
        lines.append("")
        if isinstance(exceptions, list):
            for item in exceptions:
                lines.append(f"- {item}")
        else:
            lines.append(str(exceptions))
        lines.append("")

    # 7. References
    references = data.get("references") or []
    if references:
        lines.append("## 7. References")
        lines.append("")
        for ref in references:
            lines.append(f"- {ref}")
        lines.append("")

    # 8. Revision History
    revisions = data.get("revision_history") or [
        {
            "version": data.get("version", "1.0"),
            "date": data.get("effective_date", date.today().isoformat()),
            "author": data.get("prepared_by", "[Author]"),
            "changes": "Initial release.",
        }
    ]
    lines.append("## 8. Revision History")
    lines.append("")
    lines.append("| Version | Date | Author | Changes |")
    lines.append("|---|---|---|---|")
    for rev in revisions:
        lines.append(
            f"| {rev.get('version', '')} | {rev.get('date', '')} | "
            f"{rev.get('author', '')} | {rev.get('changes', '')} |"
        )
    lines.append("")

    return "\n".join(lines)


def structure_notes_with_ai(
    notes: str,
    title: str,
    sop_number: str,
    department: str,
    prepared_by: str,
    approved_by: str = "[Supervisor Name]",
) -> dict[str, Any]:
    """
    Use Claude API to convert rough notes into a structured SOP dict.

    Requires ANTHROPIC_API_KEY in environment.
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("ERROR: anthropic SDK not installed. Run: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set in environment.")

    client = Anthropic(api_key=api_key)

    system_prompt = (
        "You convert rough process notes into a structured Standard Operating Procedure "
        "for Collier County government documentation. Output ONLY valid JSON matching the "
        "schema described below. Do not include any prose, code fences, or explanation.\n\n"
        "Schema:\n"
        "{\n"
        '  "purpose": "1-2 sentences explaining why this SOP exists",\n'
        '  "scope": "Who and what this applies to",\n'
        '  "definitions": [{"term": "...", "definition": "..."}],  // optional\n'
        '  "responsibilities": [{"role": "...", "owns": "..."}],  // optional\n'
        '  "procedure": [\n'
        '    {"phase": "Phase or task name", "steps": ["Step 1...", "Step 2..."]}\n'
        "  ],\n"
        '  "exceptions": "What to do when the normal process breaks down",  // optional\n'
        '  "references": ["Related docs, system manuals"]  // optional\n'
        "}\n\n"
        "Write in plain, professional government-document tone. No fluff, no opinions. "
        "Use imperative voice for steps ('Log into the system', not 'You should log in')."
    )

    user_msg = (
        f"SOP Title: {title}\n"
        f"SOP Number: {sop_number}\n"
        f"Department: {department}\n\n"
        f"Process notes:\n{notes}"
    )

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = message.content[0].text.strip()
    # Defensive: strip code fences if Claude included them despite instruction
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()

    try:
        structured = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: Claude returned invalid JSON: {e}\nRaw output:\n{raw}")

    return {
        "sop_number": sop_number,
        "title": title,
        "department": department,
        "version": "1.0",
        "effective_date": date.today().isoformat(),
        "prepared_by": prepared_by,
        "approved_by": approved_by,
        **structured,
    }


class SOPGenerator:
    """Top-level orchestrator: structured data → markdown → PDF."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _slug(self, text: str) -> str:
        keep = "".join(c if c.isalnum() or c in "-_" else "-" for c in text.lower())
        while "--" in keep:
            keep = keep.replace("--", "-")
        return keep.strip("-")

    def generate(self, data: dict[str, Any]) -> tuple[Path, Path]:
        """Render markdown and PDF, return both paths."""
        sop_number = data.get("sop_number", "SOP-000")
        title_slug = self._slug(data.get("title", "untitled"))
        base = f"{sop_number}_{title_slug}"

        md_path = self.output_dir / f"{base}.md"
        pdf_path = self.output_dir / f"{base}.pdf"

        markdown = render_markdown(data)
        md_path.write_text(markdown, encoding="utf-8")

        _render_pdf(markdown, pdf_path, CSS_PATH)
        print(f"  Wrote {md_path.name} and {pdf_path.name}")

        return md_path, pdf_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="Path to input file (JSON for structured, .txt for notes)")
    parser.add_argument("--from-notes", action="store_true", help="Treat input as rough notes and use Claude to structure")
    parser.add_argument("--sop-number", help="SOP number (e.g. WW-SOP-001). Required when --from-notes")
    parser.add_argument("--title", help="SOP title. Required when --from-notes")
    parser.add_argument("--department", default="Wastewater Operations", help="Department name")
    parser.add_argument("--prepared-by", default="William Marceau, I&E Technician", help="Author name")
    parser.add_argument("--approved-by", default="[Supervisor Name]", help="Approver name")
    parser.add_argument("--output-dir", default="projects/industrial-ops/data/output", help="Output directory")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"ERROR: input file not found: {input_path}")

    if args.from_notes:
        if not args.sop_number or not args.title:
            sys.exit("ERROR: --from-notes requires --sop-number and --title")
        notes = input_path.read_text(encoding="utf-8")
        print(f"→ Structuring notes via Claude API ({len(notes)} chars)...")
        data = structure_notes_with_ai(
            notes=notes,
            title=args.title,
            sop_number=args.sop_number,
            department=args.department,
            prepared_by=args.prepared_by,
            approved_by=args.approved_by,
        )
    else:
        data = json.loads(input_path.read_text(encoding="utf-8"))

    gen = SOPGenerator(output_dir=Path(args.output_dir))
    md_path, pdf_path = gen.generate(data)

    print(f"\nMarkdown: {md_path}")
    print(f"PDF:      {pdf_path}")


if __name__ == "__main__":
    main()
