#!/usr/bin/env python3
"""
Competitor Enrichment - Add competitor intelligence to leads

This script finds the top competitor for each lead (same category, same city, higher reviews/better website)
and adds competitor data to the lead for hyper-personalized messaging.

Usage:
    python -m src.competitor_enrichment enrich --limit 50
    python -m src.competitor_enrichment status
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompetitorEnrichment:
    """Enrich leads with competitor intelligence."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.google_api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    def find_top_competitor(self, lead: Dict) -> Optional[Dict]:
        """
        Find top competitor for a lead.

        Strategy:
        1. Search Google Places for same category + city
        2. Filter to businesses with:
           - Higher review count OR
           - Website (if lead has no website)
        3. Return top result

        Returns dict with: name, rating, review_count, website
        """
        if not self.google_api_key:
            logger.warning("No GOOGLE_PLACES_API_KEY - using mock data")
            return self._mock_competitor(lead)

        import requests

        # Build search query
        category = lead.get("category", "business")
        city = lead.get("city", "")
        query = f"{category} in {city}"

        # Google Places Text Search API
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "key": self.google_api_key,
            "type": category.lower().replace(" ", "_")
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK":
                logger.warning(f"Google Places API error: {data.get('status')}")
                return None

            results = data.get("results", [])

            # Filter competitors
            lead_name = lead.get("business_name", "").lower()
            lead_review_count = lead.get("review_count", 0)
            lead_has_website = bool(lead.get("website"))

            competitors = []
            for place in results:
                name = place.get("name", "")

                # Skip if same business
                if name.lower() == lead_name:
                    continue

                review_count = place.get("user_ratings_total", 0)
                rating = place.get("rating", 0.0)

                # Only consider if they have MORE reviews OR a website (if lead doesn't)
                if review_count > lead_review_count or (not lead_has_website and "website" in place):
                    competitors.append({
                        "name": name,
                        "rating": rating,
                        "review_count": review_count,
                        "website": place.get("website", ""),
                        "address": place.get("formatted_address", "")
                    })

            # Return top competitor (most reviews)
            if competitors:
                top = max(competitors, key=lambda c: c["review_count"])
                logger.info(f"Found competitor for {lead['business_name']}: {top['name']} ({top['review_count']} reviews)")
                return top

            return None

        except Exception as e:
            logger.error(f"Error finding competitor: {e}")
            return None

    def _mock_competitor(self, lead: Dict) -> Optional[Dict]:
        """Generate mock competitor data for testing."""
        category = lead.get("category", "Gym")
        city = lead.get("city", "Naples")

        # Mock competitor name based on category
        mock_names = {
            "gym": f"{city} Fitness",
            "salon": f"{city} Beauty",
            "restaurant": f"{city} Bistro"
        }

        category_lower = category.lower()
        for key, name in mock_names.items():
            if key in category_lower:
                return {
                    "name": name,
                    "rating": 4.5,
                    "review_count": lead.get("review_count", 0) + 30,  # +30 reviews
                    "website": f"https://www.{name.lower().replace(' ', '')}.com",
                    "address": f"123 Main St, {city}"
                }

        return None

    def enrich_leads(self, limit: int = None) -> Dict:
        """
        Enrich leads with competitor data.

        Updates leads.json with competitor fields.
        """
        from .models import LeadCollection

        # Load leads
        leads_collection = LeadCollection(output_dir=str(self.output_dir))
        leads_collection.load_json("leads.json")

        all_leads = list(leads_collection.leads.values())

        if limit:
            all_leads = all_leads[:limit]

        enriched_count = 0
        failed_count = 0

        for lead_obj in all_leads:
            lead_dict = lead_obj.to_dict()

            # Skip if already has competitor data
            if lead_dict.get("competitor_name"):
                logger.info(f"Skipping {lead_dict['business_name']} - already enriched")
                continue

            # Find competitor
            competitor = self.find_top_competitor(lead_dict)

            if competitor:
                # Update lead object
                lead_obj.competitor_name = competitor["name"]
                lead_obj.competitor_rating = competitor["rating"]
                lead_obj.competitor_review_count = competitor["review_count"]
                lead_obj.competitor_website = competitor["website"]

                enriched_count += 1
            else:
                failed_count += 1

        # Save updated leads
        if enriched_count > 0:
            leads_collection.save_json("leads.json")
            logger.info(f"Enriched {enriched_count} leads with competitor data")

        return {
            "total_processed": len(all_leads),
            "enriched": enriched_count,
            "failed": failed_count
        }

    def get_status(self) -> Dict:
        """Get enrichment status."""
        from .models import LeadCollection

        leads_collection = LeadCollection(output_dir=str(self.output_dir))
        leads_collection.load_json("leads.json")

        total = len(leads_collection.leads)
        with_competitor = sum(1 for l in leads_collection.leads.values() if l.competitor_name)

        return {
            "total_leads": total,
            "enriched_with_competitor": with_competitor,
            "needs_enrichment": total - with_competitor,
            "enrichment_percentage": round((with_competitor / total * 100), 1) if total > 0 else 0
        }


def main():
    parser = argparse.ArgumentParser(description="Competitor Enrichment for Leads")
    parser.add_argument("command", choices=["enrich", "status"])
    parser.add_argument("--limit", type=int, help="Limit number of leads to enrich")
    parser.add_argument("--output-dir", default="output", help="Output directory")

    args = parser.parse_args()

    enricher = CompetitorEnrichment(output_dir=args.output_dir)

    if args.command == "enrich":
        result = enricher.enrich_leads(limit=args.limit)
        print(f"\n=== Enrichment Results ===")
        print(f"Total processed: {result['total_processed']}")
        print(f"Enriched: {result['enriched']}")
        print(f"Failed: {result['failed']}")

    elif args.command == "status":
        status = enricher.get_status()
        print(f"\n=== Enrichment Status ===")
        print(f"Total leads: {status['total_leads']}")
        print(f"Enriched with competitor: {status['enriched_with_competitor']}")
        print(f"Needs enrichment: {status['needs_enrichment']}")
        print(f"Enrichment %: {status['enrichment_percentage']}%")

    return 0


if __name__ == "__main__":
    exit(main())
