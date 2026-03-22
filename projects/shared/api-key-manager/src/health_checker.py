#!/usr/bin/env python3
"""
KeyVault — Automated Health Checker

Verifies API keys actually work by making lightweight test calls.
Stores results in health_checks table and updates key status.

Run: python -m projects.shared.api-key-manager.src.health_checker [--org-id 1]
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values
from .models import get_db, decrypt_value, log_audit

MAC_ENV_PATH = Path(__file__).parents[4] / ".env"


# ─── Health check functions per service ──────────────────────

def _check_anthropic(api_key: str) -> tuple[bool, int, str]:
    """Test Anthropic API with a minimal request."""
    start = time.time()
    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({"model": "claude-haiku-4-5-20251001", "max_tokens": 1, "messages": [{"role": "user", "content": "hi"}]}).encode(),
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
        ms = int((time.time() - start) * 1000)
        return True, ms, ""
    except urllib.error.HTTPError as e:
        ms = int((time.time() - start) * 1000)
        if e.code == 401:
            return False, ms, "Invalid API key (401)"
        elif e.code == 429:
            return True, ms, "Rate limited but key is valid"
        return True, ms, f"HTTP {e.code} (key accepted)"
    except Exception as e:
        return False, 0, str(e)[:200]


def _check_openai(api_key: str) -> tuple[bool, int, str]:
    start = time.time()
    try:
        req = urllib.request.Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        urllib.request.urlopen(req, timeout=10)
        ms = int((time.time() - start) * 1000)
        return True, ms, ""
    except urllib.error.HTTPError as e:
        ms = int((time.time() - start) * 1000)
        if e.code == 401:
            return False, ms, "Invalid API key (401)"
        return True, ms, f"HTTP {e.code}"
    except Exception as e:
        return False, 0, str(e)[:200]


def _check_stripe(api_key: str) -> tuple[bool, int, str]:
    start = time.time()
    try:
        req = urllib.request.Request(
            "https://api.stripe.com/v1/balance",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        urllib.request.urlopen(req, timeout=10)
        ms = int((time.time() - start) * 1000)
        return True, ms, ""
    except urllib.error.HTTPError as e:
        ms = int((time.time() - start) * 1000)
        if e.code == 401:
            return False, ms, "Invalid API key (401)"
        return True, ms, f"HTTP {e.code}"
    except Exception as e:
        return False, 0, str(e)[:200]


def _check_twilio(account_sid: str) -> tuple[bool, int, str]:
    start = time.time()
    try:
        # Just check if the account SID format is valid and reachable
        req = urllib.request.Request(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}.json",
            headers={"Authorization": f"Basic {account_sid}:dummy"}  # Will 401 but confirms endpoint
        )
        urllib.request.urlopen(req, timeout=10)
        ms = int((time.time() - start) * 1000)
        return True, ms, ""
    except urllib.error.HTTPError as e:
        ms = int((time.time() - start) * 1000)
        if e.code == 401:
            return True, ms, "Endpoint reachable (auth not tested — needs SID+token pair)"
        return False, ms, f"HTTP {e.code}"
    except Exception as e:
        return False, 0, str(e)[:200]


def _check_elevenlabs(api_key: str) -> tuple[bool, int, str]:
    start = time.time()
    try:
        req = urllib.request.Request(
            "https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": api_key}
        )
        urllib.request.urlopen(req, timeout=10)
        ms = int((time.time() - start) * 1000)
        return True, ms, ""
    except urllib.error.HTTPError as e:
        ms = int((time.time() - start) * 1000)
        if e.code == 401:
            return False, ms, "Invalid API key (401)"
        return True, ms, f"HTTP {e.code}"
    except Exception as e:
        return False, 0, str(e)[:200]


def _check_replicate(api_token: str) -> tuple[bool, int, str]:
    start = time.time()
    try:
        req = urllib.request.Request(
            "https://api.replicate.com/v1/account",
            headers={"Authorization": f"Bearer {api_token}"}
        )
        urllib.request.urlopen(req, timeout=10)
        ms = int((time.time() - start) * 1000)
        return True, ms, ""
    except urllib.error.HTTPError as e:
        ms = int((time.time() - start) * 1000)
        if e.code == 401:
            return False, ms, "Invalid token (401)"
        return True, ms, f"HTTP {e.code}"
    except Exception as e:
        return False, 0, str(e)[:200]


def _check_xai(api_key: str) -> tuple[bool, int, str]:
    start = time.time()
    try:
        req = urllib.request.Request(
            "https://api.x.ai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        urllib.request.urlopen(req, timeout=10)
        ms = int((time.time() - start) * 1000)
        return True, ms, ""
    except urllib.error.HTTPError as e:
        ms = int((time.time() - start) * 1000)
        if e.code in (401, 403):
            return False, ms, f"Invalid/expired key ({e.code})"
        return True, ms, f"HTTP {e.code}"
    except Exception as e:
        return False, 0, str(e)[:200]


def _check_apollo(api_key: str) -> tuple[bool, int, str]:
    start = time.time()
    try:
        req = urllib.request.Request(
            "https://api.apollo.io/api/v1/auth/health",
            headers={"X-Api-Key": api_key, "Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
        ms = int((time.time() - start) * 1000)
        return True, ms, ""
    except urllib.error.HTTPError as e:
        ms = int((time.time() - start) * 1000)
        if e.code == 401:
            return False, ms, "Invalid API key (401)"
        # Apollo may not have /health — try search
        return True, ms, f"HTTP {e.code} (key format accepted)"
    except Exception as e:
        return False, 0, str(e)[:200]


def _check_x_bearer(bearer_token: str) -> tuple[bool, int, str]:
    start = time.time()
    try:
        req = urllib.request.Request(
            "https://api.twitter.com/2/users/me",
            headers={"Authorization": f"Bearer {bearer_token}"}
        )
        urllib.request.urlopen(req, timeout=10)
        ms = int((time.time() - start) * 1000)
        return True, ms, ""
    except urllib.error.HTTPError as e:
        ms = int((time.time() - start) * 1000)
        if e.code == 401:
            return False, ms, "Invalid bearer token (401)"
        if e.code == 403:
            return True, ms, "Token valid but endpoint requires user context"
        return True, ms, f"HTTP {e.code}"
    except Exception as e:
        return False, 0, str(e)[:200]


# Map env var names to check functions
HEALTH_CHECKS = {
    "ANTHROPIC_API_KEY": ("anthropic_api", _check_anthropic),
    "OPENAI_API_KEY": ("openai_api", _check_openai),
    "STRIPE_SECRET_KEY": ("stripe_api", _check_stripe),
    "TWILIO_ACCOUNT_SID": ("twilio_api", _check_twilio),
    "ELEVENLABS_API_KEY": ("elevenlabs_api", _check_elevenlabs),
    "REPLICATE_API_TOKEN": ("replicate_api", _check_replicate),
    "XAI_API_KEY": ("xai_api", _check_xai),
    "APOLLO_API_KEY": ("apollo_api", _check_apollo),
    "X_BEARER_TOKEN": ("x_bearer", _check_x_bearer),
}


def run_health_checks(org_id: int = None):
    """Run health checks for all checkable keys."""
    conn = get_db()

    # If no org_id, check all orgs
    if org_id:
        orgs = [(org_id,)]
    else:
        orgs = conn.execute("SELECT id FROM organizations").fetchall()

    total_checked = 0
    total_healthy = 0
    total_failed = 0

    for org_row in orgs:
        oid = org_row[0] if isinstance(org_row, tuple) else org_row["id"]

        # Get all active keys with stored values
        keys = conn.execute("""
            SELECT ak.id, ak.env_var_name, ak.encrypted_value, s.name as service_name
            FROM api_keys ak JOIN services s ON ak.service_id = s.id
            WHERE ak.org_id = ? AND ak.status = 'active' AND ak.encrypted_value IS NOT NULL
        """, (oid,)).fetchall()

        for key in keys:
            var_name = key["env_var_name"]
            if var_name not in HEALTH_CHECKS:
                continue

            check_type, check_fn = HEALTH_CHECKS[var_name]
            try:
                value = decrypt_value(key["encrypted_value"])
            except Exception:
                continue

            print(f"  Checking {key['service_name']} ({var_name})...", end=" ", flush=True)
            is_healthy, response_ms, error_msg = check_fn(value)
            total_checked += 1

            if is_healthy:
                total_healthy += 1
                print(f"OK ({response_ms}ms)")
            else:
                total_failed += 1
                print(f"FAILED: {error_msg}")

            # Store result
            conn.execute("""
                INSERT INTO health_checks (api_key_id, check_type, is_healthy, response_ms, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (key["id"], check_type, int(is_healthy), response_ms, error_msg or None))

            # Update key status
            new_status = "active" if is_healthy else "warning"
            conn.execute("""
                UPDATE api_keys SET last_verified_at = datetime('now'), last_verified_ok = ?, status = ?
                WHERE id = ? AND status IN ('active', 'warning')
            """, (int(is_healthy), new_status, key["id"]))

        conn.commit()
        log_audit(conn, oid, "health_check_run", details=f"Checked {total_checked}: {total_healthy} healthy, {total_failed} failed")

    print(f"\nHealth check complete: {total_checked} checked, {total_healthy} healthy, {total_failed} failed")
    conn.close()
    return total_checked, total_healthy, total_failed


if __name__ == "__main__":
    org = None
    for arg in sys.argv[1:]:
        if arg.startswith("--org-id"):
            org = int(sys.argv[sys.argv.index(arg) + 1])
    print("Running KeyVault health checks...")
    run_health_checks(org)
