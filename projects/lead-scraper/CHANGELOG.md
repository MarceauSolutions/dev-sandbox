# Changelog

All notable changes to the Lead Scraper project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0-dev] - 2026-01-14

### Added

- **Core Scraper Framework**
  - Google Places API integration for local business data
  - Yelp Fusion API integration as secondary source
  - Configurable rate limiting to avoid API bans
  - Progress saving for interrupted scrapes
  - Deduplication and lead merging from multiple sources

- **Lead Data Model**
  - Business name, contact info (email, phone, website)
  - Social media links (Facebook, Instagram, LinkedIn, Twitter)
  - Location data (address, city, state, zip, coordinates)
  - Business category and subcategories
  - Rating and review counts
  - Pain point identification

- **Pain Point Detection**
  - `no_website` - Business has no website
  - `outdated_website` - Website appears outdated
  - `no_online_booking` - No online booking capability
  - `few_reviews` / `no_reviews` - Limited social proof
  - `low_rating` - Below 3.5 star rating

- **CLI Interface**
  - `scrape` command with category/area filters
  - `export` command for CSV/JSON output
  - `stats` command for collection statistics
  - `filter` command for querying leads
  - `optout` command for managing opt-out list

- **Lead Enrichment Module**
  - Website analysis for email discovery
  - Social media link extraction
  - Pain point identification from website content
  - Respects robots.txt

- **Ethical Features**
  - Configurable rate limiting
  - Opt-out list management
  - Only collects publicly available information

- **Preconfigured Areas (SW Florida)**
  - Naples, FL
  - Fort Myers, FL
  - Bonita Springs, FL
  - Marco Island, FL
  - Estero, FL
  - Cape Coral, FL

- **Target Business Categories**
  - Gym / Fitness Center / Personal Trainer
  - Real Estate Agency
  - Moving Company
  - Restaurant / Cafe
  - Dental Office / Medical Spa
  - Salon / Beauty Services
  - Auto Repair
  - HVAC / Plumber / Electrician
  - Landscaping / Cleaning Service
  - Retail / E-commerce

### Documentation

- Created comprehensive workflow guide
- Added API setup instructions
- Documented cost estimation
- Included troubleshooting guide

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0-dev | 2026-01-14 | Initial development version |
