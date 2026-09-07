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
    def __init__(self):
        self.db = market_db
        self.tickers_file = TICKERS_FILE
        self._init_watchlist()

    def _standardize_df(self, df):
        """Standardize Postgres lowercase columns to Title Case for Yahoo Finance compatibility"""
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
        try:
            db_manager.init_watchlist_table()
            self._migrate_json_to_db()
        except Exception as e:
            self._ensure_tickers_file()

    def _migrate_json_to_db(self):
        try:
            existing = db_manager.execute_query("SELECT COUNT(*) FROM watchlist", fetch='one')
            if existing and existing[0] > 0: return
        except: pass
        if self.tickers_file.exists():
            try:
                with open(self.tickers_file, 'r') as f: data = json.load(f)
                for ticker in data.get('tickers', []):
                    db_manager.execute_query("INSERT INTO watchlist (ticker) VALUES (?) ON CONFLICT (ticker) DO NOTHING", (ticker,))
            except: pass
        else:
            for ticker in ['BBCA', 'BBRI', 'BMRI', 'BBNI', 'TLKM', 'ASII', 'UNVR', 'ICBP', 'INDF', 'KLBF', 'ADRO', 'ITMG', 'PTBA', 'ANTM', 'INCO', 'BSDE', 'PWON', 'SMGR', 'WIKA', 'PTPP']:
                db_manager.execute_query("INSERT INTO watchlist (ticker) VALUES (?) ON CONFLICT (ticker) DO NOTHING", (ticker,))

    def _ensure_tickers_file(self):
        if not self.tickers_file.exists():
            self._save_tickers_to_file(['BBCA', 'BBRI', 'BMRI', 'BBNI', 'TLKM'])

    def get_tickers(self) -> List[str]:
        try:
            results = db_manager.execute_query("SELECT ticker FROM watchlist ORDER BY ticker", fetch='all')
            if results: return [row[0] if isinstance(row, tuple) else row['ticker'] for row in results]
            return []
        except: return self._get_tickers_from_file()

    def _get_tickers_from_file(self) -> List[str]:
        if not self.tickers_file.exists(): return []
        try:
            with open(self.tickers_file, 'r') as f: data = json.load(f)
            return data.get('tickers', [])
        except: return []

    def save_tickers(self, tickers: List[str]):
        try:
            db_manager.execute_query("DELETE FROM watchlist")
            for ticker in sorted(list(set(tickers))):
                db_manager.execute_query("INSERT INTO watchlist (ticker) VALUES (?)", (ticker,))
        except: pass
        self._save_tickers_to_file(tickers)

    def _save_tickers_to_file(self, tickers: List[str]):
        try:
            self.tickers_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.tickers_file, 'w') as f: json.dump({'tickers': sorted(list(set(tickers)))}, f, indent=2)
        except: pass

    def add_ticker(self, ticker: str) -> bool:
        try:
            if db_manager.execute_query("SELECT COUNT(*) FROM watchlist WHERE ticker = ?", (ticker,), fetch='one')[0] > 0: return False
            db_manager.execute_query("INSERT INTO watchlist (ticker) VALUES (?)", (ticker,))
            return True
        except: return False

    def remove_ticker(self, ticker: str) -> bool:
        try:
            rowcount = db_manager.execute_query("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
            self.db.delete_ticker(ticker + IDX_SUFFIX)
            return rowcount > 0
        except: return False

    def import_from_csv(self, csv_path: str, replace: bool = False) -> Tuple[int, List[str]]:
        import csv
        imported = []
        try:
            with open(csv_path, 'r') as f: lines = f.readlines()
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or (i == 0 and line.lower() in ['ticker', 'tickers']): continue
                try: ticker = next(csv.reader([line]))[0].strip().upper()
                except: ticker = line.upper()
                if ticker and len(ticker) <= 10: imported.append(ticker)
            if not imported: return 0, []
            final = imported if replace else list(set(self.get_tickers() + imported))
            self.save_tickers(final)
            return len(imported), imported
        except: return 0, []

    def export_to_csv(self, csv_path: str) -> bool:
        import csv
        tickers = self.get_tickers()
        if not tickers: return False
        try:
            with open(csv_path, 'w', newline='') as f:
                w = csv.writer(f); w.writerow(['ticker'])
                for t in tickers: w.writerow([t])
            return True
        except: return False

    def _format_ticker(self, ticker: str) -> str:
        return ticker if ticker.endswith(IDX_SUFFIX) else ticker + IDX_SUFFIX

    def fetch_data(self, ticker: str, period: str = YFINANCE_PERIOD, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        try:
            data = yf.download(self._format_ticker(ticker), start=start_date, end=end_date, period=period if not start_date else None, interval=YFINANCE_INTERVAL, progress=False)
            return data.dropna() if not data.empty else None
        except: return None

    def update_ticker_data(self, ticker: str, force_full: bool = False) -> Tuple[bool, str]:
        fmt = self._format_ticker(ticker)
        try:
            if not force_full:
                last_date = self.db.get_last_date(fmt)
                if last_date:
                    start = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    today = datetime.now().strftime('%Y-%m-%d')
                    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                    if start > today: return True, f"{ticker}: Already up to date"
                    data = self.fetch_data(ticker, start_date=start, end_date=tomorrow)
                    if not data: return True, f"{ticker}: No new data"
                    return True, f"{ticker}: Added {self.db.save_data(fmt, data)} rows"
            data = self.fetch_data(ticker, period=YFINANCE_PERIOD)
            if not data: return False, f"{ticker}: Failed"
            self.db.delete_ticker(fmt)
            return True, f"{ticker}: Saved {self.db.save_data(fmt, data)} rows"
        except Exception as e: return False, f"{ticker}: Error {e}"

    def update_all_tickers(self, force_full: bool = False) -> Dict[str, str]:
        return {t: self.update_ticker_data(t, force_full)[1] for t in self.get_tickers()}

    def get_ticker_data(self, ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        fmt = self._format_ticker(ticker)
        df = self._standardize_df(self.db.get_data(fmt, start_date, end_date))
        if df.empty:
            if self.update_ticker_data(ticker)[0]:
                df = self._standardize_df(self.db.get_data(fmt, start_date, end_date))
            else: return None
        return df

    def get_ihsg_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        df = self._standardize_df(self.db.get_data(IHSG_SYMBOL, start_date, end_date))
        if not df.empty and start_date is None:
            try:
                start = (df.index[-1] + timedelta(days=1)).strftime('%Y-%m-%d')
                today = datetime.now().strftime('%Y-%m-%d')
                tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                if start < today:
                    new = yf.download(IHSG_SYMBOL, start=start, end=tomorrow, interval=YFINANCE_INTERVAL, progress=False)
                    if new is not None and not new.empty:
                        self.db.save_data(IHSG_SYMBOL, new)
                        df = self._standardize_df(self.db.get_data(IHSG_SYMBOL, start_date, end_date))
            except: pass
        if df.empty:
            data = yf.download(IHSG_SYMBOL, period=YFINANCE_PERIOD, interval=YFINANCE_INTERVAL, progress=False)
            if not data.empty:
                self.db.delete_ticker(IHSG_SYMBOL)
                self.db.save_data(IHSG_SYMBOL, data)
                df = self._standardize_df(self.db.get_data(IHSG_SYMBOL, start_date, end_date))
        return df if not df.empty else None

    def get_latest_price(self, ticker: str) -> Optional[float]:
        try:
            df = self._standardize_df(self.db.get_data(self._format_ticker(ticker)))
            if not df.empty: return float(df['Close'].iloc[-1])
            data = yf.download(self._format_ticker(ticker), period='1d', progress=False)
            return float(data['Close'].iloc[-1]) if not data.empty else None
        except: return None

    def validate_ticker(self, ticker: str) -> bool:
        try: return not yf.download(self._format_ticker(ticker), period='5d', progress=False).empty
        except: return False

data_engine = DataEngine()
