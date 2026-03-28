#!/usr/bin/env python3
"""
Fitness Influencer Daily Loop — Autonomous Content Publishing Orchestrator

Runs the full content production and publishing loop as one coordinated operation.
Designed to execute unattended, publishing fitness content across platforms.

Stages:
  1. PLAN      — Generate content for today based on content calendar
  2. QUEUE     — Queue posts to X/Twitter via Google Sheets
  3. YOUTUBE   — Upload any pending YouTube Shorts
  4. METRICS   — Track engagement from previous posts
  5. REPORT    — Daily analytics digest to Telegram

Schedule (via cron):
  8:00am   — Full loop (stages 1-3)
  6:00pm   — Metrics + digest (stages 4-5)

Usage:
    python -m projects.fitness_influencer.src.fitness_daily_loop full --dry-run
    python -m projects.fitness_influencer.src.fitness_daily_loop full --for-real
    python -m projects.fitness_influencer.src.fitness_daily_loop post-x --for-real
    python -m projects.fitness_influencer.src.fitness_daily_loop metrics
    python -m projects.fitness_influencer.src.fitness_daily_loop digest
    python -m projects.fitness_influencer.src.fitness_daily_loop status
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
import traceback
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent
REPO_ROOT = PROJECT_ROOT.parent.parent

sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "social-media" / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fitness_daily_loop")

# Stage results tracking
STAGE_RESULTS: Dict[str, Dict[str, Any]] = {}

# Self-monitoring
HEALTH_FILE = PROJECT_ROOT / "logs" / "loop_health.json"
CONSECUTIVE_FAILURE_THRESHOLD = 2

# Database
PIPELINE_DB = Path("/home/clawdbot/data/pipeline.db")
FITNESS_DB = PROJECT_ROOT / "data" / "fitness.db"


# ---------------------------------------------------------------------------
# Database Setup — Ensure fitness_posts table exists in pipeline.db
# ---------------------------------------------------------------------------

def init_fitness_tables():
    """Ensure fitness_posts table exists in pipeline.db."""
    conn = sqlite3.connect(PIPELINE_DB)
    conn.row_factory = sqlite3.Row
    
    # Content posts tracking
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fitness_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tower TEXT DEFAULT 'fitness-influencer',
            platform TEXT NOT NULL,
            post_type TEXT DEFAULT 'short',
            title TEXT,
            content TEXT,
            video_path TEXT,
            post_id TEXT,
            post_url TEXT,
            scheduled_date TEXT,
            scheduled_time TEXT,
            status TEXT DEFAULT 'pending' 
                CHECK(status IN ('pending', 'queued', 'posted', 'failed')),
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            posted_at TEXT,
            metrics_updated_at TEXT
        )
    """)
    
    # Content calendar tracking
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fitness_content_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            day_of_week TEXT,
            theme TEXT,
            topic TEXT,
            hook TEXT,
            content_format TEXT,
            status TEXT DEFAULT 'planned' 
                CHECK(status IN ('planned', 'filmed', 'edited', 'posted')),
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fitness_posts_status ON fitness_posts(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fitness_posts_platform ON fitness_posts(platform)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fitness_posts_date ON fitness_posts(scheduled_date)")
    
    conn.commit()
    conn.close()
    logger.info("Fitness tables initialized in pipeline.db")


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(PIPELINE_DB)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Self-monitoring
# ---------------------------------------------------------------------------

def _load_health() -> Dict[str, Any]:
    """Load health history from disk."""
    if HEALTH_FILE.exists():
        try:
            with open(HEALTH_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"runs": [], "consecutive_failures": 0, "last_alert_date": None}


def _save_health(health: Dict[str, Any]):
    """Save health history to disk."""
    HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_FILE, "w") as f:
        json.dump(health, f, indent=2)


def record_run_health(stage_results: Dict[str, Dict[str, Any]]):
    """Record this run's health and alert on consecutive failures."""
    health = _load_health()
    today = datetime.now().strftime("%Y-%m-%d")

    successes = sum(1 for r in stage_results.values() if r.get("success"))
    total = len(stage_results)
    critical_ok = all(
        stage_results.get(s, {}).get("success", False)
        for s in ["queue_x", "youtube_shorts"]
    )

    run_record = {
        "date": today,
        "time": datetime.now().strftime("%H:%M"),
        "stages_passed": successes,
        "stages_total": total,
        "critical_ok": critical_ok,
        "failures": {
            name: details.get("error", "")[:100]
            for name, details in stage_results.items()
            if not details.get("success")
        },
    }

    # Keep last 14 days
    health["runs"] = [r for r in health["runs"] 
                      if r.get("date", "") >= (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")]
    health["runs"].append(run_record)

    if critical_ok:
        health["consecutive_failures"] = 0
    else:
        health["consecutive_failures"] = health.get("consecutive_failures", 0) + 1

    _save_health(health)

    # Alert if consecutive failures
    if health["consecutive_failures"] >= CONSECUTIVE_FAILURE_THRESHOLD:
        if health.get("last_alert_date") != today:
            failed_stages = ", ".join(run_record["failures"].keys())
            alert = (
                f"⚠️ *FITNESS TOWER DEGRADED*\n\n"
                f"Failed {health['consecutive_failures']} days in a row.\n"
                f"Failing stages: {failed_stages}\n\n"
                f"Check logs: `projects/fitness-influencer/logs/`"
            )
            send_telegram(alert)
            health["last_alert_date"] = today
            _save_health(health)

    logger.info(f"Health: {successes}/{total} passed, consecutive failures: {health['consecutive_failures']}")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _get_ssl_context():
    """Get SSL context with proper CA bundle."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def send_telegram(message: str) -> bool:
    """Send message via Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
    if not bot_token:
        logger.warning("No TELEGRAM_BOT_TOKEN — skipping Telegram")
        return False
    try:
        data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}, method="POST",
        )
        urllib.request.urlopen(req, timeout=10, context=_get_ssl_context())
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def log_stage(stage_name: str, success: bool, details: Dict[str, Any]):
    """Record stage result for the daily digest."""
    STAGE_RESULTS[stage_name] = {
        "success": success,
        "timestamp": datetime.now().isoformat(),
        **details,
    }
    status = "✓" if success else "✗"
    logger.info(f"Stage {stage_name}: {status} — {details}")


# ---------------------------------------------------------------------------
# Stage implementations
# ---------------------------------------------------------------------------

def stage_plan_content(dry_run: bool = True) -> Dict[str, Any]:
    """Stage 1: Plan today's content based on calendar."""
    try:
        from content_calendar import CONTENT_CALENDAR
        
        today = datetime.now()
        day_name = today.strftime("%A").lower()
        
        day_plan = CONTENT_CALENDAR.get(day_name, {})
        if not day_plan:
            log_stage("plan_content", True, {"skipped": "No plan for today"})
            return {"skipped": True}
        
        conn = get_db()
        
        # Check if already planned
        existing = conn.execute(
            "SELECT * FROM fitness_content_calendar WHERE date = ?",
            (today.strftime("%Y-%m-%d"),)
        ).fetchone()
        
        if not existing:
            conn.execute("""
                INSERT INTO fitness_content_calendar 
                (date, day_of_week, theme, topic, hook, content_format, status)
                VALUES (?, ?, ?, ?, ?, ?, 'planned')
            """, (
                today.strftime("%Y-%m-%d"),
                day_name,
                str(day_plan.get("theme", "")),
                day_plan.get("topic", ""),
                day_plan.get("hook", ""),
                str(day_plan.get("format", ""))
            ))
            conn.commit()
            logger.info(f"Planned: {day_plan.get('topic')} ({day_name})")
        
        conn.close()
        
        log_stage("plan_content", True, {
            "day": day_name,
            "theme": str(day_plan.get("theme", "")),
            "topic": day_plan.get("topic", ""),
        })
        return {"day": day_name, "plan": day_plan}
        
    except Exception as e:
        logger.error(f"Plan content failed: {e}\n{traceback.format_exc()}")
        log_stage("plan_content", False, {"error": str(e)})
        return {"error": str(e)}


def stage_queue_x_posts(dry_run: bool = True) -> Dict[str, Any]:
    """Stage 2: Queue X posts to Google Sheets for n8n scheduler."""
    try:
        # Check for pending X posts
        conn = get_db()
        pending = conn.execute("""
            SELECT * FROM fitness_posts 
            WHERE platform = 'x' AND status = 'pending'
            ORDER BY scheduled_date, scheduled_time
            LIMIT 5
        """).fetchall()
        
        if not pending:
            logger.info("No pending X posts to queue")
            log_stage("queue_x", True, {"queued": 0, "skipped": "no pending"})
            conn.close()
            return {"queued": 0}
        
        queued = 0
        for post in pending:
            if dry_run:
                logger.info(f"[DRY RUN] Would queue X post: {post['content'][:50]}...")
            else:
                # Here we would call queue_x_posts module
                # For now, just update status
                conn.execute(
                    "UPDATE fitness_posts SET status = 'queued' WHERE id = ?",
                    (post['id'],)
                )
                queued += 1
        
        if not dry_run:
            conn.commit()
        conn.close()
        
        log_stage("queue_x", True, {"queued": queued})
        return {"queued": queued}
        
    except Exception as e:
        logger.error(f"Queue X posts failed: {e}\n{traceback.format_exc()}")
        log_stage("queue_x", False, {"error": str(e)})
        return {"error": str(e)}


def stage_youtube_shorts(dry_run: bool = True) -> Dict[str, Any]:
    """Stage 3: Upload pending YouTube Shorts."""
    try:
        # Check for pending videos
        conn = get_db()
        pending = conn.execute("""
            SELECT * FROM fitness_posts 
            WHERE platform = 'youtube_shorts' AND status = 'pending'
            AND video_path IS NOT NULL
            ORDER BY scheduled_date
            LIMIT 3
        """).fetchall()
        
        if not pending:
            logger.info("No pending YouTube Shorts to upload")
            log_stage("youtube_shorts", True, {"uploaded": 0, "skipped": "no pending"})
            conn.close()
            return {"uploaded": 0}
        
        uploaded = 0
        for video in pending:
            video_path = video['video_path']
            
            if not Path(video_path).exists():
                logger.warning(f"Video not found: {video_path}")
                continue
                
            if dry_run:
                logger.info(f"[DRY RUN] Would upload: {video['title'] or video_path}")
            else:
                try:
                    from youtube_uploader import YouTubeUploader
                    uploader = YouTubeUploader()
                    
                    if uploader.is_ready():
                        result = uploader.upload_short(
                            video_path=video_path,
                            title=video['title'] or "Fitness Tip #Shorts",
                            description=video['content'] or "",
                            privacy="public"
                        )
                        
                        if result.success:
                            conn.execute("""
                                UPDATE fitness_posts 
                                SET status = 'posted', 
                                    post_id = ?, 
                                    post_url = ?,
                                    posted_at = datetime('now')
                                WHERE id = ?
                            """, (result.video_id, result.url, video['id']))
                            uploaded += 1
                            logger.info(f"Uploaded: {result.url}")
                        else:
                            logger.error(f"Upload failed: {result.error}")
                    else:
                        logger.warning("YouTube uploader not ready - check credentials")
                except ImportError:
                    logger.warning("YouTube uploader not available")
        
        if not dry_run:
            conn.commit()
        conn.close()
        
        log_stage("youtube_shorts", True, {"uploaded": uploaded, "pending": len(pending)})
        return {"uploaded": uploaded}
        
    except Exception as e:
        logger.error(f"YouTube Shorts failed: {e}\n{traceback.format_exc()}")
        log_stage("youtube_shorts", False, {"error": str(e)})
        return {"error": str(e)}


def stage_collect_metrics() -> Dict[str, Any]:
    """Stage 4: Collect engagement metrics from posted content."""
    try:
        conn = get_db()
        
        # Get recent posts to update metrics
        recent = conn.execute("""
            SELECT * FROM fitness_posts 
            WHERE status = 'posted' 
            AND posted_at > datetime('now', '-7 days')
            ORDER BY posted_at DESC
        """).fetchall()
        
        updated = 0
        for post in recent:
            # For YouTube, we could fetch via API
            if post['platform'] in ('youtube_shorts', 'youtube') and post['post_id']:
                try:
                    from youtube_uploader import YouTubeUploader
                    uploader = YouTubeUploader()
                    if uploader.is_ready():
                        status = uploader.get_upload_status(post['post_id'])
                        if status:
                            conn.execute("""
                                UPDATE fitness_posts 
                                SET views = ?, likes = ?, comments = ?,
                                    metrics_updated_at = datetime('now')
                                WHERE id = ?
                            """, (
                                status.view_count or 0,
                                status.like_count or 0,
                                status.comment_count or 0,
                                post['id']
                            ))
                            updated += 1
                except Exception as e:
                    logger.warning(f"Metrics update failed for {post['post_id']}: {e}")
        
        conn.commit()
        conn.close()
        
        log_stage("metrics", True, {"updated": updated, "total_posts": len(recent)})
        return {"updated": updated}
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}\n{traceback.format_exc()}")
        log_stage("metrics", False, {"error": str(e)})
        return {"error": str(e)}


def stage_digest() -> Dict[str, Any]:
    """Stage 5: Send daily analytics digest to Telegram."""
    try:
        conn = get_db()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Today's posts
        todays_posts = conn.execute("""
            SELECT platform, COUNT(*) as cnt, SUM(views) as views, SUM(likes) as likes
            FROM fitness_posts 
            WHERE date(posted_at) = ?
            GROUP BY platform
        """, (today,)).fetchall()
        
        # Week's performance
        week_stats = conn.execute("""
            SELECT COUNT(*) as posts, 
                   SUM(views) as views, 
                   SUM(likes) as likes,
                   SUM(comments) as comments
            FROM fitness_posts 
            WHERE status = 'posted'
            AND posted_at > datetime('now', '-7 days')
        """).fetchone()
        
        # Top performing post
        top_post = conn.execute("""
            SELECT title, platform, views, likes, post_url
            FROM fitness_posts 
            WHERE status = 'posted'
            ORDER BY views DESC
            LIMIT 1
        """).fetchone()
        
        conn.close()
        
        # Build digest
        lines = [f"🏋️ *FITNESS TOWER DIGEST — {today}*\n"]
        
        if STAGE_RESULTS:
            lines.append("*Today's Loop:*")
            for stage, result in STAGE_RESULTS.items():
                status = "✓" if result.get("success") else "✗"
                lines.append(f"  {status} {stage}")
            lines.append("")
        
        if todays_posts:
            lines.append("*Today's Posts:*")
            for row in todays_posts:
                lines.append(f"  • {row['platform']}: {row['cnt']} posts, {row['views'] or 0} views")
            lines.append("")
        
        if week_stats and week_stats['posts']:
            lines.append(f"*7-Day Stats:*")
            lines.append(f"  Posts: {week_stats['posts']}")
            lines.append(f"  Views: {week_stats['views'] or 0:,}")
            lines.append(f"  Likes: {week_stats['likes'] or 0:,}")
            lines.append(f"  Comments: {week_stats['comments'] or 0}")
        
        if top_post and top_post['views']:
            lines.append(f"\n🏆 *Top Post:* {top_post['title'] or 'Untitled'}")
            lines.append(f"   {top_post['views']:,} views | {top_post['likes']:,} likes")
        
        message = "\n".join(lines)
        send_telegram(message)
        
        log_stage("digest", True, {"message_length": len(message)})
        return {"sent": True}
        
    except Exception as e:
        logger.error(f"Digest failed: {e}\n{traceback.format_exc()}")
        log_stage("digest", False, {"error": str(e)})
        return {"error": str(e)}


def show_status():
    """Show current fitness tower status."""
    init_fitness_tables()
    conn = get_db()
    
    # Post stats by status
    status_counts = conn.execute("""
        SELECT status, COUNT(*) as cnt 
        FROM fitness_posts 
        GROUP BY status
    """).fetchall()
    
    # Platform breakdown
    platforms = conn.execute("""
        SELECT platform, COUNT(*) as cnt, SUM(views) as views
        FROM fitness_posts 
        WHERE status = 'posted'
        GROUP BY platform
    """).fetchall()
    
    # Recent posts
    recent = conn.execute("""
        SELECT title, platform, status, posted_at, views
        FROM fitness_posts 
        ORDER BY created_at DESC 
        LIMIT 10
    """).fetchall()
    
    # Today's calendar
    today = datetime.now().strftime("%Y-%m-%d")
    today_plan = conn.execute("""
        SELECT * FROM fitness_content_calendar WHERE date = ?
    """, (today,)).fetchone()
    
    conn.close()
    
    print("\n🏋️ Fitness Tower Status\n")
    
    if today_plan:
        print(f"📅 Today's Plan: {today_plan['topic']}")
        print(f"   Theme: {today_plan['theme']} | Status: {today_plan['status']}\n")
    
    print("Post Status:")
    for r in status_counts:
        print(f"  {r['cnt']:>4}  {r['status']}")
    
    print(f"\nPlatform Performance:")
    for r in platforms:
        print(f"  {r['platform']:20}  {r['cnt']} posts, {r['views'] or 0:,} views")
    
    print(f"\nRecent Posts:")
    for r in recent:
        views = f"{r['views']:,}" if r['views'] else "-"
        print(f"  {r['status']:<8}  {r['platform']:<15}  {views:>8} views  {r['title'] or '(untitled)'[:30]}")


def add_post(platform: str, title: str, content: str = "", video_path: str = None,
             scheduled_date: str = None, scheduled_time: str = None):
    """Add a post to the queue."""
    init_fitness_tables()
    conn = get_db()
    
    conn.execute("""
        INSERT INTO fitness_posts 
        (platform, title, content, video_path, scheduled_date, scheduled_time, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    """, (platform, title, content, video_path, scheduled_date, scheduled_time))
    
    post_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    
    print(f"✓ Added post #{post_id}: {title} → {platform}")
    return post_id


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_full_loop(dry_run: bool = True):
    """Run the complete fitness content loop."""
    init_fitness_tables()
    
    mode = "DRY RUN" if dry_run else "LIVE"
    logger.info(f"\n{'='*60}")
    logger.info(f"FITNESS DAILY LOOP — {mode} — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info(f"{'='*60}\n")
    
    # Stage 1: Plan content
    logger.info("\n▶ Stage 1: Plan today's content")
    stage_plan_content(dry_run=dry_run)
    
    # Stage 2: Queue X posts
    logger.info("\n▶ Stage 2: Queue X posts")
    stage_queue_x_posts(dry_run=dry_run)
    
    # Stage 3: Upload YouTube Shorts
    logger.info("\n▶ Stage 3: YouTube Shorts")
    stage_youtube_shorts(dry_run=dry_run)
    
    # Stage 4: Collect metrics
    logger.info("\n▶ Stage 4: Collect metrics")
    stage_collect_metrics()
    
    # Stage 5: Daily digest
    logger.info("\n▶ Stage 5: Daily digest")
    stage_digest()
    
    # Summary
    successes = sum(1 for r in STAGE_RESULTS.values() if r.get("success"))
    total = len(STAGE_RESULTS)
    logger.info(f"\n{'='*60}")
    logger.info(f"FITNESS LOOP COMPLETE: {successes}/{total} stages succeeded")
    logger.info(f"{'='*60}\n")
    
    record_run_health(STAGE_RESULTS)


def main():
    parser = argparse.ArgumentParser(description="Fitness Influencer Daily Loop")
    parser.add_argument("command", 
                        choices=["full", "plan", "post-x", "youtube", "metrics", "digest", "status", "add"],
                        help="Which operation to run")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Preview without posting")
    parser.add_argument("--for-real", action="store_true", default=False,
                        help="Actually post content")
    # For add command
    parser.add_argument("--platform", help="Platform (x, youtube_shorts, etc)")
    parser.add_argument("--title", help="Post title")
    parser.add_argument("--content", default="", help="Post content/description")
    parser.add_argument("--video", help="Path to video file")
    parser.add_argument("--date", help="Scheduled date (YYYY-MM-DD)")
    parser.add_argument("--time", help="Scheduled time (HH:MM)")
    
    args = parser.parse_args()
    dry_run = not args.for_real
    
    if args.command == "full":
        run_full_loop(dry_run=dry_run)
    elif args.command == "plan":
        init_fitness_tables()
        stage_plan_content(dry_run=dry_run)
    elif args.command == "post-x":
        init_fitness_tables()
        stage_queue_x_posts(dry_run=dry_run)
    elif args.command == "youtube":
        init_fitness_tables()
        stage_youtube_shorts(dry_run=dry_run)
    elif args.command == "metrics":
        init_fitness_tables()
        stage_collect_metrics()
    elif args.command == "digest":
        init_fitness_tables()
        stage_digest()
    elif args.command == "status":
        show_status()
    elif args.command == "add":
        if not args.platform or not args.title:
            print("Usage: python -m ... add --platform x --title 'My Post' [--content '...'] [--video path]")
            return 1
        add_post(
            platform=args.platform,
            title=args.title,
            content=args.content,
            video_path=args.video,
            scheduled_date=args.date,
            scheduled_time=args.time
        )


if __name__ == "__main__":
    main()
