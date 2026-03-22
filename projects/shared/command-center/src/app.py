#!/usr/bin/env python3
"""
Marceau Accountability Engine — Production Dashboard

90-day execution tracker with real-time metrics, streak tracking,
goal progress visualization, and health-aware coaching.

http://127.0.0.1:8780 (local) | https://accountability.marceausolutions.com (production)
"""

import os
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from .data import get_dashboard_data, get_context, TARGETS, GOALS
from .ui import render_dashboard, render_landing

app = FastAPI(title="Marceau Accountability Engine", version="2.0.0")
PORT = int(os.getenv("ACCOUNTABILITY_PORT", "8780"))


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    try:
        data = get_dashboard_data()
        return render_dashboard(data)
    except Exception as e:
        return render_dashboard(None, error=str(e))


@app.get("/api/data")
async def api_data():
    try:
        data = get_dashboard_data()
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "accountability-engine", "version": "2.0.0"}


if __name__ == "__main__":
    print(f"\n  Marceau Accountability Engine → http://127.0.0.1:{PORT}\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
