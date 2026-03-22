#!/bin/bash
# Marceau Sales Pipeline — Launch dashboard
cd "$(dirname "$0")/.."

if lsof -i :8785 > /dev/null 2>&1; then
    echo "Sales Pipeline already running"
    open "http://127.0.0.1:8785"
    exit 0
fi

echo "Starting Sales Pipeline → http://127.0.0.1:8785"
python -m projects.shared.sales-pipeline.src.app &
sleep 2
open "http://127.0.0.1:8785"
