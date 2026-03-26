#!/usr/bin/env python3
"""
Database Configuration for Fitness Influencer AI v2.0

SQLAlchemy setup with SQLite (development) and PostgreSQL (production) support.
Uses Alembic for schema migrations.

Usage:
    from backend.database import get_db, engine, SessionLocal

    # Dependency injection for FastAPI
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Direct usage
    with SessionLocal() as db:
        user = db.query(User).first()
"""

import os
import logging
from pathlib import Path
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()

# Database URL configuration
# SQLite for development, PostgreSQL for production
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{Path(__file__).parent.parent / 'data' / 'fitness.db'}"
)

# Convert postgres:// to postgresql:// for SQLAlchemy 2.0
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Determine if using SQLite
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Create data directory for SQLite
if IS_SQLITE:
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

# Engine configuration
if IS_SQLITE:
    # SQLite-specific settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true"
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL settings
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true"
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints.

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for non-FastAPI usage.

    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.

    Only use in development. In production, use Alembic migrations.
    """
    # Import models to ensure they're registered
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized: {DATABASE_URL}")


def drop_all():
    """
    Drop all tables. USE WITH CAUTION.

    Only for development/testing.
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")


def check_connection() -> bool:
    """
    Check if database connection is working.

    Returns True if connection successful.
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1" if not IS_SQLITE else "SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


# Database info for status endpoint
def get_db_info() -> dict:
    """Get database configuration info."""
    return {
        "type": "sqlite" if IS_SQLITE else "postgresql",
        "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
        "connected": check_connection()
    }
