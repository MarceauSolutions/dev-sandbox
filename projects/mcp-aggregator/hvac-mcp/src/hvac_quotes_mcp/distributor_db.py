"""
HVAC Distributor Database

Static database of HVAC equipment distributors.
Similar to rate_cards.py for rideshare - contains provider data.

For MVP, this uses in-memory data. Production would use the platform database.
"""

from typing import List, Optional, Dict, Any
from .models import Distributor


class DistributorDB:
    """
    Database of HVAC equipment distributors.

    Provides:
    - Distributor lookup by region, brand, equipment type
    - Rating-based sorting
    - Active/inactive filtering
    """

    def __init__(self):
        self._distributors: Dict[str, Distributor] = {}
        self._load_distributors()

    def _load_distributors(self):
        """Load test distributors for MVP"""
        test_distributors = [
            Distributor(
                id='dist-ferguson-fl',
                name='Ferguson HVAC Supply - Florida',
                email_address='rfq@ferguson-hvac-fl.example.com',
                supported_regions=['FL', 'GA'],
                supported_brands=['Carrier', 'Bryant', 'Payne'],
                equipment_types=['ac_unit', 'furnace', 'heat_pump', 'air_handler', 'condenser'],
                avg_response_hours=24,
                rating=4.8,
                contact_name='Mike Johnson',
                phone='(239) 555-0101'
            ),
            Distributor(
                id='dist-johnstone-southeast',
                name='Johnstone Supply - Southeast',
                email_address='quotes@johnstone-se.example.com',
                supported_regions=['FL', 'GA', 'AL', 'SC', 'NC'],
                supported_brands=['Trane', 'American Standard', 'Ameristar'],
                equipment_types=['ac_unit', 'furnace', 'heat_pump', 'air_handler', 'mini_split'],
                avg_response_hours=18,
                rating=4.6,
                contact_name='Sarah Williams',
                phone='(404) 555-0202'
            ),
            Distributor(
                id='dist-baker-florida',
                name='Baker Distributing - Florida',
                email_address='sales@baker-fl.example.com',
                supported_regions=['FL'],
                supported_brands=['Lennox', 'Goodman', 'Amana'],
                equipment_types=['ac_unit', 'furnace', 'heat_pump', 'evaporator_coil', 'condenser'],
                avg_response_hours=12,
                rating=4.5,
                contact_name='Tom Baker',
                phone='(305) 555-0303'
            ),
            Distributor(
                id='dist-gemaire-gulf',
                name='Gemaire Distributors - Gulf Coast',
                email_address='rfq@gemaire-gulf.example.com',
                supported_regions=['FL', 'AL', 'MS', 'LA', 'TX'],
                supported_brands=['Rheem', 'Ruud', 'Goodman'],
                equipment_types=['ac_unit', 'furnace', 'heat_pump', 'air_handler', 'thermostat'],
                avg_response_hours=24,
                rating=4.4,
                contact_name='Carlos Rodriguez',
                phone='(813) 555-0404'
            ),
            Distributor(
                id='dist-winsupply-naples',
                name='WinSupply - Naples',
                email_address='orders@winsupply-naples.example.com',
                supported_regions=['FL'],
                supported_brands=['Carrier', 'Trane', 'Lennox', 'Rheem', 'Goodman'],
                equipment_types=['ac_unit', 'furnace', 'heat_pump', 'air_handler', 'condenser', 'mini_split', 'thermostat'],
                avg_response_hours=8,
                rating=4.9,
                contact_name='Jennifer Martinez',
                phone='(239) 555-0505'
            ),
            Distributor(
                id='dist-united-refrigeration',
                name='United Refrigeration - Southeast',
                email_address='sales@unitedrefrig-se.example.com',
                supported_regions=['FL', 'GA', 'SC'],
                supported_brands=['Copeland', 'Bitzer', 'Emerson'],
                equipment_types=['condenser', 'evaporator_coil', 'other'],
                avg_response_hours=36,
                rating=4.3,
                contact_name='Dave Wilson',
                phone='(770) 555-0606'
            ),
            Distributor(
                id='dist-carrier-enterprise',
                name='Carrier Enterprise - Florida',
                email_address='commercial@carrier-fl.example.com',
                supported_regions=['FL'],
                supported_brands=['Carrier', 'Bryant', 'Payne', 'Day & Night'],
                equipment_types=['ac_unit', 'furnace', 'heat_pump', 'air_handler', 'condenser', 'mini_split'],
                avg_response_hours=16,
                rating=4.7,
                contact_name='Robert Chen',
                phone='(407) 555-0707'
            ),
            Distributor(
                id='dist-trane-supply',
                name='Trane Supply - Southeast',
                email_address='quotes@tranesupply-se.example.com',
                supported_regions=['FL', 'GA', 'AL', 'TN'],
                supported_brands=['Trane', 'American Standard'],
                equipment_types=['ac_unit', 'furnace', 'heat_pump', 'air_handler', 'thermostat'],
                avg_response_hours=20,
                rating=4.6,
                contact_name='Lisa Thompson',
                phone='(615) 555-0808'
            ),
            Distributor(
                id='dist-lennox-florida',
                name='Lennox Industries - Florida Direct',
                email_address='direct@lennox-fl.example.com',
                supported_regions=['FL'],
                supported_brands=['Lennox'],
                equipment_types=['ac_unit', 'furnace', 'heat_pump', 'air_handler'],
                avg_response_hours=48,
                rating=4.8,
                contact_name='Mark Stevens',
                phone='(972) 555-0909'
            ),
            Distributor(
                id='dist-mitsubishi-comfort',
                name='Mitsubishi Electric Comfort Systems',
                email_address='orders@mitsubishi-comfort.example.com',
                supported_regions=['FL', 'GA', 'AL', 'SC', 'NC', 'TN'],
                supported_brands=['Mitsubishi Electric'],
                equipment_types=['mini_split', 'heat_pump', 'air_handler'],
                avg_response_hours=24,
                rating=4.9,
                is_active=True,
                contact_name='Kevin Tanaka',
                phone='(714) 555-1010'
            )
        ]

        for dist in test_distributors:
            self._distributors[dist.id] = dist

    def get_distributor(self, distributor_id: str) -> Optional[Distributor]:
        """Get a distributor by ID"""
        return self._distributors.get(distributor_id)

    def get_all_distributors(self, active_only: bool = True) -> List[Distributor]:
        """Get all distributors"""
        distributors = list(self._distributors.values())
        if active_only:
            distributors = [d for d in distributors if d.is_active]
        return sorted(distributors, key=lambda d: d.rating, reverse=True)

    def find_distributors(
        self,
        region: Optional[str] = None,
        brand: Optional[str] = None,
        equipment_type: Optional[str] = None,
        min_rating: float = 0.0,
        active_only: bool = True
    ) -> List[Distributor]:
        """
        Find distributors matching criteria.

        Args:
            region: State code (e.g., 'FL', 'GA')
            brand: Equipment brand (e.g., 'Carrier', 'Trane')
            equipment_type: Equipment type (e.g., 'ac_unit', 'furnace')
            min_rating: Minimum rating threshold
            active_only: Only return active distributors

        Returns:
            List of matching distributors, sorted by rating (descending)
        """
        matches = []

        for dist in self._distributors.values():
            # Filter by active status
            if active_only and not dist.is_active:
                continue

            # Filter by rating
            if dist.rating < min_rating:
                continue

            # Filter by region
            if region and region not in dist.supported_regions:
                continue

            # Filter by brand
            if brand and brand not in dist.supported_brands:
                continue

            # Filter by equipment type
            if equipment_type and equipment_type not in dist.equipment_types:
                continue

            matches.append(dist)

        # Sort by rating (highest first)
        return sorted(matches, key=lambda d: d.rating, reverse=True)

    def get_distributors_for_rfq(
        self,
        delivery_address: str,
        equipment_type: str,
        brand_preference: Optional[str] = None,
        max_distributors: int = 5
    ) -> List[Distributor]:
        """
        Get best distributors for an RFQ.

        Extracts region from address and finds matching distributors.

        Args:
            delivery_address: Full delivery address
            equipment_type: Type of equipment needed
            brand_preference: Optional preferred brand
            max_distributors: Maximum number of distributors to return

        Returns:
            List of best matching distributors
        """
        # Extract state from address (simple heuristic)
        region = self._extract_region(delivery_address)

        # Find matching distributors
        matches = self.find_distributors(
            region=region,
            brand=brand_preference,
            equipment_type=equipment_type
        )

        # Return top N
        return matches[:max_distributors]

    def _extract_region(self, address: str) -> Optional[str]:
        """
        Extract state code from address.

        Simple heuristic - looks for two-letter state codes.
        In production, would use geocoding API.
        """
        # Common state abbreviations
        states = {
            'FL', 'GA', 'AL', 'SC', 'NC', 'TN', 'MS', 'LA', 'TX',
            'CA', 'NY', 'NJ', 'PA', 'OH', 'IL', 'MI', 'VA', 'MA'
        }

        # Also check for full state names
        state_names = {
            'florida': 'FL',
            'georgia': 'GA',
            'alabama': 'AL',
            'south carolina': 'SC',
            'north carolina': 'NC',
            'tennessee': 'TN',
            'mississippi': 'MS',
            'louisiana': 'LA',
            'texas': 'TX',
            'california': 'CA',
            'new york': 'NY',
            'new jersey': 'NJ',
            'pennsylvania': 'PA',
            'ohio': 'OH',
            'illinois': 'IL',
            'michigan': 'MI',
            'virginia': 'VA',
            'massachusetts': 'MA'
        }

        address_upper = address.upper()
        address_lower = address.lower()

        # Check for state abbreviations
        for state in states:
            if f' {state} ' in address_upper or address_upper.endswith(f' {state}'):
                return state
            # Also check with comma (e.g., "Naples, FL")
            if f', {state}' in address_upper:
                return state

        # Check for full state names
        for name, abbrev in state_names.items():
            if name in address_lower:
                return abbrev

        # Default to FL for Naples-area testing
        if 'naples' in address_lower:
            return 'FL'

        return None

    def add_distributor(self, distributor: Distributor) -> None:
        """Add a new distributor"""
        self._distributors[distributor.id] = distributor

    def update_distributor(self, distributor_id: str, **updates) -> bool:
        """Update distributor fields"""
        if distributor_id not in self._distributors:
            return False

        dist = self._distributors[distributor_id]
        for key, value in updates.items():
            if hasattr(dist, key):
                setattr(dist, key, value)

        return True

    def deactivate_distributor(self, distributor_id: str) -> bool:
        """Mark a distributor as inactive"""
        return self.update_distributor(distributor_id, is_active=False)


# Singleton instance for easy access
_db_instance: Optional[DistributorDB] = None


def get_distributor_db() -> DistributorDB:
    """Get the singleton DistributorDB instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DistributorDB()
    return _db_instance
