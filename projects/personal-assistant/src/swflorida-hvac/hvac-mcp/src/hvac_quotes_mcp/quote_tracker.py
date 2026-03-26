"""
HVAC Quote Tracker

Database operations for tracking RFQs and quotes.
Uses SQLite for persistence, compatible with the platform core database.

This handles the async nature of email-based workflows:
- RFQ submitted -> status: PENDING
- Email sent -> status: SENT
- Quote received -> status: QUOTED
- No response -> status: EXPIRED
"""

import os
import json
import sqlite3
import logging
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from .models import RFQ, Quote, RFQStatus, RFQSpecifications

logger = logging.getLogger(__name__)


# Schema for HVAC tables
HVAC_SCHEMA = """
-- RFQs table
CREATE TABLE IF NOT EXISTS hvac_rfqs (
    id TEXT PRIMARY KEY,
    contractor_id TEXT NOT NULL,
    distributor_id TEXT NOT NULL,
    equipment_type TEXT NOT NULL,
    specifications TEXT,
    delivery_address TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    brand_preference TEXT,
    needed_by_date DATE,
    status TEXT DEFAULT 'pending',
    email_message_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- Quotes table
CREATE TABLE IF NOT EXISTS hvac_quotes (
    id TEXT PRIMARY KEY,
    rfq_id TEXT NOT NULL,
    distributor_id TEXT NOT NULL,
    distributor_name TEXT,
    equipment_model TEXT,
    brand TEXT,
    unit_price REAL NOT NULL,
    quantity_available INTEGER DEFAULT 1,
    lead_time_days INTEGER,
    shipping_cost REAL DEFAULT 0,
    total_price REAL NOT NULL,
    valid_until DATE,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_email_content TEXT,
    notes TEXT,
    FOREIGN KEY (rfq_id) REFERENCES hvac_rfqs(id)
);

-- Index for faster RFQ lookups
CREATE INDEX IF NOT EXISTS idx_hvac_rfqs_contractor ON hvac_rfqs(contractor_id);
CREATE INDEX IF NOT EXISTS idx_hvac_rfqs_status ON hvac_rfqs(status);
CREATE INDEX IF NOT EXISTS idx_hvac_rfqs_message_id ON hvac_rfqs(email_message_id);
CREATE INDEX IF NOT EXISTS idx_hvac_quotes_rfq ON hvac_quotes(rfq_id);
"""


class QuoteTracker:
    """
    Track RFQs and quotes in SQLite database.

    Handles the async workflow:
    1. create_rfq() - Store new RFQ (status: PENDING)
    2. mark_rfq_sent() - Update after email sent (status: SENT)
    3. add_quote() - Store received quote (status: QUOTED)
    4. expire_old_rfqs() - Mark stale RFQs as expired
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize QuoteTracker.

        Args:
            db_path: Path to SQLite database. Defaults to a temp directory
        """
        if db_path:
            self.db_path = db_path
        else:
            # Use environment variable or temp directory
            self.db_path = os.environ.get(
                'HVAC_DB_PATH',
                os.path.join(tempfile.gettempdir(), 'hvac_quotes.db')
            )
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(HVAC_SCHEMA)
            conn.commit()
        logger.info(f"HVAC database initialized at {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ==========================================
    # RFQ Operations
    # ==========================================

    def create_rfq(self, rfq: RFQ) -> str:
        """
        Store a new RFQ.

        Args:
            rfq: The RFQ to store

        Returns:
            RFQ ID
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO hvac_rfqs (
                    id, contractor_id, distributor_id, equipment_type,
                    specifications, delivery_address, quantity, brand_preference,
                    needed_by_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rfq.id,
                    rfq.contractor_id,
                    rfq.distributor_id,
                    rfq.equipment_type,
                    json.dumps(rfq.specifications.to_dict()),
                    rfq.delivery_address,
                    rfq.quantity,
                    rfq.brand_preference,
                    rfq.needed_by_date.isoformat() if rfq.needed_by_date else None,
                    rfq.status.value,
                    rfq.created_at.isoformat()
                )
            )
            conn.commit()

        logger.info(f"Created RFQ: {rfq.id} for distributor {rfq.distributor_id}")
        return rfq.id

    def get_rfq(self, rfq_id: str) -> Optional[RFQ]:
        """Get RFQ by ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM hvac_rfqs WHERE id = ?",
                (rfq_id,)
            ).fetchone()

            if row:
                return self._row_to_rfq(dict(row))
            return None

    def get_rfqs_by_contractor(self, contractor_id: str) -> List[RFQ]:
        """Get all RFQs for a contractor"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM hvac_rfqs WHERE contractor_id = ? ORDER BY created_at DESC",
                (contractor_id,)
            ).fetchall()

            return [self._row_to_rfq(dict(row)) for row in rows]

    def get_pending_rfqs(self) -> List[RFQ]:
        """Get all RFQs awaiting quotes (status: SENT)"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM hvac_rfqs WHERE status = ? ORDER BY sent_at ASC",
                (RFQStatus.SENT.value,)
            ).fetchall()

            return [self._row_to_rfq(dict(row)) for row in rows]

    def get_rfq_by_message_id(self, message_id: str) -> Optional[RFQ]:
        """Get RFQ by email message ID (for matching replies)"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM hvac_rfqs WHERE email_message_id = ?",
                (message_id,)
            ).fetchone()

            if row:
                return self._row_to_rfq(dict(row))
            return None

    def mark_rfq_sent(
        self,
        rfq_id: str,
        message_id: str,
        expiry_hours: int = 48
    ) -> bool:
        """
        Mark RFQ as sent.

        Args:
            rfq_id: RFQ to update
            message_id: Email message ID for tracking
            expiry_hours: Hours until RFQ expires (default: 48)

        Returns:
            True if updated, False if not found
        """
        sent_at = datetime.now()
        expires_at = sent_at + timedelta(hours=expiry_hours)

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE hvac_rfqs
                SET status = ?, email_message_id = ?, sent_at = ?, expires_at = ?
                WHERE id = ?
                """,
                (
                    RFQStatus.SENT.value,
                    message_id,
                    sent_at.isoformat(),
                    expires_at.isoformat(),
                    rfq_id
                )
            )
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"RFQ {rfq_id} marked as sent, expires at {expires_at}")
                return True
            return False

    def mark_rfq_quoted(self, rfq_id: str) -> bool:
        """Mark RFQ as having received at least one quote"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE hvac_rfqs SET status = ? WHERE id = ?",
                (RFQStatus.QUOTED.value, rfq_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def expire_old_rfqs(self) -> int:
        """
        Mark expired RFQs.

        Returns:
            Number of RFQs marked as expired
        """
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE hvac_rfqs
                SET status = ?
                WHERE status = ? AND expires_at < ?
                """,
                (RFQStatus.EXPIRED.value, RFQStatus.SENT.value, now)
            )
            conn.commit()

            count = cursor.rowcount
            if count > 0:
                logger.info(f"Expired {count} RFQs")
            return count

    def _row_to_rfq(self, row: Dict[str, Any]) -> RFQ:
        """Convert database row to RFQ object"""
        from datetime import date as date_type

        specs_data = row.get('specifications', '{}')
        if isinstance(specs_data, str):
            specs_data = json.loads(specs_data) if specs_data else {}

        needed_by = None
        if row.get('needed_by_date'):
            needed_by = date_type.fromisoformat(row['needed_by_date'])

        return RFQ(
            id=row['id'],
            contractor_id=row['contractor_id'],
            distributor_id=row['distributor_id'],
            equipment_type=row['equipment_type'],
            specifications=RFQSpecifications.from_dict(specs_data),
            delivery_address=row['delivery_address'],
            quantity=row.get('quantity', 1),
            brand_preference=row.get('brand_preference'),
            needed_by_date=needed_by,
            status=RFQStatus(row.get('status', 'pending')),
            email_message_id=row.get('email_message_id'),
            created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.now(),
            sent_at=datetime.fromisoformat(row['sent_at']) if row.get('sent_at') else None,
            expires_at=datetime.fromisoformat(row['expires_at']) if row.get('expires_at') else None
        )

    # ==========================================
    # Quote Operations
    # ==========================================

    def add_quote(self, quote: Quote) -> str:
        """
        Store a received quote.

        Also updates the RFQ status to QUOTED.

        Args:
            quote: The quote to store

        Returns:
            Quote ID
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO hvac_quotes (
                    id, rfq_id, distributor_id, distributor_name,
                    equipment_model, brand, unit_price, quantity_available,
                    lead_time_days, shipping_cost, total_price,
                    valid_until, received_at, raw_email_content, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    quote.id,
                    quote.rfq_id,
                    quote.distributor_id,
                    quote.distributor_name,
                    quote.equipment_model,
                    quote.brand,
                    float(quote.unit_price),
                    quote.quantity_available,
                    quote.lead_time_days,
                    float(quote.shipping_cost),
                    float(quote.total_price),
                    quote.valid_until.isoformat() if quote.valid_until else None,
                    quote.received_at.isoformat(),
                    quote.raw_email_content,
                    quote.notes
                )
            )
            conn.commit()

        # Update RFQ status
        self.mark_rfq_quoted(quote.rfq_id)

        logger.info(f"Added quote {quote.id} for RFQ {quote.rfq_id}")
        return quote.id

    def get_quote(self, quote_id: str) -> Optional[Quote]:
        """Get quote by ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM hvac_quotes WHERE id = ?",
                (quote_id,)
            ).fetchone()

            if row:
                return self._row_to_quote(dict(row))
            return None

    def get_quotes_for_rfq(self, rfq_id: str) -> List[Quote]:
        """Get all quotes for an RFQ"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM hvac_quotes WHERE rfq_id = ? ORDER BY total_price ASC",
                (rfq_id,)
            ).fetchall()

            return [self._row_to_quote(dict(row)) for row in rows]

    def get_quotes_for_rfqs(self, rfq_ids: List[str]) -> List[Quote]:
        """Get all quotes for multiple RFQs"""
        if not rfq_ids:
            return []

        placeholders = ','.join(['?' for _ in rfq_ids])

        with self._get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM hvac_quotes WHERE rfq_id IN ({placeholders}) ORDER BY total_price ASC",
                rfq_ids
            ).fetchall()

            return [self._row_to_quote(dict(row)) for row in rows]

    def _row_to_quote(self, row: Dict[str, Any]) -> Quote:
        """Convert database row to Quote object"""
        from datetime import date as date_type

        valid_until = None
        if row.get('valid_until'):
            valid_until = date_type.fromisoformat(row['valid_until'])

        return Quote(
            id=row['id'],
            rfq_id=row['rfq_id'],
            distributor_id=row['distributor_id'],
            distributor_name=row.get('distributor_name', ''),
            equipment_model=row.get('equipment_model', ''),
            brand=row.get('brand', ''),
            unit_price=Decimal(str(row['unit_price'])),
            quantity_available=row.get('quantity_available', 1),
            lead_time_days=row.get('lead_time_days', 0),
            shipping_cost=Decimal(str(row.get('shipping_cost', 0))),
            total_price=Decimal(str(row.get('total_price', 0))),
            valid_until=valid_until,
            received_at=datetime.fromisoformat(row['received_at']) if row.get('received_at') else datetime.now(),
            raw_email_content=row.get('raw_email_content'),
            notes=row.get('notes')
        )

    # ==========================================
    # Statistics
    # ==========================================

    def get_stats(self) -> Dict[str, Any]:
        """Get tracking statistics"""
        with self._get_connection() as conn:
            rfq_stats = conn.execute(
                """
                SELECT
                    status,
                    COUNT(*) as count
                FROM hvac_rfqs
                GROUP BY status
                """
            ).fetchall()

            quote_count = conn.execute(
                "SELECT COUNT(*) as count FROM hvac_quotes"
            ).fetchone()

            return {
                'rfq_counts': {row['status']: row['count'] for row in rfq_stats},
                'total_quotes': quote_count['count'] if quote_count else 0
            }


# Singleton instance
_tracker_instance: Optional[QuoteTracker] = None


def get_quote_tracker(db_path: Optional[str] = None) -> QuoteTracker:
    """Get the singleton QuoteTracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = QuoteTracker(db_path)
    return _tracker_instance
