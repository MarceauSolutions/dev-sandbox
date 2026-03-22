#!/usr/bin/env python3
"""
KeyVault — API Key Management SaaS Platform

Multi-tenant credential management with encryption, health monitoring,
environment sync, deprecation tracking, and automated alerts.

Run: python -m projects.shared.api-key-manager.src.app
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from functools import wraps

from fastapi import FastAPI, Request, Form, HTTPException, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import uvicorn

from .models import (
    get_db, create_org, create_user, authenticate_user, create_jwt, decode_jwt,
    generate_api_token, hash_password, encrypt_value, decrypt_value, mask_value,
    upsert_service, upsert_api_key, add_consumer, add_deprecation_notice,
    add_reminder, log_audit, get_all_keys_with_details, get_dashboard_summary,
    get_expiring_keys, get_active_deprecations, get_sync_status,
    get_recent_audit_log, get_plan_limits, get_health_history
)
from .ui import render_page, render_landing

app = FastAPI(title="KeyVault™", version="2.0.0")
PORT = int(os.getenv("KEYVAULT_PORT", "8793"))


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ─── Auth middleware ─────────────────────────────────────────

def get_current_user(request: Request) -> Optional[dict]:
    """Extract user from JWT cookie or Authorization header."""
    token = request.cookies.get("kv_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        return None
    try:
        payload = decode_jwt(token)
        return payload
    except Exception:
        return None


def require_auth(request: Request) -> dict:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ─── Landing page ────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return render_landing()


# ─── Auth routes ─────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    user = get_current_user(request)
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return render_page("login", "Log In", {}, error=error)


@app.post("/login")
async def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = get_db()
    user = authenticate_user(conn, email, password)
    conn.close()
    if not user:
        return RedirectResponse("/login?error=Invalid+email+or+password", status_code=303)
    token = create_jwt(user["id"], user["org_id"], user["role"], user["email"])
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie("kv_token", token, httponly=True, secure=True, max_age=72*3600, samesite="lax")
    return response


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, error: str = ""):
    user = get_current_user(request)
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return render_page("signup", "Sign Up", {}, error=error)


@app.post("/signup")
async def signup_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    org_name: str = Form(...),
):
    if len(password) < 8:
        return RedirectResponse("/signup?error=Password+must+be+at+least+8+characters", status_code=303)

    slug = re.sub(r'[^a-z0-9]+', '-', org_name.lower()).strip('-')
    conn = get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            return RedirectResponse("/signup?error=Email+already+registered", status_code=303)

        org_id = create_org(conn, org_name, slug)
        user_id = create_user(conn, email, password, name, org_id, "owner")
        log_audit(conn, org_id, "org_created", "organization", org_id, f"Org '{org_name}' created by {email}", user_id, ip=request.client.host)
        token = create_jwt(user_id, org_id, "owner", email)
        conn.close()
        response = RedirectResponse("/onboarding", status_code=303)
        response.set_cookie("kv_token", token, httponly=True, secure=True, max_age=72*3600, samesite="lax")
        return response
    except Exception as e:
        conn.close()
        return RedirectResponse(f"/signup?error={str(e)[:100]}", status_code=303)


@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("kv_token")
    return response


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return render_page("onboarding", "Get Started", {"user": user})


# ─── Dashboard ───────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    summary = get_dashboard_summary(conn, user["org_id"])
    expiring = get_expiring_keys(conn, user["org_id"], 30)
    deprecations = get_active_deprecations(conn, user["org_id"])
    limits = get_plan_limits(conn, user["org_id"])
    recent_audit = get_recent_audit_log(conn, user["org_id"], 10)
    conn.close()
    return render_page("dashboard", "Dashboard", {
        "user": user, "summary": summary, "expiring": expiring,
        "deprecations": deprecations, "limits": limits, "audit": recent_audit,
    })


# ─── Keys ────────────────────────────────────────────────────

@app.get("/keys", response_class=HTMLResponse)
async def keys_list(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    keys = get_all_keys_with_details(conn, user["org_id"])
    limits = get_plan_limits(conn, user["org_id"])
    conn.close()
    return render_page("keys", "API Keys", {"user": user, "keys": keys, "limits": limits})


@app.get("/keys/add", response_class=HTMLResponse)
async def add_key_form(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    services = conn.execute("SELECT id, name FROM services WHERE org_id = ? ORDER BY name", (user["org_id"],)).fetchall()
    limits = get_plan_limits(conn, user["org_id"])
    conn.close()
    return render_page("add_key", "Add Key", {"user": user, "services": services, "limits": limits})


@app.post("/keys/add")
async def add_key_submit(
    request: Request,
    service_id: str = Form(""),
    new_service_name: str = Form(""),
    category: str = Form("other"),
    env_var_name: str = Form(...),
    label: str = Form(""),
    key_value: str = Form(""),
    key_type: str = Form("api_key"),
    status: str = Form("active"),
    expires_at: str = Form(""),
    monthly_cost: str = Form(""),
    dashboard_url: str = Form(""),
    notes: str = Form(""),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    conn = get_db()
    limits = get_plan_limits(conn, user["org_id"])
    if limits["current_keys"] >= limits["max_keys"]:
        conn.close()
        return RedirectResponse("/keys?error=Key+limit+reached.+Upgrade+your+plan.", status_code=303)

    if service_id:
        sid = int(service_id)
    elif new_service_name:
        kwargs = {}
        if dashboard_url:
            kwargs["dashboard_url"] = dashboard_url
        sid = upsert_service(conn, user["org_id"], new_service_name, category, **kwargs)
    else:
        conn.close()
        raise HTTPException(400, "Select a service or provide a new name")

    kwargs = {"key_type": key_type, "status": status}
    if expires_at:
        kwargs["expires_at"] = expires_at
    if monthly_cost:
        kwargs["monthly_cost"] = float(monthly_cost)
    if notes:
        kwargs["notes"] = notes

    kid = upsert_api_key(conn, user["org_id"], sid, env_var_name, label=label or None, value=key_value or None, **kwargs)
    log_audit(conn, user["org_id"], "key_created", "api_key", kid, f"Added {env_var_name}", user["user_id"], ip=request.client.host)

    # Auto-create expiration reminder if expiry set
    if expires_at:
        try:
            exp_date = datetime.strptime(expires_at, "%Y-%m-%d")
            remind_date = (exp_date - timedelta(days=14)).strftime("%Y-%m-%d")
            add_reminder(conn, user["org_id"], f"API key {env_var_name} expires on {expires_at}", remind_date, "expiration", kid, sid)
        except ValueError:
            pass

    conn.close()
    return RedirectResponse("/keys", status_code=303)


@app.get("/keys/{key_id}", response_class=HTMLResponse)
async def key_detail(request: Request, key_id: int):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    key = conn.execute("""
        SELECT ak.*, s.name as service_name, s.category, s.dashboard_url
        FROM api_keys ak JOIN services s ON ak.service_id = s.id
        WHERE ak.id = ? AND ak.org_id = ?
    """, (key_id, user["org_id"])).fetchone()
    if not key:
        conn.close()
        raise HTTPException(404, "Key not found")
    consumers = conn.execute("SELECT * FROM key_consumers WHERE api_key_id = ?", (key_id,)).fetchall()
    health = get_health_history(conn, key_id, 10)
    syncs = conn.execute("""
        SELECT ess.*, e.name as env_name FROM env_sync_status ess
        JOIN environments e ON ess.environment_id = e.id WHERE ess.api_key_id = ?
    """, (key_id,)).fetchall()
    conn.close()
    return render_page("key_detail", key["label"], {
        "user": user, "key": key, "consumers": consumers, "health": health, "syncs": syncs,
    })


@app.post("/keys/{key_id}/delete")
async def delete_key(request: Request, key_id: int):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    key = conn.execute("SELECT env_var_name FROM api_keys WHERE id = ? AND org_id = ?", (key_id, user["org_id"])).fetchone()
    if key:
        conn.execute("DELETE FROM key_consumers WHERE api_key_id = ?", (key_id,))
        conn.execute("DELETE FROM env_sync_status WHERE api_key_id = ?", (key_id,))
        conn.execute("DELETE FROM health_checks WHERE api_key_id = ?", (key_id,))
        conn.execute("DELETE FROM reminders WHERE api_key_id = ?", (key_id,))
        conn.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
        log_audit(conn, user["org_id"], "key_deleted", "api_key", key_id, f"Deleted {key['env_var_name']}", user["user_id"], ip=request.client.host)
        conn.commit()
    conn.close()
    return RedirectResponse("/keys", status_code=303)


@app.post("/keys/{key_id}/reveal")
async def reveal_key(request: Request, key_id: int):
    user = get_current_user(request)
    if not user or user["role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owners/admins can reveal key values")
    conn = get_db()
    key = conn.execute("SELECT encrypted_value, env_var_name FROM api_keys WHERE id = ? AND org_id = ?", (key_id, user["org_id"])).fetchone()
    conn.close()
    if not key or not key["encrypted_value"]:
        raise HTTPException(404, "No stored value")
    log_audit(conn, user["org_id"], "key_revealed", "api_key", key_id, f"Revealed {key['env_var_name']}", user["user_id"], ip=request.client.host)
    return JSONResponse({"value": decrypt_value(key["encrypted_value"])})


# ─── Services ────────────────────────────────────────────────

@app.get("/services", response_class=HTMLResponse)
async def services_list(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    services = conn.execute("""
        SELECT s.*, COUNT(ak.id) as key_count,
            SUM(CASE WHEN ak.status = 'active' THEN 1 ELSE 0 END) as active_count
        FROM services s LEFT JOIN api_keys ak ON ak.service_id = s.id
        WHERE s.org_id = ?
        GROUP BY s.id ORDER BY s.category, s.name
    """, (user["org_id"],)).fetchall()
    conn.close()
    return render_page("services", "Services", {"user": user, "services": services})


# ─── Environments ────────────────────────────────────────────

@app.get("/environments", response_class=HTMLResponse)
async def environments_list(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    envs = conn.execute("SELECT * FROM environments WHERE org_id = ?", (user["org_id"],)).fetchall()
    syncs = get_sync_status(conn, user["org_id"])
    limits = get_plan_limits(conn, user["org_id"])
    conn.close()
    return render_page("environments", "Environments", {"user": user, "envs": envs, "syncs": syncs, "limits": limits})


@app.post("/environments/add")
async def add_environment(request: Request, name: str = Form(...), env_file_path: str = Form(""), ssh_command: str = Form(""), notes: str = Form("")):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    limits = get_plan_limits(conn, user["org_id"])
    if limits["current_envs"] >= limits["max_environments"]:
        conn.close()
        return RedirectResponse("/environments?error=Environment+limit+reached", status_code=303)
    conn.execute(
        "INSERT OR IGNORE INTO environments (org_id, name, env_file_path, ssh_command, notes) VALUES (?, ?, ?, ?, ?)",
        (user["org_id"], name, env_file_path, ssh_command, notes)
    )
    log_audit(conn, user["org_id"], "env_created", "environment", None, f"Added env '{name}'", user["user_id"], ip=request.client.host)
    conn.commit()
    conn.close()
    return RedirectResponse("/environments", status_code=303)


# ─── Deprecations ────────────────────────────────────────────

@app.get("/deprecations", response_class=HTMLResponse)
async def deprecations_list(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    deps = conn.execute("""
        SELECT dn.*, s.name as service_name
        FROM deprecation_notices dn JOIN services s ON dn.service_id = s.id
        WHERE dn.org_id = ?
        ORDER BY dn.status ASC, dn.effective_date DESC
    """, (user["org_id"],)).fetchall()
    conn.close()
    return render_page("deprecations", "Deprecations", {"user": user, "deprecations": deps})


# ─── Reminders ───────────────────────────────────────────────

@app.get("/reminders", response_class=HTMLResponse)
async def reminders_list(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    reminders = conn.execute("""
        SELECT r.*, ak.env_var_name, s.name as service_name
        FROM reminders r
        LEFT JOIN api_keys ak ON r.api_key_id = ak.id
        LEFT JOIN services s ON (r.service_id = s.id OR ak.service_id = s.id)
        WHERE r.org_id = ?
        ORDER BY r.sent ASC, r.remind_at ASC
    """, (user["org_id"],)).fetchall()
    conn.close()
    return render_page("reminders", "Reminders", {"user": user, "reminders": reminders})


# ─── Audit Log ───────────────────────────────────────────────

@app.get("/audit", response_class=HTMLResponse)
async def audit_log(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    logs = get_recent_audit_log(conn, user["org_id"], 100)
    conn.close()
    return render_page("audit", "Audit Log", {"user": user, "logs": logs})


# ─── Settings ────────────────────────────────────────────────

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    org = conn.execute("SELECT * FROM organizations WHERE id = ?", (user["org_id"],)).fetchone()
    members = conn.execute("SELECT id, email, name, role, last_login_at, created_at FROM users WHERE org_id = ?", (user["org_id"],)).fetchall()
    tokens = conn.execute("SELECT id, name, token_prefix, scopes, last_used_at, created_at FROM api_tokens WHERE org_id = ? AND is_active = 1", (user["org_id"],)).fetchall()
    notif_prefs = conn.execute("SELECT * FROM notification_prefs WHERE org_id = ?", (user["org_id"],)).fetchall()
    limits = get_plan_limits(conn, user["org_id"])
    conn.close()
    return render_page("settings", "Settings", {
        "user": user, "org": org, "members": members, "tokens": tokens,
        "notif_prefs": notif_prefs, "limits": limits,
    })


@app.post("/settings/notifications")
async def save_notification_prefs(request: Request, channel: str = Form(...), destination: str = Form(...), expiry_warn_days: int = Form(14)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    conn.execute("""
        INSERT INTO notification_prefs (org_id, channel, destination, expiry_warn_days)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(org_id, channel, destination) DO UPDATE SET expiry_warn_days = excluded.expiry_warn_days
    """, (user["org_id"], channel, destination, expiry_warn_days))
    log_audit(conn, user["org_id"], "notification_pref_updated", "notification_prefs", None, f"{channel}: {destination}", user["user_id"], ip=request.client.host)
    conn.commit()
    conn.close()
    return RedirectResponse("/settings", status_code=303)


@app.post("/settings/api-token")
async def create_api_token_route(request: Request, token_name: str = Form(...), scopes: str = Form("read")):
    user = get_current_user(request)
    if not user or user["role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owners/admins can create API tokens")
    conn = get_db()
    full_token, token_hash, prefix = generate_api_token()
    conn.execute(
        "INSERT INTO api_tokens (user_id, org_id, name, token_hash, token_prefix, scopes) VALUES (?, ?, ?, ?, ?, ?)",
        (user["user_id"], user["org_id"], token_name, token_hash, prefix, scopes)
    )
    log_audit(conn, user["org_id"], "api_token_created", "api_token", None, f"Token '{token_name}'", user["user_id"], ip=request.client.host)
    conn.commit()
    conn.close()
    # Show the token once — it can't be retrieved later
    return render_page("token_created", "API Token Created", {"user": user, "token": full_token, "name": token_name})


@app.post("/settings/invite")
async def invite_member(request: Request, email: str = Form(...), name: str = Form(...), role: str = Form("member"), password: str = Form(...)):
    user = get_current_user(request)
    if not user or user["role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owners/admins can invite members")
    conn = get_db()
    limits = get_plan_limits(conn, user["org_id"])
    if limits["current_members"] >= limits["max_members"]:
        conn.close()
        return RedirectResponse("/settings?error=Member+limit+reached.+Upgrade+plan.", status_code=303)
    try:
        uid = create_user(conn, email, password, name, user["org_id"], role)
        log_audit(conn, user["org_id"], "member_invited", "user", uid, f"Invited {email} as {role}", user["user_id"], ip=request.client.host)
    except Exception as e:
        conn.close()
        return RedirectResponse(f"/settings?error={str(e)[:80]}", status_code=303)
    conn.close()
    return RedirectResponse("/settings", status_code=303)


# ─── Public API (token-authenticated) ───────────────────────

def _api_auth(request: Request) -> dict:
    """Authenticate via Bearer token (API token or JWT)."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing Authorization header")
    token = auth[7:]

    # Try JWT first
    try:
        return decode_jwt(token)
    except Exception:
        pass

    # Try API token
    import hashlib
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = get_db()
    api_token = conn.execute(
        "SELECT * FROM api_tokens WHERE token_hash = ? AND is_active = 1",
        (token_hash,)
    ).fetchone()
    if not api_token:
        conn.close()
        raise HTTPException(401, "Invalid token")
    if api_token["expires_at"] and datetime.fromisoformat(api_token["expires_at"]) < datetime.now():
        conn.close()
        raise HTTPException(401, "Token expired")
    conn.execute("UPDATE api_tokens SET last_used_at = datetime('now') WHERE id = ?", (api_token["id"],))
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (api_token["user_id"],)).fetchone()
    conn.close()
    return {"user_id": user["id"], "org_id": user["org_id"], "role": user["role"], "email": user["email"], "scopes": api_token["scopes"]}


@app.get("/api/v1/summary")
async def api_summary(request: Request):
    user = _api_auth(request)
    conn = get_db()
    summary = get_dashboard_summary(conn, user["org_id"])
    conn.close()
    return summary


@app.get("/api/v1/keys")
async def api_keys(request: Request):
    user = _api_auth(request)
    conn = get_db()
    keys = get_all_keys_with_details(conn, user["org_id"])
    conn.close()
    result = []
    for k in keys:
        d = dict(k)
        d.pop("encrypted_value", None)  # Never expose in API
        result.append(d)
    return result


@app.get("/api/v1/keys/expiring")
async def api_expiring(request: Request, days: int = 30):
    user = _api_auth(request)
    conn = get_db()
    keys = get_expiring_keys(conn, user["org_id"], days)
    conn.close()
    return [dict(k) for k in keys]


@app.get("/api/v1/deprecations")
async def api_deprecations(request: Request):
    user = _api_auth(request)
    conn = get_db()
    deps = get_active_deprecations(conn, user["org_id"])
    conn.close()
    return [dict(d) for d in deps]


@app.get("/api/v1/health")
async def api_health():
    """Public health endpoint for uptime monitoring."""
    conn = get_db()
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return {"status": "healthy", "version": "2.0.0", "users": user_count}


# ─── Billing (Stripe) ───────────────────────────────────────

@app.get("/billing", response_class=HTMLResponse)
async def billing_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    conn = get_db()
    org = conn.execute("SELECT * FROM organizations WHERE id = ?", (user["org_id"],)).fetchone()
    limits = get_plan_limits(conn, user["org_id"])
    conn.close()
    return render_page("billing", "Billing", {"user": user, "org": org, "limits": limits})


@app.post("/billing/upgrade")
async def upgrade_plan(request: Request, plan: str = Form(...)):
    user = get_current_user(request)
    if not user or user["role"] != "owner":
        raise HTTPException(403, "Only owners can manage billing")

    plan_config = {
        "pro": {"max_keys": 100, "max_environments": 10, "max_members": 5},
        "enterprise": {"max_keys": 1000, "max_environments": 50, "max_members": 25},
    }
    if plan not in plan_config:
        raise HTTPException(400, "Invalid plan")

    conn = get_db()
    cfg = plan_config[plan]
    conn.execute("""
        UPDATE organizations SET plan = ?, max_keys = ?, max_environments = ?, max_members = ?, updated_at = datetime('now')
        WHERE id = ?
    """, (plan, cfg["max_keys"], cfg["max_environments"], cfg["max_members"], user["org_id"]))
    log_audit(conn, user["org_id"], "plan_upgraded", "organization", user["org_id"], f"Upgraded to {plan}", user["user_id"], ip=request.client.host)
    conn.commit()
    conn.close()
    return RedirectResponse("/billing?success=Plan+upgraded", status_code=303)


if __name__ == "__main__":
    print(f"\n  KeyVault™ Dashboard → http://127.0.0.1:{PORT}\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
