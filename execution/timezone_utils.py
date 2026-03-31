#!/usr/bin/env python3
"""
Timezone Utilities — Eastern Time (America/New_York) for all user-facing output

William is in Naples, Florida (Eastern Time). The EC2 server runs in UTC.
All cron jobs are scheduled in UTC but timed for correct Eastern execution.

Use these utilities for consistent timezone handling:
- now_eastern() → current Eastern datetime
- format_eastern(dt) → formatted Eastern time string
- utc_to_eastern(dt) → convert UTC datetime to Eastern
- EASTERN_TZ → the timezone object

Cron Schedule Reference (UTC → Eastern):
- 10:30 UTC = 6:30 AM ET (morning digest)
- 12:00 UTC = 8:00 AM ET (weekly lead gen)
- 13:00 UTC = 9:00 AM ET (daily loop)
- 01:00 UTC = 9:00 PM ET (evening digest)
"""

from datetime import datetime, timezone
from typing import Optional

try:
    from zoneinfo import ZoneInfo
    EASTERN_TZ = ZoneInfo("America/New_York")
except ImportError:
    # Python 3.8 fallback
    import pytz
    EASTERN_TZ = pytz.timezone("America/New_York")


def now_eastern() -> datetime:
    """Get current time in Eastern timezone (Naples, FL)."""
    return datetime.now(EASTERN_TZ)


def utc_to_eastern(dt: datetime) -> datetime:
    """Convert a UTC datetime to Eastern timezone.
    
    Args:
        dt: A datetime object (naive assumed UTC, or timezone-aware)
        
    Returns:
        Eastern timezone datetime
    """
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(EASTERN_TZ)


def format_eastern(
    dt: Optional[datetime] = None,
    fmt: str = "%Y-%m-%d %I:%M %p ET"
) -> str:
    """Format a datetime in Eastern timezone.
    
    Args:
        dt: Datetime to format (default: current time)
        fmt: strftime format string (default includes ET suffix)
        
    Returns:
        Formatted string in Eastern time
    """
    if dt is None:
        dt = now_eastern()
    elif dt.tzinfo is None or dt.tzinfo.utcoffset(dt) == timezone.utc.utcoffset(None):
        dt = utc_to_eastern(dt)
    return dt.strftime(fmt)


def format_time_only(dt: Optional[datetime] = None) -> str:
    """Format just the time portion in Eastern timezone.
    
    Args:
        dt: Datetime to format (default: current time)
        
    Returns:
        Time string like "09:15 AM ET"
    """
    return format_eastern(dt, "%I:%M %p ET")


def format_date_only(dt: Optional[datetime] = None) -> str:
    """Format just the date portion in Eastern timezone.
    
    Args:
        dt: Datetime to format (default: current time)
        
    Returns:
        Date string like "2026-03-30"
    """
    return format_eastern(dt, "%Y-%m-%d")


def today_eastern() -> str:
    """Get today's date in Eastern timezone as YYYY-MM-DD."""
    return format_date_only()


def is_business_hours_eastern() -> bool:
    """Check if current time is within business hours (9am-5pm ET, Mon-Fri)."""
    now = now_eastern()
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    return 9 <= now.hour < 17


# Convenience: print current time in both zones for debugging
if __name__ == "__main__":
    print(f"UTC Now:     {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Eastern Now: {format_eastern()}")
    print(f"Business hours: {is_business_hours_eastern()}")
