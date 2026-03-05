#!/bin/bash
# backup-untracked.sh — Emergency backup of all uncommitted + untracked work
#
# Usage:
#   ./scripts/backup-untracked.sh              # Auto-named backup
#   ./scripts/backup-untracked.sh "my-label"   # Custom label
#   ./scripts/backup-untracked.sh --restore    # List available backups
#   ./scripts/backup-untracked.sh --restore <file.tar.gz>  # Restore a backup
#
# This creates a tarball in .deploy-backups/ containing every file that
# isn't committed — both untracked files and modified tracked files.
# Think of it as a "git stash" that includes untracked files and persists
# across sessions.
#
# WHEN TO USE:
#   - Before any deploy/publish operation
#   - Before running destructive git commands (reset, checkout --, clean)
#   - Any time agents are doing parallel work and you want a snapshot
#   - The deploy_website.sh script calls this automatically

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
BACKUP_DIR="$REPO_ROOT/.deploy-backups"
mkdir -p "$BACKUP_DIR"

# ============================================================
# Restore mode
# ============================================================
if [[ "${1:-}" == "--restore" ]]; then
    if [[ -n "${2:-}" ]]; then
        RESTORE_FILE="$2"
        if [[ ! -f "$RESTORE_FILE" ]]; then
            RESTORE_FILE="$BACKUP_DIR/$2"
        fi
        if [[ ! -f "$RESTORE_FILE" ]]; then
            echo "Error: $2 not found"
            exit 1
        fi
        echo "Restoring from $RESTORE_FILE ..."
        cd "$REPO_ROOT"
        tar xzf "$RESTORE_FILE"
        echo "Done. Files restored to working tree."
        exit 0
    fi

    echo "Available backups (newest first):"
    echo ""
    ls -lt "$BACKUP_DIR"/*.tar.gz 2>/dev/null | while read -r line; do
        file=$(echo "$line" | awk '{print $NF}')
        size=$(du -h "$file" | cut -f1)
        name=$(basename "$file")
        echo "  $name  ($size)"
    done
    echo ""
    echo "To restore: $0 --restore <filename>"
    exit 0
fi

# ============================================================
# Backup mode
# ============================================================
LABEL="${1:-snapshot}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup-${LABEL}-${TIMESTAMP}.tar.gz"

cd "$REPO_ROOT"

# Gather all files that aren't committed
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null || true)
MODIFIED=$(git diff --name-only 2>/dev/null || true)
STAGED=$(git diff --cached --name-only 2>/dev/null || true)

ALL_FILES=$(printf '%s\n%s\n%s' "$UNTRACKED" "$MODIFIED" "$STAGED" | sort -u | grep -v '^$' || true)

if [[ -z "$ALL_FILES" ]]; then
    echo "Nothing to backup — working tree is clean."
    exit 0
fi

FILE_COUNT=$(echo "$ALL_FILES" | wc -l | tr -d ' ')
echo "Backing up $FILE_COUNT uncommitted files..."

# Create the tarball
echo "$ALL_FILES" | tar czf "$BACKUP_FILE" -T - 2>/dev/null

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup created: $BACKUP_FILE ($SIZE)"
echo ""
echo "To restore: $0 --restore $BACKUP_FILE"

# Prune old backups (keep last 20)
ls -t "$BACKUP_DIR"/backup-*.tar.gz 2>/dev/null | tail -n +21 | xargs rm -f 2>/dev/null || true
