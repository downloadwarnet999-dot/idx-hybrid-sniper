# 📘 IDX Hybrid Sniper - User Guide

**Version 2.0** | Complete Usage Guide for CLI & Web Interface

---

## 📑 Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [CLI Usage Guide](#cli-usage-guide)
4. [Web Dashboard Guide](#web-dashboard-guide)
5. [Strategy Explanation](#strategy-explanation)
6. [Trading Workflow](#trading-workflow)
7. [Tips & Best Practices](#tips--best-practices)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Introduction

**IDX Hybrid Sniper** adalah trading tool untuk pasar saham Indonesia (IDX) yang menggunakan strategi **Smart Money Concepts (SMC)** dan **Momentum Trading**.

### Key Features

✅ **Automated Market Scanning** - Scan 900+ saham IDX otomatis
✅ **Smart Money Concepts** - Deteksi FVG, Order Blocks, Market Structure
✅ **Momentum Entries** - HMA support bounce dengan stochastic confirmation
✅ **Risk Management** - ATR-based Stop Loss & Take Profit
✅ **Trading Journal** - Track performance dengan statistik lengkap
✅ **Telegram Notifications** - Alert otomatis untuk entry signals
✅ **Interactive Charts** - Visualisasi dengan semua indikator

### Strategy Overview

**Hybrid Sniper Protocol** menggabungkan 2 entry strategies:

1. **SMC Entry** (Priority #1)
   - Buy on weakness (low volume pullback)
   - Entry di Fair Value Gap (FVG) zones
   - Trend: Bullish (SuperTrend green)

2. **Momentum Entry** (Priority #2)
   - Buy at HMA60 support
   - Stochastic turning up (< 60)
   - Trend: Bullish continuation

---

## 🚀 Getting Started

### Installation

```bash
# Clone atau extract project
cd idx_sniper

# Install dependencies
pip install -r requirements.txt

# Verify installation
python main.py --help
```

### Initial Setup

1. **Import Watchlist** (opsional)
   ```bash
   python main.py import-csv --file watchlist_template.csv
   ```

2. **Update Market Data**
   ```bash
   python main.py update --full
   ```

3. **First Scan**
   ```bash
   python main.py scan
   ```

### Telegram Setup (Optional)

Edit `.env` atau set environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

---

## 💻 CLI Usage Guide

### Command Reference

#### `scan` - Market Scanning

Scan semua saham di watchlist untuk entry signals.

```bash
# Basic scan (with data update + notifications)
python main.py scan

# Scan without notifications
python main.py scan --no-notify

# Debug mode (show detailed analysis)
python main.py scan --debug --limit 20

# Quick scan without data update
python main.py scan --no-notify
```

**Options:**
- `--no-notify` - Disable Telegram notifications
- `--debug` - Show detailed filter analysis for each stock
- `--limit N` - Only scan first N stocks (for testing)

**Output:**
- 📊 Summary statistics (total scanned, signals found)
- 🎯 SMC Entry signals table
- ⚡ Momentum Entry signals table
- 📱 Telegram notifications (if enabled)

---

#### `update` - Data Update

Update market data untuk semua saham di watchlist.

```bash
# Incremental update (only fetch new data)
python main.py update

# Full update (fetch all historical data)
python main.py update --full
```

**Options:**
- `--full` - Force full update (fetch all history)

**When to use:**
- **Incremental**: Daily routine setelah market close
- **Full**: First time setup atau jika ada data corruption

---

#### `watchlist` - View Watchlist

Lihat semua saham yang ada di watchlist.

```bash
python main.py watchlist
```

**Output:**
- Tabel berisi semua ticker di watchlist
- Total count

---

#### `add` - Add Ticker

Tambah saham baru ke watchlist.

```bash
python main.py add --ticker BBCA
```

**Process:**
1. Validasi ticker di Yahoo Finance
2. Tambah ke watchlist
3. Fetch historical data

**Example:**
```bash
# Add single ticker
python main.py add --ticker TLKM

# Add multiple tickers
python main.py add --ticker BBRI
python main.py add --ticker BMRI
python main.py add --ticker ASII
```

---

#### `remove` - Remove Ticker

Hapus saham dari watchlist.

```bash
python main.py remove --ticker BBCA
```

**Note:** Data historis juga akan dihapus dari database.

---

#### `import-csv` - Import from CSV

Import banyak ticker sekaligus dari file CSV.

```bash
# Add to existing watchlist
python main.py import-csv --file my_tickers.csv

# Replace entire watchlist
python main.py import-csv --file my_tickers.csv --replace
```

**CSV Format:**
```csv
ticker
BBCA
BBRI
TLKM
ASII
```

**Options:**
- `--replace` - Replace existing watchlist (⚠️ hapus semua ticker lama!)

See `TICKER_MANAGEMENT.md` for detailed CSV guide.

---

#### `export-csv` - Export to CSV

Export watchlist ke CSV file.

```bash
python main.py export-csv --file my_watchlist.csv
```

**Use case:** Backup watchlist atau share dengan team.

---

#### `journal` - Trading Journal

Lihat statistik trading journal.

```bash
python main.py journal
```

**Output:**
- Total trades
- Win rate
- Average P/L
- Best/Worst trades
- Total P/L (IDR)

**Note:** Manage trades via Web Dashboard.

---

### CLI Tips

**Daily Routine:**
```bash
# Morning: Update data & scan
python main.py scan

# Evening: Check journal
python main.py journal
```

**Debug Workflow:**
```bash
# 1. Test with small sample
python main.py scan --debug --limit 10

# 2. Analyze why stocks fail filters
# Check output for ❌ messages

# 3. Full scan when satisfied
python main.py scan
```

**Backup Workflow:**
```bash
# Export watchlist
python main.py export-csv --file backup_$(date +%Y%m%d).csv

# Later: Restore from backup
python main.py import-csv --file backup_20250119.csv --replace
```

---

## 🌐 Web Dashboard Guide

### Launching Dashboard

```bash
streamlit run app.py
```

Browser akan otomatis membuka `http://localhost:8501`

---

### Tab 1: Market Screener 🔍

**Purpose:** Scan pasar untuk menemukan entry signals.

#### Step-by-Step Usage

1. **Update Data** (if needed)
   - Klik `🔄 Update All Data` di sidebar
   - Wait for progress bar to complete
   - Data akan diupdate untuk semua ticker di watchlist

2. **Run Scan**
   - Klik `🔍 Scan Market Now` button
   - Wait for analysis (progress bar shown)
   - Scan akan mengecek semua ticker untuk SMC & Momentum signals

3. **View Summary Results**
   - **Summary Metrics**: Total scanned, SMC Setup count, SMC Confirmed count, Momentum count
   - **Results Table**: All signals in one table dengan kolom:
     - Ticker, Signal Type, Current Price, Entry Price
     - Stop Loss, Take Profit, Zone Type, Rejection Quality
     - Volume Status, RS Score, Risk:Reward Ratio, Reason

4. **Filter Results**
   - Gunakan dropdown "Filter Signal" untuk filter by:
     - **All Signals** - Show semua signals
     - **SMC Setup Only** - Hanya setup signals (limit order, tunggu konfirmasi)
     - **SMC Confirmed Only** - Hanya confirmed signals (market order, execute now!)
     - **Momentum Entry Only** - Hanya momentum signals
     - **Strong RS Only** - Hanya signals dengan RS > +5%
   - Table akan auto-update sesuai filter

5. **Analyze Signal Details (🔍 Signal Details Inspector)**
   - Scroll ke section "🔍 Signal Details Inspector"
   - **Select Stock from Dropdown**: Pilih stock yang ingin dianalisis detail
     - Format dropdown: `TICKER - SIGNAL_TYPE` (contoh: "BBCA - SMC_SETUP")
     - Dropdown searchable - bisa ketik ticker untuk cari cepat
   - **View Comprehensive Analysis** untuk selected stock:
     - 📊 **Price Levels**: Current Price, Entry Price, Stop Loss, TP1
     - 🎯 **Advanced Filter Details** (Phase 1):
       - Discount Zone position (SWEET_SPOT/DISCOUNT/PREMIUM)
       - Volume Anomaly check (NORMAL/PANIC_SELLING/ACCUMULATION)
       - Rejection Candle quality (STRONG/GOOD/PENDING)
       - TP Strategy (structure-aware adjustment info)
     - 📅 **Multi-Timeframe Analysis** (Phase 2):
       - Weekly-Daily trend alignment status
       - Number of weeks in current bullish trend
     - 📢 **Action Banner**:
       - SMC_SETUP: "Pasang BUY LIMIT order di Entry Price, tunggu konfirmasi rejection!"
       - SMC_ENTRY: "BUY MARKET ORDER SEKARANG! Rejection sudah terkonfirmasi!"
     - 💰 **Position Sizing Calculator**:
       - Input your capital
       - Auto-calculate suggested lot size based on 2% risk rule
   - **Switch Between Stocks**: Pilih stock lain dari dropdown untuk compare signals

6. **Export Signals** (Optional)
   - Klik `📥 Download Signals CSV` button (if available)
   - CSV will include all current filtered signals

#### Understanding the Table Columns

**All Signals Table** (mencakup SMC Setup, SMC Confirmed, dan Momentum):

| Column | Description | Interpretation |
|--------|-------------|----------------|
| **Ticker** | Stock symbol | IDX stock code |
| **Signal** | Signal type | SMC_SETUP / SMC_ENTRY / MOMENTUM_ENTRY |
| **Current** | Current market price | Real-time price |
| **Entry** | Suggested entry price | For SETUP: FVG mid (limit order)<br>For ENTRY: Current price (market order) |
| **SL** | Stop Loss price | Entry - (2 × ATR) |
| **TP1** | Take Profit target | Entry + (3 × ATR) or adjusted for resistance |
| **Zone** | Discount zone position | SWEET_SPOT (20-40% swing) = Best<br>DISCOUNT (<50%) = Good<br>PREMIUM (>50%) = Filtered out |
| **Rejection** | Rejection candle quality | STRONG = Confirmed buyer presence<br>GOOD = Acceptable confirmation<br>PENDING = Wait for confirmation |
| **Volume** | Volume status | LOW (<0.8× MA) = Best pullback<br>NORMAL = Acceptable<br>HIGH = Risky |
| **RS Score** | Relative Strength vs IHSG | +10% = Very Strong<br>+5% = Strong<br>0% = Neutral<br>Negative = Weak |
| **R:R** | Risk:Reward ratio | 1:3 = Standard target<br>Higher = Better |
| **Reason** | Strategy logic summary | Quick explanation why signal triggered |

**Signal Type Differences:**

**SMC_SETUP** (📢 Prepare):
- Entry = FVG mid price (limit order)
- Rejection = PENDING (wait for confirmation)
- Action: Pasang limit order, monitor untuk rejection candle

**SMC_ENTRY** (✅ Execute Now):
- Entry = Current price (market order)
- Rejection = STRONG/GOOD (confirmed)
- Action: Execute market order immediately!

**MOMENTUM_ENTRY** (⚡ Trend Ride):
- Entry = Current price (HMA bounce)
- No FVG zone (trend-following strategy)
- Action: Execute market order at HMA support

#### Signal Quality Indicators

**Phase 1 & 2 Advanced Filters** memastikan hanya signals berkualitas tinggi yang muncul:

🟢 **Best Quality (Execute Priority)**
- SMC_ENTRY (✅ Confirmed) with STRONG rejection
- Zone = SWEET_SPOT (20-40% of swing range)
- Volume = LOW (<0.8× MA) or NORMAL
- RS Score > +10% (very strong vs market)
- Weekly-Daily trend aligned (both bullish)
- R:R > 1:2.5

🟡 **Good Quality (Monitor & Prepare)**
- SMC_SETUP (📢 Prepare) in DISCOUNT zone (<50%)
- Rejection = PENDING (wait for confirmation)
- Volume = NORMAL (no panic selling detected)
- RS Score > 0% (outperforming market)
- Weekly-Daily aligned
- R:R > 1:2

🔵 **Acceptable (Momentum Alternative)**
- MOMENTUM_ENTRY at HMA support
- Stochastic < 40 & turning up
- RS Score > -5%
- SuperTrend bullish
- R:R > 1:2

🔴 **Filtered Out (Won't Appear)**
- FVG in PREMIUM zone (>50% swing) ❌
- Volume spike detected (panic selling) ❌
- Distribution pattern (2+ red high vol) ❌
- Weekly trend bearish (not aligned) ❌
- RS Score < minimum threshold ❌

**Key Insight:** Jika signal muncul di table, artinya sudah lolos semua Phase 1 & 2 filters. Signal quality dijamin tinggi!

---

### Tab 2: Chart Analysis 📊

**Purpose:** Analisis detail satu saham dengan chart interaktif.

#### How to Use

1. **Select Stock**
   - Gunakan dropdown di sidebar
   - Pilih ticker yang ingin dianalisis
   - Chart akan auto-load

2. **Understanding the Chart**

   **Main Chart (Top):**
   - 🟢 **Green Line** - HMA60 (Hull Moving Average)
   - 🔴/🟢 **Dots** - SuperTrend (red = bearish, green = bullish)
   - 🟦 **Blue Boxes** - Bullish FVG zones
   - 🟪 **Purple Boxes** - Bearish FVG zones
   - 📍 **Red Marker** - Current price level

   **Volume Panel (Middle):**
   - 📊 Bar chart showing volume
   - 🔵 Line - Volume MA (moving average)
   - Compare current volume vs average

   **Stochastic Panel (Bottom):**
   - 🔵 **Blue Line** - Stochastic K
   - 🟠 **Orange Line** - Stochastic D
   - 🔴 **Red Zone** (80+) - Overbought
   - 🟢 **Green Zone** (0-20) - Oversold
   - 🟡 **Yellow Zone** (20-80) - Neutral

3. **Chart Interactions**
   - 🔍 **Zoom** - Click and drag on chart
   - 📏 **Pan** - Use pan tool in toolbar
   - 💾 **Save** - Download chart as PNG
   - 🏠 **Reset** - Reset zoom to default

4. **Key Analysis Points**

   **For SMC Entry:**
   - ✅ Price mendekati blue box (bullish FVG)
   - ✅ SuperTrend hijau (bullish trend)
   - ✅ Volume rendah saat pullback
   - ✅ Price di atas HMA60

   **For Momentum Entry:**
   - ✅ Price bounce dari HMA60
   - ✅ SuperTrend hijau
   - ✅ Stochastic crossing up di zona < 60
   - ✅ K line di atas D line

5. **Technical Indicators Summary**

   Scroll down untuk lihat current values:
   - HMA, SuperTrend direction
   - Stochastic K & D values
   - RS Score
   - Volume ratio

#### Reading Market Structure

**Bullish Setup:**
```
Price > HMA60 ✅
SuperTrend: Green ✅
FVG: Blue boxes present ✅
Volume: Low during pullback ✅
Stochastic: Turning up ✅
```

**Bearish Setup (Avoid):**
```
Price < HMA60 ❌
SuperTrend: Red ❌
No FVG zones ❌
Volume: High panic selling ❌
Stochastic: Overbought ❌
```

---

### Tab 3: Trading Journal 📔

**Purpose:** Track trades dan monitor performance.

#### Managing Trades

1. **Add New Trade**
   - Fill form di sidebar:
     - Ticker, Entry Date, Entry Price
     - Position Size (shares)
     - Strategy Type (SMC/Momentum)
   - Klik `➕ Add Trade`
   - Trade akan masuk ke Active Trades

2. **Close Trade**
   - Pilih trade dari Active Trades table
   - Enter exit date dan exit price
   - Klik `🏁 Close Trade`
   - Trade pindah ke Closed Trades
   - P/L akan dihitung otomatis

3. **View Statistics**

   **Performance Metrics Card:**
   - Total Trades
   - Win Rate % (winning trades / total)
   - Average P/L %
   - Total P/L (IDR)
   - Best Trade % (highest win)
   - Worst Trade % (biggest loss)

4. **Active Trades Table**
   - Semua open positions
   - Shows: Ticker, Entry Date, Entry Price, Size, Strategy
   - Current P/L (jika price data available)

5. **Closed Trades Table**
   - Trade history
   - Shows: All entry data + Exit Date, Exit Price, P/L %, P/L IDR
   - Sortable by any column
   - Filter by date range

6. **Performance Chart**
   - Visualisasi cumulative P/L over time
   - X-axis: Trade dates
   - Y-axis: Cumulative profit/loss

#### Best Practices

**Position Sizing:**
```
Risk per trade = 2% of capital
Position Size = (Capital × 2%) / (Entry - Stop Loss)

Example:
Capital: Rp 100,000,000
Risk: 2% = Rp 2,000,000
Entry: Rp 1,000
SL: Rp 950
Risk per share: Rp 50

Position Size = 2,000,000 / 50 = 40,000 shares
```

**Journal Discipline:**
- ✅ Input trade segera setelah execution
- ✅ Set stop loss sesuai signal (ATR-based)
- ✅ Close trade dengan jujur (win or loss)
- ✅ Review journal setiap minggu
- ❌ Jangan skip losing trades
- ❌ Jangan edit historical trades

---

### Sidebar Features

**Watchlist Management:**
- View current watchlist
- Add new ticker (validate + auto-fetch data)
- Remove ticker
- Import/Export CSV

**Data Management:**
- Quick Update button
- Last update timestamp
- Database status

**Settings:**
- Filter options
- Display preferences
- Export options

---

## 📚 Strategy Explanation

### Smart Money Concepts (SMC) Entry

**Philosophy:** "Buy on Weakness, Sell on Strength"

#### What is Fair Value Gap (FVG)?

FVG adalah gap/inefficiency di harga yang cenderung diisi ulang oleh price action.

**Bullish FVG terbentuk ketika:**
- 3 candle pattern
- Candle 3 Low > Candle 1 High
- Gap significant (> ATR threshold)

**Trading Logic:**
- Price akan kembali ke FVG zone untuk "fill the gap"
- Entry saat price masuk FVG zone
- Low volume = institutional pullback (quality)
- Exit saat price breakout dari FVG

#### SMC Entry Criteria

| Kriteria | Requirement | Why? |
|----------|-------------|------|
| **Trend** | SuperTrend = Bullish | Follow the trend |
| **FVG** | Price in/near FVG zone (±10%) | Buy at value area |
| **Volume** | < Volume MA | Quiet accumulation |
| **RS Score** | > -5% | Not severely weak |

**Example:**
```
BBCA forming bullish FVG:
- FVG Zone: 8,800 - 9,000
- Current Price: 8,850 (in zone) ✅
- SuperTrend: Green ✅
- Volume: 0.6x average (LOW) ✅
- RS Score: +3.5% ✅

→ SMC ENTRY SIGNAL! 🎯
```

---

### Momentum Entry

**Philosophy:** "Ride the Monster Trend"

#### What is HMA Support?

HMA60 (Hull Moving Average) bertindak sebagai dynamic support di uptrend.

**Trading Logic:**
- Bullish trend: Price bounces dari HMA
- Stochastic confirms oversold bounce
- Entry saat momentum turning up
- Exit dengan trailing SuperTrend

#### Momentum Entry Criteria

| Kriteria | Requirement | Why? |
|----------|-------------|------|
| **Trend** | Price > HMA & SuperTrend green | Strong uptrend |
| **HMA Distance** | < 5% from HMA | Price near support |
| **Stochastic** | < 60 & K > D | Oversold + turning up |
| **RS Score** | > -10% | Not too weak |

**Example:**
```
ADRO at HMA support:
- Price: 1,900
- HMA60: 1,850 (2.6% distance) ✅
- SuperTrend: Green ✅
- Stochastic: K=42, D=38 (turning up) ✅
- RS Score: +1.2% ✅

→ MOMENTUM ENTRY! ⚡
```

---

### Risk Management

**Position Sizing Formula:**
```python
Risk per trade = 2% of capital
Position Size = (Capital × Risk%) / (Entry - SL)
```

**Stop Loss Placement:**
- ATR-based: Entry - (2 × ATR)
- Dynamic adjustment based on volatility
- Never move SL against position

**Take Profit Strategy:**
- TP1: Entry + (3 × ATR) → Close 50%
- TP2: Trail remaining 50% with SuperTrend
- Exit when SuperTrend flips bearish

**Example Trade:**
```
Entry: 1,000
SL: 950 (50 points risk)
TP1: 1,150 (150 points reward)
R:R Ratio: 1:3 ✅

Capital: 100,000,000
Risk: 2% = 2,000,000
Position Size: 2,000,000 / 50 = 40,000 shares
```

---

### Technical Indicators Explained

#### 1. Hull Moving Average (HMA60)

**Formula:** Weighted MA with lag reduction
**Period:** 60 bars (3 months daily)
**Use:** Dynamic support/resistance

**Interpretation:**
- Price > HMA → Bullish bias
- Price < HMA → Bearish bias
- HMA slope up → Strong uptrend
- HMA slope down → Strong downtrend

---

#### 2. SuperTrend

**Formula:** ATR-based trailing stop
**Parameters:** ATR Period = 10, Multiplier = 3
**Use:** Trend direction and exit signal

**Interpretation:**
- 🟢 Green dots = Bullish trend (buy/hold)
- 🔴 Red dots = Bearish trend (sell/avoid)
- Flip from red to green = Trend reversal

---

#### 3. Stochastic Oscillator

**Formula:** (Close - Low) / (High - Low) × 100
**Period:** 14 bars
**Use:** Momentum and oversold/overbought

**Zones:**
- 0-20: Oversold (potential bounce)
- 20-80: Neutral
- 80-100: Overbought (potential reversal)

**Signals:**
- K crosses above D = Buy signal
- K crosses below D = Sell signal

---

#### 4. Relative Strength (RS)

**Formula:** (Stock % change) - (IHSG % change)
**Period:** 60 days
**Use:** Stock vs market performance

**Interpretation:**
- RS > 0 = Outperforming market ✅
- RS = 0 = Inline with market
- RS < 0 = Underperforming market ❌

**Quality Levels:**
- RS > +10% = Very Strong
- RS > +5% = Strong
- RS > 0% = Good
- RS > -5% = Acceptable
- RS < -10% = Avoid

---

## 🔄 Trading Workflow

### Daily Routine

**Before Market Open (8:30 - 9:00 AM)**

```bash
# 1. Update data
python main.py update

# 2. Scan for signals
python main.py scan

# 3. Review signals in Web Dashboard
streamlit run app.py
```

1. Check Telegram notifications
2. Open Web Dashboard → Market Screener
3. Review SMC signals (priority)
4. Review Momentum signals
5. Analyze top signals in Chart Analysis
6. Create watchlist of potential entries

---

**During Market Hours (9:00 AM - 4:00 PM)**

1. Monitor watchlist stocks
2. Wait for price to enter FVG zone (SMC)
3. Or wait for HMA bounce (Momentum)
4. Execute trade with proper position size
5. Set stop loss immediately
6. Log trade in Journal tab

---

**After Market Close (4:00 - 5:00 PM)**

```bash
# Update end-of-day data
python main.py update

# Check journal
python main.py journal
```

1. Update closed positions in Journal
2. Review daily performance
3. Plan for next day
4. Backup data weekly

---

### Weekly Review

**Every Weekend:**

1. Review Journal statistics
2. Calculate weekly win rate
3. Analyze losing trades (what went wrong?)
4. Analyze winning trades (what went right?)
5. Adjust watchlist if needed
6. Export journal to CSV for record

---

## 💡 Tips & Best Practices

### Entry Tips

✅ **DO:**
- Wait for price to enter FVG zone (don't chase)
- Enter only when ALL criteria met
- Use limit orders at FVG mid-level
- Check volume - LOW volume is best
- Confirm RS score positive
- Set SL immediately after entry

❌ **DON'T:**
- Don't chase price above FVG
- Don't enter on HIGH volume pullback
- Don't enter bearish trend (SuperTrend red)
- Don't skip stop loss
- Don't use full capital on one trade

---

### Exit Tips

✅ **DO:**
- Take 50% profit at TP1
- Trail remaining with SuperTrend
- Exit when SuperTrend flips red
- Accept small losses quickly
- Let winners run

❌ **DON'T:**
- Don't move SL closer (give room)
- Don't exit winners too early
- Don't hold losers hoping for recovery
- Don't ignore SuperTrend exit signal

---

### Journal Tips

✅ **DO:**
- Log every trade (wins AND losses)
- Review journal weekly
- Calculate position size properly
- Track R:R ratio
- Note trade reasoning

❌ **DON'T:**
- Don't skip logging losing trades
- Don't fake journal entries
- Don't overtrade to improve stats
- Don't ignore statistics

---

### Watchlist Tips

**Optimal Size:** 50-200 stocks

**Selection Criteria:**
- ✅ Liquid stocks (volume > 1M shares/day)
- ✅ Mid to large cap
- ✅ Various sectors
- ❌ Avoid penny stocks
- ❌ Avoid illiquid stocks

**Maintenance:**
- Review monthly
- Remove dead stocks (no signals for 3 months)
- Add new IPOs or strong stocks
- Balance sectors

---

## 🔧 Troubleshooting

### Common Issues

#### "No signals found"

**Possible causes:**
1. Market in bearish condition (most stocks red)
2. Filters too strict
3. Watchlist too small

**Solutions:**
```bash
# Check with debug mode
python main.py scan --debug --limit 20

# Review what's failing:
# - Most stocks BEARISH? → Wait for market recovery
# - Stocks have FVG but bearish? → Market turning, be patient
# - Stoch too high? → Normal, wait for pullback
```

---

#### "No data available"

**Causes:**
- First time running
- Data not downloaded

**Solution:**
```bash
# Force full update
python main.py update --full

# Add ticker first if missing
python main.py add --ticker BBCA
```

---

#### "CSV import failed"

**Causes:**
- Wrong format
- Invalid tickers

**Solution:**
1. Check CSV format (see `TICKER_MANAGEMENT.md`)
2. Ensure ticker column exists
3. Use template: `watchlist_template.csv`

```csv
ticker
BBCA
BBRI
TLKM
```

---

#### "Streamlit won't start"

**Solutions:**
```bash
# Check if port 8501 is busy
streamlit run app.py --server.port 8502

# Or kill existing process
# Windows: taskkill /F /IM streamlit.exe
# Linux/Mac: pkill streamlit
```

---

#### "Slow performance"

**Causes:**
- Large watchlist (1000+ stocks)
- Full update running

**Solutions:**
1. Reduce watchlist to 100-200 stocks
2. Use incremental updates (not --full)
3. Close unused tabs in web dashboard

---

### Data Issues

#### "Price data outdated"

```bash
# Manual update
python main.py update

# Force full refresh
python main.py update --full
```

---

#### "Indicator values seem wrong"

**Check:**
1. Data completeness (need 60+ bars for HMA)
2. Update to latest data
3. Verify ticker valid on Yahoo Finance

```bash
# Re-download data
python main.py remove --ticker XXXX
python main.py add --ticker XXXX
```

---

## 📞 Support & Resources

### Documentation Files

- `README.md` - Project overview
- `QUICK_START.md` - 5-minute setup guide
- `USER_GUIDE.md` - This comprehensive guide
- `TICKER_MANAGEMENT.md` - Watchlist management
- `CSV_IMPORT_GUIDE.md` - CSV format details
- `CLAUDE.md` - Technical architecture (for developers)

### Getting Help

1. Check documentation first
2. Run debug mode: `python main.py scan --debug`
3. Check error messages carefully
4. Verify data updated: `python main.py update`

### Best Learning Path

1. ✅ Read QUICK_START.md (5 min)
2. ✅ Run first scan (test with 20 stocks)
3. ✅ Read this USER_GUIDE.md (30 min)
4. ✅ Practice with Web Dashboard
5. ✅ Paper trade for 1 week
6. ✅ Start real trading with small size
7. ✅ Scale up after 20+ trades

---

## 🎓 Strategy Deep Dive

### Why This Strategy Works

**1. Edge from Smart Money Concepts**
- Institutions leave footprints (FVG)
- We follow their accumulation zones
- Buy when they buy (low volume)
- Sell when they sell (breakout)

**2. Edge from Momentum**
- Ride established trends (HMA)
- Enter on pullbacks (Stochastic)
- Exit on trend change (SuperTrend)

**3. Edge from Risk Management**
- 2% risk per trade = survive drawdowns
- 1:3 R:R ratio = profitable over time
- Stop loss = limit losses
- Position sizing = consistency

**4. Edge from Relative Strength**
- Trade strong stocks in bull market
- Avoid weak stocks in bear market
- RS filter = trade leaders, not laggards

---

### Expected Performance

**Realistic Expectations:**

```
Win Rate: 45-55%
Average R:R: 1:2 to 1:3
Trades per month: 10-20 (depends on market)
Max Drawdown: 10-15%
Annual Return: 30-60% (with discipline)
```

**Important:**
- Some months will have 0 signals (bearish market)
- Some months will have 50+ signals (bullish market)
- Consistency > home runs
- Process > outcome

---

### Trading Psychology

**Emotional Management:**

1. **FOMO (Fear of Missing Out)**
   - ❌ Don't chase price above entry zone
   - ✅ Wait for next setup
   - ✅ There's always another trade

2. **Revenge Trading**
   - ❌ Don't overtrade after loss
   - ✅ Review what went wrong
   - ✅ Follow system rules

3. **Overconfidence**
   - ❌ Don't increase size after wins
   - ✅ Stick to 2% risk rule
   - ✅ One trade at a time

4. **Analysis Paralysis**
   - ❌ Don't overthink signals
   - ✅ If criteria met → enter
   - ✅ Trust the system

---

## 📊 Appendix

### Keyboard Shortcuts (Web Dashboard)

- `Ctrl + R` - Refresh page
- `Ctrl + F` - Find in page
- `Ctrl + +/-` - Zoom in/out

### File Locations

```
idx_sniper/
├── data/
│   ├── tickers.json          # Your watchlist
│   ├── market_data.db        # Price database
│   └── trading_journal.db    # Trade history
├── config/
│   └── settings.py           # Strategy parameters
└── logs/                     # Application logs
```

### Configuration Parameters

Edit `config/settings.py` to customize:

```python
# Risk Management
RISK_PERCENT = 2.0              # Risk per trade
SL_ATR_MULTIPLIER = 2.0         # Stop loss distance
TP1_ATR_MULTIPLIER = 3.0        # Take profit distance

# Filters
MIN_LIQUIDITY_IDR = 1_000_000_000  # 1B IDR minimum
VOLUME_LOW_THRESHOLD = 0.8      # 80% of avg = LOW
STOCH_OVERSOLD = 30             # Stochastic oversold level

# Indicators
HMA_PERIOD = 60                 # HMA period
SUPERTREND_ATR_PERIOD = 10      # SuperTrend ATR period
SUPERTREND_MULTIPLIER = 3.0     # SuperTrend multiplier
```

---

## ✅ Checklist for Success

### Daily Checklist

- [ ] Update market data
- [ ] Run market scan
- [ ] Review signals quality
- [ ] Check charts for top signals
- [ ] Execute trades (if any)
- [ ] Update trading journal
- [ ] Review open positions

### Weekly Checklist

- [ ] Review journal statistics
- [ ] Calculate win rate
- [ ] Analyze losing trades
- [ ] Update watchlist if needed
- [ ] Backup data
- [ ] Plan for next week

### Monthly Checklist

- [ ] Export journal to CSV
- [ ] Calculate monthly return
- [ ] Review strategy effectiveness
- [ ] Adjust watchlist
- [ ] Rebalance sectors
- [ ] Set goals for next month

---

**Happy Trading! 🚀📈**

*Remember: Discipline + Process + Risk Management = Long-term Success*

---

**Version:** 2.0
**Last Updated:** January 2025
**Author:** IDX Hybrid Sniper Team
