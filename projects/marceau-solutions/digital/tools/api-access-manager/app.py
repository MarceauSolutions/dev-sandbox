"""
API Access Manager — Main Flask Application
Port: 8791
Launch: ./scripts/api-access-manager.sh
"""

import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta

from database import (
    init_db, get_db,
    get_all_platforms, get_platform, get_platform_by_slug,
    upsert_platform, update_platform,
    get_steps, complete_step, uncomplete_step, bulk_insert_steps,
    get_keys, add_key, update_key, rotate_key, delete_key,
    get_reminders, add_reminder, complete_reminder,
    log_activity, get_activity_log,
    get_dashboard_stats,
)
from platforms import (
    PLATFORM_GUIDES, APPLICATION_ORDER,
    get_platform_guide, get_all_platform_slugs, get_application_order,
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

PORT = 8791


@app.context_processor
def inject_globals():
    return {"platform_guides": PLATFORM_GUIDES}


# --- Template Helpers ---

@app.template_filter("timeago")
def timeago_filter(dt_str):
    if not dt_str:
        return "Never"
    try:
        dt = datetime.fromisoformat(dt_str)
        diff = datetime.now() - dt
        if diff.days > 365:
            return f"{diff.days // 365}y ago"
        if diff.days > 30:
            return f"{diff.days // 30}mo ago"
        if diff.days > 0:
            return f"{diff.days}d ago"
        if diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        return f"{diff.seconds // 60}m ago"
    except Exception:
        return dt_str


@app.template_filter("days_until")
def days_until_filter(dt_str):
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str)
        diff = dt - datetime.now()
        return diff.days
    except Exception:
        return None


@app.template_filter("status_badge")
def status_badge_filter(status):
    badges = {
        "not_started": ("Not Started", "secondary"),
        "in_progress": ("In Progress", "warning"),
        "approved": ("Approved", "success"),
        "rejected": ("Rejected", "danger"),
        "suspended": ("Suspended", "danger"),
    }
    label, cls = badges.get(status, ("Unknown", "secondary"))
    return f'<span class="badge badge-{cls}">{label}</span>'


# --- Routes ---

@app.route("/")
def dashboard():
    stats = get_dashboard_stats()
    platforms = get_all_platforms()
    upcoming_reminders = get_reminders()[:5]
    recent_activity = get_activity_log(limit=10)

    # Get keys expiring soon
    all_keys = get_keys()
    expiring_keys = []
    for k in all_keys:
        if k["expires_at"] and k["is_active"]:
            days = days_until_filter(k["expires_at"])
            if days is not None and days <= 30:
                k["days_remaining"] = days
                expiring_keys.append(k)
    expiring_keys.sort(key=lambda x: x.get("days_remaining", 999))

    return render_template(
        "dashboard.html",
        stats=stats,
        platforms=platforms,
        upcoming_reminders=upcoming_reminders,
        recent_activity=recent_activity,
        expiring_keys=expiring_keys[:5],
        application_order=APPLICATION_ORDER,
        platform_guides=PLATFORM_GUIDES,
    )


@app.route("/platforms")
def platforms_list():
    platforms = get_all_platforms()
    return render_template(
        "platforms.html",
        platforms=platforms,
        platform_guides=PLATFORM_GUIDES,
        application_order=APPLICATION_ORDER,
    )


@app.route("/platform/<slug>")
def platform_detail(slug):
    guide = get_platform_guide(slug)
    if not guide:
        return "Platform not found", 404

    # Ensure platform exists in DB
    db_platform = get_platform_by_slug(slug)
    if not db_platform:
        db_platform = upsert_platform(guide["name"], slug)
        # Seed steps from guide
        bulk_insert_steps(db_platform["id"], guide["steps"])
        log_activity(db_platform["id"], "initialized", f"Platform '{guide['name']}' added to tracker")

    steps = get_steps(db_platform["id"])
    keys = get_keys(db_platform["id"])
    reminders = get_reminders(db_platform["id"])
    activity = get_activity_log(db_platform["id"], limit=20)

    # Calculate progress
    total_steps = len(steps)
    completed_steps = sum(1 for s in steps if s["is_completed"])
    progress = int((completed_steps / total_steps * 100) if total_steps else 0)

    return render_template(
        "platform_detail.html",
        platform=db_platform,
        guide=guide,
        steps=steps,
        keys=keys,
        reminders=reminders,
        activity=activity,
        progress=progress,
        total_steps=total_steps,
        completed_steps=completed_steps,
    )


@app.route("/keys")
def keys_vault():
    all_keys = get_keys()
    for k in all_keys:
        if k["expires_at"]:
            k["days_remaining"] = days_until_filter(k["expires_at"])
        else:
            k["days_remaining"] = None
    platforms = get_all_platforms()
    return render_template("keys.html", keys=all_keys, platforms=platforms)


@app.route("/reminders")
def reminders_list():
    active = get_reminders(include_completed=False)
    completed = get_reminders(include_completed=True)
    completed = [r for r in completed if r.get("is_completed")]
    return render_template("reminders.html", active=active, completed=completed)


@app.route("/order")
def application_order():
    return render_template(
        "order.html",
        application_order=APPLICATION_ORDER,
        platform_guides=PLATFORM_GUIDES,
    )


@app.route("/activity")
def activity_page():
    activity = get_activity_log(limit=100)
    return render_template("activity.html", activity=activity)


# --- API Endpoints ---

@app.route("/api/platform/<int:platform_id>/status", methods=["POST"])
def api_update_status(platform_id):
    data = request.json
    new_status = data.get("status")
    if new_status not in ("not_started", "in_progress", "approved", "rejected", "suspended"):
        return jsonify({"error": "Invalid status"}), 400
    kwargs = {"status": new_status}
    if new_status == "in_progress":
        kwargs["started_at"] = datetime.now().isoformat()
    elif new_status == "approved":
        kwargs["approved_at"] = datetime.now().isoformat()
    update_platform(platform_id, **kwargs)
    log_activity(platform_id, "status_changed", f"Status changed to {new_status}")
    return jsonify({"ok": True})


@app.route("/api/platform/<int:platform_id>/update", methods=["POST"])
def api_update_platform(platform_id):
    data = request.json
    allowed = {"app_id", "app_name", "notes", "application_url"}
    kwargs = {k: v for k, v in data.items() if k in allowed}
    if kwargs:
        update_platform(platform_id, **kwargs)
        log_activity(platform_id, "updated", f"Updated: {', '.join(kwargs.keys())}")
    return jsonify({"ok": True})


@app.route("/api/step/<int:step_id>/toggle", methods=["POST"])
def api_toggle_step(step_id):
    data = request.json
    completed = data.get("completed", True)
    if completed:
        complete_step(step_id)
    else:
        uncomplete_step(step_id)
    return jsonify({"ok": True})


@app.route("/api/keys", methods=["POST"])
def api_add_key():
    data = request.json
    add_key(
        platform_id=data["platform_id"],
        key_name=data["key_name"],
        key_type=data.get("key_type", "api_key"),
        env_var_name=data.get("env_var_name", ""),
        rotation_days=data.get("rotation_days", 90),
        notes=data.get("notes", ""),
        expires_at=data.get("expires_at"),
    )
    log_activity(data["platform_id"], "key_added", f"Added key: {data['key_name']}")
    return jsonify({"ok": True})


@app.route("/api/keys/<int:key_id>/rotate", methods=["POST"])
def api_rotate_key(key_id):
    rotate_key(key_id)
    return jsonify({"ok": True})


@app.route("/api/keys/<int:key_id>/delete", methods=["POST"])
def api_delete_key(key_id):
    delete_key(key_id)
    return jsonify({"ok": True})


@app.route("/api/reminders", methods=["POST"])
def api_add_reminder():
    data = request.json
    add_reminder(
        platform_id=data["platform_id"],
        reminder_type=data.get("reminder_type", "follow_up"),
        title=data["title"],
        description=data.get("description", ""),
        due_date=data["due_date"],
    )
    log_activity(data["platform_id"], "reminder_added", f"Reminder: {data['title']}")
    return jsonify({"ok": True, "message": "Reminder created. Use 'Add to Calendar' button to sync with Google Calendar."})


@app.route("/api/reminders/<int:reminder_id>/complete", methods=["POST"])
def api_complete_reminder(reminder_id):
    complete_reminder(reminder_id)
    return jsonify({"ok": True})


@app.route("/api/seed", methods=["POST"])
def api_seed_platforms():
    """Seed all platforms from the knowledge base into the database."""
    for slug, guide in PLATFORM_GUIDES.items():
        order_info = next((o for o in APPLICATION_ORDER if o["slug"] == slug), {})
        db_platform = upsert_platform(
            guide["name"], slug,
            priority_order=order_info.get("order", 99),
            application_url=guide.get("api_portal", ""),
        )
        # Seed steps if none exist
        existing_steps = get_steps(db_platform["id"])
        if not existing_steps:
            bulk_insert_steps(db_platform["id"], guide["steps"])
    log_activity(None, "seeded", "All platforms seeded from knowledge base")
    return jsonify({"ok": True, "message": f"Seeded {len(PLATFORM_GUIDES)} platforms"})


# --- Initialize ---

if __name__ == "__main__":
    init_db()

    # Auto-seed platforms if DB is empty
    if not get_all_platforms():
        for slug, guide in PLATFORM_GUIDES.items():
            order_info = next((o for o in APPLICATION_ORDER if o["slug"] == slug), {})
            db_platform = upsert_platform(
                guide["name"], slug,
                priority_order=order_info.get("order", 99),
                application_url=guide.get("api_portal", ""),
            )
            bulk_insert_steps(db_platform["id"], guide["steps"])
        log_activity(None, "initialized", "All platforms seeded on first launch")
        print(f"✓ Seeded {len(PLATFORM_GUIDES)} platforms")

    print(f"\n🔑 API Access Manager running at http://127.0.0.1:{PORT}\n")
    app.run(host="127.0.0.1", port=PORT, debug=False)
