"""ClaimBack — Medical Billing Dispute Platform.

AI-powered web app that automates medical billing disputes and insurance claim denials.
Launch: ./scripts/claim-back.sh or python src/app.py
URL: http://127.0.0.1:8790
"""

import os
import sys
import json
import sqlite3

# Ensure src/ is on the path for sibling imports
sys.path.insert(0, os.path.dirname(__file__))
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, send_file, session
)
from werkzeug.utils import secure_filename

# Project paths
PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DISPUTES_DIR = DATA_DIR / "disputes"
DB_PATH = DATA_DIR / "claimback.db"

# Ensure directories exist
for d in [DATA_DIR, UPLOAD_DIR, DISPUTES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = Flask(
    __name__,
    template_folder=str(PROJECT_DIR / "templates"),
    static_folder=str(PROJECT_DIR / "static"),
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "claimback-dev-key-change-in-prod")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "tiff", "bmp", "webp"}

DISPUTE_TYPES = {
    "insurance_denial": {
        "name": "Insurance Claim Denial",
        "icon": "shield-x",
        "desc": "Your insurance company denied a claim. We'll help you appeal.",
        "color": "#ef4444",
    },
    "billing_error": {
        "name": "Billing Error",
        "icon": "calculator",
        "desc": "Incorrect charges, duplicate billing, or wrong amounts.",
        "color": "#f59e0b",
    },
    "surprise_bill": {
        "name": "Surprise Bill",
        "icon": "alert-triangle",
        "desc": "Unexpected out-of-network charges at an in-network facility.",
        "color": "#8b5cf6",
    },
    "balance_billing": {
        "name": "Balance Billing",
        "icon": "scale",
        "desc": "Provider billing you beyond what insurance allowed.",
        "color": "#3b82f6",
    },
    "service_not_rendered": {
        "name": "Service Not Rendered",
        "icon": "x-circle",
        "desc": "Charged for services you never received.",
        "color": "#ec4899",
    },
    "wrong_code": {
        "name": "Wrong Billing Code",
        "icon": "code",
        "desc": "Incorrect CPT or diagnosis codes on your bill.",
        "color": "#06b6d4",
    },
}

DISPUTE_STATUSES = {
    "intake": "Gathering Information",
    "analyzing": "AI Analyzing",
    "review": "Review Strategy",
    "letters_ready": "Letters Ready",
    "filed": "Dispute Filed",
    "appealing": "Appeal In Progress",
    "escalated": "Escalated",
    "won": "Won",
    "lost": "Denied — Escalate?",
}


# ── Database ──────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS disputes (
            id TEXT PRIMARY KEY,
            dispute_type TEXT NOT NULL,
            status TEXT DEFAULT 'intake',
            title TEXT,
            provider_name TEXT,
            insurance_company TEXT,
            claim_number TEXT,
            date_of_service TEXT,
            billed_amount REAL,
            insurance_paid REAL,
            patient_responsibility REAL,
            denial_reason TEXT,
            state TEXT,
            insurance_type TEXT,
            description TEXT,
            ai_analysis TEXT,
            strategy TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            deadline_date TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            dispute_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            doc_type TEXT,
            uploaded_at TEXT DEFAULT (datetime('now')),
            extracted_text TEXT,
            FOREIGN KEY (dispute_id) REFERENCES disputes(id)
        );

        CREATE TABLE IF NOT EXISTS generated_letters (
            id TEXT PRIMARY KEY,
            dispute_id TEXT NOT NULL,
            letter_type TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (dispute_id) REFERENCES disputes(id)
        );

        CREATE TABLE IF NOT EXISTS timeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dispute_id TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_text TEXT NOT NULL,
            evidence_ref TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (dispute_id) REFERENCES disputes(id)
        );
    """)
    conn.commit()
    conn.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Routes ────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    conn = get_db()
    disputes = conn.execute(
        "SELECT * FROM disputes ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()

    stats = {
        "total": len(disputes),
        "active": sum(1 for d in disputes if d["status"] not in ("won", "lost")),
        "won": sum(1 for d in disputes if d["status"] == "won"),
        "total_disputed": sum(d["billed_amount"] or 0 for d in disputes),
        "total_saved": sum(
            (d["billed_amount"] or 0) - (d["patient_responsibility"] or 0)
            for d in disputes if d["status"] == "won"
        ),
    }

    return render_template("dashboard.html",
                           disputes=disputes,
                           stats=stats,
                           statuses=DISPUTE_STATUSES,
                           types=DISPUTE_TYPES)


@app.route("/new", methods=["GET"])
def new_dispute():
    return render_template("new_dispute.html", types=DISPUTE_TYPES)


@app.route("/new", methods=["POST"])
def create_dispute():
    dispute_id = str(uuid.uuid4())[:8]
    dispute_type = request.form.get("dispute_type")

    if dispute_type not in DISPUTE_TYPES:
        flash("Invalid dispute type.", "error")
        return redirect(url_for("new_dispute"))

    conn = get_db()
    conn.execute("""
        INSERT INTO disputes (id, dispute_type, title, status)
        VALUES (?, ?, ?, 'intake')
    """, (dispute_id, dispute_type, f"New {DISPUTE_TYPES[dispute_type]['name']}"))
    conn.commit()
    conn.close()

    # Create dispute folder
    (DISPUTES_DIR / dispute_id).mkdir(exist_ok=True)

    return redirect(url_for("dispute_intake", dispute_id=dispute_id))


@app.route("/dispute/<dispute_id>/intake", methods=["GET", "POST"])
def dispute_intake(dispute_id):
    conn = get_db()
    dispute = conn.execute("SELECT * FROM disputes WHERE id = ?", (dispute_id,)).fetchone()
    if not dispute:
        flash("Dispute not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        # Calculate deadline based on dispute type
        deadline = None
        dos = request.form.get("date_of_service")
        if dos:
            try:
                dos_date = datetime.strptime(dos, "%Y-%m-%d")
                if dispute["dispute_type"] == "insurance_denial":
                    deadline = (dos_date + timedelta(days=180)).strftime("%Y-%m-%d")
                elif dispute["dispute_type"] == "surprise_bill":
                    deadline = (dos_date + timedelta(days=120)).strftime("%Y-%m-%d")
                else:
                    deadline = (dos_date + timedelta(days=365)).strftime("%Y-%m-%d")
            except ValueError:
                pass

        conn.execute("""
            UPDATE disputes SET
                title = ?,
                provider_name = ?,
                insurance_company = ?,
                claim_number = ?,
                date_of_service = ?,
                billed_amount = ?,
                insurance_paid = ?,
                patient_responsibility = ?,
                denial_reason = ?,
                state = ?,
                insurance_type = ?,
                description = ?,
                deadline_date = ?,
                status = 'intake',
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            request.form.get("title") or f"{DISPUTE_TYPES[dispute['dispute_type']]['name']}",
            request.form.get("provider_name"),
            request.form.get("insurance_company"),
            request.form.get("claim_number"),
            request.form.get("date_of_service"),
            float(request.form.get("billed_amount") or 0),
            float(request.form.get("insurance_paid") or 0),
            float(request.form.get("patient_responsibility") or 0),
            request.form.get("denial_reason"),
            request.form.get("state"),
            request.form.get("insurance_type"),
            request.form.get("description"),
            deadline,
            dispute_id,
        ))
        conn.commit()
        conn.close()

        return redirect(url_for("dispute_documents", dispute_id=dispute_id))

    conn.close()
    us_states = [
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
        "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
        "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
        "VA","WA","WV","WI","WY","DC"
    ]
    return render_template("intake_form.html",
                           dispute=dispute,
                           types=DISPUTE_TYPES,
                           us_states=us_states)


@app.route("/dispute/<dispute_id>/documents", methods=["GET", "POST"])
def dispute_documents(dispute_id):
    conn = get_db()
    dispute = conn.execute("SELECT * FROM disputes WHERE id = ?", (dispute_id,)).fetchone()
    if not dispute:
        flash("Dispute not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        files = request.files.getlist("documents")
        doc_type = request.form.get("doc_type", "other")

        for f in files:
            if f and f.filename and allowed_file(f.filename):
                doc_id = str(uuid.uuid4())[:8]
                ext = f.filename.rsplit(".", 1)[1].lower()
                safe_name = f"{doc_id}.{ext}"
                save_path = DISPUTES_DIR / dispute_id / safe_name
                f.save(str(save_path))

                conn.execute("""
                    INSERT INTO documents (id, dispute_id, filename, original_name, doc_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (doc_id, dispute_id, safe_name, f.filename, doc_type))

        conn.commit()
        flash(f"Uploaded {len(files)} document(s).", "success")

    documents = conn.execute(
        "SELECT * FROM documents WHERE dispute_id = ? ORDER BY uploaded_at",
        (dispute_id,)
    ).fetchall()
    conn.close()

    doc_types = [
        ("bill", "Medical Bill"),
        ("eob", "Explanation of Benefits (EOB)"),
        ("denial_letter", "Denial Letter"),
        ("insurance_card", "Insurance Card"),
        ("medical_records", "Medical Records"),
        ("correspondence", "Correspondence"),
        ("other", "Other"),
    ]

    return render_template("documents.html",
                           dispute=dispute,
                           documents=documents,
                           doc_types=doc_types,
                           types=DISPUTE_TYPES)


@app.route("/dispute/<dispute_id>/analyze", methods=["POST"])
def analyze_dispute(dispute_id):
    """Trigger AI analysis of the dispute."""
    conn = get_db()
    dispute = conn.execute("SELECT * FROM disputes WHERE id = ?", (dispute_id,)).fetchone()
    if not dispute:
        return jsonify({"error": "Dispute not found"}), 404

    conn.execute(
        "UPDATE disputes SET status = 'analyzing', updated_at = datetime('now') WHERE id = ?",
        (dispute_id,)
    )
    conn.commit()

    # Import and run analysis
    try:
        from ai_analyzer import analyze_dispute as run_analysis
        analysis = run_analysis(dict(dispute))
        conn.execute(
            "UPDATE disputes SET ai_analysis = ?, status = 'review', updated_at = datetime('now') WHERE id = ?",
            (json.dumps(analysis), dispute_id)
        )
        conn.commit()
    except Exception as e:
        conn.execute(
            "UPDATE disputes SET status = 'intake', updated_at = datetime('now') WHERE id = ?",
            (dispute_id,)
        )
        conn.commit()
        conn.close()
        flash(f"Analysis error: {str(e)}", "error")
        return redirect(url_for("dispute_documents", dispute_id=dispute_id))

    conn.close()
    return redirect(url_for("dispute_review", dispute_id=dispute_id))


@app.route("/dispute/<dispute_id>/review")
def dispute_review(dispute_id):
    conn = get_db()
    dispute = conn.execute("SELECT * FROM disputes WHERE id = ?", (dispute_id,)).fetchone()
    documents = conn.execute(
        "SELECT * FROM documents WHERE dispute_id = ?", (dispute_id,)
    ).fetchall()
    letters = conn.execute(
        "SELECT * FROM generated_letters WHERE dispute_id = ? ORDER BY created_at",
        (dispute_id,)
    ).fetchall()
    conn.close()

    if not dispute:
        flash("Dispute not found.", "error")
        return redirect(url_for("dashboard"))

    analysis = {}
    if dispute["ai_analysis"]:
        try:
            analysis = json.loads(dispute["ai_analysis"])
        except json.JSONDecodeError:
            pass

    return render_template("review.html",
                           dispute=dispute,
                           analysis=analysis,
                           documents=documents,
                           letters=letters,
                           types=DISPUTE_TYPES,
                           statuses=DISPUTE_STATUSES)


@app.route("/dispute/<dispute_id>/generate-letters", methods=["POST"])
def generate_letters(dispute_id):
    """Generate dispute/appeal letters using AI."""
    conn = get_db()
    dispute = conn.execute("SELECT * FROM disputes WHERE id = ?", (dispute_id,)).fetchone()
    if not dispute:
        return jsonify({"error": "Dispute not found"}), 404

    try:
        from letter_generator import generate_dispute_letters
        letters = generate_dispute_letters(dict(dispute))

        for letter_type, content in letters.items():
            letter_id = str(uuid.uuid4())[:8]
            conn.execute("""
                INSERT INTO generated_letters (id, dispute_id, letter_type, content)
                VALUES (?, ?, ?, ?)
            """, (letter_id, dispute_id, letter_type, content))

        conn.execute(
            "UPDATE disputes SET status = 'letters_ready', updated_at = datetime('now') WHERE id = ?",
            (dispute_id,)
        )
        conn.commit()
        flash("Letters generated successfully.", "success")
    except Exception as e:
        flash(f"Letter generation error: {str(e)}", "error")

    conn.close()
    return redirect(url_for("dispute_review", dispute_id=dispute_id))


@app.route("/dispute/<dispute_id>/delete", methods=["POST"])
def delete_dispute(dispute_id):
    conn = get_db()
    conn.execute("DELETE FROM documents WHERE dispute_id = ?", (dispute_id,))
    conn.execute("DELETE FROM generated_letters WHERE dispute_id = ?", (dispute_id,))
    conn.execute("DELETE FROM timeline_events WHERE dispute_id = ?", (dispute_id,))
    conn.execute("DELETE FROM disputes WHERE id = ?", (dispute_id,))
    conn.commit()
    conn.close()

    # Remove dispute folder
    dispute_dir = DISPUTES_DIR / dispute_id
    if dispute_dir.exists():
        import shutil
        shutil.rmtree(str(dispute_dir))

    flash("Dispute deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/api/stats")
def api_stats():
    conn = get_db()
    disputes = conn.execute("SELECT * FROM disputes").fetchall()
    conn.close()
    return jsonify({
        "total_disputes": len(disputes),
        "active": sum(1 for d in disputes if d["status"] not in ("won", "lost")),
        "won": sum(1 for d in disputes if d["status"] == "won"),
        "total_disputed": sum(d["billed_amount"] or 0 for d in disputes),
    })


# ── Main ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("\n  ClaimBack — Medical Billing Dispute Platform")
    print("  ─────────────────────────────────────────────")
    print("  http://127.0.0.1:8790\n")
    app.run(host="127.0.0.1", port=8790, debug=True)
