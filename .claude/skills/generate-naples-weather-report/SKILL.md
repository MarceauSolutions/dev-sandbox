---
name: generate-naples-weather-report
description: Generate modern, professional weekly weather reports for Naples, Florida with visual PDF output
allowed-tools: ["Bash(python:*)"]
---

# Generate Naples Weather Report

## Overview

This skill was deployed from the DOE development environment.

**Source Directive:** `directives/generate_naples_weather_report.md`

Generate modern, professional weekly weather reports for Naples, Florida with visual PDF output

## When to use

This skill is automatically triggered based on the description above. Claude will detect when your request matches this skill's capabilities.

## Execution Scripts

This skill uses the following execution scripts:

- `execution/generate_naples_weather_report.py` (create this script)


## Instructions

For detailed implementation instructions, refer to the source directive:

**Directive:** [generate_naples_weather_report.md](../../directives/generate_naples_weather_report.md)

The directive contains:
- Goal and purpose
- Input requirements
- Step-by-step process
- Output format
- Edge cases and error handling
- API considerations
- Best practices

## Usage

python execution scripts

## Deployment Information

- **Deployed:** 2026-01-05 10:48:47
- **Source:** DOE development environment
- **Status:** Production-ready

## Notes

This skill references the directive in `directives/` for complete documentation.
All execution logic is in deterministic Python scripts in `execution/`.

Intermediate files are stored in `.tmp/` and are not committed to version control.
