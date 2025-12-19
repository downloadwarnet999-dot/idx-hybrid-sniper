# 📂 CSV Import/Export Guide

## Cara Import Ticker dari CSV

Ada 2 cara untuk import ticker ke watchlist:

### Option 1: Via CLI (Command Line)

```bash
# Import dan TAMBAH ke watchlist existing
python main.py import-csv --file my_tickers.csv

# Import dan REPLACE watchlist existing (hati-hati!)
python main.py import-csv --file my_tickers.csv --replace
```

### Option 2: Via Web Dashboard

1. Buka Streamlit: `streamlit run app.py`
2. Di Sidebar, klik **"📂 Import/Export CSV"**
3. Upload file CSV Anda
4. Centang "Replace existing" jika ingin replace semua (opsional)
5. Klik **"Import"**

---

## Format CSV

### Format Standar (Dengan Header)

```csv
ticker
BBCA
BBRI
BMRI
TLKM
ASII
```

### Format Tanpa Header (Juga Diterima)

```csv
BBCA
BBRI
BMRI
TLKM
ASII
```

### Aturan:
- ✅ Satu kolom saja
- ✅ Header boleh ada atau tidak ada
- ✅ Ticker akan otomatis diconvert ke UPPERCASE
- ✅ Ticker maksimal 10 karakter
- ✅ Baris kosong akan diabaikan
- ✅ Spasi di awal/akhir akan dihapus otomatis

---

## Template CSV

Gunakan file **`watchlist_template.csv`** sebagai contoh.

Anda bisa:
1. Copy template tersebut
2. Edit dengan Excel, Notepad, atau Google Sheets
3. Save as CSV
4. Import ke aplikasi

---

## Export Watchlist

### Via CLI

```bash
python main.py export-csv --file my_watchlist.csv
```

File `my_watchlist.csv` akan dibuat dengan format standar.

### Via Web Dashboard

1. Di Sidebar, klik **"📂 Import/Export CSV"**
2. Klik **"📥 Download CSV"**
3. Klik **"💾 Save watchlist.csv"**
4. File akan terdownload ke komputer Anda

---

## Use Cases

### 1. Backup Watchlist
```bash
# Export watchlist saat ini
python main.py export-csv --file backup_$(date +%Y%m%d).csv
```

### 2. Import Watchlist Sektor Tertentu

Buat file CSV per sektor, misalnya:

**banking.csv:**
```csv
ticker
BBCA
BBRI
BMRI
BBNI
BBTN
```

**mining.csv:**
```csv
ticker
ADRO
ITMG
PTBA
ANTM
INCO
```

Lalu import:
```bash
python main.py import-csv --file banking.csv
python main.py import-csv --file mining.csv
```

### 3. Replace dengan Watchlist Baru

Jika ingin ganti total watchlist:
```bash
python main.py import-csv --file new_watchlist.csv --replace
```

⚠️ **Hati-hati!** Flag `--replace` akan **menghapus** semua ticker existing dan diganti dengan yang ada di CSV.

### 4. Ambil Watchlist dari Screener

Jika Anda punya hasil screener dari website lain (RTI, Stockbit, dll) dalam format CSV:

1. Pastikan ada kolom dengan nama ticker
2. Save kolom tersebut saja ke CSV baru
3. Import ke aplikasi

---

## Tips & Tricks

### 1. Validasi Ticker

Setelah import, jalankan update untuk validasi:
```bash
python main.py update --full
```

Ticker yang tidak valid akan gagal fetch data.

### 2. Cek Jumlah Ticker

```bash
python main.py watchlist
```

Akan menampilkan semua ticker yang ada di watchlist.

### 3. Hapus Ticker Tertentu

Jika ada ticker yang salah:
```bash
python main.py remove --ticker XXXX
```

### 4. Kombinasi Manual + CSV

Anda bisa:
1. Import dari CSV
2. Tambah ticker manual via `python main.py add --ticker YYYY`
3. Export hasil kombinasi ke CSV baru

---

## Troubleshooting

### "No tickers imported"

**Penyebab:**
- File CSV kosong
- Format salah (lebih dari 1 kolom)
- File corrupt

**Solusi:**
1. Buka CSV dengan Notepad, pastikan formatnya benar
2. Gunakan template sebagai contoh
3. Pastikan encoding UTF-8

### "File not found"

**Penyebab:**
- Path file salah
- File tidak ada

**Solusi:**
```bash
# Gunakan path absolut
python main.py import-csv --file "C:\Users\Username\Documents\tickers.csv"

# Atau gunakan path relative dari folder aplikasi
python main.py import-csv --file watchlist_template.csv
```

### Import berhasil tapi ticker tidak muncul

**Solusi:**
Reload aplikasi:
- CLI: Jalankan `python main.py watchlist` lagi
- Streamlit: Refresh browser atau tekan **R**

---

## Contoh Workflow

```bash
# 1. Export watchlist saat ini untuk backup
python main.py export-csv --file backup.csv

# 2. Edit di Excel, tambah/hapus ticker

# 3. Save as CSV

# 4. Import watchlist baru (tambah ke existing)
python main.py import-csv --file backup.csv

# 5. Update data untuk ticker baru
python main.py update --full

# 6. Scan!
python main.py scan
```

---

## Format Lanjutan (Multi-kolom)

Jika CSV Anda punya banyak kolom, aplikasi akan:
- Ambil kolom pertama saja
- Abaikan kolom lainnya

Contoh CSV dengan banyak kolom:
```csv
ticker,name,sector
BBCA,Bank Central Asia,Banking
BBRI,Bank Rakyat Indonesia,Banking
TLKM,Telkom Indonesia,Telecom
```

Hanya kolom `ticker` yang akan diambil.

---

Selamat menggunakan fitur CSV Import/Export! 🚀
