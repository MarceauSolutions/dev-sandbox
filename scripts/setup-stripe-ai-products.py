#!/usr/bin/env python3
"""
setup-stripe-ai-products.py — Create Stripe products and payment links for AI services.

Creates:
  - AI Automation Setup (one-time): $2,000 / $3,500 / $5,000
  - AI Systems Management (recurring monthly): $500 / $750 / $1,000

Usage:
    python scripts/setup-stripe-ai-products.py
"""

import os
import sys
from pathlib import Path

# Load .env
PROJECT_ROOT = Path(__file__).parent.parent
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

try:
    import stripe
except ImportError:
    print("ERROR: stripe not installed. Run: pip install stripe")
    sys.exit(1)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
if not stripe.api_key:
    print("ERROR: STRIPE_SECRET_KEY not found in .env")
    sys.exit(1)


def create_product_with_prices(name, description, prices, recurring=False):
    """Create a Stripe product with multiple price tiers and payment links."""
    print(f"\nCreating product: {name}")
    product = stripe.Product.create(
        name=name,
        description=description,
    )
    print(f"  Product ID: {product.id}")

    results = []
    for tier_name, amount_dollars in prices:
        price_params = {
            "product": product.id,
            "unit_amount": int(amount_dollars * 100),
            "currency": "usd",
        }
        if recurring:
            price_params["recurring"] = {"interval": "month"}

        price = stripe.Price.create(**price_params)
        print(f"  Price [{tier_name}]: {price.id} — ${amount_dollars}" + ("/mo" if recurring else " one-time"))

        # Create payment link
        link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}],
        )
        print(f"    Payment Link: {link.url}")

        results.append({
            "tier": tier_name,
            "price_id": price.id,
            "amount": amount_dollars,
            "payment_link": link.url,
        })

    return product.id, results


def main():
    print("=== Stripe AI Services Product Setup ===\n")

    # Product 1: AI Automation Setup (one-time)
    setup_product_id, setup_prices = create_product_with_prices(
        name="AI Automation Setup",
        description="One-time AI automation setup for your business. Includes workflow design, integration, testing, and deployment.",
        prices=[
            ("Small", 2000),
            ("Medium", 3500),
            ("Enterprise", 5000),
        ],
        recurring=False,
    )

    # Product 2: AI Systems Management (recurring monthly)
    mgmt_product_id, mgmt_prices = create_product_with_prices(
        name="AI Systems Management",
        description="Monthly AI systems management. Includes monitoring, optimization, updates, and support.",
        prices=[
            ("$500/mo", 500),
            ("$750/mo", 750),
            ("$1000/mo", 1000),
        ],
        recurring=True,
    )

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"\nAI Automation Setup (one-time) — Product: {setup_product_id}")
    for p in setup_prices:
        print(f"  {p['tier']:12s} ${p['amount']:,}     Price: {p['price_id']}")
        print(f"               Link: {p['payment_link']}")

    print(f"\nAI Systems Management (monthly) — Product: {mgmt_product_id}")
    for p in mgmt_prices:
        print(f"  {p['tier']:12s} ${p['amount']:,}/mo  Price: {p['price_id']}")
        print(f"               Link: {p['payment_link']}")

    print("\nDone!")


if __name__ == "__main__":
    main()
