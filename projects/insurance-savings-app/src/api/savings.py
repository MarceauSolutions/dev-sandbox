"""Savings recommendations API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import get_session
from src.models.savings import SavingsRecommendation, PremiumHistory
from src.models.user import UserProfile, CurrentPolicy
from src.calculators.savings_engine import run_savings_analysis_for_user

router = APIRouter()


@router.get("/{user_id}")
async def get_savings(
    user_id: int,
    status: str | None = None,
    category: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Get savings recommendations for a user, sorted by estimated savings."""
    stmt = (
        select(SavingsRecommendation)
        .where(SavingsRecommendation.user_id == user_id)
        .order_by(desc(SavingsRecommendation.estimated_annual_savings))
    )
    
    if status:
        stmt = stmt.where(SavingsRecommendation.status == status)
    if category:
        stmt = stmt.where(SavingsRecommendation.category == category)
    
    result = await session.execute(stmt)
    recs = result.scalars().all()
    
    total_potential = sum(r.estimated_annual_savings for r in recs if r.status != "dismissed")
    applied_savings = sum(r.estimated_annual_savings for r in recs if r.status == "applied")
    
    return {
        "user_id": user_id,
        "total_potential_savings": round(total_potential, 2),
        "applied_savings": round(applied_savings, 2),
        "recommendation_count": len(recs),
        "recommendations": [
            {
                "id": r.id,
                "category": r.category,
                "title": r.title,
                "description": r.description,
                "action_steps": r.action_steps,
                "estimated_annual_savings": r.estimated_annual_savings,
                "confidence": r.confidence,
                "priority": r.priority,
                "status": r.status,
                "created_at": str(r.created_at),
            }
            for r in recs
        ],
    }


@router.post("/{user_id}/analyze")
async def trigger_analysis(user_id: int, session: AsyncSession = Depends(get_session)):
    """Manually trigger savings analysis for a user."""
    # Verify user exists
    user = await session.get(UserProfile, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    count = await run_savings_analysis_for_user(user_id)
    return {"message": f"Analysis complete. Generated {count} recommendations.", "count": count}


@router.put("/{user_id}/recommendation/{rec_id}/status")
async def update_recommendation_status(
    user_id: int, rec_id: int, status: str,
    session: AsyncSession = Depends(get_session),
):
    """Update recommendation status (new, viewed, applied, dismissed)."""
    valid_statuses = {"new", "viewed", "applied", "dismissed"}
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid_statuses}")
    
    stmt = select(SavingsRecommendation).where(
        SavingsRecommendation.id == rec_id,
        SavingsRecommendation.user_id == user_id,
    )
    result = await session.execute(stmt)
    rec = result.scalar_one_or_none()
    
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    rec.status = status
    await session.commit()
    return {"message": f"Recommendation marked as '{status}'"}


@router.get("/{user_id}/summary")
async def savings_summary(user_id: int, session: AsyncSession = Depends(get_session)):
    """Get a high-level savings summary for the user."""
    # Get current policy
    policy_stmt = select(CurrentPolicy).where(CurrentPolicy.user_id == user_id)
    policy_result = await session.execute(policy_stmt)
    policies = policy_result.scalars().all()
    
    current_annual = sum(p.annual_premium for p in policies)
    
    # Get recommendations
    rec_stmt = select(SavingsRecommendation).where(
        SavingsRecommendation.user_id == user_id,
        SavingsRecommendation.status != "dismissed",
    )
    rec_result = await session.execute(rec_stmt)
    recs = rec_result.scalars().all()
    
    total_potential = sum(r.estimated_annual_savings for r in recs)
    
    # Get premium history
    history_stmt = (
        select(PremiumHistory)
        .where(PremiumHistory.user_id == user_id)
        .order_by(desc(PremiumHistory.recorded_date))
        .limit(12)
    )
    history_result = await session.execute(history_stmt)
    history = history_result.scalars().all()
    
    return {
        "current_annual_cost": round(current_annual, 2),
        "potential_savings": round(total_potential, 2),
        "optimized_annual_cost": round(current_annual - total_potential, 2),
        "savings_percentage": round((total_potential / current_annual * 100) if current_annual > 0 else 0, 1),
        "recommendations_count": len(recs),
        "top_recommendations": [
            {"title": r.title, "savings": r.estimated_annual_savings, "category": r.category}
            for r in sorted(recs, key=lambda x: x.estimated_annual_savings, reverse=True)[:5]
        ],
        "premium_history": [
            {"date": str(h.recorded_date), "carrier": h.carrier, "annual": h.annual_premium}
            for h in history
        ],
    }
