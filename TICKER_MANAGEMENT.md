# 📝 Ticker Management - Semua Cara

Ada **4 cara** untuk mengelola ticker di watchlist:

---

## 1️⃣ Manual via CLI

### Tambah satu ticker
```bash
python main.py add --ticker BBCA
```

### Hapus satu ticker
```bash
python main.py remove --ticker BBCA
```

### Lihat watchlist
```bash
python main.py watchlist
```

---

## 2️⃣ Manual via Web Dashboard

1. Buka dashboard:
   ```bash
   streamlit run app.py
   ```

2. Di **Sidebar** → ketik ticker di box "Add Ticker"
3. Klik **"➕ Add"**

---

## 3️⃣ Import dari CSV (CLI)

### Import dan TAMBAH ke watchlist existing
```bash
python main.py import-csv --file my_tickers.csv
```

### Import dan REPLACE semua watchlist
```bash
python main.py import-csv --file my_tickers.csv --replace
```

**Format CSV:**
```csv
ticker
BBCA
BBRI
BMRI
```

Atau tanpa header:
```csv
BBCA
BBRI
BMRI
```

---

## 4️⃣ Import dari CSV (Web Dashboard)

1. Buka dashboard: `streamlit run app.py`

2. Di **Sidebar** → Klik **"📂 Import/Export CSV"** (expander)

3. **Upload file CSV** → Klik "Browse files"

4. (Optional) Centang **"Replace existing"** jika ingin replace semua

5. Klik **"Import"** button

6. Watchlist akan otomatis terupdate!

---

## 📥 Export Watchlist

### Via CLI
```bash
python main.py export-csv --file my_watchlist.csv
```

### Via Web Dashboard

1. Di Sidebar → Klik **"📂 Import/Export CSV"**
2. Klik **"📥 Download CSV"**
3. Klik **"💾 Save watchlist.csv"**
4. File akan terdownload

---

## 📋 Template & Format

### Gunakan Template
File **`watchlist_template.csv`** sudah tersedia di folder aplikasi.

Format:
```csv
ticker
BBCA
BBRI
BMRI
BBNI
TLKM
ASII
UNVR
ICBP
INDF
KLBF
```

### Aturan CSV:
- ✅ Satu kolom dengan header "ticker" (atau tanpa header)
- ✅ Satu ticker per baris
- ✅ Ticker akan auto-uppercase
- ✅ Maksimal 10 karakter per ticker
- ✅ Hanya alphanumeric (A-Z, 0-9)
- ✅ Baris kosong akan diabaikan
- ✅ Spasi di awal/akhir dihapus otomatis

### Format Multi-Kolom (Juga Diterima)
Jika CSV punya banyak kolom, hanya kolom pertama yang diambil:

```csv
ticker,name,sector
BBCA,Bank Central Asia,Banking
BBRI,Bank Rakyat Indonesia,Banking
TLKM,Telkom Indonesia,Telecom
```

---

## 🎯 Use Cases

### Use Case 1: Backup Watchlist
```bash
# Export watchlist saat ini
python main.py export-csv --file backup_20250118.csv
```

### Use Case 2: Import Watchlist Sektor
Buat file per sektor:

**banking.csv:**
```csv
ticker
BBCA
BBRI
BMRI
BBNI
```

**mining.csv:**
```csv
ticker
ADRO
ITMG
PTBA
```

Import:
```bash
python main.py import-csv --file banking.csv
python main.py import-csv --file mining.csv
```

### Use Case 3: Replace Total Watchlist
Ganti semua ticker dengan yang baru:
```bash
python main.py import-csv --file new_list.csv --replace
```

⚠️ **Warning:** `--replace` akan **menghapus semua** ticker lama!

### Use Case 4: Kombinasi Manual + CSV
1. Import dari CSV
2. Tambah manual: `python main.py add --ticker YYYY`
3. Export hasil: `python main.py export-csv --file combined.csv`

---

## ✅ Tested & Working

```
✅ Export CSV: 20 tickers exported successfully
✅ Import CSV: 20 tickers imported successfully
✅ Replace mode: Working
✅ Append mode: Working
✅ Web upload: Tested in Streamlit
✅ Web download: Tested in Streamlit
```

---

## 🔍 Validasi Ticker

Setelah import, validasi dengan update data:

```bash
python main.py update --full
```

Ticker yang tidak valid akan error saat fetch data.

---

## 📚 Documentation Lengkap

Lihat **`CSV_IMPORT_GUIDE.md`** untuk panduan detail termasuk troubleshooting.

---

**Selamat mengelola watchlist! 🚀**
