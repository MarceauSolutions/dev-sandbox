#!/usr/bin/env python3
"""
Algorithm Runner - Generate Estimates for Test Routes

Reads test-routes.csv and runs the RideshareComparison algorithm
on each route to generate our predictions.

Output: estimated-quotes.csv

This script can be run autonomously - no manual data collection needed.
"""

import csv
import sys
import os
from datetime import datetime, timedelta

# Add the MCP source to path
MCP_SRC_PATH = '/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/src'
sys.path.insert(0, MCP_SRC_PATH)

from mcps.rideshare.comparison import RideshareComparison, Location
from mcps.rideshare.rate_cards import RateCardDB


def parse_time_to_datetime(time_str: str) -> datetime:
    """
    Convert time string (HH:MM) to datetime object for today

    Args:
        time_str: Time in HH:MM format

    Returns:
        datetime object
    """
    hour, minute = map(int, time_str.split(':'))
    now = datetime.now()
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def run_algorithm_on_routes(input_csv: str, output_csv: str):
    """
    Run RideshareComparison algorithm on all test routes

    Args:
        input_csv: Path to test-routes.csv
        output_csv: Path to output estimated-quotes.csv
    """
    # Initialize the comparison engine
    db = RateCardDB()
    comparator = RideshareComparison(db)

    # Read test routes
    routes = []
    with open(input_csv, 'r') as f:
        reader = csv.DictReader(f)
        routes = list(reader)

    print(f"Loaded {len(routes)} test routes from {input_csv}")
    print("Running algorithm estimates...")
    print("-" * 60)

    # Process each route
    results = []
    for route in routes:
        route_id = route['route_id']
        city = route['city']

        # Create Location objects
        pickup = Location(
            latitude=float(route['pickup_lat']),
            longitude=float(route['pickup_lng']),
            address=route['pickup_address']
        )

        dropoff = Location(
            latitude=float(route['dropoff_lat']),
            longitude=float(route['dropoff_lng']),
            address=route['dropoff_address']
        )

        try:
            # Run comparison
            result = comparator.compare_prices(pickup, dropoff, city)

            # Extract estimates
            uber_estimate = result['uber'].estimate
            uber_low = result['uber'].low_estimate
            uber_high = result['uber'].high_estimate
            uber_surge = result['uber'].surge_multiplier

            lyft_estimate = result['lyft'].estimate
            lyft_low = result['lyft'].low_estimate
            lyft_high = result['lyft'].high_estimate
            lyft_surge = result['lyft'].surge_multiplier

            distance_miles = result['distance_miles']
            duration_minutes = result['duration_minutes']
            recommendation = result['recommendation']
            savings = result['savings']

            # Add to results
            results.append({
                'route_id': route_id,
                'city': city,
                'pickup_address': route['pickup_address'],
                'dropoff_address': route['dropoff_address'],
                'distance_category': route['distance_category'],
                'time_of_day': route['time_of_day'],
                'distance_miles': distance_miles,
                'duration_minutes': duration_minutes,
                'uber_estimate': uber_estimate,
                'uber_low': uber_low,
                'uber_high': uber_high,
                'uber_surge': uber_surge,
                'lyft_estimate': lyft_estimate,
                'lyft_low': lyft_low,
                'lyft_high': lyft_high,
                'lyft_surge': lyft_surge,
                'recommendation': recommendation,
                'estimated_savings': savings,
                'timestamp': datetime.now().isoformat(),
            })

            print(f"Route {int(route_id):2d}: {city:15s} | "
                  f"Uber: ${uber_estimate:6.2f} | "
                  f"Lyft: ${lyft_estimate:6.2f} | "
                  f"Best: {recommendation}")

        except Exception as e:
            print(f"Route {route_id}: ERROR - {str(e)}")
            results.append({
                'route_id': route_id,
                'city': city,
                'pickup_address': route['pickup_address'],
                'dropoff_address': route['dropoff_address'],
                'distance_category': route['distance_category'],
                'time_of_day': route['time_of_day'],
                'distance_miles': 'ERROR',
                'duration_minutes': 'ERROR',
                'uber_estimate': 'ERROR',
                'uber_low': 'ERROR',
                'uber_high': 'ERROR',
                'uber_surge': 'ERROR',
                'lyft_estimate': 'ERROR',
                'lyft_low': 'ERROR',
                'lyft_high': 'ERROR',
                'lyft_surge': 'ERROR',
                'recommendation': 'ERROR',
                'estimated_savings': 'ERROR',
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
            })

    # Write output CSV
    fieldnames = [
        'route_id', 'city', 'pickup_address', 'dropoff_address',
        'distance_category', 'time_of_day', 'distance_miles', 'duration_minutes',
        'uber_estimate', 'uber_low', 'uber_high', 'uber_surge',
        'lyft_estimate', 'lyft_low', 'lyft_high', 'lyft_surge',
        'recommendation', 'estimated_savings', 'timestamp'
    ]

    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)

    print("-" * 60)
    print(f"\nGenerated {len(results)} estimates -> {output_csv}")

    # Print summary statistics
    print_summary(results)


def print_summary(results: list):
    """Print summary statistics of the estimates"""
    print("\n" + "=" * 60)
    print("ESTIMATE SUMMARY")
    print("=" * 60)

    # Filter successful results
    valid_results = [r for r in results if r.get('uber_estimate') != 'ERROR']

    if not valid_results:
        print("No valid estimates generated.")
        return

    # Price ranges
    uber_prices = [float(r['uber_estimate']) for r in valid_results]
    lyft_prices = [float(r['lyft_estimate']) for r in valid_results]

    print(f"\nUber Estimates:")
    print(f"  Min: ${min(uber_prices):.2f}")
    print(f"  Max: ${max(uber_prices):.2f}")
    print(f"  Avg: ${sum(uber_prices)/len(uber_prices):.2f}")

    print(f"\nLyft Estimates:")
    print(f"  Min: ${min(lyft_prices):.2f}")
    print(f"  Max: ${max(lyft_prices):.2f}")
    print(f"  Avg: ${sum(lyft_prices)/len(lyft_prices):.2f}")

    # Recommendations
    uber_wins = sum(1 for r in valid_results if r['recommendation'] == 'uber')
    lyft_wins = sum(1 for r in valid_results if r['recommendation'] == 'lyft')

    print(f"\nRecommendations:")
    print(f"  Uber recommended: {uber_wins} times ({100*uber_wins/len(valid_results):.1f}%)")
    print(f"  Lyft recommended: {lyft_wins} times ({100*lyft_wins/len(valid_results):.1f}%)")

    # Average savings
    savings = [float(r['estimated_savings']) for r in valid_results]
    print(f"\nPotential Savings:")
    print(f"  Avg savings by choosing best: ${sum(savings)/len(savings):.2f}")
    print(f"  Max savings on single ride: ${max(savings):.2f}")

    print("=" * 60)


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    input_csv = os.path.join(script_dir, 'test-routes.csv')
    output_csv = os.path.join(script_dir, 'estimated-quotes.csv')

    if not os.path.exists(input_csv):
        print(f"ERROR: {input_csv} not found!")
        print("Run generate_test_routes.py first.")
        sys.exit(1)

    run_algorithm_on_routes(input_csv, output_csv)

    print(f"\nOutput file: {output_csv}")
    print("\nNEXT STEPS:")
    print("1. Human collects actual Uber/Lyft quotes (see QUOTE-COLLECTION-GUIDE.md)")
    print("2. Human fills in actual-quotes-template.csv")
    print("3. Run calculate_accuracy.py to compare estimates vs actuals")
