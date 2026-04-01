#!/usr/bin/env python3
"""
Bidirectional Sync — keeps Mac and EC2 in sync for both git and non-git files.

Architecture:
  - EC2 is canonical for RUNTIME state (pipeline.db, learned_preferences.json, .env)
  - Mac is canonical for DEVELOPMENT (code changes via git)
  - Git handles code sync (bidirectional push/pull)
  - SCP handles non-git files (bidirectional with "newer wins" + merge for .env)

Usage:
    python3 scripts/bidirectional_sync.py              # Full sync
    python3 scripts/bidirectional_sync.py --dry-run    # Preview only
    python3 scripts/bidirectional_sync.py --status     # Show sync state
    python3 scripts/bidirectional_sync.py --env-only   # Only sync .env files
    python3 scripts/bidirectional_sync.py --data-only  # Only sync data files
    python3 scripts/bidirectional_sync.py --git-only   # Only sync git

Shortcut:
    bash scripts/sync.sh                # Alias for full sync
    bash scripts/sync.sh --dry-run      # Preview
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────

EC2_HOST = "ec2-user@34.193.98.97"
EC2_KEY = os.path.expanduser("~/.ssh/marceau-ec2-key.pem")
SSH_OPTS = f"-i {EC2_KEY} -o ConnectTimeout=10 -o StrictHostKeyChecking=no"

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = REPO_ROOT / "projects" / "personal-assistant" / "logs"
LOG_FILE = LOG_DIR / "bidirectional_sync.log"
BACKUP_DIR = REPO_ROOT / ".sync-backups"

# Files to sync bidirectionally (non-git)
# Format: (mac_path_relative_to_repo, ec2_absolute_path, canonical_side)
# canonical_side: "ec2" = EC2 wins on conflict, "mac" = Mac wins, "newer" = newer wins
DATA_FILES = [
    (
        "projects/lead-generation/sales-pipeline/data/pipeline.db",
        "/home/clawdbot/dev-sandbox/projects/lead-generation/sales-pipeline/data/pipeline.db",
        "ec2",  # EC2 cron jobs write to this
    ),
    (
        "projects/personal-assistant/data/goals.json",
        "/home/clawdbot/dev-sandbox/projects/personal-assistant/data/goals.json",
        "newer",  # Could be updated from either side
    ),
    (
        "projects/personal-assistant/data/learned_preferences.json",
        "/home/clawdbot/dev-sandbox/projects/personal-assistant/data/learned_preferences.json",
        "ec2",  # outcome_learner writes on EC2
    ),
]

# .env files to merge (not overwrite — merge keys from both sides)
ENV_FILES = [
    (
        ".env",
        "/home/clawdbot/dev-sandbox/.env",
    ),
]

# PA handler files to sync Mac→EC2 (code deployment)
PA_HANDLER_FILES = [
    "projects/personal-assistant/src/clawdbot_handlers.py",
    "projects/personal-assistant/src/goal_manager.py",
    "projects/personal-assistant/src/goal_progress.py",
    "projects/personal-assistant/src/outcome_learner.py",
    "projects/personal-assistant/src/gmail_api.py",
]
EC2_PA_DIR = "/home/clawdbot/pa-handlers"


# ─── Utilities ───────────────────────────────────────────────────────────────

def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def ssh(cmd: str, timeout: int = 30, as_clawdbot: bool = True) -> tuple:
    """Run command on EC2. Returns (returncode, stdout, stderr).
    By default runs as clawdbot user for proper file ownership."""
    if as_clawdbot:
        wrapped = f"sudo -u clawdbot bash -c {repr(cmd)}"
    else:
        wrapped = cmd
    full_cmd = f"ssh {SSH_OPTS} {EC2_HOST} {repr(wrapped)}"
    try:
        r = subprocess.run(
            full_cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "SSH timeout"


def scp_to_ec2(local_path: str, remote_path: str) -> bool:
    """Copy file from Mac to EC2 (owned by clawdbot)."""
    cmd = f"scp {SSH_OPTS} -q {repr(local_path)} {EC2_HOST}:/tmp/_sync_tmp"
    r = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
    if r.returncode != 0:
        return False
    rc, _, _ = ssh(f"cp /tmp/_sync_tmp {remote_path}", as_clawdbot=True)
    return rc == 0


def scp_from_ec2(remote_path: str, local_path: str) -> bool:
    """Copy file from EC2 to Mac."""
    cmd = f"scp {SSH_OPTS} -q {EC2_HOST}:{remote_path} {repr(local_path)}"
    r = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
    return r.returncode == 0


def file_hash(path: str) -> str:
    """Get MD5 hash of a file."""
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except FileNotFoundError:
        return "MISSING"


def ec2_file_hash(path: str) -> str:
    """Get MD5 hash of a file on EC2."""
    rc, out, _ = ssh(f"md5sum {path} 2>/dev/null || echo MISSING")
    if "MISSING" in out or rc != 0:
        return "MISSING"
    return out.split()[0]


def ec2_file_mtime(path: str) -> int:
    """Get modification time of file on EC2."""
    rc, out, _ = ssh(f"stat -c %Y {path} 2>/dev/null || echo 0")
    try:
        return int(out)
    except ValueError:
        return 0


def mac_file_mtime(path: str) -> int:
    """Get modification time of file on Mac."""
    try:
        return int(os.path.getmtime(path))
    except FileNotFoundError:
        return 0


def backup_file(path: str, label: str):
    """Create timestamped backup before overwriting."""
    if not os.path.exists(path):
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = Path(path).name
    dest = BACKUP_DIR / f"{name}.{label}.{ts}"
    shutil.copy2(path, dest)


# ─── Sync Operations ────────────────────────────────────────────────────────

def sync_git(dry_run: bool = False) -> list:
    """Bidirectional git sync."""
    results = []

    # Check local status
    r = subprocess.run(
        "git status --porcelain", shell=True, capture_output=True, text=True, cwd=REPO_ROOT
    )
    local_dirty = bool(r.stdout.strip())
    if local_dirty:
        results.append(("git", "WARN", "Local has uncommitted changes — skipping git push"))

    # Pull from origin (safe)
    if dry_run:
        results.append(("git-pull", "DRY-RUN", "Would pull from origin/main"))
    else:
        r = subprocess.run(
            "git pull origin main --rebase --autostash",
            shell=True, capture_output=True, text=True, cwd=REPO_ROOT, timeout=60
        )
        if r.returncode == 0:
            output = r.stdout.strip()
            if "Already up to date" in output:
                results.append(("git-pull", "OK", "Already up to date"))
            else:
                results.append(("git-pull", "SYNCED", f"Pulled updates: {output[:100]}"))
        else:
            results.append(("git-pull", "ERROR", f"Pull failed: {r.stderr.strip()[:100]}"))

    # EC2 pull
    if dry_run:
        results.append(("ec2-git-pull", "DRY-RUN", "Would pull on EC2"))
    else:
        rc, out, err = ssh("cd /home/clawdbot/dev-sandbox && git pull origin main --rebase --autostash 2>&1", as_clawdbot=True)
        if rc == 0:
            if "Already up to date" in out:
                results.append(("ec2-git-pull", "OK", "EC2 already up to date"))
            else:
                results.append(("ec2-git-pull", "SYNCED", f"EC2 pulled: {out[:100]}"))
        else:
            results.append(("ec2-git-pull", "ERROR", f"EC2 pull failed: {out[:100]}"))

    return results


def sync_data_files(dry_run: bool = False) -> list:
    """Sync non-git data files bidirectionally."""
    results = []

    for mac_rel, ec2_path, canonical in DATA_FILES:
        mac_path = str(REPO_ROOT / mac_rel)
        name = Path(mac_rel).name

        mac_hash = file_hash(mac_path)
        ec2_hash = ec2_file_hash(ec2_path)

        # Already in sync
        if mac_hash == ec2_hash:
            results.append((name, "OK", "In sync"))
            continue

        # Determine direction
        if mac_hash == "MISSING" and ec2_hash != "MISSING":
            direction = "ec2→mac"
        elif ec2_hash == "MISSING" and mac_hash != "MISSING":
            direction = "mac→ec2"
        elif canonical == "ec2":
            direction = "ec2→mac"
        elif canonical == "mac":
            direction = "mac→ec2"
        elif canonical == "newer":
            mac_mt = mac_file_mtime(mac_path)
            ec2_mt = ec2_file_mtime(ec2_path)
            direction = "ec2→mac" if ec2_mt > mac_mt else "mac→ec2"
        else:
            direction = "ec2→mac"  # Default: EC2 canonical

        if dry_run:
            results.append((name, "DRY-RUN", f"Would sync {direction} (mac={mac_hash[:8]}, ec2={ec2_hash[:8]})"))
            continue

        # Execute sync
        if direction == "ec2→mac":
            backup_file(mac_path, "before-ec2-sync")
            os.makedirs(os.path.dirname(mac_path), exist_ok=True)
            ok = scp_from_ec2(ec2_path, mac_path)
            if ok:
                results.append((name, "SYNCED", f"{direction} (backed up old)"))
            else:
                results.append((name, "ERROR", f"Failed to copy {direction}"))
        else:  # mac→ec2
            ok = scp_to_ec2(mac_path, ec2_path)
            if ok:
                results.append((name, "SYNCED", f"{direction}"))
            else:
                results.append((name, "ERROR", f"Failed to copy {direction}"))

    return results


def sync_env_files(dry_run: bool = False) -> list:
    """Merge .env files — combine keys from both sides, EC2 wins on conflicts."""
    results = []

    for mac_rel, ec2_path in ENV_FILES:
        mac_path = str(REPO_ROOT / mac_rel)
        name = f".env ({mac_rel})"

        # Read Mac .env
        mac_vars = {}
        if os.path.exists(mac_path):
            with open(mac_path) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, _, val = line.partition("=")
                        mac_vars[key.strip()] = val.strip()

        # Read EC2 .env
        ec2_vars = {}
        rc, out, _ = ssh(f"cat {ec2_path} 2>/dev/null", as_clawdbot=True)
        if rc == 0:
            for line in out.splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    ec2_vars[key.strip()] = val.strip()

        if not mac_vars and not ec2_vars:
            results.append((name, "SKIP", "Both empty"))
            continue

        # Merge strategy: Mac wins for KEY VALUES (since Mac is where keys are
        # rotated and updated interactively). Both sides get all keys.
        # EC2-only keys (like HOME, PWD, REPO_ROOT) are kept as-is.
        merged = dict(ec2_vars)  # Start with EC2
        mac_only = set(mac_vars.keys()) - set(ec2_vars.keys())
        ec2_only = set(ec2_vars.keys()) - set(mac_vars.keys())
        conflicts = {k for k in mac_vars if k in ec2_vars and mac_vars[k] != ec2_vars[k]}

        # Mac wins on conflicts (Mac is where keys are rotated)
        # Exception: EC2 runtime vars (HOME, PWD, REPO_ROOT, GATEWAY_MODE) stay EC2
        ec2_runtime_vars = {"HOME", "PWD", "REPO_ROOT", "GATEWAY_MODE", "CLAWDBOT_ENV"}
        for k, v in mac_vars.items():
            if k not in ec2_runtime_vars:
                merged[k] = v

        # Keep EC2 runtime vars
        for k in ec2_runtime_vars:
            if k in ec2_vars:
                merged[k] = ec2_vars[k]

        changes = []
        if mac_only:
            changes.append(f"{len(mac_only)} Mac-only keys added to EC2")
        if ec2_only:
            changes.append(f"{len(ec2_only)} EC2-only keys added to Mac")
        if conflicts:
            real_conflicts = conflicts - ec2_runtime_vars
            if real_conflicts:
                changes.append(f"{len(real_conflicts)} conflicts (Mac wins — freshly rotated keys)")
            ec2_kept = conflicts & ec2_runtime_vars
            if ec2_kept:
                changes.append(f"{len(ec2_kept)} runtime vars kept from EC2")

        if not changes:
            results.append((name, "OK", "In sync"))
            continue

        if dry_run:
            results.append((name, "DRY-RUN", f"Would merge: {', '.join(changes)}"))
            if mac_only:
                results.append((name, "DRY-RUN", f"  Mac-only: {', '.join(sorted(mac_only))}"))
            if ec2_only:
                results.append((name, "DRY-RUN", f"  EC2-only: {', '.join(sorted(ec2_only))}"))
            if conflicts:
                results.append((name, "DRY-RUN", f"  Conflicts (EC2 wins): {', '.join(sorted(conflicts))}"))
            continue

        # Write merged to both
        backup_file(mac_path, "before-env-merge")
        env_content = "\n".join(f"{k}={v}" for k, v in sorted(merged.items())) + "\n"

        with open(mac_path, "w") as f:
            f.write(env_content)

        # Write to EC2 via SCP (reliable — avoids heredoc escaping issues)
        local_tmp = "/tmp/_sync_env_to_ec2"
        with open(local_tmp, "w") as f:
            f.write(env_content)
        scp_to_ec2(local_tmp, ec2_path)
        os.remove(local_tmp)

        # Also sync to .clawdbot/.env (add any missing keys)
        rc3, clawdbot_env, _ = ssh("cat /home/clawdbot/.clawdbot/.env 2>/dev/null", as_clawdbot=True)
        if rc3 == 0:
            clawdbot_vars = {}
            for line in clawdbot_env.splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    clawdbot_vars[key.strip()] = val.strip()

            # Add critical runtime keys if missing
            critical_keys = [
                "TELEGRAM_BOT_TOKEN", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN",
                "TWILIO_PHONE_NUMBER", "SMTP_USERNAME", "SMTP_PASSWORD",
                "XAI_API_KEY", "GROK_API_KEY", "STRIPE_SECRET_KEY",
                "ANTHROPIC_API_KEY", "HUNTER_API_KEY", "GOOGLE_PLACES_API_KEY",
                "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "TELEGRAM_CHAT_ID",
            ]
            added_to_clawdbot = []
            for k in critical_keys:
                if k in merged and k not in clawdbot_vars:
                    clawdbot_vars[k] = merged[k]
                    added_to_clawdbot.append(k)

            if added_to_clawdbot:
                clawdbot_content = "\n".join(f"{k}={v}" for k, v in sorted(clawdbot_vars.items())) + "\n"
                local_tmp2 = "/tmp/_sync_clawdbot_env"
                with open(local_tmp2, "w") as f:
                    f.write(clawdbot_content)
                scp_to_ec2(local_tmp2, "/home/clawdbot/.clawdbot/.env")
                os.remove(local_tmp2)
                changes.append(f"{len(added_to_clawdbot)} keys added to .clawdbot/.env")

        results.append((name, "SYNCED", "; ".join(changes)))

    return results


def sync_pa_handlers(dry_run: bool = False) -> list:
    """Sync PA handler code Mac→EC2 (code deployment)."""
    results = []
    changed = []

    for mac_rel in PA_HANDLER_FILES:
        mac_path = str(REPO_ROOT / mac_rel)
        name = Path(mac_rel).name
        ec2_path = f"{EC2_PA_DIR}/{name}"

        mac_hash = file_hash(mac_path)
        ec2_hash = ec2_file_hash(ec2_path)

        if mac_hash == ec2_hash:
            continue

        if mac_hash == "MISSING":
            continue

        if dry_run:
            results.append((name, "DRY-RUN", f"Would deploy mac→ec2 (mac={mac_hash[:8]}, ec2={ec2_hash[:8]})"))
            continue

        ok = scp_to_ec2(mac_path, ec2_path)
        if ok:
            changed.append(name)
        else:
            results.append((name, "ERROR", "Failed to deploy"))

    if changed and not dry_run:
        # Restart PA handlers via systemd
        ssh("sudo systemctl restart pa-handlers")
        results.append(("pa-handlers", "SYNCED", f"Deployed {', '.join(changed)} + restarted service"))
    elif not changed and not dry_run:
        results.append(("pa-handlers", "OK", "All handler files in sync"))

    return results


def show_status() -> list:
    """Show sync status without making changes."""
    results = []

    # Git status
    r = subprocess.run("git rev-parse --short HEAD", shell=True, capture_output=True, text=True, cwd=REPO_ROOT)
    mac_head = r.stdout.strip()
    rc, ec2_head, _ = ssh("cd /home/clawdbot/dev-sandbox && git rev-parse --short HEAD")
    ec2_head = ec2_head.strip()
    git_match = mac_head == ec2_head
    results.append(("git", "OK" if git_match else "DRIFT", f"Mac={mac_head} EC2={ec2_head}"))

    # Data files
    for mac_rel, ec2_path, canonical in DATA_FILES:
        mac_path = str(REPO_ROOT / mac_rel)
        name = Path(mac_rel).name
        mac_h = file_hash(mac_path)[:8]
        ec2_h = ec2_file_hash(ec2_path)[:8]
        match = mac_h == ec2_h
        results.append((name, "OK" if match else "DRIFT", f"Mac={mac_h} EC2={ec2_h} (canonical={canonical})"))

    # .env key count
    mac_env_count = 0
    if os.path.exists(str(REPO_ROOT / ".env")):
        with open(str(REPO_ROOT / ".env")) as f:
            mac_env_count = sum(1 for l in f if "=" in l and not l.startswith("#"))
    rc, out, _ = ssh("cat /home/clawdbot/dev-sandbox/.env 2>/dev/null | wc -l", as_clawdbot=True)
    ec2_env_count = int(out) if rc == 0 and out.isdigit() else 0
    env_match = mac_env_count == ec2_env_count
    results.append((".env", "OK" if env_match else "DRIFT", f"Mac={mac_env_count} keys, EC2={ec2_env_count} keys"))

    # PA handlers
    handler_drift = 0
    for mac_rel in PA_HANDLER_FILES:
        mac_path = str(REPO_ROOT / mac_rel)
        name = Path(mac_rel).name
        ec2_path = f"{EC2_PA_DIR}/{name}"
        if file_hash(mac_path) != ec2_file_hash(ec2_path):
            handler_drift += 1
    results.append(("pa-handlers", "OK" if handler_drift == 0 else "DRIFT", f"{handler_drift}/{len(PA_HANDLER_FILES)} files differ"))

    return results


# ─── Main ────────────────────────────────────────────────────────────────────

def print_results(results: list):
    """Pretty-print sync results."""
    if not results:
        return
    max_name = max(len(r[0]) for r in results)
    for name, status, detail in results:
        icon = {"OK": "+", "SYNCED": ">", "DRY-RUN": "~", "ERROR": "!", "WARN": "?", "DRIFT": "*", "SKIP": "-"}
        sym = icon.get(status, " ")
        print(f"  [{sym}] {name:<{max_name}}  {status:<8}  {detail}")


def main():
    parser = argparse.ArgumentParser(description="Bidirectional Mac <-> EC2 sync")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument("--status", action="store_true", help="Show sync status only")
    parser.add_argument("--env-only", action="store_true", help="Only sync .env files")
    parser.add_argument("--data-only", action="store_true", help="Only sync data files")
    parser.add_argument("--git-only", action="store_true", help="Only sync git")
    parser.add_argument("--no-git", action="store_true", help="Skip git sync")
    parser.add_argument("--no-restart", action="store_true", help="Skip PA handler restart")
    args = parser.parse_args()

    # Check EC2 connectivity
    rc, _, _ = ssh("echo ok", timeout=10)
    if rc != 0:
        log("Cannot reach EC2 — is the server running?", "ERROR")
        sys.exit(1)

    if args.status:
        print("\nSYNC STATUS:")
        print_results(show_status())
        return

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    log(f"Starting bidirectional sync ({mode})")
    print(f"\nBIDIRECTIONAL SYNC ({mode}):")

    all_results = []
    do_all = not (args.env_only or args.data_only or args.git_only)

    # 1. Git sync
    if (do_all or args.git_only) and not args.no_git:
        print("\n  GIT:")
        results = sync_git(args.dry_run)
        print_results(results)
        all_results.extend(results)

    # 2. Data files
    if do_all or args.data_only:
        print("\n  DATA FILES:")
        results = sync_data_files(args.dry_run)
        print_results(results)
        all_results.extend(results)

    # 3. .env merge
    if do_all or args.env_only:
        print("\n  ENV FILES:")
        results = sync_env_files(args.dry_run)
        print_results(results)
        all_results.extend(results)

    # 4. PA handlers (Mac→EC2 code deployment)
    if do_all and not args.no_restart:
        print("\n  PA HANDLERS:")
        results = sync_pa_handlers(args.dry_run)
        print_results(results)
        all_results.extend(results)

    # Summary
    errors = [r for r in all_results if r[1] == "ERROR"]
    synced = [r for r in all_results if r[1] == "SYNCED"]
    print(f"\n  SUMMARY: {len(synced)} synced, {len(errors)} errors")

    if errors:
        for name, _, detail in errors:
            log(f"ERROR: {name} — {detail}", "ERROR")

    log(f"Sync complete: {len(synced)} synced, {len(errors)} errors")


if __name__ == "__main__":
    main()
