"""
HVAC Distributor MCP - Data Models

Defines the core data structures for HVAC RFQ (Request for Quote) management:
- Distributor: HVAC equipment distributor information
- RFQ: Request for Quote sent to distributors
- Quote: Quote response from a distributor
- RFQStatus: Lifecycle states for RFQs

This MCP validates the platform's support for:
- EMAIL connectivity type (not HTTP REST)
- ASYNC scoring profile (24-48 hour latency)
- Per-RFQ billing (using PER_REQUEST model)
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Any, Optional
import json


class RFQStatus(Enum):
    """RFQ lifecycle states"""
    PENDING = "pending"       # Created but not yet sent
    SENT = "sent"            # Email sent to distributor
    QUOTED = "quoted"        # At least one quote received
    EXPIRED = "expired"      # No response within timeout
    CANCELLED = "cancelled"  # User cancelled the RFQ


class EquipmentType(Enum):
    """HVAC equipment categories"""
    AC_UNIT = "ac_unit"
    FURNACE = "furnace"
    HEAT_PUMP = "heat_pump"
    AIR_HANDLER = "air_handler"
    CONDENSER = "condenser"
    EVAPORATOR_COIL = "evaporator_coil"
    MINI_SPLIT = "mini_split"
    THERMOSTAT = "thermostat"
    DUCTWORK = "ductwork"
    OTHER = "other"


@dataclass
class Distributor:
    """
    HVAC equipment distributor.

    Distributors receive RFQs via email and respond with quotes.
    Unlike rideshare services, there's no REST API - all communication
    is via email (validating EMAIL connectivity type).
    """
    id: str
    name: str
    email_address: str
    supported_regions: List[str]       # e.g., ['FL', 'GA', 'AL']
    supported_brands: List[str]        # e.g., ['Carrier', 'Trane', 'Lennox']
    equipment_types: List[str]         # e.g., ['ac_unit', 'furnace']
    avg_response_hours: int = 24       # Typical response time (validates ASYNC)
    rating: float = 0.0
    is_active: bool = True
    contact_name: Optional[str] = None
    phone: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'email_address': self.email_address,
            'supported_regions': self.supported_regions,
            'supported_brands': self.supported_brands,
            'equipment_types': self.equipment_types,
            'avg_response_hours': self.avg_response_hours,
            'rating': self.rating,
            'is_active': self.is_active,
            'contact_name': self.contact_name,
            'phone': self.phone
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Distributor':
        return cls(
            id=data['id'],
            name=data['name'],
            email_address=data['email_address'],
            supported_regions=data.get('supported_regions', []),
            supported_brands=data.get('supported_brands', []),
            equipment_types=data.get('equipment_types', []),
            avg_response_hours=data.get('avg_response_hours', 24),
            rating=data.get('rating', 0.0),
            is_active=data.get('is_active', True),
            contact_name=data.get('contact_name'),
            phone=data.get('phone')
        )


@dataclass
class RFQSpecifications:
    """Equipment specifications for an RFQ"""
    tonnage: Optional[float] = None          # AC/heat pump size
    seer: Optional[int] = None               # Efficiency rating
    btu: Optional[int] = None                # Heating capacity
    voltage: Optional[str] = None            # e.g., '208-230V'
    phase: Optional[str] = None              # e.g., 'single', 'three'
    refrigerant: Optional[str] = None        # e.g., 'R-410A'
    model_preference: Optional[str] = None   # Specific model if known
    additional_notes: Optional[str] = None   # Free-form notes

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in {
            'tonnage': self.tonnage,
            'seer': self.seer,
            'btu': self.btu,
            'voltage': self.voltage,
            'phase': self.phase,
            'refrigerant': self.refrigerant,
            'model_preference': self.model_preference,
            'additional_notes': self.additional_notes
        }.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RFQSpecifications':
        return cls(
            tonnage=data.get('tonnage'),
            seer=data.get('seer'),
            btu=data.get('btu'),
            voltage=data.get('voltage'),
            phase=data.get('phase'),
            refrigerant=data.get('refrigerant'),
            model_preference=data.get('model_preference'),
            additional_notes=data.get('additional_notes')
        )


@dataclass
class RFQ:
    """
    Request for Quote sent to HVAC distributors.

    Key differences from rideshare requests:
    - Sent via email (not HTTP)
    - Response expected in 24-48 hours (not milliseconds)
    - Billed per-RFQ (not per-request)
    """
    id: str
    contractor_id: str                       # Who is requesting the quote
    distributor_id: str                      # Target distributor
    equipment_type: str                      # ac_unit, furnace, etc.
    specifications: RFQSpecifications
    delivery_address: str
    quantity: int = 1
    brand_preference: Optional[str] = None
    needed_by_date: Optional[date] = None
    status: RFQStatus = RFQStatus.PENDING
    email_message_id: Optional[str] = None   # For tracking email replies
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'contractor_id': self.contractor_id,
            'distributor_id': self.distributor_id,
            'equipment_type': self.equipment_type,
            'specifications': self.specifications.to_dict(),
            'delivery_address': self.delivery_address,
            'quantity': self.quantity,
            'brand_preference': self.brand_preference,
            'needed_by_date': self.needed_by_date.isoformat() if self.needed_by_date else None,
            'status': self.status.value,
            'email_message_id': self.email_message_id,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RFQ':
        specs = data.get('specifications', {})
        if isinstance(specs, str):
            specs = json.loads(specs)

        return cls(
            id=data['id'],
            contractor_id=data['contractor_id'],
            distributor_id=data['distributor_id'],
            equipment_type=data['equipment_type'],
            specifications=RFQSpecifications.from_dict(specs),
            delivery_address=data['delivery_address'],
            quantity=data.get('quantity', 1),
            brand_preference=data.get('brand_preference'),
            needed_by_date=date.fromisoformat(data['needed_by_date']) if data.get('needed_by_date') else None,
            status=RFQStatus(data.get('status', 'pending')),
            email_message_id=data.get('email_message_id'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            sent_at=datetime.fromisoformat(data['sent_at']) if data.get('sent_at') else None,
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        )


@dataclass
class Quote:
    """
    Quote response from an HVAC distributor.

    Received via email, parsed, and stored for comparison.
    Multiple quotes can be received for a single RFQ if sent to multiple distributors.
    """
    id: str
    rfq_id: str
    distributor_id: str
    distributor_name: str
    equipment_model: str
    brand: str
    unit_price: Decimal
    quantity_available: int
    lead_time_days: int
    shipping_cost: Decimal = Decimal('0.00')
    total_price: Decimal = Decimal('0.00')
    valid_until: Optional[date] = None
    received_at: datetime = field(default_factory=datetime.now)
    raw_email_content: Optional[str] = None  # Original email for reference
    notes: Optional[str] = None

    def __post_init__(self):
        # Calculate total if not provided
        if self.total_price == Decimal('0.00'):
            self.total_price = (self.unit_price * self.quantity_available) + self.shipping_cost

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'rfq_id': self.rfq_id,
            'distributor_id': self.distributor_id,
            'distributor_name': self.distributor_name,
            'equipment_model': self.equipment_model,
            'brand': self.brand,
            'unit_price': str(self.unit_price),
            'quantity_available': self.quantity_available,
            'lead_time_days': self.lead_time_days,
            'shipping_cost': str(self.shipping_cost),
            'total_price': str(self.total_price),
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'received_at': self.received_at.isoformat(),
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Quote':
        return cls(
            id=data['id'],
            rfq_id=data['rfq_id'],
            distributor_id=data['distributor_id'],
            distributor_name=data.get('distributor_name', ''),
            equipment_model=data.get('equipment_model', ''),
            brand=data.get('brand', ''),
            unit_price=Decimal(str(data['unit_price'])),
            quantity_available=data.get('quantity_available', 1),
            lead_time_days=data.get('lead_time_days', 0),
            shipping_cost=Decimal(str(data.get('shipping_cost', '0'))),
            total_price=Decimal(str(data.get('total_price', '0'))),
            valid_until=date.fromisoformat(data['valid_until']) if data.get('valid_until') else None,
            received_at=datetime.fromisoformat(data['received_at']) if data.get('received_at') else datetime.now(),
            raw_email_content=data.get('raw_email_content'),
            notes=data.get('notes')
        )


@dataclass
class QuoteComparison:
    """
    Comparison results across multiple quotes.

    Helps contractors choose the best option based on:
    - Price (lowest unit price, lowest total)
    - Lead time (fastest delivery)
    - Overall value (price/lead time balance)
    """
    rfq_ids: List[str]
    quotes: List[Quote]
    best_price: Optional[Quote] = None
    fastest_delivery: Optional[Quote] = None
    recommended: Optional[Quote] = None
    comparison_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'rfq_ids': self.rfq_ids,
            'quotes': [q.to_dict() for q in self.quotes],
            'best_price': self.best_price.to_dict() if self.best_price else None,
            'fastest_delivery': self.fastest_delivery.to_dict() if self.fastest_delivery else None,
            'recommended': self.recommended.to_dict() if self.recommended else None,
            'comparison_notes': self.comparison_notes,
            'total_quotes': len(self.quotes)
        }


# Type aliases for clarity
ContractorID = str
DistributorID = str
RFQID = str
QuoteID = str
