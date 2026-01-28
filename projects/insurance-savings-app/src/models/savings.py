"""Savings recommendation and premium history models."""
from datetime import date, datetime
from sqlalchemy import String, Integer, Float, Date, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class SavingsRecommendation(Base):
    __tablename__ = "savings_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    
    category: Mapped[str] = mapped_column(String(50))
    # Categories: deductible, coverage, discount, switching, bundling, payment, timing
    
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    action_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    estimated_annual_savings: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1=highest, 10=lowest
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="new")  # new, viewed, applied, dismissed
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Link to specific deal if applicable
    deal_id: Mapped[int | None] = mapped_column(ForeignKey("insurance_deals.id"), nullable=True)


class PremiumHistory(Base):
    __tablename__ = "premium_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    carrier: Mapped[str] = mapped_column(String(100))
    
    monthly_premium: Mapped[float] = mapped_column(Float)
    annual_premium: Mapped[float] = mapped_column(Float)
    deductible: Mapped[float] = mapped_column(Float)
    
    recorded_date: Mapped[date] = mapped_column(Date, default=date.today)
    policy_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    policy_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
