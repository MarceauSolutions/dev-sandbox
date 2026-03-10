#!/usr/bin/env python3
"""
Document Generator - Generate legal documents from templates.

Usage:
    python src/document_generator.py generate      # Generate document from template
    python src/document_generator.py list-templates # List available templates
"""

import argparse
import shutil
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_DIR / "templates"
DATA_DIR = PROJECT_DIR / "data"


def list_templates(args):
    """List available document templates."""
    templates = list(TEMPLATES_DIR.glob("*.md"))
    if not templates:
        print("No templates found.")
        return

    print(f"\nAvailable Templates ({len(templates)}):\n")
    for t in sorted(templates):
        print(f"  {t.stem:30s} ({t.name})")


def generate_document(args):
    """Generate a document from a template."""
    template_name = args.template
    template_file = TEMPLATES_DIR / f"{template_name}.md"

    if not template_file.exists():
        print(f"Template not found: {template_name}")
        print(f"Available templates:")
        for t in TEMPLATES_DIR.glob("*.md"):
            print(f"  {t.stem}")
        return

    output_dir = Path(args.output) if args.output else DATA_DIR / "filings"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d")
    output_file = output_dir / f"{timestamp}-{template_name}.md"

    shutil.copy2(template_file, output_file)
    print(f"Document generated: {output_file}")
    print(f"Edit the generated file to fill in case-specific details.")


def main():
    parser = argparse.ArgumentParser(description="Legal Document Generator")
    subparsers = parser.add_subparsers(dest="command")

    # Generate
    gen_parser = subparsers.add_parser("generate", help="Generate document from template")
    gen_parser.add_argument("--template", required=True, help="Template name (without .md)")
    gen_parser.add_argument("--output", default=None, help="Output directory")

    # List templates
    subparsers.add_parser("list-templates", help="List available templates")

    args = parser.parse_args()

    commands = {
        "generate": generate_document,
        "list-templates": list_templates,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
