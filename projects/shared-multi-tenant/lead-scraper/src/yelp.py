"""
Yelp Fusion API integration for lead scraping.
Provides business data with reviews and contact info.
"""

import os
import time
import logging
import requests
from typing import Optional, List, Dict, Any, Generator

from .models import Lead
from .config import ScraperConfig, YELP_CATEGORIES

logger = logging.getLogger(__name__)


class YelpScraper:
    """
    Scraper using Yelp Fusion API.

    API Documentation: https://docs.developer.yelp.com/reference/v3_business_search

    Requires: YELP_API_KEY environment variable

    Free tier: 500 API calls per day
    """

    BASE_URL = "https://api.yelp.com/v3"
    BUSINESS_SEARCH_URL = f"{BASE_URL}/businesses/search"
    BUSINESS_DETAILS_URL = f"{BASE_URL}/businesses"

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.api_key = self.config.api.yelp_api_key or os.getenv("YELP_API_KEY", "")

        if not self.api_key:
            logger.warning("No Yelp API key found. Set YELP_API_KEY environment variable.")

        self.request_count = 0
        self.last_request_time = 0

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.rate_limit.delay_between_requests:
            time.sleep(self.config.rate_limit.delay_between_requests - elapsed)
        self.last_request_time = time.time()
        self.request_count += 1

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

    def _make_request(self, url: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make API request with rate limiting and error handling."""
        if not self.api_key:
            logger.error("No API key configured")
            return None

        self._rate_limit()

        for attempt in range(self.config.rate_limit.max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=30
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    logger.warning(f"Rate limit hit, waiting {self.config.rate_limit.retry_delay}s...")
                    time.sleep(self.config.rate_limit.retry_delay)
                elif response.status_code == 401:
                    logger.error("Invalid API key")
                    return None
                elif response.status_code == 400:
                    error_data = response.json()
                    logger.error(f"Bad request: {error_data.get('error', {}).get('description', 'Unknown')}")
                    return None
                else:
                    logger.warning(f"Unexpected status code: {response.status_code}")
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.rate_limit.max_retries - 1:
                    time.sleep(self.config.rate_limit.retry_delay)

        return None

    def search_businesses(
        self,
        term: str = "",
        location: str = "",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_meters: int = 40000,
        categories: str = "",
        limit: int = 50,
        offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Search for businesses.

        Args:
            term: Search term (e.g., "gym", "personal trainer")
            location: Location string (e.g., "Naples, FL")
            latitude: Search center latitude
            longitude: Search center longitude
            radius_meters: Search radius (max 40000m / ~25 miles)
            categories: Yelp category filter (comma-separated)
            limit: Number of results per page (max 50)
            offset: Pagination offset (max 1000)

        Returns:
            Search results dictionary
        """
        params = {
            "limit": min(limit, 50),
            "offset": min(offset, 1000)
        }

        if term:
            params["term"] = term
        if location:
            params["location"] = location
        if latitude and longitude:
            params["latitude"] = latitude
            params["longitude"] = longitude
        if radius_meters:
            params["radius"] = min(radius_meters, 40000)
        if categories:
            params["categories"] = categories

        return self._make_request(self.BUSINESS_SEARCH_URL, params)

    def get_business_details(self, business_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a business.

        Args:
            business_id: Yelp business ID

        Returns:
            Business details dictionary
        """
        url = f"{self.BUSINESS_DETAILS_URL}/{business_id}"
        return self._make_request(url)

    def search_all_results(
        self,
        term: str = "",
        location: str = "",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_meters: int = 40000,
        categories: str = "",
        max_results: int = 1000
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search and paginate through all results.

        Args:
            term: Search term
            location: Location string
            latitude: Search center latitude
            longitude: Search center longitude
            radius_meters: Search radius
            categories: Yelp category filter
            max_results: Maximum total results to fetch

        Yields:
            Business result dictionaries
        """
        offset = 0
        total_fetched = 0

        while offset < min(max_results, 1000):  # Yelp caps at 1000
            data = self.search_businesses(
                term=term,
                location=location,
                latitude=latitude,
                longitude=longitude,
                radius_meters=radius_meters,
                categories=categories,
                limit=50,
                offset=offset
            )

            if not data:
                break

            businesses = data.get("businesses", [])
            if not businesses:
                break

            for business in businesses:
                yield business
                total_fetched += 1
                if total_fetched >= max_results:
                    return

            # Check if there are more results
            total = data.get("total", 0)
            offset += len(businesses)
            if offset >= total or offset >= 1000:
                break

    def business_to_lead(self, business: Dict[str, Any], category: str = "") -> Lead:
        """
        Convert a Yelp business result to a Lead object.

        Args:
            business: Yelp business API result
            category: Business category being searched

        Returns:
            Lead object
        """
        # Parse location
        location = business.get("location", {})

        # Get coordinates
        coordinates = business.get("coordinates", {})

        # Identify pain points
        pain_points = self._identify_pain_points(business)

        # Parse categories
        yelp_categories = business.get("categories", [])
        subcategories = [cat.get("title", "") for cat in yelp_categories]

        lead = Lead(
            source="yelp",
            business_name=business.get("name", ""),
            phone=business.get("display_phone", business.get("phone", "")),
            website=business.get("url", ""),  # Yelp page URL
            address=", ".join(location.get("display_address", [])),
            city=location.get("city", ""),
            state=location.get("state", ""),
            zip_code=location.get("zip_code", ""),
            latitude=coordinates.get("latitude", 0),
            longitude=coordinates.get("longitude", 0),
            category=category,
            subcategories=subcategories,
            rating=business.get("rating", 0),
            review_count=business.get("review_count", 0),
            price_level=business.get("price", ""),
            pain_points=pain_points,
            notes=f"Distance: {business.get('distance', 'N/A')}m, Transactions: {business.get('transactions', [])}"
        )

        return lead

    def _identify_pain_points(self, business: Dict[str, Any]) -> List[str]:
        """Identify potential pain points from business data."""
        pain_points = []

        # No reviews
        review_count = business.get("review_count", 0)
        if review_count == 0:
            pain_points.append("no_reviews")
        elif review_count < 10:
            pain_points.append("few_reviews")

        # Low rating
        rating = business.get("rating", 0)
        if 0 < rating < 3.5:
            pain_points.append("low_rating")
        elif rating == 0:
            pain_points.append("no_rating")

        # No phone
        if not business.get("phone") and not business.get("display_phone"):
            pain_points.append("no_phone")

        # Closed
        if business.get("is_closed", False):
            pain_points.append("permanently_closed")

        # No transactions (booking, delivery, etc.)
        transactions = business.get("transactions", [])
        if not transactions:
            pain_points.append("no_online_transactions")

        return pain_points

    def scrape_category(
        self,
        category: str,
        location: str = "",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_meters: int = 40000,
        get_details: bool = False,
        max_results: int = 200
    ) -> Generator[Lead, None, None]:
        """
        Scrape leads for a specific business category.

        Args:
            category: Business category (e.g., "gym", "real estate agency")
            location: Location string
            latitude: Center latitude
            longitude: Center longitude
            radius_meters: Search radius in meters
            get_details: Whether to fetch detailed info (uses extra API calls)
            max_results: Maximum results to fetch

        Yields:
            Lead objects
        """
        # Get Yelp categories for this category
        yelp_cats = YELP_CATEGORIES.get(category.lower(), category.lower())

        seen_ids = set()

        # Method 1: Category search
        logger.info(f"Searching Yelp for category '{yelp_cats}'...")
        for business in self.search_all_results(
            categories=yelp_cats,
            location=location,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            max_results=max_results // 2
        ):
            biz_id = business.get("id")
            if biz_id in seen_ids:
                continue
            seen_ids.add(biz_id)

            if get_details:
                details = self.get_business_details(biz_id)
                if details:
                    business.update(details)

            yield self.business_to_lead(business, category)

        # Method 2: Term search for more results
        logger.info(f"Searching Yelp for term '{category}'...")
        for business in self.search_all_results(
            term=category,
            location=location,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            max_results=max_results // 2
        ):
            biz_id = business.get("id")
            if biz_id in seen_ids:
                continue
            seen_ids.add(biz_id)

            if get_details:
                details = self.get_business_details(biz_id)
                if details:
                    business.update(details)

            yield self.business_to_lead(business, category)

    def scrape_area(
        self,
        area_name: str,
        categories: List[str],
        location: str = "",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_meters: int = 40000,
        get_details: bool = False,
        progress_callback=None
    ) -> Generator[Lead, None, None]:
        """
        Scrape all categories in a given area.

        Args:
            area_name: Name of the area (for logging)
            categories: List of business categories
            location: Location string
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
            logger.info(f"[{area_name}] Yelp scraping {i+1}/{len(categories)}: {category}")
            category_count = 0

            for lead in self.scrape_category(
                category=category,
                location=location,
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

            logger.info(f"[{area_name}] Yelp found {category_count} leads for '{category}'")

        logger.info(f"[{area_name}] Yelp total leads: {total_leads}")
