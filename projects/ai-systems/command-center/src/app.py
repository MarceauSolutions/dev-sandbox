#!/usr/bin/env python3
"""
Marceau Accountability Engine — Production Dashboard

90-day execution tracker with real-time metrics, streak tracking,
goal progress visualization, and health-aware coaching.

http://127.0.0.1:8780 (local) | https://accountability.marceausolutions.com (production)
"""

import os
import json
import httpx
from datetime import datetime, date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from .data import get_dashboard_data, get_context, TARGETS, GOALS, get_current_time_block
from .ui import render_dashboard, render_landing, render_sprint

PROJECT_ROOT = Path(__file__).resolve().parents[4]
TASKS_FILE = PROJECT_ROOT / "projects/marceau-solutions/fitness/tools/fitness-influencer/data/tenants/wmarceau/tasks.json"
TRACKING_DIR = PROJECT_ROOT / "projects/lead-generation/output"
SESSION_CLOSE_LOG = PROJECT_ROOT / "output" / "session_close_log.json"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = "5692454753"

app = FastAPI(title="Marceau Accountability Engine", version="2.0.0")
PORT = int(os.getenv("ACCOUNTABILITY_PORT", "8780"))


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    try:
        data = get_dashboard_data()
        time_block = get_current_time_block()
        return render_dashboard(data, time_block=time_block)
    except Exception as e:
        return render_dashboard(None, error=str(e))


@app.get("/sprint", response_class=HTMLResponse)
async def sprint_hub():
    try:
        tasks = json.loads(TASKS_FILE.read_text()) if TASKS_FILE.exists() else {"tasks": []}
        # Load outreach stats from tracking files
        outreach_stats = _get_outreach_stats()
        return render_sprint(tasks, outreach_stats)
    except Exception as e:
        return render_sprint({"tasks": []}, {}, error=str(e))


@app.post("/api/sprint-add-task")
async def sprint_add_task(request: Request):
    try:
        body = await request.json()
        title = body.get("title", "").strip()
        if not title:
            return JSONResponse({"error": "title required"}, status_code=400)
        data = json.loads(TASKS_FILE.read_text())
        from datetime import timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        new_task = {
            "id": f"task_captured_{int(datetime.now().timestamp())}",
            "title": title,
            "description": body.get("description", "Captured via Sprint Hub session close."),
            "section": "today",
            "priority": body.get("priority", "medium"),
            "status": "pending",
            "due_date": None,
            "trigger_condition": None,
            "tags": ["captured", "sprint"],
            "project": "ai-client-sprint",
            "progress": 0,
            "created_at": now,
            "updated_at": now,
            "completed_at": None
        }
        data["tasks"].append(new_task)
        data["stats"]["total_created"] = len(data["tasks"])
        data["stats"]["last_updated"] = now
        TASKS_FILE.write_text(json.dumps(data, indent=2))
        return {"ok": True, "task_id": new_task["id"]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/sprint-close")
async def sprint_close(request: Request):
    """Session close: send EOD summary to Clawdbot via Telegram."""
    try:
        body = await request.json()
        missed = body.get("missed_items", "")
        data = json.loads(TASKS_FILE.read_text())
        today_tasks = [t for t in data["tasks"] if t.get("section") in ("today", "recently_done")]
        done = [t for t in today_tasks if t.get("status") == "complete"]
        pending = [t for t in today_tasks if t.get("status") == "pending"]
        done_lines = "\n".join(f"  ✓ {t['title']}" for t in done) or "  (none)"
        pending_lines = "\n".join(f"  ○ {t['title']}" for t in pending) or "  (none)"
        msg = (
            f"🔒 SESSION CLOSED — {datetime.now().strftime('%b %d, %I:%M %p')}\n\n"
            f"✅ Completed today:\n{done_lines}\n\n"
            f"⏳ Still pending:\n{pending_lines}"
        )
        if missed.strip():
            msg += f"\n\n📌 Unaddressed items captured:\n{missed.strip()}"
            # Auto-add each line as a task
            for line in missed.strip().split("\n"):
                line = line.strip().lstrip("-•").strip()
                if line:
                    t_data = json.loads(TASKS_FILE.read_text())
                    from datetime import timezone
                    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    t_data["tasks"].append({
                        "id": f"task_captured_{int(datetime.now().timestamp())}",
                        "title": line,
                        "description": "Captured at session close — was raised but not addressed.",
                        "section": "today",
                        "priority": "medium",
                        "status": "pending",
                        "due_date": None,
                        "trigger_condition": None,
                        "tags": ["captured", "session-close"],
                        "project": "ai-client-sprint",
                        "progress": 0,
                        "created_at": now_str,
                        "updated_at": now_str,
                        "completed_at": None
                    })
                    t_data["stats"]["total_created"] = len(t_data["tasks"])
                    t_data["stats"]["last_updated"] = now_str
                    TASKS_FILE.write_text(json.dumps(t_data, indent=2))
        # Send to Telegram
        source = body.get("source", "manual")
        if TELEGRAM_BOT_TOKEN:
            label = "🤖 AUTO EOD" if source == "auto_eod" else "🔒 SESSION CLOSED"
            msg = msg.replace("🔒 SESSION CLOSED", label, 1)
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": ""},
                    timeout=5
                )
        # Log close so auto-send knows not to double-fire
        try:
            SESSION_CLOSE_LOG.parent.mkdir(parents=True, exist_ok=True)
            log = {"entries": []}
            if SESSION_CLOSE_LOG.exists():
                log = json.loads(SESSION_CLOSE_LOG.read_text())
            log["entries"].append({
                "date": str(date.today()),
                "time": datetime.now().strftime("%H:%M"),
                "source": body.get("source", "manual")
            })
            log["entries"] = log["entries"][-90:]
            SESSION_CLOSE_LOG.write_text(json.dumps(log, indent=2))
        except Exception:
            pass
        return {"ok": True, "message": msg}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def _get_outreach_stats():
    """Aggregate outreach stats from all tracking JSON files."""
    stats = {"total_sent": 0, "total_failed": 0, "files": 0, "follow_ups_due": 0}
    try:
        from datetime import date, timedelta
        today = date.today()
        for f in sorted(TRACKING_DIR.glob("outreach_tracking_*.json")):
            data = json.loads(f.read_text())
            stats["total_sent"] += data.get("total_sent", 0)
            stats["total_failed"] += data.get("total_failed", 0)
            stats["files"] += 1
            # Count emails due for follow-up (sent 3+ days ago, follow_up_count == 0)
            for email in data.get("emails", []):
                sent_date_str = email.get("sent_at", "")[:10]
                try:
                    sent_date = date.fromisoformat(sent_date_str)
                    days_ago = (today - sent_date).days
                    fc = email.get("follow_up_count", 0)
                    if fc == 0 and days_ago >= 3:
                        stats["follow_ups_due"] += 1
                    elif fc == 1 and days_ago >= 4:
                        stats["follow_ups_due"] += 1
                except Exception:
                    pass
    except Exception:
        pass
    return stats


@app.get("/outreach", response_class=HTMLResponse)
async def outreach_feed():
    """Cold outreach pipeline feed — batch leads + follow-up sequence status."""
    try:
        from .ui import render_outreach
        campaigns_file = TRACKING_DIR / "outreach_campaigns.json"
        records = []
        if campaigns_file.exists():
            data = json.loads(campaigns_file.read_text())
            records = data.get("records", [])
        return render_outreach(records)
    except Exception as e:
        from .ui import render_outreach
        return render_outreach([], error=str(e))


@app.get("/api/data")
async def api_data():
    try:
        data = get_dashboard_data()
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "accountability-engine", "version": "2.0.0"}


if __name__ == "__main__":
    print(f"\n  Marceau Accountability Engine → http://127.0.0.1:{PORT}\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
