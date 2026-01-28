"""Application configuration."""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """App settings loaded from environment or .env file."""
    
    # App
    app_name: str = "AutoInsure Saver"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite+aiosqlite:///data/insurance.db"
    
    # Scraper
    scrape_interval_hours: int = 12  # How often to scan for promos
    scrape_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Notifications
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    savings_alert_threshold: float = 200.0  # Annual savings threshold for alerts
    
    # Renewal reminders (days before renewal)
    renewal_reminder_days: list[int] = [60, 45, 30, 14, 7]
    
    class Config:
        env_file = ".env"
        env_prefix = "INSURE_"


settings = Settings()

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "src" / "templates"
STATIC_DIR = BASE_DIR / "src" / "static"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
