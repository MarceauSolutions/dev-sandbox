"""Notification engine — sends alerts via Telegram when savings opportunities arise."""
import logging
from datetime import date, timedelta
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from src.models.base import async_session
from src.models.user import UserProfile, CurrentPolicy
from src.models.deals import InsuranceDeal
from src.models.savings import SavingsRecommendation
from src.config import settings

logger = logging.getLogger(__name__)


async def check_and_notify():
    """Main notification check — runs on schedule."""
    logger.info("Running notification check...")
    
    async with async_session() as session:
        # Get all users with telegram chat IDs
        stmt = (
            select(UserProfile)
            .where(UserProfile.telegram_chat_id.isnot(None))
            .options(selectinload(UserProfile.policies))
        )
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        for user in users:
            await _check_renewal_reminders(session, user)
            await _check_new_deals(session, user)
            await _check_savings_threshold(session, user)


async def _check_renewal_reminders(session, user: UserProfile):
    """Send renewal countdown notifications."""
    today = date.today()
    
    for policy in user.policies:
        if not policy.renewal_date:
            continue
        
        days_until = (policy.renewal_date - today).days
        
        if days_until in settings.renewal_reminder_days:
            message = (
                f"🔔 **Insurance Renewal Reminder**\n\n"
                f"Your {policy.carrier} policy renews in **{days_until} days** "
                f"(on {policy.renewal_date.strftime('%B %d, %Y')}).\n\n"
                f"💰 Current premium: ${policy.annual_premium:,.2f}/year "
                f"(${policy.monthly_premium:,.2f}/month)\n\n"
            )
            
            if days_until >= 30:
                message += (
                    "⏰ **Now is the time to shop around!**\n"
                    "Get quotes from competing carriers to negotiate "
                    "a better rate or switch if there's a deal.\n\n"
                    "Check the dashboard for current promos and savings tips."
                )
            elif days_until <= 14:
                message += (
                    "⚠️ **Renewal is close!** If you've found a better deal, "
                    "now is the time to switch. Make sure there's no gap in coverage."
                )
            
            await _send_telegram(user.telegram_chat_id, message)
            logger.info(f"Sent {days_until}-day renewal reminder to user {user.id}")


async def _check_new_deals(session, user: UserProfile):
    """Check for new deals that match user's profile."""
    # Find deals scraped in the last notification cycle (6 hours)
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(hours=6)
    
    stmt = select(InsuranceDeal).where(
        and_(
            InsuranceDeal.scraped_at >= cutoff,
            InsuranceDeal.is_active == True,
        )
    )
    result = await session.execute(stmt)
    new_deals = result.scalars().all()
    
    if not new_deals:
        return
    
    # Get user's current carriers to highlight competitor deals
    current_carriers = {p.carrier.lower() for p in user.policies}
    
    # Filter for relevant deals (competitor deals with significant savings)
    relevant_deals = [
        d for d in new_deals
        if (d.carrier.lower() not in current_carriers  # Different carrier
            and (d.estimated_savings_pct or 0) >= 5)    # At least 5% savings
    ]
    
    if not relevant_deals:
        return
    
    message = f"🆕 **New Insurance Deals Found!**\n\n"
    
    for deal in relevant_deals[:5]:  # Max 5 deals per notification
        savings_str = ""
        if deal.estimated_savings_pct:
            savings_str = f"~{deal.estimated_savings_pct:.0f}% savings"
        if deal.estimated_savings_amt:
            savings_str = f"~${deal.estimated_savings_amt:,.0f} savings"
        
        message += (
            f"**{deal.carrier}** — {deal.title}\n"
            f"  {deal.description[:100]}{'...' if len(deal.description) > 100 else ''}\n"
        )
        if savings_str:
            message += f"  💰 {savings_str}\n"
        if deal.url:
            message += f"  🔗 {deal.url}\n"
        message += "\n"
    
    if len(relevant_deals) > 5:
        message += f"...and {len(relevant_deals) - 5} more deals. Check the dashboard!"
    
    await _send_telegram(user.telegram_chat_id, message)
    logger.info(f"Sent {len(relevant_deals)} new deal alerts to user {user.id}")


async def _check_savings_threshold(session, user: UserProfile):
    """Alert when total potential savings exceeds threshold."""
    stmt = select(SavingsRecommendation).where(
        and_(
            SavingsRecommendation.user_id == user.id,
            SavingsRecommendation.status == "new",
        )
    )
    result = await session.execute(stmt)
    recs = result.scalars().all()
    
    total_savings = sum(r.estimated_annual_savings for r in recs)
    
    if total_savings >= settings.savings_alert_threshold:
        # Get current total premium
        current_annual = sum(p.annual_premium for p in user.policies)
        
        message = (
            f"💰 **Savings Alert!**\n\n"
            f"You could save an estimated **${total_savings:,.2f}/year** "
            f"on your car insurance!\n\n"
            f"Current annual cost: ${current_annual:,.2f}\n"
            f"Potential optimized cost: ${current_annual - total_savings:,.2f}\n\n"
            f"**Top recommendations:**\n"
        )
        
        top_recs = sorted(recs, key=lambda r: r.estimated_annual_savings, reverse=True)[:3]
        for rec in top_recs:
            message += f"• {rec.title} — save ~${rec.estimated_annual_savings:,.0f}/yr\n"
        
        message += "\nCheck the dashboard for full details and action steps."
        
        await _send_telegram(user.telegram_chat_id, message)
        logger.info(f"Sent savings threshold alert to user {user.id}: ${total_savings:.2f}")


async def _send_telegram(chat_id: str, message: str):
    """Send a Telegram message. Uses Clawdbot's notification system if available."""
    import httpx
    
    if not settings.telegram_bot_token:
        logger.warning("Telegram bot token not configured, skipping notification")
        return
    
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")


async def send_monthly_report(user_id: int):
    """Generate and send a monthly savings report."""
    async with async_session() as session:
        user = await session.get(UserProfile, user_id)
        if not user or not user.telegram_chat_id:
            return
        
        stmt = select(SavingsRecommendation).where(
            SavingsRecommendation.user_id == user_id,
        )
        result = await session.execute(stmt)
        recs = result.scalars().all()
        
        applied = [r for r in recs if r.status == "applied"]
        pending = [r for r in recs if r.status in ("new", "viewed")]
        
        total_saved = sum(r.estimated_annual_savings for r in applied)
        total_pending = sum(r.estimated_annual_savings for r in pending)
        
        message = (
            f"📊 **Monthly Insurance Savings Report**\n\n"
            f"✅ Applied savings: **${total_saved:,.2f}/year**\n"
            f"⏳ Pending opportunities: **${total_pending:,.2f}/year**\n"
            f"📋 {len(applied)} actions taken, {len(pending)} remaining\n\n"
        )
        
        if pending:
            message += "**Highest pending savings:**\n"
            for rec in sorted(pending, key=lambda r: r.estimated_annual_savings, reverse=True)[:3]:
                message += f"• {rec.title} — ${rec.estimated_annual_savings:,.0f}/yr\n"
        
        await _send_telegram(user.telegram_chat_id, message)
