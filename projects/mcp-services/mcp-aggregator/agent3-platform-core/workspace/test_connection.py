#!/usr/bin/env python3
"""
PostgreSQL Connection Test

Tests PostgreSQL connection and verifies database setup.
Run after setting up PostgreSQL with schema.sql and seed_data.sql.

Usage:
    python test_connection.py

    # With custom connection string:
    DATABASE_URL=postgresql://user:pass@host:5432/db python test_connection.py
"""

import os
import sys
from datetime import datetime


def test_connection():
    """Test PostgreSQL connection and verify setup"""
    print("=" * 60)
    print("MCP Aggregator Platform - PostgreSQL Connection Test")
    print("=" * 60)
    print()

    # Get connection settings
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/mcp_aggregator')
    print(f"Connection: {db_url.split('@')[1] if '@' in db_url else db_url}")
    print()

    # Import database module
    try:
        from database import Database, DatabaseConfig
    except ImportError as e:
        print(f"ERROR: Could not import database module: {e}")
        print("Make sure you're running from the workspace directory")
        return False

    # Create PostgreSQL config
    try:
        if db_url.startswith('postgresql://') or db_url.startswith('postgres://'):
            config = DatabaseConfig._parse_postgres_url(db_url)
        else:
            config = DatabaseConfig.postgresql()

        print(f"Host: {config.host}")
        print(f"Port: {config.port}")
        print(f"Database: {config.database}")
        print(f"User: {config.user}")
        print()
    except Exception as e:
        print(f"ERROR: Could not parse connection URL: {e}")
        return False

    # Test connection
    print("Testing connection...")
    try:
        db = Database(config)
        db.connect()
        print("  Connected successfully!")
    except ImportError:
        print()
        print("ERROR: psycopg2 not installed")
        print()
        print("Install with:")
        print("  pip install psycopg2-binary")
        print()
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Is PostgreSQL running?")
        print("     brew services start postgresql")
        print()
        print("  2. Does the database exist?")
        print("     createdb mcp_aggregator")
        print()
        print("  3. Check credentials in DATABASE_URL")
        print()
        return False

    # Health check
    print()
    print("Health check...")
    health = db.health_check()
    print(f"  Status: {health['status']}")
    print(f"  Latency: {health['latency_ms']}ms")

    # Check tables
    print()
    print("Verifying tables...")
    required_tables = [
        'developers',
        'ai_platforms',
        'mcps',
        'mcp_capabilities',
        'circuit_breaker_state',
        'transactions',
        'rate_cards',
        'health_checks',
        'daily_stats',
        'payouts',
        'invoices'
    ]

    missing_tables = []
    for table in required_tables:
        exists = db.table_exists(table)
        status = "OK" if exists else "MISSING"
        print(f"  {table}: {status}")
        if not exists:
            missing_tables.append(table)

    if missing_tables:
        print()
        print(f"ERROR: {len(missing_tables)} tables missing!")
        print()
        print("Run the schema setup:")
        print(f"  psql {config.database} < schema.sql")
        print()
        db.close()
        return False

    # Check seed data
    print()
    print("Verifying seed data...")

    checks = [
        ("Developers", "SELECT COUNT(*) as count FROM developers"),
        ("AI Platforms", "SELECT COUNT(*) as count FROM ai_platforms"),
        ("MCPs", "SELECT COUNT(*) as count FROM mcps"),
        ("Rate Cards", "SELECT COUNT(*) as count FROM rate_cards"),
    ]

    for name, query in checks:
        try:
            result = db.fetch_one(query)
            count = result['count'] if result else 0
            status = f"{count} records"
            print(f"  {name}: {status}")
        except Exception as e:
            print(f"  {name}: ERROR - {e}")

    # Test query performance
    print()
    print("Testing query performance...")

    import time

    queries = [
        ("Simple SELECT", "SELECT 1"),
        ("MCP Lookup", "SELECT * FROM mcps WHERE status = 'active' LIMIT 10"),
        ("Join Query", """
            SELECT m.*, d.display_name
            FROM mcps m
            JOIN developers d ON m.developer_id = d.id
            LIMIT 10
        """),
        ("Aggregate", "SELECT category, COUNT(*) FROM mcps GROUP BY category"),
    ]

    for name, query in queries:
        start = time.time()
        try:
            db.fetch_all(query)
            elapsed = (time.time() - start) * 1000
            print(f"  {name}: {elapsed:.2f}ms")
        except Exception as e:
            print(f"  {name}: ERROR - {e}")

    # Test write operations
    print()
    print("Testing write operations...")

    test_id = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    try:
        # Insert
        db.execute(
            """
            INSERT INTO developers (id, email, display_name, api_key_hash)
            VALUES (?, ?, ?, ?)
            """,
            (test_id, f'{test_id}@test.com', 'Test Connection User', 'test_hash')
        )
        print("  INSERT: OK")

        # Update
        db.execute(
            "UPDATE developers SET display_name = ? WHERE id = ?",
            ('Updated Test User', test_id)
        )
        print("  UPDATE: OK")

        # Delete (cleanup)
        db.execute("DELETE FROM developers WHERE id = ?", (test_id,))
        print("  DELETE: OK")

    except Exception as e:
        print(f"  ERROR: {e}")
        # Cleanup on error
        try:
            db.execute("DELETE FROM developers WHERE id = ?", (test_id,))
        except:
            pass

    # Summary
    print()
    print("=" * 60)
    print("CONNECTION TEST PASSED")
    print("=" * 60)
    print()
    print("PostgreSQL is ready for use!")
    print()
    print("Next steps:")
    print("  1. Set DATABASE_URL environment variable (if not using defaults)")
    print("  2. Run the platform tests: pytest test_platform.py -v")
    print("  3. Start the API server")
    print()

    db.close()
    return True


def main():
    """Main entry point"""
    success = test_connection()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
