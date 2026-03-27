#!/usr/bin/env python3
"""
Restaurant Finder - Find healthy, reasonably priced restaurants nearby.

Uses Google Places API and Yelp API to find restaurants matching criteria.

Usage:
    python -m src.restaurant_finder --location "3228 Sassafras Way, Pittsburgh PA 15201"
    python -m src.restaurant_finder --location "Naples, FL" --cuisine healthy --budget moderate
    python -m src.restaurant_finder --lat 40.4774 --lng -79.9619 --open-now
"""

import os
import sys
import argparse
import webbrowser
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

import requests
import anthropic


@dataclass
class Restaurant:
    """Restaurant data."""
    name: str
    address: str
    rating: float
    price_level: int  # 1-4 ($ to $$$$)
    cuisine_types: list[str]
    distance_meters: float
    is_open: bool
    google_place_id: str
    order_url: Optional[str] = None
    phone: Optional[str] = None

    @property
    def price_display(self) -> str:
        return "$" * self.price_level if self.price_level else "?"

    @property
    def distance_display(self) -> str:
        if self.distance_meters < 1000:
            return f"{int(self.distance_meters)}m"
        return f"{self.distance_meters/1000:.1f}km"


class RestaurantFinder:
    """Find restaurants using Google Places API."""

    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        self.yelp_api_key = os.getenv("YELP_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        if not self.google_api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY not set in .env")

    def geocode_address(self, address: str) -> tuple[float, float]:
        """Convert address to lat/lng coordinates."""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": self.google_api_key
        }

        response = requests.get(url, params=params)
        data = response.json()

        if data["status"] != "OK" or not data["results"]:
            raise ValueError(f"Could not geocode address: {address}")

        location = data["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]

    def search_nearby(
        self,
        lat: float,
        lng: float,
        cuisine: str = "healthy",
        budget: str = "moderate",
        radius_meters: int = 3000,
        open_now: bool = True
    ) -> list[Restaurant]:
        """Search for restaurants near a location."""

        # Build search query
        keyword = self._build_keyword(cuisine, budget)

        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius_meters,
            "type": "restaurant",
            "keyword": keyword,
            "key": self.google_api_key
        }

        if open_now:
            params["opennow"] = "true"

        response = requests.get(url, params=params)
        data = response.json()

        if data["status"] not in ["OK", "ZERO_RESULTS"]:
            raise ValueError(f"Google Places API error: {data.get('status')}")

        restaurants = []
        for place in data.get("results", [])[:10]:  # Top 10
            # Filter by price level for budget
            price_level = place.get("price_level", 2)
            if budget == "cheap" and price_level > 2:
                continue
            elif budget == "moderate" and price_level > 3:
                continue

            restaurant = Restaurant(
                name=place["name"],
                address=place.get("vicinity", ""),
                rating=place.get("rating", 0),
                price_level=price_level,
                cuisine_types=place.get("types", []),
                distance_meters=self._calculate_distance(
                    lat, lng,
                    place["geometry"]["location"]["lat"],
                    place["geometry"]["location"]["lng"]
                ),
                is_open=place.get("opening_hours", {}).get("open_now", False),
                google_place_id=place["place_id"]
            )
            restaurants.append(restaurant)

        # Sort by rating
        restaurants.sort(key=lambda r: r.rating, reverse=True)
        return restaurants

    def get_order_url(self, place_id: str) -> Optional[str]:
        """Get ordering URL for a restaurant."""
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "website,url,formatted_phone_number",
            "key": self.google_api_key
        }

        response = requests.get(url, params=params)
        data = response.json()

        if data["status"] == "OK":
            result = data.get("result", {})
            # Prefer website, fallback to Google Maps URL
            return result.get("website") or result.get("url")
        return None

    def _build_keyword(self, cuisine: str, budget: str) -> str:
        """Build search keyword from criteria."""
        keywords = []

        if cuisine:
            cuisine_map = {
                "healthy": "healthy salad bowl",
                "asian": "asian",
                "mexican": "mexican",
                "italian": "italian",
                "american": "american",
                "mediterranean": "mediterranean healthy",
                "vegan": "vegan vegetarian",
                "fast": "fast casual"
            }
            keywords.append(cuisine_map.get(cuisine.lower(), cuisine))

        if budget == "cheap":
            keywords.append("affordable")

        return " ".join(keywords)

    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters."""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371000  # Earth radius in meters

        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def rank_with_ai(self, restaurants: list[Restaurant], preferences: str = "healthy and affordable") -> list[Restaurant]:
        """Use Claude to rank restaurants based on preferences."""
        if not self.anthropic_api_key or not restaurants:
            return restaurants

        client = anthropic.Anthropic(api_key=self.anthropic_api_key)

        # Build restaurant list for Claude
        restaurant_list = "\n".join([
            f"{i+1}. {r.name} - {r.price_display} - {r.rating}⭐ - {r.distance_display} - Types: {', '.join(r.cuisine_types[:3])}"
            for i, r in enumerate(restaurants)
        ])

        prompt = f"""Given these restaurants and the user's preference for "{preferences}", rank them from best to worst match.

Restaurants:
{restaurant_list}

Return ONLY the numbers in order of best match, comma-separated. Example: 3,1,5,2,4"""

        try:
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )

            ranking = response.content[0].text.strip()
            indices = [int(x.strip()) - 1 for x in ranking.split(",") if x.strip().isdigit()]

            ranked = []
            for idx in indices:
                if 0 <= idx < len(restaurants):
                    ranked.append(restaurants[idx])

            # Add any we missed
            for r in restaurants:
                if r not in ranked:
                    ranked.append(r)

            return ranked
        except Exception as e:
            print(f"AI ranking failed: {e}")
            return restaurants


def main():
    parser = argparse.ArgumentParser(description="Find healthy, affordable restaurants nearby")
    parser.add_argument("--location", "-l", help="Address or location to search near")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lng", type=float, help="Longitude")
    parser.add_argument("--cuisine", "-c", default="healthy", help="Cuisine type (healthy, asian, mexican, etc.)")
    parser.add_argument("--budget", "-b", default="moderate", choices=["cheap", "moderate", "expensive"], help="Budget level")
    parser.add_argument("--radius", "-r", type=int, default=3000, help="Search radius in meters")
    parser.add_argument("--open-now", action="store_true", default=True, help="Only show open restaurants")
    parser.add_argument("--open-url", action="store_true", help="Open the top result's ordering page")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Validate inputs
    if not args.location and (args.lat is None or args.lng is None):
        parser.error("Either --location or both --lat and --lng are required")

    finder = RestaurantFinder()

    # Get coordinates
    if args.location:
        print(f"📍 Geocoding: {args.location}")
        lat, lng = finder.geocode_address(args.location)
        print(f"   Found: {lat}, {lng}")
    else:
        lat, lng = args.lat, args.lng

    # Search
    print(f"\n🔍 Searching for {args.cuisine} restaurants within {args.radius}m...")
    restaurants = finder.search_nearby(
        lat, lng,
        cuisine=args.cuisine,
        budget=args.budget,
        radius_meters=args.radius,
        open_now=args.open_now
    )

    if not restaurants:
        print("❌ No restaurants found matching your criteria")
        return

    # Rank with AI
    print(f"🤖 AI-ranking {len(restaurants)} results for 'healthy and affordable'...")
    restaurants = finder.rank_with_ai(restaurants, f"{args.cuisine} and {args.budget}")

    # Output
    if args.json:
        output = [
            {
                "name": r.name,
                "address": r.address,
                "rating": r.rating,
                "price": r.price_display,
                "distance": r.distance_display,
                "is_open": r.is_open,
                "place_id": r.google_place_id
            }
            for r in restaurants
        ]
        print(json.dumps(output, indent=2))
    else:
        print(f"\n✅ Found {len(restaurants)} restaurants:\n")
        for i, r in enumerate(restaurants[:5], 1):
            status = "🟢 Open" if r.is_open else "🔴 Closed"
            print(f"{i}. {r.name}")
            print(f"   {r.price_display} | {r.rating}⭐ | {r.distance_display} | {status}")
            print(f"   {r.address}")
            print()

    # Open URL if requested
    if args.open_url and restaurants:
        top = restaurants[0]
        print(f"🌐 Getting order URL for {top.name}...")
        url = finder.get_order_url(top.google_place_id)
        if url:
            print(f"   Opening: {url}")
            webbrowser.open(url)
        else:
            # Fallback to Google Maps
            maps_url = f"https://www.google.com/maps/place/?q=place_id:{top.google_place_id}"
            print(f"   Opening Google Maps: {maps_url}")
            webbrowser.open(maps_url)


if __name__ == "__main__":
    main()
