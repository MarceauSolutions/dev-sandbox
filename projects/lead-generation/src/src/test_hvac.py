#!/usr/bin/env python3
"""
HVAC MCP Tests

Tests for the HVAC Distributor MCP.
Validates:
1. Core functionality (RFQ submission, quote tracking, comparison)
2. Platform integration (EMAIL connectivity, ASYNC scoring, per-RFQ billing)

Run with: python -m pytest src/mcps/hvac/test_hvac.py -v
Or directly: python src/mcps/hvac/test_hvac.py
"""

import os
import sys
import unittest
import tempfile
from datetime import date, datetime, timedelta
from decimal import Decimal

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from src.mcps.hvac.models import (
    RFQ, Quote, RFQStatus, RFQSpecifications,
    Distributor, QuoteComparison, EquipmentType
)
from src.mcps.hvac.distributor_db import DistributorDB
from src.mcps.hvac.email_sender import EmailSender
from src.mcps.hvac.quote_tracker import QuoteTracker
from src.mcps.hvac.rfq_manager import RFQManager


class TestModels(unittest.TestCase):
    """Test data models"""

    def test_rfq_specifications_to_dict(self):
        """Test RFQSpecifications serialization"""
        specs = RFQSpecifications(
            tonnage=3.0,
            seer=16,
            voltage='208-230V',
            refrigerant='R-410A'
        )
        result = specs.to_dict()

        self.assertEqual(result['tonnage'], 3.0)
        self.assertEqual(result['seer'], 16)
        self.assertEqual(result['voltage'], '208-230V')
        self.assertNotIn('btu', result)  # None values excluded

    def test_rfq_status_enum(self):
        """Test RFQ status transitions"""
        self.assertEqual(RFQStatus.PENDING.value, 'pending')
        self.assertEqual(RFQStatus.SENT.value, 'sent')
        self.assertEqual(RFQStatus.QUOTED.value, 'quoted')
        self.assertEqual(RFQStatus.EXPIRED.value, 'expired')

    def test_equipment_types(self):
        """Test equipment type enum"""
        types = [e.value for e in EquipmentType]
        self.assertIn('ac_unit', types)
        self.assertIn('furnace', types)
        self.assertIn('heat_pump', types)

    def test_quote_total_calculation(self):
        """Test Quote auto-calculates total"""
        quote = Quote(
            id='q1',
            rfq_id='rfq1',
            distributor_id='dist1',
            distributor_name='Test Dist',
            equipment_model='Model X',
            brand='Carrier',
            unit_price=Decimal('2500.00'),
            quantity_available=2,
            lead_time_days=5,
            shipping_cost=Decimal('150.00')
        )

        # total = (unit_price * quantity) + shipping
        expected = Decimal('5150.00')
        self.assertEqual(quote.total_price, expected)


class TestDistributorDB(unittest.TestCase):
    """Test distributor database"""

    def setUp(self):
        self.db = DistributorDB()

    def test_load_test_distributors(self):
        """Test that test distributors are loaded"""
        distributors = self.db.get_all_distributors()
        self.assertGreater(len(distributors), 0)

    def test_find_by_region(self):
        """Test finding distributors by region"""
        florida_dists = self.db.find_distributors(region='FL')
        self.assertGreater(len(florida_dists), 0)

        for dist in florida_dists:
            self.assertIn('FL', dist.supported_regions)

    def test_find_by_equipment_type(self):
        """Test finding distributors by equipment type"""
        ac_dists = self.db.find_distributors(equipment_type='ac_unit')
        self.assertGreater(len(ac_dists), 0)

        for dist in ac_dists:
            self.assertIn('ac_unit', dist.equipment_types)

    def test_find_by_brand(self):
        """Test finding distributors by brand"""
        carrier_dists = self.db.find_distributors(brand='Carrier')
        self.assertGreater(len(carrier_dists), 0)

        for dist in carrier_dists:
            self.assertIn('Carrier', dist.supported_brands)

    def test_get_distributors_for_rfq(self):
        """Test getting distributors for an RFQ"""
        dists = self.db.get_distributors_for_rfq(
            delivery_address='123 Main St, Naples, FL 34102',
            equipment_type='ac_unit',
            brand_preference='Carrier',
            max_distributors=3
        )

        self.assertLessEqual(len(dists), 3)
        # Should find Florida distributors with Carrier and ac_unit
        self.assertGreater(len(dists), 0)


class TestEmailSender(unittest.TestCase):
    """Test email sending (mock mode)"""

    def setUp(self):
        self.sender = EmailSender(mock_mode=True)

    def test_mock_send_rfq(self):
        """Test sending RFQ in mock mode"""
        rfq = RFQ(
            id='test-rfq-1',
            contractor_id='contractor-1',
            distributor_id='dist-1',
            equipment_type='ac_unit',
            specifications=RFQSpecifications(tonnage=3.0, seer=16),
            delivery_address='123 Main St, Naples, FL'
        )

        distributor = Distributor(
            id='dist-1',
            name='Test Distributor',
            email_address='test@example.com',
            supported_regions=['FL'],
            supported_brands=['Carrier'],
            equipment_types=['ac_unit'],
            contact_name='John Doe'
        )

        message_id = self.sender.send_rfq(rfq, distributor)

        self.assertIsNotNone(message_id)
        self.assertTrue(message_id.startswith('<rfq-'))

        # Check sent emails
        sent = self.sender.get_sent_emails()
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]['to'], 'test@example.com')
        self.assertIn('RFQ #test-rfq-1', sent[0]['subject'])


class TestQuoteTracker(unittest.TestCase):
    """Test quote tracking database"""

    def setUp(self):
        # Use temp file for test database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.tracker = QuoteTracker(db_path=self.db_path)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_create_and_get_rfq(self):
        """Test creating and retrieving RFQ"""
        rfq = RFQ(
            id='test-rfq-1',
            contractor_id='contractor-1',
            distributor_id='dist-1',
            equipment_type='ac_unit',
            specifications=RFQSpecifications(tonnage=3.0),
            delivery_address='123 Main St, Naples, FL'
        )

        self.tracker.create_rfq(rfq)
        retrieved = self.tracker.get_rfq('test-rfq-1')

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, 'test-rfq-1')
        self.assertEqual(retrieved.equipment_type, 'ac_unit')
        self.assertEqual(retrieved.status, RFQStatus.PENDING)

    def test_mark_rfq_sent(self):
        """Test marking RFQ as sent"""
        rfq = RFQ(
            id='test-rfq-2',
            contractor_id='contractor-1',
            distributor_id='dist-1',
            equipment_type='furnace',
            specifications=RFQSpecifications(),
            delivery_address='456 Oak Ave, Miami, FL'
        )

        self.tracker.create_rfq(rfq)
        self.tracker.mark_rfq_sent('test-rfq-2', '<msg-123@example.com>')

        retrieved = self.tracker.get_rfq('test-rfq-2')
        self.assertEqual(retrieved.status, RFQStatus.SENT)
        self.assertEqual(retrieved.email_message_id, '<msg-123@example.com>')
        self.assertIsNotNone(retrieved.sent_at)
        self.assertIsNotNone(retrieved.expires_at)

    def test_add_and_get_quotes(self):
        """Test adding and retrieving quotes"""
        # Create RFQ first
        rfq = RFQ(
            id='test-rfq-3',
            contractor_id='contractor-1',
            distributor_id='dist-1',
            equipment_type='heat_pump',
            specifications=RFQSpecifications(),
            delivery_address='789 Palm Blvd, Tampa, FL'
        )
        self.tracker.create_rfq(rfq)

        # Add quote
        quote = Quote(
            id='test-quote-1',
            rfq_id='test-rfq-3',
            distributor_id='dist-1',
            distributor_name='Test Dist',
            equipment_model='HP-3000',
            brand='Trane',
            unit_price=Decimal('3500.00'),
            quantity_available=5,
            lead_time_days=7,
            shipping_cost=Decimal('200.00')
        )
        self.tracker.add_quote(quote)

        # Retrieve quotes
        quotes = self.tracker.get_quotes_for_rfq('test-rfq-3')
        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0].unit_price, Decimal('3500.00'))

        # Check RFQ status updated to QUOTED
        rfq = self.tracker.get_rfq('test-rfq-3')
        self.assertEqual(rfq.status, RFQStatus.QUOTED)


class TestRFQManager(unittest.TestCase):
    """Test RFQ manager (core business logic)"""

    def setUp(self):
        # Use fresh instances with temp database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.distributor_db = DistributorDB()
        self.email_sender = EmailSender(mock_mode=True)
        self.quote_tracker = QuoteTracker(db_path=self.db_path)

        self.manager = RFQManager(
            distributor_db=self.distributor_db,
            email_sender=self.email_sender,
            quote_tracker=self.quote_tracker
        )

    def tearDown(self):
        os.unlink(self.db_path)

    def test_submit_rfq_success(self):
        """Test successful RFQ submission"""
        result = self.manager.submit_rfq(
            contractor_id='test-contractor',
            equipment_type='ac_unit',
            delivery_address='123 Main St, Naples, FL 34102',
            specifications={'tonnage': 3, 'seer': 16},
            brand_preference='Carrier'
        )

        self.assertTrue(result['success'])
        self.assertGreater(len(result['rfq_ids']), 0)
        self.assertGreater(result['distributors_contacted'], 0)

        # Verify emails were "sent" (mock mode)
        sent_emails = self.email_sender.get_sent_emails()
        self.assertEqual(len(sent_emails), result['distributors_contacted'])

    def test_submit_rfq_invalid_equipment(self):
        """Test RFQ with invalid equipment type"""
        result = self.manager.submit_rfq(
            contractor_id='test-contractor',
            equipment_type='invalid_type',
            delivery_address='123 Main St, Naples, FL'
        )

        self.assertFalse(result['success'])
        self.assertIn('Invalid equipment type', result.get('error', ''))

    def test_check_rfq_status(self):
        """Test checking RFQ status"""
        # Submit RFQ
        submit_result = self.manager.submit_rfq(
            contractor_id='test-contractor',
            equipment_type='furnace',
            delivery_address='456 Oak Ave, Naples, FL'
        )

        rfq_id = submit_result['rfq_ids'][0]

        # Check status
        status = self.manager.check_rfq_status(rfq_id)

        self.assertTrue(status['success'])
        self.assertEqual(status['status'], 'sent')
        self.assertEqual(status['quotes_received'], 0)

    def test_simulate_quote_and_compare(self):
        """Test simulating quotes and comparing them"""
        # Submit RFQ
        submit_result = self.manager.submit_rfq(
            contractor_id='test-contractor',
            equipment_type='ac_unit',
            delivery_address='789 Palm Blvd, Naples, FL',
            max_distributors=2
        )

        self.assertTrue(submit_result['success'])
        rfq_ids = submit_result['rfq_ids']

        # Simulate quotes for each RFQ
        for i, rfq_id in enumerate(rfq_ids):
            self.manager.simulate_quote_response(
                rfq_id=rfq_id,
                unit_price=2500 + (i * 200),  # Different prices
                lead_time_days=5 + i,
                quantity_available=10 - i
            )

        # Compare quotes
        comparison = self.manager.compare_quotes(rfq_ids)

        self.assertTrue(comparison['success'])
        self.assertGreater(len(comparison['quotes']), 0)
        self.assertIsNotNone(comparison.get('best_price'))
        self.assertIsNotNone(comparison.get('recommended'))


class TestPlatformIntegration(unittest.TestCase):
    """
    Test platform integration.

    Validates that HVAC MCP works with the generalized platform:
    - EMAIL connectivity type
    - ASYNC scoring profile
    - Per-RFQ billing
    """

    def test_email_connectivity_type(self):
        """
        Test EMAIL connectivity - no HTTP endpoint required.

        Validates that HVAC MCP can operate without REST API,
        using email for distributor communication instead.
        """
        # HVAC uses email, not HTTP
        sender = EmailSender(mock_mode=True)

        rfq = RFQ(
            id='email-test-rfq',
            contractor_id='contractor-1',
            distributor_id='dist-1',
            equipment_type='ac_unit',
            specifications=RFQSpecifications(),
            delivery_address='Naples, FL'
        )

        distributor = Distributor(
            id='dist-1',
            name='Email Dist',
            email_address='test@distributor.com',  # Email address, not HTTP URL
            supported_regions=['FL'],
            supported_brands=['Carrier'],
            equipment_types=['ac_unit']
        )

        # Can send via email (no HTTP)
        message_id = sender.send_rfq(rfq, distributor)
        self.assertIsNotNone(message_id)

        # Verify no HTTP calls were made (mock mode stores emails, not HTTP requests)
        sent = sender.get_sent_emails()
        self.assertEqual(len(sent), 1)
        self.assertIn('@', sent[0]['to'])  # Email address, not URL

    def test_async_workflow(self):
        """
        Test ASYNC workflow - 24-48 hour response expected.

        Validates that the RFQ system supports async responses,
        not real-time HTTP request/response.
        """
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        db_path = temp_db.name
        temp_db.close()

        try:
            tracker = QuoteTracker(db_path=db_path)

            # Create RFQ
            rfq = RFQ(
                id='async-test-rfq',
                contractor_id='contractor-1',
                distributor_id='dist-1',
                equipment_type='ac_unit',
                specifications=RFQSpecifications(),
                delivery_address='Naples, FL'
            )
            tracker.create_rfq(rfq)

            # Mark as sent with 48-hour expiry
            tracker.mark_rfq_sent('async-test-rfq', '<msg@example.com>', expiry_hours=48)

            # Verify expiry is set correctly (async expects long wait)
            retrieved = tracker.get_rfq('async-test-rfq')
            self.assertIsNotNone(retrieved.expires_at)

            expected_expiry = datetime.now() + timedelta(hours=47)  # ~48 hours
            self.assertGreater(retrieved.expires_at, expected_expiry)

        finally:
            os.unlink(db_path)

    def test_per_rfq_billing_model(self):
        """
        Test per-RFQ billing - charged per RFQ, not per API call.

        Each RFQ submission should be tracked as a billable transaction.
        """
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        db_path = temp_db.name
        temp_db.close()

        try:
            manager = RFQManager(
                distributor_db=DistributorDB(),
                email_sender=EmailSender(mock_mode=True),
                quote_tracker=QuoteTracker(db_path=db_path)
            )

            # Submit RFQ (this would be a billable event)
            result = manager.submit_rfq(
                contractor_id='billing-test',
                equipment_type='ac_unit',
                delivery_address='Naples, FL'
            )

            self.assertTrue(result['success'])

            # Each distributor contacted = 1 RFQ = 1 billable unit
            # (Platform billing would use request_id = rfq_id)
            rfq_ids = result['rfq_ids']
            self.assertGreater(len(rfq_ids), 0)

            # Verify RFQs are trackable (for billing)
            for rfq_id in rfq_ids:
                status = manager.check_rfq_status(rfq_id)
                self.assertTrue(status['success'])
                self.assertIsNotNone(status['rfq_id'])

        finally:
            os.unlink(db_path)


def run_demo():
    """Run a demo of the HVAC MCP workflow"""
    print("=" * 60)
    print("HVAC MCP Demo")
    print("=" * 60)

    # Use temp database
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db_path = temp_db.name
    temp_db.close()

    try:
        manager = RFQManager(
            distributor_db=DistributorDB(),
            email_sender=EmailSender(mock_mode=True),
            quote_tracker=QuoteTracker(db_path=db_path)
        )

        # 1. Submit RFQ
        print("\n1. Submitting RFQ for 3-ton AC unit in Naples, FL...")
        result = manager.submit_rfq(
            contractor_id='demo-contractor',
            equipment_type='ac_unit',
            delivery_address='123 Main St, Naples, FL 34102',
            specifications={'tonnage': 3, 'seer': 16},
            brand_preference='Carrier',
            max_distributors=3
        )

        if result['success']:
            print(f"   Success! Contacted {result['distributors_contacted']} distributors")
            print(f"   RFQ IDs: {result['rfq_ids']}")
            print(f"   Expected response in {result['estimated_response_hours']} hours")
        else:
            print(f"   Failed: {result.get('error')}")
            return

        # 2. Check status (no quotes yet)
        print("\n2. Checking RFQ status (before quotes)...")
        for rfq_id in result['rfq_ids']:
            status = manager.check_rfq_status(rfq_id)
            print(f"   RFQ {rfq_id}: {status['status']} - {status['distributor']}")

        # 3. Simulate quote responses
        print("\n3. Simulating quote responses from distributors...")
        quotes_data = [
            {'price': 2450, 'lead_time': 3, 'qty': 8},
            {'price': 2650, 'lead_time': 5, 'qty': 15},
            {'price': 2375, 'lead_time': 7, 'qty': 3},
        ]

        for i, (rfq_id, qdata) in enumerate(zip(result['rfq_ids'], quotes_data)):
            quote_result = manager.simulate_quote_response(
                rfq_id=rfq_id,
                unit_price=qdata['price'],
                lead_time_days=qdata['lead_time'],
                quantity_available=qdata['qty']
            )
            print(f"   Quote from {quote_result['quote']['distributor_name']}: "
                  f"${qdata['price']}/unit, {qdata['lead_time']} day lead time")

        # 4. Compare quotes
        print("\n4. Comparing quotes...")
        comparison = manager.compare_quotes(result['rfq_ids'])

        if comparison['success'] and comparison['quotes']:
            print(f"   Total quotes: {len(comparison['quotes'])}")
            print(f"\n   Best Price: {comparison['best_price']['distributor_name']} "
                  f"at ${comparison['best_price']['unit_price']}/unit")
            print(f"   Fastest: {comparison['fastest_delivery']['distributor_name']} "
                  f"({comparison['fastest_delivery']['lead_time_days']} days)")
            print(f"   Recommended: {comparison['recommended']['distributor_name']}")

            print("\n   Comparison Table:")
            print("   " + "-" * 55)
            print(f"   {'Distributor':<20} {'Price':>10} {'Lead Time':>12} {'Qty':>8}")
            print("   " + "-" * 55)
            for q in comparison['comparison_table']:
                flags = []
                if q['is_best_price']:
                    flags.append('$')
                if q['is_fastest']:
                    flags.append('F')
                if q['is_recommended']:
                    flags.append('*')
                flag_str = ' '.join(flags) if flags else ''

                print(f"   {q['distributor']:<20} ${q['unit_price']:>8} "
                      f"{q['lead_time_days']:>8} days {q['quantity']:>6} {flag_str}")
            print("   " + "-" * 55)
            print("   $ = Best Price, F = Fastest, * = Recommended")
        else:
            print("   No quotes to compare yet")

        print("\n" + "=" * 60)
        print("Demo complete!")
        print("=" * 60)

    finally:
        os.unlink(db_path)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        run_demo()
    else:
        # Run tests
        unittest.main(verbosity=2)
