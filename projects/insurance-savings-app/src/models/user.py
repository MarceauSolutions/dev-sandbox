"""User-related models."""
from datetime import date, datetime
from sqlalchemy import String, Integer, Float, Date, DateTime, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum


class PaymentFrequency(str, enum.Enum):
    MONTHLY = "monthly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"


class CreditScoreRange(str, enum.Enum):
    EXCELLENT = "excellent"      # 800+
    VERY_GOOD = "very_good"      # 740-799
    GOOD = "good"                # 670-739
    FAIR = "fair"                # 580-669
    POOR = "poor"                # Below 580


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    policies: Mapped[list["CurrentPolicy"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    driving_record: Mapped["DrivingRecord | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"))
    year: Mapped[int] = mapped_column(Integer)
    make: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    trim: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    annual_mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_type: Mapped[str] = mapped_column(String(30), default="commute")  # commute, pleasure, business
    estimated_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    user: Mapped["UserProfile"] = relationship(back_populates="vehicles")


class CurrentPolicy(Base):
    __tablename__ = "current_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"))
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    carrier: Mapped[str] = mapped_column(String(100))
    policy_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Premiums
    monthly_premium: Mapped[float] = mapped_column(Float)
    annual_premium: Mapped[float] = mapped_column(Float)
    deductible: Mapped[float] = mapped_column(Float, default=500.0)

    # Coverage limits (in thousands)
    liability_bodily: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g., "100/300"
    liability_property: Mapped[float | None] = mapped_column(Float, nullable=True)  # e.g., 100000
    collision: Mapped[bool] = mapped_column(Boolean, default=True)
    comprehensive: Mapped[bool] = mapped_column(Boolean, default=True)
    uninsured_motorist: Mapped[bool] = mapped_column(Boolean, default=True)
    medical_payments: Mapped[float | None] = mapped_column(Float, nullable=True)
    roadside_assistance: Mapped[bool] = mapped_column(Boolean, default=False)
    rental_reimbursement: Mapped[bool] = mapped_column(Boolean, default=False)

    # Dates
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    renewal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_frequency: Mapped[str] = mapped_column(String(20), default=PaymentFrequency.MONTHLY.value)

    user: Mapped["UserProfile"] = relationship(back_populates="policies")


class DrivingRecord(Base):
    __tablename__ = "driving_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), unique=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    years_licensed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accidents_3yr: Mapped[int] = mapped_column(Integer, default=0)
    tickets_3yr: Mapped[int] = mapped_column(Integer, default=0)
    dui_history: Mapped[bool] = mapped_column(Boolean, default=False)
    credit_score_range: Mapped[str | None] = mapped_column(String(20), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(30), nullable=True)  # high_school, bachelors, masters, phd
    homeowner: Mapped[bool] = mapped_column(Boolean, default=False)
    married: Mapped[bool] = mapped_column(Boolean, default=False)
    military: Mapped[bool] = mapped_column(Boolean, default=False)
    defensive_driving_course: Mapped[bool] = mapped_column(Boolean, default=False)
    good_student: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["UserProfile"] = relationship(back_populates="driving_record")
