"""
IDX Hybrid Sniper - Data Engine
Smart data fetching with incremental updates from yfinance
"""

import yfinance as yf
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    IHSG_SYMBOL, IDX_SUFFIX, TICKERS_FILE,
    YFINANCE_PERIOD, YFINANCE_INTERVAL
)
from src.database import market_db
from src.db_manager import db_manager


class DataEngine:
    """Handles data fetching and updating from Yahoo Finance"""

    def __init__(self):
        self.db = market_db
        self.tickers_file = TICKERS_FILE
        self._init_watchlist()

    def _standardize_df(self, df):
        """GOD-MODE FIX: Standardize Postgres lowercase columns to Title Case"""
        if df is not None and not getattr(df, 'empty', True):
            try:
                rename_map = {'date':'Date', 'open':'Open', 'high':'High', 'low':'Low', 'close':'Close', 'volume':'Volume'}
                df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
                df.columns = [c.title() for c in df.columns]
                if 'Date' in df.columns and not isinstance(df.index, pd.DatetimeIndex):
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
            except Exception:
                pass
        return df

    def _init_watchlist(self):
        """Initialize watchlist (database or file fallback)"""
        try:
            db_manager.init_watchlist_table()
            self._migrate_json_to_db()
        except Exception as e:
            print(f"Warning: Could not init watchlist table: {e}")
            self._ensure_tickers_file()

    def _migrate_json_to_db(self):
        """Migrate tickers from JSON file to database (one-time)"""
        try:
            existing = db_manager.execute_query("SELECT COUNT(*) FROM watchlist", fetch='one')
            if existing and existing[0] > 0:
                return
        except:
            pass

        if self.tickers_file.exists():
            try:
                with open(self.tickers_file, 'r') as f:
                    data = json.load(f)
                    tickers = data.get('tickers', [])
                if tickers:
                    print(f"Migrating {len(tickers)} tickers from JSON to database...")
                    for ticker in tickers:
                        try:
                            query = "INSERT INTO watchlist (ticker) VALUES (?) ON CONFLICT (ticker) DO NOTHING"
                            db_manager.execute_query(query, (ticker,))
                        except:
                            pass
                    print("Migration complete!")
            except Exception as e:
                print(f"Migration failed: {e}")
        else:
            default_tickers = ['BBCA', 'BBRI', 'BMRI', 'BBNI', 'TLKM', 'ASII', 'UNVR', 'ICBP', 'INDF', 'KLBF', 'ADRO', 'ITMG', 'PTBA', 'ANTM', 'INCO', 'BSDE', 'PWON', 'SMGR', 'WIKA', 'PTPP']
            for ticker in default_tickers:
                try:
                    query = "INSERT INTO watchlist (ticker) VALUES (?) ON CONFLICT (ticker) DO NOTHING"
                    db_manager.execute_query(query, (ticker,))
                except:
                    pass

    def _ensure_tickers_file(self):
        """Create tickers file if not exists (fallback)"""
        if not self.tickers_file.exists():
            default_tickers = ['BBCA', 'BBRI', 'BMRI', 'BBNI', 'TLKM', 'ASII', 'UNVR', 'ICBP', 'INDF', 'KLBF', 'ADRO', 'ITMG', 'PTBA', 'ANTM', 'INCO', 'BSDE', 'PWON', 'SMGR', 'WIKA', 'PTPP']
            self._save_tickers_to_file(default_tickers)

    def get_tickers(self) -> List[str]:
        """Load tickers from database (or JSON fallback)"""
        try:
            query = "SELECT ticker FROM watchlist ORDER BY ticker"
            results = db_manager.execute_query(query, fetch='all')
            if results:
                return [row[0] if isinstance(row, tuple) else row['ticker'] for row in results]
            return []
        except Exception as e:
            return self._get_tickers_from_file()

    def _get_tickers_from_file(self) -> List[str]:
        """Load tickers from JSON file (fallback)"""
        if not self.tickers_file.exists():
            return []
        try:
            with open(self.tickers_file, 'r') as f:
                data = json.load(f)
            return data.get('tickers', [])
        except:
            return []

    def save_tickers(self, tickers: List[str]):
        """Save tickers to database (and JSON backup)"""
        try:
            db_manager.execute_query("DELETE FROM watchlist")
            for ticker in sorted(list(set(tickers))):
                query = "INSERT INTO watchlist (ticker) VALUES (?)"
                db_manager.execute_query(query, (ticker,))
        except Exception as e:
            print(f"Warning: Could not save to database: {e}")
        self._save_tickers_to_file(tickers)

    def _save_tickers_to_file(self, tickers: List[str]):
        """Save tickers to JSON file (backup)"""
        try:
            self.tickers_file.parent.mkdir(parents=True, exist_ok=True)
            data = {'tickers': sorted(list(set(tickers))), 'updated_at': datetime.now().isoformat()}
            with open(self.tickers_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def add_ticker(self, ticker: str) -> bool:
        """Add a new ticker to watchlist"""
        try:
            query = "SELECT COUNT(*) FROM watchlist WHERE ticker = ?"
            result = db_manager.execute_query(query, (ticker,), fetch='one')
            if result and result[0] > 0:
                return False
            query = "INSERT INTO watchlist (ticker) VALUES (?)"
            db_manager.execute_query(query, (ticker,))
            tickers = self.get_tickers()
            self._save_tickers_to_file(tickers)
            return True
        except Exception as e:
            tickers = self._get_tickers_from_file()
            if ticker not in tickers:
                tickers.append(ticker)
                self._save_tickers_to_file(tickers)
                return True
            return False

    def remove_ticker(self, ticker: str) -> bool:
        """Remove ticker from watchlist"""
        try:
            query = "DELETE FROM watchlist WHERE ticker = ?"
            rowcount = db_manager.execute_query(query, (ticker,))
            self.db.delete_ticker(ticker + IDX_SUFFIX)
            tickers = self.get_tickers()
            self._save_tickers_to_file(tickers)
            return rowcount > 0
        except Exception as e:
            tickers = self._get_tickers_from_file()
            if ticker in tickers:
                tickers.remove(ticker)
                self._save_tickers_to_file(tickers)
                self.db.delete_ticker(ticker + IDX_SUFFIX)
                return True
            return False

    def import_from_csv(self, csv_path: str, replace: bool = False) -> Tuple[int, List[str]]:
        """Import tickers from CSV file"""
        import csv
        imported_tickers = []
        try:
            with open(csv_path, 'r') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                if i == 0 and line.lower() in ['ticker', 'tickers', 'symbol', 'symbols', 'stock', 'stocks']:
                    continue
                try:
                    row = next(csv.reader([line]))
                    ticker = row[0].strip().upper()
                except:
                    ticker = line.upper()
                if ticker and len(ticker) <= 10 and ticker.isalnum():
                    imported_tickers.append(ticker)
            if not imported_tickers:
                return 0, []
            if replace:
                final_tickers = imported_tickers
            else:
                existing_tickers = self.get_tickers()
                final_tickers = list(set(existing_tickers + imported_tickers))
            self.save_tickers(final_tickers)
            return len(imported_tickers), imported_tickers
        except Exception as e:
            print(f"Error importing CSV: {e}")
            return 0, []

    def export_to_csv(self, csv_path: str) -> bool:
        """Export current watchlist to CSV file"""
        import csv
        tickers = self.get_tickers()
        if not tickers:
            return False
        try:
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ticker'])
                for ticker in tickers:
                    writer.writerow([ticker])
            return True
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False

    def _format_ticker(self, ticker: str) -> str:
        """Format ticker for Yahoo Finance (add .JK suffix if needed)"""
        if not ticker.endswith(IDX_SUFFIX):
            return ticker + IDX_SUFFIX
        return ticker

    def fetch_data(self, ticker: str, period: str = YFINANCE_PERIOD,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from Yahoo Finance"""
        formatted_ticker = self._format_ticker(ticker)
        try:
            if start_date:
                data = yf.download(formatted_ticker, start=start_date, end=end_date,
                                  interval=YFINANCE_INTERVAL, progress=False)
            else:
                data = yf.download(formatted_ticker, period=period,
                                  interval=YFINANCE_INTERVAL, progress=False)
            if data.empty:
                return None
            data = data.dropna()
            return data
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None

    def update_ticker_data(self, ticker: str, force_full: bool = False) -> Tuple[bool, str]:
        """Update data for a ticker (incremental or full)"""
        formatted_ticker = self._format_ticker(ticker)
        try:
            if not force_full:
                last_date = self.db.get_last_date(formatted_ticker)
                if last_date:
                    start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    today = datetime.now().strftime('%Y-%m-%d')
                    if start_date >= today:
                        return True, f"{ticker}: Already up to date"
                    data = self.fetch_data(ticker, start_date=start_date, end_date=today)
                    if data is None or data.empty:
                        return True, f"{ticker}: No new data available"
                    rows = self.db.save_data(formatted_ticker, data)
                    return True, f"{ticker}: Added {rows} new rows"
            data = self.fetch_data(ticker, period=YFINANCE_PERIOD)
            if data is None or data.empty:
                return False, f"{ticker}: Failed to fetch data"
            self.db.delete_ticker(formatted_ticker)
            rows = self.db.save_data(formatted_ticker, data)
            return True, f"{ticker}: Saved {rows} rows (full update)"
        except Exception as e:
            return False, f"{ticker}: Error - {str(e)}"

    def update_all_tickers(self, force_full: bool = False) -> Dict[str, str]:
        """Update data for all tickers in watchlist"""
        tickers = self.get_tickers()
        results = {}
        for ticker in tickers:
            success, message = self.update_ticker_data(ticker, force_full)
            results[ticker] = message
        return results

    def get_ticker_data(self, ticker: str, start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get ticker data from database (fetch if not available)"""
        formatted_ticker = self._format_ticker(ticker)
        df = self.db.get_data(formatted_ticker, start_date, end_date)
        
        # === GOD-MODE FIX APPLIED ===
        df = self._standardize_df(df)
        # ============================

        if df.empty:
            print(f"No data in DB for {ticker}, fetching from Yahoo Finance...")
            success, message = self.update_ticker_data(ticker)
            if success:
                df = self.db.get_data(formatted_ticker, start_date, end_date)
                # === GOD-MODE FIX APPLIED ===
                df = self._standardize_df(df)
                # ============================
            else:
                return None
        return df

    def get_ihsg_data(self, start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get IHSG (Jakarta Composite Index) data"""
        df = self.db.get_data(IHSG_SYMBOL, start_date, end_date)

        # === GOD-MODE FIX APPLIED ===
        df = self._standardize_df(df)
        # ============================

        if df.empty:
            print("Fetching IHSG data from Yahoo Finance...")
            data = yf.download(IHSG_SYMBOL, period=YFINANCE_PERIOD,
                             interval=YFINANCE_INTERVAL, progress=False)
            if not data.empty:
                self.db.delete_ticker(IHSG_SYMBOL)
                self.db.save_data(IHSG_SYMBOL, data)
                df = self.db.get_data(IHSG_SYMBOL, start_date, end_date)
                # === GOD-MODE FIX APPLIED ===
                df = self._standardize_df(df)
                # ============================
        return df if not df.empty else None

    def get_latest_price(self, ticker: str) -> Optional[float]:
        """Get the most recent closing price for a ticker"""
        formatted_ticker = self._format_ticker(ticker)
        try:
            df = self.db.get_data(formatted_ticker)
            # === GOD-MODE FIX APPLIED ===
            df = self._standardize_df(df)
            # ============================
            if not df.empty:
                return float(df['Close'].iloc[-1])
            data = yf.download(formatted_ticker, period='1d', progress=False)
            if not data.empty:
                return float(data['Close'].iloc[-1])
            return None
        except Exception as e:
            print(f"Error getting latest price for {ticker}: {e}")
            return None

    def validate_ticker(self, ticker: str) -> bool:
        """Check if ticker exists on Yahoo Finance"""
        formatted_ticker = self._format_ticker(ticker)
        try:
            data = yf.download(formatted_ticker, period='5d', progress=False)
            return not data.empty
        except:
            return False

data_engine = DataEngine()
