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

    def _safe_query(self, query, params=None, fetch='all'):
        from src.db_manager import db_manager
        return db_manager.execute_query(query, params, fetch=fetch)

    def record_entry(self, ticker: str, entry_price: float, lot_size: int,
                    sl_price: float, tp1_price: float,
                    entry_date: Optional[str] = None,
                    notes: str = "") -> int:
        """Record a new trade entry"""
        if entry_date is None:
            entry_date = datetime.now().strftime('%Y-%m-%d')
        try:
            trade_id = self.db.add_trade(
                ticker=ticker, entry_date=entry_date, entry_price=entry_price,
                lot_size=lot_size, sl_price=sl_price, tp1_price=tp1_price, notes=notes
            )
            return trade_id
        except AttributeError:
            q = """INSERT INTO trades (ticker, entry_date, entry_price, lot_size, sl_price, tp1_price, notes, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 'OPEN') RETURNING id"""
            res = self._safe_query(q, (ticker, entry_date, entry_price, lot_size, sl_price, tp1_price, notes), fetch='one')
            return res[0] if res else 0

    def get_open_positions(self, with_current_prices: bool = False) -> pd.DataFrame:
        """Get all open positions"""
        try:
            df = self.db.get_open_trades()
        except AttributeError:
            q = "SELECT * FROM trades WHERE exit_date IS NULL OR status = 'OPEN'"
            results = self._safe_query(q, fetch='all')
            df = pd.DataFrame(results) if results else pd.DataFrame()

        if df.empty:
            return df

        if with_current_prices:
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
        """Update stop loss (for trailing)"""
        if not notes:
            notes = f"Trailing SL updated to {new_sl}"
        try:
            return self.db.update_sl(trade_id, new_sl, notes)
        except AttributeError:
            q = "UPDATE trades SET sl_price = %s, notes = %s WHERE id = %s"
            self._safe_query(q, (new_sl, notes, trade_id))
            return True

    def sell_partial_tp1(self, trade_id: int, exit_price: float,
                        exit_date: Optional[str] = None) -> bool:
        """Record partial exit at TP1"""
        if exit_date is None:
            exit_date = datetime.now().strftime('%Y-%m-%d')
        try:
            trade = self.db.get_trade_by_id(trade_id)
        except AttributeError:
            trade = self._safe_query("SELECT * FROM trades WHERE id = %s", (trade_id,), fetch='one')

        if not trade:
            return False

        entry_price = trade['entry_price'] if isinstance(trade, dict) else trade[3]
        lot_size = trade['lot_size'] if isinstance(trade, dict) else trade[4]

        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        pnl_idr = (exit_price - entry_price) * (lot_size * TP1_SELL_PERCENT / 100) * 100
        notes = f"TP1 Hit ({exit_date}): Sold {TP1_SELL_PERCENT}% @ {exit_price} | Profit: {pnl_pct:.2f}% ({pnl_idr:,.0f} IDR)"
        
        try:
            return self.db.update_sl(trade_id, entry_price, notes)
        except AttributeError:
            self._safe_query("UPDATE trades SET sl_price = %s, notes = %s WHERE id = %s", (entry_price, notes, trade_id))
            return True

    def close_position(self, trade_id: int, exit_price: float,
                      exit_date: Optional[str] = None,
                      reason: str = "") -> bool:
        """Close a position completely"""
        if exit_date is None:
            exit_date = datetime.now().strftime('%Y-%m-%d')
        notes = f"Exit Reason: {reason}" if reason else "Position closed"
        try:
            return self.db.close_trade(trade_id, exit_date, exit_price, notes)
        except AttributeError:
            try:
                trade = self._safe_query("SELECT * FROM trades WHERE id = %s", (trade_id,), fetch='one')
                entry_price = trade['entry_price'] if isinstance(trade, dict) else trade[3]
                lot_size = trade['lot_size'] if isinstance(trade, dict) else trade[4]
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                pnl_amount = (exit_price - entry_price) * lot_size * 100
            except:
                pnl_pct = 0
                pnl_amount = 0
                
            q = """UPDATE trades SET exit_date = %s, exit_price = %s, notes = %s, 
                   status = 'CLOSED', pnl_percent = %s, pnl_amount = %s WHERE id = %s"""
            self._safe_query(q, (exit_date, exit_price, notes, pnl_pct, pnl_amount, trade_id))
            return True

    def get_closed_trades(self, limit: int = 50) -> pd.DataFrame:
        """Get recent closed trades"""
        try:
            return self.db.get_closed_trades(limit)
        except AttributeError:
            q = f"SELECT * FROM trades WHERE exit_date IS NOT NULL OR status = 'CLOSED' ORDER BY exit_date DESC LIMIT {limit}"
            results = self._safe_query(q, fetch='all')
            return pd.DataFrame(results) if results else pd.DataFrame()

    def get_statistics(self) -> Dict:
        """Get trading performance statistics"""
        try:
            return self.db.get_statistics()
        except AttributeError:
            stats = {
                'total_trades': 0, 'win_rate': 0.0, 'avg_pnl_percent': 0.0,
                'total_pnl_idr': 0, 'best_trade_percent': 0.0, 'worst_trade_percent': 0.0
            }
            q = "SELECT * FROM trades WHERE status = 'CLOSED' OR exit_date IS NOT NULL"
            results = self._safe_query(q, fetch='all')
            if not results:
                return stats
            df = pd.DataFrame(results)
            if 'pnl_percent' not in df.columns:
                return stats
            stats['total_trades'] = len(df)
            wins = len(df[df['pnl_percent'] > 0])
            stats['win_rate'] = (wins / stats['total_trades']) * 100 if stats['total_trades'] > 0 else 0
            stats['avg_pnl_percent'] = float(df['pnl_percent'].mean())
            stats['total_pnl_idr'] = float(df['pnl_amount'].sum()) if 'pnl_amount' in df.columns else 0
            stats['best_trade_percent'] = float(df['pnl_percent'].max())
            stats['worst_trade_percent'] = float(df['pnl_percent'].min())
            return stats

    def calculate_lot_size(self, capital: float, risk_pct: float,
                          entry_price: float, sl_price: float) -> int:
        """Calculate position size based on risk management"""
        risk_amount = capital * (risk_pct / 100)
        risk_per_share = entry_price - sl_price
        if risk_per_share <= 0:
            return 0
        shares = risk_amount / risk_per_share
        lots = int(shares / 100)
        return lots

    def check_exit_conditions(self, trade_id: int, current_price: float,
                             supertrend_value: float,
                             supertrend_direction: int) -> Dict:
        """Check if any exit conditions are met for a trade"""
        try:
            trade = self.db.get_trade_by_id(trade_id)
        except AttributeError:
            trade = self._safe_query("SELECT * FROM trades WHERE id = %s", (trade_id,), fetch='one')

        if not trade:
            return {'error': 'Trade not found or already closed'}
            
        status = trade.get('status') if isinstance(trade, dict) else None
        if status and status != 'OPEN':
            return {'error': 'Trade not found or already closed'}

        entry_price = trade['entry_price'] if isinstance(trade, dict) else trade[3]
        sl_price = trade['sl_price'] if isinstance(trade, dict) else trade[5]
        tp1_price = trade['tp1_price'] if isinstance(trade, dict) else trade[6]

        result = {
            'trade_id': trade_id,
            'ticker': trade['ticker'] if isinstance(trade, dict) else trade[1],
            'current_price': current_price,
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp1_price': tp1_price,
            'signals': []
        }

        if current_price <= sl_price:
            result['signals'].append({
                'type': 'STOP_LOSS', 'action': 'CLOSE_ALL',
                'reason': f"Price ({current_price}) hit SL ({sl_price})"
            })

        if current_price >= tp1_price:
            result['signals'].append({
                'type': 'TP1', 'action': 'SELL_50%',
                'reason': f"Price ({current_price}) hit TP1 ({tp1_price})"
            })

        if supertrend_direction == -1:
            result['signals'].append({
                'type': 'TRAILING_STOP', 'action': 'CLOSE_REMAINING',
                'reason': f"SuperTrend flipped bearish @ {supertrend_value:.2f}"
            })

        return result

# Initialize global journal manager
journal_mgr = JournalManager()
