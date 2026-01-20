"""
Elder Tech Procurement - Inquiry Manager

Core business logic for device procurement.
Based on the HVAC rfq_manager.py pattern.

This orchestrates:
- Finding matching wholesalers
- Submitting price inquiries via email
- Tracking inquiry status
- Comparing quotes
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Any
import uuid

from models import (
    PriceInquiry, PriceQuote, InquiryStatus, DeviceSpecifications,
    Wholesaler, QuoteComparison, DeviceType
)
from wholesaler_db import WholesalerDB, get_wholesaler_db
from email_sender import EmailSender, get_email_sender, NoEmailError

logger = logging.getLogger(__name__)


class InquiryManager:
    """
    Core business logic for device procurement.

    Provides:
    - submit_inquiry(): Send inquiry to matching wholesalers
    - check_inquiry_status(): Get current status
    - get_quotes(): Retrieve quotes for an inquiry
    - compare_quotes(): Compare quotes across wholesalers
    """

    def __init__(
        self,
        wholesaler_db: Optional[WholesalerDB] = None,
        email_sender: Optional[EmailSender] = None
    ):
        self.wholesalers = wholesaler_db or get_wholesaler_db()
        self.email_sender = email_sender or get_email_sender()

        # In-memory storage for MVP (replace with DB in production)
        self.inquiries: Dict[str, PriceInquiry] = {}
        self.quotes: Dict[str, List[PriceQuote]] = {}  # inquiry_id -> quotes

    def submit_inquiry(
        self,
        device_type: str,
        quantity: int = 1,
        model: Optional[str] = None,
        storage_gb: Optional[int] = None,
        condition: str = 'new',
        connectivity: str = 'wifi',
        ship_to_address: Optional[str] = None,
        needed_by_date: Optional[date] = None,
        accessories: Optional[List[str]] = None,
        max_wholesalers: int = 3,
        requester_id: str = 'eldertech-default'
    ) -> Dict[str, Any]:
        """
        Submit price inquiry to matching wholesalers.

        1. Find wholesalers matching device type and condition
        2. Create inquiry for each wholesaler
        3. Send email or generate contact form text
        4. Track inquiries

        Args:
            device_type: Type of device (ipad, android_tablet, etc.)
            quantity: Number of units needed
            model: Specific model (e.g., 'iPad 11th Generation')
            storage_gb: Storage capacity
            condition: Device condition (new, refurbished_a, etc.)
            connectivity: wifi or wifi_cellular
            ship_to_address: Delivery address
            needed_by_date: When devices are needed
            accessories: List of accessories needed
            max_wholesalers: Max wholesalers to contact
            requester_id: ID of the requester

        Returns:
            {
                'success': bool,
                'inquiry_ids': List[str],
                'wholesalers_contacted': int,
                'contact_forms_needed': List[dict],
                'message': str
            }
        """
        # Validate device type
        valid_types = [e.value for e in DeviceType]
        if device_type not in valid_types:
            return {
                'success': False,
                'inquiry_ids': [],
                'wholesalers_contacted': 0,
                'error': f"Invalid device type. Must be one of: {', '.join(valid_types)}"
            }

        # Find matching wholesalers
        wholesalers = self.wholesalers.get_wholesalers_for_inquiry(
            device_type=device_type,
            condition=condition,
            quantity=quantity,
            max_wholesalers=max_wholesalers
        )

        if not wholesalers:
            return {
                'success': False,
                'inquiry_ids': [],
                'wholesalers_contacted': 0,
                'error': f"No wholesalers found for {device_type} in {condition} condition"
            }

        # Create specifications
        specs = DeviceSpecifications(
            model=model,
            storage_gb=storage_gb,
            color=None,
            connectivity=connectivity,
            condition=condition,
            accessories_needed=accessories or []
        )

        # Create and send inquiries
        inquiry_ids = []
        emails_sent = 0
        contact_forms_needed = []
        errors = []

        for wholesaler in wholesalers:
            inquiry_id = str(uuid.uuid4())[:8]

            inquiry = PriceInquiry(
                id=inquiry_id,
                requester_id=requester_id,
                wholesaler_id=wholesaler.id,
                device_type=device_type,
                specifications=specs,
                quantity=quantity,
                ship_to_address=ship_to_address,
                needed_by_date=needed_by_date,
                status=InquiryStatus.PENDING,
                expires_at=datetime.now() + timedelta(days=7)
            )

            try:
                # Store inquiry
                self.inquiries[inquiry_id] = inquiry
                self.quotes[inquiry_id] = []

                # Try to send email
                if wholesaler.email_address:
                    message_id = self.email_sender.send_inquiry(inquiry, wholesaler)
                    inquiry.email_message_id = message_id
                    inquiry.status = InquiryStatus.SENT
                    inquiry.sent_at = datetime.now()
                    emails_sent += 1
                    logger.info(f"Inquiry {inquiry_id} sent to {wholesaler.name}")
                else:
                    # Generate contact form text
                    form_text = self.email_sender.generate_contact_form_text(inquiry, wholesaler)
                    contact_forms_needed.append({
                        'inquiry_id': inquiry_id,
                        'wholesaler_name': wholesaler.name,
                        'contact_form_url': wholesaler.contact_form_url,
                        'text_to_paste': form_text
                    })
                    logger.info(f"Inquiry {inquiry_id} needs manual contact form: {wholesaler.name}")

                inquiry_ids.append(inquiry_id)

            except NoEmailError as e:
                # Wholesaler has no email, add to contact forms
                form_text = self.email_sender.generate_contact_form_text(inquiry, wholesaler)
                contact_forms_needed.append({
                    'inquiry_id': inquiry_id,
                    'wholesaler_name': wholesaler.name,
                    'contact_form_url': wholesaler.contact_form_url,
                    'text_to_paste': form_text
                })
                inquiry_ids.append(inquiry_id)

            except Exception as e:
                logger.error(f"Failed to create inquiry for {wholesaler.name}: {e}")
                errors.append(f"{wholesaler.name}: {str(e)}")

        if not inquiry_ids:
            return {
                'success': False,
                'inquiry_ids': [],
                'wholesalers_contacted': 0,
                'error': f"Failed to create any inquiries: {'; '.join(errors)}"
            }

        # Build response message
        message_parts = []
        if emails_sent > 0:
            message_parts.append(f"Sent {emails_sent} email(s)")
        if contact_forms_needed:
            message_parts.append(f"{len(contact_forms_needed)} need manual contact form submission")

        return {
            'success': True,
            'inquiry_ids': inquiry_ids,
            'wholesalers_contacted': len(inquiry_ids),
            'emails_sent': emails_sent,
            'contact_forms_needed': contact_forms_needed,
            'wholesalers': [
                {
                    'id': w.id,
                    'name': w.name,
                    'avg_response_hours': w.avg_response_hours,
                    'rating': w.rating,
                    'has_email': bool(w.email_address)
                }
                for w in wholesalers[:len(inquiry_ids)]
            ],
            'message': '. '.join(message_parts) + '.'
        }

    def check_inquiry_status(self, inquiry_id: str) -> Dict[str, Any]:
        """
        Check the status of an inquiry.

        Args:
            inquiry_id: The inquiry ID to check

        Returns:
            Inquiry status and details
        """
        inquiry = self.inquiries.get(inquiry_id)

        if not inquiry:
            return {
                'success': False,
                'error': f"Inquiry {inquiry_id} not found"
            }

        # Get quotes for this inquiry
        quotes = self.quotes.get(inquiry_id, [])

        # Get wholesaler info
        wholesaler = self.wholesalers.get_wholesaler(inquiry.wholesaler_id)

        return {
            'success': True,
            'inquiry_id': inquiry_id,
            'status': inquiry.status.value,
            'device_type': inquiry.device_type,
            'quantity': inquiry.quantity,
            'wholesaler': wholesaler.name if wholesaler else inquiry.wholesaler_id,
            'wholesaler_email': wholesaler.email_address if wholesaler else None,
            'quotes_received': len(quotes),
            'quotes': [q.to_dict() for q in quotes],
            'sent_at': inquiry.sent_at.isoformat() if inquiry.sent_at else None,
            'expires_at': inquiry.expires_at.isoformat() if inquiry.expires_at else None,
            'created_at': inquiry.created_at.isoformat()
        }

    def add_quote(
        self,
        inquiry_id: str,
        unit_price: float,
        quantity_available: int,
        lead_time_days: int = 5,
        shipping_cost: float = 0.0,
        warranty_months: int = 12,
        device_model: str = 'iPad',
        brand: str = 'Apple',
        condition: str = 'new',
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a quote response (manual entry or simulated).

        In production, quotes come via email. This method allows
        manual entry or testing the comparison flow.

        Args:
            inquiry_id: The inquiry to respond to
            unit_price: Unit price for the device
            Other details about the quote

        Returns:
            Created quote details
        """
        inquiry = self.inquiries.get(inquiry_id)

        if not inquiry:
            return {
                'success': False,
                'error': f"Inquiry {inquiry_id} not found"
            }

        wholesaler = self.wholesalers.get_wholesaler(inquiry.wholesaler_id)

        quote = PriceQuote(
            id=str(uuid.uuid4())[:8],
            inquiry_id=inquiry_id,
            wholesaler_id=inquiry.wholesaler_id,
            wholesaler_name=wholesaler.name if wholesaler else inquiry.wholesaler_id,
            device_model=device_model,
            brand=brand,
            unit_price=Decimal(str(unit_price)),
            quantity_available=quantity_available,
            condition=condition,
            lead_time_days=lead_time_days,
            shipping_cost=Decimal(str(shipping_cost)),
            warranty_months=warranty_months,
            notes=notes
        )

        # Store quote
        if inquiry_id not in self.quotes:
            self.quotes[inquiry_id] = []
        self.quotes[inquiry_id].append(quote)

        # Update inquiry status
        inquiry.status = InquiryStatus.QUOTED

        return {
            'success': True,
            'quote_id': quote.id,
            'inquiry_id': inquiry_id,
            'quote': quote.to_dict(),
            'message': f"Quote added from {quote.wholesaler_name}"
        }

    def compare_quotes(
        self,
        inquiry_ids: List[str],
        sort_by: str = 'total_value'
    ) -> Dict[str, Any]:
        """
        Compare quotes from multiple inquiries/wholesalers.

        Identifies:
        - Best price (lowest unit price)
        - Fastest delivery (shortest lead time)
        - Best warranty (longest coverage)
        - Recommended (best overall value)

        Args:
            inquiry_ids: List of inquiry IDs to compare
            sort_by: How to sort ('price', 'lead_time', 'warranty', 'total_value')

        Returns:
            QuoteComparison as dict
        """
        if not inquiry_ids:
            return {
                'success': False,
                'error': "No inquiry IDs provided"
            }

        # Collect all quotes
        all_quotes = []
        for inquiry_id in inquiry_ids:
            quotes = self.quotes.get(inquiry_id, [])
            all_quotes.extend(quotes)

        if not all_quotes:
            # Check if inquiries exist
            existing = [self.inquiries.get(iid) for iid in inquiry_ids]
            existing = [i for i in existing if i is not None]

            if not existing:
                return {
                    'success': False,
                    'error': "No inquiries found with those IDs"
                }

            return {
                'success': True,
                'inquiry_ids': inquiry_ids,
                'quotes': [],
                'total_quotes': 0,
                'message': "No quotes received yet. Check back later or contact wholesalers directly."
            }

        # Find best in each category
        best_price = min(all_quotes, key=lambda q: q.unit_price)
        fastest = min(all_quotes, key=lambda q: q.lead_time_days)
        best_warranty = max(all_quotes, key=lambda q: q.warranty_months)
        recommended = self._calculate_recommended(all_quotes)

        # Sort quotes
        if sort_by == 'price':
            all_quotes.sort(key=lambda q: q.unit_price)
        elif sort_by == 'lead_time':
            all_quotes.sort(key=lambda q: q.lead_time_days)
        elif sort_by == 'warranty':
            all_quotes.sort(key=lambda q: q.warranty_months, reverse=True)
        else:  # total_value
            all_quotes.sort(key=lambda q: (q.unit_price, q.lead_time_days))

        # Build comparison table
        comparison_table = []
        for q in all_quotes:
            comparison_table.append({
                'wholesaler': q.wholesaler_name,
                'device_model': q.device_model,
                'condition': q.condition,
                'unit_price': str(q.unit_price),
                'quantity_available': q.quantity_available,
                'lead_time_days': q.lead_time_days,
                'shipping': str(q.shipping_cost),
                'warranty_months': q.warranty_months,
                'total_per_unit': str(q.unit_price + (q.shipping_cost / q.quantity_available if q.quantity_available > 0 else Decimal('0'))),
                'is_best_price': q.id == best_price.id,
                'is_fastest': q.id == fastest.id,
                'is_best_warranty': q.id == best_warranty.id,
                'is_recommended': q.id == recommended.id
            })

        # Generate notes
        notes = self._generate_comparison_notes(all_quotes, best_price, fastest, best_warranty, recommended)

        comparison = QuoteComparison(
            inquiry_ids=inquiry_ids,
            quotes=all_quotes,
            best_price=best_price,
            fastest_delivery=fastest,
            best_warranty=best_warranty,
            recommended=recommended,
            comparison_notes=notes
        )

        result = comparison.to_dict()
        result['success'] = True
        result['comparison_table'] = comparison_table

        return result

    def _calculate_recommended(self, quotes: List[PriceQuote]) -> PriceQuote:
        """
        Calculate recommended quote based on weighted scoring.

        Scoring factors:
        - Price: 40% weight
        - Lead time: 30% weight
        - Warranty: 20% weight
        - Availability: 10% weight
        """
        if len(quotes) == 1:
            return quotes[0]

        # Normalize scores
        min_price = min(float(q.unit_price) for q in quotes)
        max_price = max(float(q.unit_price) for q in quotes)
        min_lead = min(q.lead_time_days for q in quotes)
        max_lead = max(q.lead_time_days for q in quotes)
        max_warranty = max(q.warranty_months for q in quotes)
        max_qty = max(q.quantity_available for q in quotes)

        price_range = max_price - min_price or 1
        lead_range = max_lead - min_lead or 1

        def score_quote(q: PriceQuote) -> float:
            # Lower price = higher score (inverted)
            price_score = 1 - ((float(q.unit_price) - min_price) / price_range)

            # Lower lead time = higher score (inverted)
            lead_score = 1 - ((q.lead_time_days - min_lead) / lead_range)

            # Higher warranty = higher score
            warranty_score = q.warranty_months / max_warranty if max_warranty > 0 else 1

            # Higher availability = higher score
            qty_score = q.quantity_available / max_qty if max_qty > 0 else 1

            # Weighted total
            return (price_score * 0.4) + (lead_score * 0.3) + (warranty_score * 0.2) + (qty_score * 0.1)

        return max(quotes, key=score_quote)

    def _generate_comparison_notes(
        self,
        quotes: List[PriceQuote],
        best_price: PriceQuote,
        fastest: PriceQuote,
        best_warranty: PriceQuote,
        recommended: PriceQuote
    ) -> str:
        """Generate human-readable comparison notes"""
        notes = []

        notes.append(f"Compared {len(quotes)} quote(s) from wholesalers.")

        # Check if one quote wins all categories
        if best_price == fastest == best_warranty == recommended:
            notes.append(
                f"{best_price.wholesaler_name} offers the best overall value: "
                f"${best_price.unit_price}/unit, {best_price.lead_time_days} day delivery, "
                f"{best_price.warranty_months} month warranty."
            )
        else:
            notes.append(f"Best Price: {best_price.wholesaler_name} at ${best_price.unit_price}/unit")
            notes.append(f"Fastest Delivery: {fastest.wholesaler_name} ({fastest.lead_time_days} days)")
            notes.append(f"Best Warranty: {best_warranty.wholesaler_name} ({best_warranty.warranty_months} months)")
            notes.append(f"Recommended: {recommended.wholesaler_name} (best overall value)")

        return " ".join(notes)

    def get_all_inquiries(self, requester_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all inquiries, optionally filtered by requester.

        Args:
            requester_id: Optional filter by requester

        Returns:
            List of inquiries
        """
        inquiries = list(self.inquiries.values())

        if requester_id:
            inquiries = [i for i in inquiries if i.requester_id == requester_id]

        return {
            'success': True,
            'total_inquiries': len(inquiries),
            'inquiries': [
                {
                    'inquiry_id': i.id,
                    'device_type': i.device_type,
                    'quantity': i.quantity,
                    'status': i.status.value,
                    'wholesaler_id': i.wholesaler_id,
                    'created_at': i.created_at.isoformat(),
                    'quotes_received': len(self.quotes.get(i.id, []))
                }
                for i in inquiries
            ]
        }


# Singleton instance
_manager_instance: Optional[InquiryManager] = None


def get_inquiry_manager() -> InquiryManager:
    """Get the singleton InquiryManager instance"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = InquiryManager()
    return _manager_instance


# CLI for testing
if __name__ == '__main__':
    import sys

    print("Elder Tech Procurement - Inquiry Manager\n")

    manager = InquiryManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'submit':
            # Submit test inquiry for iPads
            result = manager.submit_inquiry(
                device_type='ipad',
                quantity=5,
                model='iPad 11th Generation',
                storage_gb=64,
                condition='new',
                connectivity='wifi',
                ship_to_address='Naples, FL 34102',
                max_wholesalers=3
            )

            print("Inquiry Submission Result:")
            print(f"  Success: {result['success']}")
            print(f"  Inquiry IDs: {result.get('inquiry_ids', [])}")
            print(f"  Emails Sent: {result.get('emails_sent', 0)}")

            if result.get('contact_forms_needed'):
                print("\nContact Forms Needed:")
                for form in result['contact_forms_needed']:
                    print(f"  - {form['wholesaler_name']}")
                    print(f"    URL: {form['contact_form_url']}")
                    print(f"    Inquiry ID: {form['inquiry_id']}")

            print(f"\nMessage: {result.get('message', '')}")

        elif command == 'demo':
            # Full demo with simulated quotes
            print("Running full procurement demo...\n")

            # 1. Submit inquiry
            result = manager.submit_inquiry(
                device_type='ipad',
                quantity=5,
                model='iPad 11th Generation',
                storage_gb=64,
                condition='new',
                max_wholesalers=3
            )

            print(f"1. Submitted {len(result['inquiry_ids'])} inquiries\n")

            # 2. Simulate quotes from each wholesaler
            prices = [299, 285, 310]  # Different price points
            lead_times = [3, 5, 2]
            warranties = [12, 6, 18]

            for i, inquiry_id in enumerate(result['inquiry_ids'][:3]):
                manager.add_quote(
                    inquiry_id=inquiry_id,
                    unit_price=prices[i],
                    quantity_available=10 + i * 5,
                    lead_time_days=lead_times[i],
                    shipping_cost=25.0,
                    warranty_months=warranties[i],
                    device_model='iPad 11th Gen 64GB',
                    brand='Apple',
                    condition='new'
                )

            print("2. Simulated quotes from wholesalers\n")

            # 3. Compare quotes
            comparison = manager.compare_quotes(result['inquiry_ids'])

            print("3. Quote Comparison:")
            print("-" * 60)

            for row in comparison.get('comparison_table', []):
                rec = " [RECOMMENDED]" if row['is_recommended'] else ""
                best = " [BEST PRICE]" if row['is_best_price'] else ""
                fast = " [FASTEST]" if row['is_fastest'] else ""
                warranty = " [BEST WARRANTY]" if row['is_best_warranty'] else ""

                print(f"\n  {row['wholesaler']}{rec}{best}{fast}{warranty}")
                print(f"    Price: ${row['unit_price']}/unit")
                print(f"    Lead Time: {row['lead_time_days']} days")
                print(f"    Warranty: {row['warranty_months']} months")
                print(f"    Available: {row['quantity_available']} units")

            print("\n" + "-" * 60)
            print(f"Summary: {comparison.get('comparison_notes', '')}")

        else:
            print("Usage:")
            print("  python inquiry_manager.py submit  - Submit test inquiry")
            print("  python inquiry_manager.py demo    - Run full demo with simulated quotes")
    else:
        print("Run 'python inquiry_manager.py demo' for full demonstration")
