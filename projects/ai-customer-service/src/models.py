"""Data models for AI Customer Service."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class CallStatus(str, Enum):
    """Status of a phone call."""
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TRANSFERRED = "transferred"
    ABANDONED = "abandoned"
    FAILED = "failed"


class OrderStatus(str, Enum):
    """Status of an order."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class TranscriptEntry(BaseModel):
    """A single entry in a call transcript."""
    role: str  # "customer", "ai", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MenuItem(BaseModel):
    """A menu item."""
    id: str
    name: str
    description: Optional[str] = None
    price: float
    category: str
    modifiers: list[dict] = Field(default_factory=list)
    available: bool = True


class OrderItem(BaseModel):
    """An item in an order."""
    menu_item_id: str
    name: str
    quantity: int = 1
    modifiers: list[str] = Field(default_factory=list)
    special_instructions: Optional[str] = None
    unit_price: float
    total_price: float


class Order(BaseModel):
    """A customer order."""
    id: str
    call_id: str
    restaurant_id: str
    items: list[OrderItem] = Field(default_factory=list)
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    pos_order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Call(BaseModel):
    """A phone call record."""
    id: str
    restaurant_id: str
    twilio_sid: str
    caller_number: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    duration_seconds: int = 0
    status: CallStatus = CallStatus.RINGING
    transcript: list[TranscriptEntry] = Field(default_factory=list)
    order_id: Optional[str] = None
    transfer_reason: Optional[str] = None
    cost_cents: int = 0


class Restaurant(BaseModel):
    """A restaurant configuration."""
    id: str
    name: str
    phone_number: str  # Twilio number assigned
    fallback_number: str  # Human transfer target
    timezone: str = "America/New_York"
    greeting: str = "Thank you for calling! How can I help you today?"
    menu: list[MenuItem] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)
    pos_type: Optional[str] = None  # "toast", "square", etc.
    pos_config: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationState(BaseModel):
    """Current state of a conversation."""
    call_id: str
    restaurant_id: str
    current_order: Optional[Order] = None
    context: list[dict] = Field(default_factory=list)  # Message history for LLM
    awaiting_confirmation: bool = False
    transfer_requested: bool = False
