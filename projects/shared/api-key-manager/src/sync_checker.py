#!/usr/bin/env python3
"""
Environment Sync Checker — compares API keys across Mac and EC2 environments.

Reads .env files locally and via SSH, compares values (hashed, not stored),
and updates the sync status in the database.

Run: python -m projects.shared.api-key-manager.src.sync_checker
"""

import hashlib
import os
import subprocess
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values

from .models import get_db


MAC_ENV_PATH = Path(__file__).parents[4] / ".env"  # dev-sandbox/.env

EC2_ENVS = {
    "ec2-clawdbot": "/home/clawdbot/.clawdbot/.env",
    "ec2-dev-sandbox": "/home/clawdbot/dev-sandbox/.env",
}

SSH_CMD = "ssh -i ~/.ssh/marceau-ec2-key.pem -o ConnectTimeout=10 ec2-user@34.193.98.97"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _read_remote_env(remote_path: str) -> dict:
    """Read a remote .env file via SSH and return key-value dict."""
    try:
        result = subprocess.run(
            f"{SSH_CMD} 'sudo cat {remote_path}'",
            shell=True, capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            print(f"  Warning: Could not read {remote_path}: {result.stderr.strip()}")
            return {}
        env = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
        return env
    except subprocess.TimeoutExpired:
        print(f"  Warning: SSH timeout reading {remote_path}")
        return {}


def check_sync():
    """Compare Mac .env against all EC2 environments and update database."""
    conn = get_db()

    # Load Mac env (source of truth)
    mac_env = dotenv_values(str(MAC_ENV_PATH))
    print(f"Loaded {len(mac_env)} vars from Mac .env")

    # Get all tracked API key env var names
    tracked_keys = conn.execute("""
        SELECT ak.id, ak.env_var_name, s.name as service_name
        FROM api_keys ak JOIN services s ON ak.service_id = s.id
        WHERE ak.status IN ('active', 'expired')
        AND ak.key_type NOT IN ('config')
    """).fetchall()

    # Get environment IDs
    envs = {row["name"]: row["id"] for row in conn.execute("SELECT id, name FROM environments").fetchall()}

    out_of_sync_count = 0

    for env_name, remote_path in EC2_ENVS.items():
        env_id = envs.get(env_name)
        if not env_id:
            continue

        print(f"\nChecking {env_name} ({remote_path})...")
        remote_env = _read_remote_env(remote_path)
        if not remote_env:
            print(f"  Skipped — could not read remote env")
            continue

        for key_row in tracked_keys:
            var_name = key_row["env_var_name"]
            mac_value = mac_env.get(var_name, "")
            remote_value = remote_env.get(var_name, "")

            in_sync = 1 if mac_value == remote_value else 0
            notes = None
            if not mac_value:
                notes = "Not in Mac .env"
                in_sync = 1  # nothing to sync
            elif not remote_value:
                notes = "Missing from remote env"
                in_sync = 0
            elif not in_sync:
                notes = f"Mac hash: {_hash(mac_value)}, Remote hash: {_hash(remote_value)}"

            if not in_sync:
                out_of_sync_count += 1
                print(f"  OUT OF SYNC: {var_name} ({key_row['service_name']})")

            conn.execute("""
                INSERT INTO env_sync_status (api_key_id, environment_id, in_sync, last_checked_at, notes)
                VALUES (?, ?, ?, datetime('now'), ?)
                ON CONFLICT(api_key_id, environment_id) DO UPDATE SET
                    in_sync = excluded.in_sync,
                    last_checked_at = excluded.last_checked_at,
                    notes = excluded.notes
            """, (key_row["id"], env_id, in_sync, notes))

        conn.commit()
        print(f"  Checked {len(tracked_keys)} keys against {env_name}")

    print(f"\nSync check complete. {out_of_sync_count} key(s) out of sync.")
    conn.close()
    return out_of_sync_count


if __name__ == "__main__":
    check_sync()
