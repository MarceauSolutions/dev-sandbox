"""
Billing System for MCP Aggregator Platform

Handles all financial transactions:
- Transaction logging for every API call
- Fee calculation (platform cut vs developer payout)
- Invoice generation for AI platforms
- Payout processing for developers

Revenue Model:
- AI Platforms pay per request (e.g., $0.02)
- Platform takes 20% ($0.004)
- Developer gets 80% ($0.016)
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from .database import Database, Row

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionStatus(Enum):
    """Transaction lifecycle status"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PricingModel(Enum):
    """
    Pricing models supported by the platform.

    Different MCPs can use different billing strategies:
    - PER_REQUEST: Traditional pay-per-call (default)
    - SUBSCRIPTION: Monthly fee, unlimited calls
    - COMMISSION: Percentage of transaction value (e.g., booking commissions)
    - TIERED: Volume-based pricing with discount tiers
    - HYBRID: Base subscription fee + per-request charges
    """
    PER_REQUEST = "per_request"       # Current model: $X per API call
    SUBSCRIPTION = "subscription"      # Monthly fee, unlimited calls
    COMMISSION = "commission"          # % of transaction value
    TIERED = "tiered"                  # Volume-based pricing
    HYBRID = "hybrid"                  # Base fee + per-request


class PayoutStatus(Enum):
    """Payout lifecycle status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class InvoiceStatus(Enum):
    """Invoice lifecycle status"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


@dataclass
class Transaction:
    """
    A single billable API transaction.

    Supports multiple pricing models:
    - PER_REQUEST: Standard per-call billing (gross_amount = fee_per_request)
    - SUBSCRIPTION: No per-call charge (tracked via subscription_id)
    - COMMISSION: Percentage of booking value (gross_amount = booking_value * commission_rate)
    - TIERED: Volume-based pricing (uses tier_name for lookup)
    - HYBRID: Combination of base + per-request
    """
    id: str
    ai_platform_id: str
    mcp_id: str
    developer_id: str
    request_id: str
    capability_name: str
    request_payload: Dict[str, Any]
    response_payload: Optional[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]
    response_time_ms: Optional[int]
    gross_amount: Decimal
    platform_fee: Decimal
    developer_payout: Decimal
    status: TransactionStatus
    error_message: Optional[str] = None

    # Pricing model fields
    pricing_model: PricingModel = PricingModel.PER_REQUEST
    subscription_id: Optional[str] = None  # For SUBSCRIPTION model
    booking_value: Optional[Decimal] = None  # For COMMISSION model (total transaction value)
    commission_rate: Optional[Decimal] = None  # For COMMISSION model (e.g., 0.10 for 10%)
    tier_name: Optional[str] = None  # For TIERED model (e.g., "starter", "growth", "enterprise")

    @classmethod
    def from_row(cls, row: Row) -> 'Transaction':
        """Create Transaction from database row"""
        import json

        request_payload = row.get('request_payload', '{}')
        if isinstance(request_payload, str):
            request_payload = json.loads(request_payload) if request_payload else {}

        response_payload = row.get('response_payload')
        if isinstance(response_payload, str) and response_payload:
            response_payload = json.loads(response_payload)

        # Parse pricing model (default to PER_REQUEST for backwards compatibility)
        pricing_model_str = row.get('pricing_model', 'per_request')
        pricing_model = PricingModel(pricing_model_str) if pricing_model_str else PricingModel.PER_REQUEST

        # Parse optional decimal fields
        booking_value = None
        if row.get('booking_value') is not None:
            booking_value = Decimal(str(row['booking_value']))

        commission_rate = None
        if row.get('commission_rate') is not None:
            commission_rate = Decimal(str(row['commission_rate']))

        return cls(
            id=row['id'],
            ai_platform_id=row['ai_platform_id'],
            mcp_id=row['mcp_id'],
            developer_id=row['developer_id'],
            request_id=row['request_id'],
            capability_name=row.get('capability_name', ''),
            request_payload=request_payload,
            response_payload=response_payload,
            started_at=row['started_at'],
            completed_at=row.get('completed_at'),
            response_time_ms=row.get('response_time_ms'),
            gross_amount=Decimal(str(row['gross_amount'])),
            platform_fee=Decimal(str(row['platform_fee'])),
            developer_payout=Decimal(str(row['developer_payout'])),
            status=TransactionStatus(row['status']),
            error_message=row.get('error_message'),
            # New pricing model fields
            pricing_model=pricing_model,
            subscription_id=row.get('subscription_id'),
            booking_value=booking_value,
            commission_rate=commission_rate,
            tier_name=row.get('tier_name')
        )


@dataclass
class Payout:
    """Developer payout record"""
    id: str
    developer_id: str
    amount: Decimal
    currency: str
    period_start: date
    period_end: date
    status: PayoutStatus
    stripe_transfer_id: Optional[str] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @classmethod
    def from_row(cls, row: Row) -> 'Payout':
        """Create Payout from database row"""
        return cls(
            id=row['id'],
            developer_id=row['developer_id'],
            amount=Decimal(str(row['amount'])),
            currency=row.get('currency', 'USD'),
            period_start=row['period_start'],
            period_end=row['period_end'],
            status=PayoutStatus(row['status']),
            stripe_transfer_id=row.get('stripe_transfer_id'),
            processed_at=row.get('processed_at'),
            error_message=row.get('error_message')
        )


@dataclass
class Invoice:
    """AI platform invoice"""
    id: str
    ai_platform_id: str
    period_start: date
    period_end: date
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    currency: str
    status: InvoiceStatus
    due_date: Optional[date] = None
    paid_at: Optional[datetime] = None
    stripe_invoice_id: Optional[str] = None

    @classmethod
    def from_row(cls, row: Row) -> 'Invoice':
        """Create Invoice from database row"""
        return cls(
            id=row['id'],
            ai_platform_id=row['ai_platform_id'],
            period_start=row['period_start'],
            period_end=row['period_end'],
            subtotal=Decimal(str(row['subtotal'])),
            tax=Decimal(str(row.get('tax', 0))),
            total=Decimal(str(row['total'])),
            currency=row.get('currency', 'USD'),
            status=InvoiceStatus(row['status']),
            due_date=row.get('due_date'),
            paid_at=row.get('paid_at'),
            stripe_invoice_id=row.get('stripe_invoice_id')
        )


@dataclass
class TierConfig:
    """Configuration for a pricing tier (volume-based discounts)"""
    name: str  # e.g., "starter", "growth", "enterprise"
    min_requests: int  # Minimum requests to qualify for this tier
    max_requests: Optional[int]  # Maximum requests (None = unlimited)
    fee_per_request: Decimal  # Price per request at this tier
    developer_share: Decimal  # Developer's share (0.0-1.0)


@dataclass
class FeeBreakdown:
    """Fee calculation breakdown"""
    gross_amount: Decimal
    platform_fee: Decimal
    developer_payout: Decimal
    platform_fee_percent: Decimal
    developer_share_percent: Decimal
    pricing_model: PricingModel = PricingModel.PER_REQUEST
    # Additional context for non-PER_REQUEST models
    booking_value: Optional[Decimal] = None  # Original booking value (for COMMISSION)
    commission_rate: Optional[Decimal] = None  # Commission rate applied (for COMMISSION)
    tier_name: Optional[str] = None  # Tier applied (for TIERED)
    subscription_id: Optional[str] = None  # Subscription reference (for SUBSCRIPTION)


class BillingSystem:
    """
    Billing system for MCP Aggregator Platform.

    Handles:
    - Transaction logging with multiple pricing models
    - Fee calculations (per-request, commission, subscription, tiered, hybrid)
    - Invoice generation
    - Payout processing

    Pricing Models:
    - PER_REQUEST: Traditional $X per API call (default)
    - SUBSCRIPTION: Monthly fee, unlimited calls (no per-call charge)
    - COMMISSION: Percentage of transaction value (e.g., 10% of booking)
    - TIERED: Volume-based pricing with discount tiers
    - HYBRID: Base subscription + per-request charges

    Usage:
        billing = BillingSystem(db)

        # Log a per-request transaction (default)
        transaction_id = billing.log_transaction(
            ai_platform_id='...',
            mcp_id='...',
            developer_id='...',
            request_id='req_123',
            capability_name='compare_prices',
            request_payload={...},
            gross_amount=Decimal('0.02')
        )

        # Log a commission-based transaction (e.g., booking service)
        transaction_id = billing.log_transaction_with_pricing(
            ai_platform_id='...',
            mcp_id='...',
            developer_id='...',
            request_id='req_456',
            capability_name='book_ride',
            request_payload={...},
            pricing_model=PricingModel.COMMISSION,
            booking_value=Decimal('45.00'),
            commission_rate=Decimal('0.10'),  # 10% commission
            developer_share=Decimal('0.70')  # Developer gets 70% of commission
        )

        # Complete transaction
        billing.complete_transaction(transaction_id, response={...}, response_time_ms=150)

        # Generate invoice
        invoice = billing.generate_invoice('ai_platform_id', period_start, period_end)

        # Process payout
        payout = billing.process_payout('developer_id', period_start, period_end)
    """

    # Default fee structure
    DEFAULT_PLATFORM_FEE_PERCENT = Decimal('0.20')  # 20%
    DEFAULT_DEVELOPER_SHARE_PERCENT = Decimal('0.80')  # 80%

    # Default tier configuration (can be overridden per-MCP)
    DEFAULT_TIERS: List[TierConfig] = [
        TierConfig(
            name="starter",
            min_requests=0,
            max_requests=1000,
            fee_per_request=Decimal('0.02'),
            developer_share=Decimal('0.80')
        ),
        TierConfig(
            name="growth",
            min_requests=1001,
            max_requests=10000,
            fee_per_request=Decimal('0.015'),
            developer_share=Decimal('0.82')
        ),
        TierConfig(
            name="scale",
            min_requests=10001,
            max_requests=100000,
            fee_per_request=Decimal('0.01'),
            developer_share=Decimal('0.85')
        ),
        TierConfig(
            name="enterprise",
            min_requests=100001,
            max_requests=None,  # Unlimited
            fee_per_request=Decimal('0.005'),
            developer_share=Decimal('0.88')
        ),
    ]

    def __init__(self, db: Database):
        self.db = db
        self._tier_cache: Dict[str, List[TierConfig]] = {}  # mcp_id -> tiers

    # ==========================================
    # FEE CALCULATION
    # ==========================================

    def calculate_fees(
        self,
        gross_amount: Decimal,
        developer_share: Optional[Decimal] = None
    ) -> FeeBreakdown:
        """
        Calculate fee breakdown for a PER_REQUEST transaction.

        Args:
            gross_amount: Total amount charged to AI platform
            developer_share: Developer's share (0.0-1.0), defaults to 0.80

        Returns:
            FeeBreakdown with all amounts
        """
        if developer_share is None:
            developer_share = self.DEFAULT_DEVELOPER_SHARE_PERCENT

        platform_fee_percent = Decimal('1.0') - developer_share

        # Calculate amounts
        developer_payout = (gross_amount * developer_share).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP
        )
        platform_fee = (gross_amount - developer_payout).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP
        )

        return FeeBreakdown(
            gross_amount=gross_amount,
            platform_fee=platform_fee,
            developer_payout=developer_payout,
            platform_fee_percent=platform_fee_percent,
            developer_share_percent=developer_share,
            pricing_model=PricingModel.PER_REQUEST
        )

    def calculate_commission_fees(
        self,
        booking_value: Decimal,
        commission_rate: Decimal,
        developer_share: Optional[Decimal] = None
    ) -> FeeBreakdown:
        """
        Calculate fee breakdown for a COMMISSION-based transaction.

        The commission is calculated as: booking_value * commission_rate
        Then split between platform and developer.

        Example:
            - Booking value: $45.00
            - Commission rate: 10% (0.10)
            - Commission: $4.50
            - Platform cut (20%): $0.90
            - Developer cut (80%): $3.60

        Args:
            booking_value: Total value of the transaction being commissioned
            commission_rate: Commission rate (0.0-1.0), e.g., 0.10 for 10%
            developer_share: Developer's share of commission (0.0-1.0), defaults to 0.80

        Returns:
            FeeBreakdown with commission details
        """
        if developer_share is None:
            developer_share = self.DEFAULT_DEVELOPER_SHARE_PERCENT

        # Calculate gross commission
        gross_amount = (booking_value * commission_rate).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP
        )

        platform_fee_percent = Decimal('1.0') - developer_share

        # Split the commission
        developer_payout = (gross_amount * developer_share).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP
        )
        platform_fee = (gross_amount - developer_payout).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP
        )

        return FeeBreakdown(
            gross_amount=gross_amount,
            platform_fee=platform_fee,
            developer_payout=developer_payout,
            platform_fee_percent=platform_fee_percent,
            developer_share_percent=developer_share,
            pricing_model=PricingModel.COMMISSION,
            booking_value=booking_value,
            commission_rate=commission_rate
        )

    def calculate_subscription_fees(
        self,
        subscription_id: str
    ) -> FeeBreakdown:
        """
        Calculate fee breakdown for a SUBSCRIPTION-based transaction.

        Subscription transactions have $0 per-call charge - the subscription
        fee is handled separately (monthly billing).

        Args:
            subscription_id: Reference to the active subscription

        Returns:
            FeeBreakdown with zero per-call charges
        """
        return FeeBreakdown(
            gross_amount=Decimal('0.00'),
            platform_fee=Decimal('0.00'),
            developer_payout=Decimal('0.00'),
            platform_fee_percent=Decimal('0.00'),
            developer_share_percent=Decimal('1.00'),  # N/A for subscription
            pricing_model=PricingModel.SUBSCRIPTION,
            subscription_id=subscription_id
        )

    def calculate_tiered_fees(
        self,
        mcp_id: str,
        current_month_requests: int,
        developer_share_override: Optional[Decimal] = None
    ) -> FeeBreakdown:
        """
        Calculate fee breakdown for a TIERED pricing transaction.

        Looks up the appropriate tier based on the MCP's monthly request volume
        and applies the corresponding rate.

        Args:
            mcp_id: MCP ID to look up tier configuration
            current_month_requests: Number of requests this month (for tier selection)
            developer_share_override: Override the tier's developer share

        Returns:
            FeeBreakdown with tier details
        """
        # Get tier configuration for this MCP (or use defaults)
        tiers = self._get_mcp_tiers(mcp_id)

        # Find applicable tier
        applicable_tier = tiers[0]  # Default to first tier
        for tier in tiers:
            if current_month_requests >= tier.min_requests:
                if tier.max_requests is None or current_month_requests <= tier.max_requests:
                    applicable_tier = tier
                    break

        # Use tier's developer share or override
        developer_share = developer_share_override or applicable_tier.developer_share
        gross_amount = applicable_tier.fee_per_request

        platform_fee_percent = Decimal('1.0') - developer_share

        developer_payout = (gross_amount * developer_share).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP
        )
        platform_fee = (gross_amount - developer_payout).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP
        )

        return FeeBreakdown(
            gross_amount=gross_amount,
            platform_fee=platform_fee,
            developer_payout=developer_payout,
            platform_fee_percent=platform_fee_percent,
            developer_share_percent=developer_share,
            pricing_model=PricingModel.TIERED,
            tier_name=applicable_tier.name
        )

    def calculate_hybrid_fees(
        self,
        base_request_fee: Decimal,
        subscription_id: str,
        developer_share: Optional[Decimal] = None
    ) -> FeeBreakdown:
        """
        Calculate fee breakdown for a HYBRID pricing transaction.

        Hybrid combines a subscription base with per-request fees.
        The subscription fee is handled separately; this calculates
        the per-request component.

        Args:
            base_request_fee: Per-request fee on top of subscription
            subscription_id: Reference to the active subscription
            developer_share: Developer's share (0.0-1.0)

        Returns:
            FeeBreakdown with hybrid details
        """
        if developer_share is None:
            developer_share = self.DEFAULT_DEVELOPER_SHARE_PERCENT

        platform_fee_percent = Decimal('1.0') - developer_share

        developer_payout = (base_request_fee * developer_share).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP
        )
        platform_fee = (base_request_fee - developer_payout).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP
        )

        return FeeBreakdown(
            gross_amount=base_request_fee,
            platform_fee=platform_fee,
            developer_payout=developer_payout,
            platform_fee_percent=platform_fee_percent,
            developer_share_percent=developer_share,
            pricing_model=PricingModel.HYBRID,
            subscription_id=subscription_id
        )

    def _get_mcp_tiers(self, mcp_id: str) -> List[TierConfig]:
        """Get tier configuration for an MCP (cached)."""
        if mcp_id in self._tier_cache:
            return self._tier_cache[mcp_id]

        # TODO: Load custom tiers from database if configured
        # For now, return default tiers
        return self.DEFAULT_TIERS

    def get_mcp_developer_share(self, mcp_id: str) -> Decimal:
        """
        Get the configured developer share for an MCP.

        Allows per-MCP billing splits (e.g., premium MCPs get 70/30 instead of 80/20).

        Args:
            mcp_id: MCP ID

        Returns:
            Developer share as Decimal (0.0-1.0)
        """
        row = self.db.fetch_one(
            "SELECT developer_share FROM mcps WHERE id = ?",
            (mcp_id,)
        )

        if row and row.get('developer_share') is not None:
            return Decimal(str(row['developer_share']))

        return self.DEFAULT_DEVELOPER_SHARE_PERCENT

    # ==========================================
    # TRANSACTION LOGGING
    # ==========================================

    def log_transaction(
        self,
        ai_platform_id: str,
        mcp_id: str,
        developer_id: str,
        request_id: str,
        capability_name: str,
        request_payload: Dict[str, Any],
        gross_amount: Decimal,
        developer_share: Optional[Decimal] = None
    ) -> str:
        """
        Log a new PER_REQUEST transaction (before MCP execution).

        This is the original method for backward compatibility.
        For other pricing models, use log_transaction_with_pricing().

        Args:
            ai_platform_id: AI platform making the request
            mcp_id: MCP handling the request
            developer_id: Developer who owns the MCP
            request_id: Unique request ID (idempotency key)
            capability_name: MCP capability being called
            request_payload: Request data
            gross_amount: Amount to charge
            developer_share: Developer's share (0.0-1.0)

        Returns:
            Transaction ID

        Raises:
            ValueError: If request_id already exists (duplicate)
        """
        return self.log_transaction_with_pricing(
            ai_platform_id=ai_platform_id,
            mcp_id=mcp_id,
            developer_id=developer_id,
            request_id=request_id,
            capability_name=capability_name,
            request_payload=request_payload,
            pricing_model=PricingModel.PER_REQUEST,
            gross_amount=gross_amount,
            developer_share=developer_share
        )

    def log_transaction_with_pricing(
        self,
        ai_platform_id: str,
        mcp_id: str,
        developer_id: str,
        request_id: str,
        capability_name: str,
        request_payload: Dict[str, Any],
        pricing_model: PricingModel = PricingModel.PER_REQUEST,
        # PER_REQUEST / HYBRID parameters
        gross_amount: Optional[Decimal] = None,
        developer_share: Optional[Decimal] = None,
        # COMMISSION parameters
        booking_value: Optional[Decimal] = None,
        commission_rate: Optional[Decimal] = None,
        # SUBSCRIPTION / HYBRID parameters
        subscription_id: Optional[str] = None,
        # TIERED parameters
        current_month_requests: Optional[int] = None,
        tier_name: Optional[str] = None
    ) -> str:
        """
        Log a new transaction with any pricing model.

        Args:
            ai_platform_id: AI platform making the request
            mcp_id: MCP handling the request
            developer_id: Developer who owns the MCP
            request_id: Unique request ID (idempotency key)
            capability_name: MCP capability being called
            request_payload: Request data
            pricing_model: How to calculate fees (PER_REQUEST, COMMISSION, etc.)

            For PER_REQUEST:
                gross_amount: Amount to charge per request
                developer_share: Developer's share (0.0-1.0)

            For COMMISSION:
                booking_value: Total transaction value
                commission_rate: Commission percentage (0.0-1.0)
                developer_share: Developer's share of commission

            For SUBSCRIPTION:
                subscription_id: Reference to active subscription

            For TIERED:
                current_month_requests: Request count for tier selection
                developer_share: Override tier's developer share

            For HYBRID:
                gross_amount: Per-request fee component
                subscription_id: Reference to active subscription
                developer_share: Developer's share (0.0-1.0)

        Returns:
            Transaction ID

        Raises:
            ValueError: If request_id already exists or required params missing
        """
        import json

        # Check for duplicate
        existing = self.db.fetch_one(
            "SELECT id FROM transactions WHERE request_id = ?",
            (request_id,)
        )
        if existing:
            raise ValueError(f"Duplicate request_id: {request_id}")

        # Calculate fees based on pricing model
        if pricing_model == PricingModel.PER_REQUEST:
            if gross_amount is None:
                raise ValueError("gross_amount required for PER_REQUEST pricing")
            fees = self.calculate_fees(gross_amount, developer_share)

        elif pricing_model == PricingModel.COMMISSION:
            if booking_value is None or commission_rate is None:
                raise ValueError("booking_value and commission_rate required for COMMISSION pricing")
            fees = self.calculate_commission_fees(booking_value, commission_rate, developer_share)

        elif pricing_model == PricingModel.SUBSCRIPTION:
            if subscription_id is None:
                raise ValueError("subscription_id required for SUBSCRIPTION pricing")
            fees = self.calculate_subscription_fees(subscription_id)

        elif pricing_model == PricingModel.TIERED:
            if current_month_requests is None:
                # Get current month's request count from database
                current_month_requests = self._get_current_month_requests(mcp_id, ai_platform_id)
            fees = self.calculate_tiered_fees(mcp_id, current_month_requests, developer_share)
            tier_name = fees.tier_name

        elif pricing_model == PricingModel.HYBRID:
            if gross_amount is None or subscription_id is None:
                raise ValueError("gross_amount and subscription_id required for HYBRID pricing")
            fees = self.calculate_hybrid_fees(gross_amount, subscription_id, developer_share)

        else:
            raise ValueError(f"Unknown pricing model: {pricing_model}")

        # Generate ID
        transaction_id = str(uuid.uuid4())

        # Insert transaction with all pricing fields
        self.db.execute(
            """
            INSERT INTO transactions (
                id, ai_platform_id, mcp_id, developer_id,
                request_id, capability_name, request_payload,
                gross_amount, platform_fee, developer_payout,
                status, pricing_model, subscription_id,
                booking_value, commission_rate, tier_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_id, ai_platform_id, mcp_id, developer_id,
                request_id, capability_name, json.dumps(request_payload),
                float(fees.gross_amount), float(fees.platform_fee),
                float(fees.developer_payout),
                TransactionStatus.PENDING.value,
                pricing_model.value,
                subscription_id or fees.subscription_id,
                float(booking_value) if booking_value else None,
                float(commission_rate) if commission_rate else None,
                tier_name or fees.tier_name
            )
        )

        logger.info(
            f"Logged {pricing_model.value} transaction: {transaction_id} "
            f"(gross=${fees.gross_amount}, model={pricing_model.value})"
        )
        return transaction_id

    def _get_current_month_requests(self, mcp_id: str, ai_platform_id: str) -> int:
        """Get the current month's request count for tiered pricing."""
        from datetime import date

        today = date.today()
        month_start = today.replace(day=1).isoformat()

        result = self.db.fetch_one(
            """
            SELECT COALESCE(SUM(total_requests), 0) as count
            FROM daily_stats
            WHERE mcp_id = ? AND ai_platform_id = ? AND date >= ?
            """,
            (mcp_id, ai_platform_id, month_start)
        )

        return int(result['count']) if result else 0

    def complete_transaction(
        self,
        transaction_id: str,
        response: Dict[str, Any],
        response_time_ms: int
    ) -> bool:
        """
        Mark transaction as completed (after successful MCP execution).

        Args:
            transaction_id: Transaction ID
            response: MCP response data
            response_time_ms: Response time in milliseconds

        Returns:
            True if updated
        """
        import json

        rows = self.db.execute(
            """
            UPDATE transactions
            SET status = ?,
                response_payload = ?,
                response_time_ms = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = ?
            """,
            (
                TransactionStatus.COMPLETED.value,
                json.dumps(response),
                response_time_ms,
                transaction_id,
                TransactionStatus.PENDING.value
            )
        )

        if rows > 0:
            logger.info(f"Completed transaction: {transaction_id}")
            # Update daily stats
            self._update_daily_stats(transaction_id, success=True)
            return True
        return False

    def fail_transaction(
        self,
        transaction_id: str,
        error_message: str
    ) -> bool:
        """
        Mark transaction as failed.

        Args:
            transaction_id: Transaction ID
            error_message: Error description

        Returns:
            True if updated
        """
        rows = self.db.execute(
            """
            UPDATE transactions
            SET status = ?,
                error_message = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = ?
            """,
            (
                TransactionStatus.FAILED.value,
                error_message,
                transaction_id,
                TransactionStatus.PENDING.value
            )
        )

        if rows > 0:
            logger.warning(f"Failed transaction: {transaction_id} - {error_message}")
            # Update daily stats
            self._update_daily_stats(transaction_id, success=False)
            return True
        return False

    def refund_transaction(self, transaction_id: str, reason: str = None) -> bool:
        """
        Refund a completed transaction.

        Args:
            transaction_id: Transaction ID
            reason: Refund reason

        Returns:
            True if refunded
        """
        rows = self.db.execute(
            """
            UPDATE transactions
            SET status = ?,
                error_message = ?
            WHERE id = ? AND status = ?
            """,
            (
                TransactionStatus.REFUNDED.value,
                f"Refunded: {reason}" if reason else "Refunded",
                transaction_id,
                TransactionStatus.COMPLETED.value
            )
        )

        if rows > 0:
            logger.info(f"Refunded transaction: {transaction_id}")
            return True
        return False

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID"""
        row = self.db.fetch_one(
            "SELECT * FROM transactions WHERE id = ?",
            (transaction_id,)
        )
        return Transaction.from_row(row) if row else None

    def get_transaction_by_request_id(self, request_id: str) -> Optional[Transaction]:
        """Get transaction by request ID (idempotency key)"""
        row = self.db.fetch_one(
            "SELECT * FROM transactions WHERE request_id = ?",
            (request_id,)
        )
        return Transaction.from_row(row) if row else None

    def _update_daily_stats(self, transaction_id: str, success: bool):
        """Update daily stats after transaction completion"""
        txn = self.db.fetch_one(
            "SELECT * FROM transactions WHERE id = ?",
            (transaction_id,)
        )

        if not txn:
            return

        today = date.today().isoformat()

        # Check if stats row exists
        existing = self.db.fetch_one(
            """
            SELECT id FROM daily_stats
            WHERE date = ? AND mcp_id = ? AND ai_platform_id = ?
            """,
            (today, txn['mcp_id'], txn['ai_platform_id'])
        )

        if existing:
            # Update existing
            if success:
                self.db.execute(
                    """
                    UPDATE daily_stats
                    SET total_requests = total_requests + 1,
                        successful_requests = successful_requests + 1,
                        gross_revenue = gross_revenue + ?,
                        platform_revenue = platform_revenue + ?,
                        developer_revenue = developer_revenue + ?
                    WHERE id = ?
                    """,
                    (
                        float(txn['gross_amount']),
                        float(txn['platform_fee']),
                        float(txn['developer_payout']),
                        existing['id']
                    )
                )
            else:
                self.db.execute(
                    """
                    UPDATE daily_stats
                    SET total_requests = total_requests + 1,
                        failed_requests = failed_requests + 1
                    WHERE id = ?
                    """,
                    (existing['id'],)
                )
        else:
            # Insert new
            stats_id = str(uuid.uuid4())
            if success:
                self.db.execute(
                    """
                    INSERT INTO daily_stats (
                        id, date, mcp_id, ai_platform_id, developer_id,
                        total_requests, successful_requests, failed_requests,
                        gross_revenue, platform_revenue, developer_revenue
                    ) VALUES (?, ?, ?, ?, ?, 1, 1, 0, ?, ?, ?)
                    """,
                    (
                        stats_id, today, txn['mcp_id'], txn['ai_platform_id'],
                        txn['developer_id'],
                        float(txn['gross_amount']),
                        float(txn['platform_fee']),
                        float(txn['developer_payout'])
                    )
                )
            else:
                self.db.execute(
                    """
                    INSERT INTO daily_stats (
                        id, date, mcp_id, ai_platform_id, developer_id,
                        total_requests, successful_requests, failed_requests,
                        gross_revenue, platform_revenue, developer_revenue
                    ) VALUES (?, ?, ?, ?, ?, 1, 0, 1, 0, 0, 0)
                    """,
                    (
                        stats_id, today, txn['mcp_id'], txn['ai_platform_id'],
                        txn['developer_id']
                    )
                )

    # ==========================================
    # INVOICE GENERATION
    # ==========================================

    def generate_invoice(
        self,
        ai_platform_id: str,
        period_start: date,
        period_end: date,
        tax_rate: Decimal = Decimal('0.0'),
        due_days: int = 30
    ) -> Invoice:
        """
        Generate invoice for an AI platform.

        Args:
            ai_platform_id: AI platform ID
            period_start: Billing period start
            period_end: Billing period end
            tax_rate: Tax rate (0.0-1.0)
            due_days: Days until due

        Returns:
            Generated Invoice
        """
        # Calculate totals from transactions
        totals = self.db.fetch_one(
            """
            SELECT
                COALESCE(SUM(gross_amount), 0) as subtotal,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE ai_platform_id = ?
                AND status = 'completed'
                AND DATE(completed_at) >= ?
                AND DATE(completed_at) <= ?
            """,
            (ai_platform_id, period_start.isoformat(), period_end.isoformat())
        )

        subtotal = Decimal(str(totals['subtotal'] or 0))
        tax = (subtotal * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total = subtotal + tax

        # Generate invoice
        invoice_id = str(uuid.uuid4())
        due_date = date.today() + timedelta(days=due_days)

        self.db.execute(
            """
            INSERT INTO invoices (
                id, ai_platform_id, period_start, period_end,
                subtotal, tax, total, status, due_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoice_id, ai_platform_id,
                period_start.isoformat(), period_end.isoformat(),
                float(subtotal), float(tax), float(total),
                InvoiceStatus.DRAFT.value, due_date.isoformat()
            )
        )

        logger.info(f"Generated invoice: {invoice_id} (${total})")

        return Invoice(
            id=invoice_id,
            ai_platform_id=ai_platform_id,
            period_start=period_start,
            period_end=period_end,
            subtotal=subtotal,
            tax=tax,
            total=total,
            currency='USD',
            status=InvoiceStatus.DRAFT,
            due_date=due_date
        )

    def send_invoice(self, invoice_id: str) -> bool:
        """Mark invoice as sent"""
        rows = self.db.execute(
            """
            UPDATE invoices
            SET status = ?
            WHERE id = ? AND status = ?
            """,
            (InvoiceStatus.SENT.value, invoice_id, InvoiceStatus.DRAFT.value)
        )
        return rows > 0

    def mark_invoice_paid(
        self,
        invoice_id: str,
        stripe_invoice_id: Optional[str] = None
    ) -> bool:
        """Mark invoice as paid"""
        rows = self.db.execute(
            """
            UPDATE invoices
            SET status = ?,
                paid_at = CURRENT_TIMESTAMP,
                stripe_invoice_id = ?
            WHERE id = ? AND status IN (?, ?)
            """,
            (
                InvoiceStatus.PAID.value,
                stripe_invoice_id,
                invoice_id,
                InvoiceStatus.SENT.value,
                InvoiceStatus.OVERDUE.value
            )
        )
        return rows > 0

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID"""
        row = self.db.fetch_one(
            "SELECT * FROM invoices WHERE id = ?",
            (invoice_id,)
        )
        return Invoice.from_row(row) if row else None

    def get_invoices_for_platform(
        self,
        ai_platform_id: str,
        limit: int = 20
    ) -> List[Invoice]:
        """Get invoices for an AI platform"""
        rows = self.db.fetch_all(
            """
            SELECT * FROM invoices
            WHERE ai_platform_id = ?
            ORDER BY period_end DESC
            LIMIT ?
            """,
            (ai_platform_id, limit)
        )
        return [Invoice.from_row(row) for row in rows]

    # ==========================================
    # PAYOUT PROCESSING
    # ==========================================

    def process_payouts(
        self,
        developer_id: str,
        period_start: date,
        period_end: date
    ) -> Payout:
        """
        Calculate and create a payout for a developer.

        Args:
            developer_id: Developer ID
            period_start: Payout period start
            period_end: Payout period end

        Returns:
            Created Payout
        """
        # Calculate total earnings
        totals = self.db.fetch_one(
            """
            SELECT
                COALESCE(SUM(developer_payout), 0) as total_earnings,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE developer_id = ?
                AND status = 'completed'
                AND DATE(completed_at) >= ?
                AND DATE(completed_at) <= ?
            """,
            (developer_id, period_start.isoformat(), period_end.isoformat())
        )

        amount = Decimal(str(totals['total_earnings'] or 0))

        # Create payout record
        payout_id = str(uuid.uuid4())

        self.db.execute(
            """
            INSERT INTO payouts (
                id, developer_id, amount, period_start, period_end, status
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payout_id, developer_id, float(amount),
                period_start.isoformat(), period_end.isoformat(),
                PayoutStatus.PENDING.value
            )
        )

        logger.info(f"Created payout: {payout_id} (${amount})")

        return Payout(
            id=payout_id,
            developer_id=developer_id,
            amount=amount,
            currency='USD',
            period_start=period_start,
            period_end=period_end,
            status=PayoutStatus.PENDING
        )

    def execute_payout(
        self,
        payout_id: str,
        stripe_transfer_id: Optional[str] = None
    ) -> bool:
        """
        Execute a pending payout (mark as processing/completed).

        In production, this would:
        1. Call Stripe API to transfer funds
        2. Store Stripe transfer ID
        3. Update status

        Args:
            payout_id: Payout ID
            stripe_transfer_id: Stripe transfer ID (if using Stripe)

        Returns:
            True if executed
        """
        # For now, just mark as completed (Stripe integration TODO)
        rows = self.db.execute(
            """
            UPDATE payouts
            SET status = ?,
                stripe_transfer_id = ?,
                processed_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = ?
            """,
            (
                PayoutStatus.COMPLETED.value,
                stripe_transfer_id,
                payout_id,
                PayoutStatus.PENDING.value
            )
        )

        if rows > 0:
            logger.info(f"Executed payout: {payout_id}")
            return True
        return False

    def fail_payout(self, payout_id: str, error_message: str) -> bool:
        """Mark payout as failed"""
        rows = self.db.execute(
            """
            UPDATE payouts
            SET status = ?,
                error_message = ?
            WHERE id = ? AND status IN (?, ?)
            """,
            (
                PayoutStatus.FAILED.value,
                error_message,
                payout_id,
                PayoutStatus.PENDING.value,
                PayoutStatus.PROCESSING.value
            )
        )
        return rows > 0

    def get_payout(self, payout_id: str) -> Optional[Payout]:
        """Get payout by ID"""
        row = self.db.fetch_one(
            "SELECT * FROM payouts WHERE id = ?",
            (payout_id,)
        )
        return Payout.from_row(row) if row else None

    def get_payouts_for_developer(
        self,
        developer_id: str,
        limit: int = 20
    ) -> List[Payout]:
        """Get payouts for a developer"""
        rows = self.db.fetch_all(
            """
            SELECT * FROM payouts
            WHERE developer_id = ?
            ORDER BY period_end DESC
            LIMIT ?
            """,
            (developer_id, limit)
        )
        return [Payout.from_row(row) for row in rows]

    # ==========================================
    # REPORTING
    # ==========================================

    def get_platform_revenue_summary(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Get platform revenue summary for a period.

        Returns:
            Dict with revenue breakdown
        """
        stats = self.db.fetch_one(
            """
            SELECT
                COALESCE(SUM(gross_revenue), 0) as total_gross,
                COALESCE(SUM(platform_revenue), 0) as total_platform,
                COALESCE(SUM(developer_revenue), 0) as total_developer,
                COALESCE(SUM(total_requests), 0) as total_requests,
                COALESCE(SUM(successful_requests), 0) as successful_requests,
                COALESCE(SUM(failed_requests), 0) as failed_requests
            FROM daily_stats
            WHERE date >= ? AND date <= ?
            """,
            (start_date.isoformat(), end_date.isoformat())
        )

        success_rate = 0.0
        if stats['total_requests'] and stats['total_requests'] > 0:
            success_rate = (stats['successful_requests'] / stats['total_requests']) * 100

        return {
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'gross_revenue': float(stats['total_gross'] or 0),
            'platform_revenue': float(stats['total_platform'] or 0),
            'developer_payouts': float(stats['total_developer'] or 0),
            'total_requests': int(stats['total_requests'] or 0),
            'successful_requests': int(stats['successful_requests'] or 0),
            'failed_requests': int(stats['failed_requests'] or 0),
            'success_rate_percent': round(success_rate, 2)
        }

    def get_developer_earnings(
        self,
        developer_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Get developer earnings for a period"""
        stats = self.db.fetch_one(
            """
            SELECT
                COALESCE(SUM(developer_revenue), 0) as total_earnings,
                COALESCE(SUM(total_requests), 0) as total_requests
            FROM daily_stats
            WHERE developer_id = ?
                AND date >= ?
                AND date <= ?
            """,
            (developer_id, start_date.isoformat(), end_date.isoformat())
        )

        return {
            'developer_id': developer_id,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_earnings': float(stats['total_earnings'] or 0),
            'total_requests': int(stats['total_requests'] or 0)
        }

    def get_mcp_revenue(
        self,
        mcp_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Get revenue for a specific MCP"""
        stats = self.db.fetch_one(
            """
            SELECT
                COALESCE(SUM(gross_revenue), 0) as gross,
                COALESCE(SUM(developer_revenue), 0) as developer,
                COALESCE(SUM(total_requests), 0) as requests
            FROM daily_stats
            WHERE mcp_id = ?
                AND date >= ?
                AND date <= ?
            """,
            (mcp_id, start_date.isoformat(), end_date.isoformat())
        )

        return {
            'mcp_id': mcp_id,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'gross_revenue': float(stats['gross'] or 0),
            'developer_revenue': float(stats['developer'] or 0),
            'total_requests': int(stats['requests'] or 0)
        }


# Example usage
if __name__ == "__main__":
    from database import create_test_database
    from decimal import Decimal

    # Create test database
    db = create_test_database()

    # Set up test data
    dev_id = str(uuid.uuid4())
    platform_id = str(uuid.uuid4())
    mcp_id = str(uuid.uuid4())

    db.execute(
        "INSERT INTO developers (id, email, display_name, api_key_hash) VALUES (?, ?, ?, ?)",
        (dev_id, 'dev@example.com', 'Test Developer', 'hash123')
    )
    db.execute(
        "INSERT INTO ai_platforms (id, name, api_key_hash) VALUES (?, ?, ?)",
        (platform_id, 'Test Platform', 'hash456')
    )
    db.execute(
        """
        INSERT INTO mcps (id, developer_id, name, slug, category, endpoint_url, developer_share)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (mcp_id, dev_id, 'Test MCP', 'test-mcp', 'rideshare', 'http://localhost:8000', 0.75)
    )

    # Create billing system
    billing = BillingSystem(db)

    # ===========================================
    # Test PER_REQUEST pricing (default)
    # ===========================================
    print("=== PER_REQUEST Fee Calculation (default) ===")
    fees = billing.calculate_fees(Decimal('0.02'))
    print(f"Gross: ${fees.gross_amount}")
    print(f"Platform fee (20%): ${fees.platform_fee}")
    print(f"Developer payout (80%): ${fees.developer_payout}")
    print(f"Pricing model: {fees.pricing_model.value}")

    # Log per-request transaction
    print("\n=== PER_REQUEST Transaction ===")
    txn_id = billing.log_transaction(
        ai_platform_id=platform_id,
        mcp_id=mcp_id,
        developer_id=dev_id,
        request_id='req_001',
        capability_name='compare_prices',
        request_payload={'pickup': {'lat': 37.7879}},
        gross_amount=Decimal('0.02')
    )
    print(f"Logged transaction: {txn_id}")

    # Complete transaction
    billing.complete_transaction(
        txn_id,
        response={'uber': '$42.50', 'lyft': '$38.25'},
        response_time_ms=145
    )
    print("Transaction completed")

    # ===========================================
    # Test COMMISSION pricing (booking services)
    # ===========================================
    print("\n=== COMMISSION Fee Calculation ===")
    commission_fees = billing.calculate_commission_fees(
        booking_value=Decimal('45.00'),  # $45 ride fare
        commission_rate=Decimal('0.10'),  # 10% commission
        developer_share=Decimal('0.70')   # 70/30 split for premium MCP
    )
    print(f"Booking value: ${commission_fees.booking_value}")
    print(f"Commission rate: {float(commission_fees.commission_rate) * 100}%")
    print(f"Gross (commission): ${commission_fees.gross_amount}")
    print(f"Platform fee: ${commission_fees.platform_fee}")
    print(f"Developer payout: ${commission_fees.developer_payout}")

    # Log commission transaction
    print("\n=== COMMISSION Transaction ===")
    commission_txn_id = billing.log_transaction_with_pricing(
        ai_platform_id=platform_id,
        mcp_id=mcp_id,
        developer_id=dev_id,
        request_id='req_002_booking',
        capability_name='book_ride',
        request_payload={'pickup': {'lat': 37.7879}, 'destination': {'lat': 37.7749}},
        pricing_model=PricingModel.COMMISSION,
        booking_value=Decimal('45.00'),
        commission_rate=Decimal('0.10'),
        developer_share=Decimal('0.70')
    )
    print(f"Logged commission transaction: {commission_txn_id}")

    # ===========================================
    # Test SUBSCRIPTION pricing
    # ===========================================
    print("\n=== SUBSCRIPTION Fee Calculation ===")
    subscription_fees = billing.calculate_subscription_fees(
        subscription_id='sub_abc123'
    )
    print(f"Gross (per-call): ${subscription_fees.gross_amount}")
    print(f"Subscription ID: {subscription_fees.subscription_id}")
    print("(Subscription fee charged separately monthly)")

    # ===========================================
    # Test TIERED pricing
    # ===========================================
    print("\n=== TIERED Fee Calculation ===")

    # Low volume (starter tier)
    tier_fees_low = billing.calculate_tiered_fees(mcp_id, current_month_requests=500)
    print(f"At 500 requests (starter tier):")
    print(f"  Tier: {tier_fees_low.tier_name}")
    print(f"  Fee per request: ${tier_fees_low.gross_amount}")

    # High volume (enterprise tier)
    tier_fees_high = billing.calculate_tiered_fees(mcp_id, current_month_requests=150000)
    print(f"At 150,000 requests (enterprise tier):")
    print(f"  Tier: {tier_fees_high.tier_name}")
    print(f"  Fee per request: ${tier_fees_high.gross_amount}")

    # ===========================================
    # Test configurable developer share
    # ===========================================
    print("\n=== Configurable Developer Share ===")
    dev_share = billing.get_mcp_developer_share(mcp_id)
    print(f"MCP developer share: {float(dev_share) * 100}%")

    # Calculate with custom share
    custom_fees = billing.calculate_fees(Decimal('0.02'), developer_share=dev_share)
    print(f"With 75% developer share:")
    print(f"  Platform fee: ${custom_fees.platform_fee}")
    print(f"  Developer payout: ${custom_fees.developer_payout}")

    # ===========================================
    # Invoice and Payout
    # ===========================================
    print("\n=== Invoice Generation ===")
    today = date.today()
    invoice = billing.generate_invoice(
        ai_platform_id=platform_id,
        period_start=today - timedelta(days=30),
        period_end=today
    )
    print(f"Generated invoice: {invoice.id}")
    print(f"Total: ${invoice.total}")

    print("\n=== Payout Processing ===")
    payout = billing.process_payouts(
        developer_id=dev_id,
        period_start=today - timedelta(days=30),
        period_end=today
    )
    print(f"Created payout: {payout.id}")
    print(f"Amount: ${payout.amount}")

    print("\n=== Revenue Summary ===")
    summary = billing.get_platform_revenue_summary(
        start_date=today - timedelta(days=30),
        end_date=today
    )
    print(f"Gross revenue: ${summary['gross_revenue']}")
    print(f"Platform revenue: ${summary['platform_revenue']}")
    print(f"Total requests: {summary['total_requests']}")

    db.close()

    print("\n=== Pricing Model Summary ===")
    print("PER_REQUEST:   $X per API call (default)")
    print("SUBSCRIPTION:  Monthly fee, unlimited calls")
    print("COMMISSION:    % of transaction value (bookings)")
    print("TIERED:        Volume discounts (starter->enterprise)")
    print("HYBRID:        Base subscription + per-request")
