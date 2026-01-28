# Insurance Savings App — Product Requirements Document

**Project:** AutoInsure Saver
**Owner:** William Marceau
**Created:** 2026-01-28
**Status:** In Development

---

## Vision
An automated insurance monitoring and savings optimization app that continuously scans for better car insurance deals, compares prices, and notifies the user when switching would save money.

## Goals
1. Never overpay on car insurance again
2. Automatically detect new promotional deals across carriers
3. Provide actionable savings recommendations
4. Track insurance costs over time

## Tech Stack
- **Backend:** Python FastAPI
- **Database:** SQLite (via SQLAlchemy)
- **Scraping:** BeautifulSoup + httpx (async HTTP)
- **Scheduling:** APScheduler
- **Notifications:** Telegram Bot API (via Clawdbot)
- **Frontend:** Jinja2 templates + HTMX for interactivity

---

## User Stories

### Phase 1 — MVP

**S1: User Profile Setup**
- User can enter vehicle info (year, make, model, VIN)
- User can enter current policy details (carrier, premium, deductible, coverage levels, renewal date)
- User can enter driving record (years licensed, accidents, tickets, credit score range)
- Data stored in SQLite

**S2: Insurance Carrier Promo Scanner**
- System scrapes major carrier promo pages on a schedule (2x daily)
- Carriers: GEICO, Progressive, State Farm, Allstate, USAA, Liberty Mutual, Farmers, Nationwide, Travelers, American Family
- Detects new customer promos, seasonal deals, bundle discounts
- Stores deals in database with timestamps, terms, and estimated savings

**S3: Savings Calculator Engine**
- Deductible optimizer: calculates break-even on higher deductible
- Coverage audit: flags over-insurance (e.g., full collision on car worth < $5K)
- Discount checklist: identifies unclaimed discounts (defensive driving, low mileage, autopay, paperless, bundling, affiliations)
- Annual vs semi-annual payment comparison
- Rate creep detector: tracks premium changes over renewal periods

**S4: Notification System**
- Telegram alerts when new promos match user profile
- Renewal countdown notifications (60, 45, 30, 14, 7 days before)
- Monthly savings report
- Alert when estimated savings exceed configurable threshold (default $200/year)

**S5: Web Dashboard**
- View current policy details
- See active deals/promos
- Savings opportunities ranked by estimated savings
- Insurance cost history chart
- Discount checklist with completion status

### Phase 2 — Enhanced

**S6: Quote Aggregator Integration**
- Integration with comparison APIs (SmartFinancial, EverQuote)
- Automated quote requests based on user profile

**S7: Multi-Vehicle Support**
- Support for multiple vehicles
- Multi-car discount analysis

**S8: Historical Analytics**
- Price trend tracking across carriers
- Best time to switch analysis
- Market-wide premium trend visualization

---

## Data Model

### UserProfile
- id, name, email, telegram_chat_id
- created_at, updated_at

### Vehicle
- id, user_id, year, make, model, vin, annual_mileage, usage_type
- vehicle_value (estimated)

### CurrentPolicy
- id, user_id, carrier, policy_number
- monthly_premium, annual_premium, deductible
- coverage_liability, coverage_collision, coverage_comprehensive
- coverage_uninsured, coverage_medical
- start_date, renewal_date
- payment_frequency (monthly/semi-annual/annual)

### DrivingRecord
- id, user_id, years_licensed, age
- accidents_3yr, tickets_3yr
- credit_score_range, education_level
- homeowner, multi_car, defensive_driving_course

### InsuranceDeal
- id, carrier, deal_type, title, description
- estimated_savings_pct, promo_code
- start_date, end_date, url
- requirements, exclusions
- scraped_at, is_active

### SavingsRecommendation
- id, user_id, category, title, description
- estimated_annual_savings
- priority, action_required
- status (new/viewed/applied/dismissed)

### PremiumHistory
- id, user_id, carrier, premium_amount
- recorded_date, policy_period
