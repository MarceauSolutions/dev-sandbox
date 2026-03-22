#!/usr/bin/env python3
"""
Environment Sync Tool — push Mac .env keys to EC2 environments.

Syncs all tracked API keys from Mac (source of truth) to EC2 Clawdbot and dev-sandbox envs.

Run: python -m projects.shared.api-key-manager.src.sync_env [--dry-run]
"""

import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

from .models import get_db

MAC_ENV_PATH = Path(__file__).parents[4] / ".env"

SSH_CMD = "ssh -i ~/.ssh/marceau-ec2-key.pem -o ConnectTimeout=10 ec2-user@34.193.98.97"

TARGETS = {
    "ec2-clawdbot": "/home/clawdbot/.clawdbot/.env",
    "ec2-dev-sandbox": "/home/clawdbot/dev-sandbox/.env",
}


def sync_env(dry_run: bool = False):
    conn = get_db()
    mac_env = dotenv_values(str(MAC_ENV_PATH))
    print(f"Loaded {len(mac_env)} vars from Mac .env")

    # Get out-of-sync keys per environment
    out_of_sync = conn.execute("""
        SELECT ess.*, ak.env_var_name, e.name as env_name
        FROM env_sync_status ess
        JOIN api_keys ak ON ess.api_key_id = ak.id
        JOIN environments e ON ess.environment_id = e.id
        WHERE ess.in_sync = 0
    """).fetchall()

    if not out_of_sync:
        print("All keys are in sync!")
        return

    # Group by environment
    by_env = {}
    for row in out_of_sync:
        env_name = row["env_name"]
        if env_name not in by_env:
            by_env[env_name] = []
        by_env[env_name].append(row["env_var_name"])

    for env_name, var_names in by_env.items():
        remote_path = TARGETS.get(env_name)
        if not remote_path:
            print(f"Skipping {env_name} — no target path configured")
            continue

        print(f"\n{'[DRY RUN] ' if dry_run else ''}Syncing {len(var_names)} keys to {env_name} ({remote_path}):")

        for var_name in var_names:
            mac_value = mac_env.get(var_name)
            if not mac_value:
                print(f"  SKIP {var_name} — not in Mac .env")
                continue

            # Escape special characters for sed
            escaped_value = mac_value.replace("/", "\\/").replace("&", "\\&").replace("%", "%%")

            print(f"  {'WOULD SYNC' if dry_run else 'SYNCING'}: {var_name}")

            if not dry_run:
                # Check if key exists in remote env
                check_cmd = f"{SSH_CMD} \"sudo grep -c '^{var_name}=' {remote_path}\""
                result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True, timeout=10)
                exists = result.stdout.strip() != "0"

                if exists:
                    # Update existing
                    sed_cmd = f"{SSH_CMD} \"sudo sed -i 's|^{var_name}=.*|{var_name}={mac_value}|' {remote_path}\""
                else:
                    # Append new
                    sed_cmd = f"{SSH_CMD} \"echo '{var_name}={mac_value}' | sudo tee -a {remote_path} > /dev/null\""

                result = subprocess.run(sed_cmd, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    print(f"    ERROR: {result.stderr.strip()}")
                else:
                    print(f"    OK")

    if not dry_run:
        # Restart Clawdbot to pick up new env
        print("\nRestarting Clawdbot to pick up new keys...")
        result = subprocess.run(
            f"{SSH_CMD} 'sudo systemctl restart clawdbot'",
            shell=True, capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            print("Clawdbot restarted successfully.")
        else:
            print(f"Warning: restart failed — {result.stderr.strip()}")

        # Re-run sync check to verify
        print("\nVerifying sync...")
        from .sync_checker import check_sync
        remaining = check_sync()
        if remaining == 0:
            print("\nAll keys now in sync!")
        else:
            print(f"\n{remaining} key(s) still out of sync — may need manual review.")

    conn.close()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    sync_env(dry_run=dry)
