#!/usr/bin/env python3
"""
Fetch weather data for Naples, Florida from the National Weather Service API.
Free API, no authentication required.
"""

import requests
import json
from datetime import datetime
from pathlib import Path

# Naples, FL coordinates
NAPLES_LAT = 26.1420
NAPLES_LON = -81.7948

# NWS API base URL
NWS_API_BASE = "https://api.weather.gov"

# Headers required by NWS API
HEADERS = {
    "User-Agent": "(Naples Weather Report Generator, contact@example.com)",
    "Accept": "application/json"
}

def get_grid_point():
    """
    Convert lat/lon to NWS grid point.
    This needs to be done once to get the forecast office and grid coordinates.
    """
    url = f"{NWS_API_BASE}/points/{NAPLES_LAT},{NAPLES_LON}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extract the forecast URL
        forecast_url = data['properties']['forecast']
        grid_id = data['properties']['gridId']
        grid_x = data['properties']['gridX']
        grid_y = data['properties']['gridY']

        print(f"✓ Grid point: {grid_id} ({grid_x},{grid_y})")
        return forecast_url

    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching grid point: {e}")
        return None

def fetch_forecast(forecast_url):
    """
    Fetch the 7-day forecast from NWS.
    """
    try:
        response = requests.get(forecast_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        periods = data['properties']['periods']

        # Take up to 14 periods (7 days = 7 days + 7 nights)
        forecast_data = []
        for period in periods[:14]:
            forecast_data.append({
                'name': period['name'],
                'temperature': period['temperature'],
                'temperatureUnit': period['temperatureUnit'],
                'shortForecast': period['shortForecast'],
                'detailedForecast': period['detailedForecast'],
                'isDaytime': period['isDaytime'],
                'windSpeed': period.get('windSpeed', 'N/A'),
                'windDirection': period.get('windDirection', 'N/A'),
                'icon': period.get('icon', '')
            })

        print(f"✓ Fetched {len(forecast_data)} forecast periods")
        return forecast_data

    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching forecast: {e}")
        return None

def save_weather_data(forecast_data):
    """
    Save weather data to .tmp directory.
    """
    # Ensure .tmp directory exists
    tmp_dir = Path(__file__).parent.parent / '.tmp'
    tmp_dir.mkdir(exist_ok=True)

    output_file = tmp_dir / 'naples_weather_data.json'

    weather_data = {
        'location': 'Naples, Florida',
        'coordinates': {
            'lat': NAPLES_LAT,
            'lon': NAPLES_LON
        },
        'fetchedAt': datetime.now().isoformat(),
        'forecast': forecast_data
    }

    with open(output_file, 'w') as f:
        json.dump(weather_data, f, indent=2)

    print(f"✓ Saved weather data to {output_file}")
    return output_file

def main():
    print("Fetching Naples, FL weather data from National Weather Service...")
    print(f"Location: {NAPLES_LAT}, {NAPLES_LON}")
    print()

    # Step 1: Get grid point
    forecast_url = get_grid_point()
    if not forecast_url:
        print("Failed to get grid point. Exiting.")
        return 1

    # Step 2: Fetch forecast
    forecast_data = fetch_forecast(forecast_url)
    if not forecast_data:
        print("Failed to fetch forecast. Exiting.")
        return 1

    # Step 3: Save data
    output_file = save_weather_data(forecast_data)

    print()
    print("=" * 50)
    print("Weather data fetched successfully!")
    print(f"Next 7 days starting with: {forecast_data[0]['name']}")
    print(f"Data saved to: {output_file}")
    print("=" * 50)

    return 0

if __name__ == "__main__":
    exit(main())
