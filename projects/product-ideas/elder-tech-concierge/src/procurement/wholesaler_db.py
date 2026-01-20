"""
Elder Tech Procurement - Wholesaler Database

Manages device wholesaler information for iPad/tablet procurement.
Based on the HVAC distributor_db.py pattern.

Target Wholesalers (per user request):
- Today's Closeout (todayscloseout.com)
- iPad Distributors (various)
- WeSellCellular (wesellcellular.com)
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from models import Wholesaler, DeviceType, DeviceCondition

logger = logging.getLogger(__name__)


# Pre-populated wholesaler database
# Based on user's requested suppliers + additional research
WHOLESALER_DATA = [
    {
        'id': 'todays-closeout',
        'name': "Today's Closeout",
        'email_address': None,  # Contact form only
        'contact_form_url': 'https://www.todayscloseout.com/pages/contact-us',
        'website': 'https://www.todayscloseout.com',
        'supported_devices': ['ipad', 'ipad_pro', 'ipad_air', 'ipad_mini', 'android_tablet'],
        'conditions_available': ['new', 'refurbished_a', 'refurbished_b'],
        'min_order_quantity': 1,
        'avg_response_hours': 24,
        'rating': 4.2,
        'notes': 'Large liquidation/closeout supplier. Good for bulk refurbished. Based in USA.'
    },
    {
        'id': 'wesellcellular',
        'name': 'WeSellCellular',
        'email_address': 'customercare@wesellcellular.com',  # Verified contact
        'contact_form_url': 'https://www.wesellcellular.com/tell-us-more/',
        'website': 'https://www.wesellcellular.com',
        'phone': '+1 (516) 334-6400',
        'supported_devices': ['ipad', 'ipad_pro', 'ipad_air', 'ipad_mini'],
        'conditions_available': ['refurbished_a', 'refurbished_b'],
        'min_order_quantity': 5,
        'avg_response_hours': 12,
        'rating': 4.5,
        'notes': 'Wholesale refurbished Apple devices. Good reputation. Fast response. Owned by ITOCHU.'
    },
    {
        'id': 'mac-of-all-trades',
        'name': 'Mac of All Trades',
        'email_address': None,  # No direct email - use support system
        'contact_form_url': 'https://macofalltrades.reamaze.com/contact',
        'website': 'https://www.macofalltrades.com',
        'supported_devices': ['ipad', 'ipad_pro', 'ipad_air', 'ipad_mini'],
        'conditions_available': ['refurbished_a', 'refurbished_b'],
        'min_order_quantity': 1,
        'avg_response_hours': 24,
        'rating': 4.3,
        'notes': 'Established Apple reseller. Business accounts available. Use Reamaze support for inquiries.'
    },
    {
        'id': 'gazelle-business',
        'name': 'Gazelle Business',
        'email_address': 'gazellesupport@ecoatm.com',  # Verified - or customercare@gazelle.com
        'contact_form_url': 'https://buy.gazelle.com/pages/help-bulk',
        'website': 'https://buy.gazelle.com',
        'phone': '1-800-GAZELLE (800-429-3553)',
        'supported_devices': ['ipad', 'ipad_pro', 'ipad_air'],
        'conditions_available': ['refurbished_a', 'refurbished_b', 'refurbished_c'],
        'min_order_quantity': 10,
        'avg_response_hours': 36,
        'rating': 4.0,
        'notes': 'Large certified refurbisher. Volume discounts for 10+ units. 500+ units use wholesale page.'
    },
    {
        'id': 'back-market-pro',
        'name': 'Back Market Pro',
        'email_address': None,
        'contact_form_url': 'https://www.backmarket.com/en-us/c/pro',
        'website': 'https://www.backmarket.com',
        'supported_devices': ['ipad', 'ipad_pro', 'ipad_air', 'ipad_mini', 'android_tablet'],
        'conditions_available': ['refurbished_a', 'refurbished_b'],
        'min_order_quantity': 5,
        'avg_response_hours': 24,
        'rating': 4.4,
        'notes': 'Large refurbished marketplace. Pro accounts for business buyers.'
    },
    {
        'id': 'reebelo-business',
        'name': 'Reebelo Business',
        'email_address': None,  # Use contact form - email not verified
        'contact_form_url': 'https://www.reebelo.com/business',
        'website': 'https://www.reebelo.com',
        'supported_devices': ['ipad', 'ipad_pro', 'ipad_air', 'ipad_mini'],
        'conditions_available': ['refurbished_a', 'refurbished_b'],
        'min_order_quantity': 3,
        'avg_response_hours': 24,
        'rating': 4.2,
        'notes': 'Sustainable tech focus. Good warranty options. Use contact form for business inquiries.'
    },
    {
        'id': 'apple-refurbished',
        'name': 'Apple Certified Refurbished',
        'email_address': None,  # No direct contact, online only
        'contact_form_url': None,
        'website': 'https://www.apple.com/shop/refurbished/ipad',
        'supported_devices': ['ipad', 'ipad_pro', 'ipad_air', 'ipad_mini'],
        'conditions_available': ['refurbished_a'],  # Apple quality
        'min_order_quantity': 1,
        'avg_response_hours': 0,  # Online pricing, instant
        'rating': 5.0,
        'notes': 'Official Apple refurbished. ~15% off retail. 1-year warranty. No bulk discounts.'
    },
    {
        'id': 'wholesale-gadget-parts',
        'name': 'Wholesale Gadget Parts',
        'email_address': None,  # Email not verified - use contact form
        'contact_form_url': 'https://wholesalegadgetparts.com/contact/',
        'website': 'https://wholesalegadgetparts.com',
        'supported_devices': ['ipad', 'ipad_pro', 'ipad_air', 'android_tablet'],
        'conditions_available': ['new', 'refurbished_a', 'refurbished_b'],
        'min_order_quantity': 5,
        'avg_response_hours': 24,
        'rating': 3.8,
        'notes': 'Wholesale parts and devices. Good for accessories bundling. Use contact form.'
    },
]


class WholesalerDB:
    """
    Database of device wholesalers for procurement.

    Provides:
    - Search/filter wholesalers by device type, condition
    - Get wholesalers for a specific inquiry
    - CRUD operations for wholesaler management
    """

    def __init__(self, data_file: Optional[str] = None):
        """
        Initialize wholesaler database.

        Args:
            data_file: Optional JSON file to load/save wholesalers
        """
        self.data_file = data_file
        self.wholesalers: Dict[str, Wholesaler] = {}

        # Load from file or use defaults
        if data_file and Path(data_file).exists():
            self._load_from_file()
        else:
            self._load_defaults()

    def _load_defaults(self):
        """Load default wholesaler data"""
        for data in WHOLESALER_DATA:
            wholesaler = Wholesaler.from_dict(data)
            self.wholesalers[wholesaler.id] = wholesaler

        logger.info(f"Loaded {len(self.wholesalers)} default wholesalers")

    def _load_from_file(self):
        """Load wholesalers from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                for item in data.get('wholesalers', []):
                    wholesaler = Wholesaler.from_dict(item)
                    self.wholesalers[wholesaler.id] = wholesaler

            logger.info(f"Loaded {len(self.wholesalers)} wholesalers from {self.data_file}")
        except Exception as e:
            logger.error(f"Failed to load wholesalers from file: {e}")
            self._load_defaults()

    def save_to_file(self):
        """Save wholesalers to JSON file"""
        if not self.data_file:
            return

        data = {
            'wholesalers': [w.to_dict() for w in self.wholesalers.values()],
            'updated_at': datetime.now().isoformat()
        }

        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(self.wholesalers)} wholesalers to {self.data_file}")

    def get_wholesaler(self, wholesaler_id: str) -> Optional[Wholesaler]:
        """Get a specific wholesaler by ID"""
        return self.wholesalers.get(wholesaler_id)

    def list_wholesalers(self, active_only: bool = True) -> List[Wholesaler]:
        """List all wholesalers"""
        wholesalers = list(self.wholesalers.values())
        if active_only:
            wholesalers = [w for w in wholesalers if w.is_active]
        return sorted(wholesalers, key=lambda w: w.rating, reverse=True)

    def find_wholesalers(
        self,
        device_type: Optional[str] = None,
        condition: Optional[str] = None,
        min_rating: float = 0.0,
        contactable_only: bool = True,
        max_results: int = 5
    ) -> List[Wholesaler]:
        """
        Find wholesalers matching criteria.

        Args:
            device_type: Filter by device type (ipad, android_tablet, etc.)
            condition: Filter by condition availability (new, refurbished_a, etc.)
            min_rating: Minimum rating threshold
            contactable_only: Only return wholesalers with email or contact form
            max_results: Maximum number of results

        Returns:
            List of matching wholesalers sorted by rating
        """
        results = []

        for wholesaler in self.wholesalers.values():
            # Skip inactive
            if not wholesaler.is_active:
                continue

            # Filter by device type
            if device_type and device_type not in wholesaler.supported_devices:
                continue

            # Filter by condition
            if condition and condition not in wholesaler.conditions_available:
                continue

            # Filter by rating
            if wholesaler.rating < min_rating:
                continue

            # Filter by contactability
            if contactable_only:
                if not wholesaler.email_address and not wholesaler.contact_form_url:
                    continue

            results.append(wholesaler)

        # Sort by rating (highest first)
        results.sort(key=lambda w: w.rating, reverse=True)

        return results[:max_results]

    def get_wholesalers_for_inquiry(
        self,
        device_type: str,
        condition: str = 'new',
        quantity: int = 1,
        max_wholesalers: int = 3
    ) -> List[Wholesaler]:
        """
        Get best wholesalers for a specific inquiry.

        Args:
            device_type: Type of device (ipad, etc.)
            condition: Desired condition
            quantity: Number of units needed
            max_wholesalers: Maximum wholesalers to return

        Returns:
            List of best-matched wholesalers
        """
        # Find matching wholesalers
        candidates = self.find_wholesalers(
            device_type=device_type,
            condition=condition,
            contactable_only=True,
            max_results=max_wholesalers * 2  # Get extras to filter
        )

        # Filter by minimum order quantity
        candidates = [w for w in candidates if w.min_order_quantity <= quantity]

        # Return top matches
        return candidates[:max_wholesalers]

    def add_wholesaler(self, wholesaler: Wholesaler) -> bool:
        """Add a new wholesaler"""
        if wholesaler.id in self.wholesalers:
            logger.warning(f"Wholesaler {wholesaler.id} already exists")
            return False

        self.wholesalers[wholesaler.id] = wholesaler
        self.save_to_file()
        return True

    def update_wholesaler(self, wholesaler_id: str, **kwargs) -> bool:
        """Update a wholesaler's information"""
        if wholesaler_id not in self.wholesalers:
            return False

        wholesaler = self.wholesalers[wholesaler_id]

        for key, value in kwargs.items():
            if hasattr(wholesaler, key):
                setattr(wholesaler, key, value)

        self.save_to_file()
        return True

    def deactivate_wholesaler(self, wholesaler_id: str) -> bool:
        """Deactivate a wholesaler"""
        return self.update_wholesaler(wholesaler_id, is_active=False)


# Singleton instance
_db_instance: Optional[WholesalerDB] = None


def get_wholesaler_db() -> WholesalerDB:
    """Get the singleton WholesalerDB instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = WholesalerDB()
    return _db_instance


# CLI for testing
if __name__ == '__main__':
    import sys

    db = WholesalerDB()

    print("Elder Tech Procurement - Wholesaler Database\n")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'list':
            print("All Wholesalers:\n")
            for w in db.list_wholesalers():
                contact = w.email_address or w.contact_form_url or "No contact"
                print(f"  [{w.id}] {w.name}")
                print(f"      Rating: {w.rating}/5.0 | Min Order: {w.min_order_quantity}")
                print(f"      Devices: {', '.join(w.supported_devices)}")
                print(f"      Conditions: {', '.join(w.conditions_available)}")
                print(f"      Contact: {contact}")
                print()

        elif command == 'find' and len(sys.argv) > 2:
            device_type = sys.argv[2]
            condition = sys.argv[3] if len(sys.argv) > 3 else 'new'

            print(f"Wholesalers for {device_type} ({condition}):\n")
            for w in db.find_wholesalers(device_type=device_type, condition=condition):
                print(f"  - {w.name} ({w.rating}/5.0)")
                print(f"    {w.website}")

        elif command == 'ipad':
            # Quick search for iPads
            print("Best Wholesalers for iPad Procurement:\n")
            for w in db.get_wholesalers_for_inquiry('ipad', 'new', 5):
                print(f"  {w.name}")
                print(f"    Rating: {w.rating}/5.0")
                print(f"    Min Order: {w.min_order_quantity}")
                print(f"    Response: ~{w.avg_response_hours} hours")
                if w.email_address:
                    print(f"    Email: {w.email_address}")
                if w.contact_form_url:
                    print(f"    Form: {w.contact_form_url}")
                print()

        else:
            print("Usage:")
            print("  python wholesaler_db.py list              - List all wholesalers")
            print("  python wholesaler_db.py find <device> [condition] - Find wholesalers")
            print("  python wholesaler_db.py ipad              - Best iPad wholesalers")
    else:
        # Summary
        print(f"Total Wholesalers: {len(db.list_wholesalers())}")
        print("\nDevice Coverage:")
        devices = set()
        for w in db.list_wholesalers():
            devices.update(w.supported_devices)
        for d in sorted(devices):
            count = len(db.find_wholesalers(device_type=d, max_results=100))
            print(f"  {d}: {count} wholesaler(s)")

        print("\nRun 'python wholesaler_db.py list' for full list")
