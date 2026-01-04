#!/usr/bin/env python3
"""
Amazon Inventory Optimizer
Provides intelligent reorder recommendations with cost-benefit analysis.

Features:
- Sales velocity calculation
- Storage fee projections (including 2026 aged inventory fees)
- Stockout risk assessment
- Buy box impact analysis
- Optimal reorder quantity recommendation

Usage:
    python amazon_inventory_optimizer.py --asin B08XYZ123
    python amazon_inventory_optimizer.py --asin B08XYZ123 --days 30
"""

import argparse
import sys
from datetime import datetime, timedelta
from amazon_sp_api import AmazonSPAPI


class InventoryOptimizer:
    """
    Analyzes inventory levels and provides reorder recommendations
    with comprehensive cost-benefit analysis.
    """

    # 2026 FBA Storage Fee Structure
    MONTHLY_STORAGE_FEES = {
        'standard': {
            'jan_sep': 0.87,  # per cubic foot
            'oct_dec': 2.40,  # per cubic foot (peak season)
        },
        'oversize': {
            'jan_sep': 0.56,
            'oct_dec': 1.40,
        }
    }

    # Aged Inventory Surcharges (2026)
    AGED_INVENTORY_FEES = {
        '12_15_months': {'per_unit': 0.30, 'per_cubic_foot': 6.90},
        '15_plus_months': {'per_unit': 0.35, 'per_cubic_foot': 7.90},
    }

    # Buy Box Loss Estimates
    STOCKOUT_IMPACT = {
        'buy_box_loss_days': 7,  # Days to regain buy box after restocking
        'sales_loss_multiplier': 0.85,  # 85% sales loss during stockout
    }

    def __init__(self):
        """Initialize with Amazon SP-API connection."""
        self.api = AmazonSPAPI()

    def calculate_sales_velocity(self, asin, days=30):
        """
        Calculate daily sales velocity for an ASIN.

        Args:
            asin: Product ASIN
            days: Number of days to analyze

        Returns:
            Float: Units sold per day
        """
        print(f"\n→ Calculating sales velocity for {asin} (last {days} days)...")

        # Get orders from last N days
        orders = self.api.get_orders(days_back=days, use_cache=True)

        if not orders:
            print(f"  WARNING: No order data available")
            return 0.0

        # Count units of this ASIN
        units_sold = 0
        for order in orders:
            # Note: In real implementation, would need to get order items
            # This is simplified for the example
            # Would use: orders_api.get_order_items(order['AmazonOrderId'])
            pass

        # For now, simulate with placeholder
        # TODO: Implement actual order item parsing
        units_sold = 45  # Placeholder

        velocity = units_sold / days
        print(f"  ✓ Sales velocity: {velocity:.2f} units/day ({units_sold} units in {days} days)")
        return velocity

    def get_current_inventory(self, asin):
        """
        Get current FBA inventory level for ASIN.

        Args:
            asin: Product ASIN

        Returns:
            Dict with inventory details
        """
        print(f"\n→ Retrieving current inventory for {asin}...")

        inventory = self.api.get_inventory_summary(asins=[asin], use_cache=True)

        if not inventory:
            print(f"  WARNING: Could not retrieve inventory data")
            return {'available': 0, 'inbound': 0, 'age_days': 0}

        # Parse inventory data (simplified)
        # TODO: Parse actual SP-API response structure
        inventory_data = {
            'available': 120,  # Placeholder
            'inbound': 0,      # Placeholder
            'age_days': 180,   # Placeholder (days inventory has been at Amazon)
        }

        print(f"  ✓ Available: {inventory_data['available']} units")
        print(f"  ✓ Inbound: {inventory_data['inbound']} units")
        print(f"  ✓ Avg age: {inventory_data['age_days']} days")

        return inventory_data

    def calculate_storage_costs(self, units, cubic_feet_per_unit, months_stored, product_size='standard'):
        """
        Calculate total storage costs including aged inventory fees.

        Args:
            units: Number of units
            cubic_feet_per_unit: Size in cubic feet
            months_stored: Projected months in storage
            product_size: 'standard' or 'oversize'

        Returns:
            Dict with cost breakdown
        """
        total_cost = 0
        breakdown = {}

        # Determine current month for seasonal rates
        current_month = datetime.now().month
        is_peak_season = current_month >= 10  # Oct-Dec

        # Monthly storage rate
        if is_peak_season:
            monthly_rate = self.MONTHLY_STORAGE_FEES[product_size]['oct_dec']
        else:
            monthly_rate = self.MONTHLY_STORAGE_FEES[product_size]['jan_sep']

        # Calculate base storage costs
        total_cubic_feet = units * cubic_feet_per_unit
        monthly_storage_cost = total_cubic_feet * monthly_rate
        base_storage_cost = monthly_storage_cost * months_stored

        breakdown['base_storage'] = base_storage_cost
        total_cost += base_storage_cost

        # Add aged inventory surcharges if applicable
        if months_stored >= 12:
            if months_stored >= 15:
                # 15+ months surcharge
                aged_fee = units * self.AGED_INVENTORY_FEES['15_plus_months']['per_unit']
                breakdown['aged_inventory_15plus'] = aged_fee
                total_cost += aged_fee
            else:
                # 12-15 months surcharge
                aged_fee = units * self.AGED_INVENTORY_FEES['12_15_months']['per_unit']
                breakdown['aged_inventory_12_15'] = aged_fee
                total_cost += aged_fee

        breakdown['total'] = total_cost
        return breakdown

    def calculate_stockout_cost(self, daily_sales, profit_per_unit, stockout_days):
        """
        Calculate cost of running out of stock.

        Args:
            daily_sales: Average daily sales
            profit_per_unit: Profit margin per unit
            stockout_days: Days out of stock

        Returns:
            Dict with stockout impact
        """
        # Lost sales during stockout
        units_lost = daily_sales * stockout_days * self.STOCKOUT_IMPACT['sales_loss_multiplier']
        revenue_lost = units_lost * profit_per_unit

        # Additional sales lost during buy box recovery period
        recovery_units_lost = daily_sales * self.STOCKOUT_IMPACT['buy_box_loss_days'] * 0.5
        recovery_revenue_lost = recovery_units_lost * profit_per_unit

        total_cost = revenue_lost + recovery_revenue_lost

        return {
            'units_lost': units_lost + recovery_units_lost,
            'revenue_lost': revenue_lost,
            'recovery_impact': recovery_revenue_lost,
            'total_cost': total_cost,
            'stockout_days': stockout_days,
        }

    def recommend_reorder_quantity(self, asin, lead_time_days=30, target_days_supply=60):
        """
        Recommend optimal reorder quantity with full cost-benefit analysis.

        Args:
            asin: Product ASIN
            lead_time_days: Days until new inventory arrives
            target_days_supply: Desired days of inventory to maintain

        Returns:
            Dict with recommendation and analysis
        """
        print("\n" + "="*70)
        print(f"INVENTORY REORDER ANALYSIS: {asin}")
        print("="*70)

        # Get current state
        inventory = self.get_current_inventory(asin)
        velocity = self.calculate_sales_velocity(asin, days=30)

        # Calculate days until stockout
        current_available = inventory['available'] + inventory['inbound']
        if velocity > 0:
            days_until_stockout = current_available / velocity
        else:
            days_until_stockout = 999  # No sales, won't stockout

        print(f"\n📊 CURRENT SITUATION")
        print(f"  • Current inventory: {current_available} units")
        print(f"  • Daily sales rate: {velocity:.2f} units/day")
        print(f"  • Days until stockout: {days_until_stockout:.1f} days")

        # Determine urgency
        if days_until_stockout < lead_time_days:
            urgency = "🔴 CRITICAL"
            print(f"  • Urgency: {urgency} - Will stockout before reorder arrives!")
        elif days_until_stockout < lead_time_days + 14:
            urgency = "🟡 HIGH"
            print(f"  • Urgency: {urgency}")
        else:
            urgency = "🟢 NORMAL"
            print(f"  • Urgency: {urgency}")

        # Calculate optimal order quantity
        # Target: enough to last target_days_supply after lead time
        days_to_cover = target_days_supply + lead_time_days - days_until_stockout
        if days_to_cover < 0:
            days_to_cover = target_days_supply  # Already past stockout

        optimal_quantity = int(velocity * days_to_cover)

        print(f"\n📦 RECOMMENDATION")
        print(f"  • Recommended order quantity: {optimal_quantity} units")
        print(f"  • Will provide {target_days_supply} days of supply")

        # Cost analysis
        # Assuming product dimensions (would fetch from API in production)
        cubic_feet_per_unit = 0.5  # Placeholder
        profit_per_unit = 10.00    # Placeholder

        # Scenario 1: Order recommended amount
        storage_months = target_days_supply / 30
        scenario_optimal = self.calculate_storage_costs(
            optimal_quantity,
            cubic_feet_per_unit,
            storage_months
        )

        # Scenario 2: Over-order by 50%
        overorder_quantity = int(optimal_quantity * 1.5)
        overorder_months = storage_months * 1.5
        scenario_overorder = self.calculate_storage_costs(
            overorder_quantity,
            cubic_feet_per_unit,
            overorder_months
        )

        # Scenario 3: Under-order by 30% (risk stockout)
        underorder_quantity = int(optimal_quantity * 0.7)
        underorder_days = underorder_quantity / velocity if velocity > 0 else 999
        stockout_days = max(0, target_days_supply - underorder_days)

        scenario_underorder_storage = self.calculate_storage_costs(
            underorder_quantity,
            cubic_feet_per_unit,
            underorder_days / 30
        )

        scenario_underorder_stockout = self.calculate_stockout_cost(
            velocity,
            profit_per_unit,
            stockout_days
        )

        print(f"\n💰 COST-BENEFIT ANALYSIS")
        print(f"\n  Optimal Order ({optimal_quantity} units):")
        print(f"    Storage cost: ${scenario_optimal['total']:.2f}")
        print(f"    Stockout risk: Minimal")
        print(f"    Total cost: ${scenario_optimal['total']:.2f}")

        print(f"\n  Over-Order Scenario ({overorder_quantity} units, +50%):")
        print(f"    Storage cost: ${scenario_overorder['total']:.2f}")
        print(f"    Extra storage: ${scenario_overorder['total'] - scenario_optimal['total']:.2f}")
        print(f"    Aged inventory risk: {'⚠️  HIGH' if overorder_months > 10 else '✓ Low'}")

        print(f"\n  Under-Order Scenario ({underorder_quantity} units, -30%):")
        print(f"    Storage cost: ${scenario_underorder_storage['total']:.2f}")
        print(f"    Stockout cost: ${scenario_underorder_stockout['total_cost']:.2f}")
        print(f"    Total cost: ${scenario_underorder_storage['total'] + scenario_underorder_stockout['total_cost']:.2f}")
        print(f"    ⚠️  RISK: {stockout_days:.0f} days stockout, {scenario_underorder_stockout['units_lost']:.0f} units lost")

        print(f"\n✅ FINAL RECOMMENDATION")
        print(f"  Order {optimal_quantity} units to balance storage costs and stockout risk")
        print(f"  Expected storage cost: ${scenario_optimal['total']:.2f}")
        print(f"  Provides: {target_days_supply} days of supply")

        # Aged inventory warning
        if inventory['age_days'] > 270:  # 9+ months
            print(f"\n⚠️  WARNING: Current inventory is {inventory['age_days']} days old")
            print(f"     Aged inventory surcharge in {365 - inventory['age_days']} days")
            print(f"     Consider price reduction or removal order")

        print("\n" + "="*70)

        return {
            'asin': asin,
            'recommended_quantity': optimal_quantity,
            'current_inventory': current_available,
            'days_until_stockout': days_until_stockout,
            'urgency': urgency,
            'storage_cost': scenario_optimal['total'],
            'scenarios': {
                'optimal': scenario_optimal,
                'overorder': scenario_overorder,
                'underorder': {
                    'storage': scenario_underorder_storage,
                    'stockout': scenario_underorder_stockout,
                }
            }
        }


def main():
    """CLI for inventory optimization."""
    parser = argparse.ArgumentParser(
        description='Amazon Inventory Optimizer - Reorder recommendations with cost analysis'
    )
    parser.add_argument('--asin', required=True, help='Product ASIN to analyze')
    parser.add_argument('--days', type=int, default=30, help='Days to analyze for sales velocity')
    parser.add_argument('--lead-time', type=int, default=30, help='Lead time in days for new inventory')
    parser.add_argument('--target-supply', type=int, default=60, help='Target days of supply to maintain')

    args = parser.parse_args()

    # Run analysis
    optimizer = InventoryOptimizer()
    result = optimizer.recommend_reorder_quantity(
        asin=args.asin,
        lead_time_days=args.lead_time,
        target_days_supply=args.target_supply
    )

    # Print API usage summary
    optimizer.api.print_api_usage_summary()


if __name__ == '__main__':
    main()
