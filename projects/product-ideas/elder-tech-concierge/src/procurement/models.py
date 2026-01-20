"""
Elder Tech Procurement - Data Models

Defines the core data structures for iPad/device procurement:
- Wholesaler: Device wholesaler information
- PriceInquiry: Request for bulk pricing sent to wholesalers
- PriceQuote: Quote response from a wholesaler
- InquiryStatus: Lifecycle states for inquiries

Based on the HVAC Distributor pattern:
- EMAIL connectivity (contact forms or direct email)
- ASYNC response times (24-48 hours typical)
- Comparison across multiple suppliers
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Any, Optional
import json


class InquiryStatus(Enum):
    """Price inquiry lifecycle states"""
    PENDING = "pending"       # Created but not yet sent
    SENT = "sent"            # Email/form submitted to wholesaler
    QUOTED = "quoted"        # Quote received
    EXPIRED = "expired"      # No response within timeout
    CANCELLED = "cancelled"  # User cancelled the inquiry


class DeviceType(Enum):
    """Device categories for procurement"""
    IPAD = "ipad"
    IPAD_PRO = "ipad_pro"
    IPAD_AIR = "ipad_air"
    IPAD_MINI = "ipad_mini"
    ANDROID_TABLET = "android_tablet"
    CASE = "case"
    STYLUS = "stylus"
    CHARGER = "charger"
    OTHER = "other"


class DeviceCondition(Enum):
    """Device condition for refurbished options"""
    NEW = "new"
    REFURBISHED_A = "refurbished_a"  # Like new
    REFURBISHED_B = "refurbished_b"  # Good condition
    REFURBISHED_C = "refurbished_c"  # Acceptable


@dataclass
class Wholesaler:
    """
    Device wholesaler for iPad/tablet procurement.

    Wholesalers are contacted via email or contact forms
    for bulk pricing inquiries.
    """
    id: str
    name: str
    email_address: Optional[str]
    contact_form_url: Optional[str]
    website: str
    supported_devices: List[str]         # ['ipad', 'ipad_pro', 'android_tablet']
    conditions_available: List[str]      # ['new', 'refurbished_a']
    min_order_quantity: int = 1
    avg_response_hours: int = 24
    rating: float = 0.0
    is_active: bool = True
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'email_address': self.email_address,
            'contact_form_url': self.contact_form_url,
            'website': self.website,
            'supported_devices': self.supported_devices,
            'conditions_available': self.conditions_available,
            'min_order_quantity': self.min_order_quantity,
            'avg_response_hours': self.avg_response_hours,
            'rating': self.rating,
            'is_active': self.is_active,
            'contact_name': self.contact_name,
            'phone': self.phone,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Wholesaler':
        return cls(
            id=data['id'],
            name=data['name'],
            email_address=data.get('email_address'),
            contact_form_url=data.get('contact_form_url'),
            website=data.get('website', ''),
            supported_devices=data.get('supported_devices', []),
            conditions_available=data.get('conditions_available', ['new']),
            min_order_quantity=data.get('min_order_quantity', 1),
            avg_response_hours=data.get('avg_response_hours', 24),
            rating=data.get('rating', 0.0),
            is_active=data.get('is_active', True),
            contact_name=data.get('contact_name'),
            phone=data.get('phone'),
            notes=data.get('notes')
        )


@dataclass
class DeviceSpecifications:
    """Device specifications for a price inquiry"""
    model: Optional[str] = None              # e.g., 'iPad 11th Generation'
    storage_gb: Optional[int] = None         # e.g., 64, 256
    color: Optional[str] = None              # e.g., 'Space Gray'
    connectivity: Optional[str] = None       # 'wifi' or 'wifi_cellular'
    condition: str = 'new'                   # 'new', 'refurbished_a', etc.
    accessories_needed: List[str] = field(default_factory=list)  # ['case', 'charger']
    additional_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in {
            'model': self.model,
            'storage_gb': self.storage_gb,
            'color': self.color,
            'connectivity': self.connectivity,
            'condition': self.condition,
            'accessories_needed': self.accessories_needed,
            'additional_notes': self.additional_notes
        }.items() if v is not None and v != []}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceSpecifications':
        return cls(
            model=data.get('model'),
            storage_gb=data.get('storage_gb'),
            color=data.get('color'),
            connectivity=data.get('connectivity'),
            condition=data.get('condition', 'new'),
            accessories_needed=data.get('accessories_needed', []),
            additional_notes=data.get('additional_notes')
        )


@dataclass
class PriceInquiry:
    """
    Price inquiry sent to device wholesalers.

    Similar to HVAC RFQ pattern:
    - Sent via email or contact form
    - Response expected in 24-48 hours
    - Compare across multiple wholesalers
    """
    id: str
    requester_id: str                        # Who is requesting the quote
    wholesaler_id: str                       # Target wholesaler
    device_type: str                         # ipad, ipad_pro, etc.
    specifications: DeviceSpecifications
    quantity: int = 1
    ship_to_address: Optional[str] = None
    needed_by_date: Optional[date] = None
    status: InquiryStatus = InquiryStatus.PENDING
    email_message_id: Optional[str] = None
    contact_form_submitted: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'requester_id': self.requester_id,
            'wholesaler_id': self.wholesaler_id,
            'device_type': self.device_type,
            'specifications': self.specifications.to_dict(),
            'quantity': self.quantity,
            'ship_to_address': self.ship_to_address,
            'needed_by_date': self.needed_by_date.isoformat() if self.needed_by_date else None,
            'status': self.status.value,
            'email_message_id': self.email_message_id,
            'contact_form_submitted': self.contact_form_submitted,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceInquiry':
        specs = data.get('specifications', {})
        if isinstance(specs, str):
            specs = json.loads(specs)

        return cls(
            id=data['id'],
            requester_id=data['requester_id'],
            wholesaler_id=data['wholesaler_id'],
            device_type=data['device_type'],
            specifications=DeviceSpecifications.from_dict(specs),
            quantity=data.get('quantity', 1),
            ship_to_address=data.get('ship_to_address'),
            needed_by_date=date.fromisoformat(data['needed_by_date']) if data.get('needed_by_date') else None,
            status=InquiryStatus(data.get('status', 'pending')),
            email_message_id=data.get('email_message_id'),
            contact_form_submitted=data.get('contact_form_submitted', False),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            sent_at=datetime.fromisoformat(data['sent_at']) if data.get('sent_at') else None,
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        )


@dataclass
class PriceQuote:
    """
    Quote response from a device wholesaler.

    Received via email, parsed, and stored for comparison.
    """
    id: str
    inquiry_id: str
    wholesaler_id: str
    wholesaler_name: str
    device_model: str
    brand: str
    unit_price: Decimal
    quantity_available: int
    condition: str
    lead_time_days: int
    shipping_cost: Decimal = Decimal('0.00')
    total_price: Decimal = Decimal('0.00')
    warranty_months: int = 0
    valid_until: Optional[date] = None
    received_at: datetime = field(default_factory=datetime.now)
    raw_email_content: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        # Calculate total if not provided
        if self.total_price == Decimal('0.00'):
            self.total_price = (self.unit_price * self.quantity_available) + self.shipping_cost

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'inquiry_id': self.inquiry_id,
            'wholesaler_id': self.wholesaler_id,
            'wholesaler_name': self.wholesaler_name,
            'device_model': self.device_model,
            'brand': self.brand,
            'unit_price': str(self.unit_price),
            'quantity_available': self.quantity_available,
            'condition': self.condition,
            'lead_time_days': self.lead_time_days,
            'shipping_cost': str(self.shipping_cost),
            'total_price': str(self.total_price),
            'warranty_months': self.warranty_months,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'received_at': self.received_at.isoformat(),
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceQuote':
        return cls(
            id=data['id'],
            inquiry_id=data['inquiry_id'],
            wholesaler_id=data['wholesaler_id'],
            wholesaler_name=data.get('wholesaler_name', ''),
            device_model=data.get('device_model', ''),
            brand=data.get('brand', ''),
            unit_price=Decimal(str(data['unit_price'])),
            quantity_available=data.get('quantity_available', 1),
            condition=data.get('condition', 'new'),
            lead_time_days=data.get('lead_time_days', 0),
            shipping_cost=Decimal(str(data.get('shipping_cost', '0'))),
            total_price=Decimal(str(data.get('total_price', '0'))),
            warranty_months=data.get('warranty_months', 0),
            valid_until=date.fromisoformat(data['valid_until']) if data.get('valid_until') else None,
            received_at=datetime.fromisoformat(data['received_at']) if data.get('received_at') else datetime.now(),
            raw_email_content=data.get('raw_email_content'),
            notes=data.get('notes')
        )


@dataclass
class QuoteComparison:
    """
    Comparison results across multiple quotes.

    Helps choose the best option based on:
    - Price (lowest unit price, lowest total)
    - Lead time (fastest delivery)
    - Warranty (longest coverage)
    - Overall value (price/quality balance)
    """
    inquiry_ids: List[str]
    quotes: List[PriceQuote]
    best_price: Optional[PriceQuote] = None
    fastest_delivery: Optional[PriceQuote] = None
    best_warranty: Optional[PriceQuote] = None
    recommended: Optional[PriceQuote] = None
    comparison_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'inquiry_ids': self.inquiry_ids,
            'quotes': [q.to_dict() for q in self.quotes],
            'best_price': self.best_price.to_dict() if self.best_price else None,
            'fastest_delivery': self.fastest_delivery.to_dict() if self.fastest_delivery else None,
            'best_warranty': self.best_warranty.to_dict() if self.best_warranty else None,
            'recommended': self.recommended.to_dict() if self.recommended else None,
            'comparison_notes': self.comparison_notes,
            'total_quotes': len(self.quotes)
        }


# Type aliases for clarity
RequesterID = str
WholesalerID = str
InquiryID = str
QuoteID = str
