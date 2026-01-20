"""
Deep Link Generation for Rideshare Apps

Legal Status: ✅ Explicitly allowed and encouraged by Uber/Lyft
Use Case: Affiliate programs, app integrations, user convenience

This module generates deep links that open Uber/Lyft apps with
pickup/dropoff pre-filled, enabling one-click booking.

No API access required - these are just URL schemes.
"""

from typing import Optional
from urllib.parse import quote


def generate_uber_link(
    pickup_lat: float,
    pickup_lng: float,
    dropoff_lat: float,
    dropoff_lng: float,
    product_id: Optional[str] = None,
    client_id: Optional[str] = None
) -> str:
    """
    Generate Uber deep link

    Opens Uber app (iOS/Android) or Uber website (desktop) with route pre-filled.

    Legal: ✅ Documented in Uber's official developer docs
    Source: https://developer.uber.com/docs/riders/ride-requests/tutorials/deep-links

    Args:
        pickup_lat: Pickup latitude
        pickup_lng: Pickup longitude
        dropoff_lat: Dropoff latitude
        dropoff_lng: Dropoff longitude
        product_id: Optional Uber product ID (UberX, UberXL, etc.)
        client_id: Optional client ID for tracking (affiliate program)

    Returns:
        Deep link URL

    Example:
        >>> generate_uber_link(37.7749, -122.4194, 37.6213, -122.3790)
        'uber://?action=setPickup&pickup[latitude]=37.7749&...'
    """
    link = (
        f"uber://?action=setPickup"
        f"&pickup[latitude]={pickup_lat}"
        f"&pickup[longitude]={pickup_lng}"
        f"&dropoff[latitude]={dropoff_lat}"
        f"&dropoff[longitude]={dropoff_lng}"
    )

    if product_id:
        link += f"&product_id={product_id}"

    if client_id:
        link += f"&client_id={client_id}"

    return link


def generate_uber_web_link(
    pickup_lat: float,
    pickup_lng: float,
    dropoff_lat: float,
    dropoff_lng: float
) -> str:
    """
    Generate Uber web link (fallback for desktop)

    Args:
        pickup_lat: Pickup latitude
        pickup_lng: Pickup longitude
        dropoff_lat: Dropoff latitude
        dropoff_lng: Dropoff longitude

    Returns:
        HTTPS URL to Uber website
    """
    return (
        f"https://m.uber.com/ul/"
        f"?action=setPickup"
        f"&pickup[latitude]={pickup_lat}"
        f"&pickup[longitude]={pickup_lng}"
        f"&dropoff[latitude]={dropoff_lat}"
        f"&dropoff[longitude]={dropoff_lng}"
    )


def generate_lyft_link(
    pickup_lat: float,
    pickup_lng: float,
    dropoff_lat: float,
    dropoff_lng: float,
    ride_type: str = "lyft",
    partner_id: Optional[str] = None
) -> str:
    """
    Generate Lyft deep link

    Opens Lyft app (iOS/Android) or Lyft website (desktop) with route pre-filled.

    Legal: ✅ Documented in Lyft's official developer docs
    Source: https://developer.lyft.com/docs/deeplinking

    Args:
        pickup_lat: Pickup latitude
        pickup_lng: Pickup longitude
        dropoff_lat: Dropoff latitude
        dropoff_lng: Dropoff longitude
        ride_type: Lyft ride type ('lyft', 'lyft_plus', 'lyft_xl', etc.)
        partner_id: Optional partner ID for tracking (affiliate program)

    Returns:
        Deep link URL

    Example:
        >>> generate_lyft_link(37.7749, -122.4194, 37.6213, -122.3790)
        'lyft://ridetype?id=lyft&pickup[latitude]=37.7749&...'
    """
    link = (
        f"lyft://ridetype?id={ride_type}"
        f"&pickup[latitude]={pickup_lat}"
        f"&pickup[longitude]={pickup_lng}"
        f"&destination[latitude]={dropoff_lat}"
        f"&destination[longitude]={dropoff_lng}"
    )

    if partner_id:
        link += f"&partner={partner_id}"

    return link


def generate_lyft_web_link(
    pickup_lat: float,
    pickup_lng: float,
    dropoff_lat: float,
    dropoff_lng: float
) -> str:
    """
    Generate Lyft web link (fallback for desktop)

    Args:
        pickup_lat: Pickup latitude
        pickup_lng: Pickup longitude
        dropoff_lat: Dropoff latitude
        dropoff_lng: Dropoff longitude

    Returns:
        HTTPS URL to Lyft website
    """
    return (
        f"https://lyft.com/ride"
        f"?pickup[latitude]={pickup_lat}"
        f"&pickup[longitude]={pickup_lng}"
        f"&destination[latitude]={dropoff_lat}"
        f"&destination[longitude]={dropoff_lng}"
    )


def generate_smart_link(
    service: str,
    pickup_lat: float,
    pickup_lng: float,
    dropoff_lat: float,
    dropoff_lng: float,
    mobile: bool = True
) -> dict:
    """
    Generate smart link with app and web fallback

    Returns both deep link (for mobile) and web link (for desktop/fallback)

    Args:
        service: 'uber' or 'lyft'
        pickup_lat: Pickup latitude
        pickup_lng: Pickup longitude
        dropoff_lat: Dropoff latitude
        dropoff_lng: Dropoff longitude
        mobile: True if user is on mobile device

    Returns:
        Dict with 'app_link' and 'web_link'

    Example:
        >>> links = generate_smart_link('uber', 37.7749, -122.4194, 37.6213, -122.3790)
        >>> print(links['app_link'])  # Use this on mobile
        >>> print(links['web_link'])  # Use this on desktop
    """
    if service.lower() == 'uber':
        app_link = generate_uber_link(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
        web_link = generate_uber_web_link(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
    elif service.lower() == 'lyft':
        app_link = generate_lyft_link(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
        web_link = generate_lyft_web_link(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
    else:
        raise ValueError(f"Unknown service: {service}. Must be 'uber' or 'lyft'")

    return {
        'app_link': app_link,
        'web_link': web_link,
        'primary': app_link if mobile else web_link
    }


# Uber Product IDs (for specific ride types)
UBER_PRODUCTS = {
    'uberx': 'a1111c8c-c720-46c3-8534-2fcdd730040d',
    'uber_xl': '821415d8-3bd5-4e27-9604-194e4359a449',
    'uber_black': 'd4abaae7-f4d6-4152-91cc-77523e8165a4',
    'uber_black_suv': '8920cb5e-51a4-4fa4-acdf-dd86c5e18ae0'
}

# Lyft Ride Types
LYFT_RIDE_TYPES = {
    'lyft': 'lyft',
    'lyft_plus': 'lyft_plus',
    'lyft_xl': 'lyft_xl',
    'lyft_lux': 'lyft_lux',
    'lyft_lux_black': 'lyft_luxblack',
    'lyft_lux_black_xl': 'lyft_luxblack_xl'
}


# Example usage
if __name__ == "__main__":
    print("Rideshare Deep Link Generator")
    print("=" * 60)

    # Example route: Union Square SF to SFO Airport
    pickup = (37.7879, -122.4074)
    dropoff = (37.6213, -122.3790)

    print("\nExample: Union Square, SF → SFO Airport")
    print()

    # Uber links
    print("UBER:")
    print(f"  App: {generate_uber_link(*pickup, *dropoff)}")
    print(f"  Web: {generate_uber_web_link(*pickup, *dropoff)}")
    print()

    # Lyft links
    print("LYFT:")
    print(f"  App: {generate_lyft_link(*pickup, *dropoff)}")
    print(f"  Web: {generate_lyft_web_link(*pickup, *dropoff)}")
    print()

    # Smart link (detects mobile vs desktop)
    print("SMART LINK (Uber):")
    links = generate_smart_link('uber', *pickup, *dropoff, mobile=True)
    print(f"  Primary (mobile): {links['primary']}")
    print(f"  Fallback (web): {links['web_link']}")
    print()

    print("✅ All links are legal - explicitly allowed by Uber/Lyft")
    print("✅ Used for affiliate programs, app integrations, user convenience")
    print("✅ No API access required - these are just URL schemes")
