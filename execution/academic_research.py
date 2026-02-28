#!/usr/bin/env python3
"""
Academic Research Tool — Search Semantic Scholar, PubMed, and Unpaywall
for papers, abstracts, and open access PDFs.

Usage:
    # Search by keyword
    python execution/academic_research.py search "tesamorelin body composition"

    # Search with options
    python execution/academic_research.py search "GH secretagogue" --limit 5 --year 2020-2025 --pubmed

    # Look up a specific paper by DOI
    python execution/academic_research.py lookup "10.1038/nature12373"

    # Find open access PDF for a DOI
    python execution/academic_research.py pdf "10.1210/jc.2017-02049"

    # Full research mode — searches all sources, finds PDFs, downloads available ones
    python execution/academic_research.py deep "peptide therapy muscle growth" --download

Module usage:
    from execution.academic_research import search_papers, lookup_doi, find_open_access
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ── Config ──────────────────────────────────────────────────────────────────

SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"
PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UNPAYWALL_BASE = "https://api.unpaywall.org/v2"

# Optional: set SEMANTIC_SCHOLAR_API_KEY in .env for higher rate limits
S2_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
UNPAYWALL_EMAIL = os.getenv("UNPAYWALL_EMAIL", "wmarceau@marceausolutions.com")

# Rate limiting
LAST_REQUEST_TIME = {"s2": 0, "pubmed": 0, "unpaywall": 0}


# ── Data Models ─────────────────────────────────────────────────────────────

@dataclass
class Paper:
    title: str
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    abstract: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmc_id: Optional[str] = None
    citation_count: Optional[int] = None
    journal: Optional[str] = None
    is_open_access: bool = False
    pdf_url: Optional[str] = None
    landing_url: Optional[str] = None
    oa_status: Optional[str] = None  # gold, green, hybrid, bronze, closed
    source: str = ""  # semantic_scholar, pubmed, unpaywall

    def summary(self, index: int = 0, verbose: bool = False) -> str:
        lines = []
        prefix = f"[{index}] " if index else ""
        oa_badge = ""
        if self.is_open_access:
            status = self.oa_status.upper() if self.oa_status else "OA"
            oa_badge = f" [{status}]"
        lines.append(f"{prefix}{self.title} ({self.year or '?'}){oa_badge}")
        if self.authors:
            author_str = ", ".join(self.authors[:3])
            if len(self.authors) > 3:
                author_str += f" +{len(self.authors) - 3} more"
            lines.append(f"  Authors: {author_str}")
        if self.journal:
            lines.append(f"  Journal: {self.journal}")
        if self.citation_count is not None:
            lines.append(f"  Citations: {self.citation_count}")
        if self.doi:
            lines.append(f"  DOI: {self.doi}")
        if self.pmid:
            lines.append(f"  PMID: {self.pmid}")
        if self.pdf_url:
            lines.append(f"  PDF: {self.pdf_url}")
        elif self.landing_url:
            lines.append(f"  URL: {self.landing_url}")
        if verbose and self.abstract:
            # Wrap abstract to ~80 chars
            words = self.abstract.split()
            current_line = "  Abstract: "
            abstract_lines = []
            for word in words:
                if len(current_line) + len(word) + 1 > 80:
                    abstract_lines.append(current_line)
                    current_line = "    " + word
                else:
                    current_line += " " + word if current_line.strip() else word
            if current_line.strip():
                abstract_lines.append(current_line)
            lines.extend(abstract_lines)
        return "\n".join(lines)


# ── HTTP Helpers ────────────────────────────────────────────────────────────

def _rate_limit(source: str, delay: float = 0.35):
    """Simple rate limiter per source."""
    now = time.time()
    elapsed = now - LAST_REQUEST_TIME.get(source, 0)
    if elapsed < delay:
        time.sleep(delay - elapsed)
    LAST_REQUEST_TIME[source] = time.time()


def _get(url: str, headers: Optional[dict] = None, source: str = "s2") -> bytes:
    """HTTP GET with rate limiting and error handling."""
    _rate_limit(source)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "AcademicResearchTool/1.0 (wmarceau@marceausolutions.com)")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"  [Rate limited by {source}] Waiting 5s...", file=sys.stderr)
            time.sleep(5)
            return _get(url, headers, source)
        raise
    except urllib.error.URLError as e:
        print(f"  [Network error: {e.reason}]", file=sys.stderr)
        return b""


def _get_json(url: str, headers: Optional[dict] = None, source: str = "s2") -> dict:
    data = _get(url, headers, source)
    if not data:
        return {}
    return json.loads(data)


# ── Semantic Scholar ────────────────────────────────────────────────────────

def search_semantic_scholar(
    query: str,
    limit: int = 10,
    year: Optional[str] = None,
    fields_of_study: Optional[str] = None,
    open_access_only: bool = False,
    min_citations: Optional[int] = None,
) -> list[Paper]:
    """Search Semantic Scholar for papers matching a query."""
    fields = "title,abstract,year,authors,openAccessPdf,citationCount,isOpenAccess,venue,externalIds"
    params = {
        "query": query,
        "fields": fields,
        "limit": min(limit, 100),
    }
    if year:
        params["year"] = year
    if fields_of_study:
        params["fieldsOfStudy"] = fields_of_study
    if open_access_only:
        params["openAccessPdf"] = ""
    if min_citations:
        params["minCitationCount"] = str(min_citations)

    url = f"{SEMANTIC_SCHOLAR_BASE}/paper/search?{urllib.parse.urlencode(params)}"
    headers = {}
    if S2_API_KEY:
        headers["x-api-key"] = S2_API_KEY

    data = _get_json(url, headers, "s2")
    if not data or "data" not in data:
        return []

    papers = []
    for item in data["data"]:
        ext_ids = item.get("externalIds") or {}
        oa_pdf = item.get("openAccessPdf") or {}
        authors = [a.get("name", "") for a in (item.get("authors") or [])]

        paper = Paper(
            title=item.get("title", "Untitled"),
            authors=authors,
            year=item.get("year"),
            abstract=item.get("abstract"),
            doi=ext_ids.get("DOI"),
            pmid=ext_ids.get("PubMed"),
            pmc_id=ext_ids.get("PubMedCentral"),
            citation_count=item.get("citationCount"),
            journal=item.get("venue"),
            is_open_access=item.get("isOpenAccess", False),
            pdf_url=oa_pdf.get("url"),
            oa_status=oa_pdf.get("status", "").lower() if oa_pdf.get("status") else None,
            source="semantic_scholar",
        )
        papers.append(paper)

    return papers


# ── PubMed ──────────────────────────────────────────────────────────────────

def search_pubmed(
    query: str,
    limit: int = 10,
    sort: str = "relevance",
    min_date: Optional[str] = None,
    max_date: Optional[str] = None,
) -> list[Paper]:
    """Search PubMed for papers and return with full abstracts."""
    # Step 1: ESearch to get PMIDs
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(min(limit, 100)),
        "sort": sort,
        "retmode": "json",
        "tool": "academic_research_tool",
        "email": UNPAYWALL_EMAIL,
    }
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    if min_date:
        params["datetype"] = "pdat"
        params["mindate"] = min_date
    if max_date:
        params["maxdate"] = max_date

    url = f"{PUBMED_BASE}/esearch.fcgi?{urllib.parse.urlencode(params)}"
    data = _get_json(url, source="pubmed")

    result = data.get("esearchresult", {})
    pmids = result.get("idlist", [])
    if not pmids:
        return []

    # Step 2: EFetch to get abstracts (XML)
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
        "tool": "academic_research_tool",
        "email": UNPAYWALL_EMAIL,
    }
    if NCBI_API_KEY:
        fetch_params["api_key"] = NCBI_API_KEY

    fetch_url = f"{PUBMED_BASE}/efetch.fcgi?{urllib.parse.urlencode(fetch_params)}"
    xml_data = _get(fetch_url, source="pubmed")
    if not xml_data:
        return []

    papers = _parse_pubmed_xml(xml_data)
    return papers


def _parse_pubmed_xml(xml_data: bytes) -> list[Paper]:
    """Parse PubMed EFetch XML into Paper objects."""
    papers = []
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError:
        return []

    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID", "")
        title = article.findtext(".//ArticleTitle", "Untitled")

        # Abstract may have multiple sections
        abstract_parts = []
        for text_el in article.findall(".//AbstractText"):
            label = text_el.get("Label", "")
            text = text_el.text or ""
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = " ".join(abstract_parts) if abstract_parts else None

        # Authors
        authors = []
        for author in article.findall(".//Author"):
            last = author.findtext("LastName", "")
            first = author.findtext("ForeName", "")
            if last:
                authors.append(f"{first} {last}".strip())

        # Year
        year_text = article.findtext(".//PubDate/Year")
        year = int(year_text) if year_text and year_text.isdigit() else None

        # Journal
        journal = article.findtext(".//Journal/Title", "")

        # External IDs
        doi = None
        pmc_id = None
        for aid in article.findall(".//ArticleId"):
            if aid.get("IdType") == "doi":
                doi = aid.text
            elif aid.get("IdType") == "pmc":
                pmc_id = aid.text

        # PMC = free full text available
        pdf_url = None
        if pmc_id:
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"

        paper = Paper(
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            doi=doi,
            pmid=pmid,
            pmc_id=pmc_id,
            journal=journal,
            is_open_access=bool(pmc_id),
            pdf_url=pdf_url,
            source="pubmed",
        )
        papers.append(paper)

    return papers


# ── Unpaywall ───────────────────────────────────────────────────────────────

def find_open_access(doi: str) -> Optional[dict]:
    """Look up a DOI on Unpaywall to find free/legal PDF links."""
    encoded_doi = urllib.parse.quote(doi, safe="")
    url = f"{UNPAYWALL_BASE}/{encoded_doi}?email={UNPAYWALL_EMAIL}"
    data = _get_json(url, source="unpaywall")
    if not data:
        return None

    best = data.get("best_oa_location") or {}
    return {
        "is_oa": data.get("is_oa", False),
        "oa_status": data.get("oa_status", "closed"),
        "title": data.get("title"),
        "journal": data.get("journal_name"),
        "year": data.get("year"),
        "pdf_url": best.get("url_for_pdf"),
        "landing_url": best.get("url_for_landing_page"),
        "host_type": best.get("host_type"),
        "version": best.get("version"),
        "license": best.get("license"),
        "all_locations": [
            {
                "url": loc.get("url_for_pdf") or loc.get("url"),
                "host": loc.get("host_type"),
                "version": loc.get("version"),
                "license": loc.get("license"),
            }
            for loc in data.get("oa_locations", [])
        ],
    }


def enrich_with_unpaywall(papers: list[Paper]) -> list[Paper]:
    """For papers without a PDF URL, try Unpaywall to find one."""
    for paper in papers:
        if paper.pdf_url or not paper.doi:
            continue
        result = find_open_access(paper.doi)
        if result and result.get("is_oa"):
            paper.is_open_access = True
            paper.oa_status = result.get("oa_status")
            paper.pdf_url = result.get("pdf_url")
            paper.landing_url = result.get("landing_url")
    return papers


# ── Combined Search ─────────────────────────────────────────────────────────

def search_papers(
    query: str,
    limit: int = 10,
    year: Optional[str] = None,
    include_pubmed: bool = False,
    open_access_only: bool = False,
    enrich_oa: bool = True,
    min_citations: Optional[int] = None,
) -> list[Paper]:
    """
    Search for academic papers across multiple sources.

    Args:
        query: Search terms
        limit: Max results per source
        year: Year or range (e.g. "2020" or "2020-2025")
        include_pubmed: Also search PubMed (slower, but better for biomedical)
        open_access_only: Only return open access papers
        enrich_oa: Use Unpaywall to find PDFs for papers without one
        min_citations: Minimum citation count filter

    Returns:
        List of Paper objects, deduplicated by DOI
    """
    all_papers = []

    # Semantic Scholar (primary)
    print(f"Searching Semantic Scholar for: {query}", file=sys.stderr)
    s2_papers = search_semantic_scholar(
        query, limit=limit, year=year,
        open_access_only=open_access_only,
        min_citations=min_citations,
    )
    all_papers.extend(s2_papers)
    print(f"  Found {len(s2_papers)} papers on Semantic Scholar", file=sys.stderr)

    # PubMed (optional, good for biomedical)
    if include_pubmed:
        print(f"Searching PubMed for: {query}", file=sys.stderr)
        min_date = None
        if year and "-" in year:
            min_date = year.split("-")[0]
        elif year:
            min_date = year
        pm_papers = search_pubmed(query, limit=limit, min_date=min_date)
        all_papers.extend(pm_papers)
        print(f"  Found {len(pm_papers)} papers on PubMed", file=sys.stderr)

    # Deduplicate by DOI
    seen_dois = set()
    unique_papers = []
    for paper in all_papers:
        if paper.doi:
            if paper.doi in seen_dois:
                continue
            seen_dois.add(paper.doi)
        unique_papers.append(paper)

    # Enrich with Unpaywall
    if enrich_oa and not open_access_only:
        papers_needing_oa = [p for p in unique_papers if not p.pdf_url and p.doi]
        if papers_needing_oa:
            print(f"  Checking Unpaywall for {len(papers_needing_oa)} papers...", file=sys.stderr)
            enrich_with_unpaywall(unique_papers)

    # Sort by citation count (highest first), then year
    unique_papers.sort(
        key=lambda p: (p.citation_count or 0, p.year or 0),
        reverse=True,
    )

    return unique_papers


def lookup_doi(doi: str) -> Optional[Paper]:
    """Look up a specific paper by DOI using Semantic Scholar + Unpaywall."""
    url = f"{SEMANTIC_SCHOLAR_BASE}/paper/DOI:{urllib.parse.quote(doi, safe='')}?fields=title,abstract,year,authors,openAccessPdf,citationCount,isOpenAccess,venue,externalIds"
    headers = {}
    if S2_API_KEY:
        headers["x-api-key"] = S2_API_KEY

    data = _get_json(url, headers, "s2")
    if not data or "title" not in data:
        # Try Unpaywall as fallback
        oa = find_open_access(doi)
        if oa and oa.get("title"):
            return Paper(
                title=oa["title"],
                year=oa.get("year"),
                journal=oa.get("journal"),
                doi=doi,
                is_open_access=oa.get("is_oa", False),
                pdf_url=oa.get("pdf_url"),
                landing_url=oa.get("landing_url"),
                oa_status=oa.get("oa_status"),
                source="unpaywall",
            )
        return None

    ext_ids = data.get("externalIds") or {}
    oa_pdf = data.get("openAccessPdf") or {}
    authors = [a.get("name", "") for a in (data.get("authors") or [])]

    paper = Paper(
        title=data.get("title", "Untitled"),
        authors=authors,
        year=data.get("year"),
        abstract=data.get("abstract"),
        doi=doi,
        pmid=ext_ids.get("PubMed"),
        pmc_id=ext_ids.get("PubMedCentral"),
        citation_count=data.get("citationCount"),
        journal=data.get("venue"),
        is_open_access=data.get("isOpenAccess", False),
        pdf_url=oa_pdf.get("url"),
        oa_status=oa_pdf.get("status", "").lower() if oa_pdf.get("status") else None,
        source="semantic_scholar",
    )

    # Enrich with Unpaywall if no PDF found
    if not paper.pdf_url:
        oa = find_open_access(doi)
        if oa and oa.get("is_oa"):
            paper.is_open_access = True
            paper.pdf_url = oa.get("pdf_url")
            paper.landing_url = oa.get("landing_url")
            paper.oa_status = oa.get("oa_status")

    return paper


def download_pdf(url: str, output_path: str) -> bool:
    """Download a PDF from a URL."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "AcademicResearchTool/1.0 (wmarceau@marceausolutions.com)")
        with urllib.request.urlopen(req, timeout=60) as resp:
            content = resp.read()
            with open(output_path, "wb") as f:
                f.write(content)
        return True
    except Exception as e:
        print(f"  Failed to download: {e}", file=sys.stderr)
        return False


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Academic Research Tool — Search papers across Semantic Scholar, PubMed, and Unpaywall",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search "tesamorelin body composition"
  %(prog)s search "GH secretagogue" --limit 5 --year 2020-2025 --pubmed
  %(prog)s search "peptide therapy" --pubmed --verbose
  %(prog)s lookup "10.1210/jc.2017-02049"
  %(prog)s pdf "10.1210/jc.2017-02049"
  %(prog)s deep "peptide therapy muscle growth" --download
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # search
    sp_search = subparsers.add_parser("search", help="Search for papers by keyword")
    sp_search.add_argument("query", help="Search query")
    sp_search.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    sp_search.add_argument("--year", help="Year or range (e.g. 2020 or 2020-2025)")
    sp_search.add_argument("--pubmed", action="store_true", help="Also search PubMed")
    sp_search.add_argument("--oa-only", action="store_true", help="Only open access papers")
    sp_search.add_argument("--min-citations", type=int, help="Minimum citation count")
    sp_search.add_argument("--verbose", "-v", action="store_true", help="Show abstracts")
    sp_search.add_argument("--json", action="store_true", help="Output JSON")

    # lookup
    sp_lookup = subparsers.add_parser("lookup", help="Look up a paper by DOI")
    sp_lookup.add_argument("doi", help="DOI to look up")
    sp_lookup.add_argument("--verbose", "-v", action="store_true", help="Show abstract")
    sp_lookup.add_argument("--json", action="store_true", help="Output JSON")

    # pdf
    sp_pdf = subparsers.add_parser("pdf", help="Find open access PDF for a DOI")
    sp_pdf.add_argument("doi", help="DOI to find PDF for")
    sp_pdf.add_argument("--download", "-d", help="Download PDF to this path")

    # deep
    sp_deep = subparsers.add_parser("deep", help="Deep research — all sources + PDF discovery")
    sp_deep.add_argument("query", help="Research topic")
    sp_deep.add_argument("--limit", type=int, default=15, help="Max results per source (default: 15)")
    sp_deep.add_argument("--year", help="Year or range")
    sp_deep.add_argument("--download", action="store_true", help="Download available PDFs")
    sp_deep.add_argument("--output", "-o", default=".", help="Download directory")
    sp_deep.add_argument("--verbose", "-v", action="store_true", help="Show abstracts")
    sp_deep.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "search":
        papers = search_papers(
            args.query,
            limit=args.limit,
            year=args.year,
            include_pubmed=args.pubmed,
            open_access_only=args.oa_only,
            min_citations=args.min_citations,
        )
        if args.json:
            print(json.dumps([asdict(p) for p in papers], indent=2))
        else:
            print(f"\n{'=' * 70}")
            print(f"Found {len(papers)} papers for: {args.query}")
            print(f"{'=' * 70}\n")
            for i, paper in enumerate(papers, 1):
                print(paper.summary(i, verbose=args.verbose))
                print()

    elif args.command == "lookup":
        paper = lookup_doi(args.doi)
        if not paper:
            print(f"No paper found for DOI: {args.doi}", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(json.dumps(asdict(paper), indent=2))
        else:
            print(paper.summary(verbose=args.verbose))

    elif args.command == "pdf":
        result = find_open_access(args.doi)
        if not result:
            print(f"No Unpaywall data for DOI: {args.doi}", file=sys.stderr)
            sys.exit(1)
        if result["is_oa"]:
            print(f"Open Access: YES ({result['oa_status']})")
            if result["pdf_url"]:
                print(f"PDF URL: {result['pdf_url']}")
                if args.download:
                    if download_pdf(result["pdf_url"], args.download):
                        print(f"Downloaded to: {args.download}")
            elif result["landing_url"]:
                print(f"Landing page: {result['landing_url']}")
            if result.get("all_locations"):
                print(f"\nAll {len(result['all_locations'])} locations:")
                for loc in result["all_locations"]:
                    print(f"  - {loc['url']} [{loc['host']}] ({loc['version']})")
        else:
            print(f"Not open access (status: {result['oa_status']})")
            print(f"This paper requires institutional access (e.g., CMU VPN)")

    elif args.command == "deep":
        papers = search_papers(
            args.query,
            limit=args.limit,
            year=args.year,
            include_pubmed=True,
            enrich_oa=True,
        )

        oa_count = sum(1 for p in papers if p.pdf_url)
        print(f"\n{'=' * 70}")
        print(f"Deep Research: {args.query}")
        print(f"Found {len(papers)} unique papers ({oa_count} with open access PDFs)")
        print(f"{'=' * 70}\n")

        for i, paper in enumerate(papers, 1):
            print(paper.summary(i, verbose=args.verbose))
            print()

        if args.download and oa_count > 0:
            dl_dir = Path(args.output)
            dl_dir.mkdir(parents=True, exist_ok=True)
            print(f"\nDownloading {oa_count} PDFs to {dl_dir}...")
            downloaded = 0
            for paper in papers:
                if not paper.pdf_url:
                    continue
                # Sanitize filename
                safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in paper.title)
                safe_title = safe_title[:80].strip()
                filename = f"{paper.year or 'unknown'}_{safe_title}.pdf"
                filepath = dl_dir / filename
                print(f"  Downloading: {filename}...")
                if download_pdf(paper.pdf_url, str(filepath)):
                    downloaded += 1
            print(f"\nDownloaded {downloaded}/{oa_count} PDFs")

        if args.json:
            print(json.dumps([asdict(p) for p in papers], indent=2))


if __name__ == "__main__":
    main()
