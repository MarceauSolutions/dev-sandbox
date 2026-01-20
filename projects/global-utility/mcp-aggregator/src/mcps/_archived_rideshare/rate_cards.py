"""
Rate Card Database - Pricing Data for Rideshare Services

CONFIDENTIAL - TRADE SECRET
Compiled pricing data from public Uber/Lyft rate cards.

Data Source: Publicly available rate cards on Uber.com/cities and Lyft.com/pricing
Update Frequency: Monthly (SOP 5)
Legal Status: ✅ Using publicly available information

Note: This is a simplified in-memory database for MVP.
Production will use PostgreSQL with automated updates.
"""

from typing import Dict, Optional
from datetime import datetime


class RateCardDB:
    """
    Rate card database for Uber and Lyft pricing

    Stores: base_fare, cost_per_mile, cost_per_minute, booking_fee, min_fare
    for each city/service/ride_type combination
    """

    def __init__(self):
        """Initialize with hardcoded rate cards (MVP)"""
        self.rate_cards = self._load_rate_cards()
        self.last_updated = datetime.now()

    def _load_rate_cards(self) -> Dict:
        """
        Load rate cards for major cities

        Data accurate as of: 2026-01-12
        Source: Uber.com/cities/[city], Lyft.com/pricing/[city]

        Returns:
            Nested dict: {city: {service: {ride_type: {...}}}}
        """
        return {
            'san_francisco': {
                'uber': {
                    'uberx': {
                        'base_fare': 2.55,
                        'cost_per_mile': 1.75,
                        'cost_per_minute': 0.30,
                        'booking_fee': 2.70,
                        'min_fare': 7.65
                    },
                    'uber_xl': {
                        'base_fare': 4.50,
                        'cost_per_mile': 2.85,
                        'cost_per_minute': 0.50,
                        'booking_fee': 3.00,
                        'min_fare': 10.00
                    }
                },
                'lyft': {
                    'lyft': {
                        'base_fare': 2.00,
                        'cost_per_mile': 1.50,
                        'cost_per_minute': 0.35,
                        'booking_fee': 2.70,
                        'min_fare': 6.00
                    },
                    'lyft_xl': {
                        'base_fare': 3.75,
                        'cost_per_mile': 2.50,
                        'cost_per_minute': 0.55,
                        'booking_fee': 3.00,
                        'min_fare': 9.00
                    }
                }
            },

            'new_york': {
                'uber': {
                    'uberx': {
                        'base_fare': 2.55,
                        'cost_per_mile': 1.95,
                        'cost_per_minute': 0.35,
                        'booking_fee': 2.75,
                        'min_fare': 8.00
                    }
                },
                'lyft': {
                    'lyft': {
                        'base_fare': 2.00,
                        'cost_per_mile': 1.71,
                        'cost_per_minute': 0.42,
                        'booking_fee': 2.75,
                        'min_fare': 7.00
                    }
                }
            },

            'los_angeles': {
                'uber': {
                    'uberx': {
                        'base_fare': 2.20,
                        'cost_per_mile': 1.20,
                        'cost_per_minute': 0.21,
                        'booking_fee': 2.40,
                        'min_fare': 5.50
                    }
                },
                'lyft': {
                    'lyft': {
                        'base_fare': 1.82,
                        'cost_per_mile': 1.08,
                        'cost_per_minute': 0.27,
                        'booking_fee': 2.40,
                        'min_fare': 5.00
                    }
                }
            },

            'chicago': {
                'uber': {
                    'uberx': {
                        'base_fare': 2.20,
                        'cost_per_mile': 1.45,
                        'cost_per_minute': 0.25,
                        'booking_fee': 2.40,
                        'min_fare': 6.55
                    }
                },
                'lyft': {
                    'lyft': {
                        'base_fare': 1.70,
                        'cost_per_mile': 1.20,
                        'cost_per_minute': 0.30,
                        'booking_fee': 2.40,
                        'min_fare': 5.75
                    }
                }
            },

            'boston': {
                'uber': {
                    'uberx': {
                        'base_fare': 2.55,
                        'cost_per_mile': 1.65,
                        'cost_per_minute': 0.35,
                        'booking_fee': 2.55,
                        'min_fare': 7.25
                    }
                },
                'lyft': {
                    'lyft': {
                        'base_fare': 2.00,
                        'cost_per_mile': 1.42,
                        'cost_per_minute': 0.39,
                        'booking_fee': 2.55,
                        'min_fare': 6.50
                    }
                }
            },

            'seattle': {
                'uber': {
                    'uberx': {
                        'base_fare': 2.45,
                        'cost_per_mile': 1.55,
                        'cost_per_minute': 0.28,
                        'booking_fee': 2.65,
                        'min_fare': 6.95
                    }
                },
                'lyft': {
                    'lyft': {
                        'base_fare': 2.07,
                        'cost_per_mile': 1.33,
                        'cost_per_minute': 0.33,
                        'booking_fee': 2.65,
                        'min_fare': 6.25
                    }
                }
            },

            'austin': {
                'uber': {
                    'uberx': {
                        'base_fare': 2.00,
                        'cost_per_mile': 1.10,
                        'cost_per_minute': 0.19,
                        'booking_fee': 2.30,
                        'min_fare': 5.30
                    }
                },
                'lyft': {
                    'lyft': {
                        'base_fare': 1.50,
                        'cost_per_mile': 0.95,
                        'cost_per_minute': 0.24,
                        'booking_fee': 2.30,
                        'min_fare': 4.75
                    }
                }
            },

            'miami': {
                'uber': {
                    'uberx': {
                        'base_fare': 2.15,
                        'cost_per_mile': 1.25,
                        'cost_per_minute': 0.22,
                        'booking_fee': 2.45,
                        'min_fare': 5.80
                    }
                },
                'lyft': {
                    'lyft': {
                        'base_fare': 1.90,
                        'cost_per_mile': 1.10,
                        'cost_per_minute': 0.26,
                        'booking_fee': 2.45,
                        'min_fare': 5.25
                    }
                }
            },

            'denver': {
                'uber': {
                    'uberx': {
                        'base_fare': 2.25,
                        'cost_per_mile': 1.35,
                        'cost_per_minute': 0.23,
                        'booking_fee': 2.50,
                        'min_fare': 6.00
                    }
                },
                'lyft': {
                    'lyft': {
                        'base_fare': 1.85,
                        'cost_per_mile': 1.18,
                        'cost_per_minute': 0.28,
                        'booking_fee': 2.50,
                        'min_fare': 5.40
                    }
                }
            },

            'washington_dc': {
                'uber': {
                    'uberx': {
                        'base_fare': 2.40,
                        'cost_per_mile': 1.60,
                        'cost_per_minute': 0.30,
                        'booking_fee': 2.60,
                        'min_fare': 7.00
                    }
                },
                'lyft': {
                    'lyft': {
                        'base_fare': 2.00,
                        'cost_per_mile': 1.38,
                        'cost_per_minute': 0.35,
                        'booking_fee': 2.60,
                        'min_fare': 6.30
                    }
                }
            }
        }

    def get_rates(
        self,
        city: str,
        service: str,
        ride_type: str
    ) -> Optional[Dict]:
        """
        Get rate card for specific city/service/ride_type

        Args:
            city: City name (e.g., 'san_francisco')
            service: 'uber' or 'lyft'
            ride_type: 'uberx', 'lyft', etc.

        Returns:
            Rate card dict or None if not found
        """
        try:
            return self.rate_cards[city][service][ride_type]
        except KeyError:
            return None

    def get_supported_cities(self) -> list:
        """Get list of supported cities"""
        return list(self.rate_cards.keys())

    def get_supported_ride_types(self, city: str, service: str) -> list:
        """Get supported ride types for city/service"""
        try:
            return list(self.rate_cards[city][service].keys())
        except KeyError:
            return []

    def update_rates(
        self,
        city: str,
        service: str,
        ride_type: str,
        new_rates: Dict
    ):
        """
        Update rate card (for SOP 5 - monthly updates)

        Args:
            city: City name
            service: 'uber' or 'lyft'
            ride_type: 'uberx', 'lyft', etc.
            new_rates: New rate card data
        """
        if city not in self.rate_cards:
            self.rate_cards[city] = {}

        if service not in self.rate_cards[city]:
            self.rate_cards[city][service] = {}

        self.rate_cards[city][service][ride_type] = new_rates
        self.last_updated = datetime.now()

    def add_city(self, city: str, rates: Dict):
        """
        Add new city to database

        Args:
            city: City name
            rates: Full rate structure {service: {ride_type: {...}}}
        """
        self.rate_cards[city] = rates
        self.last_updated = datetime.now()

    def validate_rates(self, rates: Dict) -> bool:
        """
        Validate rate card data

        Ensures all required fields present and values reasonable

        Args:
            rates: Rate card to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'base_fare',
            'cost_per_mile',
            'cost_per_minute',
            'booking_fee',
            'min_fare'
        ]

        # Check all fields present
        for field in required_fields:
            if field not in rates:
                return False

        # Check reasonable ranges
        if not (1.0 <= rates['base_fare'] <= 5.0):
            return False

        if not (0.5 <= rates['cost_per_mile'] <= 5.0):
            return False

        if not (0.1 <= rates['cost_per_minute'] <= 1.0):
            return False

        if not (1.0 <= rates['booking_fee'] <= 5.0):
            return False

        if not (3.0 <= rates['min_fare'] <= 15.0):
            return False

        return True

    def get_stats(self) -> Dict:
        """
        Get database statistics

        Returns:
            Stats dict with counts and last update time
        """
        total_cities = len(self.rate_cards)
        total_rate_cards = sum(
            len(services)
            for city_data in self.rate_cards.values()
            for services in city_data.values()
        )

        return {
            'total_cities': total_cities,
            'total_rate_cards': total_rate_cards,
            'last_updated': self.last_updated.isoformat(),
            'cities': self.get_supported_cities()
        }


# Example usage
if __name__ == "__main__":
    db = RateCardDB()

    print("Rate Card Database")
    print("=" * 50)
    print(f"Supported cities: {', '.join(db.get_supported_cities())}")
    print()

    # Get San Francisco UberX rates
    sf_uber_rates = db.get_rates('san_francisco', 'uber', 'uberx')
    print("San Francisco - UberX:")
    print(f"  Base Fare: ${sf_uber_rates['base_fare']:.2f}")
    print(f"  Per Mile: ${sf_uber_rates['cost_per_mile']:.2f}")
    print(f"  Per Minute: ${sf_uber_rates['cost_per_minute']:.2f}")
    print(f"  Booking Fee: ${sf_uber_rates['booking_fee']:.2f}")
    print(f"  Minimum Fare: ${sf_uber_rates['min_fare']:.2f}")
    print()

    # Get stats
    stats = db.get_stats()
    print(f"Database Stats:")
    print(f"  Total Cities: {stats['total_cities']}")
    print(f"  Total Rate Cards: {stats['total_rate_cards']}")
    print(f"  Last Updated: {stats['last_updated']}")
