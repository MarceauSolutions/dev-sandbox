"""Profile management API routes."""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.base import get_session
from src.models.user import UserProfile, Vehicle, CurrentPolicy, DrivingRecord

router = APIRouter()


# --- Pydantic Schemas ---

class VehicleCreate(BaseModel):
    year: int
    make: str
    model: str
    trim: str | None = None
    vin: str | None = None
    annual_mileage: int | None = None
    usage_type: str = "commute"
    estimated_value: float | None = None


class PolicyCreate(BaseModel):
    vehicle_id: int | None = None
    carrier: str
    policy_number: str | None = None
    monthly_premium: float
    annual_premium: float
    deductible: float = 500.0
    liability_bodily: str | None = None
    liability_property: float | None = None
    collision: bool = True
    comprehensive: bool = True
    uninsured_motorist: bool = True
    medical_payments: float | None = None
    roadside_assistance: bool = False
    rental_reimbursement: bool = False
    start_date: date | None = None
    renewal_date: date | None = None
    payment_frequency: str = "monthly"


class DrivingRecordCreate(BaseModel):
    age: int | None = None
    years_licensed: int | None = None
    accidents_3yr: int = 0
    tickets_3yr: int = 0
    dui_history: bool = False
    credit_score_range: str | None = None
    education_level: str | None = None
    homeowner: bool = False
    married: bool = False
    military: bool = False
    defensive_driving_course: bool = False
    good_student: bool = False


class ProfileCreate(BaseModel):
    name: str
    email: str | None = None
    telegram_chat_id: str | None = None


# --- Routes ---

@router.post("/")
async def create_profile(data: ProfileCreate, session: AsyncSession = Depends(get_session)):
    """Create a new user profile."""
    profile = UserProfile(
        name=data.name,
        email=data.email,
        telegram_chat_id=data.telegram_chat_id,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return {"id": profile.id, "name": profile.name, "message": "Profile created"}


@router.get("/{user_id}")
async def get_profile(user_id: int, session: AsyncSession = Depends(get_session)):
    """Get full user profile with vehicles, policies, and driving record."""
    stmt = (
        select(UserProfile)
        .where(UserProfile.id == user_id)
        .options(
            selectinload(UserProfile.vehicles),
            selectinload(UserProfile.policies),
            selectinload(UserProfile.driving_record),
        )
    )
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {
        "id": profile.id,
        "name": profile.name,
        "email": profile.email,
        "telegram_chat_id": profile.telegram_chat_id,
        "vehicles": [
            {
                "id": v.id, "year": v.year, "make": v.make, "model": v.model,
                "trim": v.trim, "vin": v.vin, "annual_mileage": v.annual_mileage,
                "usage_type": v.usage_type, "estimated_value": v.estimated_value,
            }
            for v in profile.vehicles
        ],
        "policies": [
            {
                "id": p.id, "carrier": p.carrier, "monthly_premium": p.monthly_premium,
                "annual_premium": p.annual_premium, "deductible": p.deductible,
                "renewal_date": str(p.renewal_date) if p.renewal_date else None,
                "payment_frequency": p.payment_frequency,
            }
            for p in profile.policies
        ],
        "driving_record": {
            "age": profile.driving_record.age,
            "years_licensed": profile.driving_record.years_licensed,
            "accidents_3yr": profile.driving_record.accidents_3yr,
            "tickets_3yr": profile.driving_record.tickets_3yr,
            "credit_score_range": profile.driving_record.credit_score_range,
            "homeowner": profile.driving_record.homeowner,
            "married": profile.driving_record.married,
            "defensive_driving_course": profile.driving_record.defensive_driving_course,
        } if profile.driving_record else None,
    }


@router.post("/{user_id}/vehicle")
async def add_vehicle(user_id: int, data: VehicleCreate, session: AsyncSession = Depends(get_session)):
    """Add a vehicle to user profile."""
    vehicle = Vehicle(user_id=user_id, **data.model_dump())
    session.add(vehicle)
    await session.commit()
    await session.refresh(vehicle)
    return {"id": vehicle.id, "message": f"Added {data.year} {data.make} {data.model}"}


@router.post("/{user_id}/policy")
async def add_policy(user_id: int, data: PolicyCreate, session: AsyncSession = Depends(get_session)):
    """Add an insurance policy to user profile."""
    policy = CurrentPolicy(user_id=user_id, **data.model_dump())
    session.add(policy)
    await session.commit()
    await session.refresh(policy)
    return {"id": policy.id, "message": f"Added {data.carrier} policy"}


@router.put("/{user_id}/policy/{policy_id}")
async def update_policy(
    user_id: int, policy_id: int, data: PolicyCreate,
    session: AsyncSession = Depends(get_session),
):
    """Update an existing policy."""
    stmt = select(CurrentPolicy).where(
        CurrentPolicy.id == policy_id,
        CurrentPolicy.user_id == user_id,
    )
    result = await session.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    for key, value in data.model_dump().items():
        setattr(policy, key, value)
    
    await session.commit()
    return {"message": "Policy updated"}


@router.post("/{user_id}/driving-record")
async def set_driving_record(
    user_id: int, data: DrivingRecordCreate,
    session: AsyncSession = Depends(get_session),
):
    """Set or update driving record."""
    stmt = select(DrivingRecord).where(DrivingRecord.user_id == user_id)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    
    if record:
        for key, value in data.model_dump().items():
            setattr(record, key, value)
    else:
        record = DrivingRecord(user_id=user_id, **data.model_dump())
        session.add(record)
    
    await session.commit()
    return {"message": "Driving record updated"}
