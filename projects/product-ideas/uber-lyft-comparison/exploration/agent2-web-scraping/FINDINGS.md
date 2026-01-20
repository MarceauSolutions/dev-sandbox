# Agent 2: Web Scraping Research - FINDINGS

**Mission**: Research web scraping Uber.com and Lyft.com for price estimates

**Date**: 2026-01-12

---

## Executive Summary

**Feasibility**: ❌ **NOT RECOMMENDED**

**Key Finding**: Web scraping Uber and Lyft is **technically possible but legally prohibited** and **extremely high-maintenance**.

**Fatal Flaws**:
1. **Terms of Service Violations**: Both Uber and Lyft explicitly prohibit web scraping in their Terms of Service
2. **High Maintenance Risk**: Heavily JavaScript-dependent sites built with React - scrapers break frequently when UIs change
3. **Anti-Scraping Measures**: Requires headless browsers (slow), vulnerable to CAPTCHA, rate limiting, and IP blocking
4. **Legal Risk**: Uber has sued competitors for scraping; this approach could expose users to legal liability

**Recommendation**: ⭐ (1/5 stars) - **Do NOT use this approach**

---

## Research Findings

### 1. Legal Analysis ⚠️

#### Uber Terms of Service

**Status**: ❌ **Explicitly Prohibited**

Uber's Terms of Service prohibit:
- Scraping or making Uber's services available for commercial use
- Aggregating Uber with competitors
- Any use that "competes with Uber or tries to drive traffic away from Uber"

**API Terms**: Even for developers using Uber's official API, they must agree NOT to include Uber API data in any tool that Uber deems competitive. Uber reserves the right to determine what is "acceptable" and can revoke API access at any time.

**Enforcement**: Uber actively blocks API access for services they deem non-compliant. Failure to comply can result in temporary or permanent account blocking.

**Real-World Precedent**: Uber has conducted extensive scraping operations against competitors (including Lyft) and has been involved in litigation regarding data scraping. Uber's subsidiary Cornershop was sued by Instacart for content scraping and settled the case, agreeing to stop using scraped data.

**Sources**:
- [Uber Developer Terms of Use](https://developer.uber.com/docs/riders/terms-of-use)
- [Uber's Massive Scraping Program Collected Data About Competitors](https://gizmodo.com/ubers-massive-scraping-program-collected-data-about-com-1820887947)
- [Instacart vs. Uber's Cornershop: Content Scraping Lawsuit](https://www.theinformation.com/briefings/60171c)

#### Lyft Terms of Service

**Status**: ❌ **Explicitly Prohibited**

Lyft's Terms of Service explicitly prohibit the use of:
> "any robot, spider, site search/retrieval application, or other manual or automatic device or process to retrieve, index, scrape, 'data mine', copy, access, acquire information, generate impressions or clicks, input or store information, search, monitor any portion of the Lyft Platform, or in any way reproduce or circumvent the navigational structure or presentation of the Lyft Platform or its contents."

**Sources**:
- [Lyft Terms of Service](https://www.lyft.com/terms)

#### Legal Risk Assessment

**Verdict**: ⚠️ **HIGH LEGAL RISK**

- Both companies explicitly prohibit scraping in their Terms of Service
- Uber has demonstrated willingness to pursue legal action against scrapers (Cornershop case)
- Terms of Service violations could result in:
  - Account termination
  - Cease and desist letters
  - Potential lawsuits for ToS violations
  - IP blocking and legal costs

**Enforceability Note**: While some argue that ToS prohibitions have limited legal enforceability, the risk remains significant. Even if not criminally liable, users could face civil lawsuits and account bans.

---

### 2. Technical Feasibility

#### Can We Access Price Estimates Without Login?

**Uber.com**: ✅ **Yes, but recently changed**

- Official price estimator at [uber.com/global/en/price-estimate/](https://www.uber.com/global/en/price-estimate/)
- **Recent Change**: Uber NOW requires login to view prices (as of a few weeks ago)
- Previous versions allowed guest access, but this has been intentionally blocked
- Third-party calculators (like 247 Calculator) still provide estimates without login
- Uber has a "Guest Trips Estimates API" for developers, but requires API access

**Lyft.com**: ⚠️ **Limited Guest Access**

- Official fare estimator at [lyft.com/rider/fare-estimate](https://www.lyft.com/rider/fare-estimate)
- Primary page is a signup funnel (phone number collection)
- Actual fare estimates require app download or separate navigation
- Third-party calculators (like lyftrideestimate.com, fareestimate.com) exist
- More focused on driving app downloads than providing web-based estimates

**Conclusion**: Uber recently locked down guest access (forcing login), making scraping more complex. Lyft primarily pushes users to download the app rather than providing web-based estimates.

**Sources**:
- [Uber Price Estimate Tool](https://www.uber.com/global/en/price-estimate/)
- [Uber Fare Estimator Now Requires Login](https://www.uberpeople.net/threads/uber-fare-estimator-now-requires-the-user-to-log-into-uber-account-or-google-account.489078/)
- [Lyft Fare Estimate Page](https://www.lyft.com/rider/fare-estimate)
- [Free Lyft Fare Estimator (Third-Party)](https://lyftrideestimate.com/)

#### HTML Structure: Easy to Scrape or Obfuscated/Dynamic?

**Uber.com**: ⚠️ **Heavily JavaScript-Dependent (React)**

**Technical Analysis**:
- Built with **React** (heavily client-side rendered)
- Uses **Fusion.js** (Uber's open-source web framework)
- Server-side rendering (SSR) + client-side hydration
- Inline JSON configuration data embedded in HTML
- CSS-in-JS with dynamic utility classes (css-bIdYaZ, css-jpTJNR, etc.)
- "Louvre" block system for managing dynamic content
- Analytics and tracking infrastructure throughout

**Form Elements**:
- Pickup location input: "Enter pickup location"
- Destination input: "Where to?"
- "See prices" submit button
- Uses "COMBINED_PICKER" variant for location entry

**Scraping Complexity**: 🔴 **High**
- Requires JavaScript execution (headless browser required)
- Dynamic class names change frequently
- Content loaded via React component lifecycle
- State management makes direct HTML parsing impossible

**Lyft.com**: ⚠️ **Even More Complex (React + Next.js)**

**Technical Analysis**:
- Built with **React** + **Next.js**
- Styled-components (CSS-in-JS)
- Large embedded JSON data for configuration
- Feature flags controlling content display
- Complex A/B testing framework
- Primary page is signup funnel, NOT price estimator

**Form Elements**:
- Phone number collection (primary CTA)
- Country code dropdown
- Links to separate fare estimate tools
- Actual pricing requires app download or separate navigation

**Scraping Complexity**: 🔴 **Very High**
- Requires JavaScript execution
- Price estimates NOT on main landing page
- Multiple page navigations required
- Dynamic content based on URL parameters and feature flags

**Conclusion**: Both sites are heavily React-based with dynamic rendering. Simple HTML parsing (BeautifulSoup) will NOT work - headless browsers (Puppeteer, Playwright, Selenium) are absolutely required.

**Sources**:
- [Uber's Fusion.js Web Framework](https://www.uber.com/blog/fusionjs-web-framework/)
- [Building m.uber: High-Performance Web App](https://www.uber.com/en-PT/blog/m-uber/)
- [JavaScript Rendering with Headless Browsers](https://docs.zenrows.com/universal-scraper-api/features/js-rendering)

---

### 3. Anti-Scraping Measures

#### What Anti-Scraping Techniques Are Used?

**Common Techniques** (based on industry standards, not Lyft/Uber-specific):

1. **Rate Limiting**
   - Servers track IP addresses and count requests per time window
   - Typical limit: 10-100 requests per minute
   - Exceeding limit triggers HTTP 429 "Too Many Requests" error
   - May escalate to temporary or permanent IP bans

2. **IP Blocking**
   - Websites monitor request volume from single IP addresses
   - High traffic from one IP triggers CAPTCHA or block
   - Can result in permanent blacklisting

3. **CAPTCHA Challenges**
   - Anti-bot providers (like Imperva Incapsula) assign "trust scores" to IP addresses
   - Low trust scores trigger CAPTCHA challenges
   - CAPTCHA is a clear signal that bot has been detected
   - Bypassing CAPTCHA requires additional tools (CapMonster, 2Captcha) - adds cost and complexity

4. **User-Agent Detection**
   - Servers check User-Agent header to identify bots
   - Default headless browser User-Agents are easily flagged
   - Requires User-Agent rotation to appear human-like

5. **JavaScript Challenges**
   - Sites may require JavaScript execution to prove it's a real browser
   - Headless browsers can be detected via missing browser APIs
   - Advanced anti-bot systems check for headless browser signatures

**Bypass Methods** (increases complexity and cost):
- **Proxy Rotation**: Use rotating residential proxies ($$$)
- **Request Timing**: Random delays, backoffs, retries to mimic human behavior
- **User-Agent Rotation**: Rotate User-Agent strings
- **Headless Browser Detection Evasion**: Use puppeteer-extra-plugin-stealth
- **CAPTCHA Solving Services**: 2Captcha, CapMonster ($0.001-$0.003 per solve)

**Uber/Lyft Specific**:
- Uber recently locked down guest access (requires login) - likely to combat scraping
- Both companies use sophisticated anti-bot infrastructure (given their scale)
- No public documentation of specific anti-scraping measures, but safe to assume industry-standard protections are in place

**Sources**:
- [Rate Limit in Web Scraping: How It Works and Bypass Methods](https://scrape.do/blog/web-scraping-rate-limit/)
- [5 Proven Ways to Bypass CAPTCHA in Python](https://scrapfly.io/blog/posts/how-to-bypass-captcha-while-web-scraping-in-2024)
- [Stop Getting Blocked: Common Web-Scraping Mistakes](https://www.firecrawl.dev/blog/web-scraping-mistakes-and-fixes)
- [How to Bypass Imperva Incapsula Anti-Scraping](https://scrapfly.io/blog/posts/how-to-bypass-imperva-incapsula-anti-scraping)

---

### 4. Maintenance Risk: How Often Do Scrapers Break?

#### Evidence from Existing Scraper Projects

**GitHub Analysis**:

I searched for existing Uber/Lyft scraper projects on GitHub to understand maintenance burden:

**Active/Maintained Projects**:
- [fiezt/Uber_Lyft_Scraping](https://github.com/fiezt/Uber_Lyft_Scraping) - Scripts for scraping pricing via APIs (not web scraping)
- [gsunit/Extreme-Uber-Eats-Scraping](https://github.com/gsunit/Extreme-Uber-Eats-Scraping) - Scraped 1.5M restaurants (Uber Eats, not ride pricing)
- [justinshapiro/Uber-Lyft-Data-Capture-Utility](https://github.com/justinshapiro/Uber-Lyft-Data-Capture-Utility) - Uses official APIs (not web scraping)

**Abandoned Projects**:
- [joshhunt/uber](https://github.com/joshhunt/uber) - Scraper for trip data, **no longer maintained** (users redirected to fork)

**Key Insights**:
- Most "scraper" projects actually use **official APIs**, not web scraping
- Web scraping projects tend to be **abandoned** (joshhunt/uber)
- Active projects focus on **API-based** data collection, NOT web scraping
- This suggests web scraping is **too unreliable** for production use

#### Industry Evidence: UI Changes Break Scrapers

**Google Scraper Example** (analogous):
- On January 15, 2025, Google made changes requiring browser rendering for search results
- This **immediately affected the entire data extraction community**
- Scrapers that worked for years broke overnight
- Required complete rewrites to use headless browsers

**Uber/Lyft Specific**:
- Uber recently changed price estimator to **require login** (within last few weeks)
- This immediately breaks any guest-access scrapers
- Shows Uber actively makes changes that affect scraping
- No public timeline, but changes can happen **without warning**

**React-Based Sites**:
- React apps frequently update component structures
- CSS class names are auto-generated and change with each build
- UI redesigns require complete scraper rewrites
- Uber uses Fusion.js (their own framework) - custom updates likely

**Maintenance Burden Estimate**:
- **Optimistic**: Breaks every 3-6 months (minor fixes)
- **Realistic**: Breaks every 1-3 months (moderate refactoring)
- **Pessimistic**: Breaks weekly or even daily during active development periods
- **Worst case**: Companies detect scraping and intentionally obfuscate (ongoing cat-and-mouse game)

**Conclusion**: 🔴 **Very High Maintenance Risk**

Web scrapers for Uber/Lyft would require **constant monitoring and updates**. React-based sites with dynamic class names and frequent UI updates make scraping extremely fragile.

**Sources**:
- [Has Your Google Scraper Stopped Working?](https://www.zyte.com/blog/has-your-google-scraper-stopped-working/)
- [Uber Fare Estimator Now Requires Login](https://www.uberpeople.net/threads/uber-fare-estimator-now-requires-the-user-to-log-into-uber-account-or-google-account.489078/)
- [GitHub: Uber/Lyft Scraping Projects](https://github.com/fiezt/Uber_Lyft_Scraping)

---

### 5. Required Tools

#### Headless Browser Options

Since both Uber and Lyft are heavily JavaScript-dependent, a **headless browser** is absolutely required.

**Tool Comparison** (Puppeteer vs Selenium vs Playwright):

| Feature | Puppeteer | Playwright | Selenium |
|---------|-----------|------------|----------|
| **Speed** | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐ Slower |
| **Browser Support** | Chrome only | Chrome, Firefox, Safari | All browsers |
| **Language Support** | JavaScript, Python | JavaScript, Python, C# | Python, Java, C#, Ruby |
| **Performance** | 849ms (benchmark) | Similar to Puppeteer | 1,008ms (30% slower) |
| **Bot Detection Evasion** | Good (with stealth plugin) | Good | Poor |
| **Learning Curve** | Easy | Easy | Moderate |
| **Best For** | Chrome-only scraping | New projects, multi-browser | Enterprise, multi-language |

**Recommendation**: **Playwright** or **Puppeteer** for this use case

- **Playwright**: Best for new projects, multi-browser support, modern features
- **Puppeteer**: Best for Chrome-only, has puppeteer-extra-plugin-stealth for bot detection evasion
- **Selenium**: Avoid (slower, worse bot detection evasion)

**Additional Tools Needed**:

1. **Proxy Rotation Service** ($$$)
   - Residential proxies: $5-15 per GB
   - Required to avoid IP bans
   - Examples: BrightData, Smartproxy, Oxylabs

2. **CAPTCHA Solving Service** ($$$)
   - 2Captcha, CapMonster: $0.001-$0.003 per solve
   - Required when anti-bot systems trigger challenges

3. **Bot Detection Evasion**:
   - puppeteer-extra-plugin-stealth (for Puppeteer)
   - Playwright stealth mode
   - User-Agent rotation libraries

4. **Rate Limiting / Request Throttling**:
   - Custom delay logic to avoid rate limits
   - Exponential backoff on errors
   - Random jitter to mimic human behavior

**Sources**:
- [Puppeteer vs Selenium vs Playwright: Best Tool?](https://www.promptcloud.com/blog/puppeteer-vs-selenium-vs-playwright-for-web-scraping/)
- [Playwright vs Puppeteer: Which to Choose in 2025?](https://www.browserstack.com/guide/playwright-vs-puppeteer)
- [Best Web Scraping Tools in 2026](https://scrapfly.io/blog/posts/best-web-scraping-tools)

---

### 6. Speed: Can We Get Results in < 5 Seconds?

**Headless Browser Performance Benchmarks**:

- **Puppeteer**: 849ms for short scripts (benchmark)
- **Selenium**: 1,008ms for short scripts (30% slower)
- **Playwright**: Similar to Puppeteer (~850ms)

**However**, these benchmarks are for **simple scripts**. For Uber/Lyft scraping:

**Realistic Timeline**:
1. **Launch headless browser**: 1-2 seconds
2. **Navigate to price estimator page**: 1-2 seconds
3. **Wait for JavaScript to load**: 1-2 seconds
4. **Fill in pickup/dropoff locations**: 0.5-1 second
5. **Click "See prices" button**: 0.5 seconds
6. **Wait for price results to load**: 2-4 seconds (API calls to Uber/Lyft backend)
7. **Parse and extract price data**: 0.5 seconds

**Total Estimated Time**: **7-12 seconds per query**

**Optimization Potential**:
- Reuse browser instance (save 1-2 seconds on subsequent queries)
- Pre-load page (save 1-2 seconds)
- **Optimistic best case**: 5-7 seconds per query after first query

**Performance Issues**:
- Headless browsers are **much slower** than API requests (which take <1 second)
- Browsers add "seconds per page" while HTTP requests complete in "milliseconds"
- 95th percentile performance often exceeds 5 seconds
- Network latency, server response time, JavaScript execution all add overhead

**Conclusion**: ⚠️ **Unlikely to consistently hit <5 seconds**

First query: 7-12 seconds
Subsequent queries (reusing browser): 5-7 seconds (optimistic)

This is **significantly slower** than official API approaches (which return results in <1 second).

**Sources**:
- [Optimize Performance of Headless Browser Scraping](https://www.linkedin.com/advice/3/how-do-you-optimize-performance-speed-headless-browser)
- [Is Your Web Scraper Slow? Here's Why](https://www.goproxy.com/blog/is-web-scraper-slow-reasons-fixes/)
- [Headless Browsers vs. API Scraping: When to Use Each](https://crawlbase.com/blog/headless-browsers-vs-api-scraping/)

---

## Technical Details: How It Would Work

**High-Level Architecture**:

```
1. User enters pickup + dropoff locations
2. Launch Puppeteer/Playwright headless browser (with stealth plugin)
3. Navigate to Uber/Lyft price estimator pages
4. Fill in location inputs programmatically
5. Click "See prices" button
6. Wait for JavaScript to execute and prices to load
7. Parse DOM to extract price data
8. Return results to user
```

**Pseudocode** (Python + Playwright):

```python
from playwright.sync_api import sync_playwright

def get_uber_price(pickup, dropoff):
    with sync_playwright() as p:
        # Launch browser (with stealth mode to avoid detection)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to price estimator
        page.goto('https://www.uber.com/global/en/price-estimate/')

        # Fill in pickup location
        page.fill('input[placeholder="Enter pickup location"]', pickup)
        page.wait_for_timeout(1000)  # Wait for autocomplete
        page.keyboard.press('Enter')

        # Fill in dropoff location
        page.fill('input[placeholder="Where to?"]', dropoff)
        page.wait_for_timeout(1000)
        page.keyboard.press('Enter')

        # Click "See prices" button
        page.click('button:has-text("See prices")')

        # Wait for prices to load (may need to handle login popup)
        page.wait_for_selector('.price-estimate-result', timeout=5000)

        # Extract price data from DOM
        prices = page.eval_on_selector_all('.price-estimate-result',
            'elements => elements.map(el => el.innerText)')

        browser.close()
        return prices
```

**Challenges**:
1. **Login Requirement**: Uber now requires login - would need to handle authentication
2. **CAPTCHA**: May trigger CAPTCHA challenges - need solving service
3. **Rate Limiting**: Frequent requests will trigger IP bans - need proxy rotation
4. **Dynamic Selectors**: CSS selectors change frequently - scraper breaks often
5. **Error Handling**: Network errors, timeouts, anti-bot detection all require robust handling

---

## Cost Analysis

### One-Time Setup Costs:
- **Development Time**: 20-40 hours to build robust scraper
  - Initial implementation: 8-12 hours
  - Error handling, retry logic: 4-8 hours
  - Anti-bot evasion setup: 4-8 hours
  - Testing and debugging: 4-12 hours

- **Tool Setup**: $0 (Puppeteer/Playwright are free and open-source)

### Ongoing Costs:

1. **Proxy Rotation Service**: $50-200/month
   - Residential proxies: ~$5-15 per GB
   - Estimate 10-40 GB/month for moderate usage

2. **CAPTCHA Solving**: $10-50/month
   - $0.001-$0.003 per CAPTCHA solve
   - Estimate 5,000-20,000 CAPTCHAs/month if heavily rate-limited

3. **Maintenance Time**: 4-16 hours/month
   - Fix broken scrapers when UI changes: 2-8 hours/month
   - Monitor for anti-bot detection: 1-4 hours/month
   - Update selectors and logic: 1-4 hours/month

4. **Server/Infrastructure**: $10-50/month
   - VPS to run headless browsers: DigitalOcean, AWS, etc.

**Total Monthly Cost**: $74-316/month + 4-16 hours maintenance time

**Annual Cost**: $888-3,792/year + 48-192 hours maintenance time

---

## Pros ✅

1. **No API Access Required**: Don't need to apply for/maintain official API credentials
2. **Access to Public Data**: Scraping publicly-visible web pages (though legally prohibited)
3. **Full Control**: Can extract exactly the data needed without API limitations
4. **Open-Source Tools**: Puppeteer/Playwright are free and well-documented

---

## Cons ❌

1. **Legal Violation**: Violates both Uber and Lyft Terms of Service
2. **Very High Maintenance**: React-based sites change frequently, breaking scrapers
3. **Slow Performance**: 7-12 seconds per query (vs <1 second for APIs)
4. **Expensive**: Proxy rotation + CAPTCHA solving = $74-316/month ongoing costs
5. **Unreliable**: Anti-bot systems can block scrapers without warning
6. **Login Required**: Uber now requires login (can't scrape as guest)
7. **Complex Implementation**: Requires headless browser, stealth plugins, proxy rotation, CAPTCHA solving
8. **Ethical Concerns**: Companies explicitly prohibit this; scraping undermines their business model
9. **Legal Risk**: Could face cease-and-desist letters, account bans, or lawsuits
10. **Detection Risk**: Uber/Lyft can detect and block scraping behavior at any time

---

## Risks ⚠️

### Legal Risks (🔴 HIGH):
- **Terms of Service Violation**: Both companies explicitly prohibit scraping
- **Lawsuit Potential**: Uber has sued competitors for scraping (Cornershop case)
- **Account Termination**: Accounts used for scraping will be banned
- **Cease and Desist**: Companies may send legal threats
- **Reputation Risk**: Public association with ToS violations

### Technical Risks (🔴 HIGH):
- **Frequent Breakage**: React apps change UI frequently, requiring constant maintenance
- **Anti-Bot Detection**: Sophisticated anti-scraping systems can block access
- **CAPTCHA Walls**: May require human intervention or expensive solving services
- **IP Blacklisting**: Scrapers can get IP addresses permanently banned
- **Performance Degradation**: Slow response times (7-12 seconds) hurt user experience

### Business Risks (🔴 HIGH):
- **Unreliable Service**: Scrapers can break at any time, leaving users stranded
- **Maintenance Burden**: Requires dedicated developer time to keep working
- **Cost Escalation**: Proxy and CAPTCHA costs can spike unexpectedly
- **Competitive Disadvantage**: Official API approaches are faster, more reliable, and legal

---

## Code Example: Proof of Concept

**Note**: This code is provided for **educational purposes only** to demonstrate technical feasibility. Using this code violates Uber and Lyft's Terms of Service and is **NOT recommended**.

```python
#!/usr/bin/env python3
"""
Web Scraper for Uber Price Estimates (EDUCATIONAL ONLY - DO NOT USE)

WARNING: This violates Uber's Terms of Service. Use at your own risk.

Dependencies:
pip install playwright
playwright install chromium
pip install playwright-stealth
"""

from playwright.sync_api import sync_playwright
import time
import random

def get_uber_price_estimate(pickup: str, dropoff: str) -> dict:
    """
    Scrape Uber price estimate using Playwright.

    Args:
        pickup: Pickup location (e.g., "San Francisco Airport")
        dropoff: Dropoff location (e.g., "Downtown San Francisco")

    Returns:
        dict: {
            'success': bool,
            'prices': list of dicts with ride types and prices,
            'error': str (if success=False)
        }
    """

    try:
        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox'
                ]
            )

            # Create context with realistic headers
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US'
            )

            page = context.new_page()

            # Navigate to price estimator
            print("Navigating to Uber price estimator...")
            page.goto('https://www.uber.com/global/en/price-estimate/',
                     wait_until='networkidle')

            # Random delay to appear human-like
            time.sleep(random.uniform(1.5, 3.0))

            # Fill in pickup location
            print(f"Entering pickup: {pickup}")
            pickup_input = page.locator('input[placeholder*="pickup"]').first
            pickup_input.fill(pickup)
            time.sleep(random.uniform(0.5, 1.5))

            # Wait for autocomplete and select first option
            page.keyboard.press('ArrowDown')
            time.sleep(random.uniform(0.3, 0.8))
            page.keyboard.press('Enter')
            time.sleep(random.uniform(1.0, 2.0))

            # Fill in dropoff location
            print(f"Entering dropoff: {dropoff}")
            dropoff_input = page.locator('input[placeholder*="Where"]').first
            dropoff_input.fill(dropoff)
            time.sleep(random.uniform(0.5, 1.5))

            # Wait for autocomplete and select first option
            page.keyboard.press('ArrowDown')
            time.sleep(random.uniform(0.3, 0.8))
            page.keyboard.press('Enter')
            time.sleep(random.uniform(1.0, 2.0))

            # Click "See prices" button
            print("Clicking 'See prices' button...")
            see_prices_btn = page.locator('button:has-text("See prices")').first
            see_prices_btn.click()

            # Wait for prices to load
            print("Waiting for price results...")
            time.sleep(random.uniform(3.0, 5.0))

            # CHALLENGE: Uber may show login modal here
            # This scraper will likely fail at this point due to login requirement

            # Attempt to extract price data
            # NOTE: Selectors will break when Uber updates their UI
            prices = []
            price_elements = page.locator('[data-testid*="price"]').all()

            for elem in price_elements:
                try:
                    ride_type = elem.locator('.ride-type').inner_text()
                    price = elem.locator('.price-amount').inner_text()
                    prices.append({
                        'ride_type': ride_type,
                        'price': price
                    })
                except:
                    pass

            browser.close()

            if prices:
                return {
                    'success': True,
                    'prices': prices,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'prices': [],
                    'error': 'Could not extract prices (likely due to login requirement or changed UI)'
                }

    except Exception as e:
        return {
            'success': False,
            'prices': [],
            'error': f'Scraping failed: {str(e)}'
        }


# Test the scraper (EDUCATIONAL ONLY)
if __name__ == '__main__':
    result = get_uber_price_estimate(
        pickup='San Francisco International Airport',
        dropoff='Union Square, San Francisco'
    )

    print("\n--- RESULT ---")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Prices: {result['prices']}")
    else:
        print(f"Error: {result['error']}")
```

**Why This Code Will Likely Fail**:
1. **Login Requirement**: Uber now requires login - scraper can't proceed as guest
2. **CAPTCHA**: Anti-bot systems will likely trigger CAPTCHA challenge
3. **Dynamic Selectors**: CSS selectors like `[data-testid*="price"]` change frequently
4. **IP Blocking**: Repeated scraping attempts will get IP address banned
5. **Bot Detection**: Headless browser detection can identify this as a bot

**Making It "Work" Would Require**:
- Account credentials (violates ToS to use for scraping)
- CAPTCHA solving service (2Captcha, CapMonster)
- Proxy rotation to avoid IP bans
- Stealth plugins to evade bot detection
- Constant maintenance as selectors change
- **Still violates Terms of Service**

---

## RECOMMENDATION: ⭐ (1 out of 5 stars)

### Overall Score: 1/5 ⭐

**DO NOT USE THIS APPROACH**

### Scoring Breakdown:

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| **Feasibility** | 2/5 | Technically possible but requires extensive workarounds |
| **Legal** | 0/5 | ❌ Violates both Uber and Lyft Terms of Service |
| **Cost** | 2/5 | $74-316/month + dev time = expensive |
| **Reliability** | 1/5 | Breaks frequently, requires constant maintenance |
| **Maintenance** | 1/5 | 4-16 hours/month fixing broken scrapers |
| **Speed** | 2/5 | 7-12 seconds per query (vs <1s for APIs) |
| **User Experience** | 2/5 | Slow, unreliable, prone to errors |
| **Scalability** | 2/5 | Expensive to scale (proxy + CAPTCHA costs) |

**Average: 1.5/5 stars** (rounded down to 1/5)

---

### Why This Approach Fails:

1. **Legal Showstopper**: Both companies explicitly prohibit scraping in ToS
2. **Technical Fragility**: React-based sites change frequently, breaking scrapers constantly
3. **Poor Economics**: $74-316/month + 4-16 hours maintenance >> cost of official APIs
4. **Slow Performance**: 7-12 seconds per query is unacceptable for real-time price comparison
5. **High Risk**: Legal liability, account bans, IP blacklisting, reputation damage

---

### Better Alternatives:

1. **Official APIs (Agent 1)**: Uber and Lyft both offer developer APIs - fast, reliable, legal
2. **Third-Party Aggregator APIs (Agent 3)**: Services that legally aggregate ride-hailing data
3. **Mobile App Integration (Agent 4)**: Explore mobile SDK or deep linking approaches

---

## Conclusion

Web scraping Uber and Lyft is **technically possible but practically inadvisable**. The combination of:
- Legal prohibition (ToS violations)
- High maintenance burden (React-based sites)
- Poor performance (7-12 seconds vs <1s for APIs)
- Significant costs ($74-316/month + dev time)
- Unreliability (anti-bot detection, frequent breakage)

...makes this approach **unsuitable for production use**.

**Recommendation**: Explore official API approaches (Agent 1) or third-party aggregators (Agent 3) instead.

---

## Sources

### Legal Analysis:
- [Uber Developer Terms of Use](https://developer.uber.com/docs/riders/terms-of-use)
- [Lyft Terms of Service](https://www.lyft.com/terms)
- [How Uber Uses API Restrictions to Block Competition](https://www.benedelman.org/news-053116/)
- [Uber's Massive Scraping Program](https://gizmodo.com/ubers-massive-scraping-program-collected-data-about-com-1820887947)
- [Instacart vs Uber Cornershop Scraping Lawsuit](https://www.theinformation.com/briefings/60171c)
- [Web Scraping vs Terms of Use](https://seidmanlawgroup.com/web-scraping-vs-terms-of-use/)
- [Is Web Scraping Legal?](https://www.scrapingbee.com/blog/is-web-scraping-legal/)

### Technical Feasibility:
- [Uber Price Estimate Tool](https://www.uber.com/global/en/price-estimate/)
- [Get a Price Estimate | Uber Help](https://help.uber.com/en/riders/article/get-a-price-estimate-for-your-trip?nodeId=cc1efc16-df15-47f3-8057-61c2b75ea529)
- [Uber Fare Estimator Now Requires Login](https://www.uberpeople.net/threads/uber-fare-estimator-now-requires-the-user-to-log-into-uber-account-or-google-account.489078/)
- [How to Estimate Lyft Ride Cost](https://help.lyft.com/hc/en-us/all/articles/115013080308-How-to-estimate-the-cost-of-a-Lyft-ride)
- [Lyft Fare Estimate Page](https://www.lyft.com/rider/fare-estimate)
- [Free Lyft Fare Estimator (Third-Party)](https://lyftrideestimate.com/)
- [Fare Estimate: Compare Ride-Sharing Apps](https://fareestimate.com/)

### Web Architecture:
- [Uber's Fusion.js Web Framework](https://www.uber.com/blog/fusionjs-web-framework/)
- [Building m.uber: High-Performance Web App](https://www.uber.com/en-PT/blog/m-uber/)
- [JavaScript Rendering with Headless Browsers](https://docs.zenrows.com/universal-scraper-api/features/js-rendering)
- [Headless Chrome: Server-Side Rendering](https://developer.chrome.com/docs/puppeteer/ssr/)

### Anti-Scraping Techniques:
- [Rate Limit in Web Scraping](https://scrape.do/blog/web-scraping-rate-limit/)
- [5 Proven Ways to Bypass CAPTCHA](https://scrapfly.io/blog/posts/how-to-bypass-captcha-while-web-scraping-in-2024)
- [How to Bypass Imperva Incapsula](https://scrapfly.io/blog/posts/how-to-bypass-imperva-incapsula-anti-scraping)
- [Stop Getting Blocked: Web Scraping Mistakes](https://www.firecrawl.dev/blog/web-scraping-mistakes-and-fixes)
- [Rate Limiting Academy](https://docs.apify.com/academy/anti-scraping/techniques/rate-limiting)
- [Bypass Rate Limit Like a Pro](https://www.zenrows.com/blog/web-scraping-rate-limit)

### Scraping Tools Comparison:
- [Puppeteer vs Selenium vs Playwright](https://www.promptcloud.com/blog/puppeteer-vs-selenium-vs-playwright-for-web-scraping/)
- [Best Web Scraping Tools in 2026](https://scrapfly.io/blog/posts/best-web-scraping-tools)
- [Playwright vs Puppeteer (2025)](https://www.browserstack.com/guide/playwright-vs-puppeteer)
- [Selenium vs Puppeteer vs Playwright Comparison](https://www.vocso.com/blog/dynamic-web-scraping-tools-comparison-selenium-vs-puppeteer-vs-playwright/)
- [Playwright vs Puppeteer for Web Scraping](https://brightdata.com/blog/web-data/puppeteer-vs-playwright)

### Performance & Speed:
- [Optimize Headless Browser Performance](https://www.linkedin.com/advice/3/how-do-you-optimize-performance-speed-headless-browser)
- [What Is a Headless Browser?](https://www.zenrows.com/blog/headless-browser-scraping)
- [Is Your Web Scraper Slow?](https://www.goproxy.com/blog/is-web-scraper-slow-reasons-fixes/)
- [Headless Browsers vs API Scraping](https://crawlbase.com/blog/headless-browsers-vs-api-scraping/)
- [Best Headless Browsers for Web Scraping](https://latenode.com/blog/best-headless-browsers-for-web-scraping-tools-and-examples)

### GitHub Projects:
- [fiezt/Uber_Lyft_Scraping](https://github.com/fiezt/Uber_Lyft_Scraping)
- [gsunit/Extreme-Uber-Eats-Scraping](https://github.com/gsunit/Extreme-Uber-Eats-Scraping)
- [joshhunt/uber (no longer maintained)](https://github.com/joshhunt/uber)
- [justinshapiro/Uber-Lyft-Data-Capture-Utility](https://github.com/justinshapiro/Uber-Lyft-Data-Capture-Utility)

### Scraper Breakage:
- [Has Your Google Scraper Stopped Working?](https://www.zyte.com/blog/has-your-google-scraper-stopped-working/)

---

**END OF FINDINGS**
