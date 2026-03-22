"""Digest runner — wraps the existing search logic with DB persistence and PDF generation."""

import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent  # dev-sandbox root
sys.path.insert(0, str(ROOT))

from execution.dystonia_research_digest import (
    search_pubmed,
    search_semantic_scholar,
    deduplicate,
    format_html_email,
    send_email,
    SEARCH_QUERIES,
)

from src.database import (
    create_digest,
    update_digest,
    save_papers,
    get_enabled_categories,
    seed_categories,
    init_db,
)

PDF_DIR = Path(__file__).resolve().parent.parent / "data" / "pdfs"


def generate_pdf(digest_id: int, papers_by_category: dict, days_back: int) -> str:
    """Generate a branded PDF for this digest. Returns the file path."""
    try:
        from execution.branded_pdf_engine import BrandedPDFEngine

        engine = BrandedPDFEngine()
        date_str = datetime.now().strftime("%Y-%m-%d")
        total = sum(len(v) for v in papers_by_category.values())

        data = {
            "title": f"Dystonia Research Digest — {datetime.now().strftime('%B %d, %Y')}",
            "subtitle": f"{total} papers | Last {days_back} days | PubMed + Semantic Scholar",
            "sections": [],
        }

        for category, papers in papers_by_category.items():
            if not papers:
                continue
            section_content = []
            for p in papers:
                authors_str = ", ".join(p.get("authors", [])[:4])
                if len(p.get("authors", [])) > 4:
                    authors_str += f" +{len(p['authors']) - 4} more"
                entry = f"**{p['title']}**\n"
                entry += f"{authors_str}\n"
                entry += f"*{p.get('journal', '')}* | {p.get('date', 'Unknown')}"
                if p.get("pmid"):
                    entry += f" | PMID: {p['pmid']}"
                if p.get("doi"):
                    entry += f" | DOI: {p['doi']}"
                entry += "\n"
                if p.get("abstract"):
                    entry += f"\n{p['abstract']}\n"
                section_content.append(entry)

            data["sections"].append({
                "heading": f"{category} ({len(papers)} papers)",
                "content": "\n---\n".join(section_content),
            })

        PDF_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(PDF_DIR / f"digest-{date_str}.pdf")

        # Use generic_document template with our structured data
        content_md = f"# {data['title']}\n\n*{data['subtitle']}*\n\n"
        for section in data["sections"]:
            content_md += f"## {section['heading']}\n\n{section['content']}\n\n"

        engine.generate_to_file("generic_document", {"title": data["title"], "content": content_md}, output_path)
        return output_path
    except Exception as e:
        print(f"  PDF generation failed: {e}")
        traceback.print_exc()
        return ""


def run_digest_with_persistence(days_back: int = 7, send_emails: bool = True) -> dict:
    """Run digest with full DB persistence, email, and PDF generation.

    Returns dict with digest_id, total_papers, status, error.
    """
    init_db()
    seed_categories(SEARCH_QUERIES)

    digest_id = create_digest(days_back)
    result = {"digest_id": digest_id, "total_papers": 0, "status": "running", "error": None}

    try:
        # Use DB-managed categories (allows enable/disable from UI)
        categories = get_enabled_categories()
        if not categories:
            categories = SEARCH_QUERIES

        all_papers = []
        papers_by_category = {}

        for query, category in categories:
            pm_papers = search_pubmed(query, days_back=days_back, max_results=5)
            s2_papers = search_semantic_scholar(query, days_back=days_back, max_results=5)

            category_papers = pm_papers + s2_papers
            if category_papers:
                all_papers.extend(category_papers)
                papers_by_category[category] = category_papers

        # Deduplicate within each category
        for cat in papers_by_category:
            papers_by_category[cat] = deduplicate(papers_by_category[cat])

        # Global dedup across categories
        seen = set()
        for cat in papers_by_category:
            unique = []
            for p in papers_by_category[cat]:
                key = p.get("doi") or p.get("pmid") or p["title"].lower()[:80]
                if key not in seen:
                    seen.add(key)
                    unique.append(p)
            papers_by_category[cat] = unique

        total_unique = sum(len(v) for v in papers_by_category.values())
        categories_with_results = len([c for c, p in papers_by_category.items() if p])

        # Save papers to DB
        save_papers(digest_id, papers_by_category)

        # Generate HTML
        html = format_html_email(papers_by_category, days_back)

        # Generate PDF
        pdf_path = generate_pdf(digest_id, papers_by_category, days_back)

        # Send email
        email_sent = False
        if send_emails and total_unique > 0:
            try:
                send_email(html, total_unique)
                email_sent = True
            except Exception as e:
                print(f"  Email failed: {e}")

        # Update digest record
        update_digest(
            digest_id,
            total_papers=total_unique,
            categories_with_results=categories_with_results,
            email_sent=email_sent,
            pdf_path=pdf_path,
            html_content=html,
            status="completed",
        )

        result["total_papers"] = total_unique
        result["status"] = "completed"
        result["email_sent"] = email_sent
        result["pdf_path"] = pdf_path

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        update_digest(digest_id, status="failed", error_message=error_msg)
        result["status"] = "failed"
        result["error"] = error_msg
        traceback.print_exc()

    return result
