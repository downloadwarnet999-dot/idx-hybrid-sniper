import os
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import logging

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

logger = logging.getLogger(__name__)

SUPABASE_URL = "postgresql://postgres.rcdrjzhbjyuyftniduwx:PercobaaN385@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require"

class MarketDatabase:
    def __init__(self, db_path: Path = Path('data/market_data.db')):
        self.db_path = db_path
        self.use_supabase = bool(SUPABASE_URL and HAS_PSYCOPG2)
        if self.use_supabase:
            logger.info("✅ Using Supabase")
        else:
            logger.info("❌ Using SQLite")

    def _get_conn(self):
        if self.use_supabase:
            return psycopg2.connect(SUPABASE_URL)
        return sqlite3.connect(str(self.db_path))

    def _execute(self, query, params=None, fetch='all'):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if fetch == 'all':
                return cursor.fetchall()
            elif fetch == 'one':
                return cursor.fetchone()
            elif fetch == 'none':
                conn.commit()
                return cursor.rowcount
        finally:
            conn.close()

    def get_all_tickers(self) -> List[str]:
        try:
            if self.use_supabase:
                rows = self._execute("SELECT ticker FROM watchlist ORDER BY ticker", fetch='all')
                return [row[0] for row in rows] if rows else []
            else:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT ticker FROM watchlist ORDER BY ticker")
                rows = cursor.fetchall()
                conn.close()
                return [row[0] for row in rows]
        except Exception as e:
            logger.warning(f"Failed to get tickers: {e}")
            return []

    def get_data(self, ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        if self.use_supabase:
            query = "SELECT date, open, high, low, close, volume, adj_close FROM market_data WHERE ticker = %s"
            params = [ticker]
            if start_date:
                query += " AND date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND date <= %s"
                params.append(end_date)
            query += " ORDER BY date ASC"
            rows = self._execute(query, tuple(params), fetch='all')
            if not rows:
                return pd.DataFrame()
            df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume', 'adj_close'])
            df['date'] = pd.to_datetime(df['date'])
            return df.set_index('date')
        else:
            conn = sqlite3.connect(str(self.db_path))
            query = "SELECT date, open, high, low, close, volume, adj_close FROM market_data WHERE ticker = ?"
            params = [ticker]
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            query += " ORDER BY date ASC"
            df = pd.read_sql_query(query, conn, params=params, parse_dates=['date'])
            conn.close()
            return df.set_index('date')

    def save_data(self, ticker: str, df: pd.DataFrame):
        if df.empty:
            return
        df = df.reset_index()
        if 'date' not in df.columns:
            df['date'] = pd.Timestamp.now().date()
        if 'adj_close' not in df.columns:
            df['adj_close'] = df['close'] if 'close' in df.columns else None
        df['ticker'] = ticker
        cols = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
        df = df[cols]
        data = df.to_records(index=False).tolist()

        if self.use_supabase:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT INTO market_data (ticker, date, open, high, low, close, volume, adj_close)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, date) DO NOTHING
            ''', data)
            conn.commit()
            conn.close()
        else:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT OR REPLACE INTO market_data (ticker, date, open, high, low, close, volume, adj_close)
                VALUES (?,?,?,?,?,?,?,?)
            ''', data)
            conn.commit()
            conn.close()

    def add_ticker(self, ticker: str) -> bool:
        try:
            if self.use_supabase:
                conn = self._get_conn()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO watchlist (ticker) VALUES (%s) ON CONFLICT (ticker) DO NOTHING", (ticker,))
                conn.commit()
                affected = cursor.rowcount
                conn.close()
                return affected > 0
            else:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                cursor.execute("INSERT INTO watchlist (ticker) VALUES (?)", (ticker,))
                conn.commit()
                conn.close()
                return True
        except Exception:
            return False

    def get_last_date(self, ticker: str):
        """Get the last available date for a ticker"""
        if self.use_supabase:
            query = "SELECT MAX(date) FROM market_data WHERE ticker = %s"
            rows = self._execute(query, (ticker,), fetch='one')
            return rows[0] if rows else None
        else:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(date) FROM market_data WHERE ticker = ?", (ticker,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
class JournalDatabase:
    def __init__(self, db_path: Path = Path('data/journal.db')):
        self.db_path = db_path
        self.use_supabase = bool(SUPABASE_URL and HAS_PSYCOPG2)

    def _get_conn(self):
        if self.use_supabase:
            return psycopg2.connect(SUPABASE_URL)
        return sqlite3.connect(str(self.db_path))

    def _execute(self, query, params=None, fetch='all'):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if fetch == 'all':
                return cursor.fetchall()
            elif fetch == 'one':
                return cursor.fetchone()
            elif fetch == 'none':
                conn.commit()
                return cursor.rowcount
        finally:
            conn.close()

    def add_entry(self, entry: Dict[str, Any]) -> bool:
        return True

market_db = MarketDatabase()
journal_db = JournalDatabase()
