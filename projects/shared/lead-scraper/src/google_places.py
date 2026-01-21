"""
Google Places API integration for lead scraping.
Uses the Places API (New) for business data.
"""

import os
import time
import json
import logging
import requests
from typing import Optional, List, Dict, Any, Generator
from pathlib import Path

from .models import Lead
from .config import ScraperConfig, GOOGLE_PLACES_TYPES
from .website_validator import is_real_business_website

logger = logging.getLogger(__name__)


class GooglePlacesScraper:
    """
    Scraper using Google Places API.

    API Documentation: https://developers.google.com/maps/documentation/places/web-service

    Requires: GOOGLE_PLACES_API_KEY environment variable

    Pricing (as of 2024):
    - Nearby Search: $32 per 1000 requests
    - Place Details: $17 per 1000 requests (Basic), $25 (Contact), $30 (Atmosphere)
    - Free tier: $200/month credit (~6000 basic searches)
    """

    BASE_URL = "https://maps.googleapis.com/maps/api/place"
    NEARBY_SEARCH_URL = f"{BASE_URL}/nearbysearch/json"
    PLACE_DETAILS_URL = f"{BASE_URL}/details/json"
    TEXT_SEARCH_URL = f"{BASE_URL}/textsearch/json"

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.api_key = self.config.api.google_places_api_key or os.getenv("GOOGLE_PLACES_API_KEY", "")

        if not self.api_key:
            logger.warning("No Google Places API key found. Set GOOGLE_PLACES_API_KEY environment variable.")

        self.request_count = 0
        self.last_request_time = 0

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.rate_limit.delay_between_requests:
            time.sleep(self.config.rate_limit.delay_between_requests - elapsed)
        self.last_request_time = time.time()
        self.request_count += 1

    def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make API request with rate limiting and error handling."""
        if not self.api_key:
            logger.error("No API key configured")
            return None

        self._rate_limit()
        params["key"] = self.api_key

        for attempt in range(self.config.rate_limit.max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                status = data.get("status")
                if status == "OK" or status == "ZERO_RESULTS":
                    return data
                elif status == "OVER_QUERY_LIMIT":
                    logger.warning(f"Rate limit hit, waiting {self.config.rate_limit.retry_delay}s...")
                    time.sleep(self.config.rate_limit.retry_delay)
                elif status == "REQUEST_DENIED":
                    logger.error(f"Request denied: {data.get('error_message', 'Unknown error')}")
                    return None
                elif status == "INVALID_REQUEST":
                    logger.error(f"Invalid request: {data.get('error_message', 'Unknown error')}")
                    return None
                else:
                    logger.warning(f"Unexpected status: {status}")
                    return data

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.rate_limit.max_retries - 1:
                    time.sleep(self.config.rate_limit.retry_delay)

        return None

    def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 5000,
        keyword: str = "",
        place_type: str = ""
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search for places near a location.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_meters: Search radius in meters (max 50000)
            keyword: Search keyword (e.g., "gym", "real estate")
            place_type: Google place type filter

        Yields:
            Place result dictionaries
        """
        params = {
            "location": f"{latitude},{longitude}",
            "radius": min(radius_meters, 50000),
        }

        if keyword:
            params["keyword"] = keyword
        if place_type:
            params["type"] = place_type

        next_page_token = None

        while True:
            if next_page_token:
                # Google requires a short delay before using page token
                time.sleep(2)
                params["pagetoken"] = next_page_token
            elif "pagetoken" in params:
                del params["pagetoken"]

            data = self._make_request(self.NEARBY_SEARCH_URL, params)

            if not data:
                break

            results = data.get("results", [])
            for place in results:
                yield place

            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break

    def text_search(
        self,
        query: str,
        location: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_meters: int = 50000
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search for places using text query.

        Args:
            query: Search query (e.g., "gyms in Naples FL")
            location: Location bias (e.g., "Naples, FL")
            latitude: Optional center latitude for location bias
            longitude: Optional center longitude for location bias
            radius_meters: Search radius in meters

        Yields:
            Place result dictionaries
        """
        params = {
            "query": query,
        }

        if latitude and longitude:
            params["location"] = f"{latitude},{longitude}"
            params["radius"] = min(radius_meters, 50000)

        next_page_token = None

        while True:
            if next_page_token:
                time.sleep(2)
                params["pagetoken"] = next_page_token
            elif "pagetoken" in params:
                del params["pagetoken"]

            data = self._make_request(self.TEXT_SEARCH_URL, params)

            if not data:
                break

            results = data.get("results", [])
            for place in results:
                yield place

            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break

    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a place.

        Args:
            place_id: Google Place ID

        Returns:
            Place details dictionary or None
        """
        params = {
            "place_id": place_id,
            "fields": ",".join([
                # Basic (no charge)
                "place_id", "name", "type", "business_status",
                # Contact ($3 per 1000)
                "formatted_phone_number", "international_phone_number",
                "opening_hours", "website",
                # Atmosphere ($5 per 1000)
                "price_level", "rating", "user_ratings_total",
                # Location
                "formatted_address", "geometry", "address_component",
                "vicinity"
            ])
        }

        data = self._make_request(self.PLACE_DETAILS_URL, params)

        if data and data.get("status") == "OK":
            return data.get("result")

        return None

    def place_to_lead(self, place: Dict[str, Any], category: str = "") -> Lead:
        """
        Convert a Google Place result to a Lead object.

        Args:
            place: Google Place API result
            category: Business category being searched

        Returns:
            Lead object
        """
        # Parse address components
        address_parts = self._parse_address(place)

        # Identify pain points
        pain_points = self._identify_pain_points(place)

        # Format phone number
        phone = place.get("formatted_phone_number", "")
        if not phone:
            phone = place.get("international_phone_number", "")

        lead = Lead(
            source="google_places",
            business_name=place.get("name", ""),
            phone=phone,
            website=place.get("website", ""),
            address=place.get("formatted_address", place.get("vicinity", "")),
            city=address_parts.get("city", ""),
            state=address_parts.get("state", ""),
            zip_code=address_parts.get("zip_code", ""),
            latitude=place.get("geometry", {}).get("location", {}).get("lat", 0),
            longitude=place.get("geometry", {}).get("location", {}).get("lng", 0),
            category=category,
            subcategories=place.get("types", []),
            rating=place.get("rating", 0),
            review_count=place.get("user_ratings_total", 0),
            price_level=self._format_price_level(place.get("price_level")),
            pain_points=pain_points
        )

        return lead

    def _parse_address(self, place: Dict[str, Any]) -> Dict[str, str]:
        """Parse address components from place data."""
        result = {"city": "", "state": "", "zip_code": ""}

        components = place.get("address_components", [])
        for component in components:
            types = component.get("types", [])
            if "locality" in types:
                result["city"] = component.get("long_name", "")
            elif "administrative_area_level_1" in types:
                result["state"] = component.get("short_name", "")
            elif "postal_code" in types:
                result["zip_code"] = component.get("long_name", "")

        # Fallback: try to parse from formatted address
        if not result["city"] or not result["state"]:
            formatted = place.get("formatted_address", "")
            # Try pattern: "123 Main St, Naples, FL 34102, USA"
            parts = formatted.split(", ")
            if len(parts) >= 3:
                if not result["city"]:
                    result["city"] = parts[-3] if len(parts) >= 3 else ""
                if not result["state"]:
                    state_zip = parts[-2] if len(parts) >= 2 else ""
                    state_parts = state_zip.split(" ")
                    if state_parts:
                        result["state"] = state_parts[0]
                        if len(state_parts) > 1 and not result["zip_code"]:
                            result["zip_code"] = state_parts[1]

        return result

    def _format_price_level(self, price_level: Optional[int]) -> str:
        """Convert price level integer to $ symbols."""
        if price_level is None:
            return ""
        return "$" * price_level if 0 < price_level <= 4 else ""

    def _identify_pain_points(self, place: Dict[str, Any]) -> List[str]:
        """Identify potential pain points from place data."""
        pain_points = []

        # Website validation using website_validator.py
        website_url = place.get("website", "")
        is_real, reason = is_real_business_website(website_url)

        if not website_url:
            # Truly no website at all
            pain_points.append("no_website")
        elif not is_real:
            # Has URL but it's just an aggregator (Yelp, Google Maps, Facebook)
            pain_points.append("aggregator_only")
            logger.debug(f"{place.get('name')}: {reason}")

        # No or few reviews
        review_count = place.get("user_ratings_total", 0)
        if review_count == 0:
            pain_points.append("no_reviews")
        elif review_count < 10:
            pain_points.append("few_reviews")

        # Low rating
        rating = place.get("rating", 0)
        if 0 < rating < 3.5:
            pain_points.append("low_rating")
        elif rating == 0:
            pain_points.append("no_rating")

        # Business status issues
        status = place.get("business_status", "OPERATIONAL")
        if status != "OPERATIONAL":
            pain_points.append(f"status_{status.lower()}")

        return pain_points

    def scrape_category(
        self,
        category: str,
        latitude: float,
        longitude: float,
        radius_meters: int = 25000,
        get_details: bool = True
    ) -> Generator[Lead, None, None]:
        """
        Scrape leads for a specific business category.

        Args:
            category: Business category (e.g., "gym", "real estate agency")
            latitude: Center latitude
            longitude: Center longitude
            radius_meters: Search radius in meters
            get_details: Whether to fetch detailed info for each place

        Yields:
            Lead objects
        """
        # Get Google place types for this category
        place_types = GOOGLE_PLACES_TYPES.get(category.lower(), [])

        seen_place_ids = set()

        # Method 1: Nearby search with keyword
        logger.info(f"Searching nearby for '{category}'...")
        for place in self.search_nearby(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            keyword=category
        ):
            place_id = place.get("place_id")
            if place_id in seen_place_ids:
                continue
            seen_place_ids.add(place_id)

            if get_details:
                details = self.get_place_details(place_id)
                if details:
                    place.update(details)

            yield self.place_to_lead(place, category)

        # Method 2: Text search for more results
        logger.info(f"Text searching for '{category}'...")
        query = f"{category} near {latitude},{longitude}"
        for place in self.text_search(
            query=query,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters
        ):
            place_id = place.get("place_id")
            if place_id in seen_place_ids:
                continue
            seen_place_ids.add(place_id)

            if get_details:
                details = self.get_place_details(place_id)
                if details:
                    place.update(details)

            yield self.place_to_lead(place, category)

        # Method 3: Search by place types
        for place_type in place_types:
            logger.info(f"Searching by type '{place_type}'...")
            for place in self.search_nearby(
                latitude=latitude,
                longitude=longitude,
                radius_meters=radius_meters,
                place_type=place_type
            ):
                place_id = place.get("place_id")
                if place_id in seen_place_ids:
                    continue
                seen_place_ids.add(place_id)

                if get_details:
                    details = self.get_place_details(place_id)
                    if details:
                        place.update(details)

                yield self.place_to_lead(place, category)

    def scrape_area(
        self,
        area_name: str,
        categories: List[str],
        latitude: float,
        longitude: float,
        radius_meters: int = 25000,
        get_details: bool = True,
        progress_callback=None
    ) -> Generator[Lead, None, None]:
        """
        Scrape all categories in a given area.

        Args:
            area_name: Name of the area (for logging)
            categories: List of business categories
            latitude: Center latitude
            longitude: Center longitude
            radius_meters: Search radius in meters
            get_details: Whether to fetch detailed info
            progress_callback: Optional callback(category, lead_count)

        Yields:
            Lead objects
        """
        total_leads = 0

        for i, category in enumerate(categories):
            logger.info(f"[{area_name}] Scraping category {i+1}/{len(categories)}: {category}")
            category_count = 0

            for lead in self.scrape_category(
                category=category,
                latitude=latitude,
                longitude=longitude,
                radius_meters=radius_meters,
                get_details=get_details
            ):
                yield lead
                category_count += 1
                total_leads += 1

            if progress_callback:
                progress_callback(category, category_count)

            logger.info(f"[{area_name}] Found {category_count} leads for '{category}'")

        logger.info(f"[{area_name}] Total leads found: {total_leads}")
