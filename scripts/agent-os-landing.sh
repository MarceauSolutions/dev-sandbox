#!/bin/bash
# Launch AgentOS landing page
PORT=8795
echo "Opening AgentOS landing page at http://127.0.0.1:$PORT"
cd "$(dirname "$0")/../projects/marceau-solutions/labs/agent-os/landing-page"
open "http://127.0.0.1:$PORT"
python3 -m http.server $PORT
