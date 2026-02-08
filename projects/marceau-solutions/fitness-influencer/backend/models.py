#!/usr/bin/env python3
"""
Database Models for Fitness Influencer AI v2.0

SQLAlchemy models for jobs, content, users, and analytics.

Models:
    - User: User accounts and settings
    - Job: Background processing jobs
    - Content: Video/image content metadata
    - Analytics: Performance metrics
    - ContentExport: Platform-specific exports
    - CaptionStyle: Custom caption styles
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from backend.database import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=True)
    name = Column(String(255), nullable=True)

    # Subscription tier: free, pro, enterprise
    tier = Column(String(20), default="free", nullable=False)

    # API usage tracking
    daily_video_jobs = Column(Integer, default=0)
    daily_caption_jobs = Column(Integer, default=0)
    daily_export_jobs = Column(Integer, default=0)
    last_reset_date = Column(DateTime, default=datetime.utcnow)

    # OAuth tokens (encrypted in production)
    google_token_json = Column(Text, nullable=True)

    # Settings
    settings = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    content = relationship("Content", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email or self.id}>"

    def reset_daily_quotas(self):
        """Reset daily quota counters."""
        self.daily_video_jobs = 0
        self.daily_caption_jobs = 0
        self.daily_export_jobs = 0
        self.last_reset_date = datetime.utcnow()

    @property
    def quota_limits(self) -> Dict[str, int]:
        """Get quota limits based on tier."""
        limits = {
            "free": {"video_jobs": 5, "caption_jobs": 10, "export_jobs": 20},
            "pro": {"video_jobs": 50, "caption_jobs": -1, "export_jobs": -1},  # -1 = unlimited
            "enterprise": {"video_jobs": -1, "caption_jobs": -1, "export_jobs": -1}
        }
        return limits.get(self.tier, limits["free"])


class Job(Base):
    """Background job model."""

    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    # Job type: video_caption, video_reframe, video_export, etc.
    job_type = Column(String(50), nullable=False, index=True)

    # Status: queued, processing, complete, failed, cancelled
    status = Column(String(20), default="queued", nullable=False, index=True)

    # Priority: 1 (highest) to 10 (lowest)
    priority = Column(Integer, default=5)

    # Progress: 0-100
    progress = Column(Integer, default=0)

    # Input parameters (JSON)
    params = Column(JSON, default=dict)

    # Result data (JSON)
    result = Column(JSON, nullable=True)

    # Error message if failed
    error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Processing time in seconds
    duration = Column(Float, nullable=True)

    # Relationships
    user = relationship("User", back_populates="jobs")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_jobs_user_status", "user_id", "status"),
        Index("ix_jobs_created_desc", "created_at", "status"),
    )

    def __repr__(self):
        return f"<Job {self.id[:8]} {self.job_type} {self.status}>"

    def mark_processing(self):
        """Mark job as processing."""
        self.status = "processing"
        self.started_at = datetime.utcnow()

    def mark_complete(self, result: Dict[str, Any]):
        """Mark job as complete."""
        self.status = "complete"
        self.progress = 100
        self.result = result
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()

    def mark_failed(self, error: str):
        """Mark job as failed."""
        self.status = "failed"
        self.error = error
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "job_type": self.job_type,
            "status": self.status,
            "priority": self.priority,
            "progress": self.progress,
            "params": self.params,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration
        }


class Content(Base):
    """Video/image content model."""

    __tablename__ = "content"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    # Content type: video, image, audio
    content_type = Column(String(20), nullable=False, index=True)

    # Title and description
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)

    # Original source URL
    original_url = Column(Text, nullable=True)

    # Processed URL (after editing)
    processed_url = Column(Text, nullable=True)

    # Thumbnail URL
    thumbnail_url = Column(Text, nullable=True)

    # Duration in seconds (for video/audio)
    duration = Column(Float, nullable=True)

    # Metadata: resolution, format, file size, etc.
    metadata = Column(JSON, default=dict)

    # AI-generated data: transcript, keywords, viral score
    ai_data = Column(JSON, default=dict)

    # Tags for categorization
    tags = Column(JSON, default=list)

    # Viral score (0-100)
    viral_score = Column(Integer, nullable=True)

    # Processing status
    status = Column(String(20), default="draft", index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="content")
    exports = relationship("ContentExport", back_populates="content", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="content", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Content {self.id[:8]} {self.content_type} {self.title or 'Untitled'}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content_type": self.content_type,
            "title": self.title,
            "description": self.description,
            "original_url": self.original_url,
            "processed_url": self.processed_url,
            "thumbnail_url": self.thumbnail_url,
            "duration": self.duration,
            "metadata": self.metadata,
            "ai_data": self.ai_data,
            "tags": self.tags,
            "viral_score": self.viral_score,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None
        }


class ContentExport(Base):
    """Platform-specific content export."""

    __tablename__ = "content_exports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    content_id = Column(String(36), ForeignKey("content.id"), nullable=False, index=True)

    # Platform: tiktok, instagram, youtube_shorts, linkedin, twitter
    platform = Column(String(30), nullable=False, index=True)

    # Export URL
    export_url = Column(Text, nullable=True)

    # Platform-specific metadata
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    hashtags = Column(JSON, default=list)

    # Export settings used
    settings = Column(JSON, default=dict)

    # Status: pending, complete, failed
    status = Column(String(20), default="pending")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    exported_at = Column(DateTime, nullable=True)

    # Relationships
    content = relationship("Content", back_populates="exports")

    __table_args__ = (
        Index("ix_exports_content_platform", "content_id", "platform"),
    )

    def __repr__(self):
        return f"<ContentExport {self.id[:8]} {self.platform}>"


class Analytics(Base):
    """Performance analytics for content."""

    __tablename__ = "analytics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    content_id = Column(String(36), ForeignKey("content.id"), nullable=False, index=True)

    # Platform
    platform = Column(String(30), nullable=False, index=True)

    # Engagement metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)

    # Retention curve (array of percentages at intervals)
    retention_curve = Column(JSON, nullable=True)

    # Average watch time in seconds
    avg_watch_time = Column(Float, nullable=True)

    # Engagement rate (likes + comments + shares) / views
    engagement_rate = Column(Float, nullable=True)

    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    content = relationship("Content", back_populates="analytics")

    __table_args__ = (
        Index("ix_analytics_content_platform", "content_id", "platform"),
        Index("ix_analytics_recorded", "recorded_at"),
    )

    def __repr__(self):
        return f"<Analytics {self.id[:8]} {self.platform} {self.views} views>"

    def calculate_engagement_rate(self):
        """Calculate and update engagement rate."""
        if self.views and self.views > 0:
            total_engagement = (self.likes or 0) + (self.comments or 0) + (self.shares or 0)
            self.engagement_rate = total_engagement / self.views
        else:
            self.engagement_rate = 0.0


class CaptionStyle(Base):
    """Custom caption style presets."""

    __tablename__ = "caption_styles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    # Style name
    name = Column(String(100), nullable=False)

    # Is this a system preset?
    is_system = Column(Boolean, default=False)

    # Style configuration
    font_family = Column(String(100), default="Arial")
    font_size = Column(Integer, default=48)
    font_color = Column(String(20), default="#FFFFFF")
    outline_color = Column(String(20), default="#000000")
    outline_width = Column(Integer, default=2)
    shadow_color = Column(String(20), nullable=True)
    shadow_offset = Column(Integer, default=0)
    background_color = Column(String(20), nullable=True)
    background_opacity = Column(Float, default=0.0)
    position = Column(String(20), default="bottom")  # top, center, bottom
    animation = Column(String(50), nullable=True)  # fade, slide, pop, typewriter

    # Full configuration as JSON (for complex styles)
    config = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CaptionStyle {self.name}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "is_system": self.is_system,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "font_color": self.font_color,
            "outline_color": self.outline_color,
            "outline_width": self.outline_width,
            "shadow_color": self.shadow_color,
            "shadow_offset": self.shadow_offset,
            "background_color": self.background_color,
            "background_opacity": self.background_opacity,
            "position": self.position,
            "animation": self.animation,
            "config": self.config
        }


# Default caption styles to seed
DEFAULT_CAPTION_STYLES = [
    {
        "name": "trending",
        "font_family": "Impact",
        "font_size": 56,
        "font_color": "#FFFFFF",
        "outline_color": "#000000",
        "outline_width": 3,
        "animation": "pop"
    },
    {
        "name": "glow",
        "font_family": "Arial Bold",
        "font_size": 52,
        "font_color": "#00FF88",
        "outline_color": "#000000",
        "outline_width": 2,
        "shadow_color": "#00FF88",
        "shadow_offset": 3,
        "animation": "fade"
    },
    {
        "name": "minimal",
        "font_family": "Helvetica",
        "font_size": 42,
        "font_color": "#FFFFFF",
        "outline_width": 0,
        "background_color": "#000000",
        "background_opacity": 0.6
    },
    {
        "name": "bold",
        "font_family": "Arial Black",
        "font_size": 64,
        "font_color": "#FFFF00",
        "outline_color": "#000000",
        "outline_width": 4,
        "animation": "slide"
    },
    {
        "name": "clean",
        "font_family": "Roboto",
        "font_size": 44,
        "font_color": "#FFFFFF",
        "outline_color": "#333333",
        "outline_width": 2
    },
    {
        "name": "neon",
        "font_family": "Arial Bold",
        "font_size": 50,
        "font_color": "#FF00FF",
        "outline_color": "#000000",
        "outline_width": 2,
        "shadow_color": "#FF00FF",
        "shadow_offset": 4,
        "animation": "fade"
    },
    {
        "name": "subtitle",
        "font_family": "Arial",
        "font_size": 36,
        "font_color": "#FFFFFF",
        "background_color": "#000000",
        "background_opacity": 0.8,
        "position": "bottom"
    },
    {
        "name": "fitness",
        "font_family": "Impact",
        "font_size": 54,
        "font_color": "#FF4500",
        "outline_color": "#FFFFFF",
        "outline_width": 3,
        "animation": "pop"
    },
    {
        "name": "professional",
        "font_family": "Georgia",
        "font_size": 40,
        "font_color": "#FFFFFF",
        "outline_color": "#1a1a1a",
        "outline_width": 2,
        "position": "bottom"
    },
    {
        "name": "dramatic",
        "font_family": "Arial Black",
        "font_size": 72,
        "font_color": "#FF0000",
        "outline_color": "#000000",
        "outline_width": 5,
        "animation": "slide"
    }
]
