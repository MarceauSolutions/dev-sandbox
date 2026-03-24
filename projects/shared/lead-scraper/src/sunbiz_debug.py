#!/usr/bin/env python3
"""Get raw text from Dolphin Cooling and Family Air detail pages."""
import asyncio
from playwright.async_api import async_playwright

async def get_detail_text(page, search_term, match_text):
    await page.goto("https://search.sunbiz.org/Inquiry/CorporationSearch/ByName", timeout=15000)
    await page.fill("input#SearchTerm", search_term)
    await page.click("input[type=submit]")
    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_timeout(500)
    links = await page.query_selector_all("a")
    for link in links:
        href = await link.get_attribute("href") or ""
        if "/CorporationSearch/SearchResultDetail" in href:
            text = (await link.text_content()).strip()
            if match_text.upper() in text.upper():
                await page.goto(f"https://search.sunbiz.org{href}", timeout=15000)
                await page.wait_for_load_state("domcontentloaded")
                return await page.inner_text("body")
    return None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0")

        for search_term, match_text, label in [
            ("Dolphin Cooling Heating", "DOLPHIN COOLING AND HEATING", "Dolphin Cooling"),
            ("Family Air Conditioning and Heating", "FAMILY AIR CONDITIONING AND HEATING", "Family Air"),
        ]:
            print(f"\n=== {label} ===")
            text = await get_detail_text(page, search_term, match_text)
            if text:
                # Print the relevant section
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                for i, line in enumerate(lines):
                    if any(k in line.upper() for k in ["AGENT", "OFFICER", "TITLE", "AUTHORIZED", "PRESIDENT", "MANAGER"]):
                        print(f"  [{i}] {line}")
                        for j in range(i+1, min(i+5, len(lines))):
                            print(f"  [{j}]   {lines[j]}")
            else:
                print("  NOT FOUND")

        await browser.close()

asyncio.run(main())
