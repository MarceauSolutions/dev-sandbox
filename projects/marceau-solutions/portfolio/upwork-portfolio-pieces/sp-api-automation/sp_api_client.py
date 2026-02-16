#!/usr/bin/env python3
"""
Amazon SP-API Automated Data Pipeline

This module provides automated extraction and processing of Amazon Seller Central
data via the Selling Partner API. Features include:
- Automatic token refresh and authentication
- Daily sales and inventory sync
- Profit margin calculation with fee breakdowns
- Restock recommendations based on velocity

Author: William Marceau
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

import requests
from sp_api.api import Orders, Inventory, Reports, Finances
from sp_api.base import Marketplaces, SellingApiException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProductMetrics:
    """Container for product-level metrics."""
    asin: str
    sku: str
    title: str
    units_sold: int
    revenue: float
    cost: float
    fees: float
    profit: float
    margin: float
    inventory_level: int
    days_of_stock: int
    restock_recommended: int


class AmazonDataPipeline:
    """
    Automated data pipeline for Amazon SP-API.

    Handles authentication, data extraction, and processing for
    sales, inventory, and financial data.
    """

    def __init__(self, refresh_token: str = None):
        """
        Initialize the pipeline with credentials.

        Args:
            refresh_token: LWA refresh token (uses env var if not provided)
        """
        self.credentials = {
            'refresh_token': refresh_token or os.getenv('AMAZON_REFRESH_TOKEN'),
            'lwa_app_id': os.getenv('AMAZON_LWA_APP_ID'),
            'lwa_client_secret': os.getenv('AMAZON_LWA_CLIENT_SECRET'),
            'aws_access_key': os.getenv('AMAZON_AWS_ACCESS_KEY'),
            'aws_secret_key': os.getenv('AMAZON_AWS_SECRET_KEY'),
            'role_arn': os.getenv('AMAZON_ROLE_ARN'),
        }
        self.marketplace = Marketplaces.US

        # Initialize API clients
        self._orders_api = None
        self._inventory_api = None
        self._reports_api = None
        self._finances_api = None

    @property
    def orders(self) -> Orders:
        """Lazy-load Orders API client."""
        if self._orders_api is None:
            self._orders_api = Orders(credentials=self.credentials,
                                       marketplace=self.marketplace)
        return self._orders_api

    @property
    def inventory(self) -> Inventory:
        """Lazy-load Inventory API client."""
        if self._inventory_api is None:
            self._inventory_api = Inventory(credentials=self.credentials,
                                             marketplace=self.marketplace)
        return self._inventory_api

    def get_sales_summary(self, days: int = 30) -> Dict:
        """
        Get sales summary for the specified period.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with sales metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()

        logger.info(f"Fetching sales data for last {days} days...")

        try:
            # Fetch orders
            response = self.orders.get_orders(
                CreatedAfter=start_date.isoformat(),
                CreatedBefore=end_date.isoformat(),
                OrderStatuses=['Shipped', 'Unshipped']
            )

            orders = response.payload.get('Orders', [])
            total_revenue = sum(
                float(o.get('OrderTotal', {}).get('Amount', 0))
                for o in orders
            )
            total_units = sum(
                sum(item.get('QuantityOrdered', 0) for item in o.get('OrderItems', []))
                for o in orders
            )

            return {
                'period_days': days,
                'total_orders': len(orders),
                'total_units': total_units,
                'total_revenue': round(total_revenue, 2),
                'avg_order_value': round(total_revenue / len(orders), 2) if orders else 0,
                'units_per_day': round(total_units / days, 1),
            }

        except SellingApiException as e:
            logger.error(f"SP-API Error: {e}")
            raise

    def get_inventory_health(self) -> List[Dict]:
        """
        Analyze inventory health and generate restock recommendations.

        Returns:
            List of products with inventory metrics and restock recommendations
        """
        logger.info("Analyzing inventory health...")

        # Get FBA inventory
        response = self.inventory.get_inventory_summary_marketplace(
            details=True,
            granularityType='Marketplace',
            granularityId=self.marketplace.marketplace_id
        )

        products = []
        for item in response.payload.get('inventorySummaries', []):
            asin = item.get('asin')
            sku = item.get('sellerSku')
            inventory = item.get('totalQuantity', 0)

            # Calculate velocity (units sold per day over last 30 days)
            velocity = self._calculate_velocity(sku)

            # Days of stock remaining
            days_of_stock = int(inventory / velocity) if velocity > 0 else 999

            # Restock recommendation (target 60 days of stock)
            target_stock = int(velocity * 60)
            restock_qty = max(0, target_stock - inventory)

            products.append({
                'asin': asin,
                'sku': sku,
                'inventory_level': inventory,
                'daily_velocity': round(velocity, 2),
                'days_of_stock': days_of_stock,
                'restock_recommended': restock_qty,
                'urgency': self._get_urgency(days_of_stock)
            })

        # Sort by urgency (lowest days of stock first)
        products.sort(key=lambda x: x['days_of_stock'])

        return products

    def get_profit_breakdown(self, days: int = 30) -> List[ProductMetrics]:
        """
        Calculate detailed profit breakdown by product.

        Includes: revenue, COGS, Amazon fees, net profit, margin

        Args:
            days: Period to analyze

        Returns:
            List of ProductMetrics with full profit breakdown
        """
        logger.info(f"Calculating profit breakdown for last {days} days...")

        # This would pull from multiple endpoints:
        # - Orders API for revenue
        # - Finances API for fee breakdown
        # - Your cost data (from spreadsheet or database)

        # Example structure (actual implementation would hit real APIs)
        products = []

        # In production, this loops through actual order data
        example_product = ProductMetrics(
            asin='B08EXAMPLE',
            sku='WIDGET-001',
            title='Premium Widget Set',
            units_sold=324,
            revenue=6480.00,
            cost=2592.00,  # 40% COGS
            fees=1425.60,  # ~22% Amazon fees
            profit=2462.40,
            margin=38.0,
            inventory_level=45,
            days_of_stock=12,
            restock_recommended=150
        )
        products.append(example_product)

        return products

    def generate_daily_report(self) -> Dict:
        """
        Generate comprehensive daily report.

        Combines sales, inventory, and profit data into single report.

        Returns:
            Complete daily metrics report
        """
        logger.info("Generating daily report...")

        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'sales': self.get_sales_summary(days=1),
            'sales_30d': self.get_sales_summary(days=30),
            'inventory_alerts': [
                p for p in self.get_inventory_health()
                if p['urgency'] in ['CRITICAL', 'WARNING']
            ],
            'low_stock_count': len([
                p for p in self.get_inventory_health()
                if p['days_of_stock'] < 14
            ])
        }

        return report

    def _calculate_velocity(self, sku: str) -> float:
        """Calculate daily sales velocity for a SKU."""
        # In production, this queries historical order data
        # Returns average units sold per day over last 30 days
        return 8.5  # Example value

    def _get_urgency(self, days_of_stock: int) -> str:
        """Determine restock urgency level."""
        if days_of_stock <= 7:
            return 'CRITICAL'
        elif days_of_stock <= 14:
            return 'WARNING'
        elif days_of_stock <= 30:
            return 'MONITOR'
        return 'OK'


# === Automated Daily Sync ===

def run_daily_sync():
    """
    Run automated daily data sync.

    This function is called by cron/scheduler to:
    1. Pull latest sales data
    2. Update inventory metrics
    3. Generate alerts for low stock
    4. Push to dashboard/notification system
    """
    pipeline = AmazonDataPipeline()

    # Generate report
    report = pipeline.generate_daily_report()

    # Save to file (in production, this goes to database)
    output_path = f"reports/daily_{datetime.now().strftime('%Y%m%d')}.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Daily report saved to {output_path}")

    # Send alerts for critical inventory
    critical_items = [
        item for item in report['inventory_alerts']
        if item['urgency'] == 'CRITICAL'
    ]

    if critical_items:
        logger.warning(f"ALERT: {len(critical_items)} items critically low on stock!")
        # In production: send SMS/email notification

    return report


if __name__ == '__main__':
    # Example usage
    pipeline = AmazonDataPipeline()

    print("=== Sales Summary (30 days) ===")
    sales = pipeline.get_sales_summary(days=30)
    print(json.dumps(sales, indent=2))

    print("\n=== Inventory Health ===")
    inventory = pipeline.get_inventory_health()
    for item in inventory[:5]:  # Top 5 needing restock
        print(f"{item['sku']}: {item['days_of_stock']} days left, restock {item['restock_recommended']} units")
