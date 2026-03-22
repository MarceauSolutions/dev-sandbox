#!/bin/bash
# KeyVault — API Key Management SaaS
# Usage: ./scripts/api-key-manager.sh [--seed] [--seed-force] [--sync]

cd "$(dirname "$0")/.."

if [[ "$1" == "--seed" ]]; then
    echo "Seeding database..."
    python -m projects.shared.api-key-manager.src.seed
    exit 0
fi

if [[ "$1" == "--seed-force" ]]; then
    echo "Force re-seeding database..."
    python -m projects.shared.api-key-manager.src.seed --force
    exit 0
fi

if [[ "$1" == "--sync" ]]; then
    echo "Running environment sync check..."
    python -m projects.shared.api-key-manager.src.sync_checker
    exit 0
fi

# Check if already running
if lsof -i :8793 > /dev/null 2>&1; then
    echo "KeyVault already running"
    open "http://127.0.0.1:8793"
    exit 0
fi

# Seed if database doesn't exist
DB_PATH="projects/shared/api-key-manager/data/keyvault.db"
if [ ! -f "$DB_PATH" ]; then
    echo "First run — seeding database..."
    python -m projects.shared.api-key-manager.src.seed
fi

echo "Starting KeyVault → http://127.0.0.1:8793"
python -m projects.shared.api-key-manager.src.app &
sleep 2
open "http://127.0.0.1:8793"
