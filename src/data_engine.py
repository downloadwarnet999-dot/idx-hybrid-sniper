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


class DataEngine:
    """Handles data fetching and updating from Yahoo Finance"""

    def __init__(self):
        self.db = market_db
        self.tickers_file = TICKERS_FILE
        self._ensure_tickers_file()

    def _ensure_tickers_file(self):
        """Create tickers file if not exists"""
        if not self.tickers_file.exists():
            # Default IDX blue chip stocks
            default_tickers = [
                'BBCA', 'BBRI', 'BMRI', 'BBNI', 'TLKM',
                'ASII', 'UNVR', 'ICBP', 'INDF', 'KLBF',
                'ADRO', 'ITMG', 'PTBA', 'ANTM', 'INCO',
                'BSDE', 'PWON', 'SMGR', 'WIKA', 'PTPP'
            ]

            self.save_tickers(default_tickers)

    def get_tickers(self) -> List[str]:
        """Load tickers from JSON file"""
        if not self.tickers_file.exists():
            return []

        with open(self.tickers_file, 'r') as f:
            data = json.load(f)

        return data.get('tickers', [])

    def save_tickers(self, tickers: List[str]):
        """Save tickers to JSON file"""
        self.tickers_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'tickers': sorted(list(set(tickers))),  # Remove duplicates and sort
            'updated_at': datetime.now().isoformat()
        }

        with open(self.tickers_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_ticker(self, ticker: str) -> bool:
        """Add a new ticker to watchlist"""
        tickers = self.get_tickers()

        if ticker not in tickers:
            tickers.append(ticker)
            self.save_tickers(tickers)
            return True

        return False

    def remove_ticker(self, ticker: str) -> bool:
        """Remove ticker from watchlist"""
        tickers = self.get_tickers()

        if ticker in tickers:
            tickers.remove(ticker)
            self.save_tickers(tickers)
            self.db.delete_ticker(ticker + IDX_SUFFIX)
            return True

        return False

    def import_from_csv(self, csv_path: str, replace: bool = False) -> Tuple[int, List[str]]:
        """
        Import tickers from CSV file

        CSV Format:
        - Single column with header 'ticker' or 'TICKER'
        - Or no header, just ticker list (one per line)

        Example CSV:
        ticker
        BBCA
        BBRI
        TLKM

        Args:
            csv_path: Path to CSV file
            replace: If True, replace existing watchlist. If False, append to existing.

        Returns:
            Tuple of (count_imported, list_of_imported_tickers)
        """
        import csv

        imported_tickers = []

        try:
            with open(csv_path, 'r') as f:
                # Read all lines
                lines = f.readlines()

            # Process lines
            for i, line in enumerate(lines):
                line = line.strip()

                if not line:  # Skip empty lines
                    continue

                # Skip header if first line looks like header
                if i == 0 and line.lower() in ['ticker', 'tickers', 'symbol', 'symbols', 'stock', 'stocks']:
                    continue

                # Try CSV parsing first
                try:
                    row = next(csv.reader([line]))
                    ticker = row[0].strip().upper()
                except:
                    # If CSV parsing fails, treat whole line as ticker
                    ticker = line.upper()

                # Validate ticker
                if ticker and len(ticker) <= 10 and ticker.isalnum():
                    imported_tickers.append(ticker)

            if not imported_tickers:
                return 0, []

            # Get existing tickers
            if replace:
                final_tickers = imported_tickers
            else:
                existing_tickers = self.get_tickers()
                final_tickers = list(set(existing_tickers + imported_tickers))

            # Save
            self.save_tickers(final_tickers)

            return len(imported_tickers), imported_tickers

        except Exception as e:
            print(f"Error importing CSV: {e}")
            return 0, []

    def export_to_csv(self, csv_path: str) -> bool:
        """
        Export current watchlist to CSV file

        Args:
            csv_path: Path to save CSV file

        Returns:
            Success status
        """
        import csv

        tickers = self.get_tickers()

        if not tickers:
            return False

        try:
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ticker'])  # Header

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
        """
        Fetch OHLCV data from Yahoo Finance

        Args:
            ticker: Stock ticker (without .JK suffix)
            period: Period string (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            start_date: Start date (YYYY-MM-DD) - overrides period
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data or None if failed
        """
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

            # Clean data
            data = data.dropna()

            return data

        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None

    def update_ticker_data(self, ticker: str, force_full: bool = False) -> Tuple[bool, str]:
        """
        Update data for a ticker (incremental or full)

        Args:
            ticker: Stock ticker (without .JK suffix)
            force_full: If True, fetch all data regardless of existing data

        Returns:
            Tuple of (success: bool, message: str)
        """
        formatted_ticker = self._format_ticker(ticker)

        try:
            if not force_full:
                # Check last date in database
                last_date = self.db.get_last_date(formatted_ticker)

                if last_date:
                    # Fetch only new data
                    start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    today = datetime.now().strftime('%Y-%m-%d')

                    # If already up to date
                    if start_date >= today:
                        return True, f"{ticker}: Already up to date"

                    # Incremental fetch
                    data = self.fetch_data(ticker, start_date=start_date, end_date=today)

                    if data is None or data.empty:
                        return True, f"{ticker}: No new data available"

                    rows = self.db.save_data(formatted_ticker, data)
                    return True, f"{ticker}: Added {rows} new rows"

            # Full fetch
            data = self.fetch_data(ticker, period=YFINANCE_PERIOD)

            if data is None or data.empty:
                return False, f"{ticker}: Failed to fetch data"

            # Delete old data if exists
            self.db.delete_ticker(formatted_ticker)

            # Save new data
            rows = self.db.save_data(formatted_ticker, data)
            return True, f"{ticker}: Saved {rows} rows (full update)"

        except Exception as e:
            return False, f"{ticker}: Error - {str(e)}"

    def update_all_tickers(self, force_full: bool = False) -> Dict[str, str]:
        """
        Update data for all tickers in watchlist

        Returns:
            Dictionary mapping ticker to status message
        """
        tickers = self.get_tickers()
        results = {}

        for ticker in tickers:
            success, message = self.update_ticker_data(ticker, force_full)
            results[ticker] = message

        return results

    def get_ticker_data(self, ticker: str, start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Get ticker data from database (fetch if not available)

        Args:
            ticker: Stock ticker (without .JK suffix)
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            DataFrame with OHLCV data or None
        """
        formatted_ticker = self._format_ticker(ticker)

        # Try to get from database
        df = self.db.get_data(formatted_ticker, start_date, end_date)

        # If empty, fetch from Yahoo Finance
        if df.empty:
            print(f"No data in DB for {ticker}, fetching from Yahoo Finance...")
            success, message = self.update_ticker_data(ticker)

            if success:
                df = self.db.get_data(formatted_ticker, start_date, end_date)
            else:
                return None

        return df

    def get_ihsg_data(self, start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Get IHSG (Jakarta Composite Index) data

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            DataFrame with IHSG OHLCV data
        """
        # Check database first
        df = self.db.get_data(IHSG_SYMBOL, start_date, end_date)

        # If empty or outdated, fetch new data
        if df.empty:
            print("Fetching IHSG data from Yahoo Finance...")

            data = yf.download(IHSG_SYMBOL, period=YFINANCE_PERIOD,
                             interval=YFINANCE_INTERVAL, progress=False)

            if not data.empty:
                self.db.delete_ticker(IHSG_SYMBOL)
                self.db.save_data(IHSG_SYMBOL, data)
                df = self.db.get_data(IHSG_SYMBOL, start_date, end_date)

        return df if not df.empty else None

    def get_latest_price(self, ticker: str) -> Optional[float]:
        """
        Get the most recent closing price for a ticker

        Args:
            ticker: Stock ticker (without .JK suffix)

        Returns:
            Latest close price or None
        """
        formatted_ticker = self._format_ticker(ticker)

        try:
            # Try database first
            df = self.db.get_data(formatted_ticker)

            if not df.empty:
                return float(df['Close'].iloc[-1])

            # Fetch from Yahoo Finance
            data = yf.download(formatted_ticker, period='1d', progress=False)

            if not data.empty:
                return float(data['Close'].iloc[-1])

            return None

        except Exception as e:
            print(f"Error getting latest price for {ticker}: {e}")
            return None

    def validate_ticker(self, ticker: str) -> bool:
        """
        Check if ticker exists on Yahoo Finance

        Args:
            ticker: Stock ticker (without .JK suffix)

        Returns:
            True if ticker is valid
        """
        formatted_ticker = self._format_ticker(ticker)

        try:
            data = yf.download(formatted_ticker, period='5d', progress=False)
            return not data.empty
        except:
            return False


# Initialize global data engine
data_engine = DataEngine()
