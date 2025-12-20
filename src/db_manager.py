"""
IDX Hybrid Sniper - Database Manager
Universal database abstraction supporting SQLite (local) and PostgreSQL (cloud)
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional, Any, List, Tuple
from contextlib import contextmanager

# Try to import PostgreSQL driver
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class DatabaseManager:
    """
    Universal database manager that works with both SQLite and PostgreSQL
    Auto-detects environment and uses appropriate database
    """

    def __init__(self):
        """Initialize database manager"""
        self.db_type = self._detect_db_type()
        self.connection_string = self._get_connection_string()

    def _detect_db_type(self) -> str:
        """
        Detect which database to use based on environment

        Returns:
            'postgresql' or 'sqlite'
        """
        # Check if running on Streamlit Cloud or has database URL in secrets
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'database' in st.secrets:
                if st.secrets['database'].get('type') == 'postgresql':
                    return 'postgresql'
        except:
            pass

        # Check environment variable
        if os.getenv('DATABASE_URL'):
            return 'postgresql'

        # Default to SQLite for local development
        return 'sqlite'

    def _get_connection_string(self) -> str:
        """
        Get database connection string

        Returns:
            Connection string or path
        """
        if self.db_type == 'postgresql':
            # Try Streamlit secrets first
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and 'database' in st.secrets:
                    return st.secrets['database']['url']
            except:
                pass

            # Try environment variable
            db_url = os.getenv('DATABASE_URL')
            if db_url:
                return db_url

            raise ValueError("PostgreSQL selected but no connection string found in secrets or environment")

        else:
            # SQLite: Use local data directory
            data_dir = Path(__file__).parent.parent / 'data'
            data_dir.mkdir(parents=True, exist_ok=True)
            return str(data_dir / 'market_data.db')

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections
        Automatically handles connection and cleanup

        Usage:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        if self.db_type == 'postgresql':
            if not POSTGRES_AVAILABLE:
                raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")

            conn = psycopg2.connect(self.connection_string)
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()

        else:
            # SQLite
            conn = sqlite3.connect(self.connection_string)
            conn.row_factory = sqlite3.Row  # Return rows as dicts
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()

    def execute_query(self, query: str, params: Optional[tuple] = None, fetch: str = 'none') -> Any:
        """
        Execute a database query

        Args:
            query: SQL query (use ? for SQLite, %s for PostgreSQL)
            params: Query parameters
            fetch: 'none', 'one', 'all'

        Returns:
            Query results or None
        """
        # Convert placeholders if needed
        if self.db_type == 'postgresql' and '?' in query:
            query = query.replace('?', '%s')

        with self.get_connection() as conn:
            if self.db_type == 'postgresql':
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            else:
                cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch == 'one':
                return cursor.fetchone()
            elif fetch == 'all':
                return cursor.fetchall()
            else:
                return cursor.lastrowid if self.db_type == 'sqlite' else cursor.rowcount

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute query with multiple parameter sets

        Args:
            query: SQL query
            params_list: List of parameter tuples

        Returns:
            Number of rows affected
        """
        # Convert placeholders if needed
        if self.db_type == 'postgresql' and '?' in query:
            query = query.replace('?', '%s')

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount

    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists

        Args:
            table_name: Name of table

        Returns:
            True if table exists, False otherwise
        """
        if self.db_type == 'postgresql':
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                )
            """
            result = self.execute_query(query, (table_name,), fetch='one')
            return result[0] if result else False

        else:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(query, (table_name,), fetch='one')
            return result is not None

    def init_market_data_table(self):
        """Initialize market data table"""
        if self.db_type == 'postgresql':
            # PostgreSQL schema
            query = """
                CREATE TABLE IF NOT EXISTS market_data (
                    ticker VARCHAR(10) NOT NULL,
                    date DATE NOT NULL,
                    open NUMERIC(12, 2),
                    high NUMERIC(12, 2),
                    low NUMERIC(12, 2),
                    close NUMERIC(12, 2),
                    volume BIGINT,
                    PRIMARY KEY (ticker, date)
                )
            """
        else:
            # SQLite schema
            query = """
                CREATE TABLE IF NOT EXISTS market_data (
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    PRIMARY KEY (ticker, date)
                )
            """

        self.execute_query(query)

        # Create index for faster queries
        if self.db_type == 'postgresql':
            self.execute_query("CREATE INDEX IF NOT EXISTS idx_ticker ON market_data(ticker)")
            self.execute_query("CREATE INDEX IF NOT EXISTS idx_date ON market_data(date)")
        else:
            self.execute_query("CREATE INDEX IF NOT EXISTS idx_ticker ON market_data(ticker)")
            self.execute_query("CREATE INDEX IF NOT EXISTS idx_date ON market_data(date)")

    def init_journal_table(self):
        """Initialize trading journal table"""
        if self.db_type == 'postgresql':
            # PostgreSQL schema
            query = """
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(10) NOT NULL,
                    entry_date DATE NOT NULL,
                    entry_price NUMERIC(12, 2) NOT NULL,
                    lot_size INTEGER NOT NULL,
                    sl_price NUMERIC(12, 2),
                    tp1_price NUMERIC(12, 2),
                    exit_date DATE,
                    exit_price NUMERIC(12, 2),
                    pnl_percent NUMERIC(8, 2),
                    pnl_amount NUMERIC(15, 2),
                    notes TEXT,
                    status VARCHAR(20) DEFAULT 'OPEN',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        else:
            # SQLite schema
            query = """
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    entry_date TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    lot_size INTEGER NOT NULL,
                    sl_price REAL,
                    tp1_price REAL,
                    exit_date TEXT,
                    exit_price REAL,
                    pnl_percent REAL,
                    pnl_amount REAL,
                    notes TEXT,
                    status TEXT DEFAULT 'OPEN',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """

        self.execute_query(query)

    def init_watchlist_table(self):
        """Initialize watchlist table"""
        if self.db_type == 'postgresql':
            # PostgreSQL schema
            query = """
                CREATE TABLE IF NOT EXISTS watchlist (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL UNIQUE,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            """
        else:
            # SQLite schema
            query = """
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL UNIQUE,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            """

        self.execute_query(query)

        # Create index
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_ticker_watchlist ON watchlist(ticker)")

    def init_all_tables(self):
        """Initialize all database tables"""
        self.init_market_data_table()
        self.init_journal_table()
        self.init_watchlist_table()


# Global database manager instance
db_manager = DatabaseManager()
