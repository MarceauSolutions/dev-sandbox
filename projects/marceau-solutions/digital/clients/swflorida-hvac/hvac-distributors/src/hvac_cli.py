#!/usr/bin/env python3
"""
HVAC Distributor RFQ CLI

Command-line interface for the HVAC distributor RFQ system.
This provides a simple way to test the functionality without Claude Desktop.

Usage:
    # Submit an RFQ
    python hvac_cli.py submit --type ac_unit --address "Naples, FL" --tonnage 3 --seer 16

    # Check status
    python hvac_cli.py status RFQ-123

    # Get quotes
    python hvac_cli.py quotes RFQ-123

    # Compare quotes
    python hvac_cli.py compare RFQ-123 RFQ-456

    # Simulate a quote (for testing)
    python hvac_cli.py simulate RFQ-123 --price 2500 --lead-time 5

    # Run demo
    python hvac_cli.py demo
"""

import os
import sys
import argparse
import json
from datetime import date, timedelta

# Add src directory to path
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC_DIR)

from rfq_manager import RFQManager, get_rfq_manager
from models import EquipmentType


def submit_rfq(args):
    """Submit an RFQ to distributors"""
    manager = get_rfq_manager()

    # Build specifications from args
    specs = {}
    if args.tonnage:
        specs['tonnage'] = args.tonnage
    if args.seer:
        specs['seer'] = args.seer
    if args.btu:
        specs['btu'] = args.btu
    if args.voltage:
        specs['voltage'] = args.voltage

    # Parse needed_by_date
    needed_by = None
    if args.needed_by:
        try:
            needed_by = date.fromisoformat(args.needed_by)
        except ValueError:
            print(f"Invalid date format: {args.needed_by}. Use YYYY-MM-DD")
            return

    result = manager.submit_rfq(
        contractor_id=args.contractor or 'cli-user',
        equipment_type=args.type,
        delivery_address=args.address,
        specifications=specs,
        brand_preference=args.brand,
        needed_by_date=needed_by,
        quantity=args.quantity or 1,
        max_distributors=args.max_distributors or 3
    )

    print("\n" + "=" * 60)
    print("RFQ SUBMITTED")
    print("=" * 60)
    print(f"\nEquipment: {args.type}")
    print(f"Delivery: {args.address}")
    if specs:
        print(f"Specs: {json.dumps(specs)}")
    if args.brand:
        print(f"Brand Preference: {args.brand}")

    print(f"\nDistributors contacted: {result['distributors_contacted']}")
    print(f"RFQ IDs:")
    for rfq_id in result['rfq_ids']:
        print(f"  - {rfq_id}")

    print("\n" + "-" * 60)
    print("NOTE: Distributors typically respond within 24-48 hours.")
    print("Use 'hvac_cli.py status <RFQ_ID>' to check for quotes.")
    print("-" * 60 + "\n")


def check_status(args):
    """Check RFQ status"""
    manager = get_rfq_manager()
    result = manager.check_rfq_status(args.rfq_id)

    print("\n" + "=" * 60)
    print("RFQ STATUS")
    print("=" * 60)

    if 'error' in result:
        print(f"\nError: {result['error']}")
        return

    print(f"\nRFQ ID: {result['rfq_id']}")
    print(f"Status: {result['status']}")
    print(f"Equipment: {result['equipment_type']}")
    print(f"Created: {result['created_at']}")
    print(f"Expires: {result['expires_at']}")
    print(f"Quotes Received: {result.get('quotes_received', 0)}")

    if result.get('quotes_received', 0) > 0:
        print("\nUse 'hvac_cli.py quotes <RFQ_ID>' to view quotes.")


def get_quotes(args):
    """Get quotes for an RFQ"""
    manager = get_rfq_manager()
    result = manager.get_quotes(args.rfq_id)

    print("\n" + "=" * 60)
    print("QUOTES RECEIVED")
    print("=" * 60)

    if 'error' in result:
        print(f"\nError: {result['error']}")
        return

    print(f"\nRFQ ID: {result['rfq_id']}")
    print(f"Status: {result['status']}")
    print(f"Total Quotes: {result['total_quotes']}")

    if result['total_quotes'] == 0:
        print("\nNo quotes received yet. Check back in 24-48 hours.")
        return

    print("\n" + "-" * 60)
    for quote in result['quotes']:
        print(f"\nDistributor: {quote['distributor_name']}")
        print(f"  Unit Price: ${float(quote['unit_price']):,.2f}")
        print(f"  Quantity Available: {quote['quantity_available']}")
        print(f"  Lead Time: {quote['lead_time_days']} days")
        print(f"  Shipping: ${float(quote['shipping_cost']):,.2f}")
        print(f"  Total: ${float(quote['total_price']):,.2f}")
        print(f"  Valid Until: {quote['valid_until']}")


def compare_quotes(args):
    """Compare quotes from multiple RFQs"""
    manager = get_rfq_manager()
    result = manager.compare_quotes(
        rfq_ids=args.rfq_ids,
        sort_by=args.sort_by or 'total_value'
    )

    print("\n" + "=" * 60)
    print("QUOTE COMPARISON")
    print("=" * 60)

    if 'error' in result:
        print(f"\nError: {result['error']}")
        return

    print(f"\nTotal Quotes: {result['total_quotes']}")
    print(f"Sorted By: {result['sorted_by']}")

    if result['total_quotes'] == 0:
        print("\nNo quotes to compare. Submit RFQs and wait for responses.")
        return

    # Print comparison table
    print("\n" + "-" * 80)
    print(f"{'Distributor':<25} {'Unit Price':>12} {'Lead Time':>12} {'Shipping':>12} {'Total':>14}")
    print("-" * 80)

    for quote in result['quotes']:
        print(f"{quote['distributor_name']:<25} "
              f"${float(quote['unit_price']):>10,.2f} "
              f"{quote['lead_time_days']:>10} days "
              f"${float(quote['shipping_cost']):>10,.2f} "
              f"${float(quote['total_price']):>12,.2f}")

    print("-" * 80)

    # Print recommendations
    if result.get('best_price'):
        bp = result['best_price']
        print(f"\nBEST PRICE: {bp['distributor_name']} - ${float(bp['total_price']):,.2f}")

    if result.get('fastest_delivery'):
        fd = result['fastest_delivery']
        print(f"FASTEST: {fd['distributor_name']} - {fd['lead_time_days']} days")

    if result.get('recommended'):
        rec = result['recommended']
        print(f"\nRECOMMENDED: {rec['distributor_name']}")
        print(f"  Reason: {rec.get('reason', 'Best overall value')}")


def simulate_quote(args):
    """Simulate a quote response (for testing)"""
    manager = get_rfq_manager()
    result = manager.simulate_quote_response(
        rfq_id=args.rfq_id,
        unit_price=args.price,
        lead_time_days=args.lead_time or 5,
        quantity_available=args.quantity or 10,
        shipping_cost=args.shipping or 150.0
    )

    print("\n" + "=" * 60)
    print("SIMULATED QUOTE")
    print("=" * 60)

    if 'error' in result:
        print(f"\nError: {result['error']}")
        return

    quote = result.get('quote', {})
    unit_price = float(quote.get('unit_price', 0))
    total_price = float(quote.get('total_price', 0))
    print(f"\nQuote ID: {result['quote_id']}")
    print(f"RFQ ID: {result['rfq_id']}")
    print(f"Distributor: {quote.get('distributor_name', 'Unknown')}")
    print(f"Unit Price: ${unit_price:,.2f}")
    print(f"Lead Time: {quote.get('lead_time_days', 0)} days")
    print(f"Total: ${total_price:,.2f}")
    print(f"\nUse 'hvac_cli.py quotes {args.rfq_id}' to see all quotes.")


def run_demo(args):
    """Run a demo of the full workflow"""
    print("\n" + "=" * 60)
    print("HVAC DISTRIBUTOR RFQ DEMO")
    print("=" * 60)

    manager = get_rfq_manager()

    # Step 1: Submit RFQ
    print("\n[Step 1] Submitting RFQ for 3-ton AC unit...")
    result = manager.submit_rfq(
        contractor_id='demo-contractor',
        equipment_type='ac_unit',
        delivery_address='123 Main St, Naples, FL 34102',
        specifications={'tonnage': 3, 'seer': 16},
        brand_preference='Carrier',
        quantity=1,
        max_distributors=3
    )

    print(f"  Distributors contacted: {result['distributors_contacted']}")
    rfq_ids = result['rfq_ids']
    print(f"  RFQ IDs: {rfq_ids}")

    # Step 2: Check status (should be pending/sent)
    print(f"\n[Step 2] Checking status of first RFQ...")
    status = manager.check_rfq_status(rfq_ids[0])
    print(f"  Status: {status['status']}")
    print(f"  Quotes: {status.get('quotes_received', 0)}")

    # Step 3: Simulate quotes
    print(f"\n[Step 3] Simulating quote responses...")
    prices = [2450.00, 2650.00, 2380.00]
    lead_times = [5, 3, 7]

    for i, rfq_id in enumerate(rfq_ids[:len(prices)]):
        sim_result = manager.simulate_quote_response(
            rfq_id=rfq_id,
            unit_price=prices[i],
            lead_time_days=lead_times[i],
            quantity_available=5,
            shipping_cost=125.00
        )
        quote = sim_result.get('quote', {})
        unit_price = float(quote.get('unit_price', 0))
        print(f"  Quote from {quote.get('distributor_name', 'Unknown')}: "
              f"${unit_price:,.2f} ({quote.get('lead_time_days', 0)} days)")

    # Step 4: Get quotes for first RFQ
    print(f"\n[Step 4] Getting quotes for first RFQ...")
    quotes = manager.get_quotes(rfq_ids[0])
    if quotes['total_quotes'] > 0:
        q = quotes['quotes'][0]
        print(f"  {q['distributor_name']}: ${float(q['total_price']):,.2f}")
    else:
        print("  No quotes yet (this RFQ may not have been simulated)")

    # Step 5: Compare all quotes
    print(f"\n[Step 5] Comparing quotes across all RFQs...")
    comparison = manager.compare_quotes(rfq_ids, sort_by='total_value')
    print(f"  Total quotes: {comparison['total_quotes']}")

    if comparison['total_quotes'] > 0:
        print("\n  " + "-" * 70)
        print(f"  {'Distributor':<25} {'Price':>12} {'Lead Time':>12} {'Total':>14}")
        print("  " + "-" * 70)

        for q in comparison['quotes']:
            print(f"  {q['distributor_name']:<25} "
                  f"${float(q['unit_price']):>10,.2f} "
                  f"{q['lead_time_days']:>10} days "
                  f"${float(q['total_price']):>12,.2f}")

        print("  " + "-" * 70)

        if comparison.get('best_price'):
            bp = comparison['best_price']
            print(f"\n  BEST PRICE: {bp['distributor_name']} - ${float(bp['total_price']):,.2f}")

        if comparison.get('fastest_delivery'):
            fd = comparison['fastest_delivery']
            print(f"  FASTEST: {fd['distributor_name']} - {fd['lead_time_days']} days")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nThis demo ran in MOCK EMAIL MODE.")
    print("In production, RFQs would be sent via SMTP to real distributors.")


def main():
    parser = argparse.ArgumentParser(
        description='HVAC Distributor RFQ CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python hvac_cli.py submit --type ac_unit --address "Naples, FL" --tonnage 3
  python hvac_cli.py status RFQ-abc123
  python hvac_cli.py quotes RFQ-abc123
  python hvac_cli.py compare RFQ-abc123 RFQ-def456
  python hvac_cli.py simulate RFQ-abc123 --price 2500
  python hvac_cli.py demo
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Submit command
    submit_parser = subparsers.add_parser('submit', help='Submit an RFQ')
    submit_parser.add_argument('--type', '-t', required=True,
                               choices=[e.value for e in EquipmentType],
                               help='Equipment type')
    submit_parser.add_argument('--address', '-a', required=True,
                               help='Delivery address')
    submit_parser.add_argument('--tonnage', type=float, help='AC/heat pump tonnage')
    submit_parser.add_argument('--seer', type=int, help='SEER rating')
    submit_parser.add_argument('--btu', type=int, help='BTU capacity')
    submit_parser.add_argument('--voltage', help='Voltage requirements')
    submit_parser.add_argument('--brand', '-b', help='Brand preference')
    submit_parser.add_argument('--quantity', '-q', type=int, help='Number of units')
    submit_parser.add_argument('--needed-by', help='Need by date (YYYY-MM-DD)')
    submit_parser.add_argument('--contractor', help='Contractor ID')
    submit_parser.add_argument('--max-distributors', type=int, help='Max distributors (default 3)')

    # Status command
    status_parser = subparsers.add_parser('status', help='Check RFQ status')
    status_parser.add_argument('rfq_id', help='RFQ ID to check')

    # Quotes command
    quotes_parser = subparsers.add_parser('quotes', help='Get quotes for an RFQ')
    quotes_parser.add_argument('rfq_id', help='RFQ ID')

    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare quotes')
    compare_parser.add_argument('rfq_ids', nargs='+', help='RFQ IDs to compare')
    compare_parser.add_argument('--sort-by', choices=['price', 'lead_time', 'total_value'],
                                default='total_value', help='Sort criteria')

    # Simulate command
    simulate_parser = subparsers.add_parser('simulate', help='Simulate a quote (testing)')
    simulate_parser.add_argument('rfq_id', help='RFQ ID')
    simulate_parser.add_argument('--price', '-p', type=float, required=True,
                                  help='Unit price')
    simulate_parser.add_argument('--lead-time', '-l', type=int, default=5,
                                  help='Lead time in days')
    simulate_parser.add_argument('--quantity', '-q', type=int, default=10,
                                  help='Quantity available')
    simulate_parser.add_argument('--shipping', '-s', type=float, default=150.0,
                                  help='Shipping cost')

    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run a demo of the full workflow')

    args = parser.parse_args()

    if args.command == 'submit':
        submit_rfq(args)
    elif args.command == 'status':
        check_status(args)
    elif args.command == 'quotes':
        get_quotes(args)
    elif args.command == 'compare':
        compare_quotes(args)
    elif args.command == 'simulate':
        simulate_quote(args)
    elif args.command == 'demo':
        run_demo(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
