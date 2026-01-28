"""Dashboard routes — serves the web UI."""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import TEMPLATES_DIR
from src.models.base import get_session
from src.models.user import UserProfile, Vehicle, CurrentPolicy, DrivingRecord
from src.models.deals import InsuranceDeal
from src.models.savings import SavingsRecommendation, PremiumHistory

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, session: AsyncSession = Depends(get_session)):
    """Main dashboard page."""
    # Get first user (single-user MVP)
    stmt = (
        select(UserProfile)
        .options(
            selectinload(UserProfile.vehicles),
            selectinload(UserProfile.policies),
            selectinload(UserProfile.driving_record),
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    # Get active deals
    deals_stmt = (
        select(InsuranceDeal)
        .where(InsuranceDeal.is_active == True)
        .order_by(desc(InsuranceDeal.scraped_at))
        .limit(20)
    )
    deals_result = await session.execute(deals_stmt)
    deals = deals_result.scalars().all()
    
    # Get savings recommendations
    savings = []
    total_savings = 0
    current_annual = 0
    
    if user:
        savings_stmt = (
            select(SavingsRecommendation)
            .where(SavingsRecommendation.user_id == user.id)
            .order_by(desc(SavingsRecommendation.estimated_annual_savings))
        )
        savings_result = await session.execute(savings_stmt)
        savings = savings_result.scalars().all()
        total_savings = sum(s.estimated_annual_savings for s in savings if s.status != "dismissed")
        current_annual = sum(p.annual_premium for p in user.policies) if user.policies else 0
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "deals": deals,
        "savings": savings,
        "total_savings": total_savings,
        "current_annual": current_annual,
        "optimized_annual": current_annual - total_savings,
    })


@router.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    """Profile setup page."""
    return templates.TemplateResponse("setup.html", {"request": request})


@router.get("/deals", response_class=HTMLResponse)
async def deals_page(request: Request, session: AsyncSession = Depends(get_session)):
    """All deals page."""
    stmt = (
        select(InsuranceDeal)
        .where(InsuranceDeal.is_active == True)
        .order_by(desc(InsuranceDeal.scraped_at))
    )
    result = await session.execute(stmt)
    deals = result.scalars().all()
    
    # Group by carrier
    by_carrier = {}
    for deal in deals:
        if deal.carrier not in by_carrier:
            by_carrier[deal.carrier] = []
        by_carrier[deal.carrier].append(deal)
    
    return templates.TemplateResponse("deals.html", {
        "request": request,
        "deals": deals,
        "by_carrier": by_carrier,
    })
