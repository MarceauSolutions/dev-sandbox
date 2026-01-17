"""
Elder Tech Procurement - iPad/Device Wholesale Sourcing

This module provides tools for sourcing devices from wholesalers,
based on the HVAC Distributor RFQ pattern.

Key components:
- models.py: Data structures (Wholesaler, PriceInquiry, PriceQuote)
- wholesaler_db.py: Database of device wholesalers
- email_sender.py: SMTP email sender for inquiries
- inquiry_manager.py: Core business logic

Target Wholesalers:
- Today's Closeout (todayscloseout.com)
- WeSellCellular (wesellcellular.com)
- Mac of All Trades
- Gazelle Business
- Back Market Pro
- Reebelo Business
- Apple Certified Refurbished

Usage:
    from procurement import get_inquiry_manager

    manager = get_inquiry_manager()

    # Submit inquiry to multiple wholesalers
    result = manager.submit_inquiry(
        device_type='ipad',
        quantity=5,
        model='iPad 11th Generation',
        storage_gb=64,
        condition='new'
    )

    # Compare quotes when received
    comparison = manager.compare_quotes(result['inquiry_ids'])
"""

from .models import (
    Wholesaler,
    PriceInquiry,
    PriceQuote,
    DeviceSpecifications,
    QuoteComparison,
    InquiryStatus,
    DeviceType,
    DeviceCondition
)

from .wholesaler_db import (
    WholesalerDB,
    get_wholesaler_db
)

from .email_sender import (
    EmailSender,
    get_email_sender,
    EmailSendError,
    NoEmailError
)

from .inquiry_manager import (
    InquiryManager,
    get_inquiry_manager
)

__all__ = [
    # Models
    'Wholesaler',
    'PriceInquiry',
    'PriceQuote',
    'DeviceSpecifications',
    'QuoteComparison',
    'InquiryStatus',
    'DeviceType',
    'DeviceCondition',

    # Wholesaler DB
    'WholesalerDB',
    'get_wholesaler_db',

    # Email
    'EmailSender',
    'get_email_sender',
    'EmailSendError',
    'NoEmailError',

    # Manager
    'InquiryManager',
    'get_inquiry_manager',
]

__version__ = '1.0.0'
