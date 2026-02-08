#!/usr/bin/env python3
"""
Test Route Generator for Accuracy Validation

Generates 30 diverse test routes across supported cities with:
- Various distance categories (short, medium, long)
- Different times of day (morning, afternoon, evening, late night)
- Urban and suburban routes
- Airport runs
- Common landmarks

Output: test-routes.csv
"""

import csv
import random
from datetime import datetime

# Landmark coordinates for each city
# Format: (name, latitude, longitude)
LANDMARKS = {
    'san_francisco': [
        ('Union Square', 37.7879, -122.4074),
        ('SFO Airport', 37.6213, -122.3790),
        ('Golden Gate Park', 37.7694, -122.4862),
        ('Fishermans Wharf', 37.8080, -122.4177),
        ('Mission District', 37.7599, -122.4148),
        ('SOMA', 37.7785, -122.3950),
        ('Castro', 37.7609, -122.4350),
        ('Marina District', 37.8036, -122.4362),
        ('Sunset District', 37.7527, -122.4936),
        ('Presidio', 37.7989, -122.4662),
    ],
    'new_york': [
        ('Times Square', 40.7580, -73.9855),
        ('JFK Airport', 40.6413, -73.7781),
        ('Central Park', 40.7829, -73.9654),
        ('Wall Street', 40.7074, -74.0113),
        ('Brooklyn Bridge', 40.7061, -73.9969),
        ('Midtown', 40.7549, -73.9840),
        ('Upper East Side', 40.7736, -73.9566),
        ('Greenwich Village', 40.7336, -74.0027),
        ('Harlem', 40.8116, -73.9465),
        ('LaGuardia Airport', 40.7769, -73.8740),
    ],
    'los_angeles': [
        ('LAX Airport', 33.9425, -118.4081),
        ('Hollywood', 34.0928, -118.3287),
        ('Santa Monica', 34.0195, -118.4912),
        ('Downtown LA', 34.0522, -118.2437),
        ('Beverly Hills', 34.0736, -118.4004),
        ('Venice Beach', 33.9850, -118.4695),
        ('Burbank', 34.1808, -118.3090),
        ('Westwood', 34.0635, -118.4455),
        ('Koreatown', 34.0577, -118.3011),
        ('Silver Lake', 34.0869, -118.2702),
    ],
    'chicago': [
        ('ORD Airport', 41.9742, -87.9073),
        ('The Loop', 41.8827, -87.6233),
        ('Wrigley Field', 41.9484, -87.6553),
        ('Navy Pier', 41.8917, -87.6086),
        ('Lincoln Park', 41.9214, -87.6513),
        ('Wicker Park', 41.9088, -87.6796),
        ('South Loop', 41.8568, -87.6235),
        ('Midway Airport', 41.7868, -87.7522),
        ('Hyde Park', 41.7943, -87.5907),
        ('River North', 41.8922, -87.6324),
    ],
    'boston': [
        ('Logan Airport', 42.3656, -71.0096),
        ('Downtown Crossing', 42.3555, -71.0604),
        ('Harvard Square', 42.3736, -71.1189),
        ('Fenway Park', 42.3467, -71.0972),
        ('North End', 42.3647, -71.0542),
        ('Back Bay', 42.3501, -71.0762),
        ('South Boston', 42.3388, -71.0483),
        ('Beacon Hill', 42.3588, -71.0707),
        ('Cambridge', 42.3736, -71.1097),
        ('Charlestown', 42.3782, -71.0602),
    ],
    'seattle': [
        ('SeaTac Airport', 47.4502, -122.3088),
        ('Pike Place Market', 47.6097, -122.3422),
        ('Capitol Hill', 47.6253, -122.3222),
        ('University District', 47.6607, -122.3132),
        ('Fremont', 47.6511, -122.3502),
        ('Ballard', 47.6681, -122.3843),
        ('Downtown', 47.6062, -122.3321),
        ('Queen Anne', 47.6372, -122.3571),
        ('SoDo', 47.5801, -122.3312),
        ('Bellevue', 47.6101, -122.2015),
    ],
    'austin': [
        ('Austin Airport', 30.1975, -97.6664),
        ('Downtown Austin', 30.2672, -97.7431),
        ('UT Campus', 30.2849, -97.7341),
        ('South Congress', 30.2460, -97.7495),
        ('East Austin', 30.2652, -97.7131),
        ('Zilker Park', 30.2665, -97.7731),
        ('The Domain', 30.4014, -97.7250),
        ('Mueller', 30.2988, -97.7023),
        ('Barton Creek', 30.2616, -97.8094),
        ('North Austin', 30.3500, -97.7500),
    ],
    'miami': [
        ('MIA Airport', 25.7959, -80.2870),
        ('South Beach', 25.7826, -80.1341),
        ('Downtown Miami', 25.7617, -80.1918),
        ('Brickell', 25.7617, -80.1919),
        ('Wynwood', 25.8011, -80.1990),
        ('Coral Gables', 25.7215, -80.2684),
        ('Coconut Grove', 25.7289, -80.2425),
        ('Little Havana', 25.7655, -80.2182),
        ('Design District', 25.8117, -80.1922),
        ('Miami Beach', 25.8103, -80.1325),
    ],
    'denver': [
        ('DEN Airport', 39.8561, -104.6737),
        ('Downtown Denver', 39.7392, -104.9903),
        ('LoDo', 39.7533, -105.0022),
        ('Cherry Creek', 39.7181, -104.9529),
        ('Capitol Hill', 39.7312, -104.9811),
        ('RiNo', 39.7656, -104.9811),
        ('Highlands', 39.7656, -105.0075),
        ('Washington Park', 39.6975, -104.9709),
        ('Park Hill', 39.7500, -104.9250),
        ('Five Points', 39.7541, -104.9858),
    ],
    'washington_dc': [
        ('DCA Airport', 38.8512, -77.0402),
        ('Capitol Hill', 38.8899, -77.0091),
        ('Georgetown', 38.9076, -77.0723),
        ('Dupont Circle', 38.9096, -77.0434),
        ('National Mall', 38.8895, -77.0353),
        ('Adams Morgan', 38.9215, -77.0422),
        ('U Street', 38.9170, -77.0310),
        ('Navy Yard', 38.8756, -77.0001),
        ('Foggy Bottom', 38.8981, -77.0509),
        ('Columbia Heights', 38.9283, -77.0326),
    ],
}

# Distance categories with typical mile ranges
DISTANCE_CATEGORIES = {
    'short': (1.0, 3.0),      # Quick rides in neighborhood
    'medium': (4.0, 8.0),     # Cross-town trips
    'long': (10.0, 20.0),     # Airport runs, suburb to downtown
}

# Time of day categories
TIME_CATEGORIES = [
    ('morning_rush', '08:00'),
    ('midday', '13:00'),
    ('evening_rush', '17:30'),
    ('late_night', '23:00'),
    ('early_morning', '06:00'),
]


def generate_routes(num_routes: int = 30) -> list:
    """
    Generate diverse test routes

    Distribution strategy:
    - 10 cities x 3 routes each = 30 routes
    - Mix of distance categories
    - Mix of time categories
    """
    routes = []
    route_id = 1

    cities = list(LANDMARKS.keys())

    for city in cities:
        landmarks = LANDMARKS[city]

        # Generate 3 routes per city
        for i in range(3):
            # Select different distance categories
            if i == 0:
                distance_cat = 'short'
            elif i == 1:
                distance_cat = 'medium'
            else:
                distance_cat = 'long'

            # Pick pickup and dropoff locations
            # For short: adjacent landmarks
            # For long: airport to downtown (or similar)
            if distance_cat == 'short':
                pickup = landmarks[0]
                dropoff = landmarks[4]  # Nearby
            elif distance_cat == 'medium':
                pickup = landmarks[1]
                dropoff = landmarks[5]
            else:  # long
                # Airport route (usually first landmark is airport-related)
                if 'Airport' in landmarks[1][0] or 'Airport' in landmarks[0][0]:
                    pickup = landmarks[0]
                    dropoff = landmarks[1]
                else:
                    pickup = landmarks[0]
                    dropoff = landmarks[-1]

            # Assign time category (cycle through)
            time_cat_idx = (route_id - 1) % len(TIME_CATEGORIES)
            time_name, time_str = TIME_CATEGORIES[time_cat_idx]

            route = {
                'route_id': route_id,
                'pickup_lat': pickup[1],
                'pickup_lng': pickup[2],
                'dropoff_lat': dropoff[1],
                'dropoff_lng': dropoff[2],
                'pickup_address': pickup[0],
                'dropoff_address': dropoff[0],
                'city': city,
                'distance_category': distance_cat,
                'time_of_day': time_name,
                'test_time': time_str,
            }

            routes.append(route)
            route_id += 1

    return routes


def write_routes_csv(routes: list, output_path: str):
    """Write routes to CSV file"""
    fieldnames = [
        'route_id', 'pickup_lat', 'pickup_lng', 'dropoff_lat', 'dropoff_lng',
        'pickup_address', 'dropoff_address', 'city', 'distance_category',
        'time_of_day', 'test_time'
    ]

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(routes)

    print(f"Generated {len(routes)} routes -> {output_path}")


def print_route_summary(routes: list):
    """Print summary of generated routes"""
    print("\n" + "=" * 60)
    print("TEST ROUTES SUMMARY")
    print("=" * 60)

    # Count by city
    cities = {}
    for r in routes:
        cities[r['city']] = cities.get(r['city'], 0) + 1

    print(f"\nTotal routes: {len(routes)}")
    print("\nBy City:")
    for city, count in sorted(cities.items()):
        print(f"  {city}: {count} routes")

    # Count by distance category
    distances = {}
    for r in routes:
        cat = r['distance_category']
        distances[cat] = distances.get(cat, 0) + 1

    print("\nBy Distance:")
    for cat, count in sorted(distances.items()):
        print(f"  {cat}: {count} routes")

    # Count by time of day
    times = {}
    for r in routes:
        t = r['time_of_day']
        times[t] = times.get(t, 0) + 1

    print("\nBy Time of Day:")
    for t, count in sorted(times.items()):
        print(f"  {t}: {count} routes")

    print("=" * 60)


if __name__ == "__main__":
    import os

    # Generate routes
    routes = generate_routes(30)

    # Output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'test-routes.csv')

    # Write CSV
    write_routes_csv(routes, output_path)

    # Print summary
    print_route_summary(routes)

    print(f"\nOutput file: {output_path}")
    print("\nNext step: Run run_algorithm.py to generate estimates")
