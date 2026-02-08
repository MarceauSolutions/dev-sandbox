"""
HVAC Distributor MCP

Provides RFQ (Request for Quote) management for HVAC equipment distributors.

This MCP validates the MCP Aggregator platform's support for:
- EMAIL connectivity type (not HTTP REST)
- ASYNC scoring profile (24-48 hour response times)
- Per-RFQ billing (using PER_REQUEST model)
- UTILITIES category

Key differences from rideshare MCP:
- Communication via email, not HTTP
- Response times in hours/days, not milliseconds
- Billed per-RFQ, not per-API-call

Usage:
    from src.mcps.hvac import RFQManager, get_rfq_manager

    # Get manager instance
    manager = get_rfq_manager()

    # Submit RFQ
    result = manager.submit_rfq(
        contractor_id='contractor-123',
        equipment_type='ac_unit',
        delivery_address='123 Main St, Naples, FL',
        specifications={'tonnage': 3, 'seer': 16},
        brand_preference='Carrier'
    )

    # Check status
    status = manager.check_rfq_status(result['rfq_ids'][0])

    # Get quotes
    quotes = manager.get_quotes(result['rfq_ids'][0])

    # Compare quotes
    comparison = manager.compare_quotes(result['rfq_ids'])
"""

# Data models
from .models import (
    RFQ,
    Quote,
    RFQStatus,
    RFQSpecifications,
    Distributor,
    QuoteComparison,
    EquipmentType
)

# Core manager
from .rfq_manager import RFQManager, get_rfq_manager

# Distributor database
from .distributor_db import DistributorDB, get_distributor_db

# Email handling
from .email_sender import EmailSender, get_email_sender, EmailSendError
from .email_receiver import EmailReceiver, get_email_receiver

# Quote tracking
from .quote_tracker import QuoteTracker, get_quote_tracker

__all__ = [
    # Models
    'RFQ',
    'Quote',
    'RFQStatus',
    'RFQSpecifications',
    'Distributor',
    'QuoteComparison',
    'EquipmentType',

    # Manager
    'RFQManager',
    'get_rfq_manager',

    # Distributors
    'DistributorDB',
    'get_distributor_db',

    # Email
    'EmailSender',
    'get_email_sender',
    'EmailSendError',
    'EmailReceiver',
    'get_email_receiver',

    # Tracking
    'QuoteTracker',
    'get_quote_tracker',
]

__version__ = '1.0.0-dev'
