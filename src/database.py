"""
IDX Hybrid Sniper - Database Module
Universal database CRUD operations supporting SQLite (local) and PostgreSQL (cloud)
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import MARKET_DB, JOURNAL_DB
from src.db_manager import db_manager


class MarketDatabase:
    """Handles market data (OHLCV) storage and retrieval"""

    def __init__(self, db_path: Path = MARKET_DB):
        """
        Initialize market database

        Args:
            db_path: SQLite database path (ignored if using PostgreSQL cloud)
        """
        self.db_path = db_path
        if db_manager.db_type == 'sqlite':
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._create_tables()

    def _create_tables(self):
        """Create market_data table if not exists"""
        if db_manager.db_type == 'postgresql':
            # PostgreSQL schema
            query = """
                CREATE TABLE IF NOT EXISTS market_data (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL,
                    date DATE NOT NULL,
                    open NUMERIC(12, 2),
                    high NUMERIC(12, 2),
                    low NUMERIC(12, 2),
                    close NUMERIC(12, 2),
                    volume BIGINT,
                    adj_close NUMERIC(12, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, date)
                )
            """
            db_manager.execute_query(query)

            # Create indexes
            db_manager.execute_query(
                "CREATE INDEX IF NOT EXISTS idx_ticker_date ON market_data(ticker, date DESC)"
            )

        else:
            # SQLite schema
            query = """
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    date DATE NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    adj_close REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, date)
                )
            """
            db_manager.execute_query(query)

            # Create index
            db_manager.execute_query(
                "CREATE INDEX IF NOT EXISTS idx_ticker_date ON market_data(ticker, date DESC)"
            )

    def save_data(self, ticker: str, df: pd.DataFrame) -> int:
        """
        Save or update market data for a ticker

        Args:
            ticker: Stock ticker symbol
            df: DataFrame with columns [Date, Open, High, Low, Close, Volume, Adj Close]

        Returns:
            Number of rows inserted/updated
        """
        if df.empty:
            return 0

        # Prepare data
        df_copy = df.copy()
        df_copy['ticker'] = ticker
        df_copy = df_copy.reset_index()

        # Rename columns to match DB schema
        column_mapping = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Adj Close': 'adj_close'
        }
        df_copy = df_copy.rename(columns=column_mapping)

        # Ensure adj_close exists
        if 'adj_close' not in df_copy.columns:
            df_copy['adj_close'] = df_copy['close']

        # Convert date to string format
        if 'date' in df_copy.columns:
            df_copy['date'] = df_copy['date'].astype(str)

        # Select only needed columns
        columns = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
        df_copy = df_copy[columns]

        # Insert or replace
        if db_manager.db_type == 'postgresql':
            # PostgreSQL: Use ON CONFLICT for upsert
            query = """
                INSERT INTO market_data
                (ticker, date, open, high, low, close, volume, adj_close)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, date)
                DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    adj_close = EXCLUDED.adj_close
            """
        else:
            # SQLite: Use INSERT OR REPLACE
            query = """
                INSERT OR REPLACE INTO market_data
                (ticker, date, open, high, low, close, volume, adj_close)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

        # Batch insert
        params_list = [tuple(row) for _, row in df_copy.iterrows()]
        db_manager.execute_many(query, params_list)

        return len(df_copy)

    def get_data(self, ticker: str, start_date: Optional[str] = None,
                 end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve market data for a ticker

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD) or None for all data
            end_date: End date (YYYY-MM-DD) or None for all data

        Returns:
            DataFrame with OHLCV data, indexed by date
        """
        query = "SELECT * FROM market_data WHERE ticker = ?"
        params = [ticker]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date ASC"

        results = db_manager.execute_query(query, tuple(params), fetch='all')

        if not results:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(results)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')

            # Rename columns back to standard format
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume',
                'adj_close': 'Adj Close'
            })

        return df

    def get_last_date(self, ticker: str) -> Optional[datetime]:
        """Get the last available date for a ticker"""
        query = "SELECT MAX(date) as last_date FROM market_data WHERE ticker = ?"
        result = db_manager.execute_query(query, (ticker,), fetch='one')

        if result:
            # Handle both tuple (SQLite) and dict (PostgreSQL) results
            last_date = result[0] if isinstance(result, tuple) else result.get('last_date')
            if last_date:
                return pd.to_datetime(last_date)
        return None

    def get_all_tickers(self) -> List[str]:
        """Get list of all tickers in database"""
        query = "SELECT DISTINCT ticker FROM market_data ORDER BY ticker"
        results = db_manager.execute_query(query, fetch='all')
        return [row[0] if isinstance(row, tuple) else row['ticker'] for row in results]

    def delete_ticker(self, ticker: str) -> int:
        """Delete all data for a ticker"""
        query = "DELETE FROM market_data WHERE ticker = ?"
        return db_manager.execute_query(query, (ticker,))


class JournalDatabase:
    """Handles trading journal storage and retrieval"""

    def __init__(self, db_path: Path = JOURNAL_DB):
        """
        Initialize journal database

        Args:
            db_path: SQLite database path (ignored if using PostgreSQL cloud)
        """
        self.db_path = db_path
        if db_manager.db_type == 'sqlite':
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._create_tables()

    def _create_tables(self):
        """Create trading_journal table if not exists"""
        if db_manager.db_type == 'postgresql':
            # PostgreSQL schema
            query = """
                CREATE TABLE IF NOT EXISTS trading_journal (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL,
                    entry_date DATE NOT NULL,
                    entry_price NUMERIC(12, 2) NOT NULL,
                    lot_size INTEGER NOT NULL,
                    sl_price NUMERIC(12, 2) NOT NULL,
                    tp1_price NUMERIC(12, 2) NOT NULL,
                    status VARCHAR(20) DEFAULT 'OPEN',
                    exit_date DATE,
                    exit_price NUMERIC(12, 2),
                    pnl_percent NUMERIC(8, 2),
                    pnl_amount NUMERIC(15, 2),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        else:
            # SQLite schema
            query = """
                CREATE TABLE IF NOT EXISTS trading_journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    entry_date DATE NOT NULL,
                    entry_price REAL NOT NULL,
                    lot_size INTEGER NOT NULL,
                    sl_price REAL NOT NULL,
                    tp1_price REAL NOT NULL,
                    status TEXT DEFAULT 'OPEN',
                    exit_date DATE,
                    exit_price REAL,
                    pnl_percent REAL,
                    pnl_amount REAL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """

        db_manager.execute_query(query)

        # Create index
        if db_manager.db_type == 'postgresql':
            db_manager.execute_query(
                "CREATE INDEX IF NOT EXISTS idx_status ON trading_journal(status)"
            )
        else:
            db_manager.execute_query(
                "CREATE INDEX IF NOT EXISTS idx_status ON trading_journal(status)"
            )

    def add_trade(self, ticker: str, entry_date: str, entry_price: float,
                  lot_size: int, sl_price: float, tp1_price: float,
                  notes: str = "") -> int:
        """
        Add a new trade to journal

        Returns:
            Trade ID
        """
        query = """
            INSERT INTO trading_journal
            (ticker, entry_date, entry_price, lot_size, sl_price, tp1_price, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        return db_manager.execute_query(
            query,
            (ticker, entry_date, entry_price, lot_size, sl_price, tp1_price, notes)
        )

    def get_open_trades(self) -> pd.DataFrame:
        """Get all open trades"""
        query = """
            SELECT * FROM trading_journal
            WHERE status = 'OPEN'
            ORDER BY entry_date DESC
        """

        results = db_manager.execute_query(query, fetch='all')

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)
        if not df.empty and 'entry_date' in df.columns:
            df['entry_date'] = pd.to_datetime(df['entry_date'])

        return df

    def get_closed_trades(self, limit: int = 50) -> pd.DataFrame:
        """Get recent closed trades"""
        query = f"""
            SELECT * FROM trading_journal
            WHERE status = 'CLOSED'
            ORDER BY exit_date DESC
            LIMIT {limit}
        """

        results = db_manager.execute_query(query, fetch='all')

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)
        if not df.empty:
            if 'entry_date' in df.columns:
                df['entry_date'] = pd.to_datetime(df['entry_date'])
            if 'exit_date' in df.columns:
                df['exit_date'] = pd.to_datetime(df['exit_date'])

        return df

    def get_trade_by_id(self, trade_id: int) -> Optional[dict]:
        """Get single trade by ID"""
        query = "SELECT * FROM trading_journal WHERE id = ?"
        result = db_manager.execute_query(query, (trade_id,), fetch='one')

        if result:
            return dict(result)
        return None

    def update_sl(self, trade_id: int, new_sl: float, notes: str = "") -> bool:
        """Update stop loss for a trade (trailing stop)"""
        if db_manager.db_type == 'postgresql':
            query = """
                UPDATE trading_journal
                SET sl_price = %s,
                    notes = CASE
                        WHEN %s != '' THEN CONCAT(notes, E'\\n', %s)
                        ELSE notes
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND status = 'OPEN'
            """
        else:
            query = """
                UPDATE trading_journal
                SET sl_price = ?,
                    notes = CASE
                        WHEN ? != '' THEN notes || '\n' || ?
                        ELSE notes
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'OPEN'
            """

        rowcount = db_manager.execute_query(query, (new_sl, notes, notes, trade_id))
        return rowcount > 0

    def close_trade(self, trade_id: int, exit_date: str, exit_price: float,
                   notes: str = "") -> bool:
        """Close a trade and calculate P&L"""
        # Get trade details first
        trade = self.get_trade_by_id(trade_id)
        if not trade or trade['status'] != 'OPEN':
            return False

        # Calculate P&L
        entry_price = float(trade['entry_price'])
        lot_size = int(trade['lot_size'])
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        pnl_amount = (exit_price - entry_price) * lot_size * 100  # IDX lot = 100 shares

        # Update database
        if db_manager.db_type == 'postgresql':
            query = """
                UPDATE trading_journal
                SET status = 'CLOSED',
                    exit_date = %s,
                    exit_price = %s,
                    pnl_percent = %s,
                    pnl_amount = %s,
                    notes = CASE
                        WHEN %s != '' THEN CONCAT(notes, E'\\n', %s)
                        ELSE notes
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
        else:
            query = """
                UPDATE trading_journal
                SET status = 'CLOSED',
                    exit_date = ?,
                    exit_price = ?,
                    pnl_percent = ?,
                    pnl_amount = ?,
                    notes = CASE
                        WHEN ? != '' THEN notes || '\n' || ?
                        ELSE notes
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """

        rowcount = db_manager.execute_query(
            query,
            (exit_date, exit_price, pnl_percent, pnl_amount, notes, notes, trade_id)
        )
        return rowcount > 0

    def get_statistics(self) -> dict:
        """Get trading statistics"""
        # Helper function to extract value from result (handles both tuple and dict)
        def get_value(result, key=0):
            if not result:
                return None
            return result[key] if isinstance(result, tuple) else list(result.values())[0]

        # Total trades
        result = db_manager.execute_query(
            "SELECT COUNT(*) FROM trading_journal WHERE status = 'CLOSED'",
            fetch='one'
        )
        total_trades = get_value(result) or 0

        # Win rate
        result = db_manager.execute_query(
            "SELECT COUNT(*) FROM trading_journal WHERE status = 'CLOSED' AND pnl_percent > 0",
            fetch='one'
        )
        winning_trades = get_value(result) or 0

        # Average P&L
        result = db_manager.execute_query(
            "SELECT AVG(pnl_percent) FROM trading_journal WHERE status = 'CLOSED'",
            fetch='one'
        )
        avg_pnl_val = get_value(result)
        avg_pnl = float(avg_pnl_val) if avg_pnl_val is not None else 0

        # Total P&L
        result = db_manager.execute_query(
            "SELECT SUM(pnl_amount) FROM trading_journal WHERE status = 'CLOSED'",
            fetch='one'
        )
        total_pnl_val = get_value(result)
        total_pnl = float(total_pnl_val) if total_pnl_val is not None else 0

        # Best trade
        result = db_manager.execute_query(
            "SELECT MAX(pnl_percent) FROM trading_journal WHERE status = 'CLOSED'",
            fetch='one'
        )
        best_trade_val = get_value(result)
        best_trade = float(best_trade_val) if best_trade_val is not None else 0

        # Worst trade
        result = db_manager.execute_query(
            "SELECT MIN(pnl_percent) FROM trading_journal WHERE status = 'CLOSED'",
            fetch='one'
        )
        worst_trade_val = get_value(result)
        worst_trade = float(worst_trade_val) if worst_trade_val is not None else 0

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate': win_rate,
            'avg_pnl_percent': avg_pnl,
            'total_pnl_idr': total_pnl,
            'best_trade_percent': best_trade,
            'worst_trade_percent': worst_trade
        }


# Initialize databases on module import
market_db = MarketDatabase()
journal_db = JournalDatabase()
