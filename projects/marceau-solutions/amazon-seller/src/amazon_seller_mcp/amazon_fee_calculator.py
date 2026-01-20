#!/usr/bin/env python3
"""
Amazon FBA Fee Calculator
Calculates comprehensive FBA fees including 2026 fee structure.

Features:
- FBA fulfillment fees (size-tier based)
- Monthly storage fees (seasonal rates)
- Referral fees (category-based)
- Aged inventory surcharges (12-15 months, 15+ months)
- Low inventory level fees
- Profit margin analysis

Usage:
    python amazon_fee_calculator.py --asin B08XYZ123 --price 29.99
    python amazon_fee_calculator.py --asin B08XYZ123 --price 29.99 --month 10
"""

import argparse
import sys
from datetime import datetime
try:
    from .amazon_sp_api import AmazonSPAPI
except ImportError:
    from amazon_sp_api import AmazonSPAPI


class FBAFeeCalculator:
    """
    Calculates all FBA fees for products based on 2026 fee structure.
    """

    # 2026 FBA Fulfillment Fees (per unit)
    # Source: https://sellerengine.com/amazon-2026-fba-fees/
    FULFILLMENT_FEES = {
        'small_standard': {
            'up_to_10oz': 3.22,
            'up_to_1lb': 3.77,
            'up_to_2lb': 4.36,
        },
        'large_standard': {
            'up_to_1lb': 4.07,
            'up_to_2lb': 4.66,
            'up_to_3lb': 5.83,
            '1lb_to_20lb': lambda weight: 5.83 + ((weight - 3) * 0.16),  # $0.16 per lb over 3 lb
            'over_20lb': lambda weight: 8.55 + ((weight - 20) * 0.16),
        },
        'large_bulky': {
            'up_to_50lb': lambda weight: 9.73 + (weight * 0.42),
            'over_50lb': lambda weight: 30.73 + ((weight - 50) * 0.42),
        },
        'extra_large': {
            'up_to_70lb': lambda weight: 89.98 + (weight * 0.83),
            'over_70lb': lambda weight: 147.98 + ((weight - 70) * 0.83),
        }
    }

    # 2026 Monthly Storage Fees (per cubic foot)
    STORAGE_FEES = {
        'standard': {
            'jan_sep': 0.87,  # Per cubic foot
            'oct_dec': 2.40,  # Peak season
        },
        'oversize': {
            'jan_sep': 0.56,
            'oct_dec': 1.40,
        }
    }

    # Aged Inventory Surcharges (2026)
    AGED_INVENTORY_SURCHARGE = {
        '12_15_months': {
            'per_unit': 0.30,
            'per_cubic_foot': 6.90,
        },
        '15_plus_months': {
            'per_unit': 0.35,
            'per_cubic_foot': 7.90,
        }
    }

    # Low Inventory Level Fee (2026)
    # Applies when inventory is below optimal level
    LOW_INVENTORY_FEE = {
        'small_standard': 0.89,
        'large_standard': 1.11,
        'large_bulky': 1.39,
        'extra_large': 1.39,
    }

    # Referral Fees by Category (2026)
    # Most categories are 15%, some vary
    REFERRAL_FEES = {
        'default': 0.15,  # 15% for most categories
        'electronics': 0.08,  # 8% for electronics under $100
        'electronics_over_100': 0.15,  # 15% for electronics over $100
        'furniture': 0.15,
        'home': 0.15,
        'toys': 0.15,
        'clothing': 0.17,  # 17% for apparel
        'jewelry': 0.20,  # 20% for jewelry over $250
        'amazon_device_accessories': 0.45,  # 45% for Amazon device accessories
    }

    # Minimum referral fees
    MIN_REFERRAL_FEE = 0.30  # $0.30 minimum

    def __init__(self):
        """Initialize with Amazon SP-API connection."""
        self.api = AmazonSPAPI()

    def estimate_size_tier(self, dimensions=None, weight=None):
        """
        Estimate product size tier based on dimensions and weight.

        Args:
            dimensions: Dict with 'length', 'width', 'height' in inches
            weight: Weight in pounds

        Returns:
            String: Size tier classification
        """
        if not dimensions or not weight:
            # Default to large_standard if no data
            return 'large_standard'

        length = dimensions.get('length', 0)
        width = dimensions.get('width', 0)
        height = dimensions.get('height', 0)

        # Calculate longest, median, shortest sides
        sides = sorted([length, width, height], reverse=True)
        longest = sides[0]
        median = sides[1]
        shortest = sides[2]

        # Small standard: longest side ≤ 15", median ≤ 12", shortest ≤ 0.75", weight ≤ 2 lb
        if longest <= 15 and median <= 12 and shortest <= 0.75 and weight <= 2:
            return 'small_standard'

        # Large standard: longest side ≤ 18", median ≤ 14", shortest ≤ 8", weight ≤ 20 lb
        if longest <= 18 and median <= 14 and shortest <= 8 and weight <= 20:
            return 'large_standard'

        # Large bulky: longest side ≤ 59", median ≤ 33", shortest ≤ 33", weight ≤ 50 lb
        if longest <= 59 and median <= 33 and shortest <= 33 and weight <= 50:
            return 'large_bulky'

        # Extra large: everything else
        return 'extra_large'

    def calculate_fulfillment_fee(self, size_tier, weight):
        """
        Calculate FBA fulfillment fee based on size tier and weight.

        Args:
            size_tier: Product size tier
            weight: Product weight in pounds

        Returns:
            Float: Fulfillment fee in dollars
        """
        if size_tier == 'small_standard':
            if weight <= 0.625:  # 10 oz
                return self.FULFILLMENT_FEES['small_standard']['up_to_10oz']
            elif weight <= 1:
                return self.FULFILLMENT_FEES['small_standard']['up_to_1lb']
            else:
                return self.FULFILLMENT_FEES['small_standard']['up_to_2lb']

        elif size_tier == 'large_standard':
            if weight <= 1:
                return self.FULFILLMENT_FEES['large_standard']['up_to_1lb']
            elif weight <= 2:
                return self.FULFILLMENT_FEES['large_standard']['up_to_2lb']
            elif weight <= 3:
                return self.FULFILLMENT_FEES['large_standard']['up_to_3lb']
            elif weight <= 20:
                return self.FULFILLMENT_FEES['large_standard']['1lb_to_20lb'](weight)
            else:
                return self.FULFILLMENT_FEES['large_standard']['over_20lb'](weight)

        elif size_tier == 'large_bulky':
            if weight <= 50:
                return self.FULFILLMENT_FEES['large_bulky']['up_to_50lb'](weight)
            else:
                return self.FULFILLMENT_FEES['large_bulky']['over_50lb'](weight)

        else:  # extra_large
            if weight <= 70:
                return self.FULFILLMENT_FEES['extra_large']['up_to_70lb'](weight)
            else:
                return self.FULFILLMENT_FEES['extra_large']['over_70lb'](weight)

    def calculate_storage_fee(self, cubic_feet, size_tier='standard', month=None):
        """
        Calculate monthly storage fee.

        Args:
            cubic_feet: Product size in cubic feet
            size_tier: 'standard' or 'oversize'
            month: Month number (1-12), defaults to current month

        Returns:
            Float: Monthly storage fee in dollars
        """
        if month is None:
            month = datetime.now().month

        # Determine if peak season (Oct-Dec)
        is_peak = month >= 10

        if size_tier == 'standard':
            rate = self.STORAGE_FEES['standard']['oct_dec'] if is_peak else self.STORAGE_FEES['standard']['jan_sep']
        else:
            rate = self.STORAGE_FEES['oversize']['oct_dec'] if is_peak else self.STORAGE_FEES['oversize']['jan_sep']

        return cubic_feet * rate

    def calculate_referral_fee(self, price, category='default'):
        """
        Calculate Amazon referral fee.

        Args:
            price: Selling price
            category: Product category (affects rate)

        Returns:
            Float: Referral fee in dollars
        """
        rate = self.REFERRAL_FEES.get(category, self.REFERRAL_FEES['default'])

        # Special case: Electronics
        if category == 'electronics':
            if price > 100:
                rate = self.REFERRAL_FEES['electronics_over_100']

        fee = price * rate

        # Apply minimum fee
        return max(fee, self.MIN_REFERRAL_FEE)

    def calculate_aged_inventory_surcharge(self, age_days, cubic_feet, units=1):
        """
        Calculate aged inventory surcharge.

        Args:
            age_days: Age of inventory in days
            cubic_feet: Size per unit in cubic feet
            units: Number of units

        Returns:
            Float: Aged inventory surcharge in dollars
        """
        if age_days < 365:  # Less than 12 months
            return 0.0

        if age_days < 456:  # 12-15 months
            per_unit = self.AGED_INVENTORY_SURCHARGE['12_15_months']['per_unit']
            per_cf = self.AGED_INVENTORY_SURCHARGE['12_15_months']['per_cubic_foot']
        else:  # 15+ months
            per_unit = self.AGED_INVENTORY_SURCHARGE['15_plus_months']['per_unit']
            per_cf = self.AGED_INVENTORY_SURCHARGE['15_plus_months']['per_cubic_foot']

        # Use greater of per-unit or per-cubic-foot charge
        unit_charge = units * per_unit
        cf_charge = (units * cubic_feet) * per_cf

        return max(unit_charge, cf_charge)

    def calculate_low_inventory_fee(self, size_tier, has_low_inventory=False):
        """
        Calculate low inventory level fee.

        Args:
            size_tier: Product size tier
            has_low_inventory: Whether inventory is below optimal level

        Returns:
            Float: Low inventory fee per unit
        """
        if not has_low_inventory:
            return 0.0

        return self.LOW_INVENTORY_FEE.get(size_tier, 0.0)

    def calculate_comprehensive_fees(
        self,
        asin,
        price,
        category='default',
        month=None,
        units=1,
        age_days=0,
        cost_per_unit=None
    ):
        """
        Calculate all FBA fees for a product.

        Args:
            asin: Product ASIN
            price: Selling price
            category: Product category
            month: Month for storage fee calculation
            units: Number of units
            age_days: Age of inventory in days
            cost_per_unit: Cost to acquire product (for profit calculation)

        Returns:
            Dict with comprehensive fee breakdown
        """
        print(f"\n{'='*70}")
        print(f"FBA FEE CALCULATOR: {asin}")
        print(f"{'='*70}")

        # Get product details from API
        print(f"\n→ Retrieving product details...")
        product_data = self.api.get_product_details(asin, use_cache=True)

        # Extract dimensions and weight (with fallbacks)
        # In production, would parse from product_data
        # For now, using reasonable defaults
        dimensions = {'length': 12, 'width': 8, 'height': 2}  # inches
        weight = 1.5  # pounds
        cubic_feet = (dimensions['length'] * dimensions['width'] * dimensions['height']) / 1728  # Convert cubic inches to cubic feet

        print(f"  • Dimensions: {dimensions['length']}\" x {dimensions['width']}\" x {dimensions['height']}\"")
        print(f"  • Weight: {weight} lb")
        print(f"  • Cubic feet: {cubic_feet:.2f} ft³")

        # Determine size tier
        size_tier = self.estimate_size_tier(dimensions, weight)
        storage_tier = 'standard' if size_tier in ['small_standard', 'large_standard'] else 'oversize'

        print(f"  • Size tier: {size_tier}")

        # Calculate all fees
        print(f"\n💰 FEE BREAKDOWN (Per Unit)")
        print(f"{'-'*70}")

        # 1. Fulfillment fee
        fulfillment_fee = self.calculate_fulfillment_fee(size_tier, weight)
        print(f"  FBA Fulfillment Fee:        ${fulfillment_fee:.2f}")

        # 2. Storage fee
        storage_fee = self.calculate_storage_fee(cubic_feet, storage_tier, month)
        print(f"  Monthly Storage Fee:        ${storage_fee:.2f}")

        # 3. Referral fee
        referral_fee = self.calculate_referral_fee(price, category)
        print(f"  Referral Fee ({category}):   ${referral_fee:.2f} ({referral_fee/price*100:.1f}% of price)")

        # 4. Aged inventory surcharge
        aged_surcharge = self.calculate_aged_inventory_surcharge(age_days, cubic_feet, units=1)
        if aged_surcharge > 0:
            print(f"  Aged Inventory Surcharge:   ${aged_surcharge:.2f} ({age_days} days old)")

        # 5. Low inventory fee (checking if this applies)
        inventory_summary = self.api.get_inventory_summary(asins=[asin], use_cache=True)
        has_low_inventory = False  # Would calculate based on inventory_summary
        low_inventory_fee = self.calculate_low_inventory_fee(size_tier, has_low_inventory)
        if low_inventory_fee > 0:
            print(f"  Low Inventory Level Fee:    ${low_inventory_fee:.2f}")

        # Total fees
        total_fees_per_unit = (
            fulfillment_fee +
            storage_fee +
            referral_fee +
            aged_surcharge +
            low_inventory_fee
        )

        print(f"{'-'*70}")
        print(f"  TOTAL FEES (per unit):      ${total_fees_per_unit:.2f}")

        # Profit analysis
        print(f"\n📊 PROFIT ANALYSIS")
        print(f"{'-'*70}")
        print(f"  Selling Price:              ${price:.2f}")
        print(f"  Total Amazon Fees:          ${total_fees_per_unit:.2f}")

        if cost_per_unit:
            print(f"  Cost of Goods (your cost):  ${cost_per_unit:.2f}")
            profit = price - total_fees_per_unit - cost_per_unit
            margin = (profit / price) * 100
            roi = (profit / cost_per_unit) * 100

            print(f"{'-'*70}")
            print(f"  NET PROFIT (per unit):      ${profit:.2f}")
            print(f"  Profit Margin:              {margin:.1f}%")
            print(f"  ROI:                        {roi:.1f}%")
        else:
            net_revenue = price - total_fees_per_unit
            print(f"{'-'*70}")
            print(f"  NET REVENUE (after fees):   ${net_revenue:.2f}")
            print(f"  Revenue Margin:             {(net_revenue/price)*100:.1f}%")

        # Multi-unit analysis
        if units > 1:
            print(f"\n📦 TOTAL FOR {units} UNITS")
            print(f"{'-'*70}")
            total_revenue = price * units
            total_fees = total_fees_per_unit * units

            print(f"  Total Revenue:              ${total_revenue:.2f}")
            print(f"  Total Amazon Fees:          ${total_fees:.2f}")

            if cost_per_unit:
                total_cost = cost_per_unit * units
                total_profit = total_revenue - total_fees - total_cost
                print(f"  Total COGS:                 ${total_cost:.2f}")
                print(f"  Total Profit:               ${total_profit:.2f}")

        print(f"\n{'='*70}")

        return {
            'asin': asin,
            'price': price,
            'size_tier': size_tier,
            'fees': {
                'fulfillment': fulfillment_fee,
                'storage': storage_fee,
                'referral': referral_fee,
                'aged_inventory': aged_surcharge,
                'low_inventory': low_inventory_fee,
                'total_per_unit': total_fees_per_unit,
            },
            'profit': {
                'revenue_per_unit': price - total_fees_per_unit,
                'cost_per_unit': cost_per_unit,
                'profit_per_unit': (price - total_fees_per_unit - cost_per_unit) if cost_per_unit else None,
                'margin_percent': ((price - total_fees_per_unit - cost_per_unit) / price * 100) if cost_per_unit else None,
            },
            'product_specs': {
                'dimensions': dimensions,
                'weight': weight,
                'cubic_feet': cubic_feet,
            }
        }


def main():
    """CLI for FBA fee calculator."""
    parser = argparse.ArgumentParser(
        description='Amazon FBA Fee Calculator - Calculate comprehensive fees including 2026 structure'
    )
    parser.add_argument('--asin', required=True, help='Product ASIN to analyze')
    parser.add_argument('--price', type=float, required=True, help='Selling price in USD')
    parser.add_argument('--cost', type=float, help='Your cost per unit (for profit calculation)')
    parser.add_argument('--category', default='default', help='Product category (affects referral fee)')
    parser.add_argument('--month', type=int, help='Month (1-12) for storage fee calculation')
    parser.add_argument('--units', type=int, default=1, help='Number of units to analyze')
    parser.add_argument('--age-days', type=int, default=0, help='Age of inventory in days')

    args = parser.parse_args()

    # Validate inputs
    if args.price <= 0:
        print("Error: Price must be positive")
        return 1

    if args.month and (args.month < 1 or args.month > 12):
        print("Error: Month must be between 1 and 12")
        return 1

    # Run calculator
    try:
        calculator = FBAFeeCalculator()
        result = calculator.calculate_comprehensive_fees(
            asin=args.asin,
            price=args.price,
            category=args.category,
            month=args.month,
            units=args.units,
            age_days=args.age_days,
            cost_per_unit=args.cost
        )

        # Print API usage summary
        calculator.api.print_api_usage_summary()

        return 0

    except Exception as e:
        print(f"\n✗ Error calculating fees: {e}")
        print("\nTip: If you're getting auth errors, check:")
        print("  1. Your .env file has valid Amazon SP-API credentials")
        print("  2. Run: python execution/setup_amazon_auth.py")
        return 1


if __name__ == '__main__':
    sys.exit(main())
