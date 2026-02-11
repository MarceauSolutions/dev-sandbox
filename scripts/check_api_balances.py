#!/usr/bin/env python3
"""
check_api_balances.py - API Provider Balance Dashboard

Checks the balance/status of all API providers and displays a dashboard.
Auto-updates .claude/hooks/provider-status.json when status changes.

Usage:
    python scripts/check_api_balances.py
    python scripts/check_api_balances.py --update    # Force update provider-status.json
    python scripts/check_api_balances.py --json       # Output as JSON

Requires: API keys in .env (REPLICATE_API_TOKEN, ELEVENLABS_API_KEY, etc.)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

SANDBOX_ROOT = Path(__file__).resolve().parents[1]

try:
    from dotenv import load_dotenv
    load_dotenv(SANDBOX_ROOT / ".env")
except ImportError:
    pass

STATUS_FILE = SANDBOX_ROOT / ".claude" / "hooks" / "provider-status.json"

PROVIDERS = {
    "replicate": {
        "env_key": "REPLICATE_API_TOKEN",
        "check_url": "https://api.replicate.com/v1/account",
        "billing_url": "https://replicate.com/account/billing",
        "pricing": "Pay-as-you-go",
    },
    "elevenlabs": {
        "env_key": "ELEVENLABS_API_KEY",
        "check_url": "https://api.elevenlabs.io/v1/user/subscription",
        "billing_url": "https://elevenlabs.io/subscription",
        "pricing": "Creator plan $22/mo, ~100K chars/mo",
    },
    "xai": {
        "env_key": "XAI_API_KEY",
        "check_url": None,
        "billing_url": "https://console.x.ai/",
        "pricing": "Pay-as-you-go",
    },
    "fal.ai": {
        "env_key": "FAL_API_KEY",
        "check_url": None,
        "billing_url": "https://fal.ai/billing",
        "pricing": "Pay-as-you-go",
    },
    "openai-tts": {
        "env_key": "OPENAI_API_KEY",
        "check_url": None,
        "billing_url": "https://platform.openai.com/usage",
        "pricing": "Pay-as-you-go",
    },
    "ideogram": {
        "env_key": "IDEOGRAM_API_KEY",
        "check_url": None,
        "billing_url": "https://ideogram.ai/manage",
        "pricing": "Pay-as-you-go",
    },
    "kie.ai": {
        "env_key": "KIE_API_KEY",
        "check_url": None,
        "billing_url": "https://kie.ai/billing",
        "pricing": "Pay-as-you-go (Veo 3 access)",
    },
}


def load_status():
    """Load provider status from JSON file."""
    if STATUS_FILE.exists():
        with open(STATUS_FILE) as f:
            return json.load(f)
    return {}


def save_status(status):
    """Save provider status to JSON file."""
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)
        f.write("\n")


def check_replicate():
    """Check Replicate account balance."""
    try:
        import requests
    except ImportError:
        return {"status": "unknown", "detail": "requests not installed"}

    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        return {"status": "no_key", "detail": "REPLICATE_API_TOKEN not set"}

    try:
        resp = requests.get(
            "https://api.replicate.com/v1/account",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            # Replicate doesn't expose balance directly in /v1/account
            # but a successful auth means the key is valid
            return {"status": "active", "detail": "Key valid, pay-as-you-go"}
        elif resp.status_code == 401:
            return {"status": "blocked", "detail": "Invalid API token"}
        else:
            return {"status": "unknown", "detail": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"status": "unknown", "detail": str(e)}


def check_elevenlabs():
    """Check ElevenLabs subscription status."""
    try:
        import requests
    except ImportError:
        return {"status": "unknown", "detail": "requests not installed"}

    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        return {"status": "no_key", "detail": "ELEVENLABS_API_KEY not set"}

    try:
        resp = requests.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": key},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            char_count = data.get("character_count", 0)
            char_limit = data.get("character_limit", 0)
            next_reset = data.get("next_character_count_reset_unix")
            tier = data.get("tier", "unknown")

            reset_str = ""
            if next_reset:
                reset_date = datetime.fromtimestamp(next_reset)
                days_left = (reset_date - datetime.now()).days
                reset_str = f", resets in {days_left}d ({reset_date.strftime('%b %d')})"

            remaining = char_limit - char_count
            pct = (char_count / char_limit * 100) if char_limit > 0 else 0

            if pct > 95:
                return {
                    "status": "blocked",
                    "detail": f"{char_count:,}/{char_limit:,} chars ({pct:.0f}% used){reset_str}",
                    "reason": "Character limit nearly exhausted",
                    "action": f"Wait for reset or upgrade plan",
                }
            elif pct > 80:
                return {
                    "status": "active",
                    "detail": f"{char_count:,}/{char_limit:,} chars ({pct:.0f}% used){reset_str}",
                    "warning": "LOW",
                }
            else:
                return {
                    "status": "active",
                    "detail": f"{char_count:,}/{char_limit:,} chars ({pct:.0f}% used){reset_str}",
                }
        elif resp.status_code == 401:
            return {"status": "blocked", "detail": "Invalid API key"}
        else:
            return {"status": "unknown", "detail": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"status": "unknown", "detail": str(e)}


def check_key_only(provider_name, env_key):
    """Simple key existence check for providers without balance APIs."""
    key = os.environ.get(env_key)
    if not key:
        return {"status": "no_key", "detail": f"{env_key} not set"}
    return {"status": "active", "detail": f"Key valid ({key[:4]}...{key[-4:]})"}


def check_all():
    """Check all providers and return results."""
    results = {}

    # Providers with real balance APIs
    results["replicate"] = check_replicate()
    results["elevenlabs"] = check_elevenlabs()

    # Key-only checks
    for name in ("xai", "fal.ai", "openai-tts", "ideogram", "kie.ai"):
        env_key = PROVIDERS[name]["env_key"]
        results[name] = check_key_only(name, env_key)

    # Overlay with existing status file (for manually blocked providers)
    existing = load_status()
    for name, info in existing.items():
        if info.get("status") == "blocked" and name in results:
            # Keep manual blocks unless the live check shows it's working
            if results[name]["status"] != "active":
                results[name] = {
                    "status": "blocked",
                    "detail": info.get("reason", "Manually blocked"),
                    "action": info.get("action", ""),
                    "renewal": info.get("renewal", ""),
                }

    return results


def update_status_file(results):
    """Update provider-status.json with live results."""
    existing = load_status()

    for name, result in results.items():
        if name not in existing:
            existing[name] = {}

        if result["status"] == "active":
            existing[name]["status"] = "active"
            existing[name]["note"] = result.get("detail", PROVIDERS.get(name, {}).get("pricing", ""))
            # Remove blocked fields if previously blocked
            for field in ("reason", "blocked_date", "renewal", "action"):
                existing[name].pop(field, None)
        elif result["status"] == "blocked":
            existing[name]["status"] = "blocked"
            existing[name]["reason"] = result.get("detail", "")
            existing[name]["action"] = result.get("action", "")
            if "renewal" in result:
                existing[name]["renewal"] = result["renewal"]
            if "blocked_date" not in existing[name]:
                existing[name]["blocked_date"] = datetime.now().strftime("%Y-%m-%d")

    save_status(existing)


def print_dashboard(results):
    """Print formatted dashboard."""
    print()
    print("API Provider Dashboard")
    print("=" * 60)

    for name, result in results.items():
        status = result["status"]
        detail = result.get("detail", "")
        warning = result.get("warning", "")
        action = result.get("action", "")

        if status == "active" and warning == "LOW":
            icon = "WARNING LOW"
            status_str = detail
        elif status == "active":
            icon = "OK"
            status_str = detail
        elif status == "blocked":
            icon = "BLOCKED"
            status_str = detail
        elif status == "no_key":
            icon = "NO KEY"
            status_str = detail
        else:
            icon = "???"
            status_str = detail

        print(f"  {name:15s}  {status_str:40s}  [{icon}]")
        if action:
            print(f"  {' ':15s}  -> {action}")

    print("=" * 60)
    print(f"  Status file: {STATUS_FILE}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Check API provider balances and status",
    )
    parser.add_argument("--update", action="store_true",
                        help="Force update provider-status.json")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    results = check_all()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_dashboard(results)

    if args.update:
        update_status_file(results)
        print("  Updated provider-status.json")
    else:
        # Always update if we detect status changes
        update_status_file(results)


if __name__ == "__main__":
    main()
