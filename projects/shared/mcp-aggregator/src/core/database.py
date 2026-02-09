"""
Database Connection Layer for MCP Aggregator Platform

Provides unified database access that works with both:
- SQLite (for local testing, no setup required)
- PostgreSQL (for production)

Features:
- Connection pooling
- Query helpers with parameterized queries
- Transaction support
- Automatic schema detection
- Type-safe row access
"""

import os
import sqlite3
import logging
from typing import Optional, List, Dict, Any, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, date
from contextlib import contextmanager
from enum import Enum
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_type: DatabaseType

    # SQLite settings
    sqlite_path: str = ":memory:"

    # PostgreSQL settings
    host: str = "localhost"
    port: int = 5432
    database: str = "mcp_aggregator"
    user: str = "postgres"
    password: str = ""

    # Connection pool settings
    min_connections: int = 2
    max_connections: int = 10

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create config from environment variables"""
        db_url = os.getenv('DATABASE_URL', '')

        if db_url.startswith('postgresql://') or db_url.startswith('postgres://'):
            # Parse PostgreSQL URL
            # Format: postgresql://user:password@host:port/database
            return cls._parse_postgres_url(db_url)
        else:
            # Default to SQLite
            sqlite_path = os.getenv('SQLITE_PATH', ':memory:')
            return cls(db_type=DatabaseType.SQLITE, sqlite_path=sqlite_path)

    @classmethod
    def _parse_postgres_url(cls, url: str) -> 'DatabaseConfig':
        """Parse PostgreSQL connection URL"""
        # Remove protocol
        url = url.replace('postgresql://', '').replace('postgres://', '')

        # Split auth from host
        if '@' in url:
            auth, hostpath = url.split('@', 1)
            if ':' in auth:
                user, password = auth.split(':', 1)
            else:
                user, password = auth, ''
        else:
            user, password = 'postgres', ''
            hostpath = url

        # Split host from database
        if '/' in hostpath:
            hostport, database = hostpath.split('/', 1)
        else:
            hostport, database = hostpath, 'mcp_aggregator'

        # Split host from port
        if ':' in hostport:
            host, port_str = hostport.split(':', 1)
            port = int(port_str)
        else:
            host, port = hostport, 5432

        return cls(
            db_type=DatabaseType.POSTGRESQL,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )

    @classmethod
    def sqlite(cls, path: str = ':memory:') -> 'DatabaseConfig':
        """Create SQLite config"""
        return cls(db_type=DatabaseType.SQLITE, sqlite_path=path)

    @classmethod
    def postgresql(
        cls,
        host: str = 'localhost',
        port: int = 5432,
        database: str = 'mcp_aggregator',
        user: str = 'postgres',
        password: str = ''
    ) -> 'DatabaseConfig':
        """Create PostgreSQL config"""
        return cls(
            db_type=DatabaseType.POSTGRESQL,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )


class Row(dict):
    """
    Dictionary-like row that supports attribute access.

    Usage:
        row = Row({'id': 1, 'name': 'Test'})
        print(row.id)  # 1
        print(row['name'])  # 'Test'
    """
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"Row has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any):
        self[name] = value


class Database:
    """
    Unified database interface for SQLite and PostgreSQL.

    Usage:
        # SQLite (testing)
        db = Database(DatabaseConfig.sqlite('test.db'))

        # PostgreSQL (production)
        db = Database(DatabaseConfig.postgresql(database='mcp_aggregator'))

        # From environment
        db = Database(DatabaseConfig.from_env())

        # Query
        rows = db.fetch_all("SELECT * FROM mcps WHERE status = ?", ('active',))

        # Insert
        db.execute("INSERT INTO mcps (name) VALUES (?)", ('Test MCP',))

        # Transaction
        with db.transaction():
            db.execute("UPDATE accounts SET balance = balance - 100 WHERE id = ?", (1,))
            db.execute("UPDATE accounts SET balance = balance + 100 WHERE id = ?", (2,))
    """

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection = None
        self._pg_pool = None

        logger.info(f"Database initialized with {config.db_type.value}")

    def connect(self):
        """Establish database connection"""
        if self.config.db_type == DatabaseType.SQLITE:
            self._connect_sqlite()
        else:
            self._connect_postgresql()

    def _connect_sqlite(self):
        """Connect to SQLite database"""
        self._connection = sqlite3.connect(
            self.config.sqlite_path,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        self._connection.row_factory = sqlite3.Row

        # Enable foreign keys
        self._connection.execute("PRAGMA foreign_keys = ON")

        logger.info(f"Connected to SQLite: {self.config.sqlite_path}")

    def _connect_postgresql(self):
        """Connect to PostgreSQL database"""
        try:
            import psycopg2
            from psycopg2 import pool
            from psycopg2.extras import RealDictCursor

            self._pg_pool = pool.ThreadedConnectionPool(
                self.config.min_connections,
                self.config.max_connections,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                cursor_factory=RealDictCursor
            )

            logger.info(f"Connected to PostgreSQL: {self.config.host}:{self.config.port}/{self.config.database}")

        except ImportError:
            raise ImportError(
                "psycopg2 is required for PostgreSQL. "
                "Install with: pip install psycopg2-binary"
            )

    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None

        if self._pg_pool:
            self._pg_pool.closeall()
            self._pg_pool = None

        logger.info("Database connection closed")

    @contextmanager
    def _get_connection(self):
        """Get a connection from the pool (or single connection for SQLite)"""
        if self.config.db_type == DatabaseType.SQLITE:
            if not self._connection:
                self._connect_sqlite()
            yield self._connection
        else:
            if not self._pg_pool:
                self._connect_postgresql()
            conn = self._pg_pool.getconn()
            try:
                yield conn
            finally:
                self._pg_pool.putconn(conn)

    def _convert_params(self, sql: str, params: tuple) -> Tuple[str, tuple]:
        """
        Convert query syntax between SQLite (?) and PostgreSQL (%s).

        SQLite uses ? for placeholders.
        PostgreSQL uses %s for placeholders.
        """
        if self.config.db_type == DatabaseType.POSTGRESQL:
            # Replace ? with %s for PostgreSQL
            sql = sql.replace('?', '%s')

        return sql, params

    def execute(self, sql: str, params: tuple = ()) -> int:
        """
        Execute a single SQL statement.

        Args:
            sql: SQL statement with ? placeholders
            params: Parameter tuple

        Returns:
            Number of affected rows
        """
        sql, params = self._convert_params(sql, params)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount

    def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """
        Execute a SQL statement with multiple parameter sets.

        Args:
            sql: SQL statement with ? placeholders
            params_list: List of parameter tuples

        Returns:
            Total number of affected rows
        """
        sql, _ = self._convert_params(sql, ())

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            conn.commit()
            return cursor.rowcount

    def fetch_one(self, sql: str, params: tuple = ()) -> Optional[Row]:
        """
        Fetch a single row.

        Args:
            sql: SQL query with ? placeholders
            params: Parameter tuple

        Returns:
            Row dict or None if not found
        """
        sql, params = self._convert_params(sql, params)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()

            if row is None:
                return None

            # Convert to Row
            if self.config.db_type == DatabaseType.SQLITE:
                return Row(dict(zip([col[0] for col in cursor.description], row)))
            else:
                return Row(dict(row))

    def fetch_all(self, sql: str, params: tuple = ()) -> List[Row]:
        """
        Fetch all rows.

        Args:
            sql: SQL query with ? placeholders
            params: Parameter tuple

        Returns:
            List of Row dicts
        """
        sql, params = self._convert_params(sql, params)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            if self.config.db_type == DatabaseType.SQLITE:
                columns = [col[0] for col in cursor.description]
                return [Row(dict(zip(columns, row))) for row in rows]
            else:
                return [Row(dict(row)) for row in rows]

    def fetch_value(self, sql: str, params: tuple = ()) -> Any:
        """
        Fetch a single value (first column of first row).

        Args:
            sql: SQL query with ? placeholders
            params: Parameter tuple

        Returns:
            Single value or None
        """
        row = self.fetch_one(sql, params)
        if row is None:
            return None

        # Return first value
        return list(row.values())[0]

    def insert_returning_id(self, table: str, data: Dict[str, Any]) -> Any:
        """
        Insert a row and return the generated ID.

        Args:
            table: Table name
            data: Column-value dict

        Returns:
            Generated ID (usually UUID or integer)
        """
        columns = list(data.keys())
        placeholders = ', '.join(['?' for _ in columns])
        columns_str = ', '.join(columns)
        values = tuple(data.values())

        if self.config.db_type == DatabaseType.SQLITE:
            sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
            sql, values = self._convert_params(sql, values)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
                conn.commit()
                return cursor.lastrowid
        else:
            # PostgreSQL: Use RETURNING
            sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) RETURNING id"
            sql, values = self._convert_params(sql, values)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
                result = cursor.fetchone()
                conn.commit()
                return result['id'] if result else None

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.

        Usage:
            with db.transaction():
                db.execute(...)
                db.execute(...)
            # Commits on success, rolls back on exception
        """
        with self._get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction rolled back: {e}")
                raise

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        if self.config.db_type == DatabaseType.SQLITE:
            result = self.fetch_one(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
        else:
            result = self.fetch_one(
                "SELECT table_name FROM information_schema.tables WHERE table_name = ?",
                (table_name,)
            )
        return result is not None

    def get_table_columns(self, table_name: str) -> List[str]:
        """Get column names for a table"""
        if self.config.db_type == DatabaseType.SQLITE:
            rows = self.fetch_all(f"PRAGMA table_info({table_name})")
            return [row['name'] for row in rows]
        else:
            rows = self.fetch_all(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = ?
                ORDER BY ordinal_position
                """,
                (table_name,)
            )
            return [row['column_name'] for row in rows]

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a database health check.

        Returns:
            Dict with connection status and latency
        """
        import time

        start = time.time()
        try:
            if self.config.db_type == DatabaseType.SQLITE:
                self.fetch_one("SELECT 1")
            else:
                self.fetch_one("SELECT 1")

            latency_ms = (time.time() - start) * 1000

            return {
                'status': 'healthy',
                'database_type': self.config.db_type.value,
                'latency_ms': round(latency_ms, 2),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'database_type': self.config.db_type.value,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


class SQLiteSchema:
    """
    SQLite-compatible schema for testing.

    Creates tables that mirror the PostgreSQL schema but use SQLite syntax.
    """

    @staticmethod
    def create_tables(db: Database):
        """Create all tables for SQLite testing"""

        # Developers
        db.execute("""
            CREATE TABLE IF NOT EXISTS developers (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                company_name TEXT,
                display_name TEXT NOT NULL,
                api_key_hash TEXT NOT NULL,
                stripe_customer_id TEXT,
                stripe_account_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_verified INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )
        """)

        # AI Platforms
        db.execute("""
            CREATE TABLE IF NOT EXISTS ai_platforms (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                api_key_hash TEXT NOT NULL,
                contact_email TEXT,
                billing_email TEXT,
                stripe_customer_id TEXT,
                monthly_credit_limit REAL DEFAULT 1000.00,
                current_balance REAL DEFAULT 0.00,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # MCPs
        db.execute("""
            CREATE TABLE IF NOT EXISTS mcps (
                id TEXT PRIMARY KEY,
                developer_id TEXT REFERENCES developers(id),
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                version TEXT DEFAULT '1.0.0',
                endpoint_url TEXT,
                health_check_url TEXT,
                documentation_url TEXT,
                fee_per_request REAL DEFAULT 0.01,
                developer_share REAL DEFAULT 0.80,
                status TEXT DEFAULT 'pending_review',
                avg_response_time_ms INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0.00,
                total_requests INTEGER DEFAULT 0,
                total_errors INTEGER DEFAULT 0,
                uptime_percent REAL DEFAULT 100.00,
                tags TEXT,
                supported_regions TEXT,
                rate_limit_rpm INTEGER DEFAULT 100,
                timeout_ms INTEGER DEFAULT 30000,
                connectivity_type TEXT DEFAULT 'http',
                email_address TEXT,
                webhook_path TEXT,
                oauth_config TEXT,
                async_callback_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_health_check TIMESTAMP
            )
        """)

        # MCP Capabilities
        db.execute("""
            CREATE TABLE IF NOT EXISTS mcp_capabilities (
                id TEXT PRIMARY KEY,
                mcp_id TEXT REFERENCES mcps(id),
                name TEXT NOT NULL,
                description TEXT,
                input_schema TEXT,
                output_schema TEXT,
                examples TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(mcp_id, name)
            )
        """)

        # Circuit Breaker State
        db.execute("""
            CREATE TABLE IF NOT EXISTS circuit_breaker_state (
                id TEXT PRIMARY KEY,
                mcp_id TEXT UNIQUE REFERENCES mcps(id),
                state TEXT DEFAULT 'closed',
                failure_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                last_failure_at TIMESTAMP,
                last_success_at TIMESTAMP,
                opened_at TIMESTAMP,
                half_opened_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Transactions
        db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                ai_platform_id TEXT REFERENCES ai_platforms(id),
                mcp_id TEXT REFERENCES mcps(id),
                developer_id TEXT REFERENCES developers(id),
                request_id TEXT UNIQUE NOT NULL,
                capability_name TEXT,
                request_payload TEXT,
                response_payload TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                response_time_ms INTEGER,
                gross_amount REAL NOT NULL,
                platform_fee REAL NOT NULL,
                developer_payout REAL NOT NULL,
                pricing_model TEXT DEFAULT 'per_request',
                subscription_id TEXT,
                booking_value REAL,
                commission_rate REAL,
                tier_name TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Rate Cards
        db.execute("""
            CREATE TABLE IF NOT EXISTS rate_cards (
                id TEXT PRIMARY KEY,
                city TEXT NOT NULL,
                service TEXT NOT NULL,
                ride_type TEXT NOT NULL,
                base_fare REAL NOT NULL,
                cost_per_mile REAL NOT NULL,
                cost_per_minute REAL NOT NULL,
                booking_fee REAL NOT NULL,
                min_fare REAL NOT NULL,
                source_url TEXT,
                effective_date DATE NOT NULL,
                expires_date DATE,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(city, service, ride_type, effective_date)
            )
        """)

        # Health Checks
        db.execute("""
            CREATE TABLE IF NOT EXISTS health_checks (
                id TEXT PRIMARY KEY,
                mcp_id TEXT REFERENCES mcps(id),
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_healthy INTEGER NOT NULL,
                response_time_ms INTEGER,
                status_code INTEGER,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Daily Stats
        db.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                id TEXT PRIMARY KEY,
                date DATE NOT NULL,
                mcp_id TEXT REFERENCES mcps(id),
                ai_platform_id TEXT REFERENCES ai_platforms(id),
                developer_id TEXT REFERENCES developers(id),
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                avg_response_time_ms INTEGER DEFAULT 0,
                p95_response_time_ms INTEGER DEFAULT 0,
                p99_response_time_ms INTEGER DEFAULT 0,
                gross_revenue REAL DEFAULT 0,
                platform_revenue REAL DEFAULT 0,
                developer_revenue REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, mcp_id, ai_platform_id)
            )
        """)

        # Payouts
        db.execute("""
            CREATE TABLE IF NOT EXISTS payouts (
                id TEXT PRIMARY KEY,
                developer_id TEXT REFERENCES developers(id),
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                period_start DATE NOT NULL,
                period_end DATE NOT NULL,
                status TEXT DEFAULT 'pending',
                stripe_transfer_id TEXT,
                processed_at TIMESTAMP,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Invoices
        db.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                ai_platform_id TEXT REFERENCES ai_platforms(id),
                period_start DATE NOT NULL,
                period_end DATE NOT NULL,
                subtotal REAL NOT NULL,
                tax REAL DEFAULT 0,
                total REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                status TEXT DEFAULT 'draft',
                due_date DATE,
                paid_at TIMESTAMP,
                stripe_invoice_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        logger.info("SQLite schema created successfully")


# Convenience function for testing
def create_test_database(sqlite_path: str = ':memory:') -> Database:
    """
    Create a test database with schema.

    Args:
        sqlite_path: Path to SQLite file (default: in-memory)

    Returns:
        Database instance with schema initialized
    """
    db = Database(DatabaseConfig.sqlite(sqlite_path))
    db.connect()
    SQLiteSchema.create_tables(db)
    return db


# Module-level database instance (configured from environment)
_default_db: Optional[Database] = None


def get_database() -> Database:
    """Get the default database instance"""
    global _default_db
    if _default_db is None:
        _default_db = Database(DatabaseConfig.from_env())
        _default_db.connect()
    return _default_db


def close_database():
    """Close the default database connection"""
    global _default_db
    if _default_db is not None:
        _default_db.close()
        _default_db = None


# Example usage
if __name__ == "__main__":
    # Create test database
    db = create_test_database()

    # Health check
    health = db.health_check()
    print(f"Database health: {health}")

    # Insert test data
    import uuid

    dev_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO developers (id, email, display_name, api_key_hash)
        VALUES (?, ?, ?, ?)
        """,
        (dev_id, 'test@example.com', 'Test Developer', 'hash123')
    )

    # Query
    devs = db.fetch_all("SELECT * FROM developers")
    print(f"Developers: {devs}")

    # Check tables
    tables = ['developers', 'mcps', 'transactions', 'rate_cards']
    for table in tables:
        exists = db.table_exists(table)
        columns = db.get_table_columns(table) if exists else []
        print(f"Table {table}: exists={exists}, columns={len(columns)}")

    db.close()
