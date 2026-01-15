#!/usr/bin/env python3
"""
Lead Scraper - Main entry point for local business lead generation.

Usage:
    python -m src.scraper --help
    python -m src.scraper scrape --category "gym" --location "Naples, FL"
    python -m src.scraper scrape --all-categories --all-areas
    python -m src.scraper export --format csv
    python -m src.scraper stats

Environment Variables:
    GOOGLE_PLACES_API_KEY - Google Places API key
    YELP_API_KEY - Yelp Fusion API key
"""

import argparse
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import ScraperConfig, SearchConfig
from src.models import Lead, LeadCollection
from src.google_places import GooglePlacesScraper
from src.yelp import YelpScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class LeadScraperCLI:
    """Main lead scraper orchestrator."""

    def __init__(self, output_dir: str = "output"):
        self.config = ScraperConfig()
        self.config.api = self.config.api.from_env()

        # Initialize output directory (relative to project root)
        project_root = Path(__file__).parent.parent
        self.output_dir = project_root / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize lead collection
        self.leads = LeadCollection(str(self.output_dir))

        # Initialize scrapers
        self.google_scraper = GooglePlacesScraper(self.config)
        self.yelp_scraper = YelpScraper(self.config)

        # Load existing data
        self._load_existing_data()

    def _load_existing_data(self) -> None:
        """Load existing leads and optout list."""
        # Load optout list
        self.leads.load_optout_list()

        # Load existing leads
        json_count = self.leads.load_json()
        if json_count > 0:
            logger.info(f"Loaded {json_count} existing leads from JSON")

    def _save_progress(self) -> None:
        """Save current progress to files."""
        self.leads.save_json()
        self.leads.save_csv()
        self.leads.save_optout_list()
        logger.info(f"Progress saved: {len(self.leads.leads)} total leads")

    def scrape(
        self,
        categories: Optional[List[str]] = None,
        areas: Optional[List[Dict]] = None,
        sources: List[str] = None,
        get_details: bool = True
    ) -> int:
        """
        Run the lead scraping process.

        Args:
            categories: List of business categories to scrape
            areas: List of areas with name, lat, lng
            sources: List of sources to use ["google", "yelp"]
            get_details: Whether to fetch detailed info (more API calls)

        Returns:
            Number of new leads found
        """
        if categories is None:
            categories = self.config.search.target_categories
        if areas is None:
            areas = self.config.search.surrounding_areas
        if sources is None:
            sources = ["google", "yelp"]

        initial_count = len(self.leads.leads)
        new_leads = 0

        for area in areas:
            area_name = area.get("name", "Unknown")
            latitude = area.get("lat", self.config.search.default_latitude)
            longitude = area.get("lng", self.config.search.default_longitude)

            logger.info(f"=== Scraping area: {area_name} ===")

            # Google Places
            if "google" in sources and self.config.api.google_places_api_key:
                logger.info(f"Using Google Places API for {area_name}...")
                try:
                    for lead in self.google_scraper.scrape_area(
                        area_name=area_name,
                        categories=categories,
                        latitude=latitude,
                        longitude=longitude,
                        radius_meters=self.config.search.default_radius_meters,
                        get_details=get_details
                    ):
                        if self.leads.add(lead):
                            new_leads += 1

                        # Save progress periodically
                        if new_leads % 50 == 0 and new_leads > 0:
                            self._save_progress()

                except Exception as e:
                    logger.error(f"Google Places error for {area_name}: {e}")

            # Yelp
            if "yelp" in sources and self.config.api.yelp_api_key:
                logger.info(f"Using Yelp API for {area_name}...")
                try:
                    for lead in self.yelp_scraper.scrape_area(
                        area_name=area_name,
                        categories=categories,
                        location=area_name,
                        latitude=latitude,
                        longitude=longitude,
                        get_details=get_details
                    ):
                        if self.leads.add(lead):
                            new_leads += 1

                        # Save progress periodically
                        if new_leads % 50 == 0 and new_leads > 0:
                            self._save_progress()

                except Exception as e:
                    logger.error(f"Yelp error for {area_name}: {e}")

            # Save after each area
            self._save_progress()

        final_count = len(self.leads.leads)
        logger.info(f"=== Scraping complete ===")
        logger.info(f"New leads: {new_leads}")
        logger.info(f"Total leads: {final_count}")
        logger.info(f"Duplicates merged: {new_leads - (final_count - initial_count)}")

        return new_leads

    def export(self, format: str = "both", filename: str = None) -> List[str]:
        """
        Export leads to file(s).

        Args:
            format: "csv", "json", or "both"
            filename: Custom filename (without extension)

        Returns:
            List of created file paths
        """
        files = []

        if format in ["csv", "both"]:
            csv_file = filename + ".csv" if filename else "leads.csv"
            path = self.leads.save_csv(csv_file)
            files.append(path)
            logger.info(f"Exported to CSV: {path}")

        if format in ["json", "both"]:
            json_file = filename + ".json" if filename else "leads.json"
            path = self.leads.save_json(json_file)
            files.append(path)
            logger.info(f"Exported to JSON: {path}")

        return files

    def filter_leads(
        self,
        category: str = None,
        city: str = None,
        pain_points: List[str] = None,
        has_email: bool = None,
        has_phone: bool = None,
        min_rating: float = None
    ) -> List[Lead]:
        """
        Filter leads by various criteria.

        Returns:
            List of matching leads
        """
        results = list(self.leads.leads.values())

        if category:
            results = [l for l in results if category.lower() in l.category.lower()]

        if city:
            results = [l for l in results if city.lower() in l.city.lower()]

        if pain_points:
            results = [l for l in results if any(pp in l.pain_points for pp in pain_points)]

        if has_email is not None:
            if has_email:
                results = [l for l in results if l.email]
            else:
                results = [l for l in results if not l.email]

        if has_phone is not None:
            if has_phone:
                results = [l for l in results if l.phone]
            else:
                results = [l for l in results if not l.phone]

        if min_rating is not None:
            results = [l for l in results if l.rating >= min_rating]

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the lead collection."""
        return self.leads.get_statistics()

    def add_optout(self, identifier: str) -> None:
        """Add identifier to optout list."""
        self.leads.add_optout(identifier)
        self.leads.save_optout_list()
        logger.info(f"Added to optout list: {identifier}")


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Lead Scraper - Local business lead generation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Scrape gyms in Naples
    python -m src.scraper scrape --category gym --area "Naples, FL"

    # Scrape all categories in all configured areas
    python -m src.scraper scrape --all-categories --all-areas

    # Scrape only using Google (no Yelp)
    python -m src.scraper scrape --source google --all-categories

    # Export to CSV
    python -m src.scraper export --format csv --filename naples_leads

    # Show statistics
    python -m src.scraper stats

    # Filter leads
    python -m src.scraper filter --category gym --city Naples --pain-point no_website

    # Add optout
    python -m src.scraper optout --add "business@example.com"

Environment Variables:
    GOOGLE_PLACES_API_KEY - Google Places API key
    YELP_API_KEY - Yelp Fusion API key
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape leads from sources")
    scrape_parser.add_argument("--category", "-c", type=str, help="Single category to scrape")
    scrape_parser.add_argument("--all-categories", action="store_true", help="Scrape all configured categories")
    scrape_parser.add_argument("--area", "-a", type=str, help="Single area name (e.g., 'Naples, FL')")
    scrape_parser.add_argument("--all-areas", action="store_true", help="Scrape all configured areas")
    scrape_parser.add_argument("--source", "-s", type=str, choices=["google", "yelp", "all"], default="all",
                               help="Data source to use")
    scrape_parser.add_argument("--no-details", action="store_true", help="Skip fetching detailed info (faster)")
    scrape_parser.add_argument("--output-dir", "-o", type=str, default="output", help="Output directory")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export leads to file")
    export_parser.add_argument("--format", "-f", type=str, choices=["csv", "json", "both"], default="both",
                               help="Export format")
    export_parser.add_argument("--filename", type=str, help="Output filename (without extension)")
    export_parser.add_argument("--output-dir", "-o", type=str, default="output", help="Output directory")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show lead statistics")
    stats_parser.add_argument("--output-dir", "-o", type=str, default="output", help="Output directory")

    # Filter command
    filter_parser = subparsers.add_parser("filter", help="Filter and display leads")
    filter_parser.add_argument("--category", "-c", type=str, help="Filter by category")
    filter_parser.add_argument("--city", type=str, help="Filter by city")
    filter_parser.add_argument("--pain-point", "-p", type=str, action="append", help="Filter by pain point")
    filter_parser.add_argument("--has-email", action="store_true", help="Only leads with email")
    filter_parser.add_argument("--has-phone", action="store_true", help="Only leads with phone")
    filter_parser.add_argument("--min-rating", type=float, help="Minimum rating")
    filter_parser.add_argument("--output-dir", "-o", type=str, default="output", help="Output directory")
    filter_parser.add_argument("--export", type=str, help="Export filtered results to file")

    # Optout command
    optout_parser = subparsers.add_parser("optout", help="Manage optout list")
    optout_parser.add_argument("--add", type=str, help="Add identifier to optout list")
    optout_parser.add_argument("--list", action="store_true", help="List all optouts")
    optout_parser.add_argument("--output-dir", "-o", type=str, default="output", help="Output directory")

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize scraper
    output_dir = getattr(args, "output_dir", "output")
    scraper = LeadScraperCLI(output_dir=output_dir)

    if args.command == "scrape":
        # Determine categories
        if args.all_categories:
            categories = scraper.config.search.target_categories
        elif args.category:
            categories = [args.category]
        else:
            print("Please specify --category or --all-categories")
            return 1

        # Determine areas
        if args.all_areas:
            areas = scraper.config.search.surrounding_areas
        elif args.area:
            # Find matching area or create custom one
            matching = [a for a in scraper.config.search.surrounding_areas if args.area.lower() in a["name"].lower()]
            if matching:
                areas = matching
            else:
                # Create custom area entry (will use default lat/lng)
                areas = [{"name": args.area, "lat": scraper.config.search.default_latitude,
                          "lng": scraper.config.search.default_longitude}]
        else:
            print("Please specify --area or --all-areas")
            return 1

        # Determine sources
        if args.source == "all":
            sources = ["google", "yelp"]
        else:
            sources = [args.source]

        # Run scraper
        new_leads = scraper.scrape(
            categories=categories,
            areas=areas,
            sources=sources,
            get_details=not args.no_details
        )

        print(f"\nScraping complete! Found {new_leads} new leads.")
        print(f"Total leads: {len(scraper.leads.leads)}")

    elif args.command == "export":
        files = scraper.export(format=args.format, filename=args.filename)
        print(f"Exported to: {', '.join(files)}")

    elif args.command == "stats":
        stats = scraper.get_stats()
        print("\n=== Lead Statistics ===")
        print(f"Total leads: {stats['total_leads']}")
        print(f"With email: {stats['with_email']}")
        print(f"With phone: {stats['with_phone']}")
        print(f"With website: {stats['with_website']}")
        print("\nBy Category:")
        for cat, count in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")
        print("\nBy City:")
        for city, count in sorted(stats["by_city"].items(), key=lambda x: -x[1]):
            print(f"  {city}: {count}")
        print("\nBy Source:")
        for source, count in stats["by_source"].items():
            print(f"  {source}: {count}")
        print("\nBy Pain Point:")
        for pp, count in sorted(stats["by_pain_point"].items(), key=lambda x: -x[1]):
            print(f"  {pp}: {count}")

    elif args.command == "filter":
        results = scraper.filter_leads(
            category=args.category,
            city=args.city,
            pain_points=args.pain_point,
            has_email=args.has_email if args.has_email else None,
            has_phone=args.has_phone if args.has_phone else None,
            min_rating=args.min_rating
        )

        print(f"\nFound {len(results)} matching leads:")
        for lead in results[:20]:  # Show first 20
            print(f"\n  {lead.business_name}")
            print(f"    Category: {lead.category}")
            print(f"    Location: {lead.city}, {lead.state}")
            print(f"    Phone: {lead.phone or 'N/A'}")
            print(f"    Website: {lead.website or 'N/A'}")
            print(f"    Rating: {lead.rating} ({lead.review_count} reviews)")
            if lead.pain_points:
                print(f"    Pain Points: {', '.join(lead.pain_points)}")

        if len(results) > 20:
            print(f"\n  ... and {len(results) - 20} more")

        if args.export:
            # Export filtered results
            collection = LeadCollection(str(scraper.output_dir))
            for lead in results:
                collection.leads[lead.id] = lead
            collection.save_csv(args.export + ".csv")
            collection.save_json(args.export + ".json")
            print(f"\nExported filtered results to {args.export}.csv and {args.export}.json")

    elif args.command == "optout":
        if args.add:
            scraper.add_optout(args.add)
            print(f"Added to optout list: {args.add}")
        elif args.list:
            print("Optout list:")
            for identifier in sorted(scraper.leads.optout_list):
                print(f"  {identifier}")
            print(f"\nTotal: {len(scraper.leads.optout_list)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
