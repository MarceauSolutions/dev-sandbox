"""
Configuration management for Lead Scraper.
Handles API keys, rate limits, and scraping settings.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass
class APIConfig:
    """API configuration settings."""
    google_places_api_key: str = ""
    yelp_api_key: str = ""
    apollo_api_key: str = ""
    hunter_api_key: str = ""  # Hunter.io for email verification

    @classmethod
    def from_env(cls) -> "APIConfig":
        """Load API keys from environment variables."""
        return cls(
            google_places_api_key=os.getenv("GOOGLE_PLACES_API_KEY", ""),
            yelp_api_key=os.getenv("YELP_API_KEY", ""),
            apollo_api_key=os.getenv("APOLLO_API_KEY", ""),
            hunter_api_key=os.getenv("HUNTER_API_KEY", "")
        )


@dataclass
class RateLimitConfig:
    """Rate limiting configuration to avoid bans."""
    requests_per_minute: int = 30
    delay_between_requests: float = 2.0  # seconds
    retry_delay: float = 60.0  # seconds after rate limit hit
    max_retries: int = 3


@dataclass
class SearchConfig:
    """Search parameters configuration."""
    # Default location: Naples, FL
    default_location: str = "Naples, FL"
    default_latitude: float = 26.1420
    default_longitude: float = -81.7948
    default_radius_meters: int = 25000  # ~15.5 miles

    # Business categories to target
    target_categories: List[str] = field(default_factory=lambda: [
        "gym",
        "fitness center",
        "personal trainer",
        "real estate agency",
        "moving company",
        "ecommerce",
        "retail store",
        "restaurant",
        "dental office",
        "medical spa",
        "salon",
        "auto repair",
        "hvac contractor",
        "plumber",
        "electrician",
        "landscaping",
        "cleaning service"
    ])

    # Surrounding areas to include
    surrounding_areas: List[dict] = field(default_factory=lambda: [
        {"name": "Naples, FL", "lat": 26.1420, "lng": -81.7948},
        {"name": "Fort Myers, FL", "lat": 26.6406, "lng": -81.8723},
        {"name": "Bonita Springs, FL", "lat": 26.3398, "lng": -81.7787},
        {"name": "Marco Island, FL", "lat": 25.9410, "lng": -81.7184},
        {"name": "Estero, FL", "lat": 26.4381, "lng": -81.8067},
        {"name": "Cape Coral, FL", "lat": 26.5629, "lng": -81.9495}
    ])


@dataclass
class OutputConfig:
    """Output file configuration."""
    output_dir: str = "output"
    csv_filename: str = "leads.csv"
    json_filename: str = "leads.json"
    progress_filename: str = "scrape_progress.json"
    optout_filename: str = "optout_list.json"


@dataclass
class ScraperConfig:
    """Main configuration container."""
    api: APIConfig = field(default_factory=APIConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "api": asdict(self.api),
            "rate_limit": asdict(self.rate_limit),
            "search": asdict(self.search),
            "output": asdict(self.output)
        }

    def save(self, filepath: str) -> None:
        """Save configuration to JSON file."""
        # Don't save API keys
        config_dict = self.to_dict()
        config_dict["api"] = {"google_places_api_key": "", "yelp_api_key": ""}

        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "ScraperConfig":
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        config = cls()
        config.api = APIConfig.from_env()  # Always load API keys from env

        if "rate_limit" in data:
            config.rate_limit = RateLimitConfig(**data["rate_limit"])
        if "search" in data:
            config.search = SearchConfig(**data["search"])
        if "output" in data:
            config.output = OutputConfig(**data["output"])

        return config


# Pain point indicators to look for
PAIN_POINT_INDICATORS = {
    "no_website": [
        "no website found",
        "website unavailable"
    ],
    "outdated_website": [
        "copyright 20[0-1][0-9]",  # Old copyright years
        "flash required",
        "not mobile friendly"
    ],
    "no_online_booking": [
        "call to schedule",
        "phone only",
        "no online booking"
    ],
    "limited_social_presence": [
        "no facebook",
        "no instagram",
        "inactive social"
    ],
    "no_reviews": [
        "0 reviews",
        "no reviews"
    ],
    "low_ratings": [
        "rating below 3.5"
    ]
}


# Google Places API types for different business categories
GOOGLE_PLACES_TYPES = {
    "gym": ["gym", "health"],
    "fitness center": ["gym", "health"],
    "personal trainer": ["gym", "health"],
    "real estate agency": ["real_estate_agency"],
    "moving company": ["moving_company"],
    "restaurant": ["restaurant", "cafe", "bakery"],
    "dental office": ["dentist"],
    "medical spa": ["spa", "beauty_salon"],
    "salon": ["hair_care", "beauty_salon"],
    "auto repair": ["car_repair"],
    "hvac contractor": ["general_contractor"],
    "plumber": ["plumber"],
    "electrician": ["electrician"],
    "landscaping": ["general_contractor"],
    "cleaning service": ["home_goods_store"],  # No direct type, use search
    "retail store": ["store", "shopping_mall"],
    "ecommerce": ["store"]  # Search-based
}


# Yelp API categories
YELP_CATEGORIES = {
    "gym": "gyms,fitness",
    "fitness center": "gyms,fitness",
    "personal trainer": "personaltrainers",
    "real estate agency": "realestate",
    "moving company": "movers",
    "restaurant": "restaurants",
    "dental office": "dentists",
    "medical spa": "medicalspa",
    "salon": "hair,beautysvc",
    "auto repair": "autorepair",
    "hvac contractor": "hvac",
    "plumber": "plumbing",
    "electrician": "electricians",
    "landscaping": "landscaping",
    "cleaning service": "homecleaning",
    "retail store": "shopping",
    "ecommerce": "shopping"
}
