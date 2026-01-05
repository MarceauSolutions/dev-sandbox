---
name: naples-weather-report
description: Generates a modern, professional weekly weather report for Naples, Florida with visual PDF output. Use when user asks to generate, create, or produce a Naples weather report, weekly forecast, or weather summary.
allowed-tools: Bash(python:*)
---

# Naples Florida Weekly Weather Report Generator

## Overview

This Skill generates a professional weekly weather report for Naples, Florida. It fetches real-time data from the National Weather Service and produces a modern PDF report with visual design matching corporate templates.

## When to use

Use this Skill when the user asks to:
- Generate a Naples weather report
- Create a weekly forecast for Naples, FL
- Produce the weekly weather summary
- Make a Naples weather PDF
- Get Naples weather information in report format

## Instructions

### 1. Fetch Weather Data

Run the weather data collection script:

```bash
python execution/fetch_naples_weather.py
```

This script:
- Fetches 7-day forecast from National Weather Service API (free, no auth required)
- Gets Naples, FL specific data (26.1420° N, 81.7948° W)
- Saves to `.tmp/naples_weather_data.json`

### 2. Generate PDF Report

Run the report generation script:

```bash
python execution/generate_weather_report.py
```

This script:
- Reads weather data from `.tmp/naples_weather_data.json`
- Downloads Naples hero image (cached after first run)
- Generates modern PDF with:
  - Orange and dark blue color scheme
  - Circular hero image
  - 7-day forecast with temperatures and conditions
  - Weather icons and visual indicators
- Outputs to `.tmp/naples_weather_report_YYYYMMDD.pdf`

### 3. Provide Report Location

Tell the user where the report was saved:

```
Report generated: .tmp/naples_weather_report_YYYYMMDD.pdf

You can open it with:
open .tmp/naples_weather_report_YYYYMMDD.pdf
```

## Error Handling

**Missing dependencies:**
If you get import errors, install required packages:
```bash
pip install reportlab pillow requests
```

**API rate limits:**
National Weather Service limits requests. If you hit rate limits, wait 60 seconds between requests.

**Network issues:**
If weather fetch fails, check internet connection and NWS API status at https://www.weather.gov/documentation/services-web-api

## Output Format

The generated PDF includes:
- **Header**: "WEEKLY WEATHER REPORT" with date
- **Hero Image**: Circular Naples/Florida coastal scene
- **7-Day Forecast**: Each day shows:
  - Day name (Today, Monday, Tuesday, etc.)
  - High/low temperature
  - Weather condition (Sunny, Cloudy, Rain, etc.)
  - Weather emoji icon
- **Footer**: Data source attribution and generation timestamp

## Best Practices

- Run both scripts sequentially (fetch data first, then generate report)
- Report filename includes date (YYYYMMDD) for versioning
- Hero image is cached in `.tmp/` for faster subsequent runs
- All intermediate files stay in `.tmp/` directory
- Report is ready to email, print, or share as PDF

## Example Usage

User asks: "Generate the Naples weather report"

Your response:
1. Run `fetch_naples_weather.py`
2. Run `generate_weather_report.py`
3. Confirm success and provide file location

## Additional Resources

For detailed implementation, see:
- Directive: `directives/generate_naples_weather_report.md`
- Weather fetcher: `execution/fetch_naples_weather.py`
- Report generator: `execution/generate_weather_report.py`
