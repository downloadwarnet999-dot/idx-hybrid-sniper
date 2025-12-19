"""
IDX Hybrid Sniper - Trading Journal Manager
High-level interface for trading journal operations
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.database import journal_db
from src.data_engine import data_engine
from config.settings import TP1_SELL_PERCENT


class JournalManager:
    """High-level trading journal management"""

    def __init__(self):
        self.db = journal_db
        self.data_engine = data_engine

    def record_entry(self, ticker: str, entry_price: float, lot_size: int,
                    sl_price: float, tp1_price: float,
                    entry_date: Optional[str] = None,
                    notes: str = "") -> int:
        """
        Record a new trade entry

        Args:
            ticker: Stock ticker (without .JK)
            entry_price: Entry price per share
            lot_size: Number of lots (1 lot = 100 shares IDX)
            sl_price: Stop loss price
            tp1_price: Take profit 1 price
            entry_date: Entry date (YYYY-MM-DD), defaults to today
            notes: Additional notes

        Returns:
            Trade ID
        """
        if entry_date is None:
            entry_date = datetime.now().strftime('%Y-%m-%d')

        trade_id = self.db.add_trade(
            ticker=ticker,
            entry_date=entry_date,
            entry_price=entry_price,
            lot_size=lot_size,
            sl_price=sl_price,
            tp1_price=tp1_price,
            notes=notes
        )

        return trade_id

    def get_open_positions(self, with_current_prices: bool = False) -> pd.DataFrame:
        """
        Get all open positions

        Args:
            with_current_prices: If True, fetch current prices and calculate floating P/L

        Returns:
            DataFrame with open positions
        """
        df = self.db.get_open_trades()

        if df.empty:
            return df

        if with_current_prices:
            # Add current price and floating P/L
            current_prices = []
            floating_pnl_pct = []
            floating_pnl_idr = []

            for _, row in df.iterrows():
                ticker = row['ticker']
                current_price = self.data_engine.get_latest_price(ticker)

                if current_price:
                    pnl_pct = ((current_price - row['entry_price']) / row['entry_price']) * 100
                    pnl_idr = (current_price - row['entry_price']) * row['lot_size'] * 100

                    current_prices.append(current_price)
                    floating_pnl_pct.append(pnl_pct)
                    floating_pnl_idr.append(pnl_idr)
                else:
                    current_prices.append(None)
                    floating_pnl_pct.append(None)
                    floating_pnl_idr.append(None)

            df['current_price'] = current_prices
            df['floating_pnl_pct'] = floating_pnl_pct
            df['floating_pnl_idr'] = floating_pnl_idr

        return df

    def update_trailing_stop(self, trade_id: int, new_sl: float, notes: str = "") -> bool:
        """
        Update stop loss (for trailing)

        Args:
            trade_id: Trade ID
            new_sl: New stop loss price
            notes: Reason for update

        Returns:
            Success status
        """
        if not notes:
            notes = f"Trailing SL updated to {new_sl}"

        return self.db.update_sl(trade_id, new_sl, notes)

    def sell_partial_tp1(self, trade_id: int, exit_price: float,
                        exit_date: Optional[str] = None) -> bool:
        """
        Record partial exit at TP1 (typically 50% of position)

        This updates the notes but keeps position open.
        User should manually update lot_size if tracking remaining position.

        Args:
            trade_id: Trade ID
            exit_price: Exit price
            exit_date: Exit date, defaults to today

        Returns:
            Success status
        """
        if exit_date is None:
            exit_date = datetime.now().strftime('%Y-%m-%d')

        trade = self.db.get_trade_by_id(trade_id)

        if not trade:
            return False

        # Calculate profit on 50% position
        pnl_pct = ((exit_price - trade['entry_price']) / trade['entry_price']) * 100
        pnl_idr = (exit_price - trade['entry_price']) * (trade['lot_size'] * TP1_SELL_PERCENT / 100) * 100

        notes = f"TP1 Hit ({exit_date}): Sold {TP1_SELL_PERCENT}% @ {exit_price} | Profit: {pnl_pct:.2f}% ({pnl_idr:,.0f} IDR)"

        # Update notes and move SL to breakeven
        return self.db.update_sl(trade['entry_price'], trade_id, notes)

    def close_position(self, trade_id: int, exit_price: float,
                      exit_date: Optional[str] = None,
                      reason: str = "") -> bool:
        """
        Close a position completely

        Args:
            trade_id: Trade ID
            exit_price: Exit price
            exit_date: Exit date, defaults to today
            reason: Exit reason (e.g., 'SuperTrend Exit', 'Stop Loss')

        Returns:
            Success status
        """
        if exit_date is None:
            exit_date = datetime.now().strftime('%Y-%m-%d')

        notes = f"Exit Reason: {reason}" if reason else "Position closed"

        return self.db.close_trade(trade_id, exit_date, exit_price, notes)

    def get_closed_trades(self, limit: int = 50) -> pd.DataFrame:
        """Get recent closed trades"""
        return self.db.get_closed_trades(limit)

    def get_statistics(self) -> Dict:
        """Get trading performance statistics"""
        return self.db.get_statistics()

    def calculate_lot_size(self, capital: float, risk_pct: float,
                          entry_price: float, sl_price: float) -> int:
        """
        Calculate position size based on risk management

        Formula: Lot Size = (Capital × Risk%) / (Entry - SL) / 100

        Args:
            capital: Total trading capital (IDR)
            risk_pct: Risk percentage (e.g., 2 for 2%)
            entry_price: Planned entry price
            sl_price: Stop loss price

        Returns:
            Number of lots (rounded down for safety)
        """
        risk_amount = capital * (risk_pct / 100)
        risk_per_share = entry_price - sl_price

        if risk_per_share <= 0:
            return 0

        shares = risk_amount / risk_per_share
        lots = int(shares / 100)  # IDX: 1 lot = 100 shares

        return lots

    def check_exit_conditions(self, trade_id: int, current_price: float,
                             supertrend_value: float,
                             supertrend_direction: int) -> Dict:
        """
        Check if any exit conditions are met for a trade

        Returns:
            Dictionary with exit signals and recommendations
        """
        trade = self.db.get_trade_by_id(trade_id)

        if not trade or trade['status'] != 'OPEN':
            return {'error': 'Trade not found or already closed'}

        result = {
            'trade_id': trade_id,
            'ticker': trade['ticker'],
            'current_price': current_price,
            'entry_price': trade['entry_price'],
            'sl_price': trade['sl_price'],
            'tp1_price': trade['tp1_price'],
            'signals': []
        }

        # Check Stop Loss
        if current_price <= trade['sl_price']:
            result['signals'].append({
                'type': 'STOP_LOSS',
                'action': 'CLOSE_ALL',
                'reason': f"Price ({current_price}) hit SL ({trade['sl_price']})"
            })

        # Check TP1
        if current_price >= trade['tp1_price']:
            result['signals'].append({
                'type': 'TP1',
                'action': 'SELL_50%',
                'reason': f"Price ({current_price}) hit TP1 ({trade['tp1_price']})"
            })

        # Check SuperTrend Exit (bearish flip)
        if supertrend_direction == -1:
            result['signals'].append({
                'type': 'TRAILING_STOP',
                'action': 'CLOSE_REMAINING',
                'reason': f"SuperTrend flipped bearish @ {supertrend_value:.2f}"
            })

        return result


# Initialize global journal manager
journal_mgr = JournalManager()
