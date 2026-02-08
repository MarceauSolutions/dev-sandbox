"""Initial schema for Fitness Influencer AI v2.0

Revision ID: 001
Revises:
Create Date: 2026-02-07

Creates tables:
- users: User accounts and settings
- jobs: Background processing jobs
- content: Video/image content metadata
- content_exports: Platform-specific exports
- analytics: Performance metrics
- caption_styles: Custom caption presets
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('tier', sa.String(20), nullable=False, default='free'),
        sa.Column('daily_video_jobs', sa.Integer, default=0),
        sa.Column('daily_caption_jobs', sa.Integer, default=0),
        sa.Column('daily_export_jobs', sa.Integer, default=0),
        sa.Column('last_reset_date', sa.DateTime),
        sa.Column('google_token_json', sa.Text, nullable=True),
        sa.Column('settings', sa.JSON, default=dict),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='queued'),
        sa.Column('priority', sa.Integer, default=5),
        sa.Column('progress', sa.Integer, default=0),
        sa.Column('params', sa.JSON, default=dict),
        sa.Column('result', sa.JSON, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('duration', sa.Float, nullable=True),
    )
    op.create_index('ix_jobs_user_id', 'jobs', ['user_id'])
    op.create_index('ix_jobs_job_type', 'jobs', ['job_type'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    op.create_index('ix_jobs_created_at', 'jobs', ['created_at'])
    op.create_index('ix_jobs_user_status', 'jobs', ['user_id', 'status'])
    op.create_index('ix_jobs_created_desc', 'jobs', ['created_at', 'status'])

    # Content table
    op.create_table(
        'content',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('content_type', sa.String(20), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('original_url', sa.Text, nullable=True),
        sa.Column('processed_url', sa.Text, nullable=True),
        sa.Column('thumbnail_url', sa.Text, nullable=True),
        sa.Column('duration', sa.Float, nullable=True),
        sa.Column('metadata', sa.JSON, default=dict),
        sa.Column('ai_data', sa.JSON, default=dict),
        sa.Column('tags', sa.JSON, default=list),
        sa.Column('viral_score', sa.Integer, nullable=True),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('published_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_content_user_id', 'content', ['user_id'])
    op.create_index('ix_content_content_type', 'content', ['content_type'])
    op.create_index('ix_content_status', 'content', ['status'])
    op.create_index('ix_content_created_at', 'content', ['created_at'])

    # Content exports table
    op.create_table(
        'content_exports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('content_id', sa.String(36), sa.ForeignKey('content.id'), nullable=False),
        sa.Column('platform', sa.String(30), nullable=False),
        sa.Column('export_url', sa.Text, nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('hashtags', sa.JSON, default=list),
        sa.Column('settings', sa.JSON, default=dict),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('exported_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_exports_content_id', 'content_exports', ['content_id'])
    op.create_index('ix_exports_platform', 'content_exports', ['platform'])
    op.create_index('ix_exports_content_platform', 'content_exports', ['content_id', 'platform'])

    # Analytics table
    op.create_table(
        'analytics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('content_id', sa.String(36), sa.ForeignKey('content.id'), nullable=False),
        sa.Column('platform', sa.String(30), nullable=False),
        sa.Column('views', sa.Integer, default=0),
        sa.Column('likes', sa.Integer, default=0),
        sa.Column('comments', sa.Integer, default=0),
        sa.Column('shares', sa.Integer, default=0),
        sa.Column('saves', sa.Integer, default=0),
        sa.Column('retention_curve', sa.JSON, nullable=True),
        sa.Column('avg_watch_time', sa.Float, nullable=True),
        sa.Column('engagement_rate', sa.Float, nullable=True),
        sa.Column('recorded_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_analytics_content_id', 'analytics', ['content_id'])
    op.create_index('ix_analytics_platform', 'analytics', ['platform'])
    op.create_index('ix_analytics_content_platform', 'analytics', ['content_id', 'platform'])
    op.create_index('ix_analytics_recorded_at', 'analytics', ['recorded_at'])

    # Caption styles table
    op.create_table(
        'caption_styles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('font_family', sa.String(100), default='Arial'),
        sa.Column('font_size', sa.Integer, default=48),
        sa.Column('font_color', sa.String(20), default='#FFFFFF'),
        sa.Column('outline_color', sa.String(20), default='#000000'),
        sa.Column('outline_width', sa.Integer, default=2),
        sa.Column('shadow_color', sa.String(20), nullable=True),
        sa.Column('shadow_offset', sa.Integer, default=0),
        sa.Column('background_color', sa.String(20), nullable=True),
        sa.Column('background_opacity', sa.Float, default=0.0),
        sa.Column('position', sa.String(20), default='bottom'),
        sa.Column('animation', sa.String(50), nullable=True),
        sa.Column('config', sa.JSON, default=dict),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )
    op.create_index('ix_caption_styles_user_id', 'caption_styles', ['user_id'])
    op.create_index('ix_caption_styles_name', 'caption_styles', ['name'])


def downgrade() -> None:
    op.drop_table('caption_styles')
    op.drop_table('analytics')
    op.drop_table('content_exports')
    op.drop_table('content')
    op.drop_table('jobs')
    op.drop_table('users')
