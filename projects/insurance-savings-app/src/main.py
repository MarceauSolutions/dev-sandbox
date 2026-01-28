"""AutoInsure Saver — Main application entry point."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config import settings, TEMPLATES_DIR, STATIC_DIR
from src.models import init_db
from src.api.profile import router as profile_router
from src.api.deals import router as deals_router
from src.api.savings import router as savings_router
from src.api.dashboard import router as dashboard_router
from src.scrapers.promo_scanner import run_all_scrapers
from src.calculators.savings_engine import run_savings_analysis
from src.notifications.notifier import check_and_notify

# Scheduler
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Initialize database
    await init_db()
    
    # Schedule promo scanning (every 12 hours)
    scheduler.add_job(
        run_all_scrapers,
        "interval",
        hours=settings.scrape_interval_hours,
        id="promo_scanner",
        name="Insurance Promo Scanner",
    )
    
    # Schedule savings analysis (daily at 8 AM UTC)
    scheduler.add_job(
        run_savings_analysis,
        "cron",
        hour=8,
        id="savings_analysis",
        name="Savings Analysis Engine",
    )
    
    # Schedule notification check (every 6 hours)
    scheduler.add_job(
        check_and_notify,
        "interval",
        hours=6,
        id="notification_check",
        name="Notification Check",
    )
    
    scheduler.start()
    
    yield
    
    scheduler.shutdown()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Mount static files
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include routers
app.include_router(profile_router, prefix="/api/profile", tags=["Profile"])
app.include_router(deals_router, prefix="/api/deals", tags=["Deals"])
app.include_router(savings_router, prefix="/api/savings", tags=["Savings"])
app.include_router(dashboard_router, tags=["Dashboard"])


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "scheduler_running": scheduler.running,
        "jobs": [
            {"id": job.id, "name": job.name, "next_run": str(job.next_run_time)}
            for job in scheduler.get_jobs()
        ],
    }
