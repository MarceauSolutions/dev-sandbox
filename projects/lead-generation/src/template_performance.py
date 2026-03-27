#!/usr/bin/env python3
"""
template_performance.py — Template A/B Performance Tracker

Tracks email template sends and responses over time via SQLite.

DATABASE: projects/shared/lead-scraper/output/template_performance.db

TABLES:
  sends          — One row per email sent
  responses      — One row per reply received
  template_stats — Aggregated counters per template (auto-updated)

USAGE:
  # Log a send
  python execution/template_performance.py log-send \\
      --template personalized_cold_v1 --tier deep_personalized \\
      --industry "HVAC / Home Services" --email mike@kozakair.com \\
      --company "Kozak AC" --score 85

  # Log a response
  python execution/template_performance.py log-response \\
      --email mike@kozakair.com --sentiment positive

  # Show performance report
  python execution/template_performance.py report
"""

import argparse
import sqlite3
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Database path
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent.parent / (
    "projects/shared/lead-scraper/output/template_performance.db"
)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS sends (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id     TEXT    NOT NULL,
    tier            TEXT    NOT NULL,
    industry        TEXT,
    recipient_email TEXT    NOT NULL,
    company         TEXT,
    lead_score      INTEGER,
    sent_at         TEXT    NOT NULL,
    campaign_date   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS responses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    send_id         INTEGER REFERENCES sends(id),
    recipient_email TEXT    NOT NULL,
    responded_at    TEXT    NOT NULL,
    sentiment       TEXT    NOT NULL CHECK(sentiment IN ('positive','neutral','bounce','unsubscribe')),
    reply_snippet   TEXT
);

CREATE TABLE IF NOT EXISTS template_stats (
    template_id     TEXT PRIMARY KEY,
    tier            TEXT,
    total_sent      INTEGER DEFAULT 0,
    total_replies   INTEGER DEFAULT 0,
    positive_replies INTEGER DEFAULT 0,
    last_send       TEXT,
    last_updated    TEXT
);
"""


def get_conn(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_log_send(
    template_id: str,
    tier: str,
    industry: str,
    email: str,
    company: str,
    score: Optional[int],
    db_path: Path = DB_PATH,
) -> int:
    """Log a single send. Returns the new send row id."""
    conn = get_conn(db_path)
    now = datetime.now(timezone.utc).isoformat()
    campaign_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    cur = conn.execute(
        """
        INSERT INTO sends
            (template_id, tier, industry, recipient_email, company, lead_score, sent_at, campaign_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (template_id, tier, industry or "", email, company or "", score, now, campaign_date),
    )
    send_id = cur.lastrowid

    # Upsert template_stats
    conn.execute(
        """
        INSERT INTO template_stats (template_id, tier, total_sent, total_replies,
                                    positive_replies, last_send, last_updated)
        VALUES (?, ?, 1, 0, 0, ?, ?)
        ON CONFLICT(template_id) DO UPDATE SET
            total_sent   = total_sent + 1,
            tier         = excluded.tier,
            last_send    = excluded.last_send,
            last_updated = excluded.last_updated
        """,
        (template_id, tier, now, now),
    )
    conn.commit()
    conn.close()
    return send_id


def cmd_log_response(
    email: str,
    sentiment: str,
    reply_snippet: str = "",
    db_path: Path = DB_PATH,
) -> bool:
    """
    Log a response for the most recent send to this email address.
    Returns True if a matching send was found, False otherwise.
    """
    valid_sentiments = {"positive", "neutral", "bounce", "unsubscribe"}
    if sentiment not in valid_sentiments:
        print(
            f"ERROR: sentiment must be one of: {', '.join(sorted(valid_sentiments))}",
            file=sys.stderr,
        )
        sys.exit(1)

    conn = get_conn(db_path)

    # Find most recent send for this email
    row = conn.execute(
        "SELECT id, template_id FROM sends WHERE recipient_email = ? ORDER BY sent_at DESC LIMIT 1",
        (email,),
    ).fetchone()

    if not row:
        conn.close()
        return False

    send_id = row["id"]
    template_id = row["template_id"]
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        """
        INSERT INTO responses (send_id, recipient_email, responded_at, sentiment, reply_snippet)
        VALUES (?, ?, ?, ?, ?)
        """,
        (send_id, email, now, sentiment, reply_snippet or ""),
    )

    # Update template_stats
    conn.execute(
        """
        UPDATE template_stats
        SET total_replies  = total_replies + 1,
            positive_replies = positive_replies + CASE WHEN ? = 'positive' THEN 1 ELSE 0 END,
            last_updated   = ?
        WHERE template_id = ?
        """,
        (sentiment, now, template_id),
    )
    conn.commit()
    conn.close()
    return True


def cmd_report(db_path: Path = DB_PATH):
    """Print a performance table for all templates."""
    conn = get_conn(db_path)
    rows = conn.execute(
        """
        SELECT template_id, tier, total_sent, total_replies, positive_replies,
               last_send, last_updated
        FROM template_stats
        ORDER BY total_sent DESC
        """
    ).fetchall()
    conn.close()

    if not rows:
        print("No template data yet. Log some sends first.")
        return

    print()
    print("=" * 80)
    print("TEMPLATE PERFORMANCE REPORT")
    print("=" * 80)
    print(
        f"{'Template':<28} {'Tier':<20} {'Sent':>5} {'Replies':>8} {'Positive':>9} {'Open%':>6}"
    )
    print("-" * 80)
    for r in rows:
        reply_rate = (r["total_replies"] / r["total_sent"] * 100) if r["total_sent"] > 0 else 0
        pos_rate = (
            (r["positive_replies"] / r["total_sent"] * 100) if r["total_sent"] > 0 else 0
        )
        print(
            f"{r['template_id'][:27]:<28} {r['tier'][:19]:<20} "
            f"{r['total_sent']:>5} {r['total_replies']:>8} "
            f"{r['positive_replies']:>9} {reply_rate:>5.1f}%"
        )
    print()
    print(f"Last updated: {rows[0]['last_updated'] if rows else 'n/a'}")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Template A/B Performance Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  log-send      Log a sent email
  log-response  Log a reply received
  report        Print performance table

Examples:
  python execution/template_performance.py log-send \\
      --template personalized_cold_v1 --tier deep_personalized \\
      --industry "HVAC / Home Services" --email mike@kozakair.com \\
      --company "Kozak AC" --score 85

  python execution/template_performance.py log-response \\
      --email mike@kozakair.com --sentiment positive

  python execution/template_performance.py report
""",
    )
    sub = parser.add_subparsers(dest="command")

    # log-send
    p_send = sub.add_parser("log-send", help="Log a sent email")
    p_send.add_argument("--template", required=True, help="Template ID")
    p_send.add_argument("--tier", required=True, help="Routing tier name")
    p_send.add_argument("--industry", default="", help="Industry")
    p_send.add_argument("--email", required=True, help="Recipient email")
    p_send.add_argument("--company", default="", help="Company name")
    p_send.add_argument("--score", type=int, default=None, help="Lead score (0-100)")

    # log-response
    p_resp = sub.add_parser("log-response", help="Log a reply received")
    p_resp.add_argument("--email", required=True, help="Recipient email")
    p_resp.add_argument(
        "--sentiment",
        required=True,
        choices=["positive", "neutral", "bounce", "unsubscribe"],
    )
    p_resp.add_argument("--snippet", default="", help="Brief reply snippet")

    # report
    sub.add_parser("report", help="Print performance report")

    args = parser.parse_args()

    if args.command == "log-send":
        send_id = cmd_log_send(
            template_id=args.template,
            tier=args.tier,
            industry=args.industry,
            email=args.email,
            company=args.company,
            score=args.score,
        )
        print(f"Logged send #{send_id}: {args.template} → {args.email} (score={args.score})")

    elif args.command == "log-response":
        found = cmd_log_response(
            email=args.email,
            sentiment=args.sentiment,
            reply_snippet=args.snippet,
        )
        if found:
            print(f"Logged {args.sentiment} response from {args.email}")
        else:
            print(
                f"WARNING: No send record found for {args.email}. "
                "Response not logged.",
                file=sys.stderr,
            )
            sys.exit(1)

    elif args.command == "report":
        cmd_report()

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
