# 🎯 IDX Hybrid Sniper v2.0

**Trading Ecosystem untuk Bursa Efek Indonesia (IDX)**

*Buy on Weakness, Sell on Strength, Ride the Monster Trend*

---

## 📖 Deskripsi

IDX Hybrid Sniper adalah sistem trading lengkap yang menggabungkan **Smart Money Concepts (SMC)** dengan analisis teknikal tradisional untuk pasar saham Indonesia. Sistem ini mengimplementasikan filosofi "Hybrid Sniper Protocol":

- **Masuk sebagai Sniper** (Swing Trading): Beli saat harga diskon dengan presisi tinggi
- **Keluar sebagai Paus** (Trend Following): Tahan posisi selama tren masih berlangsung

### Fitur Utama

✅ **Dual Interface**
- 🖥️ Web Dashboard (Streamlit) - Analisis visual interaktif
- 💻 CLI Tool - Automasi scan dan notifikasi

✅ **Smart Money Concepts**
- Fair Value Gap (FVG) detection
- Relative Strength vs IHSG
- Volume validation (Low volume pullback filter)

✅ **Technical Indicators**
- Hull Moving Average (HMA)
- SuperTrend dengan trailing stop
- Stochastic Oscillator

✅ **Trading Journal Digital**
- Track open positions
- Hitung floating P/L otomatis
- Performance analytics

✅ **Telegram Notifications**
- Real-time trading signals
- Daily watchlist summary

---

## 🚀 Installation

### 1. Clone atau Download Repository

```bash
cd idx_sniper
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Telegram (Opsional)

Jika ingin menerima notifikasi via Telegram:

**Windows:**
```cmd
set TELEGRAM_BOT_TOKEN=your_bot_token_here
set TELEGRAM_CHAT_ID=your_chat_id_here
```

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN=your_bot_token_here
export TELEGRAM_CHAT_ID=your_chat_id_here
```

Cara mendapatkan Telegram Bot Token:
1. Chat dengan [@BotFather](https://t.me/BotFather) di Telegram
2. Ketik `/newbot` dan ikuti instruksi
3. Copy token yang diberikan
4. Untuk mendapatkan Chat ID, chat dengan [@userinfobot](https://t.me/userinfobot)

---

## 💻 Penggunaan

### Web Dashboard (Streamlit)

Jalankan aplikasi web interaktif:

```bash
streamlit run app.py
```

Dashboard akan terbuka di browser (default: http://localhost:8501)

**3 Tab Utama:**

#### 1. 📊 Market Screener
- Scan semua saham di watchlist
- Filter berdasarkan tipe signal (SMC/Momentum)
- Filter berdasarkan Relative Strength
- Lihat detail setup dan kalkulator lot size

#### 2. 📈 Chart Analysis
- Pilih saham individual
- Chart interaktif dengan semua indikator
- FVG zones visualization
- Position size calculator

#### 3. 📔 Trading Journal
- Catat entry baru
- Monitor open positions dengan real-time price
- Update trailing stop
- Close positions dan lihat performance

### CLI Tool

#### Update Data

Update semua data saham (incremental):
```bash
python main.py update
```

Full update (fetch ulang semua history):
```bash
python main.py update --full
```

#### Scan Market

Scan pasar dan kirim notifikasi Telegram:
```bash
python main.py scan
```

Scan tanpa notifikasi:
```bash
python main.py scan --no-notify
```

#### Kelola Watchlist

Lihat watchlist:
```bash
python main.py watchlist
```

Tambah saham:
```bash
python main.py add --ticker BBCA
```

Hapus saham:
```bash
python main.py remove --ticker BBCA
```

#### Lihat Journal Summary

```bash
python main.py journal
```

---

## 📁 Struktur Proyek

```
idx_sniper/
├── config/
│   └── settings.py          # Konfigurasi & konstanta
├── data/
│   ├── tickers.json         # Watchlist saham
│   ├── market_data.db       # Database OHLCV
│   └── journal.db           # Database trading journal
├── src/
│   ├── database.py          # SQLite operations
│   ├── data_engine.py       # Data fetching (yfinance)
│   ├── indicators.py        # Technical indicators
│   ├── strategy.py          # Signal generation logic
│   ├── journal_mgr.py       # Trading journal manager
│   ├── visualizer.py        # Plotly charts
│   └── notifier.py          # Telegram bot
├── app.py                   # Streamlit dashboard
├── main.py                  # CLI tool
└── requirements.txt         # Dependencies
```

---

## 🎯 Trading Strategy

### Setup A: SMC Entry (High Quality)

**Kriteria:**
1. ✅ Price > SuperTrend (Trend bullish)
2. ✅ Price masuk ke Bullish FVG zone
3. ✅ Volume < Volume MA(20) - **CRITICAL** (Pullback sehat)
4. ✅ RS Score > -5% (Tidak lemah vs IHSG)

**Entry:** Mid-point FVG zone (Limit order)

### Setup B: Momentum Entry (Secondary)

**Kriteria:**
1. ✅ Price > HMA(60) dan > SuperTrend
2. ✅ Price menyentuh HMA(60) support
3. ✅ Stochastic < 30 (Oversold)
4. ✅ Stochastic Golden Cross (K crosses D)
5. ✅ RS Score > 0% (Outperforming IHSG)

**Entry:** Market order atau mendekati HMA

### Exit Strategy (2 Tahap)

#### Tahap 1: Secure The Bag
- **Kapan:** Price hit TP1 (Entry + 2.0 × ATR)
- **Aksi:**
  - Jual 50% posisi
  - Geser SL ke Break Even
- **Hasil:** Risk-free trade!

#### Tahap 2: Ride The Monster
- **Kapan:** Selama tren masih berlangsung
- **Aksi:** Hold sisa 50% posisi
- **Trailing:** SuperTrend line
- **Final Exit:** Close menembus SuperTrend (berubah merah)

### Risk Management

- **Maximum Risk:** 2% per trade
- **Stop Loss:** Entry - (1.5 × ATR)
- **Position Size:** `(Capital × 2%) / (Entry - SL) / 100`

---

## 📊 Indikator & Parameter

| Indikator | Parameter | Fungsi |
|-----------|-----------|---------|
| HMA | Period: 60 | Tren menengah responsif |
| SuperTrend | ATR: 10, Multiplier: 3.0 | Tren utama & trailing stop |
| Stochastic | K: 5, D: 3, Smooth: 3 | Momentum reversal |
| Volume MA | Period: 20 | Validasi pullback |
| RS vs IHSG | Lookback: 20 hari | Kekuatan relatif |

---

## 🔔 Notifikasi Telegram

Aplikasi akan mengirim notifikasi untuk:

- 🎯 **SMC Entry Signal** - dengan info volume & FVG level
- ⚡ **Momentum Entry Signal** - dengan info stochastic
- 📋 **Daily Watchlist Summary** - rangkuman scan pagi
- ✅ **TP1 Hit** - reminder untuk geser SL
- 🛑 **Stop Loss** - konfirmasi exit
- 🔔 **SuperTrend Exit** - trailing stop triggered

---

## 🛠️ Kustomisasi

### Menambah Sektor Saham

Edit `config/settings.py`:

```python
SECTORS = {
    'FINANCE': ['BBCA', 'BBRI', 'BMRI', ...],
    'CONSUMER': ['UNVR', 'INDF', ...],
    # Tambahkan sektor baru di sini
}
```

### Mengubah Parameter Strategi

Edit `config/settings.py`:

```python
# Risk Management
RISK_PERCENT = 2.0  # Ubah menjadi 1.0 untuk lebih konservatif

# Indikator
HMA_PERIOD = 60  # Ubah menjadi 50 untuk lebih responsif
SUPERTREND_MULTIPLIER = 3.0  # Ubah menjadi 2.5 untuk SL lebih ketat

# Volume Threshold
VOLUME_LOW_THRESHOLD = 0.8  # < 80% dari MA = Low Volume
```

---

## 📝 Best Practices

### Rutinitas Harian

**08:00 - Pre-Market**
```bash
# Update data dan scan market
python main.py scan
```
- Cek notifikasi Telegram untuk watchlist
- Buka web dashboard untuk detail analysis

**09:00 - Market Open**
- Eksekusi order di aplikasi sekuritas
- Catat trade di Trading Journal (tab 3)
- Pasang Stop Loss di sistem broker

**16:00 - Post-Market**
- Update floating P/L di dashboard
- Geser trailing stop jika diperlukan
- Review jurnal dan evaluasi

### Tips Penggunaan

1. ✅ **Always validate FVG dengan volume** - Ini yang membedakan true pullback vs knife catch
2. ✅ **Prioritaskan SMC Entry** dibanding Momentum Entry
3. ✅ **Jangan trading saham dengan RS Score < -5%** saat IHSG naik
4. ✅ **Geser SL ke BE setelah TP1** - risk management utama
5. ✅ **Trust the SuperTrend trailing** - jangan exit prematur

---

## ⚠️ Disclaimer

Aplikasi ini adalah tool bantu analisis teknikal. Keputusan trading sepenuhnya tanggung jawab pengguna. Tidak ada jaminan profit. Selalu gunakan risk management yang ketat.

**Risiko Trading:**
- Modal bisa berkurang
- Past performance ≠ future results
- Gunakan uang dingin (bukan uang darurat)

---

## 🤝 Support

Jika menemukan bug atau ada pertanyaan:

1. Check CLAUDE.md untuk panduan development
2. Review dokumentasi strategy di file .txt
3. Periksa logs dan error messages

---

## 📜 License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International

---

## 🎯 Mantra Trading

> **"Buy on Weakness, Sell on Strength, Ride the Monster Trend"**

Selamat Trading! 📈🚀
