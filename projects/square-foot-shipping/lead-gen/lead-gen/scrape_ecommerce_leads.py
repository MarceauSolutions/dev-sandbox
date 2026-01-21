#!/usr/bin/env python3
"""
E-commerce Lead Scraper for Square Foot Shipping

This wrapper script uses the dev-sandbox lead-scraper to find e-commerce sellers
who need shipping services (100-1000 packages/month volume).

Target Profile:
- E-commerce stores (Shopify, WooCommerce, Amazon FBA sellers)
- Physical goods (not digital products)
- Estimated shipping volume: 100-1000 packages/month
- Located in target markets (SW Florida, expanding nationwide)

Usage:
    # Dry run (test without making API calls)
    python scrape_ecommerce_leads.py --dry-run --limit 10

    # Real scrape
    python scrape_ecommerce_leads.py --area "Naples, FL" --limit 50

    # Scrape multiple areas
    python scrape_ecommerce_leads.py --all-areas --limit 100
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add dev-sandbox lead-scraper to path
DEV_SANDBOX_PATH = Path("/Users/williammarceaujr./dev-sandbox")
LEAD_SCRAPER_PATH = DEV_SANDBOX_PATH / "projects" / "lead-scraper"
sys.path.insert(0, str(LEAD_SCRAPER_PATH))

from src.scraper import LeadScraperCLI
from src.models import Lead
from src.config import ScraperConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# E-commerce specific configuration
ECOMMERCE_CATEGORIES = [
    "online store",
    "e-commerce",
    "retail store",
    "gift shop",
    "boutique",
    "sporting goods",
    "home goods",
    "apparel store",
    "electronics store",
    "jewelry store",
    "toy store",
    "bookstore",
    "pet store",
    "health food store",
    "vitamin store"
]

# Shipping volume estimation (very rough heuristics)
VOLUME_INDICATORS = {
    "high": {  # 500-1000+ packages/month
        "review_count_min": 100,
        "keywords": ["nationwide shipping", "ships worldwide", "free shipping"]
    },
    "medium": {  # 100-500 packages/month
        "review_count_min": 30,
        "keywords": ["online orders", "delivery available", "shop online"]
    },
    "low": {  # <100 packages/month (still viable)
        "review_count_min": 10,
        "keywords": ["shipping", "mail order"]
    }
}


class EcommerceLeadScraper:
    """Wrapper for lead-scraper focused on e-commerce shipping leads."""

    def __init__(self, output_dir: str = "scraped-leads"):
        self.output_dir = Path(__file__).parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize base scraper
        self.scraper = LeadScraperCLI(output_dir=str(self.output_dir))

        # Override categories for e-commerce focus
        self.scraper.config.search.target_categories = ECOMMERCE_CATEGORIES

        logger.info(f"Initialized e-commerce lead scraper")
        logger.info(f"Output directory: {self.output_dir}")

    def estimate_shipping_volume(self, lead: Lead) -> Dict[str, Any]:
        """
        Estimate monthly shipping volume for a lead.

        Returns dict with:
        - volume_tier: "high", "medium", "low", or "unknown"
        - estimated_packages_min: int
        - estimated_packages_max: int
        - confidence: float (0-1)
        """
        # Default unknown
        result = {
            "volume_tier": "unknown",
            "estimated_packages_min": 0,
            "estimated_packages_max": 0,
            "confidence": 0.0
        }

        # Check review count as proxy for business volume
        if lead.review_count >= VOLUME_INDICATORS["high"]["review_count_min"]:
            result["volume_tier"] = "high"
            result["estimated_packages_min"] = 500
            result["estimated_packages_max"] = 1000
            result["confidence"] = 0.6
        elif lead.review_count >= VOLUME_INDICATORS["medium"]["review_count_min"]:
            result["volume_tier"] = "medium"
            result["estimated_packages_min"] = 100
            result["estimated_packages_max"] = 500
            result["confidence"] = 0.5
        elif lead.review_count >= VOLUME_INDICATORS["low"]["review_count_min"]:
            result["volume_tier"] = "low"
            result["estimated_packages_min"] = 10
            result["estimated_packages_max"] = 100
            result["confidence"] = 0.4

        # Boost confidence if website mentions shipping keywords
        if lead.website or lead.notes:
            combined_text = f"{lead.website} {lead.notes}".lower()
            for tier, indicators in VOLUME_INDICATORS.items():
                if any(keyword in combined_text for keyword in indicators["keywords"]):
                    if result["volume_tier"] == "unknown":
                        result["volume_tier"] = tier
                        result["estimated_packages_min"] = 50
                        result["estimated_packages_max"] = 200
                    result["confidence"] = min(result["confidence"] + 0.2, 1.0)
                    break

        return result

    def filter_ecommerce_leads(self, leads: List[Lead]) -> List[Dict[str, Any]]:
        """
        Filter and enrich leads for e-commerce shipping prospects.

        Returns list of dicts with lead data + shipping volume estimate.
        """
        qualified_leads = []

        for lead in leads:
            # Estimate shipping volume
            volume_estimate = self.estimate_shipping_volume(lead)

            # Filter: Must have at least "low" volume estimate
            if volume_estimate["volume_tier"] == "unknown":
                continue

            # Filter: Prefer leads with websites (can check for e-commerce platform)
            has_website = bool(lead.website)

            # Create enriched lead record
            enriched_lead = {
                "business_name": lead.business_name,
                "contact_name": lead.owner_name or "",
                "phone": lead.phone or "",
                "email": lead.email or "",
                "website": lead.website or "",
                "address": lead.address,
                "city": lead.city,
                "state": lead.state,
                "category": lead.category,
                "rating": lead.rating,
                "review_count": lead.review_count,
                "volume_tier": volume_estimate["volume_tier"],
                "estimated_packages_min": volume_estimate["estimated_packages_min"],
                "estimated_packages_max": volume_estimate["estimated_packages_max"],
                "confidence": volume_estimate["confidence"],
                "has_website": has_website,
                "social_media": {
                    "facebook": lead.facebook or "",
                    "instagram": lead.instagram or ""
                },
                "scraped_at": lead.scraped_at
            }

            qualified_leads.append(enriched_lead)

        # Sort by estimated volume (descending) and confidence
        qualified_leads.sort(
            key=lambda x: (x["estimated_packages_max"], x["confidence"]),
            reverse=True
        )

        return qualified_leads

    def scrape(
        self,
        areas: List[str] = None,
        limit: int = 100,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Run the e-commerce lead scraping process.

        Args:
            areas: List of area names (e.g., ["Naples, FL"])
            limit: Max leads to return
            dry_run: If True, just test setup without making real API calls

        Returns:
            Dict with results summary
        """
        if dry_run:
            logger.info("=== DRY RUN MODE ===")
            logger.info("This would scrape e-commerce leads using:")
            logger.info(f"  Categories: {', '.join(ECOMMERCE_CATEGORIES[:5])}... (+{len(ECOMMERCE_CATEGORIES)-5} more)")
            logger.info(f"  Areas: {areas or 'All configured areas'}")
            logger.info(f"  Limit: {limit}")
            logger.info(f"  Output: {self.output_dir}/scraped-leads.json")
            logger.info("\nNo API calls made in dry-run mode.")

            # Create sample lead for demonstration
            sample_lead = Lead(
                business_name="Sample E-commerce Store",
                category="online store",
                city="Naples",
                state="FL",
                phone="+1-239-555-0100",
                website="https://example-store.com",
                review_count=45,
                rating=4.5
            )
            sample_leads = [sample_lead]
            qualified = self.filter_ecommerce_leads(sample_leads)

            logger.info(f"\nSample qualified lead:")
            logger.info(json.dumps(qualified[0], indent=2))

            return {
                "dry_run": True,
                "total_scraped": 1,
                "qualified_leads": 1,
                "sample_output": qualified[0]
            }

        # Real scrape
        logger.info("=== SCRAPING E-COMMERCE LEADS ===")

        # Convert area names to area dicts
        if areas:
            area_dicts = []
            for area_name in areas:
                # Try to find in configured areas
                matching = [a for a in self.scraper.config.search.surrounding_areas
                           if area_name.lower() in a["name"].lower()]
                if matching:
                    area_dicts.extend(matching)
                else:
                    # Use default coordinates
                    area_dicts.append({
                        "name": area_name,
                        "lat": self.scraper.config.search.default_latitude,
                        "lng": self.scraper.config.search.default_longitude
                    })
        else:
            # Use all configured areas
            area_dicts = self.scraper.config.search.surrounding_areas

        # Run scrape
        new_leads = self.scraper.scrape(
            categories=ECOMMERCE_CATEGORIES,
            areas=area_dicts,
            sources=["google", "yelp"],
            get_details=True
        )

        # Get all leads
        all_leads = list(self.scraper.leads.leads.values())

        # Filter and enrich for e-commerce shipping
        qualified_leads = self.filter_ecommerce_leads(all_leads)

        # Limit results
        qualified_leads = qualified_leads[:limit]

        # Save to JSON
        output_file = self.output_dir / "scraped-leads.json"
        with open(output_file, 'w') as f:
            json.dump({
                "scrape_date": datetime.now().isoformat(),
                "total_scraped": len(all_leads),
                "qualified_count": len(qualified_leads),
                "leads": qualified_leads
            }, f, indent=2)

        logger.info(f"\n=== SCRAPING COMPLETE ===")
        logger.info(f"Total leads scraped: {len(all_leads)}")
        logger.info(f"Qualified e-commerce leads: {len(qualified_leads)}")
        logger.info(f"Output saved to: {output_file}")

        # Show tier breakdown
        tier_counts = {}
        for lead in qualified_leads:
            tier = lead["volume_tier"]
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        logger.info("\nShipping Volume Breakdown:")
        for tier in ["high", "medium", "low"]:
            count = tier_counts.get(tier, 0)
            if count > 0:
                logger.info(f"  {tier.capitalize()} (100-1000 pkg/mo): {count}")

        return {
            "dry_run": False,
            "total_scraped": len(all_leads),
            "qualified_leads": len(qualified_leads),
            "output_file": str(output_file),
            "tier_breakdown": tier_counts
        }


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="E-commerce lead scraper for Square Foot Shipping",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run (test without API calls)
    python scrape_ecommerce_leads.py --dry-run --limit 10

    # Scrape Naples area
    python scrape_ecommerce_leads.py --area "Naples, FL" --limit 50

    # Scrape all SW Florida areas
    python scrape_ecommerce_leads.py --all-areas --limit 100

    # Specific areas
    python scrape_ecommerce_leads.py --area "Fort Myers, FL" --area "Cape Coral, FL"
        """
    )

    parser.add_argument(
        "--area", "-a",
        type=str,
        action="append",
        help="Target area (can specify multiple times)"
    )
    parser.add_argument(
        "--all-areas",
        action="store_true",
        help="Scrape all configured SW Florida areas"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=100,
        help="Max qualified leads to return (default: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode - no real API calls"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="scraped-leads",
        help="Output directory (default: scraped-leads/)"
    )

    args = parser.parse_args()

    # Validate args
    if not args.dry_run and not args.area and not args.all_areas:
        parser.error("Please specify --area, --all-areas, or --dry-run")

    # Determine areas
    areas = None
    if args.all_areas:
        areas = None  # Will use all configured areas
    elif args.area:
        areas = args.area

    # Run scraper
    scraper = EcommerceLeadScraper(output_dir=args.output_dir)
    results = scraper.scrape(
        areas=areas,
        limit=args.limit,
        dry_run=args.dry_run
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
