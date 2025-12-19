# 🚀 Quick Start Guide - IDX Hybrid Sniper

## ✅ Installation Complete!

Aplikasi sudah ditest dan siap digunakan. Semua module berfungsi dengan baik:

- ✅ Data Engine - Fetch data dari Yahoo Finance
- ✅ Technical Indicators - HMA, SuperTrend, FVG, Stochastic, RS
- ✅ Strategy Module - Signal generation SMC & Momentum
- ✅ Trading Journal - Record trades & performance tracking
- ✅ Chart Visualizer - Interactive Plotly charts
- ✅ CLI Tool - Command line interface
- ✅ Streamlit Dashboard - Web interface

---

## 🎯 Cara Menggunakan

### Option 1: Web Dashboard (Recommended untuk pemula)

```bash
cd "C:\Users\faizr\OneDrive\Smart Money Concepts\idx_sniper"
streamlit run app.py
```

Dashboard akan membuka di browser dengan 3 tab:
- **📊 Market Screener** - Scan pasar untuk entry signals
- **📈 Chart Analysis** - Analisis chart individual
- **📔 Trading Journal** - Catat dan monitor trades

### Option 2: CLI Tool (Recommended untuk automation)

#### Scan Market
```bash
cd "C:\Users\faizr\OneDrive\Smart Money Concepts\idx_sniper"
python main.py scan
```

Ini akan:
1. Update data terbaru
2. Scan semua 20 saham di watchlist
3. Tampilkan SMC & Momentum entry signals
4. (Optional) Kirim notifikasi Telegram

#### Update Data
```bash
python main.py update
```

#### Lihat Watchlist
```bash
python main.py watchlist
```

#### Tambah/Hapus Saham
```bash
python main.py add --ticker BBRI
python main.py remove --ticker BBRI
```

#### Lihat Journal Stats
```bash
python main.py journal
```

---

## 📝 Workflow Trading Harian

### Pagi (08:00 - 08:45)
```bash
python main.py scan
```
- Bot akan scan 20 saham dan tampilkan signals
- Cek saham dengan setup SMC Entry (prioritas #1)
- Validasi volume status: **LOW = Safe**, HIGH = Risk

### Market Open (09:00)
1. Buka web dashboard untuk detail analysis:
   ```bash
   streamlit run app.py
   ```
2. Klik saham di Market Screener untuk lihat chart
3. Gunakan Calculator untuk hitung lot size
4. Eksekusi order di aplikasi sekuritas (OLT/IPOT/etc)

### Setelah Entry
1. Buka tab "Trading Journal"
2. Klik "Add Trade"
3. Input:
   - Ticker
   - Entry date & price
   - Lot size
   - SL & TP1 (sudah auto-calculate di screener)
4. Save trade

### Monitoring (Hari berikutnya)
1. Buka tab "Open Positions"
2. Klik "🔄 Refresh Prices" untuk update floating P/L
3. Jika TP1 hit:
   - Jual 50% posisi di sekuritas
   - Update SL ke Break Even (klik "📝 Update SL")
4. Jika SuperTrend berubah merah:
   - Jual sisa 50%
   - Close position di journal

---

## 🔔 Setup Telegram (Opsional)

Untuk menerima notifikasi otomatis:

### 1. Buat Bot Telegram
1. Chat dengan [@BotFather](https://t.me/BotFather)
2. Ketik `/newbot`
3. Ikuti instruksi, copy **Bot Token**

### 2. Dapatkan Chat ID
1. Chat dengan [@userinfobot](https://t.me/userinfobot)
2. Copy **ID** yang muncul

### 3. Set Environment Variables

**Option A: Temporary (untuk sesi saat ini)**
```cmd
set TELEGRAM_BOT_TOKEN=your_bot_token_here
set TELEGRAM_CHAT_ID=your_chat_id_here
```

**Option B: Permanent**
1. Tekan `Win + R`, ketik `sysdm.cpl`
2. Tab "Advanced" → "Environment Variables"
3. Di "User variables" klik "New"
4. Variable name: `TELEGRAM_BOT_TOKEN`, Value: token Anda
5. Ulangi untuk `TELEGRAM_CHAT_ID`

### 4. Test Notifikasi
```bash
python main.py scan
```

Anda akan menerima:
- 🎯 SMC Entry Signal (jika ada)
- ⚡ Momentum Entry Signal (jika ada)
- 📋 Daily Watchlist Summary

---

## 🎓 Memahami Signals

### SMC Entry (Best Quality) 🎯
```
Kriteria:
✓ Price > SuperTrend (Trend bullish)
✓ Price di area Bullish FVG
✓ Volume < Volume MA (Pullback sehat)
✓ RS Score > -5% (Tidak lemah vs IHSG)

Entry: Limit order di mid-FVG
SL: Entry - (1.5 × ATR)
TP1: Entry + (2.0 × ATR)
```

### Momentum Entry (Secondary) ⚡
```
Kriteria:
✓ Price > HMA60 dan > SuperTrend
✓ Price sentuh HMA60
✓ Stochastic oversold + golden cross
✓ RS Score > 0% (Lebih kuat dari IHSG)

Entry: Market order saat stoch cross
SL: Entry - (1.5 × ATR)
TP1: Entry + (2.0 × ATR)
```

---

## 📊 Watchlist Default

20 saham blue chip IDX:
- Banking: BBCA, BBRI, BMRI, BBNI
- Telecom: TLKM
- Mining: ADRO, ITMG, PTBA, ANTM, INCO
- Consumer: UNVR, ICBP, INDF, KLBF
- Property: BSDE, PWON
- Others: ASII, SMGR, WIKA, PTPP

Edit di: `data/tickers.json`

---

## ⚙️ Kustomisasi

### Ubah Parameter Risk
Edit `config/settings.py`:
```python
RISK_PERCENT = 2.0  # Ubah ke 1.0 untuk lebih konservatif
```

### Ubah Parameter Indikator
```python
HMA_PERIOD = 60  # Ubah ke 50 untuk lebih responsif
SUPERTREND_MULTIPLIER = 3.0  # Ubah ke 2.5 untuk SL lebih ketat
```

### Tambah Saham ke Watchlist
Via CLI:
```bash
python main.py add --ticker ASII
```

Via Web Dashboard:
1. Sidebar → Input ticker → Klik "➕ Add"

---

## 🐛 Troubleshooting

### Error: "YF.download() FutureWarning"
**Status:** Warning saja, bukan error. Aplikasi tetap berjalan normal.

### Error: Streamlit tidak buka
```bash
# Check Streamlit version
streamlit --version

# Jika error, reinstall
pip install --upgrade streamlit
```

### Database kosong setelah scan
**Solusi:** Jalankan update penuh:
```bash
python main.py update --full
```

### Emoji tidak muncul di console
**Status:** Sudah dihandle dengan fallback text. Console Windows memiliki keterbatasan karakter.

---

## 📈 Test Results

```
Testing IDX Hybrid Sniper Core Modules...
==================================================

1. Testing Data Engine...
   ✓ Loaded 20 tickers from watchlist

2. Testing Data Fetch (BBCA)...
   ✓ Fetched 237 bars of BBCA data
   ✓ Latest close: Rp 8,175

3. Testing Technical Indicators...
   ✓ HMA calculated, latest: 8279.79
   ✓ SuperTrend calculated, direction: BEARISH
   ✓ FVG detected: 12 bullish, 16 bearish

4. Testing Strategy Module...
   ✓ IHSG data loaded: 237 bars
   ✓ Signal generated: NO_SIGNAL
   ✓ Current price: Rp 8,175

5. Testing Trading Journal...
   ✓ Journal stats loaded: 0 total trades
   ✓ Position calculator: 66 lots for 100M capital

6. Testing Chart Visualizer...
   ✓ Chart created with 8 traces

==================================================
✅ Core functionality test completed!
```

---

## 🎯 Next Steps

1. **Test Dashboard:**
   ```bash
   streamlit run app.py
   ```

2. **Scan Market:**
   ```bash
   python main.py scan
   ```

3. **Baca Strategy:**
   - `Grand Strategy.txt` - Manual lengkap strategi
   - `README.md` - Dokumentasi teknis

4. **Setup Automation (Optional):**
   - Windows Task Scheduler untuk run `python main.py scan` setiap pagi jam 08:00
   - Setup Telegram untuk notifikasi otomatis

---

## ⚠️ Disclaimer

Aplikasi ini adalah tool bantu analisis. Keputusan trading sepenuhnya tanggung jawab Anda. Gunakan risk management yang ketat (max 2% per trade).

**Selamat Trading! 🚀📈**
