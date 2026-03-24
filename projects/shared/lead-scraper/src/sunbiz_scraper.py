#!/usr/bin/env python3
"""
Sunbiz owner name scraper using Playwright.
Parses officer names from Florida Division of Corporations detail pages.
"""

import json
import asyncio
import sys
import re
import sqlite3
from pathlib import Path
from playwright.async_api import async_playwright

SEARCH_URL = "https://search.sunbiz.org/Inquiry/CorporationSearch/ByName"

# (pipeline_db_company_name, sunbiz_search_term)
COMPANIES = [
    ("Family Air Conditioning and Heating, Inc.", "Family Air Conditioning"),
    ("Cool Zone Inc", "Cool Zone Inc"),
    ("One Way Air", "One Way Air"),
    ("Dolphin Cooling & Heating Inc", "Dolphin Cooling"),
    ("Stone Cold HVAC", "Stone Cold HVAC"),
    ("ASH HEATING AND AIR CONDITIONING", "ASH Heating Air Conditioning"),
    ("Accurate Comfort Services - Naples, FL", "Accurate Comfort Services"),
    ("Homepatible", "Homepatible"),
    ("Freeze The Heat Air Conditioning & Duct Cleaning", "Freeze The Heat"),
    ("Soave Mechanical", "Soave Mechanical"),
    ("Always Be Cooling - Air Conditioning, HVAC Installation, AC Maintenance, Insulation, & Duct Cleaning", "Always Be Cooling"),
    ("Downeast Air Heating & Cooling", "Downeast Air"),
    ("Jackson Total Service", "Jackson Total Service"),
    ("JL Appliances Services Inc", "JL Appliances Services"),
    ("Wilshere AC Repair Naples", "Wilshere AC"),
    ("Naples Air Conditioning LLC", "Naples Air Conditioning"),
    ("Low Temp A/C LLC", "Low Temp AC"),
    ("Nixon Air Conditioning", "Nixon Air Conditioning"),
    ("JP Brett & Sons Air Conditioning", "JP Brett Sons"),
]


def parse_name(raw: str) -> str:
    """Convert 'LAST, FIRST MIDDLE' to 'First Last'."""
    raw = raw.strip().rstrip(",")
    if "," in raw:
        parts = raw.split(",", 1)
        last = parts[0].strip().title()
        first = parts[1].strip().title()
        return f"{first} {last}"
    return raw.title()


async def get_officer(page, db_company: str, search_term: str) -> dict | None:
    try:
        await page.goto(SEARCH_URL, timeout=15000, wait_until="domcontentloaded")
        await page.fill("input#SearchTerm", search_term)
        await page.click("input[type=submit]")
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(400)

        # Get first result link
        links = await page.query_selector_all("a")
        detail_href = None
        for link in links:
            href = await link.get_attribute("href")
            if href and "/CorporationSearch/SearchResultDetail" in href:
                detail_href = href
                break

        if not detail_href:
            return None

        await page.goto(f"https://search.sunbiz.org{detail_href}", timeout=15000)
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(300)

        text = await page.inner_text("body")
        lines = [l.strip() for l in text.split("\n")]

        # Strategy: find "Title [ROLE]" then grab next non-empty line as the name
        # Names are in ALL-CAPS "LAST, FIRST" format
        PRIORITY_TITLES = ["PRESIDENT", "OWNER", "CEO", "MANAGER", "MANAGING MEMBER", "MEMBER", "REGISTERED AGENT"]
        candidates = []

        for i, line in enumerate(lines):
            if line.upper().startswith("TITLE "):
                title = line[6:].strip()
                # Grab next non-empty line
                for j in range(i+1, min(i+5, len(lines))):
                    candidate = lines[j].strip()
                    if candidate and re.match(r"^[A-Z][A-Z\s,'-]{3,}$", candidate):
                        candidates.append({"name": candidate, "title": title})
                        break

        if not candidates:
            # Also check registered agent
            for i, line in enumerate(lines):
                if "REGISTERED AGENT NAME" in line.upper():
                    for j in range(i+1, min(i+5, len(lines))):
                        candidate = lines[j].strip()
                        if candidate and re.match(r"^[A-Z][A-Z\s,'-]{3,}$", candidate):
                            candidates.append({"name": candidate, "title": "Registered Agent"})
                            break

        if not candidates:
            return None

        # Pick best: prefer President > Owner > Manager > first
        best = candidates[0]
        for c in candidates:
            t = c["title"].upper()
            for pt in PRIORITY_TITLES:
                if pt in t:
                    best = c
                    break

        return {
            "company": db_company,
            "name": parse_name(best["name"]),
            "title": best["title"].title(),
            "source": "sunbiz"
        }

    except Exception as e:
        print(f"  ERR {db_company}: {e}", file=sys.stderr)
    return None


async def main():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        for db_company, search_term in COMPANIES:
            short = search_term[:30]
            print(f"  {short:<30}", end=" ", flush=True)
            result = await get_officer(page, db_company, search_term)
            if result:
                print(f"✓ {result['name']} ({result['title']})")
                results.append(result)
            else:
                print("—")
            await asyncio.sleep(0.3)

        await browser.close()

    print(f"\nFound {len(results)}/{len(COMPANIES)} names")

    if results:
        # Update local pipeline.db
        db_path = Path(__file__).parents[3] / "sales-pipeline" / "data" / "pipeline.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            updated = 0
            for r in results:
                match_key = r["company"][:30]
                cur = conn.execute(
                    "UPDATE deals SET contact_name=? WHERE company LIKE ? AND (contact_name IS NULL OR contact_name='')",
                    (r["name"], f"%{match_key}%")
                )
                if cur.rowcount > 0:
                    updated += cur.rowcount
                    print(f"  DB updated: {r['company'][:50]} → {r['name']}")
            conn.commit()
            conn.close()
            print(f"\n{updated} records updated in pipeline.db")

    out_path = Path(__file__).parent.parent / "output" / "sunbiz_owners.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved → {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
