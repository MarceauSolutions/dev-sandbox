"""
Insurance Promo Scanner
=======================

Async scraper module that fetches current promotions, discounts, and deals
from major insurance carriers and aggregator sites. Designed for the
AutoInsure Saver app to surface real-time savings opportunities.

Carriers scraped:
    GEICO, Progressive, State Farm, Allstate, USAA, Liberty Mutual,
    Farmers, Nationwide, Travelers, American Family

Aggregators scraped:
    NerdWallet, The Zebra, ValuePenguin

Features:
    - Concurrent async scraping with httpx
    - Retry logic with exponential backoff (3 attempts)
    - Per-domain rate limiting (1s between requests)
    - Content-hash deduplication (SHA-256)
    - Graceful error handling with structured logging
    - Database persistence via SQLAlchemy async sessions
"""

import asyncio
import hashlib
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
import httpx
from sqlalchemy import select, update

from src.models.base import async_session
from src.models.deals import InsuranceDeal

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("promo_scanner")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(_handler)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 30.0          # seconds
MAX_RETRIES = 3
BACKOFF_BASE = 2.0              # exponential backoff base (seconds)
RATE_LIMIT_SECONDS = 1.0        # minimum gap between requests to same domain

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DealData:
    """Structured representation of a single insurance deal/promotion."""

    title: str
    carrier: str
    description: str = ""
    estimated_savings: Optional[str] = None
    deal_type: str = "discount"          # discount | bundle | new_customer | referral | loyalty | other
    source_url: str = ""
    requirements: str = ""
    expiry_date: Optional[date] = None
    scraped_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def content_hash(self) -> str:
        """SHA-256 hash of title + carrier + description for dedup."""
        raw = f"{self.title.strip().lower()}|{self.carrier.strip().lower()}|{self.description.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Carrier definitions
# ---------------------------------------------------------------------------

CARRIERS: dict[str, dict] = {
    "GEICO": {
        "base_url": "https://www.geico.com",
        "pages": [
            "/save/discounts",
            "/save",
            "/information/aboutinsurance/discount-insurance",
        ],
    },
    "Progressive": {
        "base_url": "https://www.progressive.com",
        "pages": [
            "/auto/discounts/",
            "/auto/save-on-car-insurance/",
            "/auto/",
        ],
    },
    "State Farm": {
        "base_url": "https://www.statefarm.com",
        "pages": [
            "/insurance/auto/discounts/",
            "/simple-insights/insurance/auto/car-insurance-discounts",
            "/insurance/auto/",
        ],
    },
    "Allstate": {
        "base_url": "https://www.allstate.com",
        "pages": [
            "/auto-insurance/car-insurance-discounts",
            "/auto-insurance/save/",
            "/auto-insurance/",
        ],
    },
    "USAA": {
        "base_url": "https://www.usaa.com",
        "pages": [
            "/inet/wc/insurance-auto-discounts",
            "/insurance/auto/discounts/",
            "/insurance/auto/",
        ],
    },
    "Liberty Mutual": {
        "base_url": "https://www.libertymutual.com",
        "pages": [
            "/auto/car-insurance-discounts/",
            "/auto/save-on-car-insurance/",
            "/auto/",
        ],
    },
    "Farmers": {
        "base_url": "https://www.farmers.com",
        "pages": [
            "/auto/discounts/",
            "/auto/savings/",
            "/auto/",
        ],
    },
    "Nationwide": {
        "base_url": "https://www.nationwide.com",
        "pages": [
            "/personal/insurance/auto/discounts/",
            "/personal/insurance/auto/savings/",
            "/personal/insurance/auto/",
        ],
    },
    "Travelers": {
        "base_url": "https://www.travelers.com",
        "pages": [
            "/car-insurance/discounts",
            "/car-insurance/savings",
            "/car-insurance",
        ],
    },
    "American Family": {
        "base_url": "https://www.amfam.com",
        "pages": [
            "/insurance/auto/discounts/",
            "/insurance/auto/savings/",
            "/insurance/auto/",
        ],
    },
}

AGGREGATORS: dict[str, dict] = {
    "NerdWallet": {
        "base_url": "https://www.nerdwallet.com",
        "pages": [
            "/article/insurance/car-insurance-discounts",
            "/blog/insurance/cheapest-car-insurance/",
            "/insurance/car/",
        ],
    },
    "The Zebra": {
        "base_url": "https://www.thezebra.com",
        "pages": [
            "/auto-insurance/discounts/",
            "/auto-insurance/cheap-car-insurance/",
            "/auto-insurance/",
        ],
    },
    "ValuePenguin": {
        "base_url": "https://www.valuepenguin.com",
        "pages": [
            "/car-insurance/discounts",
            "/cheapest-car-insurance",
            "/car-insurance",
        ],
    },
}

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

class DomainRateLimiter:
    """Ensures a minimum delay between consecutive requests to the same domain."""

    def __init__(self, min_interval: float = RATE_LIMIT_SECONDS):
        self._min_interval = min_interval
        self._last_request: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def wait(self, domain: str) -> None:
        async with self._lock:
            now = time.monotonic()
            last = self._last_request.get(domain, 0.0)
            wait_time = self._min_interval - (now - last)
            if wait_time > 0:
                logger.debug("Rate-limit: sleeping %.2fs for %s", wait_time, domain)
                await asyncio.sleep(wait_time)
            self._last_request[domain] = time.monotonic()


_rate_limiter = DomainRateLimiter()

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get_domain(url: str) -> str:
    """Extract the domain (netloc) from a URL for rate-limiting."""
    from urllib.parse import urlparse
    return urlparse(url).netloc


async def fetch_page(
    client: httpx.AsyncClient,
    url: str,
    *,
    retries: int = MAX_RETRIES,
) -> Optional[str]:
    """
    Fetch a single page with retry + exponential backoff.

    Returns the decoded HTML text, or ``None`` on permanent failure.
    """
    domain = _get_domain(url)

    for attempt in range(1, retries + 1):
        try:
            await _rate_limiter.wait(domain)
            logger.info("Fetching %s (attempt %d/%d)", url, attempt, retries)
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            return resp.text

        except httpx.TimeoutException:
            logger.warning("Timeout fetching %s (attempt %d)", url, attempt)
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            # Don't retry on client errors (except 429)
            if 400 <= code < 500 and code != 429:
                logger.warning("HTTP %d for %s – skipping", code, url)
                return None
            logger.warning("HTTP %d for %s (attempt %d)", code, url, attempt)
        except httpx.RequestError as exc:
            logger.warning("Request error for %s: %s (attempt %d)", url, exc, attempt)

        if attempt < retries:
            backoff = BACKOFF_BASE ** attempt
            logger.debug("Backing off %.1fs before retry", backoff)
            await asyncio.sleep(backoff)

    logger.error("All %d attempts failed for %s", retries, url)
    return None

# ---------------------------------------------------------------------------
# Generic HTML extraction helpers
# ---------------------------------------------------------------------------

_SAVINGS_PATTERN = re.compile(
    r"(?:save|up\s+to|savings?\s+of)\s*\$?\s*(\d[\d,]*(?:\.\d{2})?)\s*%?",
    re.IGNORECASE,
)

_PERCENTAGE_PATTERN = re.compile(
    r"(\d{1,3})\s*%\s*(?:off|discount|savings?|less|reduction)",
    re.IGNORECASE,
)


def _extract_savings(text: str) -> Optional[str]:
    """Try to pull a savings figure or percentage out of text."""
    m = _SAVINGS_PATTERN.search(text)
    if m:
        return m.group(0).strip()
    m = _PERCENTAGE_PATTERN.search(text)
    if m:
        return m.group(0).strip()
    return None


def _classify_deal(text: str) -> str:
    """Classify a deal type from its text content."""
    lower = text.lower()
    if any(w in lower for w in ("bundle", "multi-policy", "multi policy", "combined")):
        return "bundle"
    if any(w in lower for w in ("new customer", "new driver", "switch", "new policyholder")):
        return "new_customer"
    if any(w in lower for w in ("refer", "referral")):
        return "referral"
    if any(w in lower for w in ("loyal", "renewal", "long-term", "tenure")):
        return "loyalty"
    if any(w in lower for w in ("discount", "save", "saving", "% off", "reduce")):
        return "discount"
    return "other"


def _clean_text(text: str) -> str:
    """Collapse whitespace and strip surrounding junk from extracted text."""
    return re.sub(r"\s+", " ", text).strip()


def _extract_deals_from_sections(
    soup: BeautifulSoup,
    carrier: str,
    page_url: str,
) -> list[DealData]:
    """
    Generic extraction: look for headings + adjacent descriptions that
    mention discounts, savings, or offers.  Works across most carrier sites.
    """
    deals: list[DealData] = []

    # Strategy 1: cards / list items with headings inside
    card_selectors = [
        "div.card", "div.discount-card", "li.discount",
        "div.offer", "article", "div.promo",
        "div[class*='discount']", "div[class*='offer']",
        "div[class*='savings']", "div[class*='deal']",
        "section[class*='discount']", "section[class*='offer']",
    ]
    seen_titles: set[str] = set()

    for selector in card_selectors:
        for card in soup.select(selector):
            heading = card.find(re.compile(r"^h[1-6]$"))
            if not heading:
                # fallback: first strong/b tag
                heading = card.find(["strong", "b"])
            if not heading:
                continue

            title = _clean_text(heading.get_text())
            if not title or len(title) < 5 or title.lower() in seen_titles:
                continue
            seen_titles.add(title.lower())

            body = _clean_text(card.get_text())
            desc = body.replace(title, "", 1).strip()[:500]

            deals.append(DealData(
                title=title,
                carrier=carrier,
                description=desc,
                estimated_savings=_extract_savings(body),
                deal_type=_classify_deal(body),
                source_url=page_url,
                requirements=_extract_requirements(body),
            ))

    # Strategy 2: headings followed by <p> siblings (common on info pages)
    for heading in soup.find_all(re.compile(r"^h[2-4]$")):
        title = _clean_text(heading.get_text())
        if not title or len(title) < 5 or title.lower() in seen_titles:
            continue

        # Collect text from following siblings until next heading
        parts: list[str] = []
        sibling = heading.find_next_sibling()
        while sibling and not (isinstance(sibling, Tag) and sibling.name and re.match(r"^h[1-4]$", sibling.name)):
            parts.append(_clean_text(sibling.get_text()))
            sibling = sibling.find_next_sibling()
            if len(parts) > 5:
                break

        body = " ".join(parts)[:600]
        combined = f"{title} {body}"

        # Only keep if it looks like a deal / discount
        if not any(kw in combined.lower() for kw in (
            "discount", "save", "saving", "% off", "offer",
            "bundle", "reduce", "credit", "reward", "free",
        )):
            continue

        seen_titles.add(title.lower())
        deals.append(DealData(
            title=title,
            carrier=carrier,
            description=body[:500],
            estimated_savings=_extract_savings(combined),
            deal_type=_classify_deal(combined),
            source_url=page_url,
            requirements=_extract_requirements(combined),
        ))

    # Strategy 3: <li> items that contain discount keywords
    for li in soup.find_all("li"):
        text = _clean_text(li.get_text())
        if len(text) < 20 or len(text) > 300:
            continue
        if not any(kw in text.lower() for kw in ("discount", "save", "% off", "savings")):
            continue
        # Use first sentence as title
        title = text.split(".")[0].strip()[:120]
        if not title or title.lower() in seen_titles:
            continue
        seen_titles.add(title.lower())
        deals.append(DealData(
            title=title,
            carrier=carrier,
            description=text[:500],
            estimated_savings=_extract_savings(text),
            deal_type=_classify_deal(text),
            source_url=page_url,
            requirements=_extract_requirements(text),
        ))

    return deals


def _extract_requirements(text: str) -> str:
    """Try to extract eligibility / requirement info from text."""
    patterns = [
        r"(?:must|need to|require[sd]?|eligible if|qualify if|available (?:to|for))[^.]{5,120}",
        r"(?:enrollment|sign[- ]?up|enroll)[^.]{5,80}",
    ]
    reqs: list[str] = []
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            reqs.append(_clean_text(m.group(0)))
    return "; ".join(reqs)[:300]

# ---------------------------------------------------------------------------
# Per-carrier scraper functions
# ---------------------------------------------------------------------------

async def _scrape_carrier(
    client: httpx.AsyncClient,
    carrier: str,
    config: dict,
) -> list[DealData]:
    """
    Scrape all configured pages for a single carrier and return deals found.
    """
    all_deals: list[DealData] = []
    base = config["base_url"]

    for path in config["pages"]:
        url = urljoin(base, path)
        html = await fetch_page(client, url)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        deals = _extract_deals_from_sections(soup, carrier, url)
        logger.info("  [%s] %s → %d deals", carrier, path, len(deals))
        all_deals.extend(deals)

    logger.info("[%s] Total raw deals: %d", carrier, len(all_deals))
    return all_deals


async def scrape_geico(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape GEICO promotions and discounts."""
    return await _scrape_carrier(client, "GEICO", CARRIERS["GEICO"])


async def scrape_progressive(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape Progressive promotions and discounts."""
    return await _scrape_carrier(client, "Progressive", CARRIERS["Progressive"])


async def scrape_state_farm(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape State Farm promotions and discounts."""
    return await _scrape_carrier(client, "State Farm", CARRIERS["State Farm"])


async def scrape_allstate(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape Allstate promotions and discounts."""
    return await _scrape_carrier(client, "Allstate", CARRIERS["Allstate"])


async def scrape_usaa(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape USAA promotions and discounts."""
    return await _scrape_carrier(client, "USAA", CARRIERS["USAA"])


async def scrape_liberty_mutual(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape Liberty Mutual promotions and discounts."""
    return await _scrape_carrier(client, "Liberty Mutual", CARRIERS["Liberty Mutual"])


async def scrape_farmers(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape Farmers promotions and discounts."""
    return await _scrape_carrier(client, "Farmers", CARRIERS["Farmers"])


async def scrape_nationwide(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape Nationwide promotions and discounts."""
    return await _scrape_carrier(client, "Nationwide", CARRIERS["Nationwide"])


async def scrape_travelers(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape Travelers promotions and discounts."""
    return await _scrape_carrier(client, "Travelers", CARRIERS["Travelers"])


async def scrape_american_family(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape American Family promotions and discounts."""
    return await _scrape_carrier(client, "American Family", CARRIERS["American Family"])


# Mapping from carrier name → dedicated scraper function
CARRIER_SCRAPERS = {
    "GEICO": scrape_geico,
    "Progressive": scrape_progressive,
    "State Farm": scrape_state_farm,
    "Allstate": scrape_allstate,
    "USAA": scrape_usaa,
    "Liberty Mutual": scrape_liberty_mutual,
    "Farmers": scrape_farmers,
    "Nationwide": scrape_nationwide,
    "Travelers": scrape_travelers,
    "American Family": scrape_american_family,
}

# ---------------------------------------------------------------------------
# Aggregator scrapers
# ---------------------------------------------------------------------------

async def _scrape_aggregator(
    client: httpx.AsyncClient,
    name: str,
    config: dict,
) -> list[DealData]:
    """
    Scrape an aggregator site.  Aggregator deals get the aggregator name
    as carrier, since they cover multiple insurers.
    """
    all_deals: list[DealData] = []
    base = config["base_url"]

    for path in config["pages"]:
        url = urljoin(base, path)
        html = await fetch_page(client, url)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")

        # Aggregators often use tables, comparison cards, or ranked lists
        deals = _extract_deals_from_sections(soup, f"(via {name})", url)

        # Also look for comparison tables
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            headers = [_clean_text(th.get_text()) for th in rows[0].find_all(["th", "td"])] if rows else []
            for row in rows[1:]:
                cells = [_clean_text(td.get_text()) for td in row.find_all(["td", "th"])]
                if len(cells) < 2:
                    continue
                title = cells[0][:120]
                desc = " | ".join(f"{h}: {c}" for h, c in zip(headers, cells) if c)[:500]
                if not any(kw in desc.lower() for kw in ("discount", "save", "%", "rate", "cheap", "low")):
                    continue
                deals.append(DealData(
                    title=title,
                    carrier=f"(via {name})",
                    description=desc,
                    estimated_savings=_extract_savings(desc),
                    deal_type=_classify_deal(desc),
                    source_url=url,
                ))

        logger.info("  [%s] %s → %d deals", name, path, len(deals))
        all_deals.extend(deals)

    logger.info("[%s] Total raw deals: %d", name, len(all_deals))
    return all_deals


async def scrape_nerdwallet(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape NerdWallet insurance deals/articles."""
    return await _scrape_aggregator(client, "NerdWallet", AGGREGATORS["NerdWallet"])


async def scrape_the_zebra(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape The Zebra insurance promotions."""
    return await _scrape_aggregator(client, "The Zebra", AGGREGATORS["The Zebra"])


async def scrape_valuepenguin(client: httpx.AsyncClient) -> list[DealData]:
    """Scrape ValuePenguin insurance deals."""
    return await _scrape_aggregator(client, "ValuePenguin", AGGREGATORS["ValuePenguin"])


AGGREGATOR_SCRAPERS = {
    "NerdWallet": scrape_nerdwallet,
    "The Zebra": scrape_the_zebra,
    "ValuePenguin": scrape_valuepenguin,
}

# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def deduplicate_deals(deals: list[DealData]) -> list[DealData]:
    """Remove duplicate deals based on content hash."""
    seen: dict[str, DealData] = {}
    for deal in deals:
        h = deal.content_hash
        if h not in seen:
            seen[h] = deal
    deduped = list(seen.values())
    logger.info("Dedup: %d raw → %d unique deals", len(deals), len(deduped))
    return deduped

# ---------------------------------------------------------------------------
# Database persistence
# ---------------------------------------------------------------------------

async def _store_deals(deals: list[DealData]) -> int:
    """
    Persist new deals to the database and mark expired ones inactive.

    Returns the number of *new* deals inserted.
    """
    new_count = 0

    async with async_session() as session:
        async with session.begin():
            # Fetch existing hashes so we can skip duplicates
            result = await session.execute(
                select(InsuranceDeal.content_hash).where(InsuranceDeal.is_active == True)  # noqa: E712
            )
            existing_hashes: set[str] = {row[0] for row in result.fetchall()}

            for deal in deals:
                h = deal.content_hash
                if h in existing_hashes:
                    logger.debug("Skipping existing deal: %s", deal.title[:60])
                    continue

                record = InsuranceDeal(
                    title=deal.title,
                    carrier=deal.carrier,
                    description=deal.description,
                    estimated_savings=deal.estimated_savings,
                    deal_type=deal.deal_type,
                    source_url=deal.source_url,
                    requirements=deal.requirements,
                    content_hash=h,
                    expiry_date=deal.expiry_date,
                    scraped_at=deal.scraped_at,
                    is_active=True,
                )
                session.add(record)
                new_count += 1
                logger.info("New deal: [%s] %s", deal.carrier, deal.title[:60])

            # Mark deals not seen in this run as inactive (expired)
            current_hashes = {d.content_hash for d in deals}
            stale_hashes = existing_hashes - current_hashes
            if stale_hashes:
                await session.execute(
                    update(InsuranceDeal)
                    .where(InsuranceDeal.content_hash.in_(stale_hashes))
                    .values(is_active=False)
                )
                logger.info("Marked %d stale deals as inactive", len(stale_hashes))

    return new_count

# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

async def run_all_scrapers(
    *,
    include_aggregators: bool = True,
    persist: bool = True,
) -> dict:
    """
    Run all carrier (and optionally aggregator) scrapers concurrently,
    deduplicate results, and persist new deals to the database.

    Returns a summary dict::

        {
            "total_raw": int,
            "total_unique": int,
            "new_stored": int,
            "by_carrier": {carrier: count, ...},
            "errors": [str, ...],
        }
    """
    logger.info("=" * 60)
    logger.info("Starting insurance promo scan at %s", datetime.utcnow().isoformat())
    logger.info("=" * 60)

    errors: list[str] = []

    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=httpx.Timeout(REQUEST_TIMEOUT),
        http2=True,
    ) as client:

        # Build task list ------------------------------------------------
        tasks: dict[str, asyncio.Task] = {}

        for name, fn in CARRIER_SCRAPERS.items():
            tasks[name] = asyncio.create_task(fn(client), name=f"scrape_{name}")

        if include_aggregators:
            for name, fn in AGGREGATOR_SCRAPERS.items():
                tasks[name] = asyncio.create_task(fn(client), name=f"scrape_{name}")

        # Gather results -------------------------------------------------
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        all_deals: list[DealData] = []
        by_carrier: dict[str, int] = {}

        for name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                msg = f"[{name}] Scraper failed: {result!r}"
                logger.error(msg)
                errors.append(msg)
                by_carrier[name] = 0
            else:
                by_carrier[name] = len(result)
                all_deals.extend(result)

    total_raw = len(all_deals)
    logger.info("Raw deals collected: %d", total_raw)

    # Deduplicate --------------------------------------------------------
    unique_deals = deduplicate_deals(all_deals)
    total_unique = len(unique_deals)

    # Persist ------------------------------------------------------------
    new_stored = 0
    if persist and unique_deals:
        try:
            new_stored = await _store_deals(unique_deals)
        except Exception as exc:
            msg = f"Database persistence failed: {exc!r}"
            logger.error(msg)
            errors.append(msg)

    # Summary ------------------------------------------------------------
    summary = {
        "total_raw": total_raw,
        "total_unique": total_unique,
        "new_stored": new_stored,
        "by_carrier": by_carrier,
        "errors": errors,
    }

    logger.info("-" * 60)
    logger.info("Scan complete. Raw=%d  Unique=%d  NewStored=%d  Errors=%d",
                total_raw, total_unique, new_stored, len(errors))
    logger.info("Per-source: %s", by_carrier)
    if errors:
        logger.warning("Errors encountered:\n  %s", "\n  ".join(errors))
    logger.info("=" * 60)

    return summary


# ---------------------------------------------------------------------------
# Convenience: run a single carrier
# ---------------------------------------------------------------------------

async def run_single_carrier(carrier: str, *, persist: bool = False) -> list[DealData]:
    """
    Scrape a single carrier by name. Useful for testing or targeted refresh.

    Args:
        carrier: Carrier name (must match a key in CARRIER_SCRAPERS).
        persist: If True, store results in the database.

    Returns:
        List of DealData objects found.
    """
    fn = CARRIER_SCRAPERS.get(carrier)
    if fn is None:
        raise ValueError(
            f"Unknown carrier '{carrier}'. "
            f"Available: {', '.join(CARRIER_SCRAPERS.keys())}"
        )

    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=httpx.Timeout(REQUEST_TIMEOUT),
        http2=True,
    ) as client:
        deals = await fn(client)

    deals = deduplicate_deals(deals)

    if persist and deals:
        await _store_deals(deals)

    return deals


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

async def _main() -> None:
    """Run the full scan from the command line."""
    import json
    summary = await run_all_scrapers(persist=False)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(_main())
