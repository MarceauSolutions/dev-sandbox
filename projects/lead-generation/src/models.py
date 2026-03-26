"""
Data models for Lead Scraper.
Defines the Lead structure and related utilities.
"""

import json
import csv
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class Lead:
    """Represents a business lead."""
    # Core identification
    id: str = ""  # Generated hash for deduplication
    source: str = ""  # google_places, yelp, apollo, etc.

    # Business info
    business_name: str = ""
    owner_name: str = ""

    # Apollo B2B fields (decision maker info)
    first_name: str = ""  # Contact first name (Apollo)
    last_name: str = ""   # Contact last name (Apollo)
    title: str = ""       # Job title (Apollo)
    industry: str = ""    # Industry category (Apollo)

    # Contact info
    email: str = ""
    phone: str = ""
    website: str = ""

    # Social media
    facebook: str = ""
    instagram: str = ""
    linkedin: str = ""
    twitter: str = ""

    # Location
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    latitude: float = 0.0
    longitude: float = 0.0

    # Business details
    category: str = ""
    subcategories: List[str] = field(default_factory=list)
    rating: float = 0.0
    review_count: int = 0
    price_level: str = ""  # $, $$, $$$, $$$$

    # Competitor intelligence (for hyper-personalization)
    competitor_name: str = ""
    competitor_rating: float = 0.0
    competitor_review_count: int = 0
    competitor_website: str = ""

    # Pain points / opportunities
    pain_points: List[str] = field(default_factory=list)
    notes: str = ""

    # Metadata
    scraped_at: str = ""
    last_updated: str = ""

    def __post_init__(self):
        """Generate ID and timestamps after initialization."""
        if not self.id:
            self.id = self._generate_id()
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = self.scraped_at

    def _generate_id(self) -> str:
        """Generate unique ID based on business name and address."""
        unique_string = f"{self.business_name.lower()}{self.address.lower()}{self.phone}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Convert lead to dictionary."""
        return asdict(self)

    def to_csv_row(self) -> Dict[str, str]:
        """Convert lead to flat CSV row."""
        return {
            "id": self.id,
            "source": self.source,
            "business_name": self.business_name,
            "owner_name": self.owner_name,
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
            "facebook": self.facebook,
            "instagram": self.instagram,
            "linkedin": self.linkedin,
            "twitter": self.twitter,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "latitude": str(self.latitude),
            "longitude": str(self.longitude),
            "category": self.category,
            "subcategories": "|".join(self.subcategories),
            "rating": str(self.rating),
            "review_count": str(self.review_count),
            "price_level": self.price_level,
            "competitor_name": self.competitor_name,
            "competitor_rating": str(self.competitor_rating),
            "competitor_review_count": str(self.competitor_review_count),
            "competitor_website": self.competitor_website,
            "pain_points": "|".join(self.pain_points),
            "notes": self.notes,
            "scraped_at": self.scraped_at,
            "last_updated": self.last_updated
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Lead":
        """Create Lead from dictionary."""
        # Handle list fields that might be strings
        if isinstance(data.get("subcategories"), str):
            data["subcategories"] = data["subcategories"].split("|") if data["subcategories"] else []
        if isinstance(data.get("pain_points"), str):
            data["pain_points"] = data["pain_points"].split("|") if data["pain_points"] else []

        return cls(**data)

    def merge_with(self, other: "Lead") -> "Lead":
        """Merge this lead with another, preferring non-empty values."""
        merged_data = self.to_dict()
        other_data = other.to_dict()

        for key, value in other_data.items():
            if key in ["id", "scraped_at"]:
                continue

            current_value = merged_data.get(key)

            # Prefer non-empty values
            if not current_value and value:
                merged_data[key] = value
            # Merge lists
            elif isinstance(value, list) and isinstance(current_value, list):
                merged_data[key] = list(set(current_value + value))

        merged_data["last_updated"] = datetime.now().isoformat()
        merged_data["source"] = f"{self.source},{other.source}"

        return Lead.from_dict(merged_data)


class LeadCollection:
    """Collection of leads with deduplication and persistence."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.leads: Dict[str, Lead] = {}
        self.optout_list: set = set()

    def add(self, lead: Lead) -> bool:
        """
        Add a lead to the collection.
        Returns True if new lead, False if duplicate (merged).
        """
        # Check optout list
        if self._is_opted_out(lead):
            return False

        if lead.id in self.leads:
            # Merge with existing
            self.leads[lead.id] = self.leads[lead.id].merge_with(lead)
            return False
        else:
            self.leads[lead.id] = lead
            return True

    def _is_opted_out(self, lead: Lead) -> bool:
        """Check if lead has opted out."""
        identifiers = [
            lead.email.lower(),
            lead.phone,
            lead.business_name.lower()
        ]
        return any(identifier in self.optout_list for identifier in identifiers if identifier)

    def add_optout(self, identifier: str) -> None:
        """Add identifier to optout list."""
        self.optout_list.add(identifier.lower())

    def filter_by_category(self, category: str) -> List[Lead]:
        """Filter leads by category."""
        return [
            lead for lead in self.leads.values()
            if category.lower() in lead.category.lower()
            or any(category.lower() in sub.lower() for sub in lead.subcategories)
        ]

    def filter_by_location(self, city: str = "", state: str = "", zip_code: str = "") -> List[Lead]:
        """Filter leads by location."""
        results = []
        for lead in self.leads.values():
            if city and city.lower() not in lead.city.lower():
                continue
            if state and state.lower() != lead.state.lower():
                continue
            if zip_code and zip_code != lead.zip_code:
                continue
            results.append(lead)
        return results

    def filter_by_pain_points(self, pain_points: List[str]) -> List[Lead]:
        """Filter leads that have specific pain points."""
        results = []
        for lead in self.leads.values():
            if any(pp in lead.pain_points for pp in pain_points):
                results.append(lead)
        return results

    def filter_high_response_verticals(self) -> List[Lead]:
        """
        Filter leads to only high-response verticals.

        Research shows these verticals have 8-12% response rates:
        - Gyms / Fitness Centers
        - Salons / Spas / Beauty
        - Restaurants / Cafes

        Low-response verticals (excluded): Medical, Legal, Corporate
        """
        HIGH_RESPONSE_CATEGORIES = [
            "gym", "fitness", "crossfit", "yoga", "pilates", "martial arts",
            "salon", "spa", "beauty", "barber", "nail", "hair",
            "restaurant", "cafe", "coffee", "bar", "pizza", "food"
        ]

        results = []
        for lead in self.leads.values():
            category_lower = lead.category.lower()
            subcats_lower = [s.lower() for s in lead.subcategories]

            # Check if category or subcategory matches high-response vertical
            if any(keyword in category_lower for keyword in HIGH_RESPONSE_CATEGORIES):
                results.append(lead)
            elif any(any(keyword in sub for keyword in HIGH_RESPONSE_CATEGORIES) for sub in subcats_lower):
                results.append(lead)

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics."""
        categories = {}
        cities = {}
        sources = {}
        pain_point_counts = {}

        for lead in self.leads.values():
            categories[lead.category] = categories.get(lead.category, 0) + 1
            cities[lead.city] = cities.get(lead.city, 0) + 1

            for source in lead.source.split(","):
                sources[source] = sources.get(source, 0) + 1

            for pp in lead.pain_points:
                pain_point_counts[pp] = pain_point_counts.get(pp, 0) + 1

        return {
            "total_leads": len(self.leads),
            "by_category": categories,
            "by_city": cities,
            "by_source": sources,
            "by_pain_point": pain_point_counts,
            "with_email": sum(1 for l in self.leads.values() if l.email),
            "with_phone": sum(1 for l in self.leads.values() if l.phone),
            "with_website": sum(1 for l in self.leads.values() if l.website)
        }

    def save_csv(self, filename: str = "leads.csv") -> str:
        """Save leads to CSV file."""
        filepath = self.output_dir / filename

        if not self.leads:
            return str(filepath)

        fieldnames = list(next(iter(self.leads.values())).to_csv_row().keys())

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for lead in self.leads.values():
                writer.writerow(lead.to_csv_row())

        return str(filepath)

    def save_json(self, filename: str = "leads.json") -> str:
        """Save leads to JSON file."""
        filepath = self.output_dir / filename

        data = {
            "leads": [lead.to_dict() for lead in self.leads.values()],
            "statistics": self.get_statistics(),
            "exported_at": datetime.now().isoformat()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        return str(filepath)

    def save_optout_list(self, filename: str = "optout_list.json") -> str:
        """Save optout list to file."""
        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(list(self.optout_list), f, indent=2)

        return str(filepath)

    def load_optout_list(self, filename: str = "optout_list.json") -> None:
        """Load optout list from file."""
        filepath = self.output_dir / filename

        if filepath.exists():
            with open(filepath, 'r') as f:
                self.optout_list = set(json.load(f))

    def load_csv(self, filename: str = "leads.csv") -> int:
        """Load leads from CSV file. Returns count of leads loaded."""
        filepath = self.output_dir / filename

        if not filepath.exists():
            return 0

        count = 0
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert string numbers back
                row["latitude"] = float(row["latitude"]) if row["latitude"] else 0.0
                row["longitude"] = float(row["longitude"]) if row["longitude"] else 0.0
                row["rating"] = float(row["rating"]) if row["rating"] else 0.0
                row["review_count"] = int(row["review_count"]) if row["review_count"] else 0

                lead = Lead.from_dict(row)
                self.leads[lead.id] = lead
                count += 1

        return count

    def load_json(self, filename: str = "leads.json") -> int:
        """Load leads from JSON file. Returns count of leads loaded."""
        filepath = self.output_dir / filename

        if not filepath.exists():
            return 0

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        for lead_data in data.get("leads", []):
            lead = Lead.from_dict(lead_data)
            self.leads[lead.id] = lead
            count += 1

        return count
