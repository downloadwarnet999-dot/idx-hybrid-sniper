import os
import sys
import requests
from datetime import datetime

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_engine import data_engine
from src.strategy import strategy

def send_rich_report():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Missing Telegram secrets in environment.")
        return

    print("🔍 Running fast DB scan for Telegram report...")
    tickers = data_engine.get_tickers()
    signals = strategy.scan_tickers(tickers, data_engine)
    
    real_signals = [s for s in signals if s.signal_type != 'NO_SIGNAL']
    now = datetime.now()
    
    if not real_signals:
        msg = f"<b>😴 IDX SNIPER REPORT</b>\n<i>📅 {now.strftime('%Y-%m-%d %H:%M')} WIB</i>\n\n"
        msg += "Tidak ada sinyal entry hari ini. Pasar sedang konsolidasi atau semua emiten terfilter."
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        print("✅ Sent 'No Signals' report.")
        return

    # Count types
    smc_entry = len([s for s in real_signals if s.signal_type == 'SMC_ENTRY'])
    smc_setup = len([s for s in real_signals if s.signal_type == 'SMC_SETUP'])
    momentum = len([s for s in real_signals if s.signal_type == 'MOMENTUM_ENTRY'])
    
    msg = f"<b>🎯 IDX HYBRID SNIPER - DAILY REPORT</b>\n"
    msg += f"<i>📅 {now.strftime('%Y-%m-%d %H:%M')} WIB</i>\n\n"
    
    msg += f"<b>📊 MARKET SUMMARY</b>\n"
    msg += f"┣ Scanned: {len(tickers)} tickers\n"
    msg += f"┣ 🟢 SMC Confirmed: {smc_entry}\n"
    msg += f"┣ 🟡 SMC Setup: {smc_setup}\n"
    msg += f"┗ ⚡ Momentum: {momentum}\n\n"
    
    # Monospaced table (max 10 rows to avoid 4096 char limit)
    msg += "<pre>\n"
    msg += f"{'TICKER':<8} | {'TYPE':<10} | {'ENTRY':<7} | {'SL':<7} | {'R:R':<5}\n"
    msg += "-" * 45 + "\n"
    for s in real_signals[:10]:
        t_type = s.signal_type.replace('SMC_', '').replace('_ENTRY', ' ENT').replace('_SETUP', ' SET')
        msg += f"{s.ticker:<8} | {t_type:<10} | {s.entry_price:<7.0f} | {s.sl_price:<7.0f} | 1:{s.risk_reward_ratio:<3.1f}\n"
    msg += "</pre>\n\n"
    
    # Deep dive top 3
    msg += "<b>🔍 TOP SETUPS DEEP-DIVE:</b>\n"
    for s in real_signals[:3]:
        msg += f"\n<b>🚀 {s.ticker}</b> ({s.signal_type})\n"
        msg += f"┣ Entry: <code>{s.entry_price:.0f}</code> | SL: <code>{s.sl_price:.0f}</code> | TP1: <code>{s.tp1_price:.0f}</code>\n"
        msg += f"┣ RS Score: <b>{s.rs_score:+.1f}%</b> | Vol: {s.volume_status}\n"
        msg += f"┗ Zone: {s.zone_type or 'N/A'}\n"
        msg += f"  <i>{s.reason}</i>\n"

    msg += "\n<i>📊 Full CSV/HTML reports available on your Streamlit Dashboard.</i>"

    res = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                  json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
    
    if res.ok:
        print("✅ Rich Telegram report sent successfully!")
    else:
        print(f"❌ Failed to send Telegram report: {res.text}")

if __name__ == "__main__":
    send_rich_report()
