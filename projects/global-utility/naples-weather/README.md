# Naples Weather Report Generator

Automated weekly weather report generator for Naples, Florida with professional PDF output.

## Status: Development

## Features

| Feature | Script | Description |
|---------|--------|-------------|
| Weather Fetch | `fetch_naples_weather.py` | Get weather data from API |
| Report Generator | `generate_weather_report.py` | Create formatted PDF report |

## Directory Structure

```
naples-weather/
├── src/
│   ├── fetch_naples_weather.py
│   └── generate_weather_report.py
├── docs/
└── README.md
```

## Quick Start

```bash
python src/fetch_naples_weather.py
python src/generate_weather_report.py
```

## Skill Configuration

Located at: `.claude/skills/naples-weather-report/SKILL.md`

## Related Documentation

- Main directive: `directives/generate_naples_weather_report.md`
