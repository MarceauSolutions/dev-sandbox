#!/usr/bin/env python3
"""
Pipeline Data Validator — Run before ANY lead list generation.

Catches:
1. Orphan outreach records (no deal_id)
2. Leads marked "Contacted" with no outreach history
3. Duplicate companies
4. Leads with fabricated history (claims without verification)

Usage:
    python -m src.validate_pipeline           # Check and report
    python -m src.validate_pipeline --fix     # Auto-fix what we can
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = str(Path(__file__).parent.parent / "data" / "pipeline.db")


def validate_pipeline(auto_fix: bool = False) -> dict:
    """Validate pipeline data integrity. Returns dict of issues."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    issues = {
        "orphan_outreach": [],
        "contacted_no_history": [],
        "duplicate_companies": [],
        "stage_mismatch": [],
        "fixed": []
    }
    
    # 1. Check for orphan outreach records
    orphans = conn.execute("""
        SELECT id, company, channel, message_summary, created_at 
        FROM outreach_log WHERE deal_id IS NULL
    """).fetchall()
    
    for o in orphans:
        issues["orphan_outreach"].append({
            "id": o["id"],
            "company": o["company"],
            "channel": o["channel"],
            "message": o["message_summary"][:50] if o["message_summary"] else "",
            "date": o["created_at"]
        })
    
    if auto_fix and orphans:
        conn.execute("DELETE FROM outreach_log WHERE deal_id IS NULL")
        issues["fixed"].append(f"Deleted {len(orphans)} orphan outreach records")
    
    # 2. Check for "Contacted" leads with no outreach history
    no_history = conn.execute("""
        SELECT d.id, d.company, d.stage FROM deals d
        WHERE d.stage = 'Contacted'
        AND d.id NOT IN (SELECT DISTINCT deal_id FROM outreach_log WHERE deal_id IS NOT NULL)
    """).fetchall()
    
    for d in no_history:
        issues["contacted_no_history"].append({
            "id": d["id"],
            "company": d["company"],
            "stage": d["stage"]
        })
    
    if auto_fix and no_history:
        conn.execute("""
            UPDATE deals SET stage = 'Intake' 
            WHERE stage = 'Contacted'
            AND id NOT IN (SELECT DISTINCT deal_id FROM outreach_log WHERE deal_id IS NOT NULL)
        """)
        issues["fixed"].append(f"Reset {len(no_history)} 'Contacted' leads without history to 'Intake'")
    
    # 3. Check for duplicate companies
    dupes = conn.execute("""
        SELECT company, COUNT(*) as cnt FROM deals 
        GROUP BY LOWER(company) HAVING cnt > 1
    """).fetchall()
    
    for d in dupes:
        issues["duplicate_companies"].append({
            "company": d["company"],
            "count": d["cnt"]
        })
    
    # 4. Check for stage mismatches (e.g., "Closed Lost" with recent positive outreach)
    mismatches = conn.execute("""
        SELECT d.id, d.company, d.stage, o.response, o.created_at
        FROM deals d
        JOIN outreach_log o ON o.deal_id = d.id
        WHERE d.stage = 'Closed Lost'
        AND o.response LIKE '%interested%'
        AND o.response NOT LIKE '%not interested%'
        AND o.created_at > datetime('now', '-7 days')
    """).fetchall()
    
    for m in mismatches:
        issues["stage_mismatch"].append({
            "id": m["id"],
            "company": m["company"],
            "stage": m["stage"],
            "recent_positive": m["response"]
        })
    
    conn.commit()
    conn.close()
    
    return issues


def print_report(issues: dict):
    """Print validation report."""
    print("\n" + "="*60)
    print("PIPELINE VALIDATION REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    total_issues = sum(len(v) for k, v in issues.items() if k != "fixed")
    
    if total_issues == 0:
        print("\n✅ Pipeline data is CLEAN. No issues found.")
    else:
        print(f"\n⚠️  Found {total_issues} issue(s):\n")
    
    if issues["orphan_outreach"]:
        print(f"🔴 ORPHAN OUTREACH RECORDS: {len(issues['orphan_outreach'])}")
        print("   These have outreach logged but no deal_id - they're disconnected from tracking.")
        for o in issues["orphan_outreach"][:5]:
            print(f"   - {o['company']} ({o['channel']}, {o['date'][:10]})")
        if len(issues["orphan_outreach"]) > 5:
            print(f"   ... and {len(issues['orphan_outreach']) - 5} more")
        print()
    
    if issues["contacted_no_history"]:
        print(f"🟠 'CONTACTED' LEADS WITH NO HISTORY: {len(issues['contacted_no_history'])}")
        print("   These claim to be contacted but have no outreach records to prove it.")
        for d in issues["contacted_no_history"][:5]:
            print(f"   - {d['company']} (ID: {d['id']})")
        print()
    
    if issues["duplicate_companies"]:
        print(f"🟡 DUPLICATE COMPANIES: {len(issues['duplicate_companies'])}")
        for d in issues["duplicate_companies"]:
            print(f"   - {d['company']} appears {d['count']} times")
        print()
    
    if issues["stage_mismatch"]:
        print(f"🟣 STAGE MISMATCHES: {len(issues['stage_mismatch'])}")
        print("   These are 'Closed Lost' but have recent positive responses.")
        for m in issues["stage_mismatch"]:
            print(f"   - {m['company']}: {m['recent_positive'][:40]}...")
        print()
    
    if issues["fixed"]:
        print("🔧 AUTO-FIXES APPLIED:")
        for fix in issues["fixed"]:
            print(f"   - {fix}")
        print()
    
    print("="*60)
    return total_issues == 0


def main():
    auto_fix = "--fix" in sys.argv
    
    if auto_fix:
        print("Running validation with AUTO-FIX enabled...")
    else:
        print("Running validation (read-only, use --fix to auto-correct)...")
    
    issues = validate_pipeline(auto_fix=auto_fix)
    is_clean = print_report(issues)
    
    sys.exit(0 if is_clean else 1)


if __name__ == "__main__":
    main()
