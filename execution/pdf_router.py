#!/usr/bin/env python3
"""
pdf_router.py — Auto-route branded PDFs to organized folder locations.

Determines the correct destination folder based on template type, content
keywords, and metadata. Ensures all generated content lands in the right
place automatically.

Usage:
    # Auto-route a PDF based on its template and content
    python execution/pdf_router.py --template workout --title "5-Day Athletic Program" --file output.pdf

    # Route an existing PDF by analyzing its filename/metadata
    python execution/pdf_router.py --auto --file docs/some-random-output.pdf

    # Just get the destination path without moving
    python execution/pdf_router.py --template workout --title "test" --dry-run

    # Use from Python
    from execution.pdf_router import route_pdf
    dest = route_pdf(template="workout", title="My Program", source_path="output.pdf")
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# =============================================================================
# ROUTING TABLE
# =============================================================================

# Template → default folder mapping
TEMPLATE_ROUTES = {
    "workout": "projects/marceau-solutions/fitness/content/workout-programs",
    "nutrition": "projects/marceau-solutions/fitness/content/nutrition-guides",
    "peptide": "docs/medical/peptides",
    "progress": "projects/marceau-solutions/fitness/content/client-reports",
    "onboarding": "projects/marceau-solutions/fitness/clients/pt-business/onboarding",
    "challenge": "projects/marceau-solutions/fitness/content/lead-magnets",
    "generic": None,  # Requires keyword analysis
}

# Keyword → folder mapping (checked when template is "generic" or unknown)
KEYWORD_ROUTES = [
    # Medical / Health
    (["dystonia", "movement disorder", "dbs", "deep brain"], "docs/medical/dystonia"),
    (["peptide", "tesamorelin", "gh secretagogue", "bpc-157"], "docs/medical/peptides"),
    (["apothecary", "herbal", "tincture", "botanical", "remedy"], "docs/medical/herbal-medicine"),
    (["chargeback", "dispute", "refund", "evidence package", "billing"], "docs/medical/billing-disputes"),
    (["treatment", "clinical", "protocol", "medical"], "docs/medical"),

    # Fitness content
    (["workout", "program", "training plan", "exercise", "athletic", "strength"], "projects/marceau-solutions/fitness/content/workout-programs"),
    (["nutrition", "meal plan", "diet", "macros", "calorie"], "projects/marceau-solutions/fitness/content/nutrition-guides"),
    (["lead magnet", "free guide", "challenge", "7-day", "7 day"], "projects/marceau-solutions/fitness/content/lead-magnets"),
    (["offer", "pricing", "package", "coaching offer"], "projects/marceau-solutions/fitness/content/offers"),
    (["textbook", "education", "course", "certification"], "projects/marceau-solutions/fitness/content/education"),

    # Business
    (["operations manual", "sop", "business guide", "client acquisition"], "docs/business/guides"),
    (["waiver", "liability", "contract", "terms of service", "cancellation"], "docs/business/legal"),
    (["report", "analytics", "revenue", "campaign"], "docs/business/reports"),
    (["weather", "naples", "forecast"], "docs/reports/weather"),

    # Client-specific
    (["boabfit", "julia"], "projects/marceau-solutions/fitness/clients/boabfit"),
    (["hvac", "sw florida comfort"], "projects/marceau-solutions/digital/clients/swflorida-hvac"),
    (["flames", "passion"], "projects/marceau-solutions/digital/clients/flames-of-passion"),
]

# Fallback if nothing matches
DEFAULT_ROUTE = "docs/generated"


def determine_route(template=None, title="", description="", filename="", tags=None):
    """
    Determine the correct destination folder for a PDF.

    Args:
        template: Template name from branded_pdf_engine (workout, nutrition, etc.)
        title: PDF title or document name
        description: Optional description/summary of content
        filename: Original filename (used for keyword analysis)
        tags: Optional list of tags/categories

    Returns:
        Relative path from project root to destination folder
    """
    # Step 1: Check template-based routing
    if template and template in TEMPLATE_ROUTES:
        route = TEMPLATE_ROUTES[template]
        if route is not None:
            return route

    # Step 2: Keyword analysis on title + description + filename
    search_text = f"{title} {description} {filename} {' '.join(tags or [])}".lower()

    for keywords, folder in KEYWORD_ROUTES:
        if any(kw in search_text for kw in keywords):
            return folder

    # Step 3: Fallback
    return DEFAULT_ROUTE


def route_pdf(source_path, template=None, title="", description="", tags=None, dry_run=False, copy=False):
    """
    Route a PDF file to its correct location.

    Args:
        source_path: Path to the source PDF file
        template: Template type
        title: Document title
        description: Document description
        tags: Category tags
        dry_run: If True, just return the destination without moving
        copy: If True, copy instead of move

    Returns:
        Destination path (absolute)
    """
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    folder = determine_route(
        template=template,
        title=title,
        description=description,
        filename=source.name,
        tags=tags,
    )

    dest_dir = PROJECT_ROOT / folder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / source.name

    # Handle name conflicts
    if dest_path.exists() and dest_path != source:
        stem = dest_path.stem
        suffix = dest_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{stem}-{counter}{suffix}"
            counter += 1

    if dry_run:
        return str(dest_path)

    if copy:
        shutil.copy2(str(source), str(dest_path))
    else:
        shutil.move(str(source), str(dest_path))

    return str(dest_path)


def auto_route_file(filepath, dry_run=False, copy=False):
    """Route a file based solely on its filename (no template/title hints)."""
    p = Path(filepath)
    return route_pdf(
        source_path=filepath,
        title=p.stem.replace("-", " ").replace("_", " "),
        dry_run=dry_run,
        copy=copy,
    )


def main():
    parser = argparse.ArgumentParser(description="PDF Router — auto-file branded PDFs")
    parser.add_argument("--file", "-f", required=True, help="PDF file to route")
    parser.add_argument("--template", "-t", help="Template type (workout, nutrition, etc.)")
    parser.add_argument("--title", help="Document title")
    parser.add_argument("--description", help="Document description")
    parser.add_argument("--tags", nargs="*", help="Category tags")
    parser.add_argument("--auto", action="store_true", help="Auto-detect from filename")
    parser.add_argument("--dry-run", action="store_true", help="Show destination without moving")
    parser.add_argument("--copy", action="store_true", help="Copy instead of move")
    args = parser.parse_args()

    if args.auto:
        dest = auto_route_file(args.file, dry_run=args.dry_run, copy=args.copy)
    else:
        dest = route_pdf(
            source_path=args.file,
            template=args.template,
            title=args.title or "",
            description=args.description or "",
            tags=args.tags,
            dry_run=args.dry_run,
            copy=args.copy,
        )

    if args.dry_run:
        print(f"Would route to: {dest}")
    else:
        print(f"Routed to: {dest}")


if __name__ == "__main__":
    main()
