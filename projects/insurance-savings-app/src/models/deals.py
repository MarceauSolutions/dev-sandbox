"""Insurance deal/promo models."""
from datetime import date, datetime
from sqlalchemy import String, Integer, Float, Date, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class InsuranceDeal(Base):
    __tablename__ = "insurance_deals"

    id: Mapped[int] = mapped_column(primary_key=True)
    carrier: Mapped[str] = mapped_column(String(100), index=True)
    deal_type: Mapped[str] = mapped_column(String(50))  # new_customer, bundle, seasonal, loyalty, referral
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    
    # Savings info
    estimated_savings_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_savings_amt: Mapped[float | None] = mapped_column(Float, nullable=True)
    promo_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Validity
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Details
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclusions: Mapped[str | None] = mapped_column(Text, nullable=True)
    fine_print: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Dedup
    content_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
