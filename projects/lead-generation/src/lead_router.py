#!/usr/bin/env python3
"""
lead_router.py — Lead Scoring + Routing Engine for AI Client Sprint

Scores every prospect 0–100 and assigns a routing tier based on industry fit,
company size, location, email quality, and decision-maker title.

ROUTING TIERS:
  Tier 1 (80–100): deep_personalized  — manual research before sending
  Tier 2 (50–79):  industry_batch     — industry template, name+company personalized
  Tier 3 (20–49):  generic_batch      — generic template, minimal personalization
  Skip   (<20):    skip               — wrong fit, do not contact

AUTO-DISQUALIFICATION (sets tier to Skip regardless of score):
  - B2B-only businesses (fire suppression, drone/aerial services, IT infrastructure,
    commercial electrical, commercial construction, telecom, wholesale)
  - Low phone-dependency (scheduled contract-based services where clients don't call in)

USAGE:
  python execution/lead_router.py --input <csv_path> --output <csv_path> [--tier 1|2|3|all]

INPUT CSV COLUMNS (Apollo format):
  company_name, contact_name, first_name, last_name, title, email, phone,
  industry, apollo_industry, employee_count, website, linkedin_url, city, state

OUTPUT CSV:
  All input columns + lead_score, routing_tier, tier_name, score_breakdown, disqualified, disqualify_reason
"""

import argparse
import csv
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# ---------------------------------------------------------------------------
# Scoring constants
# ---------------------------------------------------------------------------

INDUSTRY_SCORES = {
    # 30 pts
    "hvac / home services": 30,
    "hvac/home services": 30,
    "hvac": 30,
    "home services": 30,
    "plumbing": 30,
    "electrical": 30,
    "roofing": 30,
    # 25 pts
    "dental": 25,
    "medical": 25,
    "med spa": 25,
    "medspa": 25,
    "beauty": 25,
    "cosmetic": 25,
    "aesthetics": 25,
    "health & wellness": 25,
    "healthcare": 25,
    # 15 pts
    "legal": 15,
    "accounting": 15,
    "insurance": 15,
    "financial services": 15,
    "law": 15,
    # 10 pts
    "real estate": 10,
    "property management": 10,
    # 5 pts
    "restaurant": 5,
    "restaurants": 5,
    "hospitality": 5,
    "food & beverage": 5,
    "food and beverage": 5,
}

INDUSTRY_SCORE_DEFAULT = 8  # "Other"

# ---------------------------------------------------------------------------
# Disqualification logic — B2B-only or low phone-dependency patterns
# These override the score and force tier = Skip
# ---------------------------------------------------------------------------

# Company name keywords that strongly signal B2B-only or non-inbound business model
# These businesses don't get residential inbound calls — they work on contracts,
# scheduled routes, or project bids. The AI missed-call offer has no hook here.
B2B_DISQUALIFY_COMPANY_KEYWORDS = [
    # Fire / life safety — commercial inspections, code compliance, building contracts
    "fire stop", "fire suppression", "fire protection", "fire systems",
    "fire sprinkler", "fire alarm", "fire safety",
    # Drone / aerial — commercial agriculture, insurance, surveying
    "drone", "aerial", "uav", "unmanned",
    # Commercial construction / general contractors with large project focus
    # (kkgbuild.com is a GC — but residential remodelers ARE phone-dependent,
    # so we only flag explicit commercial signals)
    # IT / Technology infrastructure — B2B managed services
    "managed service", "it managed", "it services", "it solutions",
    "network solutions", "tech solutions", "technology solutions",
    "infrastructure", "cybersecurity", "cyber security", "data center",
    "cloud solutions", "telecom", "telecommunications",
    # Security systems / commercial integrators
    "security integrat", "access control",
    # Wholesale / distribution
    "wholesale", "distributor", "distribution", "supply chain",
    "manufacturing",
    # Staffing / recruiting
    "recruiting", "staffing", "talent acquisition", "executive search",
    "green hunters",
    # Franchise support / B2B consulting
    "franchise consult",
]

# Company name keywords that signal RESIDENTIAL service businesses with HIGH phone dependency
# These are the strongest YES signals — emergencies, scheduling, homeowner calls
HIGH_PHONE_DEPENDENCY_KEYWORDS = [
    # HVAC — emergency breakdowns, seasonal tune-ups
    "air conditioning", "hvac", "cooling", "heating", "a/c",
    "climate control", "comfort control",
    # Plumbing — emergency calls
    "plumb", "drain", "sewer",
    # Electrical — residential service calls
    "electric", "electrical",
    # Roofing — storm damage, leak calls
    "roof", "reroof",
    # Pool — weekly service + emergency repairs
    "pool",
    # Pest control — recurring service, infestation calls
    "pest", "exterminator", "termite", "bug control",
    # Home repair / handyman
    "repair", "handyman", "maintenance",
    # Painting
    "paint",
    # Landscaping
    "lawn", "landscape", "landscaping", "irrigation",
    # Moving
    "moving", "movers",
    # Cleaning
    "cleaning", "maid", "janitorial",
]

# These company/industry combinations are B2B even if they have a residential-sounding name
# Format: (keyword_in_company_name, disqualify_reason)
CONTEXTUAL_B2B_SIGNALS = [
    # "All In One Technology" — IT managed services for businesses
    ("all in one technology", "IT managed services — B2B, no residential inbound calls"),
    ("all-in-one technology", "IT managed services — B2B, no residential inbound calls"),
    # Fire Stop Systems — commercial fire code compliance
    ("fireproofers", "Commercial fire suppression — B2B contract work, no consumer inbound"),
    ("fire stop", "Commercial fire suppression — B2B contract work, no consumer inbound"),
    # Eco Green Drone — agricultural/commercial drone services
    ("eco green drone", "Commercial drone services — B2B, not consumer call-in"),
    ("ecogreendrone", "Commercial drone services — B2B, not consumer call-in"),
    # Knauf-Koenig Group — large GC, project-bid driven, not inbound call dependent
    ("knauf-koenig", "Large commercial GC (16 employees) — project bids, not inbound calls"),
    ("kkgbuild", "Large commercial GC (16 employees) — project bids, not inbound calls"),
    # Imperial Homes — custom home builder, project-driven not call-driven
    ("imperial homes", "Custom home builder — project-bid driven, clients don't call in"),
]


def check_disqualification(row: Dict[str, str]) -> tuple[bool, str]:
    """
    Check if a lead should be auto-disqualified regardless of score.

    Returns (disqualified: bool, reason: str)

    Disqualification criteria:
    1. Company name matches a known B2B-only pattern
    2. Strong contextual B2B signals (company + business model mismatch)

    We are CONSERVATIVE here — only disqualify when we're confident.
    A roofing company named "All American Roofing" should NOT be disqualified
    just because it has a website and looks professional.
    """
    company = (row.get("company_name", "") or "").strip().lower()
    industry = (row.get("industry", "") or "").strip().lower()

    # Check contextual B2B signals first (most specific, highest confidence)
    for keyword, reason in CONTEXTUAL_B2B_SIGNALS:
        if keyword in company:
            return True, reason

    # Check generic B2B company keywords
    for kw in B2B_DISQUALIFY_COMPANY_KEYWORDS:
        if kw in company:
            return True, f"B2B signal in company name: '{kw}' — likely not consumer-facing"

    # No disqualification
    return False, ""


def classify_phone_dependency(row: Dict[str, str]) -> str:
    """
    Classify how phone-dependent this business model is.

    Returns: 'high' | 'medium' | 'low'

    HIGH = emergency calls, scheduling calls, consumers call to book
    MEDIUM = some inbound calls but also contract/referral driven
    LOW = primarily B2B contracts, referrals, project bids — not inbound call dependent
    """
    company = (row.get("company_name", "") or "").strip().lower()

    for kw in HIGH_PHONE_DEPENDENCY_KEYWORDS:
        if kw in company:
            return "high"

    # Default to medium for other home services
    industry = (row.get("industry", "") or "").strip().lower()
    if "home services" in industry or "hvac" in industry:
        return "medium"

    return "low"


TITLE_KEYWORDS_TIER1 = [
    "owner", "ceo", "founder", "president", "principal",
    "managing partner", "co-founder", "proprietor"
]
TITLE_KEYWORDS_TIER2 = [
    "manager", "director", "vp", "vice president", "head of",
    "chief", "partner", "general manager", "gm", "operations"
]

GENERIC_EMAIL_PREFIXES = {
    "info", "contact", "hello", "admin", "support", "office",
    "sales", "team", "mail", "general", "enquiries", "enquiry",
    "service", "services", "help", "billing", "accounting",
    "reception", "front", "webmaster", "noreply", "no-reply",
    "marketing", "hr", "careers", "jobs"
}


# ---------------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------------

def score_industry(industry_raw: str, apollo_industry_raw: str) -> tuple[int, str]:
    """Score industry fit. Returns (points, label)."""
    # Combine both fields for matching
    candidates = [
        (industry_raw or "").strip().lower(),
        (apollo_industry_raw or "").strip().lower(),
    ]

    best = INDUSTRY_SCORE_DEFAULT
    matched_label = "other"
    for candidate in candidates:
        if not candidate:
            continue
        for keyword, pts in INDUSTRY_SCORES.items():
            if keyword in candidate:
                if pts > best:
                    best = pts
                    matched_label = keyword
                break  # first match in this candidate
    return best, matched_label


def score_company_size(employee_count_raw: str) -> tuple[int, str]:
    """Score company size. Returns (points, label)."""
    raw = (employee_count_raw or "").strip()
    if not raw:
        return 10, "unknown"
    try:
        count = int(float(raw))
    except ValueError:
        return 10, "unknown"

    if count <= 10:
        return 20, "1-10"
    elif count <= 25:
        return 15, "11-25"
    elif count <= 50:
        return 8, "26-50"
    else:
        return 2, "51+"


def score_location(city: str, state: str) -> tuple[int, str]:
    """Score location. Returns (points, label)."""
    city_lower = (city or "").strip().lower()
    state_lower = (state or "").strip().lower()

    naples_cities = {"naples"}
    swfl_cities = {
        "fort myers", "bonita springs", "marco island", "cape coral",
        "estero", "lehigh acres", "immokalee", "golden gate",
        "north naples", "ave maria"
    }

    if city_lower in naples_cities:
        return 20, "Naples FL"
    elif city_lower in swfl_cities:
        return 12, "SWFL"
    elif state_lower in ("florida", "fl"):
        return 6, "Florida other"
    else:
        label = f"{city}, {state}" if city and state else "unknown"
        return 2, label


def score_email(email: str) -> tuple[int, str]:
    """Score email quality. Returns (points, label)."""
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return 0, "no_email"

    prefix = email.split("@")[0]
    # Strip common separators to isolate base prefix
    # e.g. "first.last@domain.com" → owner email
    if prefix in GENERIC_EMAIL_PREFIXES:
        return 5, "generic_role"
    # Check if prefix starts with any generic word
    for generic in GENERIC_EMAIL_PREFIXES:
        if prefix.startswith(generic):
            return 5, "generic_role"
    return 15, "personal_owner"


def score_title(title: str) -> tuple[int, str]:
    """Score decision-maker title. Returns (points, label)."""
    title_lower = (title or "").strip().lower()
    if not title_lower:
        return 3, "blank"
    for kw in TITLE_KEYWORDS_TIER1:
        if kw in title_lower:
            return 15, kw
    for kw in TITLE_KEYWORDS_TIER2:
        if kw in title_lower:
            return 8, kw
    return 3, "other"


def score_lead(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Score a single lead row. Returns scoring dict with lead_score,
    routing_tier, tier_name, score_breakdown, disqualified, and disqualify_reason.

    Disqualification overrides the tier to 0 (skip) regardless of numeric score.
    Phone dependency is tracked as metadata to help prioritize outreach and
    customize email hook selection.
    """
    ind_pts, ind_label = score_industry(
        row.get("industry", ""), row.get("apollo_industry", "")
    )
    size_pts, size_label = score_company_size(row.get("employee_count", ""))
    loc_pts, loc_label = score_location(row.get("city", ""), row.get("state", ""))
    email_pts, email_label = score_email(row.get("email", ""))
    title_pts, title_label = score_title(row.get("title", ""))

    total = ind_pts + size_pts + loc_pts + email_pts + title_pts

    # Check disqualification BEFORE assigning tier
    disqualified, disqualify_reason = check_disqualification(row)
    phone_dependency = classify_phone_dependency(row)

    if disqualified:
        tier = 0
        tier_name = "skip"
    elif total >= 80:
        tier = 1
        tier_name = "deep_personalized"
    elif total >= 50:
        tier = 2
        tier_name = "industry_batch"
    elif total >= 20:
        tier = 3
        tier_name = "generic_batch"
    else:
        tier = 0
        tier_name = "skip"

    breakdown = {
        "industry": {"pts": ind_pts, "matched": ind_label},
        "company_size": {"pts": size_pts, "label": size_label},
        "location": {"pts": loc_pts, "label": loc_label},
        "email": {"pts": email_pts, "label": email_label},
        "title": {"pts": title_pts, "label": title_label},
        "phone_dependency": phone_dependency,
        "disqualified": disqualified,
    }

    return {
        "lead_score": total,
        "routing_tier": tier,
        "tier_name": tier_name,
        "score_breakdown": json.dumps(breakdown),
        "disqualified": "YES" if disqualified else "NO",
        "disqualify_reason": disqualify_reason,
        "phone_dependency": phone_dependency,
    }


# ---------------------------------------------------------------------------
# CSV processing
# ---------------------------------------------------------------------------

def route_csv(
    input_path: str,
    output_path: str,
    tier_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Read Apollo CSV, score each row, write routed CSV.
    Returns summary stats.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    rows_in = []
    with open(input_file, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows_in.append(row)

    if not rows_in:
        print("ERROR: Input CSV is empty.", file=sys.stderr)
        sys.exit(1)

    # Score all rows
    scored = []
    for row in rows_in:
        scores = score_lead(row)
        merged = {**row, **scores}
        scored.append(merged)

    # Apply tier filter
    if tier_filter and tier_filter != "all":
        try:
            tier_int = int(tier_filter)
        except ValueError:
            print(f"ERROR: --tier must be 1, 2, 3, or all", file=sys.stderr)
            sys.exit(1)
        filtered = [r for r in scored if r["routing_tier"] == tier_int]
    else:
        filtered = scored

    # Write output CSV
    if filtered:
        fieldnames = list(rows_in[0].keys()) + [
            "lead_score", "routing_tier", "tier_name", "score_breakdown",
            "disqualified", "disqualify_reason", "phone_dependency"
        ]
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(filtered)

    # Build summary
    tier_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    disqualified_count = 0
    high_phone_dep = 0
    for r in scored:
        tier_counts[r["routing_tier"]] = tier_counts.get(r["routing_tier"], 0) + 1
        if r.get("disqualified") == "YES":
            disqualified_count += 1
        if r.get("phone_dependency") == "high":
            high_phone_dep += 1

    tier1_leads = [r for r in scored if r["routing_tier"] == 1]
    tier1_leads.sort(key=lambda x: x["lead_score"], reverse=True)

    # Show disqualified leads for transparency
    disqualified_leads = [
        {"company": r.get("company_name", ""), "reason": r.get("disqualify_reason", "")}
        for r in scored if r.get("disqualified") == "YES"
    ]

    return {
        "total_input": len(rows_in),
        "total_output": len(filtered),
        "tier_counts": tier_counts,
        "tier1_top10": tier1_leads[:10],
        "output_path": str(output_file.absolute()),
        "disqualified_count": disqualified_count,
        "high_phone_dependency_count": high_phone_dep,
        "disqualified_leads": disqualified_leads[:20],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_summary(summary: Dict[str, Any]):
    """Print a human-readable tier summary to stdout."""
    tier_counts = summary["tier_counts"]
    total = summary["total_input"]

    print()
    print("=" * 60)
    print("LEAD ROUTING SUMMARY")
    print("=" * 60)
    print(f"Total prospects scored:  {total}")
    print()
    print(f"  Tier 1 — deep_personalized  (80-100):  {tier_counts.get(1, 0):>4}")
    print(f"  Tier 2 — industry_batch     (50-79):   {tier_counts.get(2, 0):>4}")
    print(f"  Tier 3 — generic_batch      (20-49):   {tier_counts.get(3, 0):>4}")
    print(f"  Skip   — wrong fit/B2B      (<20):     {tier_counts.get(0, 0):>4}")
    print()
    disq = summary.get("disqualified_count", 0)
    hi_phone = summary.get("high_phone_dependency_count", 0)
    if disq:
        print(f"  Auto-disqualified (B2B/low phone): {disq}")
    if hi_phone:
        print(f"  High phone-dependency (best fit):  {hi_phone}")
    print()
    print(f"Output written to: {summary['output_path']}")

    # Show disqualified leads so William can audit
    disq_leads = summary.get("disqualified_leads", [])
    if disq_leads:
        print()
        print("=" * 60)
        print("AUTO-DISQUALIFIED LEADS (B2B / Low Phone Dependency)")
        print("Review these — if any are wrong, adjust CONTEXTUAL_B2B_SIGNALS")
        print("=" * 60)
        for d in disq_leads:
            print(f"  {d['company'][:40]:<40}  {d['reason']}")

    top10 = summary.get("tier1_top10", [])
    if top10:
        print()
        print("=" * 60)
        print(f"TOP {len(top10)} TIER 1 LEADS (deep_personalized)")
        print("=" * 60)
        print(f"{'#':<3} {'Score':<6} {'Name':<22} {'Company':<28} {'Industry'}")
        print("-" * 90)
        for i, lead in enumerate(top10, 1):
            name = (
                lead.get("contact_name")
                or f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
                or "Unknown"
            )
            company = lead.get("company_name", "Unknown")[:27]
            try:
                breakdown = json.loads(lead.get("score_breakdown", "{}"))
                industry_label = breakdown.get("industry", {}).get("matched", "?")
            except Exception:
                industry_label = lead.get("industry", "?")
            print(
                f"{i:<3} {lead['lead_score']:<6} {name[:21]:<22} {company:<28} {industry_label}"
            )
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Lead Scoring + Routing Engine — scores Apollo CSV prospects 0-100",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python execution/lead_router.py \\
      --input projects/marceau-solutions/digital/outputs/naples-ai-prospects-apollo-enriched-2026-03-23.csv \\
      --output projects/marceau-solutions/digital/outputs/naples-ai-prospects-routed-2026-03-23.csv

  # Only output Tier 1 leads
  python execution/lead_router.py --input leads.csv --output tier1.csv --tier 1
""",
    )
    parser.add_argument("--input", required=True, help="Path to input Apollo CSV")
    parser.add_argument("--output", required=True, help="Path to write routed CSV")
    parser.add_argument(
        "--tier",
        default="all",
        help="Filter output to tier 1, 2, 3, or all (default: all)",
    )

    args = parser.parse_args()
    summary = route_csv(args.input, args.output, args.tier)
    print_summary(summary)


if __name__ == "__main__":
    main()
