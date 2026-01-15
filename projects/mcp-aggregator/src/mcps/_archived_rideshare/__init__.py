"""
Rideshare Comparison MCP

Flagship service for comparing Uber and Lyft prices.
"""

from .comparison import RideshareComparison, Location, FareEstimate
from .rate_cards import RateCardDB
from .deep_links import (
    generate_uber_link,
    generate_lyft_link,
    generate_smart_link
)

__all__ = [
    'RideshareComparison',
    'Location',
    'FareEstimate',
    'RateCardDB',
    'generate_uber_link',
    'generate_lyft_link',
    'generate_smart_link'
]
