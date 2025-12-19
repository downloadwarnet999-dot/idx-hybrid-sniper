"""
IDX Hybrid Sniper - Telegram Notifier
Send trading signals and alerts via Telegram
"""

import requests
from pathlib import Path
from typing import Optional, List
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED,
    ALERT_SMC_ENTRY, ALERT_MOMENTUM_ENTRY,
    ALERT_TP1_HIT, ALERT_SL_HIT, ALERT_TRAILING_EXIT
)


class TelegramNotifier:
    """Send notifications via Telegram Bot"""

    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.enabled = TELEGRAM_ENABLED

        if not self.enabled:
            try:
                print("⚠️ Telegram notifications disabled. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment.")
            except:
                print("WARNING: Telegram notifications disabled. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment.")

    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        Send text message to Telegram

        Args:
            message: Message text
            parse_mode: 'Markdown' or 'HTML'

        Returns:
            Success status
        """
        if not self.enabled:
            print(f"[Telegram Disabled] {message}")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode
        }

        try:
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            return True

        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def send_smc_entry_signal(self, signal) -> bool:
        """
        Send SMC entry signal notification

        Args:
            signal: Signal object from strategy

        Returns:
            Success status
        """
        vol_emoji = "🟢" if signal.volume_status == 'LOW' else "🟡" if signal.volume_status == 'NORMAL' else "🔴"

        message = f"""
🎯 *SMC ENTRY SIGNAL*

*{signal.ticker}* - Smart Money Concepts Setup

📊 *Price Info:*
Current: Rp {signal.current_price:,.0f}
Entry: Rp {signal.entry_price:,.0f} (FVG Mid)
SL: Rp {signal.sl_price:,.0f}
TP1: Rp {signal.tp1_price:,.0f}

💰 *FVG Zone:* {signal.fvg_level}

{vol_emoji} *Volume:* {signal.volume_status}
{'✅ Safe Pullback - Low Volume' if signal.volume_status == 'LOW' else '⚠️ Risk! High Volume Pullback' if signal.volume_status == 'HIGH' else 'Normal Volume'}

📈 *Relative Strength:* {signal.rs_score:+.2f}%
{'🔥 Outperforming IHSG' if signal.rs_score > 0 else '❄️ Underperforming IHSG'}

⚖️ *Risk/Reward:* 1:{signal.risk_reward_ratio:.2f}

💡 *Strategy:* {signal.reason}
"""

        return self.send_message(message)

    def send_momentum_entry_signal(self, signal) -> bool:
        """
        Send momentum entry signal notification

        Args:
            signal: Signal object from strategy

        Returns:
            Success status
        """
        message = f"""
⚡ *MOMENTUM ENTRY SIGNAL*

*{signal.ticker}* - HMA Support + Stochastic

📊 *Price Info:*
Current: Rp {signal.current_price:,.0f}
SL: Rp {signal.sl_price:,.0f}
TP1: Rp {signal.tp1_price:,.0f}

📉 *Stochastic:* {signal.stoch_value:.1f} (Oversold)

📈 *Relative Strength:* {signal.rs_score:+.2f}%

⚖️ *Risk/Reward:* 1:{signal.risk_reward_ratio:.2f}

💡 *Strategy:* {signal.reason}
"""

        return self.send_message(message)

    def send_watchlist_summary(self, signals: List, total_scanned: int) -> bool:
        """
        Send daily watchlist summary

        Args:
            signals: List of Signal objects with entry setups
            total_scanned: Total number of stocks scanned

        Returns:
            Success status
        """
        smc_signals = [s for s in signals if s.signal_type == 'SMC_ENTRY']
        momentum_signals = [s for s in signals if s.signal_type == 'MOMENTUM_ENTRY']

        message = f"""
📋 *DAILY WATCHLIST*

🔍 Scanned: {total_scanned} stocks

🎯 *SMC Entries:* {len(smc_signals)}
"""

        for signal in smc_signals[:5]:  # Limit to top 5
            vol_emoji = "🟢" if signal.volume_status == 'LOW' else "🟡"
            message += f"\n• {signal.ticker}: {signal.current_price:,.0f} {vol_emoji}"

        message += f"\n\n⚡ *Momentum Entries:* {len(momentum_signals)}"

        for signal in momentum_signals[:5]:
            message += f"\n• {signal.ticker}: {signal.current_price:,.0f}"

        if len(signals) == 0:
            message += "\n\n😴 No signals today. Market in consolidation."

        return self.send_message(message)

    def send_tp1_alert(self, ticker: str, entry_price: float,
                      exit_price: float, profit_pct: float) -> bool:
        """Send TP1 hit alert"""
        message = ALERT_TP1_HIT.format(
            ticker=ticker,
            profit=f"{profit_pct:.2f}"
        )

        message += f"\n\nEntry: Rp {entry_price:,.0f}\nTP1: Rp {exit_price:,.0f}"
        message += "\n\n💡 Geser SL ke Break Even untuk posisi sisa 50%"

        return self.send_message(message)

    def send_sl_alert(self, ticker: str, entry_price: float,
                     sl_price: float, loss_pct: float) -> bool:
        """Send Stop Loss alert"""
        message = ALERT_SL_HIT.format(
            ticker=ticker,
            loss=f"{loss_pct:.2f}"
        )

        message += f"\n\nEntry: Rp {entry_price:,.0f}\nSL: Rp {sl_price:,.0f}"
        message += "\n\n💡 Risk management worked. Onto the next trade!"

        return self.send_message(message)

    def send_trailing_exit_alert(self, ticker: str, entry_price: float,
                                 exit_price: float, total_profit_pct: float) -> bool:
        """Send SuperTrend trailing exit alert"""
        message = ALERT_TRAILING_EXIT.format(
            ticker=ticker,
            profit=f"{total_profit_pct:.2f}"
        )

        message += f"\n\nEntry: Rp {entry_price:,.0f}\nExit: Rp {exit_price:,.0f}"
        message += "\n\n🎯 Trend follower strategy executed perfectly!"

        return self.send_message(message)

    def send_custom_alert(self, title: str, message: str) -> bool:
        """Send custom alert message"""
        formatted_message = f"*{title}*\n\n{message}"
        return self.send_message(formatted_message)


# Initialize global notifier
notifier = TelegramNotifier()
