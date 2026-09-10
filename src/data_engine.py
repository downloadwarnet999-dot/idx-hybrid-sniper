"""
IDX Hybrid Sniper - Data Engine (FINAL CANONICAL v4.2.1)
v4.2: writes market_data rows DIRECTLY via db_manager.
v4.2.1: all long lines split short (mobile-paste safe).
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


def _flatten(df):
    """Normalize ANY dataframe to flat Title-case + Date index."""
    if df is None or getattr(df, 'empty', True):
        return df
    try:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        rename_map = {
            'date': 'Date', 'open': 'Open', 'high': 'High',
            'low': 'Low', 'close': 'Close', 'volume': 'Volume',
            'adj close': 'Adj Close', 'adj_close': 'Adj Close',
        }
        keep = {k: v for k, v in rename_map.items() if k in df.columns}
        df.rename(columns=keep, inplace=True)
        df.columns = [c.title() for c in df.columns]
        if 'Adj Close' not in df.columns and 'Close' in df.columns:
            df['Adj Close'] = df['Close']
        has_date = 'Date' in df.columns
        not_dt = not isinstance(df.index, pd.DatetimeIndex)
        if has_date and not_dt:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
    except Exception:
        pass
    return df


class DataEngine:
    """Handles data fetching and updating from Yahoo Finance"""

    def __init__(self):
        self.db = market_db
        self.tickers_file = TICKERS_FILE
        self._init_watchlist()

    def _save_rows(self, fmt: str, df: pd.DataFrame) -> int:
        """Write candles straight into market_data (explicit columns)."""
        if df is None or df.empty:
            return 0
        df = df[~df.index.duplicated(keep='last')]
        cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.dropna(subset=cols)
        if df.empty:
            return 0
        dates = [d.strftime('%Y-%m-%d') for d in df.index]
        ph = ','.join(['%s'] * len(dates))
        del_sql = "DELETE FROM market_data WHERE ticker = %s"
        del_sql += " AND date IN (" + ph + ")"
        db_manager.execute_query(del_sql, tuple([fmt] + dates))
        row_ph = '(%s,%s,%s,%s,%s,%s,%s,%s)'
        values_sql = ','.join([row_ph] * len(dates))
        params = []
        has_adj = 'Adj Close' in df.columns
        for d in dates:
            r = df.loc[pd.Timestamp(d)]
            adj = r['Adj Close'] if has_adj else r['Close']
            params.extend([fmt, d, float(r['Open']), float(r['High']),
                           float(r['Low']), float(r['Close']),
                           int(r['Volume']), float(adj)])
        ins_sql = "INSERT INTO market_data (ticker,date,open,"
        ins_sql += "high,low,close,volume,adj_close) VALUES "
        ins_sql += values_sql
        db_manager.execute_query(ins_sql, tuple(params))
        return len(dates)

    def _init_watchlist(self):
        try:
            db_manager.init_watchlist_table()
            self._migrate_json_to_db()
        except Exception:
            self._ensure_tickers_file()

    def _migrate_json_to_db(self):
        try:
            q = "SELECT COUNT(*) FROM watchlist"
            existing = db_manager.execute_query(q, fetch='one')
            if existing and existing[0] > 0:
                return
        except Exception:
            pass
        if self.tickers_file.exists():
            try:
                with open(self.tickers_file, 'r') as f:
                    data = json.load(f)
                for ticker in data.get('tickers', []):
                    q = "INSERT INTO watchlist (ticker) VALUES (?)"
                    q += " ON CONFLICT (ticker) DO NOTHING"
                    db_manager.execute_query(q, (ticker,))
            except Exception:
                pass

    def _ensure_tickers_file(self):
        if not self.tickers_file.exists():
            self._save_tickers_to_file(['BBCA', 'BBRI', 'BMRI', 'BBNI', 'TLKM'])

    def get_tickers(self) -> List[str]:
        try:
            q = "SELECT ticker FROM watchlist ORDER BY ticker"
            results = db_manager.execute_query(q, fetch='all')
            if results:
                out = []
                for row in results:
                    if isinstance(row, (tuple, list)):
                        out.append(row[0])
                    else:
                        out.append(row['ticker'])
                return out
            return []
        except Exception:
            return self._get_tickers_from_file()

    def _get_tickers_from_file(self) -> List[str]:
        if not self.tickers_file.exists():
            return []
        try:
            with open(self.tickers_file, 'r') as f:
                data = json.load(f)
            return data.get('tickers', [])
        except Exception:
            return []

    def save_tickers(self, tickers: List[str]):
        try:
            db_manager.execute_query("DELETE FROM watchlist")
            for ticker in sorted(list(set(tickers))):
                q = "INSERT INTO watchlist (ticker) VALUES (?)"
                db_manager.execute_query(q, (ticker,))
        except Exception:
            pass
        self._save_tickers_to_file(tickers)

    def _save_tickers_to_file(self, tickers: List[str]):
        try:
            self.tickers_file.parent.mkdir(parents=True, exist_ok=True)
            data = {'tickers': sorted(list(set(tickers)))}
            with open(self.tickers_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def add_ticker(self, ticker: str) -> bool:
        try:
            q = "SELECT COUNT(*) FROM watchlist WHERE ticker = ?"
            result = db_manager.execute_query(q, (ticker,), fetch='one')
            if result and result[0] > 0:
                return False
            q = "INSERT INTO watchlist (ticker) VALUES (?)"
            db_manager.execute_query(q, (ticker,))
            return True
        except Exception:
            return False

    def remove_ticker(self, ticker: str) -> bool:
        try:
            q = "DELETE FROM watchlist WHERE ticker = ?"
            rowcount = db_manager.execute_query(q, (ticker,))
            self.db.delete_ticker(ticker + IDX_SUFFIX)
            return rowcount > 0
        except Exception:
            return False

    def import_from_csv(self, csv_path: str, replace: bool = False):
        import csv
        imported = []
        try:
            with open(csv_path, 'r') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                if i == 0 and line.lower() in ['ticker', 'tickers']:
                    continue
                try:
                    ticker = next(csv.reader([line]))[0].strip().upper()
                except Exception:
                    ticker = line.upper()
                if ticker and len(ticker) <= 10:
                    imported.append(ticker)
            if not imported:
                return 0, []
            if replace:
                final = imported
            else:
                final = list(set(self.get_tickers() + imported))
            self.save_tickers(final)
            return len(imported), imported
        except Exception:
            return 0, []

    def export_to_csv(self, csv_path: str) -> bool:
        import csv
        tickers = self.get_tickers()
        if not tickers:
            return False
        try:
            with open(csv_path, 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(['ticker'])
                for t in tickers:
                    w.writerow([t])
            return True
        except Exception:
            return False

    def _format_ticker(self, ticker: str) -> str:
        if ticker.endswith(IDX_SUFFIX):
            return ticker
        return ticker + IDX_SUFFIX

    def fetch_data(self, ticker: str, period: str = YFINANCE_PERIOD,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None):
        try:
            fmt = self._format_ticker(ticker)
            per = None if start_date else period
            data = yf.download(fmt, start=start_date, end=end_date,
                               period=per, interval=YFINANCE_INTERVAL,
                               progress=False)
            data = _flatten(data)
            if data is None or data.empty:
                return None
            return data.dropna()
        except Exception:
            return None

    def update_ticker_data(self, ticker: str, force_full: bool = False):
        fmt = self._format_ticker(ticker)
        try:
            if not force_full:
                last_date = self.db.get_last_date(fmt)
                if last_date:
                    nxt = last_date + timedelta(days=1)
                    start = nxt.strftime('%Y-%m-%d')
                    now = datetime.now()
                    today = now.strftime('%Y-%m-%d')
                    tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
                    if start > today:
                        return True, f"{ticker}: Already up to date"
                    data = self.fetch_data(ticker, start_date=start,
                                           end_date=tomorrow)
                    if data is None or data.empty:
                        return True, f"{ticker}: No new data"
                    n = self._save_rows(fmt, data)
                    return True, f"{ticker}: Added {n} rows"
            data = self.fetch_data(ticker, period=YFINANCE_PERIOD)
            if data is None or data.empty:
                return False, f"{ticker}: Failed"
            self.db.delete_ticker(fmt)
            n = self._save_rows(fmt, data)
            return True, f"{ticker}: Saved {n} rows"
        except Exception as e:
            return False, f"{ticker}: Error {e}"

    def update_all_tickers(self, force_full: bool = False):
        out = {}
        for t in self.get_tickers():
            out[t] = self.update_ticker_data(t, force_full)[1]
        return out

    def get_ticker_data(self, ticker: str, start_date: Optional[str] = None,
                        end_date: Optional[str] = None):
        fmt = self._format_ticker(ticker)
        df = _flatten(self.db.get_data(fmt, start_date, end_date))
        if df is None or df.empty:
            if self.update_ticker_data(ticker)[0]:
                df = _flatten(self.db.get_data(fmt, start_date, end_date))
            else:
                return None
        return df

    def get_ihsg_data(self, start_date: Optional[str] = None,
                      end_date: Optional[str] = None):
        df = _flatten(self.db.get_data(IHSG_SYMBOL, start_date, end_date))
        ok = df is not None and not df.empty
        if ok and start_date is None:
            try:
                nxt = df.index[-1] + timedelta(days=1)
                start = nxt.strftime('%Y-%m-%d')
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
                if start < today:
                    raw = yf.download(IHSG_SYMBOL, start=start,
                                      end=tomorrow,
                                      interval=YFINANCE_INTERVAL,
                                      progress=False)
                    new = _flatten(raw)
                    if new is not None and not new.empty:
                        self._save_rows(IHSG_SYMBOL, new)
                        q = self.db.get_data(IHSG_SYMBOL, start_date, end_date)
                        df = _flatten(q)
            except Exception:
                pass
        if df is None or df.empty:
            raw = yf.download(IHSG_SYMBOL, period=YFINANCE_PERIOD,
                              interval=YFINANCE_INTERVAL, progress=False)
            data = _flatten(raw)
            if data is not None and not data.empty:
                self.db.delete_ticker(IHSG_SYMBOL)
                self._save_rows(IHSG_SYMBOL, data)
                q = self.db.get_data(IHSG_SYMBOL, start_date, end_date)
                df = _flatten(q)
        if df is None or df.empty:
            return None
        return df

    def get_latest_price(self, ticker: str) -> Optional[float]:
        try:
            fmt = self._format_ticker(ticker)
            df = _flatten(self.db.get_data(fmt))
            if df is not None and not df.empty:
                return float(df['Close'].iloc[-1])
            raw = yf.download(fmt, period='1d', progress=False)
            data = _flatten(raw)
            if data is None or data.empty:
                return None
            return float(data['Close'].iloc[-1])
        except Exception:
            return None

    def validate_ticker(self, ticker: str) -> bool:
        try:
            fmt = self._format_ticker(ticker)
            data = yf.download(fmt, period='5d', progress=False)
            return data is not None and not data.empty
        except Exception:
            return False


data_engine = DataEngine()
