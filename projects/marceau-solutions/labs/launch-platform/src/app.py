#!/usr/bin/env python3
"""
LaunchPad — Iterative Product Launch Platform
Flask backend: reads any product's launch/ directory and serves a unified dashboard.

Usage:
    python src/app.py --product dumbphone-lock
    python src/app.py --product dumbphone-lock --port 8765
"""

import os
import sys
import json
import io
import zipfile
import importlib.util
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request, send_file, abort
from dotenv import load_dotenv

# ─── Paths ────────────────────────────────────────────────────────────────────

APP_DIR   = Path(__file__).resolve().parent
TMPL_DIR  = APP_DIR.parent / "templates"
STATIC    = APP_DIR.parent / "static"
ROOT      = APP_DIR.parents[4]   # dev-sandbox root
LABS_DIR  = APP_DIR.parents[1]   # .../labs/

load_dotenv(ROOT / ".env")

app = Flask(__name__, template_folder=str(TMPL_DIR), static_folder=str(STATIC))

# ─── Product Registry ─────────────────────────────────────────────────────────

ACTIVE_PRODUCT = None   # set at startup via --product


def _find_products():
    """Scan labs/ for any directory with a launch/ subdir."""
    products = {}
    for candidate in LABS_DIR.iterdir():
        if not candidate.is_dir():
            continue
        launch_dir = candidate / "launch"
        if launch_dir.is_dir() and (launch_dir / "launch_state.json").exists():
            products[candidate.name] = {
                "id":           candidate.name,
                "label":        candidate.name.replace("-", " ").title(),
                "dir":          candidate,
                "launch_dir":   launch_dir,
                "manager_path": launch_dir / "launch_manager.py",
                "pipeline_path": launch_dir / "content_pipeline.py",
                "state_path":   launch_dir / "launch_state.json",
            }
    return products


def _get_product(product_id=None):
    products = _find_products()
    pid = product_id or ACTIVE_PRODUCT
    if pid and pid in products:
        return products[pid]
    # fallback: first available
    return next(iter(products.values()), None)


# ─── Loaders ─────────────────────────────────────────────────────────────────

def _load_pipeline(product):
    """Dynamically import content_pipeline.py for the given product."""
    path = product["pipeline_path"]
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("content_pipeline", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _read_state(product):
    try:
        return json.loads(product["state_path"].read_text())
    except Exception:
        return {}


def _write_state(product, state):
    product["state_path"].write_text(json.dumps(state, indent=2))


# ─── Phase Logic ──────────────────────────────────────────────────────────────

PHASES = [
    {"id": "preflight",          "label": "Pre-launch Checklist",    "order": 1},
    {"id": "organic_validation", "label": "48h Organic Validation",  "order": 2},
    {"id": "gate_evaluation",    "label": "Validation Gate",         "order": 3},
    {"id": "content_generation", "label": "Content Generation",      "order": 4},
    {"id": "paid_ads",           "label": "Paid Ad Phase",           "order": 5},
]

PHASE_ORDER = {p["id"]: p["order"] for p in PHASES}


def _phase_status(current_phase):
    """Return phases list with done/active/pending for each."""
    current_order = PHASE_ORDER.get(current_phase, 1)
    result = []
    for p in PHASES:
        if p["order"] < current_order:
            status = "done"
        elif p["order"] == current_order:
            status = "active"
        else:
            status = "pending"
        result.append({**p, "status": status})
    return result


# ─── Posting Schedule ─────────────────────────────────────────────────────────

POSTING_SCHEDULE = [
    {"order": 1,  "offset_h": 0,    "key": "reddit_nosurf"},
    {"order": 2,  "offset_h": 0.5,  "key": "twitter"},
    {"order": 3,  "offset_h": 1,    "key": "reddit_productivity"},
    {"order": 4,  "offset_h": 1.5,  "key": "instagram"},
    {"order": 5,  "offset_h": 2,    "key": "reddit_dm"},
    {"order": 6,  "offset_h": 2.5,  "key": "tiktok"},
    {"order": 7,  "offset_h": 3,    "key": "reddit_dumbphones"},
    {"order": 8,  "offset_h": 4,    "key": "hackernews"},
    {"order": 9,  "offset_h": 6,    "key": "reddit_getdisciplined"},
    {"order": 10, "offset_h": 0,    "key": "reddit_comments"},
]

AUTONOMY_LABELS = {
    1: "Manual",
    2: "Browser-assist",
    3: "Auto",
}

CONNECTION_KEYS = {
    "twitter":    ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"],
    "instagram":  ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ID"],
    "tiktok":     ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN"],
    "reddit":     ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME"],
    "hackernews": [],  # no API — always manual
    "reddit_comments": [],
}


def _platform_connection(ptype):
    keys = CONNECTION_KEYS.get(ptype, [])
    if not keys:
        return "manual"
    missing = [k for k in keys if not os.getenv(k)]
    if not missing:
        return "connected"
    # partial = some keys present (applied, waiting)
    present = [k for k in keys if os.getenv(k)]
    if present:
        return "pending"
    return "not_connected"


def _build_platforms(product, pipeline_mod, state):
    """Build enriched platform list with status, copy excerpt, image path."""
    platforms   = getattr(pipeline_mod, "PLATFORMS", {})
    done        = state.get("posts_completed", {})
    started_raw = state.get("validation_started")
    started_dt  = datetime.fromisoformat(started_raw) if started_raw else None

    result = []
    for entry in POSTING_SCHEDULE:
        key  = entry["key"]
        pdef = platforms.get(key, {})
        if not pdef:
            continue

        ptype = pdef.get("type", "")

        # timing
        if started_dt:
            post_time = started_dt + timedelta(hours=entry["offset_h"])
            ready     = datetime.now() >= post_time
            post_time_iso = post_time.isoformat()
        else:
            ready         = False
            post_time_iso = None

        # status
        if key in done:
            status = "done"
        elif ready:
            status = "ready"
        else:
            status = "scheduled"

        # copy excerpt
        copy_excerpt = ""
        copy_title   = ""
        try:
            title, body, _ = pipeline_mod.get_platform_copy(key)
            copy_title   = title or ""
            copy_excerpt = (body or "")[:300]
        except Exception:
            pass

        # image
        assets_dir = product["launch_dir"] / "assets"
        img_path   = assets_dir / f"{key}.png"
        has_image  = img_path.exists()

        # connection
        connection = _platform_connection(ptype)
        autonomy   = pdef.get("autonomy", 1)

        # override autonomy based on connection
        if connection in ("not_connected", "pending") and autonomy == 3:
            autonomy   = 1   # degrade to manual until keys arrive
            connection_note = "API key pending — manual until connected"
        else:
            connection_note = ""

        result.append({
            "key":            key,
            "order":          entry["order"],
            "label":          pdef.get("label", key),
            "type":           ptype,
            "status":         status,
            "autonomy":       autonomy,
            "autonomy_label": AUTONOMY_LABELS.get(autonomy, "Manual"),
            "connection":     connection,
            "connection_note": connection_note,
            "post_time":      post_time_iso,
            "copy_title":     copy_title,
            "copy_excerpt":   copy_excerpt,
            "has_image":      has_image,
            "image_style":    pdef.get("image_style"),
            "done_at":        done.get(key),
        })

    return result


# ─── Metrics ──────────────────────────────────────────────────────────────────

def _fetch_signups(product):
    """Call launch_manager status subprocess and parse JSON output, or return zeros."""
    manager = product.get("manager_path")
    if not manager or not manager.exists():
        return {"total": 0, "goal": 100, "by_source": {}, "velocity": 0}

    try:
        result = subprocess.run(
            [sys.executable, str(manager), "status", "--json"],
            capture_output=True, text=True, timeout=10,
            cwd=str(ROOT)
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            return data.get("metrics", {"total": 0, "goal": 100, "by_source": {}, "velocity": 0})
    except Exception:
        pass

    return {"total": 0, "goal": 100, "by_source": {}, "velocity": 0}


# ─── API: State ───────────────────────────────────────────────────────────────

@app.route("/api/state")
def api_state():
    product  = _get_product(request.args.get("product"))
    if not product:
        return jsonify({"error": "no product found"}), 404

    state   = _read_state(product)
    phases  = _phase_status(state.get("phase", "preflight"))

    # time remaining in 48h window
    started_raw = state.get("validation_started")
    time_remaining = None
    pct_elapsed    = 0
    if started_raw:
        started   = datetime.fromisoformat(started_raw)
        window    = timedelta(hours=48)
        elapsed   = datetime.now() - started
        remaining = window - elapsed
        if remaining.total_seconds() > 0:
            total_s         = window.total_seconds()
            elapsed_s       = min(elapsed.total_seconds(), total_s)
            pct_elapsed     = round(elapsed_s / total_s * 100, 1)
            h, rem          = divmod(int(remaining.total_seconds()), 3600)
            m               = rem // 60
            time_remaining  = f"{h}h {m}m"
        else:
            pct_elapsed    = 100
            time_remaining = "Window closed"

    return jsonify({
        "product":        product["id"],
        "product_label":  product["label"],
        "phase":          state.get("phase", "preflight"),
        "phases":         phases,
        "time_remaining": time_remaining,
        "pct_elapsed":    pct_elapsed,
        "gate_decision":  state.get("gate_decision"),
        "gate_decided_at": state.get("gate_decided_at"),
        "validation_started": started_raw,
        "notes":          state.get("notes", []),
    })


# ─── API: Metrics ─────────────────────────────────────────────────────────────

@app.route("/api/metrics")
def api_metrics():
    product = _get_product(request.args.get("product"))
    if not product:
        return jsonify({"error": "no product found"}), 404

    state    = _read_state(product)
    done     = state.get("posts_completed", {})
    pipeline = _load_pipeline(product)
    total_platforms = len(getattr(pipeline, "PLATFORMS", {})) if pipeline else 0

    signups  = _fetch_signups(product)

    return jsonify({
        "signups":        signups.get("total", 0),
        "goal":           signups.get("goal", 100),
        "by_source":      signups.get("by_source", {}),
        "velocity":       signups.get("velocity", 0),
        "posts_done":     len(done),
        "posts_total":    total_platforms,
        "milestones":     state.get("milestones_hit", []),
    })


# ─── API: Platforms ───────────────────────────────────────────────────────────

@app.route("/api/platforms")
def api_platforms():
    product  = _get_product(request.args.get("product"))
    if not product:
        return jsonify({"error": "no product found"}), 404

    pipeline = _load_pipeline(product)
    if not pipeline:
        return jsonify({"error": "content pipeline not found"}), 404

    state     = _read_state(product)
    platforms = _build_platforms(product, pipeline, state)

    return jsonify({"platforms": platforms})


# ─── API: Mark Post Done ──────────────────────────────────────────────────────

@app.route("/api/mark/<key>", methods=["POST"])
def api_mark(key):
    product = _get_product(request.args.get("product"))
    if not product:
        return jsonify({"error": "no product found"}), 404

    state = _read_state(product)
    done  = state.setdefault("posts_completed", {})
    done[key] = datetime.now().isoformat()
    _write_state(product, state)

    return jsonify({"ok": True, "key": key, "done_at": done[key]})


# ─── API: Unmark Post ─────────────────────────────────────────────────────────

@app.route("/api/unmark/<key>", methods=["POST"])
def api_unmark(key):
    product = _get_product(request.args.get("product"))
    if not product:
        return jsonify({"error": "no product found"}), 404

    state = _read_state(product)
    done  = state.get("posts_completed", {})
    done.pop(key, None)
    _write_state(product, state)

    return jsonify({"ok": True, "key": key})


# ─── API: Copy ────────────────────────────────────────────────────────────────

@app.route("/api/content/<key>/copy")
def api_copy(key):
    product  = _get_product(request.args.get("product"))
    if not product:
        return jsonify({"error": "no product found"}), 404

    pipeline = _load_pipeline(product)
    if not pipeline:
        return jsonify({"error": "pipeline not found"}), 404

    title, body, raw = pipeline.get_platform_copy(key)
    if not body and not raw:
        return jsonify({"error": "no copy found for key"}), 404

    platforms = getattr(pipeline, "PLATFORMS", {})
    pdef      = platforms.get(key, {})

    return jsonify({
        "key":   key,
        "label": pdef.get("label", key),
        "title": title or "",
        "body":  body or "",
        "raw":   raw or "",
    })


# ─── API: Image ───────────────────────────────────────────────────────────────

@app.route("/api/content/<key>/image")
def api_image(key):
    product = _get_product(request.args.get("product"))
    if not product:
        abort(404)

    img = product["launch_dir"] / "assets" / f"{key}.png"
    if img.exists():
        return send_file(str(img), mimetype="image/png")
    abort(404)


# ─── API: Download Zip ────────────────────────────────────────────────────────

@app.route("/api/content/<key>/download")
def api_download(key):
    product  = _get_product(request.args.get("product"))
    if not product:
        abort(404)

    pipeline = _load_pipeline(product)
    if not pipeline:
        abort(404)

    platforms = getattr(pipeline, "PLATFORMS", {})
    pdef      = platforms.get(key, {})
    if not pdef:
        abort(404)

    title, body, raw = pipeline.get_platform_copy(key)
    label            = pdef.get("label", key)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # copy.txt
        copy_content = ""
        if title:
            copy_content += f"TITLE:\n{title}\n\n"
        if body:
            copy_content += f"BODY:\n{body}\n"
        zf.writestr(f"{key}/copy.txt", copy_content)

        # raw.txt (full markdown copy)
        if raw:
            zf.writestr(f"{key}/raw.txt", raw)

        # utm_link.txt
        landing = getattr(pipeline, "LANDING_URL", "https://marceausolutions.com/dumbphone")
        utm = f"{landing}?utm_source={pdef.get('type','unknown')}&utm_medium=post&utm_campaign=launch"
        if pdef.get("subreddit"):
            utm = f"{landing}?utm_source=reddit&utm_medium=post&utm_campaign={pdef['subreddit']}"
        zf.writestr(f"{key}/utm_link.txt", utm)

        # instructions.txt
        instructions = _get_instructions(pdef)
        zf.writestr(f"{key}/instructions.txt", instructions)

        # image if available
        img = product["launch_dir"] / "assets" / f"{key}.png"
        if img.exists():
            zf.write(str(img), f"{key}/image.png")

    buf.seek(0)
    filename = f"{key}-post-package.zip"
    return send_file(buf, mimetype="application/zip",
                     as_attachment=True, download_name=filename)


def _get_instructions(pdef):
    ptype = pdef.get("type", "")
    label = pdef.get("label", "")
    if ptype == "twitter":
        return (
            "TWITTER/X THREAD — MANUAL POST STEPS:\n"
            "1. Open twitter.com/compose/tweet\n"
            "2. Paste Tweet 1 from copy.txt\n"
            "3. Click '+' to add next tweet in thread\n"
            "4. Repeat for all 9 tweets\n"
            "5. Post the entire thread at once\n"
            "6. Upload image.png as media on Tweet 1\n"
        )
    elif ptype == "reddit":
        sub = pdef.get("subreddit", "")
        return (
            f"REDDIT r/{sub} — MANUAL POST STEPS:\n"
            f"1. Go to reddit.com/r/{sub}/submit\n"
            "2. Select 'Text post'\n"
            "3. Paste TITLE from copy.txt into Title field\n"
            "4. Paste BODY from copy.txt into Body field\n"
            "5. Post (no image needed for text posts)\n"
            "6. Check back in 30 min to reply to any comments\n"
        )
    elif ptype == "instagram":
        return (
            "INSTAGRAM REEL — MANUAL POST STEPS:\n"
            "1. Record or upload a 15-30s screen recording of the app\n"
            "2. Open Instagram → + → Reel\n"
            "3. Upload your video\n"
            "4. Paste the caption from copy.txt\n"
            "5. Add trending audio from Reels library\n"
            "6. Post → share to Feed too\n"
            "7. Update link in bio → marceausolutions.com/links\n"
        )
    elif ptype == "tiktok":
        return (
            "TIKTOK — MANUAL POST STEPS:\n"
            "1. Record a 15-30s vertical video showing the app\n"
            "2. Open TikTok → + → upload video\n"
            "3. Paste caption from copy.txt\n"
            "4. Add relevant sounds from TikTok library\n"
            "5. Post with link in bio set to marceausolutions.com/links\n"
        )
    elif ptype == "hackernews":
        return (
            "HACKER NEWS — MANUAL POST STEPS:\n"
            "1. Go to news.ycombinator.com/submitlink\n"
            "2. Title: paste TITLE from copy.txt\n"
            "3. URL: leave blank (text post)\n"
            "4. In the text area: paste BODY from copy.txt\n"
            "5. Submit\n"
            "Note: HN ranks by engagement velocity. Post between 9am-12pm ET weekdays.\n"
        )
    elif ptype == "reddit_comments":
        return (
            "REDDIT COMMENTS — MANUAL POST STEPS:\n"
            "1. Search r/nosurf, r/digitalminimalism, r/productivity for recent threads\n"
            "   about 'screen time', 'app blocker', 'dumb phone'\n"
            "2. Use the comment templates from copy.txt — adapt naturally\n"
            "3. Post 1-2 comments per subreddit max (avoid spam flags)\n"
            "4. Reply to any responses within 2 hours\n"
        )
    return f"{label} — copy above, follow platform's standard posting procedure.\n"


# ─── API: Generate Image ──────────────────────────────────────────────────────

@app.route("/api/generate/<key>", methods=["POST"])
def api_generate(key):
    product  = _get_product(request.args.get("product"))
    if not product:
        return jsonify({"error": "no product found"}), 404

    pipeline = _load_pipeline(product)
    if not pipeline:
        return jsonify({"error": "pipeline not found"}), 404

    force = request.json.get("force", False) if request.is_json else False

    try:
        img_path = pipeline.generate_image(key, force=force)
        if img_path:
            return jsonify({"ok": True, "key": key, "image_path": img_path})
        else:
            return jsonify({"ok": False, "error": "generation failed or no style for this platform"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ─── API: Gate Evaluation ─────────────────────────────────────────────────────

@app.route("/api/gate", methods=["POST"])
def api_gate():
    product = _get_product(request.args.get("product"))
    if not product:
        return jsonify({"error": "no product found"}), 404

    try:
        result = subprocess.run(
            [sys.executable, str(product["manager_path"]), "gate", "--json"],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT)
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            return jsonify(data)
        else:
            return jsonify({"ok": False, "output": result.stdout, "error": result.stderr})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ─── API: Report ──────────────────────────────────────────────────────────────

@app.route("/api/report")
def api_report():
    product = _get_product(request.args.get("product"))
    if not product:
        return jsonify({"error": "no product found"}), 404

    try:
        result = subprocess.run(
            [sys.executable, str(product["manager_path"]), "report"],
            capture_output=True, text=True, timeout=60, cwd=str(ROOT)
        )
        # Find the generated PDF path in output
        for line in result.stdout.split("\n"):
            if ".pdf" in line.lower() and "/" in line:
                import re
                m = re.search(r"(/[^\s]+\.pdf)", line)
                if m:
                    pdf_path = Path(m.group(1))
                    if pdf_path.exists():
                        return send_file(str(pdf_path), mimetype="application/pdf",
                                         as_attachment=True,
                                         download_name=f"{product['id']}-launch-report.pdf")
        return jsonify({"ok": True, "output": result.stdout})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ─── API: Products List ───────────────────────────────────────────────────────

@app.route("/api/products")
def api_products():
    products = _find_products()
    return jsonify({
        "products": [{"id": k, "label": v["label"]} for k, v in products.items()],
        "active":   ACTIVE_PRODUCT,
    })


# ─── API: Connection Status ───────────────────────────────────────────────────

@app.route("/api/connections")
def api_connections():
    """Report which platform API credentials are configured."""
    connections = {}
    for ptype, keys in CONNECTION_KEYS.items():
        if not keys:
            connections[ptype] = {"status": "manual", "keys": []}
            continue
        missing = [k for k in keys if not os.getenv(k)]
        present = [k for k in keys if os.getenv(k)]
        if not missing:
            connections[ptype] = {"status": "connected", "keys": keys}
        elif present:
            connections[ptype] = {
                "status": "pending",
                "present": present,
                "missing": missing,
                "note": f"{len(missing)} key(s) missing — applied or waiting for approval"
            }
        else:
            connections[ptype] = {
                "status": "not_connected",
                "keys": keys,
                "note": "No credentials configured"
            }
    return jsonify({"connections": connections})


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    products = _find_products()
    return render_template("index.html",
                           products=list(products.values()),
                           active_product=ACTIVE_PRODUCT)


# ─── Entry ────────────────────────────────────────────────────────────────────

def main():
    global ACTIVE_PRODUCT

    parser = argparse.ArgumentParser(description="LaunchPad Web Server")
    parser.add_argument("--product", default=None, help="Product ID (e.g. dumbphone-lock)")
    parser.add_argument("--port",    type=int, default=8765)
    parser.add_argument("--host",    default="127.0.0.1")
    parser.add_argument("--debug",   action="store_true")
    args = parser.parse_args()

    if args.product:
        ACTIVE_PRODUCT = args.product
    else:
        # auto-detect first available
        products = _find_products()
        if products:
            ACTIVE_PRODUCT = next(iter(products))

    if not ACTIVE_PRODUCT:
        print("ERROR: No product found. Pass --product <name> or ensure launch_state.json exists.")
        sys.exit(1)

    print(f"\n  LaunchPad running → http://{args.host}:{args.port}")
    print(f"  Active product: {ACTIVE_PRODUCT}\n")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
