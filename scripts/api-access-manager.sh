#!/bin/bash
DIR="$(cd "$(dirname "$0")/../projects/marceau-solutions/digital/tools/api-access-manager" && pwd)"
cd "$DIR" || exit 1
lsof -ti:8791 | xargs kill -9 2>/dev/null
python app.py &
sleep 2
open "http://127.0.0.1:8791"
