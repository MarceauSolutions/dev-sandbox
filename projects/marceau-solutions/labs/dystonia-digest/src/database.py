"""SQLite database layer for Dystonia Research Digest."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dystonia_digest.db"


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS digests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT NOT NULL,
            days_back INTEGER DEFAULT 7,
            total_papers INTEGER DEFAULT 0,
            categories_with_results INTEGER DEFAULT 0,
            email_sent BOOLEAN DEFAULT FALSE,
            pdf_path TEXT,
            html_content TEXT,
            status TEXT DEFAULT 'running',
            error_message TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            digest_id INTEGER REFERENCES digests(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            authors TEXT,
            abstract TEXT,
            journal TEXT,
            pub_date TEXT,
            pmid TEXT,
            doi TEXT,
            url TEXT,
            source TEXT,
            category TEXT,
            citations INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            label TEXT NOT NULL,
            enabled BOOLEAN DEFAULT TRUE,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS seen_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT UNIQUE NOT NULL,
            first_seen_date TEXT,
            digest_id INTEGER REFERENCES digests(id)
        );

        CREATE INDEX IF NOT EXISTS idx_papers_digest ON papers(digest_id);
        CREATE INDEX IF NOT EXISTS idx_papers_category ON papers(category);
        CREATE INDEX IF NOT EXISTS idx_seen_identifier ON seen_papers(identifier);
    """)
    conn.commit()
    conn.close()


# ── Digest CRUD ──────────────────────────────────────────────────────────────

def create_digest(days_back: int = 7) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO digests (run_date, days_back, status) VALUES (?, ?, 'running')",
        (datetime.now().isoformat(), days_back),
    )
    digest_id = cur.lastrowid
    conn.commit()
    conn.close()
    return digest_id


def update_digest(digest_id: int, **kwargs):
    conn = get_db()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [digest_id]
    conn.execute(f"UPDATE digests SET {sets} WHERE id = ?", vals)
    conn.commit()
    conn.close()


def get_digest(digest_id: int) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM digests WHERE id = ?", (digest_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_digests(limit: int = 50, offset: int = 0) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM digests ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_digest_count() -> int:
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM digests").fetchone()[0]
    conn.close()
    return count


# ── Paper CRUD ───────────────────────────────────────────────────────────────

def save_papers(digest_id: int, papers_by_category: dict):
    conn = get_db()
    for category, papers in papers_by_category.items():
        for p in papers:
            conn.execute(
                """INSERT INTO papers
                   (digest_id, title, authors, abstract, journal, pub_date,
                    pmid, doi, url, source, category, citations)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    digest_id,
                    p.get("title", ""),
                    json.dumps(p.get("authors", [])),
                    p.get("abstract", ""),
                    p.get("journal", ""),
                    p.get("date", ""),
                    p.get("pmid", ""),
                    p.get("doi", ""),
                    p.get("url", ""),
                    p.get("source", ""),
                    category,
                    p.get("citations", 0),
                ),
            )
            # Track for cross-run dedup
            identifier = p.get("doi") or p.get("pmid") or p["title"].lower()[:80]
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO seen_papers (identifier, first_seen_date, digest_id) VALUES (?, ?, ?)",
                    (identifier, datetime.now().isoformat(), digest_id),
                )
            except sqlite3.IntegrityError:
                pass
    conn.commit()
    conn.close()


def get_papers_for_digest(digest_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM papers WHERE digest_id = ? ORDER BY category, id",
        (digest_id,),
    ).fetchall()
    conn.close()
    papers = []
    for r in rows:
        d = dict(r)
        try:
            d["authors"] = json.loads(d["authors"]) if d["authors"] else []
        except (json.JSONDecodeError, TypeError):
            d["authors"] = []
        papers.append(d)
    return papers


def get_papers_by_category(digest_id: int) -> dict:
    papers = get_papers_for_digest(digest_id)
    by_cat = {}
    for p in papers:
        cat = p.get("category", "Uncategorized")
        by_cat.setdefault(cat, []).append(p)
    return by_cat


def get_paper(paper_id: int) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["authors"] = json.loads(d["authors"]) if d["authors"] else []
    except (json.JSONDecodeError, TypeError):
        d["authors"] = []
    return d


def search_papers(query: str, limit: int = 50) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        """SELECT p.*, d.run_date FROM papers p
           JOIN digests d ON d.id = p.digest_id
           WHERE p.title LIKE ? OR p.abstract LIKE ? OR p.category LIKE ?
           ORDER BY p.id DESC LIMIT ?""",
        (f"%{query}%", f"%{query}%", f"%{query}%", limit),
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        try:
            d["authors"] = json.loads(d["authors"]) if d["authors"] else []
        except (json.JSONDecodeError, TypeError):
            d["authors"] = []
        results.append(d)
    return results


def get_total_paper_count() -> int:
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    conn.close()
    return count


def get_total_unique_paper_count() -> int:
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM seen_papers").fetchone()[0]
    conn.close()
    return count


# ── Category CRUD ────────────────────────────────────────────────────────────

def seed_categories(search_queries: list[tuple]):
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if existing == 0:
        for query, label in search_queries:
            conn.execute(
                "INSERT INTO categories (query, label) VALUES (?, ?)",
                (query, label),
            )
        conn.commit()
    conn.close()


def get_categories() -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM categories ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_enabled_categories() -> list[tuple]:
    conn = get_db()
    rows = conn.execute(
        "SELECT query, label FROM categories WHERE enabled = TRUE ORDER BY id"
    ).fetchall()
    conn.close()
    return [(r["query"], r["label"]) for r in rows]


def add_category(query: str, label: str) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO categories (query, label) VALUES (?, ?)", (query, label)
    )
    cat_id = cur.lastrowid
    conn.commit()
    conn.close()
    return cat_id


def toggle_category(cat_id: int):
    conn = get_db()
    conn.execute(
        "UPDATE categories SET enabled = NOT enabled WHERE id = ?", (cat_id,)
    )
    conn.commit()
    conn.close()


def delete_category(cat_id: int):
    conn = get_db()
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()


# ── Stats ────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    conn = get_db()
    total_digests = conn.execute("SELECT COUNT(*) FROM digests WHERE status = 'completed'").fetchone()[0]
    total_papers = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    unique_papers = conn.execute("SELECT COUNT(*) FROM seen_papers").fetchone()[0]
    last_run = conn.execute(
        "SELECT * FROM digests ORDER BY id DESC LIMIT 1"
    ).fetchone()
    top_categories = conn.execute(
        """SELECT category, COUNT(*) as cnt FROM papers
           GROUP BY category ORDER BY cnt DESC LIMIT 5"""
    ).fetchall()
    conn.close()
    return {
        "total_digests": total_digests,
        "total_papers": total_papers,
        "unique_papers": unique_papers,
        "last_run": dict(last_run) if last_run else None,
        "top_categories": [dict(r) for r in top_categories],
    }
