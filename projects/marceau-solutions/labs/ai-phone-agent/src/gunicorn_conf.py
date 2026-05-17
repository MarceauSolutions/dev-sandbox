"""
Gunicorn config for the AI phone agent and the dashboard.

Usage on EC2:
    cd /home/clawdbot/dev-sandbox/projects/marceau-solutions/labs/ai-phone-agent/src
    gunicorn -c gunicorn_conf.py app:app          # phone agent (port 8795)
    gunicorn -c gunicorn_conf.py dashboard:app    # dashboard   (port 8796)

`bind` defaults to phone-agent port. Override with:
    BIND=0.0.0.0:8796 gunicorn -c gunicorn_conf.py dashboard:app

Workers: 3 (enough headroom for concurrent calls on a small EC2 box). Twilio
fires multiple webhooks during a single call — each must be served in parallel
or the call stalls.

Sync worker class is intentional: each Twilio webhook is short and synchronous
(no long-poll), and SQLite WAL mode handles concurrent worker writes safely.
"""

import os

bind = os.environ.get("BIND", "0.0.0.0:8795")
workers = int(os.environ.get("WEB_CONCURRENCY", "3"))
worker_class = "sync"
timeout = 60               # Twilio's webhook timeout is 15s; we set 60s headroom
graceful_timeout = 30
keepalive = 5
accesslog = "-"            # stdout (captured by journalctl)
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")
preload_app = True         # init DB once in master before forking workers
