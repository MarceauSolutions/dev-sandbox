#!/usr/bin/env python3
"""
Daily Dystonia Research Digest — automated email of new papers.

Searches PubMed and Semantic Scholar for papers published in the last 7 days
related to dystonia treatment, DBS, TMS, and pain management. Sends a
formatted HTML email to William every morning.

Usage:
    # Preview to console (no email sent)
    python execution/dystonia_research_digest.py --preview

    # Send email digest
    python execution/dystonia_research_digest.py

    # Custom lookback period
    python execution/dystonia_research_digest.py --days 14

Designed to run daily via n8n workflow or launchd on EC2/Mac.
"""

import argparse
import json
import os
import smtplib
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import requests

# Add project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── Config ──────────────────────────────────────────────────────────────────

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USERNAME", "wmarceau@marceausolutions.com")
SMTP_PASS = os.getenv("SMTP_PASSWORD", "")
TO_EMAIL = "wmarceau@marceausolutions.com"

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
S2_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

# ── Search Queries ──────────────────────────────────────────────────────────
# Each tuple: (search_query, category_label)
# These are designed to cast a wide net for anything relevant to William's condition

SEARCH_QUERIES = [
    # Core condition
    ("secondary dystonia treatment", "Dystonia Treatment"),
    ("dystonia pain management", "Dystonia Pain"),
    ("dystonia spasticity therapy", "Dystonia & Spasticity"),

    # Specific treatments he's used or considering
    ("deep brain stimulation dystonia", "Deep Brain Stimulation (DBS)"),
    ("transcranial magnetic stimulation dystonia", "Transcranial Magnetic Stimulation (TMS)"),
    ("clonazepam dystonia", "Clonazepam"),
    ("benzodiazepine movement disorder", "Benzodiazepines for Movement Disorders"),
    ("gabapentin dystonia spasticity", "Gabapentin"),
    ("low dose naltrexone neurological pain", "Low-Dose Naltrexone (LDN)"),
    ("botulinum toxin dystonia", "Botox"),
    ("trihexyphenidyl dystonia", "Trihexyphenidyl"),

    # Complementary approaches
    ("acupuncture dystonia", "Acupuncture"),
    ("cannabidiol dystonia spasticity", "CBD / Cannabis"),
    ("medical cannabis movement disorder", "Medical Cannabis"),
    ("mindfulness chronic neurological pain", "Mindfulness & Pain"),

    # Emerging / cutting edge
    ("dystonia gene therapy", "Gene Therapy"),
    ("dystonia novel treatment 2025", "Novel Treatments"),
    ("neuromodulation dystonia", "Neuromodulation"),
    ("DBS lead technology", "DBS Hardware / Technology"),
    ("sensorimotor retraining dystonia", "Sensorimotor Retraining"),

    # Pain-specific
    ("myofascial pain dystonia", "Myofascial Pain"),
    ("neuropathic pain movement disorder", "Neuropathic Pain"),
    ("central sensitization dystonia", "Central Pain Sensitization"),
]

# ── Rate Limiting ───────────────────────────────────────────────────────────
_last_request = {"pubmed": 0, "s2": 0}

def _rate_limit(source, delay=0.4):
    now = time.time()
    elapsed = now - _last_request.get(source, 0)
    if elapsed < delay:
        time.sleep(delay - elapsed)
    _last_request[source] = time.time()


def _get(url, source="pubmed"):
    _rate_limit(source)
    headers = {"User-Agent": "DystoniaResearchDigest/1.0 (wmarceau@marceausolutions.com)"}
    if source == "s2" and S2_API_KEY:
        headers["x-api-key"] = S2_API_KEY
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 429:
            time.sleep(5)
            return _get(url, source)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        return b""


# ── PubMed Search ───────────────────────────────────────────────────────────

def search_pubmed(query: str, days_back: int = 7, max_results: int = 10) -> list[dict]:
    """Search PubMed for recent papers."""
    from urllib.parse import urlencode
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": "date",
        "datetype": "edat",
        "reldate": days_back,
        "retmode": "json",
    }
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    url = f"{PUBMED_BASE}/esearch.fcgi?{urlencode(params)}"
    data = _get(url, "pubmed")
    if not data:
        return []

    result = json.loads(data)
    ids = result.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    # Fetch details for each paper
    papers = []
    from urllib.parse import urlencode
    detail_params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml",
    }
    if NCBI_API_KEY:
        detail_params["api_key"] = NCBI_API_KEY

    detail_url = f"{PUBMED_BASE}/efetch.fcgi?{urlencode(detail_params)}"
    xml_data = _get(detail_url, "pubmed")
    if not xml_data:
        return []

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError:
        return []

    for article in root.findall(".//PubmedArticle"):
        try:
            medline = article.find(".//MedlineCitation")
            art = medline.find(".//Article")

            title_el = art.find(".//ArticleTitle")
            title = "".join(title_el.itertext()).strip() if title_el is not None else "No title"

            # Abstract
            abstract_parts = []
            for abs_text in art.findall(".//Abstract/AbstractText"):
                label = abs_text.get("Label", "")
                text = "".join(abs_text.itertext()).strip()
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)

            # Authors
            authors = []
            for author in art.findall(".//AuthorList/Author"):
                last = author.findtext("LastName", "")
                fore = author.findtext("ForeName", "")
                if last:
                    authors.append(f"{last} {fore}".strip())

            # Journal
            journal = art.findtext(".//Journal/Title", "")
            journal_abbrev = art.findtext(".//Journal/ISOAbbreviation", journal)

            # Date
            pub_date = art.find(".//Journal/JournalIssue/PubDate")
            year = pub_date.findtext("Year", "") if pub_date is not None else ""
            month = pub_date.findtext("Month", "") if pub_date is not None else ""
            day = pub_date.findtext("Day", "") if pub_date is not None else ""
            date_str = f"{year} {month} {day}".strip()

            # PMID
            pmid = medline.findtext(".//PMID", "")

            # DOI
            doi = ""
            for id_el in article.findall(".//ArticleIdList/ArticleId"):
                if id_el.get("IdType") == "doi":
                    doi = id_el.text or ""
                    break

            papers.append({
                "title": title,
                "authors": authors,
                "abstract": abstract[:500] + ("..." if len(abstract) > 500 else ""),
                "journal": journal_abbrev or journal,
                "date": date_str,
                "pmid": pmid,
                "doi": doi,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                "source": "PubMed",
            })
        except Exception:
            continue

    return papers


# ── Semantic Scholar Search ─────────────────────────────────────────────────

def search_semantic_scholar(query: str, days_back: int = 7, max_results: int = 5) -> list[dict]:
    """Search Semantic Scholar for recent papers."""
    from urllib.parse import urlencode
    current_year = datetime.now().year
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,authors,abstract,year,externalIds,journal,citationCount,url,publicationDate",
        "year": f"{current_year - 1}-{current_year}",
        "sort": "publicationDate:desc",
    }
    url = f"{SEMANTIC_SCHOLAR_BASE}/paper/search?{urlencode(params)}"
    data = _get(url, "s2")
    if not data:
        return []

    result = json.loads(data)
    papers = []
    cutoff = datetime.now() - timedelta(days=days_back)

    for item in result.get("data", []):
        pub_date_str = item.get("publicationDate", "")
        # Don't filter too aggressively — S2 date indexing can lag
        if pub_date_str and days_back <= 14:
            try:
                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                if pub_date < cutoff:
                    continue
            except ValueError:
                pass

        authors = [a.get("name", "") for a in item.get("authors", [])[:5]]
        ext_ids = item.get("externalIds") or {}

        papers.append({
            "title": item.get("title", "No title"),
            "authors": authors,
            "abstract": (item.get("abstract") or "")[:500],
            "journal": (item.get("journal") or {}).get("name", ""),
            "date": pub_date_str or str(item.get("year", "")),
            "pmid": ext_ids.get("PubMed", ""),
            "doi": ext_ids.get("DOI", ""),
            "url": item.get("url", ""),
            "citations": item.get("citationCount", 0),
            "source": "Semantic Scholar",
        })

    return papers


# ── Deduplication ───────────────────────────────────────────────────────────

def deduplicate(papers: list[dict]) -> list[dict]:
    """Remove duplicate papers based on title similarity and DOI/PMID."""
    seen_ids = set()
    seen_titles = set()
    unique = []

    for p in papers:
        # Check DOI
        if p.get("doi") and p["doi"] in seen_ids:
            continue
        # Check PMID
        if p.get("pmid") and p["pmid"] in seen_ids:
            continue
        # Check title (normalized)
        norm_title = p["title"].lower().strip()[:80]
        if norm_title in seen_titles:
            continue

        if p.get("doi"):
            seen_ids.add(p["doi"])
        if p.get("pmid"):
            seen_ids.add(p["pmid"])
        seen_titles.add(norm_title)
        unique.append(p)

    return unique


# ── Email Formatting ────────────────────────────────────────────────────────

def format_html_email(papers_by_category: dict, days_back: int) -> str:
    """Generate branded HTML email."""
    date_str = datetime.now().strftime("%B %d, %Y")
    total = sum(len(v) for v in papers_by_category.values())

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                   color: #333; max-width: 700px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #1a2744 0%, #333 100%);
                      color: white; padding: 25px; border-radius: 8px; margin-bottom: 20px; }}
            .header h1 {{ color: #C9963C; margin: 0 0 5px 0; font-size: 22px; }}
            .header p {{ color: #ccc; margin: 2px 0; font-size: 13px; }}
            .category {{ background: #f8f6f0; border-left: 4px solid #C9963C;
                        padding: 8px 12px; margin: 20px 0 10px 0; font-weight: bold;
                        font-size: 15px; color: #1a2744; }}
            .paper {{ border: 1px solid #e5e5e5; border-radius: 6px; padding: 14px;
                     margin: 8px 0; background: white; }}
            .paper-title {{ font-weight: bold; color: #1a2744; font-size: 14px;
                           margin-bottom: 4px; }}
            .paper-title a {{ color: #1a2744; text-decoration: none; }}
            .paper-title a:hover {{ color: #C9963C; text-decoration: underline; }}
            .paper-meta {{ font-size: 12px; color: #666; margin: 3px 0; }}
            .paper-abstract {{ font-size: 12px; color: #555; margin-top: 6px;
                              line-height: 1.5; }}
            .badge {{ display: inline-block; padding: 2px 8px; border-radius: 3px;
                     font-size: 10px; font-weight: bold; margin-right: 5px; }}
            .badge-pubmed {{ background: #e8f5e9; color: #2e7d32; }}
            .badge-s2 {{ background: #e3f2fd; color: #1565c0; }}
            .badge-doi {{ background: #f3e5f5; color: #7b1fa2; }}
            .footer {{ margin-top: 30px; padding-top: 15px; border-top: 2px solid #C9963C;
                      font-size: 11px; color: #999; text-align: center; }}
            .no-results {{ color: #999; font-style: italic; padding: 10px; }}
            .summary-box {{ background: #1a2744; color: white; padding: 15px;
                           border-radius: 6px; margin: 15px 0; }}
            .summary-box span {{ color: #C9963C; font-weight: bold; font-size: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Dystonia Research Digest</h1>
            <p>{date_str} | Papers from the last {days_back} days</p>
            <p>Secondary Dystonia | DBS | TMS | Pain Management | Emerging Treatments</p>
        </div>

        <div class="summary-box">
            <span>{total}</span> new papers found across
            <span>{len([c for c, p in papers_by_category.items() if p])}</span> categories
        </div>
    """

    if total == 0:
        html += '<p class="no-results">No new papers found in the last '
        html += f'{days_back} days. This is normal — not every day produces '
        html += 'new dystonia research. The search will continue tomorrow.</p>'
    else:
        for category, papers in papers_by_category.items():
            if not papers:
                continue
            html += f'<div class="category">{category} ({len(papers)} papers)</div>'

            for p in papers:
                url = p.get("url", "")
                if not url and p.get("doi"):
                    url = f"https://doi.org/{p['doi']}"
                if not url and p.get("pmid"):
                    url = f"https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/"

                title_html = f'<a href="{url}">{p["title"]}</a>' if url else p["title"]

                badges = ""
                if p.get("source") == "PubMed":
                    badges += '<span class="badge badge-pubmed">PubMed</span>'
                else:
                    badges += '<span class="badge badge-s2">Semantic Scholar</span>'
                if p.get("doi"):
                    badges += f'<span class="badge badge-doi">DOI: {p["doi"]}</span>'

                authors_str = ", ".join(p.get("authors", [])[:4])
                if len(p.get("authors", [])) > 4:
                    authors_str += f" +{len(p['authors']) - 4} more"

                html += f"""
                <div class="paper">
                    <div class="paper-title">{title_html}</div>
                    <div class="paper-meta">{badges}</div>
                    <div class="paper-meta">{authors_str}</div>
                    <div class="paper-meta">
                        {p.get('journal', '')} | Published: {p.get('date', 'Unknown')}
                        {f' | PMID: {p["pmid"]}' if p.get('pmid') else ''}
                    </div>
                """
                if p.get("abstract"):
                    html += f'<div class="paper-abstract">{p["abstract"]}</div>'
                html += '</div>'

    html += f"""
        <div class="footer">
            <p>Dystonia Research Digest — Automated daily report</p>
            <p>Searches: PubMed (NIH) + Semantic Scholar | {len(SEARCH_QUERIES)} research queries</p>
            <p>Covering: secondary dystonia, DBS, TMS, clonazepam, gabapentin, LDN,
               acupuncture, CBD, gene therapy, neuromodulation, pain management</p>
            <p>Generated by Marceau Solutions AI Infrastructure</p>
        </div>
    </body>
    </html>
    """
    return html


# ── Send Email ──────────────────────────────────────────────────────────────

def send_email(html_body: str, total_papers: int):
    """Send the digest via SMTP."""
    date_str = datetime.now().strftime("%b %d")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Dystonia Research Digest — {date_str} — {total_papers} new papers"
    msg["From"] = f"Research Digest <{SMTP_USER}>"
    msg["To"] = TO_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

    print(f"  Email sent to {TO_EMAIL}")


# ── Main ────────────────────────────────────────────────────────────────────

def run_digest(days_back: int = 7, preview: bool = False):
    """Run the full research digest pipeline."""
    print("=" * 60)
    print("DYSTONIA RESEARCH DIGEST")
    print(f"Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"Looking back: {days_back} days")
    print("=" * 60)

    all_papers = []
    papers_by_category = {}

    for query, category in SEARCH_QUERIES:
        print(f"\n  Searching: {category} ({query})...")

        # PubMed
        pm_papers = search_pubmed(query, days_back=days_back, max_results=5)
        print(f"    PubMed: {len(pm_papers)} results")

        # Semantic Scholar
        s2_papers = search_semantic_scholar(query, days_back=days_back, max_results=5)
        print(f"    Semantic Scholar: {len(s2_papers)} results")

        category_papers = pm_papers + s2_papers
        if category_papers:
            all_papers.extend(category_papers)
            papers_by_category[category] = category_papers

    # Deduplicate within each category and globally
    print(f"\n  Total raw results: {len(all_papers)}")
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
    print(f"  After dedup: {total_unique} unique papers")

    # Generate email
    html = format_html_email(papers_by_category, days_back)

    if preview:
        # Save to file and open
        preview_path = ROOT / "docs" / "dystonia-research-digest-preview.html"
        with open(preview_path, "w") as f:
            f.write(html)
        print(f"\n  Preview saved: {preview_path}")
        os.system(f'open "{preview_path}"')
    else:
        # Send email
        print("\n  Sending email...")
        try:
            send_email(html, total_unique)
            print(f"\n  SUCCESS — {total_unique} papers emailed to {TO_EMAIL}")
        except Exception as e:
            print(f"\n  ERROR sending email: {e}")
            # Save as fallback
            fallback = ROOT / "docs" / "dystonia-research-digest-fallback.html"
            with open(fallback, "w") as f:
                f.write(html)
            print(f"  Saved fallback to: {fallback}")

    print("=" * 60)
    return total_unique


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Dystonia Research Digest")
    parser.add_argument("--preview", action="store_true", help="Preview in browser, don't send email")
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    args = parser.parse_args()

    run_digest(days_back=args.days, preview=args.preview)
