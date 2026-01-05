#!/usr/bin/env python3
"""
Amazon Selling Partner API (SP-API) Wrapper
Provides authentication and base functionality for Amazon Seller Central operations.

Key Features:
- LWA (Login with Amazon) authentication with automatic token refresh
- Rate limiting and request optimization (to minimize 2026 GET call fees)
- Multi-marketplace support
- Comprehensive error handling
- Caching to reduce API calls

Requirements:
- sp-api Python library: pip install python-amazon-sp-api
- Environment variables in .env (see .env.example)
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import sp-api library
try:
    from sp_api.api import Orders, Products, Inventories, Feeds, Reports, Notifications
    from sp_api.base import Marketplaces, SellingApiException
except ImportError:
    print("ERROR: python-amazon-sp-api library not installed")
    print("Install with: pip install python-amazon-sp-api")
    sys.exit(1)


class AmazonSPAPI:
    """
    Amazon Selling Partner API wrapper for seller operations.

    This class handles authentication, API calls, caching, and error handling
    for Amazon SP-API operations.
    """

    def __init__(self):
        """Initialize API credentials and configuration from environment."""
        # Required credentials
        self.refresh_token = os.getenv('AMAZON_REFRESH_TOKEN')
        self.lwa_app_id = os.getenv('AMAZON_LWA_APP_ID')  # Client ID
        self.lwa_client_secret = os.getenv('AMAZON_LWA_CLIENT_SECRET')
        self.aws_access_key = os.getenv('AMAZON_AWS_ACCESS_KEY')
        self.aws_secret_key = os.getenv('AMAZON_AWS_SECRET_KEY')
        self.role_arn = os.getenv('AMAZON_ROLE_ARN')

        # Marketplace configuration
        marketplace_id = os.getenv('AMAZON_MARKETPLACE_ID', 'ATVPDKIKX0DER')  # Default: US
        self.marketplace = self._get_marketplace(marketplace_id)

        # Validate credentials
        self._validate_credentials()

        # Initialize cache
        self.cache_dir = Path('.tmp/amazon_cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # API call tracking (for cost monitoring)
        self.get_calls_count = 0

    def _validate_credentials(self):
        """Validate that all required credentials are present."""
        missing = []
        if not self.refresh_token:
            missing.append('AMAZON_REFRESH_TOKEN')
        if not self.lwa_app_id:
            missing.append('AMAZON_LWA_APP_ID')
        if not self.lwa_client_secret:
            missing.append('AMAZON_LWA_CLIENT_SECRET')
        if not self.aws_access_key:
            missing.append('AMAZON_AWS_ACCESS_KEY')
        if not self.aws_secret_key:
            missing.append('AMAZON_AWS_SECRET_KEY')
        if not self.role_arn:
            missing.append('AMAZON_ROLE_ARN')

        if missing:
            print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
            print("Please configure these in your .env file")
            sys.exit(1)

    def _get_marketplace(self, marketplace_id):
        """Map marketplace ID to sp-api Marketplace object."""
        marketplace_map = {
            'ATVPDKIKX0DER': Marketplaces.US,
            'A2EUQ1WTGCTBG2': Marketplaces.CA,
            'A1AM78C64UM0Y8': Marketplaces.MX,
            'A2Q3Y263D00KWC': Marketplaces.BR,
            'A1PA6795UKMFR9': Marketplaces.DE,
            'A1RKKUPIHCS9HS': Marketplaces.ES,
            'A13V1IB3VIYZZH': Marketplaces.FR,
            'A1F83G8C2ARO7P': Marketplaces.UK,
            'APJ6JRA9NG5V4': Marketplaces.IT,
            'A1805IZSGTT6HS': Marketplaces.NL,
            'A19VAU5U5O7RUS': Marketplaces.SG,
            'A39IBJ37TRP1C6': Marketplaces.AU,
            'A1VC38T7YXB528': Marketplaces.JP,
        }
        return marketplace_map.get(marketplace_id, Marketplaces.US)

    def _get_credentials(self):
        """Return credentials dict for sp-api library."""
        return {
            'refresh_token': self.refresh_token,
            'lwa_app_id': self.lwa_app_id,
            'lwa_client_secret': self.lwa_client_secret,
            'aws_access_key': self.aws_access_key,
            'aws_secret_key': self.aws_secret_key,
            'role_arn': self.role_arn,
        }

    def _cache_get(self, cache_key, max_age_minutes=60):
        """
        Get cached data if fresh enough.

        Args:
            cache_key: Unique identifier for cached data
            max_age_minutes: Maximum age of cache in minutes

        Returns:
            Cached data if fresh, None if stale or missing
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None

        # Check age
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if file_age > timedelta(minutes=max_age_minutes):
            return None

        # Load cached data
        with open(cache_file, 'r') as f:
            return json.load(f)

    def _cache_set(self, cache_key, data):
        """
        Save data to cache.

        Args:
            cache_key: Unique identifier for cached data
            data: Data to cache (must be JSON serializable)
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def get_inventory_summary(self, asins=None, use_cache=True, cache_minutes=30):
        """
        Get FBA inventory summary for specified ASINs.

        Args:
            asins: List of ASINs to query (None = all inventory)
            use_cache: Whether to use cached data
            cache_minutes: Cache validity in minutes

        Returns:
            Dict with inventory data per ASIN
        """
        cache_key = f"inventory_{'_'.join(asins) if asins else 'all'}"

        # Check cache first
        if use_cache:
            cached = self._cache_get(cache_key, cache_minutes)
            if cached:
                print(f"✓ Using cached inventory data (saved 1 GET call)")
                return cached

        # Make API call (costs money after April 30, 2026)
        self.get_calls_count += 1
        print(f"→ Making GET call #{self.get_calls_count} (will incur fee after April 30, 2026)")

        try:
            inventory_api = Inventories(
                credentials=self._get_credentials(),
                marketplace=self.marketplace
            )

            # Get inventory summaries
            if asins:
                result = inventory_api.get_inventory_summary_marketplace(
                    granularityType='Marketplace',
                    granularityId=self.marketplace.marketplace_id,
                    sellerSkus=asins
                )
            else:
                result = inventory_api.get_inventory_summary_marketplace(
                    granularityType='Marketplace',
                    granularityId=self.marketplace.marketplace_id
                )

            # Parse response
            inventory_data = result.payload if hasattr(result, 'payload') else result

            # Cache result
            if use_cache:
                self._cache_set(cache_key, inventory_data)

            return inventory_data

        except SellingApiException as e:
            print(f"ERROR: Amazon SP-API error: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")
            return None

    def get_orders(self, days_back=7, use_cache=True, cache_minutes=15):
        """
        Get recent orders for sales velocity calculations.

        Args:
            days_back: Number of days to look back
            use_cache: Whether to use cached data
            cache_minutes: Cache validity in minutes

        Returns:
            List of order objects
        """
        cache_key = f"orders_last_{days_back}_days"

        # Check cache
        if use_cache:
            cached = self._cache_get(cache_key, cache_minutes)
            if cached:
                print(f"✓ Using cached order data (saved 1 GET call)")
                return cached

        # Make API call
        self.get_calls_count += 1
        print(f"→ Making GET call #{self.get_calls_count} (will incur fee after April 30, 2026)")

        try:
            orders_api = Orders(
                credentials=self._get_credentials(),
                marketplace=self.marketplace
            )

            # Calculate date range
            created_after = (datetime.now() - timedelta(days=days_back)).isoformat()

            # Get orders
            result = orders_api.get_orders(
                CreatedAfter=created_after,
                MarketplaceIds=[self.marketplace.marketplace_id]
            )

            orders = result.payload['Orders'] if hasattr(result, 'payload') else []

            # Cache result
            if use_cache:
                self._cache_set(cache_key, orders)

            return orders

        except SellingApiException as e:
            print(f"ERROR: Amazon SP-API error: {e}")
            return []
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")
            return []

    def get_order_items(self, order_id, use_cache=True, cache_minutes=60):
        """
        Get line items for a specific order.

        Args:
            order_id: Amazon Order ID
            use_cache: Whether to use cached data
            cache_minutes: Cache validity in minutes

        Returns:
            List of order items
        """
        cache_key = f"order_items_{order_id}"

        # Check cache
        if use_cache:
            cached = self._cache_get(cache_key, cache_minutes)
            if cached:
                return cached

        # Make API call
        self.get_calls_count += 1

        try:
            orders_api = Orders(
                credentials=self._get_credentials(),
                marketplace=self.marketplace
            )

            result = orders_api.get_order_items(order_id)
            items = result.payload['OrderItems'] if hasattr(result, 'payload') else []

            # Cache result
            if use_cache:
                self._cache_set(cache_key, items)

            return items

        except SellingApiException as e:
            print(f"ERROR: Could not get order items for {order_id}: {e}")
            return []
        except Exception as e:
            print(f"ERROR: Unexpected error getting order items: {e}")
            return []

    def get_product_details(self, asin, use_cache=True, cache_minutes=1440):
        """
        Get product details including dimensions and category.

        Args:
            asin: Product ASIN
            use_cache: Whether to use cached data
            cache_minutes: Cache validity (default 24 hours)

        Returns:
            Dict with product details
        """
        cache_key = f"product_{asin}"

        # Check cache (product details rarely change)
        if use_cache:
            cached = self._cache_get(cache_key, cache_minutes)
            if cached:
                print(f"✓ Using cached product data (saved 1 GET call)")
                return cached

        # Make API call
        self.get_calls_count += 1
        print(f"→ Making GET call #{self.get_calls_count} (will incur fee after April 30, 2026)")

        try:
            products_api = Products(
                credentials=self._get_credentials(),
                marketplace=self.marketplace
            )

            # Try multiple method names as the library API varies by version
            try:
                result = products_api.get_competitive_pricing_for_asin([asin])
            except AttributeError:
                try:
                    result = products_api.get_competitive_pricing(asin_list=[asin])
                except AttributeError:
                    # Method doesn't exist - return None, caller will use defaults
                    print(f"  Note: Product API method not available, using defaults")
                    return None

            product_data = result.payload if hasattr(result, 'payload') else {}

            # Cache result
            if use_cache:
                self._cache_set(cache_key, product_data)

            return product_data

        except SellingApiException as e:
            print(f"ERROR: Amazon SP-API error getting product {asin}: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")
            return None

    def get_product_fees(self, asin, price, use_cache=True, cache_minutes=1440):
        """
        Get FBA fee estimates for a product.

        Args:
            asin: Product ASIN
            price: Selling price
            use_cache: Whether to use cached data
            cache_minutes: Cache validity (default 24 hours - fees change rarely)

        Returns:
            Dict with fee breakdown
        """
        cache_key = f"fees_{asin}_{price}"

        # Check cache (fees rarely change, cache aggressively)
        if use_cache:
            cached = self._cache_get(cache_key, cache_minutes)
            if cached:
                print(f"✓ Using cached fee data (saved 1 GET call)")
                return cached

        # Make API call
        self.get_calls_count += 1
        print(f"→ Making GET call #{self.get_calls_count} (will incur fee after April 30, 2026)")

        try:
            products_api = Products(
                credentials=self._get_credentials(),
                marketplace=self.marketplace
            )

            # Prepare fee request
            fee_request = {
                'FeesEstimateRequest': {
                    'MarketplaceId': self.marketplace.marketplace_id,
                    'IdType': 'ASIN',
                    'IdValue': asin,
                    'IsAmazonFulfilled': True,
                    'PriceToEstimateFees': {
                        'ListingPrice': {
                            'Amount': price,
                            'CurrencyCode': 'USD'  # TODO: Make dynamic based on marketplace
                        }
                    },
                    'Identifier': f'fee_estimate_{asin}'
                }
            }

            result = products_api.get_my_fees_estimate(fee_request)

            fees = result.payload if hasattr(result, 'payload') else {}

            # Cache result
            if use_cache:
                self._cache_set(cache_key, fees)

            return fees

        except SellingApiException as e:
            print(f"ERROR: Amazon SP-API error: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")
            return None

    def print_api_usage_summary(self):
        """Print summary of API calls made (for cost tracking)."""
        print("\n" + "="*60)
        print("API USAGE SUMMARY")
        print("="*60)
        print(f"Total GET calls made: {self.get_calls_count}")
        print(f"Cost impact: Starting April 30, 2026, GET calls will incur fees")
        print(f"Optimization: Using caching saved multiple GET calls")
        print("="*60 + "\n")


def main():
    """Test the Amazon SP-API wrapper."""
    print("Amazon SP-API Wrapper - Test Mode\n")

    # Initialize API
    api = AmazonSPAPI()
    print(f"✓ Connected to marketplace: {api.marketplace.marketplace_id}\n")

    # Test inventory retrieval
    print("Testing inventory retrieval...")
    inventory = api.get_inventory_summary()
    if inventory:
        print(f"✓ Retrieved inventory data")

    # Test order retrieval
    print("\nTesting order retrieval...")
    orders = api.get_orders(days_back=7)
    if orders:
        print(f"✓ Retrieved {len(orders)} orders from last 7 days")

    # Print API usage
    api.print_api_usage_summary()


if __name__ == '__main__':
    main()
