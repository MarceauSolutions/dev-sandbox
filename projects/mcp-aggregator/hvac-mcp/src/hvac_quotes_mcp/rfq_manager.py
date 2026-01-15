"""
HVAC RFQ Manager

Core business logic for HVAC RFQ management.
Analogous to comparison.py in rideshare - the main algorithm class.

This orchestrates:
- Finding matching distributors
- Submitting RFQs via email
- Tracking quote status
- Comparing quotes
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional, Any
import uuid

from .models import (
    RFQ, Quote, RFQStatus, RFQSpecifications,
    Distributor, QuoteComparison, EquipmentType
)
from .distributor_db import DistributorDB, get_distributor_db
from .email_sender import EmailSender, get_email_sender
from .quote_tracker import QuoteTracker, get_quote_tracker

logger = logging.getLogger(__name__)


class RFQManager:
    """
    Core business logic for HVAC RFQ management.

    Provides:
    - submit_rfq(): Send RFQ to matching distributors
    - check_rfq_status(): Get current status of an RFQ
    - get_quotes(): Retrieve quotes for an RFQ
    - compare_quotes(): Compare quotes across distributors

    This validates the platform's support for:
    - EMAIL connectivity (no HTTP API calls)
    - ASYNC scoring (24-48 hour response times)
    - Per-RFQ billing
    """

    def __init__(
        self,
        distributor_db: Optional[DistributorDB] = None,
        email_sender: Optional[EmailSender] = None,
        quote_tracker: Optional[QuoteTracker] = None
    ):
        self.distributors = distributor_db or get_distributor_db()
        self.email_sender = email_sender or get_email_sender()
        self.quote_tracker = quote_tracker or get_quote_tracker()

    def submit_rfq(
        self,
        contractor_id: str,
        equipment_type: str,
        delivery_address: str,
        specifications: Optional[Dict[str, Any]] = None,
        brand_preference: Optional[str] = None,
        needed_by_date: Optional[date] = None,
        quantity: int = 1,
        max_distributors: int = 3
    ) -> Dict[str, Any]:
        """
        Submit RFQ to matching distributors.

        1. Find distributors matching region/brand/equipment
        2. Create RFQ for each distributor
        3. Send email to each distributor
        4. Track RFQs in database

        Args:
            contractor_id: Who is requesting the quote
            equipment_type: Type of equipment (ac_unit, furnace, etc.)
            delivery_address: Delivery address (used to determine region)
            specifications: Equipment specs (tonnage, SEER, BTU, etc.)
            brand_preference: Preferred brand (optional)
            needed_by_date: When equipment is needed (optional)
            quantity: Number of units (default: 1)
            max_distributors: Max distributors to contact (default: 3)

        Returns:
            {
                'success': bool,
                'rfq_ids': List[str],
                'distributors_contacted': int,
                'estimated_response_hours': int,
                'message': str
            }
        """
        # Validate equipment type
        valid_types = [e.value for e in EquipmentType]
        if equipment_type not in valid_types:
            return {
                'success': False,
                'rfq_ids': [],
                'distributors_contacted': 0,
                'error': f"Invalid equipment type. Must be one of: {', '.join(valid_types)}"
            }

        # Find matching distributors
        distributors = self.distributors.get_distributors_for_rfq(
            delivery_address=delivery_address,
            equipment_type=equipment_type,
            brand_preference=brand_preference,
            max_distributors=max_distributors
        )

        if not distributors:
            return {
                'success': False,
                'rfq_ids': [],
                'distributors_contacted': 0,
                'error': f"No distributors found for {equipment_type} in that region"
            }

        # Parse specifications
        specs = RFQSpecifications.from_dict(specifications or {})

        # Create and send RFQs
        rfq_ids = []
        errors = []
        total_response_hours = 0

        for distributor in distributors:
            rfq_id = str(uuid.uuid4())[:8]  # Short ID for easy reference

            rfq = RFQ(
                id=rfq_id,
                contractor_id=contractor_id,
                distributor_id=distributor.id,
                equipment_type=equipment_type,
                specifications=specs,
                delivery_address=delivery_address,
                quantity=quantity,
                brand_preference=brand_preference,
                needed_by_date=needed_by_date,
                status=RFQStatus.PENDING
            )

            try:
                # Store RFQ
                self.quote_tracker.create_rfq(rfq)

                # Send email
                message_id = self.email_sender.send_rfq(rfq, distributor)

                # Mark as sent
                self.quote_tracker.mark_rfq_sent(rfq_id, message_id)

                rfq_ids.append(rfq_id)
                total_response_hours += distributor.avg_response_hours

                logger.info(f"RFQ {rfq_id} sent to {distributor.name}")

            except Exception as e:
                logger.error(f"Failed to send RFQ to {distributor.name}: {e}")
                errors.append(f"{distributor.name}: {str(e)}")

        if not rfq_ids:
            return {
                'success': False,
                'rfq_ids': [],
                'distributors_contacted': 0,
                'error': f"Failed to send any RFQs: {'; '.join(errors)}"
            }

        # Calculate average response time
        avg_response_hours = total_response_hours // len(rfq_ids)

        return {
            'success': True,
            'rfq_ids': rfq_ids,
            'distributors_contacted': len(rfq_ids),
            'estimated_response_hours': avg_response_hours,
            'distributors': [
                {
                    'id': d.id,
                    'name': d.name,
                    'avg_response_hours': d.avg_response_hours,
                    'rating': d.rating
                }
                for d in distributors[:len(rfq_ids)]
            ],
            'message': f"RFQ sent to {len(rfq_ids)} distributor(s). Expected response in {avg_response_hours} hours."
        }

    def check_rfq_status(self, rfq_id: str) -> Dict[str, Any]:
        """
        Check the status of an RFQ.

        Returns current status and any received quotes.

        Args:
            rfq_id: The RFQ ID to check

        Returns:
            {
                'success': bool,
                'rfq_id': str,
                'status': str,
                'quotes_received': int,
                'quotes': List[Dict],
                'distributor': str,
                'sent_at': str,
                'expires_at': str
            }
        """
        # Expire old RFQs first
        self.quote_tracker.expire_old_rfqs()

        rfq = self.quote_tracker.get_rfq(rfq_id)

        if not rfq:
            return {
                'success': False,
                'error': f"RFQ {rfq_id} not found"
            }

        # Get any quotes
        quotes = self.quote_tracker.get_quotes_for_rfq(rfq_id)

        # Get distributor info
        distributor = self.distributors.get_distributor(rfq.distributor_id)

        return {
            'success': True,
            'rfq_id': rfq_id,
            'status': rfq.status.value,
            'equipment_type': rfq.equipment_type,
            'distributor': distributor.name if distributor else rfq.distributor_id,
            'distributor_email': distributor.email_address if distributor else None,
            'quotes_received': len(quotes),
            'quotes': [q.to_dict() for q in quotes],
            'sent_at': rfq.sent_at.isoformat() if rfq.sent_at else None,
            'expires_at': rfq.expires_at.isoformat() if rfq.expires_at else None,
            'created_at': rfq.created_at.isoformat()
        }

    def get_quotes(self, rfq_id: str) -> Dict[str, Any]:
        """
        Get all quotes received for an RFQ.

        Args:
            rfq_id: The RFQ ID

        Returns:
            {
                'success': bool,
                'rfq_id': str,
                'quotes': List[Dict],
                'total_quotes': int
            }
        """
        rfq = self.quote_tracker.get_rfq(rfq_id)

        if not rfq:
            return {
                'success': False,
                'error': f"RFQ {rfq_id} not found"
            }

        quotes = self.quote_tracker.get_quotes_for_rfq(rfq_id)

        return {
            'success': True,
            'rfq_id': rfq_id,
            'status': rfq.status.value,
            'quotes': [q.to_dict() for q in quotes],
            'total_quotes': len(quotes)
        }

    def compare_quotes(
        self,
        rfq_ids: List[str],
        sort_by: str = 'total_value'
    ) -> Dict[str, Any]:
        """
        Compare quotes from multiple RFQs/distributors.

        Identifies:
        - Best price (lowest unit price)
        - Fastest delivery (shortest lead time)
        - Recommended (best overall value)

        Args:
            rfq_ids: List of RFQ IDs to compare
            sort_by: How to sort ('price', 'lead_time', 'total_value')

        Returns:
            QuoteComparison as dict
        """
        if not rfq_ids:
            return {
                'success': False,
                'error': "No RFQ IDs provided"
            }

        # Get all quotes
        quotes = self.quote_tracker.get_quotes_for_rfqs(rfq_ids)

        if not quotes:
            # Check if RFQs exist
            existing_rfqs = [self.quote_tracker.get_rfq(rid) for rid in rfq_ids]
            existing_rfqs = [r for r in existing_rfqs if r is not None]

            if not existing_rfqs:
                return {
                    'success': False,
                    'error': "No RFQs found with those IDs"
                }

            return {
                'success': True,
                'rfq_ids': rfq_ids,
                'quotes': [],
                'total_quotes': 0,
                'message': "No quotes received yet. Check back later."
            }

        # Find best price
        best_price = min(quotes, key=lambda q: q.unit_price)

        # Find fastest delivery
        fastest = min(quotes, key=lambda q: q.lead_time_days)

        # Calculate recommended (weighted score)
        recommended = self._calculate_recommended(quotes)

        # Sort quotes
        if sort_by == 'price':
            quotes.sort(key=lambda q: q.unit_price)
        elif sort_by == 'lead_time':
            quotes.sort(key=lambda q: q.lead_time_days)
        else:  # total_value
            quotes.sort(key=lambda q: (q.unit_price, q.lead_time_days))

        # Build comparison table
        comparison_table = []
        for q in quotes:
            comparison_table.append({
                'distributor': q.distributor_name,
                'brand': q.brand,
                'model': q.equipment_model,
                'unit_price': str(q.unit_price),
                'quantity': q.quantity_available,
                'lead_time_days': q.lead_time_days,
                'shipping': str(q.shipping_cost),
                'total': str(q.total_price),
                'valid_until': q.valid_until.isoformat() if q.valid_until else None,
                'is_best_price': q.id == best_price.id,
                'is_fastest': q.id == fastest.id,
                'is_recommended': q.id == recommended.id
            })

        comparison = QuoteComparison(
            rfq_ids=rfq_ids,
            quotes=quotes,
            best_price=best_price,
            fastest_delivery=fastest,
            recommended=recommended,
            comparison_notes=self._generate_comparison_notes(quotes, best_price, fastest, recommended)
        )

        result = comparison.to_dict()
        result['success'] = True
        result['comparison_table'] = comparison_table

        return result

    def _calculate_recommended(self, quotes: List[Quote]) -> Quote:
        """
        Calculate recommended quote based on weighted scoring.

        Scoring factors:
        - Price: 50% weight
        - Lead time: 30% weight
        - Quantity available: 20% weight
        """
        if len(quotes) == 1:
            return quotes[0]

        # Normalize scores
        min_price = min(q.unit_price for q in quotes)
        max_price = max(q.unit_price for q in quotes)
        min_lead = min(q.lead_time_days for q in quotes)
        max_lead = max(q.lead_time_days for q in quotes)
        max_qty = max(q.quantity_available for q in quotes)

        price_range = float(max_price - min_price) or 1
        lead_range = max_lead - min_lead or 1

        def score_quote(q: Quote) -> float:
            # Lower price = higher score (inverted)
            price_score = 1 - (float(q.unit_price - min_price) / price_range)

            # Lower lead time = higher score (inverted)
            lead_score = 1 - ((q.lead_time_days - min_lead) / lead_range)

            # Higher quantity = higher score
            qty_score = q.quantity_available / max_qty if max_qty > 0 else 1

            # Weighted total
            return (price_score * 0.5) + (lead_score * 0.3) + (qty_score * 0.2)

        return max(quotes, key=score_quote)

    def _generate_comparison_notes(
        self,
        quotes: List[Quote],
        best_price: Quote,
        fastest: Quote,
        recommended: Quote
    ) -> str:
        """Generate human-readable comparison notes"""
        notes = []

        notes.append(f"Compared {len(quotes)} quote(s) from distributors.")

        if best_price == fastest == recommended:
            notes.append(
                f"{best_price.distributor_name} offers the best overall value "
                f"with lowest price (${best_price.unit_price}) and fastest delivery "
                f"({best_price.lead_time_days} days)."
            )
        else:
            notes.append(
                f"Best Price: {best_price.distributor_name} at ${best_price.unit_price}/unit"
            )
            notes.append(
                f"Fastest Delivery: {fastest.distributor_name} ({fastest.lead_time_days} days)"
            )
            notes.append(
                f"Recommended: {recommended.distributor_name} (best overall value)"
            )

        return " ".join(notes)

    def get_contractor_rfqs(self, contractor_id: str) -> Dict[str, Any]:
        """
        Get all RFQs for a contractor.

        Args:
            contractor_id: The contractor ID

        Returns:
            List of RFQs with their statuses
        """
        rfqs = self.quote_tracker.get_rfqs_by_contractor(contractor_id)

        return {
            'success': True,
            'contractor_id': contractor_id,
            'total_rfqs': len(rfqs),
            'rfqs': [
                {
                    'rfq_id': rfq.id,
                    'equipment_type': rfq.equipment_type,
                    'status': rfq.status.value,
                    'created_at': rfq.created_at.isoformat(),
                    'distributor_id': rfq.distributor_id
                }
                for rfq in rfqs
            ]
        }

    def simulate_quote_response(
        self,
        rfq_id: str,
        unit_price: float,
        lead_time_days: int = 5,
        quantity_available: int = 10,
        shipping_cost: float = 150.0,
        equipment_model: str = "Standard Model",
        brand: str = "Carrier"
    ) -> Dict[str, Any]:
        """
        Simulate a quote response (for testing).

        In production, quotes come via email. This method allows
        testing the quote comparison flow without actual emails.

        Args:
            rfq_id: The RFQ to respond to
            unit_price: Unit price for the equipment
            lead_time_days: Days until delivery
            quantity_available: Units in stock
            shipping_cost: Shipping cost
            equipment_model: Model number
            brand: Equipment brand

        Returns:
            Created quote details
        """
        rfq = self.quote_tracker.get_rfq(rfq_id)

        if not rfq:
            return {
                'success': False,
                'error': f"RFQ {rfq_id} not found"
            }

        distributor = self.distributors.get_distributor(rfq.distributor_id)

        quote = Quote(
            id=str(uuid.uuid4())[:8],
            rfq_id=rfq_id,
            distributor_id=rfq.distributor_id,
            distributor_name=distributor.name if distributor else rfq.distributor_id,
            equipment_model=equipment_model,
            brand=brand,
            unit_price=Decimal(str(unit_price)),
            quantity_available=quantity_available,
            lead_time_days=lead_time_days,
            shipping_cost=Decimal(str(shipping_cost)),
            notes="Simulated quote for testing"
        )

        self.quote_tracker.add_quote(quote)

        return {
            'success': True,
            'quote_id': quote.id,
            'rfq_id': rfq_id,
            'quote': quote.to_dict(),
            'message': f"Quote simulated from {quote.distributor_name}"
        }


# Singleton instance
_manager_instance: Optional[RFQManager] = None


def get_rfq_manager() -> RFQManager:
    """Get the singleton RFQManager instance"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = RFQManager()
    return _manager_instance
