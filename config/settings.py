"""
IDX Hybrid Sniper - Configuration Settings
All shared constants and configurations
"""

import os
from pathlib import Path
import sys

# Project Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
REPORTS_DIR = BASE_DIR / 'reports'
CHARTS_DIR = REPORTS_DIR / 'charts'

# Add src to path to import config_mgr
sys.path.append(str(BASE_DIR))
from src.config_mgr import config_mgr

# Database Paths
MARKET_DB = DATA_DIR / 'market_data.db'
JOURNAL_DB = DATA_DIR / 'journal.db'
TICKERS_FILE = DATA_DIR / 'tickers.json'

# Market Settings
IHSG_SYMBOL = '^JKSE'  # Jakarta Composite Index
IDX_SUFFIX = '.JK'  # Yahoo Finance suffix for IDX stocks
MARKET_TIMEZONE = 'Asia/Jakarta'

# Dynamic Configuration Loading
# Strategy Parameters
RISK_PERCENT = config_mgr.get("RISK_PERCENT", 2.0)
MIN_LIQUIDITY_IDR = config_mgr.get("MIN_LIQUIDITY_IDR", 5_000_000_000)

# Technical Indicator Settings
HMA_PERIOD = config_mgr.get("HMA_PERIOD", 60)
SUPERTREND_ATR_PERIOD = 10
SUPERTREND_MULTIPLIER = config_mgr.get("SUPERTREND_MULTIPLIER", 3.0)
STOCH_K_PERIOD = 5
STOCH_D_PERIOD = 3
STOCH_SMOOTH = 3
STOCH_OVERSOLD = 30
STOCH_OVERBOUGHT = 70
VOLUME_MA_PERIOD = 20
RS_LOOKBACK_PERIOD = 20

# Stop Loss & Take Profit
SL_ATR_MULTIPLIER = config_mgr.get("SL_ATR_MULTIPLIER", 2.0)
TP1_ATR_MULTIPLIER = config_mgr.get("TP1_ATR_MULTIPLIER", 3.0)
TP1_SELL_PERCENT = 50

# Volume & RS Thresholds
VOLUME_LOW_THRESHOLD = config_mgr.get("VOLUME_LOW_THRESHOLD", 0.8)
VOLUME_HIGH_THRESHOLD = 1.5
RS_STRONG = config_mgr.get("RS_STRONG", 5.0)
RS_WEAK = config_mgr.get("RS_WEAK", -5.0)

# Fair Value Gap (FVG) Settings
FVG_MIN_ATR_RATIO = 0.5
FVG_LOOKBACK = 100

# Telegram Settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

# Scanner Schedule
SCAN_TIME = '08:00'

# IDX Sector Classification
SECTORS = {
    'FINANCE': ['BBCA', 'BBRI', 'BMRI', 'BBNI', 'BBTN'],
    'CONSUMER': ['UNVR', 'INDF', 'ICBP', 'MYOR', 'KLBF'],
    'INFRASTRUCTURE': ['TLKM', 'EXCL', 'JSMR', 'WIKA', 'PTPP'],
    'MINING': ['ANTM', 'INCO', 'PTBA', 'ADRO', 'ITMG'],
    'PROPERTY': ['BSDE', 'PWON', 'CTRA', 'SMRA', 'ASRI'],
}

# Data Fetching Settings
YFINANCE_PERIOD = '1y'
YFINANCE_INTERVAL = '1d'

# Streamlit Dashboard Settings
DASHBOARD_TITLE = 'IDX Hybrid Sniper Dashboard'
DASHBOARD_ICON = '🎯'
DASHBOARD_LAYOUT = 'wide'

# Chart Settings
CHART_HEIGHT = 600
CHART_TEMPLATE = 'plotly_dark'

# Display Settings
MAX_DISPLAY_STOCKS = 50
AGGRID_HEIGHT = 400

# Advanced Filter Settings
VOLUME_SPIKE_THRESHOLD = 3.0
REJECTION_WICK_MIN = 0.4
REJECTION_CLOSE_MIN = 0.6
DISCOUNT_ZONE_LOOKBACK = 50
SWEET_SPOT_LOW = 0.2
SWEET_SPOT_HIGH = 0.4
RESISTANCE_LOOKBACK = 50
TP_RESISTANCE_BUFFER = 0.98
MIN_RR_AT_RESISTANCE = 1.5

# Alert Messages
ALERT_SMC_ENTRY = "🎯 {ticker} - SMC Entry Signal\n💰 FVG: {fvg_level}\n📊 Vol: {vol_status}"
ALERT_MOMENTUM_ENTRY = "⚡ {ticker} - Momentum Entry\n📈 HMA Support\n📊 Stoch: {stoch_value}"
ALERT_TP1_HIT = "✅ {ticker} - TP1 Tercapai!\n💵 Profit: {profit}%"
ALERT_SL_HIT = "🛑 {ticker} - Stop Loss!\n📉 Loss: {loss}%"
ALERT_TRAILING_EXIT = "🔔 {ticker} - SuperTrend Exit\n💰 Total Profit: {profit}%"

# Color Scheme
COLOR_BULLISH = '#089981'
COLOR_BEARISH = '#F23645'
COLOR_NEUTRAL = '#878b94'
COLOR_WARNING = '#FFA500'
COLOR_SUCCESS = '#00ff68'

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'