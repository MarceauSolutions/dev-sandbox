"""
Test script for rideshare comparison MCP

Run this to verify the flagship MCP is working correctly.
"""

import sys
sys.path.insert(0, '/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/src')

from mcps.rideshare import RideshareComparison, Location, RateCardDB


def test_basic_comparison():
    """Test basic price comparison"""
    print("="*70)
    print("TEST 1: Basic Price Comparison")
    print("="*70)

    # Initialize
    db = RateCardDB()
    comparator = RideshareComparison(db)

    # Test route: Union Square SF to SFO Airport
    pickup = Location(
        latitude=37.7879,
        longitude=-122.4074,
        address="Union Square, San Francisco"
    )

    dropoff = Location(
        latitude=37.6213,
        longitude=-122.3790,
        address="SFO Airport"
    )

    # Compare
    result = comparator.compare_prices(pickup, dropoff)

    # Display results
    print(f"\nRoute: {pickup.address} → {dropoff.address}")
    print(f"City: {result['city']}")
    print(f"Distance: {result['distance_miles']} miles")
    print(f"Duration: ~{result['duration_minutes']:.0f} minutes")
    print()

    print("UBER:")
    uber = result['uber']
    print(f"  Estimate: ${uber.estimate:.2f}")
    print(f"  Range: ${uber.low_estimate:.2f} - ${uber.high_estimate:.2f}")
    print(f"  Surge: {uber.surge_multiplier}x")
    print(f"  Confidence: {uber.confidence * 100:.0f}%")
    print(f"  Deep Link: {uber.deep_link[:50]}...")
    print()

    print("LYFT:")
    lyft = result['lyft']
    print(f"  Estimate: ${lyft.estimate:.2f}")
    print(f"  Range: ${lyft.low_estimate:.2f} - ${lyft.high_estimate:.2f}")
    print(f"  Surge: {lyft.surge_multiplier}x")
    print(f"  Confidence: {lyft.confidence * 100:.0f}%")
    print(f"  Deep Link: {lyft.deep_link[:50]}...")
    print()

    print(f"✅ RECOMMENDATION: {result['recommendation'].upper()}")
    print(f"💰 SAVINGS: ${result['savings']:.2f}")
    print()

    # Verify accuracy
    assert result['distance_miles'] > 0, "Distance should be positive"
    assert result['duration_minutes'] > 0, "Duration should be positive"
    assert uber.estimate > 0, "Uber estimate should be positive"
    assert lyft.estimate > 0, "Lyft estimate should be positive"
    assert result['recommendation'] in ['uber', 'lyft'], "Invalid recommendation"

    print("✅ TEST 1 PASSED\n")


def test_multiple_cities():
    """Test multiple cities"""
    print("="*70)
    print("TEST 2: Multiple Cities")
    print("="*70)

    db = RateCardDB()
    comparator = RideshareComparison(db)

    # Test routes in different cities
    test_routes = [
        {
            'city': 'san_francisco',
            'pickup': Location(37.7879, -122.4074, "Union Square"),
            'dropoff': Location(37.6213, -122.3790, "SFO Airport"),
            'expected_distance': 14.0  # Approximate
        },
        {
            'city': 'new_york',
            'pickup': Location(40.7589, -73.9851, "Times Square"),
            'dropoff': Location(40.6413, -73.7781, "JFK Airport"),
            'expected_distance': 16.0
        },
        {
            'city': 'los_angeles',
            'pickup': Location(34.0522, -118.2437, "Downtown LA"),
            'dropoff': Location(33.9416, -118.4085, "LAX Airport"),
            'expected_distance': 15.0
        }
    ]

    for route in test_routes:
        result = comparator.compare_prices(
            route['pickup'],
            route['dropoff'],
            route['city']
        )

        print(f"\n{route['city'].upper().replace('_', ' ')}:")
        print(f"  Distance: {result['distance_miles']} miles")
        print(f"  Uber: ${result['uber'].estimate:.2f}")
        print(f"  Lyft: ${result['lyft'].estimate:.2f}")
        print(f"  Cheaper: {result['recommendation'].upper()} (save ${result['savings']:.2f})")

        # Verify
        assert result['distance_miles'] > 0
        assert abs(result['distance_miles'] - route['expected_distance']) < 3.0, \
            f"Distance calculation off by more than 3 miles"

    print("\n✅ TEST 2 PASSED\n")


def test_surge_estimation():
    """Test surge pricing estimation"""
    print("="*70)
    print("TEST 3: Surge Pricing Estimation")
    print("="*70)

    db = RateCardDB()
    comparator = RideshareComparison(db)

    # Test same route at different times
    pickup = Location(37.7879, -122.4074)
    dropoff = Location(37.6213, -122.3790)

    from datetime import datetime

    test_times = [
        (datetime(2026, 1, 13, 8, 0), "Monday 8 AM (morning rush)"),
        (datetime(2026, 1, 13, 14, 0), "Monday 2 PM (normal)"),
        (datetime(2026, 1, 13, 18, 0), "Monday 6 PM (evening rush)"),
        (datetime(2026, 1, 17, 23, 0), "Friday 11 PM (night out)"),
        (datetime(2026, 1, 19, 10, 0), "Sunday 10 AM (low demand)")
    ]

    for timestamp, description in test_times:
        # Manually set surge for testing
        surge_uber = comparator._estimate_surge('san_francisco', 'uber', timestamp)
        surge_lyft = comparator._estimate_surge('san_francisco', 'lyft', timestamp)

        print(f"\n{description}:")
        print(f"  Uber surge: {surge_uber}x")
        print(f"  Lyft surge: {surge_lyft}x")

        assert 0.8 <= surge_uber <= 2.0, "Surge should be between 0.8x and 2.0x"
        assert 0.8 <= surge_lyft <= 2.0, "Surge should be between 0.8x and 2.0x"

    print("\n✅ TEST 3 PASSED\n")


def test_rate_card_db():
    """Test rate card database"""
    print("="*70)
    print("TEST 4: Rate Card Database")
    print("="*70)

    db = RateCardDB()

    # Check supported cities
    cities = db.get_supported_cities()
    print(f"\nSupported cities ({len(cities)}):")
    print(f"  {', '.join(cities)}")

    assert len(cities) >= 10, "Should support at least 10 cities"

    # Check specific rate card
    sf_uber = db.get_rates('san_francisco', 'uber', 'uberx')
    print(f"\nSan Francisco - UberX:")
    print(f"  Base Fare: ${sf_uber['base_fare']:.2f}")
    print(f"  Per Mile: ${sf_uber['cost_per_mile']:.2f}")
    print(f"  Per Minute: ${sf_uber['cost_per_minute']:.2f}")
    print(f"  Minimum: ${sf_uber['min_fare']:.2f}")

    # Validate rates
    assert db.validate_rates(sf_uber), "Rates should be valid"

    # Check stats
    stats = db.get_stats()
    print(f"\nDatabase Stats:")
    print(f"  Total Cities: {stats['total_cities']}")
    print(f"  Total Rate Cards: {stats['total_rate_cards']}")
    print(f"  Last Updated: {stats['last_updated']}")

    print("\n✅ TEST 4 PASSED\n")


def test_deep_links():
    """Test deep link generation"""
    print("="*70)
    print("TEST 5: Deep Link Generation")
    print("="*70)

    from mcps.rideshare.deep_links import (
        generate_uber_link,
        generate_lyft_link,
        generate_smart_link
    )

    pickup = (37.7879, -122.4074)
    dropoff = (37.6213, -122.3790)

    # Test Uber link
    uber_link = generate_uber_link(*pickup, *dropoff)
    print(f"\nUber Deep Link:")
    print(f"  {uber_link}")
    assert uber_link.startswith('uber://'), "Should be Uber deep link"
    assert 'pickup[latitude]=37.7879' in uber_link

    # Test Lyft link
    lyft_link = generate_lyft_link(*pickup, *dropoff)
    print(f"\nLyft Deep Link:")
    print(f"  {lyft_link}")
    assert lyft_link.startswith('lyft://'), "Should be Lyft deep link"
    assert 'pickup[latitude]=37.7879' in lyft_link

    # Test smart link
    smart = generate_smart_link('uber', *pickup, *dropoff, mobile=True)
    print(f"\nSmart Link (Uber, mobile):")
    print(f"  App: {smart['app_link'][:60]}...")
    print(f"  Web: {smart['web_link'][:60]}...")
    print(f"  Primary: {smart['primary'][:60]}...")

    assert smart['primary'] == smart['app_link'], "Should prioritize app on mobile"

    print("\n✅ TEST 5 PASSED\n")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print(" "*15 + "RIDESHARE MCP TEST SUITE")
    print("="*70 + "\n")

    try:
        test_basic_comparison()
        test_multiple_cities()
        test_surge_estimation()
        test_rate_card_db()
        test_deep_links()

        print("="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\nRideshare MCP is ready for deployment.")
        print("Target accuracy: 85%+ within ±20% of actual price")
        print("\nNext steps:")
        print("  1. Test with real Uber/Lyft quotes (manual verification)")
        print("  2. Calculate actual accuracy on 100 test routes")
        print("  3. Deploy to production")
        print("  4. Start earning affiliate commissions")
        print()

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
