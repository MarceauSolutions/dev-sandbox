#!/usr/bin/env python3
"""
Capture timestamped screenshots of Propane Fitness web pages as evidence.
Uses Playwright (headless Chromium) to produce full-page PDF and PNG screenshots.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "projects" / "marceau-solutions" / "labs" / "PropaneFitnessDispute" / "web-evidence"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PAGES = [
    {
        "name": "sales-page-onlinecoach",
        "url": "https://propanefitness.com/onlinecoach",
        "description": "Main sales page — note absence of 'dedicated 1-2-1 coach'",
    },
    {
        "name": "terms-of-use",
        "url": "https://www.propane-business.com/terms",
        "description": "Terms of Use — includes Section 7 (refund), 11.4 (misrepresentation), 12.5 (disputes)",
    },
    {
        "name": "clickfunnels-sales-page",
        "url": "https://propanefitness.clickfunnels.com/sales-page36722115",
        "description": "Clickfunnels sales page — describes 'group-based coaching'",
    },
    {
        "name": "is-this-a-scam-article",
        "url": "https://www.propane-business.com/articles/is-the-propane-fitness-mentorship-a-scam",
        "description": "Propane's own article acknowledging complaints and Coffeezilla reference",
    },
    {
        "name": "propane-business-homepage",
        "url": "https://www.propane-business.com",
        "description": "PropaneBusiness homepage",
    },
    {
        "name": "companies-house-registration",
        "url": "https://find-and-update.company-information.service.gov.uk/company/07779096",
        "description": "UK Companies House registration for Propane Fitness Ltd (Co. 07779096)",
    },
]


def capture_all():
    from playwright.sync_api import sync_playwright

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    print(f"Evidence capture started: {timestamp}")
    print(f"Output directory: {OUTPUT_DIR}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        for page_info in PAGES:
            name = page_info["name"]
            url = page_info["url"]
            desc = page_info["description"]

            print(f"Capturing: {name}")
            print(f"  URL: {url}")
            print(f"  Description: {desc}")

            try:
                page = context.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)  # Extra wait for dynamic content

                # Full-page PNG screenshot
                png_path = OUTPUT_DIR / f"{timestamp}_{name}.png"
                page.screenshot(path=str(png_path), full_page=True)
                print(f"  PNG: {png_path.name} ({png_path.stat().st_size // 1024}KB)")

                # PDF version (better for submission)
                pdf_path = OUTPUT_DIR / f"{timestamp}_{name}.pdf"
                page.pdf(
                    path=str(pdf_path),
                    format="Letter",
                    print_background=True,
                    margin={"top": "0.5in", "bottom": "0.5in", "left": "0.5in", "right": "0.5in"}
                )
                print(f"  PDF: {pdf_path.name} ({pdf_path.stat().st_size // 1024}KB)")

                page.close()
                print(f"  OK\n")

            except Exception as e:
                print(f"  ERROR: {e}\n")

        browser.close()

    # Create evidence index
    index_path = OUTPUT_DIR / f"{timestamp}_EVIDENCE-INDEX.md"
    with open(index_path, "w") as f:
        f.write(f"# Propane Fitness Web Evidence — Captured {timestamp}\n\n")
        f.write("These screenshots were captured programmatically using Playwright (headless Chromium)\n")
        f.write(f"on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} from the cardholder's computer.\n\n")
        f.write("| Page | URL | Files |\n")
        f.write("|------|-----|-------|\n")
        for page_info in PAGES:
            name = page_info["name"]
            url = page_info["url"]
            f.write(f"| {page_info['description']} | {url} | `{timestamp}_{name}.png` / `.pdf` |\n")

    print(f"Evidence index: {index_path.name}")
    print(f"\nAll evidence saved to: {OUTPUT_DIR}")
    print(f"Total files: {len(list(OUTPUT_DIR.glob(f'{timestamp}_*')))}")


if __name__ == "__main__":
    capture_all()
