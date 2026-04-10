# Generate Naples Florida Weekly Weather Report

## Goal
Generate a modern, visually appealing weekly weather report for Naples, Florida using publicly available weather data.

## Inputs
- **Location**: Naples, Florida (coordinates: 26.1420° N, 81.7948° W)
- **Report Period**: Current week (7 days)
- **Template**: Modern design based on `.tmp/modern weekly report.PNG`

## Tools/Scripts
- `execution/fetch_naples_weather.py` - Fetches weather data from National Weather Service API (free, no API key required)
- `execution/generate_weather_report.py` - Generates visual report using the template design

## Process

### 1. Fetch Weather Data
Run the weather fetching script:
```bash
python execution/fetch_naples_weather.py
```

**What it does:**
- Uses National Weather Service API (weather.gov) - free, no authentication
- Gets 7-day forecast for Naples, FL
- Retrieves: temperature (high/low), conditions, precipitation chance, wind
- Saves data to `.tmp/naples_weather_data.json`

### 2. Generate Report
Run the report generation script:
```bash
python execution/generate_weather_report.py
```

**What it does:**
- Reads weather data from `.tmp/naples_weather_data.json`
- Uses template design from `.tmp/modern weekly report.PNG`
- Generates modern PDF/PNG report with:
  - Hero image (Naples, FL related)
  - "WEEKLY WEATHER REPORT" title
  - Current date
  - 7-day forecast with icons and details
- Saves to `.tmp/naples_weather_report_YYYYMMDD.pdf`

## Outputs
- **Intermediate**: `.tmp/naples_weather_data.json` - Raw weather data
- **Deliverable**: `.tmp/naples_weather_report_YYYYMMDD.pdf` - Final report

## Edge Cases & Learnings

### API Considerations
- **Rate Limits**: NWS API is free but rate-limited. Don't call more than once per minute.
- **Forecast Updates**: Weather forecasts update every 1-6 hours. Cache data appropriately.
- **Grid Points**: NWS API requires converting lat/lon to grid points first. Cache this lookup.

### Data Handling
- **Missing Data**: If API is down, use cached data from previous successful fetch
- **Incomplete Forecast**: Sometimes NWS doesn't have full 7-day data. Handle gracefully.
- **Weather Icons**: Map NWS condition codes to weather icons

### Report Generation
- **Image Quality**: Use high-res hero images (1920x1080 minimum)
- **Date Format**: Match template style (e.g., "23 JANUARY 2023")
- **Font Consistency**: Use bold sans-serif for headers

## Example Usage

```bash
# Generate today's weather report
python execution/fetch_naples_weather.py
python execution/generate_weather_report.py

# Output: .tmp/naples_weather_report_20260105.pdf
```

## Automation Options
- **Schedule**: Run weekly on Sundays at 8 AM
- **Webhook**: Can be triggered via Modal webhook for on-demand generation
- **Email**: Can be extended to email the report automatically

## Dependencies
```
requests>=2.31.0
pillow>=10.0.0
reportlab>=4.0.0
python-dotenv>=1.0.0
```

## Notes
- NWS API documentation: https://www.weather.gov/documentation/services-web-api
- No API key required
- All data is public domain
- Template maintains modern corporate aesthetic from reference image
