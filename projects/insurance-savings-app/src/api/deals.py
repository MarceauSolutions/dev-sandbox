"""Insurance deals API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import get_session
from src.models.deals import InsuranceDeal
from src.scrapers.promo_scanner import run_all_scrapers

router = APIRouter()

CARRIERS = [
    "GEICO", "Progressive", "State Farm", "Allstate", "USAA",
    "Liberty Mutual", "Farmers", "Nationwide", "Travelers", "American Family",
]


@router.get("/")
async def list_deals(
    carrier: str | None = None,
    deal_type: str | None = None,
    active_only: bool = True,
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session),
):
    """List insurance deals with optional filters."""
    stmt = select(InsuranceDeal).order_by(desc(InsuranceDeal.scraped_at))
    
    if carrier:
        stmt = stmt.where(InsuranceDeal.carrier == carrier)
    if deal_type:
        stmt = stmt.where(InsuranceDeal.deal_type == deal_type)
    if active_only:
        stmt = stmt.where(InsuranceDeal.is_active == True)
    
    stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    deals = result.scalars().all()
    
    return {
        "count": len(deals),
        "deals": [
            {
                "id": d.id,
                "carrier": d.carrier,
                "deal_type": d.deal_type,
                "title": d.title,
                "description": d.description,
                "estimated_savings_pct": d.estimated_savings_pct,
                "estimated_savings_amt": d.estimated_savings_amt,
                "promo_code": d.promo_code,
                "start_date": str(d.start_date) if d.start_date else None,
                "end_date": str(d.end_date) if d.end_date else None,
                "url": d.url,
                "requirements": d.requirements,
                "scraped_at": str(d.scraped_at),
                "is_active": d.is_active,
            }
            for d in deals
        ],
    }


@router.get("/carriers")
async def list_carriers():
    """List supported insurance carriers."""
    return {"carriers": CARRIERS}


@router.post("/scan")
async def trigger_scan():
    """Manually trigger a promo scan."""
    try:
        new_count = await run_all_scrapers()
        return {"message": f"Scan complete. Found {new_count} new deals.", "new_deals": new_count}
    except Exception as e:
        return {"message": f"Scan encountered errors: {str(e)}", "error": True}


@router.get("/stats")
async def deal_stats(session: AsyncSession = Depends(get_session)):
    """Get deal statistics by carrier."""
    stmt = select(InsuranceDeal).where(InsuranceDeal.is_active == True)
    result = await session.execute(stmt)
    deals = result.scalars().all()
    
    stats = {}
    for d in deals:
        if d.carrier not in stats:
            stats[d.carrier] = {"total": 0, "types": {}}
        stats[d.carrier]["total"] += 1
        deal_type = d.deal_type or "unknown"
        stats[d.carrier]["types"][deal_type] = stats[d.carrier]["types"].get(deal_type, 0) + 1
    
    return {"active_deals": len(deals), "by_carrier": stats}
