"""
AutoInsure Saver — Savings Calculator Engine

Calculates personalized insurance savings recommendations by analyzing
deductibles, coverage adequacy, unclaimed discounts, rate creep,
payment frequency, and switch timing.

Each calculator returns a list of recommendation dicts that map directly
to SavingsRecommendation model fields:
    category, title, description, estimated_annual_savings,
    priority (1-5, 1=highest), confidence (0.0-1.0), action_steps
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from typing import Any, Sequence

from sqlalchemy import select

from src.models.base import async_session
from src.models.user import UserProfile, Vehicle, CurrentPolicy, DrivingRecord
from src.models.savings import SavingsRecommendation, PremiumHistory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------

@dataclass
class Recommendation:
    """Structured savings recommendation ready for persistence."""

    category: str
    title: str
    description: str
    estimated_annual_savings: float
    priority: int  # 1 (highest) → 5 (lowest)
    confidence: float  # 0.0 → 1.0
    action_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ── Deductible tier savings schedule ──────────────────────────────────────
# Maps (from_deductible, to_deductible) → estimated savings % on the
# collision + comprehensive portion of the premium.
# Source: industry rule-of-thumb averages.
_DEDUCTIBLE_SAVINGS: dict[tuple[int, int], tuple[float, float]] = {
    # (from, to): (low%, high%)
    (250, 500):   (0.08, 0.12),
    (250, 1000):  (0.20, 0.30),
    (250, 1500):  (0.28, 0.38),
    (250, 2000):  (0.35, 0.45),
    (500, 1000):  (0.15, 0.20),
    (500, 1500):  (0.22, 0.30),
    (500, 2000):  (0.28, 0.38),
    (1000, 1500): (0.05, 0.10),
    (1000, 2000): (0.12, 0.18),
    (1500, 2000): (0.05, 0.08),
}

# Collision + comprehensive is roughly this fraction of total premium.
_COLL_COMP_FRACTION = 0.40

# Standard deductible tiers to evaluate.
_DEDUCTIBLE_TIERS = [500, 1000, 1500, 2000]


# ── Discount catalogue ────────────────────────────────────────────────────

@dataclass
class _DiscountDef:
    key: str
    name: str
    savings_low: float
    savings_high: float
    eligibility_check: str  # attribute path or special key


_DISCOUNT_CATALOGUE: list[_DiscountDef] = [
    _DiscountDef("multi_car",      "Multi-Car Discount",              0.05, 0.25, "num_vehicles"),
    _DiscountDef("good_driver",    "Good Driver / Accident-Free",     0.10, 0.25, "accident_free"),
    _DiscountDef("defensive_driving", "Defensive Driving Course",     0.05, 0.15, "defensive_driving_course"),
    _DiscountDef("good_student",   "Good Student Discount",           0.05, 0.20, "good_student"),
    _DiscountDef("low_mileage",    "Low Mileage (<7,500 mi/yr)",      0.05, 0.15, "low_mileage"),
    _DiscountDef("homeowner",      "Homeowner Discount",              0.05, 0.10, "is_homeowner"),
    _DiscountDef("bundle",         "Bundle Home + Auto",              0.10, 0.25, "bundle_eligible"),
    _DiscountDef("paperless",      "Paperless Billing",               0.03, 0.05, "paperless_billing"),
    _DiscountDef("autopay",        "Autopay Discount",                0.03, 0.05, "autopay"),
    _DiscountDef("pay_in_full",    "Pay-in-Full (Annual)",            0.05, 0.10, "pay_in_full"),
    _DiscountDef("military",       "Military / Veteran Discount",     0.05, 0.15, "is_military"),
    _DiscountDef("affiliation",    "Professional / Alumni Affiliation", 0.02, 0.10, "has_affiliation"),
    _DiscountDef("anti_theft",     "Anti-Theft Device",               0.05, 0.15, "has_anti_theft"),
    _DiscountDef("telematics",     "Telematics / Usage-Based",        0.05, 0.30, "telematics_enrolled"),
    _DiscountDef("married",        "Married Discount",                0.05, 0.10, "is_married"),
    _DiscountDef("education",      "Advanced Education Discount",     0.03, 0.05, "advanced_education"),
]


# ---------------------------------------------------------------------------
# 1. Deductible Optimizer
# ---------------------------------------------------------------------------

async def calculate_deductible_savings(
    current_deductible: int,
    annual_premium: float,
    accidents_last_3_years: int = 0,
) -> list[Recommendation]:
    """
    Evaluate savings from raising the deductible.

    Args:
        current_deductible: Current deductible amount in dollars.
        annual_premium: Current annual premium in dollars.
        accidents_last_3_years: Number of at-fault accidents in the last 3 years.

    Returns:
        A list of Recommendation objects, one per viable higher-deductible tier.
    """
    recommendations: list[Recommendation] = []
    coll_comp_premium = annual_premium * _COLL_COMP_FRACTION

    for tier in _DEDUCTIBLE_TIERS:
        if tier <= current_deductible:
            continue

        key = (current_deductible, tier)
        if key not in _DEDUCTIBLE_SAVINGS:
            # Interpolate from the closest known bracket.
            low_pct, high_pct = _interpolate_savings(current_deductible, tier)
        else:
            low_pct, high_pct = _DEDUCTIBLE_SAVINGS[key]

        midpoint_pct = (low_pct + high_pct) / 2.0
        estimated_savings = round(coll_comp_premium * midpoint_pct, 2)

        # Break-even: additional out-of-pocket risk / annual savings.
        additional_risk = tier - current_deductible
        if estimated_savings > 0:
            break_even_years = round(additional_risk / estimated_savings, 1)
        else:
            break_even_years = float("inf")

        # Adjust confidence based on driving record.
        # Clean drivers benefit more predictably; accident-prone drivers
        # face higher real cost from the larger deductible.
        if accidents_last_3_years == 0:
            confidence = 0.85
            priority = 2
            risk_note = "Your clean driving record makes this a strong choice."
        elif accidents_last_3_years == 1:
            confidence = 0.60
            priority = 3
            risk_note = (
                "With 1 recent accident, the higher deductible carries moderate risk. "
                f"Break-even period is ~{break_even_years} years without a claim."
            )
        else:
            confidence = 0.35
            priority = 4
            risk_note = (
                f"With {accidents_last_3_years} recent accidents, raising your deductible "
                "is risky. You'd pay more out-of-pocket on each claim."
            )

        recommendations.append(Recommendation(
            category="deductible",
            title=f"Raise deductible to ${tier:,}",
            description=(
                f"Raising your deductible from ${current_deductible:,} to ${tier:,} "
                f"could save an estimated ${estimated_savings:,.0f}/year "
                f"({low_pct:.0%}–{high_pct:.0%} of collision/comprehensive). "
                f"Break-even period: ~{break_even_years} years claim-free. {risk_note}"
            ),
            estimated_annual_savings=estimated_savings,
            priority=priority,
            confidence=confidence,
            action_steps=[
                f"Call your insurer and request a quote with a ${tier:,} deductible.",
                f"Set aside ${tier:,} in an emergency fund to cover the higher deductible.",
                "Compare the new quoted premium against your current cost.",
            ],
        ))

    return recommendations


def _interpolate_savings(from_ded: int, to_ded: int) -> tuple[float, float]:
    """Rough linear interpolation for deductible pairs not in the table."""
    gap = to_ded - from_ded
    # ~0.04% per $100 increase as a rough baseline
    pct = min(gap / 100 * 0.04, 0.45)
    return (pct * 0.75, pct * 1.25)


# ---------------------------------------------------------------------------
# 2. Coverage Auditor
# ---------------------------------------------------------------------------

async def audit_coverage(
    vehicle_value: float,
    vehicle_age_years: int,
    annual_premium: float,
    collision_comp_cost: float,
    liability_limits: tuple[int, int, int],  # (bodily per-person, bodily per-accident, property)
    add_ons: list[str] | None = None,
) -> list[Recommendation]:
    """
    Audit current coverage for waste or gaps.

    Args:
        vehicle_value: Estimated current market value of the vehicle ($).
        vehicle_age_years: Age of the vehicle in years.
        annual_premium: Total annual premium ($).
        collision_comp_cost: Annual cost of collision + comprehensive portion ($).
        liability_limits: Tuple of (per-person BI, per-accident BI, property damage) in thousands.
        add_ons: List of active add-on names (e.g., ["roadside", "rental_reimbursement"]).

    Returns:
        List of Recommendation objects identifying over-insurance, gaps, or waste.
    """
    recommendations: list[Recommendation] = []
    add_ons = add_ons or []

    # ── Over-insurance check ──────────────────────────────────────────
    if vehicle_value > 0:
        cost_ratio = collision_comp_cost / vehicle_value
        if cost_ratio > 0.10:
            savings = round(collision_comp_cost - vehicle_value * 0.10, 2)
            recommendations.append(Recommendation(
                category="coverage",
                title="Over-insured: collision/comprehensive costs too high",
                description=(
                    f"You're paying ${collision_comp_cost:,.0f}/year for collision + comprehensive "
                    f"on a vehicle worth ${vehicle_value:,.0f}. That's {cost_ratio:.1%} of the "
                    "vehicle's value — the 10% threshold suggests this coverage may not be "
                    "cost-effective."
                ),
                estimated_annual_savings=max(savings, 0),
                priority=2,
                confidence=0.80,
                action_steps=[
                    "Review your collision and comprehensive deductibles.",
                    "Consider raising deductibles or dropping coverage if you can self-insure.",
                    "Get a fresh quote without collision/comprehensive to see the difference.",
                ],
            ))

    # ── Drop collision/comp on low-value vehicles ─────────────────────
    if vehicle_value < 5_000 and collision_comp_cost > 0:
        recommendations.append(Recommendation(
            category="coverage",
            title="Consider dropping collision/comprehensive coverage",
            description=(
                f"Your vehicle is valued at ${vehicle_value:,.0f}, which is under $5,000. "
                f"You're paying ${collision_comp_cost:,.0f}/year for collision + comprehensive. "
                "In a total-loss scenario the payout (minus deductible) would be minimal. "
                "Dropping this coverage could save you the full premium amount."
            ),
            estimated_annual_savings=round(collision_comp_cost, 2),
            priority=1,
            confidence=0.85,
            action_steps=[
                "Calculate your potential payout: vehicle value minus deductible.",
                "If the payout is less than one year of premiums, consider dropping coverage.",
                "Redirect the savings into an emergency vehicle fund.",
            ],
        ))

    # ── Liability adequacy check ──────────────────────────────────────
    bi_pp, bi_pa, pd = liability_limits  # in thousands (e.g. 100 = $100k)
    recommended = (100, 300, 100)
    if bi_pp < recommended[0] or bi_pa < recommended[1] or pd < recommended[2]:
        current_str = f"{bi_pp}/{bi_pa}/{pd}"
        rec_str = f"{recommended[0]}/{recommended[1]}/{recommended[2]}"
        recommendations.append(Recommendation(
            category="coverage",
            title="Liability limits may be too low",
            description=(
                f"Your current liability limits are {current_str} ($k). "
                f"We recommend at least {rec_str} ($k) to protect your assets "
                "in a serious accident. Higher limits often cost only $50-$150/year more."
            ),
            estimated_annual_savings=0.0,  # This is a cost increase, but prevents catastrophic loss
            priority=1,
            confidence=0.90,
            action_steps=[
                f"Request a quote for {rec_str} liability limits.",
                "Consider an umbrella policy for additional protection.",
                "Review your total assets to determine adequate coverage.",
            ],
        ))

    # ── Unnecessary add-ons on older vehicles ─────────────────────────
    _unnecessary_for_old = {
        "roadside": ("Roadside Assistance", 50.0, 80.0),
        "roadside_assistance": ("Roadside Assistance", 50.0, 80.0),
        "rental_reimbursement": ("Rental Reimbursement", 60.0, 120.0),
        "rental": ("Rental Reimbursement", 60.0, 120.0),
        "gap_insurance": ("GAP Insurance", 100.0, 200.0),
        "gap": ("GAP Insurance", 100.0, 200.0),
    }

    if vehicle_age_years >= 10:
        for addon in add_ons:
            addon_lower = addon.lower().strip()
            if addon_lower in _unnecessary_for_old:
                name, low_cost, high_cost = _unnecessary_for_old[addon_lower]
                est_savings = round((low_cost + high_cost) / 2, 2)
                recommendations.append(Recommendation(
                    category="coverage",
                    title=f"Consider removing {name}",
                    description=(
                        f"{name} may not be worth the cost on a {vehicle_age_years}-year-old "
                        f"vehicle valued at ${vehicle_value:,.0f}. Standalone alternatives "
                        "(e.g., AAA for roadside) are often cheaper."
                    ),
                    estimated_annual_savings=est_savings,
                    priority=3,
                    confidence=0.70,
                    action_steps=[
                        f"Compare standalone {name.lower()} costs vs. your add-on premium.",
                        f"Remove {name.lower()} from your policy at next renewal if cheaper alternatives exist.",
                    ],
                ))

    return recommendations


# ---------------------------------------------------------------------------
# 3. Discount Finder
# ---------------------------------------------------------------------------

async def find_unclaimed_discounts(
    profile: dict[str, Any],
    driving_record: dict[str, Any],
    annual_premium: float,
    currently_applied_discounts: list[str] | None = None,
) -> list[Recommendation]:
    """
    Identify discounts the user qualifies for but hasn't claimed.

    Args:
        profile: User profile attributes as a dict. Expected keys vary per discount
                 (e.g., is_homeowner, is_married, num_vehicles, annual_mileage, etc.).
        driving_record: Driving history dict (e.g., accidents_3yr, violations_3yr).
        annual_premium: Current annual premium ($).
        currently_applied_discounts: List of discount keys already applied.

    Returns:
        List of Recommendation objects sorted by estimated savings (highest first).
    """
    applied = set(d.lower().strip() for d in (currently_applied_discounts or []))
    recommendations: list[Recommendation] = []

    for disc in _DISCOUNT_CATALOGUE:
        if disc.key in applied:
            continue

        eligible = _check_discount_eligibility(disc, profile, driving_record)
        if not eligible:
            continue

        midpoint = (disc.savings_low + disc.savings_high) / 2.0
        est_savings = round(annual_premium * midpoint, 2)

        recommendations.append(Recommendation(
            category="discount",
            title=f"Unclaimed: {disc.name}",
            description=(
                f"You may qualify for the {disc.name} discount, which typically saves "
                f"{disc.savings_low:.0%}–{disc.savings_high:.0%} on your premium "
                f"(~${est_savings:,.0f}/year based on your ${annual_premium:,.0f} premium)."
            ),
            estimated_annual_savings=est_savings,
            priority=2,
            confidence=0.75,
            action_steps=[
                f"Ask your insurer about the {disc.name} discount.",
                "Provide any required documentation (certificate, ID, etc.).",
                "Confirm the discount is applied at your next renewal.",
            ],
        ))

    # Sort by savings descending.
    recommendations.sort(key=lambda r: r.estimated_annual_savings, reverse=True)
    return recommendations


def _check_discount_eligibility(
    disc: _DiscountDef,
    profile: dict[str, Any],
    driving_record: dict[str, Any],
) -> bool:
    """
    Determine whether a user is likely eligible for a given discount.

    Uses heuristic checks based on profile and driving record fields.
    Returns True if eligible (or likely eligible), False otherwise.
    """
    key = disc.eligibility_check

    # ── Special compound checks ───────────────────────────────────────
    if key == "num_vehicles":
        return profile.get("num_vehicles", 1) >= 2

    if key == "accident_free":
        return (
            driving_record.get("accidents_3yr", 0) == 0
            and driving_record.get("violations_3yr", 0) == 0
        )

    if key == "low_mileage":
        return profile.get("annual_mileage", 12_000) < 7_500

    if key == "bundle_eligible":
        return profile.get("is_homeowner", False) and not profile.get("has_bundle", False)

    if key == "pay_in_full":
        return profile.get("payment_frequency", "monthly") != "annual"

    if key == "good_student":
        age = profile.get("age", 30)
        gpa = profile.get("gpa", 0.0)
        return age < 26 and gpa >= 3.0

    # ── Simple boolean attribute checks ───────────────────────────────
    return bool(profile.get(key, False))


# ---------------------------------------------------------------------------
# 4. Rate Creep Detector
# ---------------------------------------------------------------------------

async def detect_rate_creep(
    premium_history: list[dict[str, Any]],
    has_claims: bool = False,
) -> list[Recommendation]:
    """
    Detect whether premiums have been creeping up across renewal periods.

    Args:
        premium_history: List of dicts with at least ``effective_date`` (date/str)
                         and ``premium`` (float), ordered chronologically.
        has_claims: Whether the user has had claims during the observed period.

    Returns:
        List of Recommendation objects (0 or 1 items).
    """
    recommendations: list[Recommendation] = []

    if len(premium_history) < 2:
        return recommendations

    # Normalise dates.
    parsed: list[tuple[date, float]] = []
    for rec in premium_history:
        eff = rec.get("effective_date") or rec.get("date")
        if isinstance(eff, str):
            eff = date.fromisoformat(eff)
        elif isinstance(eff, datetime):
            eff = eff.date()
        premium = float(rec["premium"])
        parsed.append((eff, premium))

    parsed.sort(key=lambda x: x[0])

    # Compute period-over-period increases.
    increases: list[float] = []
    for i in range(1, len(parsed)):
        prev_date, prev_premium = parsed[i - 1]
        curr_date, curr_premium = parsed[i]
        if prev_premium <= 0:
            continue
        period_years = max((curr_date - prev_date).days / 365.25, 0.25)
        annual_increase = ((curr_premium / prev_premium) - 1.0) / period_years
        increases.append(annual_increase)

    if not increases:
        return recommendations

    avg_annual_increase = sum(increases) / len(increases)
    total_increase_pct = (parsed[-1][1] / parsed[0][1]) - 1.0
    latest_premium = parsed[-1][1]
    first_premium = parsed[0][1]
    span_years = max((parsed[-1][0] - parsed[0][0]).days / 365.25, 1.0)

    # Flag if average increase > 3% (above typical inflation).
    if avg_annual_increase > 0.03:
        excess_pct = avg_annual_increase - 0.03
        estimated_overpay = round(latest_premium * excess_pct, 2)

        if has_claims:
            description = (
                f"Your premium has increased {avg_annual_increase:.1%}/year on average "
                f"over {span_years:.1f} years (total: {total_increase_pct:.1%}). "
                "Some of this may be due to claims, but it's still worth shopping around."
            )
            confidence = 0.55
            priority = 3
        else:
            description = (
                f"⚠️ Loyalty tax detected! Your premium rose {avg_annual_increase:.1%}/year "
                f"on average over {span_years:.1f} years (total: {total_increase_pct:.1%}), "
                "despite having NO claims. Insurers often gradually raise rates on loyal "
                "customers. Shopping around could save you significantly."
            )
            confidence = 0.85
            priority = 1

        recommendations.append(Recommendation(
            category="rate_creep",
            title="Rate creep detected — you may be overpaying",
            description=description,
            estimated_annual_savings=estimated_overpay,
            priority=priority,
            confidence=confidence,
            action_steps=[
                "Get at least 3 competitive quotes from other insurers.",
                "Mention your clean record (if applicable) when requesting quotes.",
                "Ask your current insurer for a rate review or loyalty discount.",
                "Consider switching if you find savings of $200+/year.",
            ],
        ))

    return recommendations


# ---------------------------------------------------------------------------
# 5. Payment Optimizer
# ---------------------------------------------------------------------------

async def optimize_payment(
    annual_premium: float,
    current_frequency: str = "monthly",
    monthly_fee_pct: float = 0.08,
    semi_annual_fee_pct: float = 0.03,
) -> list[Recommendation]:
    """
    Compare payment frequencies to find installment-fee savings.

    Args:
        annual_premium: Base annual premium (without installment fees).
        current_frequency: One of 'monthly', 'semi_annual', 'annual'.
        monthly_fee_pct: Typical surcharge for monthly payments (default 8%).
        semi_annual_fee_pct: Typical surcharge for semi-annual payments (default 3%).

    Returns:
        List of Recommendation objects (0-2 items).
    """
    recommendations: list[Recommendation] = []
    current = current_frequency.lower().replace("-", "_").replace(" ", "_")

    costs = {
        "monthly": annual_premium * (1 + monthly_fee_pct),
        "semi_annual": annual_premium * (1 + semi_annual_fee_pct),
        "annual": annual_premium,
    }

    current_cost = costs.get(current, costs["monthly"])

    # Suggest cheaper frequencies.
    options = [
        ("annual", "Pay annually (in full)"),
        ("semi_annual", "Pay semi-annually"),
    ]

    for freq_key, freq_label in options:
        if freq_key == current:
            continue
        savings = round(current_cost - costs[freq_key], 2)
        if savings <= 0:
            continue

        recommendations.append(Recommendation(
            category="payment",
            title=f"Switch to {freq_label.lower()}",
            description=(
                f"Switching from {current.replace('_', '-')} to {freq_label.lower()} "
                f"payments could save ~${savings:,.0f}/year by avoiding installment fees. "
                f"Current estimated annual cost: ${current_cost:,.0f}; "
                f"{freq_label} cost: ${costs[freq_key]:,.0f}."
            ),
            estimated_annual_savings=savings,
            priority=3,
            confidence=0.90,
            action_steps=[
                f"Ask your insurer about switching to {freq_label.lower()} billing.",
                f"Budget ${costs[freq_key]:,.0f} for the lump payment.",
                "Confirm there are no penalties for changing payment frequency mid-term.",
            ],
        ))

    return recommendations


# ---------------------------------------------------------------------------
# 6. Switch Window Calculator
# ---------------------------------------------------------------------------

async def calculate_switch_window(
    renewal_date: date,
    policy_start_date: date,
    annual_premium: float,
    cancellation_penalty_pct: float = 0.10,
    today: date | None = None,
) -> list[Recommendation]:
    """
    Calculate the optimal window to switch insurers.

    Args:
        renewal_date: Date of next policy renewal.
        policy_start_date: Start date of the current policy term.
        annual_premium: Current annual premium ($).
        cancellation_penalty_pct: Typical short-rate cancellation penalty (default 10%).
        today: Override for current date (for testing). Defaults to date.today().

    Returns:
        List of Recommendation objects (0-2 items: optimal window + early-switch estimate).
    """
    recommendations: list[Recommendation] = []
    today = today or date.today()

    # ── Optimal switch window: 30-60 days before renewal ──────────────
    window_start = renewal_date - timedelta(days=60)
    window_end = renewal_date - timedelta(days=30)
    days_until_renewal = (renewal_date - today).days

    if days_until_renewal < 0:
        # Renewal already passed — flag it.
        recommendations.append(Recommendation(
            category="switch_timing",
            title="Renewal date has passed — shop now",
            description=(
                "Your renewal date has already passed. If you haven't reviewed your "
                "policy, now is still a good time to get competitive quotes."
            ),
            estimated_annual_savings=0.0,
            priority=2,
            confidence=0.70,
            action_steps=[
                "Get 3+ quotes from competing insurers immediately.",
                "Switch at any time — most policies allow 30-day free-look periods.",
            ],
        ))
        return recommendations

    in_window = window_start <= today <= window_end
    if in_window:
        urgency = "🟢 You're in the optimal switching window RIGHT NOW."
        priority = 1
    elif today < window_start:
        days_to_window = (window_start - today).days
        urgency = (
            f"Your optimal switching window opens in {days_to_window} days "
            f"({window_start.isoformat()} → {window_end.isoformat()})."
        )
        priority = 3
    else:
        # Between window_end and renewal.
        urgency = (
            f"The ideal window has passed, but you still have {days_until_renewal} days "
            "before renewal. Act quickly to compare rates."
        )
        priority = 2

    recommendations.append(Recommendation(
        category="switch_timing",
        title="Optimal switch window for your policy",
        description=(
            f"{urgency} Shopping 30-60 days before renewal (on {renewal_date.isoformat()}) "
            "gives you time to compare quotes without pressure, and avoids cancellation fees."
        ),
        estimated_annual_savings=0.0,  # Savings come from the switch itself, not the timing.
        priority=priority,
        confidence=0.90,
        action_steps=[
            f"Start collecting quotes by {window_start.isoformat()}.",
            "Compare at least 3 insurers (try direct writers + independent agents).",
            "Give your current insurer a chance to match the best offer.",
            "Switch effective on your renewal date to avoid cancellation penalties.",
        ],
    ))

    # ── Early-switch / mid-term cancellation estimate ─────────────────
    if today < renewal_date and not in_window and days_until_renewal > 30:
        days_into_term = (today - policy_start_date).days
        term_days = (renewal_date - policy_start_date).days
        if term_days > 0 and days_into_term > 0:
            remaining_fraction = max((term_days - days_into_term) / term_days, 0)
            prorated_refund = annual_premium * remaining_fraction
            penalty = annual_premium * cancellation_penalty_pct
            net_refund = round(max(prorated_refund - penalty, 0), 2)

            recommendations.append(Recommendation(
                category="switch_timing",
                title="Mid-term switch estimate",
                description=(
                    f"If you switch today, your prorated refund would be ~${prorated_refund:,.0f} "
                    f"minus a ~${penalty:,.0f} cancellation penalty = ~${net_refund:,.0f} net refund. "
                    "Switching at renewal avoids the penalty entirely."
                ),
                estimated_annual_savings=0.0,
                priority=4,
                confidence=0.65,
                action_steps=[
                    "Review your policy's cancellation terms for exact penalty details.",
                    "If quotes elsewhere save significantly more than the penalty, consider switching now.",
                    f"Otherwise, wait until {window_start.isoformat()} to switch penalty-free.",
                ],
            ))

    return recommendations


# ---------------------------------------------------------------------------
# 7. Master Analysis — Run all calculators for all users
# ---------------------------------------------------------------------------

async def run_savings_analysis() -> dict[str, Any]:
    """
    Run the full savings analysis pipeline for every user in the database.

    Fetches all user profiles, vehicles, policies, driving records, and premium
    histories, then feeds them through each calculator. Results are persisted as
    SavingsRecommendation records (inserted or updated).

    Returns:
        Summary dict with counts of users processed, recommendations created/updated.
    """
    stats: dict[str, int] = {
        "users_processed": 0,
        "recommendations_created": 0,
        "recommendations_updated": 0,
        "errors": 0,
    }

    async with async_session() as session:
        # Fetch all user profiles.
        result = await session.execute(select(UserProfile))
        users: Sequence[UserProfile] = result.scalars().all()

        for user in users:
            try:
                recs = await _analyze_single_user(session, user)
                await _persist_recommendations(session, user.id, recs, stats)
                stats["users_processed"] += 1
            except Exception:
                logger.exception("Error analyzing user %s", user.id)
                stats["errors"] += 1

        await session.commit()

    logger.info(
        "Savings analysis complete: %d users, %d created, %d updated, %d errors",
        stats["users_processed"],
        stats["recommendations_created"],
        stats["recommendations_updated"],
        stats["errors"],
    )
    return stats


async def run_savings_analysis_for_user(user_id: int) -> int:
    """Run savings analysis for a single user. Returns count of recommendations generated."""
    async with async_session() as session:
        user = await session.get(UserProfile, user_id)
        if not user:
            return 0
        stats: dict[str, int] = {
            "users_processed": 0,
            "recommendations_created": 0,
            "recommendations_updated": 0,
            "errors": 0,
        }
        try:
            recs = await _analyze_single_user(session, user)
            await _persist_recommendations(session, user.id, recs, stats)
            await session.commit()
        except Exception:
            logger.exception("Error analyzing user %s", user_id)
        return stats["recommendations_created"] + stats["recommendations_updated"]


async def _analyze_single_user(
    session: Any,
    user: UserProfile,
) -> list[Recommendation]:
    """Run all calculators for a single user and return combined recommendations."""
    all_recs: list[Recommendation] = []

    # ── Load related data ─────────────────────────────────────────────
    vehicles_result = await session.execute(
        select(Vehicle).where(Vehicle.user_id == user.id)
    )
    vehicles: Sequence[Vehicle] = vehicles_result.scalars().all()

    policy_result = await session.execute(
        select(CurrentPolicy).where(CurrentPolicy.user_id == user.id)
    )
    policy: CurrentPolicy | None = policy_result.scalars().first()

    driving_result = await session.execute(
        select(DrivingRecord).where(DrivingRecord.user_id == user.id)
    )
    driving_record: DrivingRecord | None = driving_result.scalars().first()

    history_result = await session.execute(
        select(PremiumHistory)
        .where(PremiumHistory.user_id == user.id)
        .order_by(PremiumHistory.effective_date)
    )
    premium_history: Sequence[PremiumHistory] = history_result.scalars().all()

    if not policy:
        logger.debug("User %s has no current policy — skipping.", user.id)
        return all_recs

    annual_premium = float(policy.annual_premium)

    # ── 1. Deductible Optimizer ───────────────────────────────────────
    accidents = int(driving_record.accidents_last_3_years) if driving_record else 0
    current_deductible = int(policy.deductible) if policy.deductible else 500
    deductible_recs = await calculate_deductible_savings(
        current_deductible=current_deductible,
        annual_premium=annual_premium,
        accidents_last_3_years=accidents,
    )
    all_recs.extend(deductible_recs)

    # ── 2. Coverage Auditor (per vehicle) ─────────────────────────────
    for vehicle in vehicles:
        vehicle_value = float(vehicle.estimated_value) if vehicle.estimated_value else 0
        vehicle_age = _vehicle_age(vehicle)
        coll_comp_cost = float(policy.collision_comprehensive_cost) if hasattr(policy, "collision_comprehensive_cost") and policy.collision_comprehensive_cost else annual_premium * _COLL_COMP_FRACTION
        liability = _extract_liability_limits(policy)
        add_ons = _extract_add_ons(policy)

        coverage_recs = await audit_coverage(
            vehicle_value=vehicle_value,
            vehicle_age_years=vehicle_age,
            annual_premium=annual_premium,
            collision_comp_cost=coll_comp_cost,
            liability_limits=liability,
            add_ons=add_ons,
        )
        all_recs.extend(coverage_recs)

    # ── 3. Discount Finder ────────────────────────────────────────────
    profile_dict = _user_to_profile_dict(user, vehicles)
    driving_dict = _driving_record_to_dict(driving_record) if driving_record else {}
    applied = _extract_applied_discounts(policy)

    discount_recs = await find_unclaimed_discounts(
        profile=profile_dict,
        driving_record=driving_dict,
        annual_premium=annual_premium,
        currently_applied_discounts=applied,
    )
    all_recs.extend(discount_recs)

    # ── 4. Rate Creep Detector ────────────────────────────────────────
    if premium_history:
        history_dicts = [
            {"effective_date": ph.effective_date, "premium": float(ph.premium)}
            for ph in premium_history
        ]
        has_claims = bool(driving_record and driving_record.claims_last_3_years and int(driving_record.claims_last_3_years) > 0)
        creep_recs = await detect_rate_creep(
            premium_history=history_dicts,
            has_claims=has_claims,
        )
        all_recs.extend(creep_recs)

    # ── 5. Payment Optimizer ──────────────────────────────────────────
    payment_freq = getattr(policy, "payment_frequency", "monthly") or "monthly"
    payment_recs = await optimize_payment(
        annual_premium=annual_premium,
        current_frequency=payment_freq,
    )
    all_recs.extend(payment_recs)

    # ── 6. Switch Window Calculator ───────────────────────────────────
    if policy.renewal_date and policy.start_date:
        switch_recs = await calculate_switch_window(
            renewal_date=_to_date(policy.renewal_date),
            policy_start_date=_to_date(policy.start_date),
            annual_premium=annual_premium,
        )
        all_recs.extend(switch_recs)

    return all_recs


async def _persist_recommendations(
    session: Any,
    user_id: int,
    recommendations: list[Recommendation],
    stats: dict[str, int],
) -> None:
    """Insert or update SavingsRecommendation records for a user."""
    # Index existing recommendations by (category, title) for upsert logic.
    existing_result = await session.execute(
        select(SavingsRecommendation).where(SavingsRecommendation.user_id == user_id)
    )
    existing: dict[tuple[str, str], SavingsRecommendation] = {
        (r.category, r.title): r for r in existing_result.scalars().all()
    }

    for rec in recommendations:
        key = (rec.category, rec.title)
        if key in existing:
            db_rec = existing[key]
            db_rec.description = rec.description
            db_rec.estimated_annual_savings = rec.estimated_annual_savings
            db_rec.priority = rec.priority
            db_rec.confidence = rec.confidence
            db_rec.action_steps = rec.action_steps
            db_rec.updated_at = datetime.utcnow()
            stats["recommendations_updated"] += 1
        else:
            db_rec = SavingsRecommendation(
                user_id=user_id,
                category=rec.category,
                title=rec.title,
                description=rec.description,
                estimated_annual_savings=rec.estimated_annual_savings,
                priority=rec.priority,
                confidence=rec.confidence,
                action_steps=rec.action_steps,
            )
            session.add(db_rec)
            stats["recommendations_created"] += 1


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _vehicle_age(vehicle: Vehicle) -> int:
    """Return vehicle age in years from its model_year attribute."""
    year = getattr(vehicle, "model_year", None) or getattr(vehicle, "year", None)
    if year:
        return max(date.today().year - int(year), 0)
    return 0


def _to_date(value: date | datetime | str) -> date:
    """Coerce a value to a date object."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value)
    return value


def _extract_liability_limits(policy: CurrentPolicy) -> tuple[int, int, int]:
    """Extract liability limits as (BI per-person, BI per-accident, PD) in $k."""
    try:
        bi_pp = int(getattr(policy, "bi_per_person", 0) or 0)
        bi_pa = int(getattr(policy, "bi_per_accident", 0) or 0)
        pd = int(getattr(policy, "property_damage", 0) or 0)
        if bi_pp > 0:
            return (bi_pp, bi_pa, pd)
    except (TypeError, ValueError):
        pass
    # Try a combined limits string like "50/100/50".
    limits_str = getattr(policy, "liability_limits", None)
    if limits_str and isinstance(limits_str, str):
        parts = limits_str.replace("$", "").replace("k", "").split("/")
        if len(parts) == 3:
            try:
                return tuple(int(p.strip()) for p in parts)  # type: ignore[return-value]
            except ValueError:
                pass
    return (50, 100, 50)  # conservative default


def _extract_add_ons(policy: CurrentPolicy) -> list[str]:
    """Extract list of add-on names from a policy."""
    add_ons = getattr(policy, "add_ons", None)
    if isinstance(add_ons, list):
        return add_ons
    if isinstance(add_ons, str):
        return [a.strip() for a in add_ons.split(",") if a.strip()]
    return []


def _extract_applied_discounts(policy: CurrentPolicy) -> list[str]:
    """Extract currently applied discount keys."""
    discounts = getattr(policy, "applied_discounts", None) or getattr(policy, "discounts", None)
    if isinstance(discounts, list):
        return discounts
    if isinstance(discounts, str):
        return [d.strip() for d in discounts.split(",") if d.strip()]
    return []


def _user_to_profile_dict(user: UserProfile, vehicles: Sequence[Vehicle]) -> dict[str, Any]:
    """Build the profile dict expected by find_unclaimed_discounts."""
    return {
        "num_vehicles": len(vehicles),
        "is_homeowner": getattr(user, "is_homeowner", False),
        "is_married": getattr(user, "is_married", False),
        "is_military": getattr(user, "is_military", False),
        "has_affiliation": getattr(user, "has_affiliation", False),
        "has_anti_theft": any(getattr(v, "has_anti_theft", False) for v in vehicles),
        "telematics_enrolled": getattr(user, "telematics_enrolled", False),
        "advanced_education": getattr(user, "advanced_education", False),
        "defensive_driving_course": getattr(user, "defensive_driving_course", False),
        "good_student": getattr(user, "good_student", False),
        "age": getattr(user, "age", None) or _calculate_age(user),
        "gpa": getattr(user, "gpa", 0.0),
        "annual_mileage": getattr(user, "annual_mileage", 12_000),
        "low_mileage": (getattr(user, "annual_mileage", 12_000) or 12_000) < 7_500,
        "paperless_billing": getattr(user, "paperless_billing", False),
        "autopay": getattr(user, "autopay", False),
        "payment_frequency": getattr(user, "payment_frequency", "monthly"),
        "has_bundle": getattr(user, "has_bundle", False),
        "bundle_eligible": getattr(user, "is_homeowner", False) and not getattr(user, "has_bundle", False),
        "pay_in_full": getattr(user, "payment_frequency", "monthly") == "annual",
    }


def _calculate_age(user: UserProfile) -> int:
    """Calculate age from date_of_birth if available."""
    dob = getattr(user, "date_of_birth", None)
    if dob:
        dob = _to_date(dob)
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return 30  # default assumption


def _driving_record_to_dict(record: DrivingRecord) -> dict[str, Any]:
    """Convert a DrivingRecord model instance to a plain dict."""
    return {
        "accidents_3yr": getattr(record, "accidents_last_3_years", 0) or 0,
        "violations_3yr": getattr(record, "violations_last_3_years", 0) or 0,
        "claims_3yr": getattr(record, "claims_last_3_years", 0) or 0,
    }
